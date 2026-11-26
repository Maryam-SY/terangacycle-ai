"""`core.jobs` sans Valkey (story 1.18) : mise en file après le commit seulement, depuis une
unité synchrone ou asynchrone, durée bornée et échec journalisé quand Valkey ne répond pas.

La file réelle (Valkey) est couverte par `tests/integration/test_thumbnails.py`.
"""

import asyncio
import json
import socket
import threading
import time
from collections.abc import Callable, Iterator
from typing import Any

import anyio
import anyio.to_thread
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import db, jobs
from app.core.config import get_settings


class Boom(Exception):
    pass


@pytest.fixture
def uow(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    monkeypatch.setattr(
        db, "get_sessionmaker", lambda: sessionmaker(bind=engine, expire_on_commit=False)
    )
    yield
    engine.dispose()


@pytest.fixture
def valkey_url(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[[str], None]]:
    def set_url(url: str) -> None:
        monkeypatch.setenv("VALKEY_URL", url)
        get_settings.cache_clear()

    yield set_url
    get_settings.cache_clear()


@pytest.fixture
def queue(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, tuple[Any, ...], str, int]]:
    """Mises en file réussies (fonction, arguments, job_id, thread de la boucle)."""
    sent: list[tuple[str, tuple[Any, ...], str, int]] = []

    async def fake_enqueue_once(function: str, args: tuple[Any, ...], job_id: str) -> None:
        asyncio.get_running_loop()  # toujours dans une boucle asyncio
        sent.append((function, args, job_id, threading.get_ident()))

    monkeypatch.setattr(jobs, "_enqueue_once", fake_enqueue_once)
    return sent


def _events(out: str, event: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in out.splitlines() if line.startswith("{") and event in line]


# --- Après le commit seulement ----------------------------------------------------------


def test_sync_unit_enqueues_after_commit(uow: None, queue: list) -> None:
    with db.unit_of_work():
        jobs.enqueue_after_commit("thumb", "photo-1", job_id="thumb:photo-1")
        assert queue == []  # pas avant le commit
    assert [entry[:3] for entry in queue] == [("thumb", ("photo-1",), "thumb:photo-1")]


def test_sync_unit_never_enqueues_after_a_rollback(uow: None, queue: list) -> None:
    with pytest.raises(Boom), db.unit_of_work():
        jobs.enqueue_after_commit("thumb", "photo-1", job_id="thumb:photo-1")
        raise Boom
    assert queue == []


def test_async_unit_enqueues_after_commit_in_the_loop(uow: None, queue: list) -> None:
    async def run(fail: bool) -> int:
        async with db.async_unit_of_work():
            jobs.enqueue_after_commit("thumb", "p", job_id=f"thumb:{fail}")
            if fail:
                raise Boom
        return threading.get_ident()

    with pytest.raises(Boom):
        asyncio.run(run(fail=True))
    assert queue == []
    loop_thread = asyncio.run(run(fail=False))
    assert [(entry[2], entry[3]) for entry in queue] == [("thumb:False", loop_thread)]


def test_sync_unit_in_an_anyio_worker_thread_uses_the_application_loop(
    uow: None, queue: list
) -> None:
    """Route `def` de FastAPI : la mise en file est confiée à la boucle de l'application."""

    def route() -> int:
        with db.unit_of_work():
            jobs.enqueue_after_commit("thumb", "p", job_id="thumb:p")
        return threading.get_ident()

    async def app() -> tuple[int, int]:
        worker_thread = await anyio.to_thread.run_sync(route)
        return threading.get_ident(), worker_thread

    loop_thread, worker_thread = anyio.run(app)
    assert loop_thread != worker_thread
    assert [entry[3] for entry in queue] == [loop_thread]


def test_sync_unit_in_a_plain_thread_uses_an_ephemeral_loop(uow: None, queue: list) -> None:
    threads: list[int] = []

    def script() -> None:
        with db.unit_of_work():
            jobs.enqueue_after_commit("thumb", "p", job_id="thumb:p")
        threads.append(threading.get_ident())

    thread = threading.Thread(target=script)
    thread.start()
    thread.join(timeout=10)
    assert [entry[3] for entry in queue] == threads


def test_refuses_to_run_outside_a_unit_of_work(queue: list) -> None:
    with pytest.raises(RuntimeError, match="unité de travail"):
        jobs.enqueue_after_commit("thumb", "p", job_id="thumb:p")
    assert queue == []


def test_job_id_is_required(uow: None, queue: list) -> None:
    with db.unit_of_work(), pytest.raises(ValueError, match="job_id"):
        jobs.enqueue_after_commit("thumb", "p", job_id="")


# --- Pool arq --------------------------------------------------------------------------


def test_redis_settings_have_no_reconnection_loop(valkey_url: Callable[[str], None]) -> None:
    valkey_url("redis://queue.example:6380/3")
    settings = jobs._redis_settings()
    assert (settings.host, settings.port, settings.database) == ("queue.example", 6380, 3)
    assert settings.conn_retries == 0
    assert settings.conn_timeout <= jobs.ENQUEUE_TIMEOUT_S == 2.0


class FakePool:
    def __init__(self, job: object) -> None:
        self.job = job
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
        self.closed = False

    async def enqueue_job(self, function: str, *args: Any, **kwargs: Any) -> object:
        self.calls.append((function, args, kwargs))
        return self.job

    async def aclose(self) -> None:
        self.closed = True


@pytest.mark.parametrize(
    ("job", "event"), [(object(), "job_enqueued"), (None, "job_already_enqueued")]
)
def test_enqueue_passes_the_job_id_and_closes_the_pool(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    job: object,
    event: str,
) -> None:
    pool = FakePool(job)

    async def fake_create_pool(settings: Any) -> FakePool:
        return pool

    monkeypatch.setattr(jobs, "create_pool", fake_create_pool)
    capsys.readouterr()
    asyncio.run(jobs._enqueue("thumb", ("photo-1",), "thumb:photo-1"))
    assert pool.calls == [("thumb", ("photo-1",), {"_job_id": "thumb:photo-1"})]
    assert pool.closed
    (line,) = _events(capsys.readouterr().out, f'"{event}"')
    assert line["job_id"] == "thumb:photo-1"


# --- Valkey injoignable ----------------------------------------------------------------


@pytest.fixture
def silent_server() -> Iterator[int]:
    """Serveur TCP qui accepte les connexions et ne répond jamais : Valkey bloqué."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(16)
    accepted: list[socket.socket] = []
    stop = threading.Event()

    def accept() -> None:
        server.settimeout(0.1)
        while not stop.is_set():
            try:
                accepted.append(server.accept()[0])
            except OSError:
                continue

    thread = threading.Thread(target=accept, daemon=True)
    thread.start()
    try:
        yield server.getsockname()[1]
    finally:
        stop.set()
        thread.join(timeout=5)
        for conn in accepted:
            conn.close()
        server.close()


def test_silent_valkey_bounds_the_wait_and_logs_the_job_id_only(
    uow: None,
    valkey_url: Callable[[str], None],
    silent_server: int,
    capsys: pytest.CaptureFixture[str],
) -> None:
    valkey_url(f"redis://127.0.0.1:{silent_server}/0")
    capsys.readouterr()
    started = time.monotonic()
    with db.unit_of_work():
        jobs.enqueue_after_commit("thumb", "photo-secret-arg", job_id="thumb:photo-1")
    elapsed = time.monotonic() - started
    assert jobs.ENQUEUE_TIMEOUT_S - 0.5 <= elapsed < jobs.ENQUEUE_TIMEOUT_S + 1.5
    out = capsys.readouterr().out
    (line,) = _events(out, '"job_enqueue_failed"')
    assert line["job_id"] == "thumb:photo-1"
    assert set(line) - {"event", "level", "timestamp", "logger"} <= {"job_id", "reason"}
    assert "photo-secret-arg" not in out


def test_refused_valkey_fails_without_raising(
    uow: None, valkey_url: Callable[[str], None], capsys: pytest.CaptureFixture[str]
) -> None:
    # Port libre, fermé aussitôt : connexion refusée.
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    valkey_url(f"redis://127.0.0.1:{port}/0")
    capsys.readouterr()
    started = time.monotonic()
    with db.unit_of_work():
        jobs.enqueue_after_commit("thumb", "p", job_id="thumb:p")
    assert time.monotonic() - started < jobs.ENQUEUE_TIMEOUT_S + 1.5
    (line,) = _events(capsys.readouterr().out, '"job_enqueue_failed"')
    assert line["job_id"] == "thumb:p"


def test_silent_valkey_is_bounded_from_an_anyio_worker_thread(
    uow: None, valkey_url: Callable[[str], None], silent_server: int
) -> None:
    """Même borne quand la mise en file passe par la boucle de l'application."""
    valkey_url(f"redis://127.0.0.1:{silent_server}/0")

    def route() -> float:
        started = time.monotonic()
        with db.unit_of_work():
            jobs.enqueue_after_commit("thumb", "p", job_id="thumb:p")
        return time.monotonic() - started

    async def app() -> float:
        return await anyio.to_thread.run_sync(route)

    assert anyio.run(app) < jobs.ENQUEUE_TIMEOUT_S + 1.5
