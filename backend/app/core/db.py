"""Accès à la base : moteur SQLAlchemy, métadonnées et unité de travail (AD-17).

Unité de travail : une session et une transaction par requête ou par tâche, gardées
dans un `contextvar`.

- Requête HTTP : la dépendance `get_uow()` (à déclarer via `UowSession`) ouvre
  l'unité, valide en sortie, annule si une exception traverse la route.
- Tâche (worker, script) : `@transactional` ouvre l'unité si aucune n'est en cours.
- Service : `@transactional` rejoint l'unité en cours ; seul le niveau externe valide
  ou annule. Jamais de `commit`, `rollback` ni `begin` dans un service ou un
  repository (test d'architecture).
- Effets : `after_commit(fn, *args)` s'exécute après le commit externe et jamais après
  une annulation ; `after_rollback(fn, *args)` seulement après une annulation.

Règle : la session est synchrone (bloquante). Les routes et les services qui touchent
la base sont des `def` simples, exécutés par FastAPI dans le pool de threads. Du code
`async def` (route, tâche arq) n'interroge jamais la base via `current_session()` : il
bloquerait la boucle asyncio ; il délègue à une fonction `def` (pool de threads).
"""

import asyncio
import functools
import inspect
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)

# Convention de nommage des contraintes, pour des migrations Alembic stables.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


@lru_cache
def get_engine() -> Engine:
    """Moteur de l'application, connecté avec le rôle `teranga_app` (DML seulement)."""
    url = get_settings().database_url
    if url is None:
        raise RuntimeError(
            "Base de données non configurée : DATABASE_URL ou le secret db_app_password manque."
        )
    # Délai de connexion borné : une base arrêtée ne bloque pas /readyz ni une requête.
    # hide_parameters : les valeurs liées (une Position, par exemple) ne figurent jamais
    # dans les messages d'erreur, donc jamais dans les journaux.
    return create_engine(
        url.get_secret_value(),
        pool_pre_ping=True,
        hide_parameters=True,
        connect_args={"connect_timeout": 5},
    )


@lru_cache
def get_sessionmaker() -> sessionmaker:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


# --- Unité de travail -------------------------------------------------------------

Hook = tuple[Callable[..., Any], tuple[Any, ...]]


@dataclass
class UnitOfWork:
    session: Session
    # Vrai si l'unité se termine dans une boucle asyncio : les effets peuvent alors
    # être des coroutines.
    is_async: bool
    _after_commit: list[Hook] = field(default_factory=list)
    _after_rollback: list[Hook] = field(default_factory=list)


_current: ContextVar[UnitOfWork | None] = ContextVar("unit_of_work", default=None)


def _require_uow() -> UnitOfWork:
    uow = _current.get()
    if uow is None:
        raise RuntimeError("Aucune unité de travail en cours (get_uow ou @transactional).")
    return uow


def in_unit_of_work() -> bool:
    """Vrai si une unité de travail est en cours : un `@transactional` la rejoindrait."""
    return _current.get() is not None


def current_session() -> Session:
    """Session de l'unité de travail en cours (pour les repositories)."""
    return _require_uow().session


def _register(hooks: list[Hook], uow: UnitOfWork, fn: Callable[..., Any], args: tuple) -> None:
    if not uow.is_async and inspect.iscoroutinefunction(fn):
        raise TypeError(f"{fn!r} est une coroutine : l'unité de travail en cours est synchrone.")
    hooks.append((fn, args))


def after_commit(fn: Callable[..., Any], *args: Any) -> None:
    """Enregistre un effet externe, exécuté après le commit externe, abandonné au rollback."""
    uow = _require_uow()
    _register(uow._after_commit, uow, fn, args)


def after_rollback(fn: Callable[..., Any], *args: Any) -> None:
    """Enregistre un nettoyage, exécuté seulement si l'unité est annulée."""
    uow = _require_uow()
    _register(uow._after_rollback, uow, fn, args)


def _run_hooks_sync(hooks: list[Hook], kind: str) -> None:
    # Un effet en échec n'annule ni le commit déjà fait ni les effets suivants.
    for fn, args in hooks:
        try:
            fn(*args)
        except Exception:
            log.exception("uow_hook_failed", kind=kind, hook=getattr(fn, "__qualname__", "?"))


async def _run_hooks_async(hooks: list[Hook], kind: str) -> None:
    for fn, args in hooks:
        try:
            result = fn(*args)
            if inspect.isawaitable(result):
                await result
        except Exception:
            log.exception("uow_hook_failed", kind=kind, hook=getattr(fn, "__qualname__", "?"))


def _new_uow(is_async: bool) -> UnitOfWork:
    if _current.get() is not None:
        raise RuntimeError("Une unité de travail est déjà en cours : la rejoindre.")
    return UnitOfWork(session=get_sessionmaker()(), is_async=is_async)


@contextmanager
def unit_of_work() -> Iterator[Session]:
    """Unité de travail synchrone (tâche, script) : commit en sortie, rollback sur exception."""
    uow = _new_uow(is_async=False)
    token = _current.set(uow)
    committed = False
    try:
        try:
            yield uow.session
            uow.session.commit()
            committed = True
        except BaseException:
            uow.session.rollback()
            raise
        finally:
            try:
                uow.session.close()
            finally:
                _current.reset(token)
    finally:
        # Hors de l'unité : un effet qui ouvre une nouvelle unité ne rejoint pas celle-ci.
        _run_hooks_sync(
            uow._after_commit if committed else uow._after_rollback,
            "after_commit" if committed else "after_rollback",
        )


async def _shielded_commit(session: Session) -> bool:
    """Commit protégé de l'annulation ; renvoie True si une annulation est survenue.

    Une annulation pendant l'attente ne lance pas de rollback concurrent du commit en
    cours : on attend l'issue réelle du commit, qui décide des effets à exécuter.
    """
    task = asyncio.ensure_future(run_in_threadpool(session.commit))
    cancelled = False
    while not task.done():
        try:
            await asyncio.wait({task})
        except asyncio.CancelledError:
            cancelled = True
    task.result()  # lève l'erreur du commit, s'il a échoué
    return cancelled


@asynccontextmanager
async def async_unit_of_work() -> AsyncIterator[Session]:
    """Unité de travail pilotée depuis la boucle asyncio (requête, tâche arq).

    Les appels bloquants (commit, rollback, close) passent par le pool de threads.
    """
    uow = _new_uow(is_async=True)
    token = _current.set(uow)
    committed = False
    cancelled = False
    try:
        try:
            yield uow.session
            cancelled = await _shielded_commit(uow.session)
            committed = True
        except BaseException:
            await run_in_threadpool(uow.session.rollback)
            raise
        finally:
            try:
                await run_in_threadpool(uow.session.close)
            finally:
                _current.reset(token)
    finally:
        await _run_hooks_async(
            uow._after_commit if committed else uow._after_rollback,
            "after_commit" if committed else "after_rollback",
        )
    if cancelled:
        # Commit fait et effets exécutés : l'annulation reçue pendant le commit repart.
        raise asyncio.CancelledError


async def get_uow() -> AsyncIterator[Session]:
    """Dépendance FastAPI : une unité de travail par requête.

    À déclarer avec `scope="function"` (voir `UowSession`) : le commit a lieu avant
    l'envoi de la réponse, et une erreur de commit devient une réponse 500.
    La route qui l'utilise est un `def` simple (voir la règle du module).
    """
    async with async_unit_of_work() as session:
        yield session


# Type à utiliser dans les routes : `def route(session: UowSession) -> ...`.
# La route est un `def` simple, jamais `async def` : la session est bloquante et doit
# s'exécuter dans le pool de threads, pas dans la boucle asyncio.
UowSession = Annotated[Session, Depends(get_uow, scope="function")]


def transactional[**P, R](fn: Callable[P, R]) -> Callable[P, R]:
    """Rejoint l'unité de travail en cours, ou en ouvre une (tâche) s'il n'y en a pas.

    Fonctionne sur une fonction synchrone ou une coroutine.
    """
    if inspect.iscoroutinefunction(fn):

        @functools.wraps(fn)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            if _current.get() is not None:
                return await fn(*args, **kwargs)
            async with async_unit_of_work():
                return await fn(*args, **kwargs)

        return async_wrapper  # type: ignore[return-value]

    @functools.wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if _current.get() is not None:
            return fn(*args, **kwargs)
        with unit_of_work():
            return fn(*args, **kwargs)

    return wrapper
