"""Worker : battement `worker:heartbeat`, cycle de vie et healthcheck (AD-27) ; tâche
`thumb` (story 1.18)."""

import asyncio
import json
import threading
from uuid import UUID, uuid4

import pytest
from arq import Retry
from arq.worker import Function

from app import worker
from app.core.errors import DomainError, ErrorCode
from app.core.health import HEARTBEAT_KEY, heartbeat_is_fresh
from app.modules.reports import service as reports_service


class FakeRedis:
    """Valkey simulé : `set` (avec TTL) et `get` ; échoue sur les appels demandés."""

    def __init__(self, fail_on: set[int] | None = None) -> None:
        self.store: dict[str, str] = {}
        self.ttls: dict[str, int] = {}
        self.calls = 0
        self.fail_on = fail_on or set()

    async def set(self, key: str, value: str, ex: int) -> None:
        self.calls += 1
        if self.calls in self.fail_on:
            raise ConnectionError("valkey indisponible")
        self.store[key] = value
        self.ttls[key] = ex

    async def get(self, key: str) -> str | None:
        return self.store.get(key)


def test_write_heartbeat_contract() -> None:
    fake = FakeRedis()
    asyncio.run(worker.write_heartbeat(fake))  # type: ignore[arg-type]
    assert fake.ttls[HEARTBEAT_KEY] == 90
    # La valeur écrite par le worker est celle que lit /readyz.
    assert heartbeat_is_fresh(fake.store[HEARTBEAT_KEY])


def test_heartbeat_loop_survives_a_valkey_error() -> None:
    fake = FakeRedis(fail_on={1})

    async def run() -> None:
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(worker.heartbeat_loop(fake, interval_s=0.01), timeout=0.2)  # type: ignore[arg-type]

    asyncio.run(run())
    assert fake.calls >= 2
    assert HEARTBEAT_KEY in fake.store


def test_startup_then_shutdown_cancels_the_heartbeat() -> None:
    fake = FakeRedis()

    async def run() -> asyncio.Task:
        ctx: dict = {"redis": fake}
        await worker.startup(ctx)
        task = ctx["heartbeat_task"]
        await asyncio.sleep(0)  # premier battement
        await worker.shutdown(ctx)
        assert "heartbeat_task" not in ctx
        return task

    task = asyncio.run(run())
    assert task.cancelled()
    assert HEARTBEAT_KEY in fake.store


def test_worker_settings_declare_cron_jobs() -> None:
    assert worker.WorkerSettings.cron_jobs == []
    assert worker.WorkerSettings.on_startup is worker.startup
    assert worker.WorkerSettings.on_shutdown is worker.shutdown


@pytest.mark.parametrize(("fresh", "code"), [(True, 0), (False, 1)])
def test_healthcheck_exit_code(fresh: bool, code: int, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_healthcheck() -> bool:
        return fresh

    monkeypatch.setattr(worker, "_healthcheck", fake_healthcheck)
    assert worker.main(["healthcheck"]) == code


def test_healthcheck_error_is_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    async def broken() -> bool:
        raise ConnectionError("valkey indisponible")

    monkeypatch.setattr(worker, "_healthcheck", broken)
    assert worker.main(["healthcheck"]) == 1


def test_main_without_command_is_usage_error() -> None:
    assert worker.main([]) == 2


# --- Tâche thumb (story 1.18) ------------------------------------------------------------


def test_worker_functions_are_noop_and_thumb() -> None:
    noop, thumb = worker.WorkerSettings.functions
    assert noop is worker.noop
    assert isinstance(thumb, Function)
    assert thumb.name == reports_service.THUMB_JOB == "thumb"
    assert thumb.coroutine is worker.thumb
    assert thumb.max_tries == worker.THUMB_MAX_TRIES == 5


def test_thumb_delegates_to_the_service_in_a_thread(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[UUID, int]] = []

    def make_thumbnail(photo_id: UUID) -> str:
        calls.append((photo_id, threading.get_ident()))
        return "report_thumb/2026/11/x.jpg"

    monkeypatch.setattr(reports_service, "make_thumbnail", make_thumbnail)
    photo_id = uuid4()

    async def run() -> int:
        await worker.thumb({"job_try": 1}, str(photo_id))
        return threading.get_ident()

    loop_thread = asyncio.run(run())
    assert [call[0] for call in calls] == [photo_id]
    assert calls[0][1] != loop_thread  # pool de threads, pas la boucle


def _unavailable(photo_id: UUID) -> str:
    raise DomainError(ErrorCode.STORAGE_UNAVAILABLE, 503)


@pytest.mark.parametrize(("job_try", "defer_s"), [(1, 5.0), (2, 10.0), (3, 20.0), (4, 40.0)])
def test_unavailable_storage_retries_with_a_growing_delay(
    monkeypatch: pytest.MonkeyPatch, job_try: int, defer_s: float
) -> None:
    monkeypatch.setattr(reports_service, "make_thumbnail", _unavailable)
    with pytest.raises(Retry) as exc_info:
        asyncio.run(worker.thumb({"job_try": job_try}, str(uuid4())))
    assert exc_info.value.defer_score == int(defer_s * 1000)


def test_last_try_fails_and_is_logged(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(reports_service, "make_thumbnail", _unavailable)
    photo_id = str(uuid4())
    capsys.readouterr()
    with pytest.raises(RuntimeError, match="storage_unavailable"):
        asyncio.run(worker.thumb({"job_try": worker.THUMB_MAX_TRIES}, photo_id))
    lines = [
        json.loads(line) for line in capsys.readouterr().out.splitlines() if "thumb_failed" in line
    ]
    assert [(line["photo_id"], line["job_try"]) for line in lines] == [(photo_id, 5)]


def test_other_domain_errors_are_not_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    def refused(photo_id: UUID) -> str:
        raise DomainError(ErrorCode.VALIDATION_ERROR, 422)

    monkeypatch.setattr(reports_service, "make_thumbnail", refused)
    with pytest.raises(DomainError) as exc_info:
        asyncio.run(worker.thumb({"job_try": 1}, str(uuid4())))
    assert exc_info.value.code is ErrorCode.VALIDATION_ERROR
