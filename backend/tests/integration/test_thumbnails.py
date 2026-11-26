"""Miniature d'une photo de Signalement sur PostgreSQL, Garage et Valkey réels (story 1.18),
sans mock.

Exige la pile démarrée et migrée et les variables de `test_reports_api.py`, plus
`TEST_VALKEY_URL` (Valkey publié sur 127.0.0.1). Sans elles, les tests sont ignorés, sauf
avec `REQUIRE_INTEGRATION=1` (CI) : ils échouent.

Les tâches mises en file dans `TEST_VALKEY_URL` sont exécutées par le worker de la pile, qui
doit tourner sur le code testé (voir le README). La clé d'une tâche est donc acceptée dans
n'importe quel état (`arq:job:`, `arq:in-progress:`, `arq:result:`) : le worker peut l'avoir
déjà prise. Les scénarios qui exécutent eux-mêmes la tâche (rejeu, ligne retirée, Garage
indisponible) partent d'un Signalement créé quand Valkey est injoignable : aucune tâche n'est
alors en file, et le worker de la pile ne leur fait pas concurrence.

L'horloge est fixée en juillet 2032 (objets sous `report/2032/07/` et `report_thumb/2032/07/`,
préfixes propres à ce fichier) ; ce que crée un test est supprimé à la fin.
"""

import asyncio
import base64
import hashlib
import hmac
import io
import json
import os
import socket
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import boto3
import pytest
import redis
from arq.connections import RedisSettings, create_pool
from arq.constants import (
    in_progress_key_prefix,
    job_key_prefix,
    result_key_prefix,
    retry_key_prefix,
)
from arq.jobs import Job
from arq.worker import Worker, func
from botocore.config import Config
from fastapi import FastAPI
from PIL import Image
from sqlalchemy import Engine, create_engine, make_url, text

from app import worker
from app.core import clock, db, jobs, storage
from app.core.config import get_settings
from app.core.security import Principal
from app.main import create_app
from app.modules.reports import service as reports_service
from app.modules.reports.schemas import parse_meta
from tests import photos
from tests.asgi import Response
from tests.reports import TEST_PEPPER, new_device_id, post_report, report_meta, sample_photo

pytestmark = pytest.mark.integration

DEFAULT_BUCKET = "terangacycle-photos"
FIXED_NOW = datetime(2032, 7, 15, 9, 0, tzinfo=UTC)
PHOTO_PREFIX = "report/2032/07/"
THUMB_PREFIX = "report_thumb/2032/07/"
TRACKING_YEAR = 2032
# Critère d'acceptation : la miniature est enregistrée par le worker de la pile en moins de
# 30 s.
WORKER_DEADLINE_S = 30.0
CONNECT_TIMEOUT_S = 10
JOB_STATES = (job_key_prefix, in_progress_key_prefix, result_key_prefix)


class Boom(Exception):
    pass


def _env(var: str) -> str:
    value = os.environ.get(var, "").strip()
    if not value:
        pytest.skip(f"{var} non défini : tests d'intégration de la miniature ignorés")
    return value


def _hash(device_id: str) -> str:
    key = base64.b64decode(TEST_PEPPER)
    return hmac.new(key, device_id.encode("ascii"), hashlib.sha256).hexdigest()


def _free_port() -> int:
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    return port


class _Server:
    """Serveur TCP local : `close_at_once` ferme chaque connexion aussitôt (S3 en panne),
    sinon la garde ouverte sans jamais répondre (Valkey bloqué)."""

    def __init__(self, close_at_once: bool) -> None:
        self.close_at_once = close_at_once
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(64)
        self.sock.settimeout(0.1)
        self.port = self.sock.getsockname()[1]
        self.held: list[socket.socket] = []
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self) -> None:
        while not self.stop.is_set():
            try:
                conn, _ = self.sock.accept()
            except OSError:
                continue
            if self.close_at_once:
                conn.close()
            else:
                self.held.append(conn)

    def close(self) -> None:
        self.stop.set()
        self.thread.join(timeout=5)
        for conn in self.held:
            conn.close()
        self.sock.close()


@dataclass
class Stack:
    app: FastAPI
    engine: Engine
    s3: Any
    bucket: str
    valkey: redis.Redis
    valkey_url: str
    monkeypatch: pytest.MonkeyPatch
    device_ids: list[str] = field(default_factory=list)
    owner_keys: list[str] = field(default_factory=list)
    job_ids: list[str] = field(default_factory=list)

    # --- Réglages ----------------------------------------------------------------------

    def use_valkey(self, url: str) -> None:
        """Valkey vu par `core.jobs` (lu dans `get_settings()` à chaque mise en file)."""
        self.monkeypatch.setenv("VALKEY_URL", url)
        get_settings.cache_clear()

    def use_s3_endpoint(self, url: str) -> None:
        self.monkeypatch.setenv("S3_ENDPOINT", url)
        get_settings.cache_clear()
        storage._s3_client.cache_clear()

    # --- Requêtes ----------------------------------------------------------------------

    def device(self) -> str:
        device_id = new_device_id()
        self.device_ids.append(device_id)
        return device_id

    def post(
        self, meta: dict[str, Any] | None = None, photo: bytes | None = None, **kwargs: Any
    ) -> Response:
        device_id = kwargs.pop("device_id", None) or self.device()
        return post_report(
            self.app,
            device_id,
            report_meta() if meta is None else meta,
            sample_photo() if photo is None else photo,
        )

    def create(self, photo: bytes | None = None) -> Any:
        """Signalement créé (201) ; renvoie sa ligne `report_photos`."""
        response = self.post(photo=photo)
        assert response.status == 201, response.text
        (row,) = self.photos_of(response.json()["id"])
        self.job_ids.append(f"thumb:{row.id}")
        return row

    def create_without_job(self, photo: bytes | None = None) -> Any:
        """Signalement créé alors que Valkey refuse la connexion : aucune tâche en file."""
        self.use_valkey(f"redis://127.0.0.1:{_free_port()}/0")
        try:
            return self.create(photo)
        finally:
            self.use_valkey(self.valkey_url)

    # --- Relecture ---------------------------------------------------------------------

    def photos_of(self, report_id: str) -> list[Any]:
        with self.engine.connect() as conn:
            return conn.execute(
                text("SELECT * FROM report_photos WHERE report_id = :id"), {"id": report_id}
            ).all()

    def photo(self, photo_id: UUID) -> Any:
        with self.engine.connect() as conn:
            return conn.execute(
                text("SELECT * FROM report_photos WHERE id = :id"), {"id": photo_id}
            ).one_or_none()

    def objects(self, prefix: str) -> list[str]:
        paginator = self.s3.get_paginator("list_objects_v2")
        return [
            item["Key"]
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix)
            for item in page.get("Contents", [])
        ]

    def read(self, key: str) -> bytes:
        return self.s3.get_object(Bucket=self.bucket, Key=key)["Body"].read()

    def job_states(self, job_id: str) -> list[str]:
        """États où la tâche `job_id` figure dans Valkey (en file, en cours, terminée)."""
        return [prefix for prefix in JOB_STATES if self.valkey.exists(prefix + job_id)]

    def wait_thumb_keys(self, photo_ids: list[UUID]) -> dict[UUID, str]:
        """Clés de miniature enregistrées par le worker de la pile, attendues 30 s au plus."""
        deadline = time.monotonic() + WORKER_DEADLINE_S
        while True:
            with self.engine.connect() as conn:
                rows = conn.execute(
                    text("SELECT id, thumb_key FROM report_photos WHERE id = ANY(:ids)"),
                    {"ids": photo_ids},
                ).all()
            done = {row.id: row.thumb_key for row in rows if row.thumb_key is not None}
            if len(done) == len(photo_ids):
                return done
            assert time.monotonic() < deadline, (
                f"{len(photo_ids) - len(done)} miniature(s) absente(s) après "
                f"{WORKER_DEADLINE_S:.0f} s : le worker de la pile exécute-t-il le code testé ?"
            )
            time.sleep(0.2)

    # --- Nettoyage ---------------------------------------------------------------------

    def cleanup(self, counter_existed: bool) -> None:
        owner_keys = [f"device:{_hash(device_id)}" for device_id in self.device_ids]
        owner_keys += self.owner_keys
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "DELETE FROM report_photos WHERE report_id IN "
                    "(SELECT id FROM reports WHERE owner_key = ANY(:keys))"
                ),
                {"keys": owner_keys},
            )
            conn.execute(
                text("DELETE FROM reports WHERE owner_key = ANY(:keys)"), {"keys": owner_keys}
            )
            conn.execute(
                text("DELETE FROM devices WHERE device_hash = ANY(:h)"),
                {"h": [_hash(device_id) for device_id in self.device_ids]},
            )
            if not counter_existed:
                conn.execute(
                    text(
                        "DELETE FROM tracking_counters WHERE year = :y AND NOT EXISTS "
                        "(SELECT 1 FROM reports WHERE tracking_number LIKE :prefix)"
                    ),
                    {"y": TRACKING_YEAR, "prefix": f"TC-{TRACKING_YEAR}-%"},
                )
        # Après la suppression des lignes : une tâche en cours a fini d'écrire (verrou),
        # une tâche à venir ne trouvera plus de ligne.
        for key in {*self.objects(PHOTO_PREFIX), *self.objects(THUMB_PREFIX)}:
            try:
                self.s3.delete_object(Bucket=self.bucket, Key=key)
            except Exception as exc:
                print(f"nettoyage impossible : {key} ({type(exc).__name__})")
        for job_id in self.job_ids:
            self.valkey.delete(result_key_prefix + job_id, retry_key_prefix + job_id)


@pytest.fixture
def stack(monkeypatch: pytest.MonkeyPatch) -> Iterator[Stack]:
    endpoint = _env("TEST_S3_ENDPOINT")
    access_key = _env("TEST_S3_ACCESS_KEY_ID")
    secret_key = _env("TEST_S3_SECRET_ACCESS_KEY")
    valkey_url = _env("TEST_VALKEY_URL")
    bucket = os.environ.get("TEST_S3_BUCKET", "").strip() or DEFAULT_BUCKET
    region = os.environ.get("TEST_S3_REGION", "").strip() or "garage"
    database_url = make_url(_env("TEST_APP_DATABASE_URL"))
    if database_url.drivername in ("postgresql", "postgres"):
        database_url = database_url.set(drivername="postgresql+psycopg")

    for name, value in {
        "ENV": "dev",
        "DEMO_MODE": "false",
        "DATABASE_URL": database_url.render_as_string(hide_password=False),
        "S3_ENDPOINT": endpoint,
        "S3_ACCESS_KEY_ID": access_key,
        "S3_SECRET_ACCESS_KEY": secret_key,
        "S3_BUCKET": bucket,
        "S3_REGION": region,
        "VALKEY_URL": valkey_url,
        "DEVICE_ID_PEPPER": TEST_PEPPER,
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(clock, "now", lambda: FIXED_NOW)
    caches = (get_settings, db.get_engine, db.get_sessionmaker, storage._s3_client)
    for cache in caches:
        cache.cache_clear()

    engine = create_engine(
        database_url, hide_parameters=True, connect_args={"connect_timeout": CONNECT_TIMEOUT_S}
    )
    s3 = boto3.session.Session().client(
        "s3",
        endpoint_url=endpoint,
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(
            s3={"addressing_style": "path"},
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        ),
    )
    valkey = redis.Redis.from_url(valkey_url, socket_connect_timeout=5, socket_timeout=5)
    target = Stack(
        app=create_app(get_settings()),
        engine=engine,
        s3=s3,
        bucket=bucket,
        valkey=valkey,
        valkey_url=valkey_url,
        monkeypatch=monkeypatch,
    )
    with engine.connect() as conn:
        counter_existed = (
            conn.scalar(text("SELECT n FROM tracking_counters WHERE year = :y"), {"y": 2032})
            is not None
        )
    try:
        yield target
    finally:
        try:
            target.use_valkey(valkey_url)
            target.use_s3_endpoint(endpoint)
            target.cleanup(counter_existed)
        finally:
            valkey.close()
            engine.dispose()
            db.get_engine().dispose()
            for cache in caches:
                cache.cache_clear()


def _assert_thumbnail(stack: Stack, photo: Any, thumb_key: str) -> Image.Image:
    assert thumb_key == storage.thumb_key_for(photo.object_key)
    assert thumb_key == THUMB_PREFIX + photo.object_key.removeprefix(PHOTO_PREFIX)
    body = stack.read(thumb_key)
    assert len(body) <= storage.MAX_THUMB_BYTES == 30_720
    assert not set(photos.jpeg_markers(body)) & photos.METADATA_MARKERS
    image = Image.open(io.BytesIO(body))
    assert image.format == "JPEG" and not image.getexif()
    assert max(image.size) <= storage.THUMB_MAX_SIDE
    head = stack.s3.head_object(Bucket=stack.bucket, Key=thumb_key)
    assert head["ContentType"] == "image/jpeg"
    return image


def _thumb(photo_id: UUID) -> None:
    """La tâche `thumb` telle que le worker l'exécute (premier essai)."""
    asyncio.run(worker.thumb({"job_try": 1}, str(photo_id)))


def _events(out: str, event: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in out.splitlines() if f'"{event}"' in line]


# --- Nominal et petite photo -------------------------------------------------------------


def test_creation_enqueues_the_job_and_the_stack_worker_records_the_thumbnail(
    stack: Stack, capsys: pytest.CaptureFixture[str]
) -> None:
    capsys.readouterr()
    photo = stack.create(sample_photo())  # 64 × 48
    job_id = f"thumb:{photo.id}"
    # En file, en cours ou déjà terminée : le worker de la pile a pu la prendre.
    assert stack.job_states(job_id), f"aucune tâche {job_id} dans Valkey"
    (enqueued,) = _events(capsys.readouterr().out, "job_enqueued")
    assert enqueued["job_id"] == job_id

    thumb_key = stack.wait_thumb_keys([photo.id])[photo.id]
    image = _assert_thumbnail(stack, photo, thumb_key)
    assert image.size == (64, 48)  # jamais agrandie
    assert stack.objects(THUMB_PREFIX) == [thumb_key]


def test_ten_1_mb_photos_get_ten_thumbnails_under_30_kib(stack: Stack) -> None:
    aspects = [(4, 3), (3, 4), (16, 9), (9, 16), (1, 1), (3, 1), (1, 3), (5, 4), (2, 1), (4, 5)]
    rows = []
    for seed, aspect in enumerate(aspects):
        received = photos.high_entropy_jpeg(aspect, seed=1800 + seed)
        assert 900_000 <= len(received) <= storage.MAX_PHOTO_BYTES
        rows.append(stack.create(received))

    thumb_keys = stack.wait_thumb_keys([row.id for row in rows])
    for row in rows:
        _assert_thumbnail(stack, row, thumb_keys[row.id])
    assert sorted(stack.objects(THUMB_PREFIX)) == sorted(thumb_keys.values())


# --- Rejeu -------------------------------------------------------------------------------


def test_replaying_the_job_never_creates_a_second_object(
    stack: Stack, capsys: pytest.CaptureFixture[str]
) -> None:
    photo = stack.create_without_job()
    assert stack.job_states(f"thumb:{photo.id}") == []
    before = len(stack.objects(THUMB_PREFIX))

    _thumb(photo.id)
    first = stack.photo(photo.id).thumb_key
    _assert_thumbnail(stack, photo, first)
    capsys.readouterr()
    _thumb(photo.id)

    assert stack.photo(photo.id).thumb_key == first
    assert len(stack.objects(THUMB_PREFIX)) == before + 1
    assert stack.objects(first) == [first]
    (line,) = _events(capsys.readouterr().out, "thumb_already_recorded")
    assert line["photo_id"] == str(photo.id)


def test_two_concurrent_runs_store_a_single_object(stack: Stack) -> None:
    photo = stack.create_without_job()
    before = len(stack.objects(THUMB_PREFIX))
    results: list[str | None] = []
    errors: list[BaseException] = []

    def run() -> None:
        try:
            results.append(reports_service.make_thumbnail(photo.id))
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=run) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    assert not errors
    thumb_key = stack.photo(photo.id).thumb_key
    assert results == [thumb_key, thumb_key]
    assert len(stack.objects(THUMB_PREFIX)) == before + 1
    _assert_thumbnail(stack, photo, thumb_key)


# --- Annulation et renvoi -----------------------------------------------------------------


def test_rollback_after_storage_enqueues_nothing(
    stack: Stack, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exception après `ingest_photo` et après l'enregistrement de la mise en file, avant
    le commit : ni tâche (dans aucun état), ni ligne, ni objet."""
    registered: list[str] = []
    real_enqueue = jobs.enqueue_after_commit

    def enqueue_then_fail(function: str, *args: Any, job_id: str) -> None:
        real_enqueue(function, *args, job_id=job_id)
        registered.append(job_id)
        raise Boom("échec avant le commit")

    monkeypatch.setattr(jobs, "enqueue_after_commit", enqueue_then_fail)
    user = Principal(kind="user", owner_key=f"user:{uuid4()}")
    stack.owner_keys.append(user.owner_key)
    meta = parse_meta(json.dumps(report_meta()))

    with pytest.raises(Boom):
        reports_service.create_report(user, meta, sample_photo, stack.app.state.settings)

    (job_id,) = registered
    stack.job_ids.append(job_id)
    photo_id = UUID(job_id.removeprefix("thumb:"))
    assert stack.job_states(job_id) == []
    assert not stack.valkey.exists(retry_key_prefix + job_id)
    assert stack.photo(photo_id) is None
    assert stack.objects(PHOTO_PREFIX) == [] and stack.objects(THUMB_PREFIX) == []


def test_idempotent_resend_enqueues_no_new_job(
    stack: Stack, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    real_enqueue = jobs.enqueue_after_commit

    def counting(function: str, *args: Any, job_id: str) -> None:
        calls.append(job_id)
        real_enqueue(function, *args, job_id=job_id)

    monkeypatch.setattr(jobs, "enqueue_after_commit", counting)
    device_id = stack.device()
    meta = report_meta()
    first = stack.post(meta, device_id=device_id)
    assert first.status == 201, first.text
    (photo,) = stack.photos_of(first.json()["id"])
    stack.job_ids.append(f"thumb:{photo.id}")

    again = stack.post(meta, device_id=device_id)
    assert again.status == 200, again.text
    assert again.json()["id"] == first.json()["id"]
    assert calls == [f"thumb:{photo.id}"]
    assert stack.job_states(f"thumb:{photo.id}")


# --- Ligne retirée, Garage indisponible ---------------------------------------------------


def test_removed_report_stops_the_job_without_writing(
    stack: Stack, capsys: pytest.CaptureFixture[str]
) -> None:
    photo = stack.create_without_job()
    with stack.engine.begin() as conn:
        conn.execute(text("DELETE FROM report_photos WHERE id = :id"), {"id": photo.id})
        conn.execute(text("DELETE FROM reports WHERE id = :id"), {"id": photo.report_id})
    capsys.readouterr()

    _thumb(photo.id)

    assert stack.objects(THUMB_PREFIX) == []
    (line,) = _events(capsys.readouterr().out, "thumb_photo_gone")
    assert line["photo_id"] == str(photo.id)


def test_missing_source_object_stops_without_retry(
    stack: Stack, capsys: pytest.CaptureFixture[str]
) -> None:
    photo = stack.create_without_job()
    stack.s3.delete_object(Bucket=stack.bucket, Key=photo.object_key)
    capsys.readouterr()

    _thumb(photo.id)  # aucune exception : pas de nouvel essai

    assert stack.photo(photo.id).thumb_key is None
    assert stack.objects(THUMB_PREFIX) == []
    (line,) = _events(capsys.readouterr().out, "thumb_source_missing")
    assert (line["photo_id"], line["object_key"]) == (str(photo.id), photo.object_key)


def test_unavailable_storage_is_retried_five_times_then_fails(
    stack: Stack, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Vrai worker arq (en rafale, file propre au test) et vrai Valkey ; le stockage est un
    port local qui ferme chaque connexion. 5 essais, délais réduits, puis échec journalisé."""
    photo = stack.create_without_job()
    tries: list[int] = []
    real_make = reports_service.make_thumbnail

    def counting(photo_id: UUID) -> str | None:
        tries.append(1)
        return real_make(photo_id)

    monkeypatch.setattr(reports_service, "make_thumbnail", counting)
    monkeypatch.setattr(worker, "THUMB_RETRY_BASE_S", 0.05)
    queue_name = f"test-thumb:{uuid4()}"
    job_id = f"thumb:{photo.id}"
    broken_s3 = _Server(close_at_once=True)
    stack.use_s3_endpoint(f"http://127.0.0.1:{broken_s3.port}")
    capsys.readouterr()

    async def run() -> Any:
        settings = RedisSettings.from_dsn(stack.valkey_url)
        pool = await create_pool(settings)
        try:
            await pool.enqueue_job("thumb", str(photo.id), _job_id=job_id, _queue_name=queue_name)
            arq_worker = Worker(
                functions=[func(worker.thumb, name="thumb", max_tries=worker.THUMB_MAX_TRIES)],
                redis_settings=settings,
                queue_name=queue_name,
                burst=True,
                poll_delay=0.05,
                handle_signals=False,
            )
            try:
                await asyncio.wait_for(arq_worker.main(), timeout=120)
            finally:
                await arq_worker.close()
            return await Job(job_id, pool, _queue_name=queue_name).result_info()
        finally:
            await pool.delete(queue_name)
            await pool.aclose()

    try:
        result = asyncio.run(run())
    finally:
        broken_s3.close()
        stack.job_ids.append(job_id)

    assert len(tries) == worker.THUMB_MAX_TRIES == 5
    assert result is not None and result.success is False and result.job_try == 5
    out = capsys.readouterr().out
    assert len(_events(out, "thumb_retry")) == 4
    (failed,) = _events(out, "thumb_failed")
    assert (failed["photo_id"], failed["job_try"]) == (str(photo.id), 5)
    assert stack.photo(photo.id).thumb_key is None
    stack.use_s3_endpoint(_env("TEST_S3_ENDPOINT"))
    assert stack.objects(THUMB_PREFIX) == []


# --- Valkey indisponible ------------------------------------------------------------------


def test_unreachable_valkey_keeps_the_201_and_bounds_the_request(
    stack: Stack, capsys: pytest.CaptureFixture[str]
) -> None:
    silent = _Server(close_at_once=False)
    stack.use_valkey(f"redis://127.0.0.1:{silent.port}/0")
    capsys.readouterr()
    try:
        started = time.monotonic()
        response = stack.post()
        elapsed = time.monotonic() - started
    finally:
        silent.close()
        stack.use_valkey(stack.valkey_url)

    assert response.status == 201, response.text
    assert elapsed < jobs.ENQUEUE_TIMEOUT_S + 3.0
    (photo,) = stack.photos_of(response.json()["id"])
    job_id = f"thumb:{photo.id}"
    out = capsys.readouterr().out
    (failed,) = _events(out, "job_enqueue_failed")
    assert failed["job_id"] == job_id
    # Commit fait malgré l'échec : ligne et photo présentes, aucune tâche en file.
    assert photo.thumb_key is None
    assert stack.objects(PHOTO_PREFIX) == [photo.object_key]
    assert stack.job_states(job_id) == []


def test_enqueue_with_the_same_job_id_is_refused_by_arq(stack: Stack) -> None:
    """Unicité par `job_id` : une seconde mise en file de `thumb:<photo_id>` n'ajoute rien
    tant que la tâche ou son résultat est dans Valkey."""
    photo = stack.create()
    job_id = f"thumb:{photo.id}"
    stack.wait_thumb_keys([photo.id])
    assert stack.job_states(job_id)

    async def enqueue_again() -> object:
        pool = await create_pool(RedisSettings.from_dsn(stack.valkey_url))
        try:
            return await pool.enqueue_job("thumb", str(photo.id), _job_id=job_id)
        finally:
            await pool.aclose()

    assert asyncio.run(enqueue_again()) is None
