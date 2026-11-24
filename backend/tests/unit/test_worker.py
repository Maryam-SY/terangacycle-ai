"""Worker : battement `worker:heartbeat`, cycle de vie et healthcheck (AD-27)."""

import asyncio

import pytest

from app import worker
from app.core.health import HEARTBEAT_KEY, heartbeat_is_fresh


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
