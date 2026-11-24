"""Unité de travail (AD-17) : commit externe, rejoint, `after_commit` et `after_rollback`.

Mécanique seulement : la base est un SQLite en mémoire (aucune règle métier testée).
"""

import asyncio
from collections.abc import Callable, Iterator

import pytest
from fastapi import FastAPI
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import db
from app.core.config import Settings
from app.core.db import (
    UowSession,
    after_commit,
    after_rollback,
    current_session,
    transactional,
    unit_of_work,
)
from app.main import create_app
from tests.asgi import request


class Boom(Exception):
    pass


@pytest.fixture
def engine(monkeypatch: pytest.MonkeyPatch) -> Iterator[Engine]:
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE items (name TEXT NOT NULL)"))
    monkeypatch.setattr(
        db, "get_sessionmaker", lambda: sessionmaker(bind=engine, expire_on_commit=False)
    )
    yield engine
    engine.dispose()


def _names(engine: Engine) -> list[str]:
    with engine.connect() as conn:
        return list(conn.scalars(text("SELECT name FROM items ORDER BY name")))


def _insert(name: str) -> None:
    current_session().execute(text("INSERT INTO items (name) VALUES (:n)"), {"n": name})


# --- Unité synchrone (tâche) ----------------------------------------------------


def test_commit_then_after_commit(engine: Engine) -> None:
    events: list[str] = []

    @transactional
    def task() -> None:
        _insert("a")
        after_commit(events.append, "committed")
        after_rollback(events.append, "rolled_back")
        assert events == []  # rien avant la fin de l'unité

    task()
    assert _names(engine) == ["a"]
    assert events == ["committed"]


def test_exception_rolls_back_and_skips_after_commit(engine: Engine) -> None:
    events: list[str] = []

    @transactional
    def task() -> None:
        _insert("a")
        after_commit(events.append, "committed")
        after_rollback(events.append, "rolled_back")
        raise Boom

    with pytest.raises(Boom):
        task()
    assert _names(engine) == []
    assert events == ["rolled_back"]


def test_nested_transactional_joins_outer_unit(engine: Engine) -> None:
    """Le service appelé rejoint l'unité : une erreur plus tard annule tout."""
    events: list[str] = []

    @transactional
    def inner_service() -> None:
        _insert("inner")
        after_commit(events.append, "inner_committed")
        after_rollback(events.append, "inner_rolled_back")

    @transactional
    def outer_service() -> None:
        _insert("outer")
        inner_service()
        # L'unité interne n'a rien validé : les effets attendent l'unité externe.
        assert events == []
        raise Boom

    with pytest.raises(Boom):
        outer_service()
    assert _names(engine) == []
    assert events == ["inner_rolled_back"]


def test_nested_success_commits_once(engine: Engine) -> None:
    events: list[str] = []

    @transactional
    def inner_service() -> None:
        _insert("inner")
        after_commit(events.append, "inner")

    @transactional
    def outer_service() -> None:
        inner_service()
        _insert("outer")
        after_commit(events.append, "outer")

    outer_service()
    assert _names(engine) == ["inner", "outer"]
    assert events == ["inner", "outer"]


def test_failing_after_commit_hook_does_not_break_others(engine: Engine) -> None:
    events: list[str] = []

    def broken() -> None:
        raise RuntimeError("effet en échec")

    with unit_of_work():
        _insert("a")
        after_commit(broken)
        after_commit(events.append, "second")

    assert _names(engine) == ["a"]
    assert events == ["second"]


def test_hooks_require_a_unit_of_work() -> None:
    with pytest.raises(RuntimeError):
        after_commit(print)
    with pytest.raises(RuntimeError):
        after_rollback(print)
    with pytest.raises(RuntimeError):
        current_session()


def test_coroutine_hook_refused_in_sync_unit(engine: Engine) -> None:
    async def effect() -> None:
        return None

    with pytest.raises(TypeError), unit_of_work():
        after_commit(effect)


def test_after_commit_runs_outside_the_finished_unit(engine: Engine) -> None:
    """Un effet qui ouvre une nouvelle unité ne rejoint pas celle qui vient de valider."""

    @transactional
    def follow_up() -> None:
        _insert("follow_up")

    @transactional
    def task() -> None:
        _insert("first")
        after_commit(follow_up)

    task()
    assert _names(engine) == ["first", "follow_up"]


# --- Unité asynchrone (tâche arq) -----------------------------------------------


def test_async_transactional_runs_coroutine_hooks(engine: Engine) -> None:
    events: list[str] = []

    async def enqueue(name: str) -> None:
        events.append(name)

    @transactional
    async def task(fail: bool) -> None:
        _insert("x")
        after_commit(enqueue, "committed")
        after_rollback(enqueue, "rolled_back")
        if fail:
            raise Boom

    with pytest.raises(Boom):
        asyncio.run(task(True))
    assert (_names(engine), events) == ([], ["rolled_back"])

    events.clear()
    asyncio.run(task(False))
    assert (_names(engine), events) == (["x"], ["committed"])


# --- Dépendance FastAPI get_uow ---------------------------------------------------


@pytest.fixture
def app(engine: Engine, make_settings: Callable[..., Settings]) -> tuple[FastAPI, list[str]]:
    events: list[str] = []
    application = create_app(make_settings())

    @transactional
    def service(name: str, fail: bool) -> None:
        _insert(name)
        after_commit(events.append, f"commit:{name}")
        after_rollback(events.append, f"rollback:{name}")
        if fail:
            raise Boom

    @application.post("/v1/_test/items/{name}")
    def create_item(name: str, session: UowSession, fail: bool = False) -> dict[str, str]:
        assert session is current_session()
        service(name, fail)
        return {"name": name}

    return application, events


def test_request_commits_then_runs_after_commit(
    app: tuple[FastAPI, list[str]], engine: Engine
) -> None:
    application, events = app
    response = request(application, "POST", "/v1/_test/items/ok")
    assert response.status == 200
    assert _names(engine) == ["ok"]
    assert events == ["commit:ok"]


def test_request_error_rolls_back(app: tuple[FastAPI, list[str]], engine: Engine) -> None:
    application, events = app
    response = request(application, "POST", "/v1/_test/items/ko?fail=true")
    assert response.status == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert _names(engine) == []
    assert events == ["rollback:ko"]


# --- Échecs du commit et de la fermeture --------------------------------------------


class CommitFails(Exception):
    pass


def _use_session_class(monkeypatch: pytest.MonkeyPatch, engine: Engine, cls: type) -> None:
    monkeypatch.setattr(
        db,
        "get_sessionmaker",
        lambda: sessionmaker(bind=engine, class_=cls, expire_on_commit=False),
    )


class FailingCommitSession(Session):
    def commit(self) -> None:
        raise CommitFails


def test_failed_commit_in_request_rolls_back(
    app: tuple[FastAPI, list[str]], engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    application, events = app
    _use_session_class(monkeypatch, engine, FailingCommitSession)
    response = request(application, "POST", "/v1/_test/items/lost")
    assert response.status == 500
    body = response.json()
    assert body["error"]["code"] == "internal_error"
    assert body["error"]["request_id"] == response.headers["x-request-id"]
    assert _names(engine) == []
    assert events == ["rollback:lost"]


def test_failed_commit_in_sync_unit_runs_after_rollback(
    engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_session_class(monkeypatch, engine, FailingCommitSession)
    events: list[str] = []
    with pytest.raises(CommitFails), unit_of_work():
        _insert("lost")
        after_commit(events.append, "committed")
        after_rollback(events.append, "rolled_back")
    assert events == ["rolled_back"]
    assert db._current.get() is None


def test_response_is_sent_after_commit(
    app: tuple[FastAPI, list[str]], engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    application, _ = app
    order: list[str] = []

    class RecordingSession(Session):
        def commit(self) -> None:
            super().commit()
            order.append("commit")

    _use_session_class(monkeypatch, engine, RecordingSession)

    def on_message(message: dict) -> None:
        if message["type"] == "http.response.start":
            order.append("response.start")

    response = request(application, "POST", "/v1/_test/items/ordered", on_message=on_message)
    assert response.status == 200
    assert order == ["commit", "response.start"]


class FailingCloseSession(Session):
    def close(self) -> None:
        super().close()
        raise RuntimeError("fermeture en échec")


def test_close_failure_still_resets_the_unit(
    engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_session_class(monkeypatch, engine, FailingCloseSession)
    with pytest.raises(RuntimeError, match="fermeture"), unit_of_work():
        _insert("a")
    assert db._current.get() is None

    async def run() -> None:
        with pytest.raises(RuntimeError, match="fermeture"):
            async with db.async_unit_of_work():
                pass
        assert db._current.get() is None

    asyncio.run(run())
