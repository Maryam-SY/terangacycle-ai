"""`POST /v1/reports` sur PostgreSQL, PostGIS et Garage réels (story 1.11), sans mock.

Exige la pile démarrée et migrée et les variables de `test_storage_garage.py` :
`TEST_APP_DATABASE_URL` et `TEST_S3_ENDPOINT`, `TEST_S3_ACCESS_KEY_ID`,
`TEST_S3_SECRET_ACCESS_KEY` (`TEST_S3_BUCKET`, `TEST_S3_REGION` facultatifs). Sans elles,
les tests sont ignorés, sauf avec `REQUIRE_INTEGRATION=1` (CI) : ils échouent.

Chaque ligne de la matrice de la story est vérifiée par relecture de la base et du bucket.
L'horloge est fixée en mai 2032 (objets sous `report/2032/05/`) ; les Signalements,
appareils, Organisations, objets et compteurs créés par un test sont supprimés à la fin.
"""

import base64
import hashlib
import hmac
import io
import json
import os
import re
import threading
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import boto3
import pytest
from botocore.config import Config
from fastapi import FastAPI
from PIL import Image
from sqlalchemy import Engine, create_engine, make_url, text
from sqlalchemy.orm import Session

from app.core import clock, db, geo, storage
from app.core.config import get_settings
from app.core.errors import ErrorCode
from app.core.errors.codes import DEFAULT_MESSAGES
from app.main import create_app
from app.modules.orgs.service import PLATFORM_ORGANIZATION_ID
from app.modules.reports import repository as reports_repository
from tests import photos
from tests.asgi import Response
from tests.reports import (
    MISSING,
    PLATEAU,
    TEST_PEPPER,
    THIES,
    new_device_id,
    post_report,
    report_meta,
    sample_photo,
)

pytestmark = pytest.mark.integration

DEFAULT_BUCKET = "terangacycle-photos"
FIXED_NOW = datetime(2032, 5, 10, 8, 30, tzinfo=UTC)
OBJECT_PREFIX = "report/2032/05/"
# Années dont un test crée le compteur ; supprimé en fin de test s'il n'existait pas.
TEST_YEARS = (2026, 2027, 2032)
UUID4 = r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
OBJECT_KEY = re.compile(rf"report/2032/05/({UUID4})\.jpg")
TRACKING_NUMBER = re.compile(r"TC-[0-9]{4}-[0-9]{6}")
RESPONSE_FIELDS = {"id", "tracking_number", "status", "received_at", "is_demo"}


class Boom(Exception):
    pass


def _env(var: str) -> str:
    value = os.environ.get(var, "").strip()
    if not value:
        pytest.skip(f"{var} non défini : tests d'intégration de POST /v1/reports ignorés")
    return value


def _hash(device_id: str) -> str:
    key = base64.b64decode(TEST_PEPPER)
    return hmac.new(key, device_id.encode("ascii"), hashlib.sha256).hexdigest()


@dataclass
class Stack:
    app: FastAPI
    engine: Engine
    s3: Any
    bucket: str
    device_ids: list[str] = field(default_factory=list)
    org_ids: list[UUID] = field(default_factory=list)

    # --- Requêtes --------------------------------------------------------------------

    def device(self) -> str:
        device_id = new_device_id()
        self.device_ids.append(device_id)
        return device_id

    def post(
        self,
        meta: dict[str, Any] | str | None = None,
        photo: bytes | None = None,
        *,
        device_id: str | None = None,
        **kwargs: Any,
    ) -> Response:
        return post_report(
            self.app,
            device_id or self.device(),
            report_meta() if meta is None else meta,
            sample_photo() if photo is None else photo,
            **kwargs,
        )

    def created(self, response: Response) -> dict[str, Any]:
        assert response.status == 201, response.text
        body = response.json()
        assert set(body) == RESPONSE_FIELDS
        return body

    # --- Relecture ---------------------------------------------------------------------

    def scalar(self, sql: str, **params: Any) -> Any:
        with self.engine.connect() as conn:
            return conn.scalar(text(sql), params)

    def report(self, report_id: str) -> Any:
        with self.engine.connect() as conn:
            return conn.execute(
                text(
                    "SELECT r.*, ST_Y(r.geog::geometry) AS lat, ST_X(r.geog::geometry) AS lng, "
                    "char_length(r.comment) AS comment_chars FROM reports r WHERE r.id = :id"
                ),
                {"id": report_id},
            ).one()

    def photos_of(self, report_id: str) -> list[Any]:
        with self.engine.connect() as conn:
            return conn.execute(
                text("SELECT * FROM report_photos WHERE report_id = :id"), {"id": report_id}
            ).all()

    def device_row(self, device_id: str) -> Any:
        with self.engine.connect() as conn:
            return conn.execute(
                text("SELECT * FROM devices WHERE device_hash = :h"), {"h": _hash(device_id)}
            ).one_or_none()

    def objects(self) -> list[str]:
        paginator = self.s3.get_paginator("list_objects_v2")
        return [
            item["Key"]
            for page in paginator.paginate(Bucket=self.bucket, Prefix=OBJECT_PREFIX)
            for item in page.get("Contents", [])
        ]

    def counter(self, year: int) -> int | None:
        return self.scalar("SELECT n FROM tracking_counters WHERE year = :y", y=year)

    def footprint(self) -> dict[str, Any]:
        """Ce qu'une requête refusée ne doit jamais changer."""
        return {
            "reports": self.scalar("SELECT count(*) FROM reports"),
            "report_photos": self.scalar("SELECT count(*) FROM report_photos"),
            "devices": self.scalar("SELECT count(*) FROM devices"),
            "counters": {year: self.counter(year) for year in TEST_YEARS},
            "objects": sorted(self.objects()),
        }

    # --- Organisations de test -----------------------------------------------------------

    def organization(
        self, kind: str, zone_id: str, *, status: str = "active", created_at: datetime = FIXED_NOW
    ) -> UUID:
        org_id = uuid4()
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO organizations "
                    "(id, type, name, zone_id, status, is_demo, created_at, updated_at) "
                    "VALUES (:id, :type, :name, :zone_id, :status, false, :at, :at)"
                ),
                {
                    "id": org_id,
                    "type": kind,
                    "name": f"Test 1.11 {kind} {zone_id}",
                    "zone_id": zone_id,
                    "status": status,
                    "at": created_at,
                },
            )
        self.org_ids.append(org_id)
        return org_id

    # --- Nettoyage -----------------------------------------------------------------------

    def cleanup(self, existing_years: set[int]) -> None:
        owner_keys = [f"device:{_hash(device_id)}" for device_id in self.device_ids]
        with self.engine.begin() as conn:
            keys = conn.scalars(
                text(
                    "SELECT p.object_key FROM report_photos p JOIN reports r "
                    "ON r.id = p.report_id WHERE r.owner_key = ANY(:keys)"
                ),
                {"keys": owner_keys},
            ).all()
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
            conn.execute(
                text("DELETE FROM organizations WHERE id = ANY(:ids)"), {"ids": self.org_ids}
            )
            for year in set(TEST_YEARS) - existing_years:
                # Compteur créé par les tests : retiré s'il ne numérote plus rien.
                conn.execute(
                    text(
                        "DELETE FROM tracking_counters WHERE year = :y AND NOT EXISTS "
                        "(SELECT 1 FROM reports WHERE tracking_number LIKE :prefix)"
                    ),
                    {"y": year, "prefix": f"TC-{year}-%"},
                )
        for key in {*keys, *self.objects()}:
            try:
                self.s3.delete_object(Bucket=self.bucket, Key=key)
            except Exception as exc:
                print(f"nettoyage impossible : {key} ({type(exc).__name__})")


@pytest.fixture
def stack(monkeypatch: pytest.MonkeyPatch) -> Iterator[Stack]:
    endpoint = _env("TEST_S3_ENDPOINT")
    access_key = _env("TEST_S3_ACCESS_KEY_ID")
    secret_key = _env("TEST_S3_SECRET_ACCESS_KEY")
    bucket = os.environ.get("TEST_S3_BUCKET", "").strip() or DEFAULT_BUCKET
    region = os.environ.get("TEST_S3_REGION", "").strip() or "garage"
    database_url = make_url(_env("TEST_APP_DATABASE_URL"))
    if database_url.drivername in ("postgresql", "postgres"):
        database_url = database_url.set(drivername="postgresql+psycopg")

    # L'application lit ses réglages dans Settings (environnement).
    for name, value in {
        "ENV": "dev",
        "DEMO_MODE": "false",
        "DATABASE_URL": database_url.render_as_string(hide_password=False),
        "S3_ENDPOINT": endpoint,
        "S3_ACCESS_KEY_ID": access_key,
        "S3_SECRET_ACCESS_KEY": secret_key,
        "S3_BUCKET": bucket,
        "S3_REGION": region,
        "DEVICE_ID_PEPPER": TEST_PEPPER,
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(clock, "now", lambda: FIXED_NOW)
    caches = (get_settings, db.get_engine, db.get_sessionmaker, storage._s3_client)
    for cache in caches:
        cache.cache_clear()

    engine = create_engine(database_url, hide_parameters=True)
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
    target = Stack(app=create_app(get_settings()), engine=engine, s3=s3, bucket=bucket)
    existing_years = {year for year in TEST_YEARS if target.counter(year) is not None}
    try:
        yield target
    finally:
        try:
            target.cleanup(existing_years)
        finally:
            engine.dispose()
            db.get_engine().dispose()
            for cache in caches:
                cache.cache_clear()


def _error(response: Response, status: int, code: ErrorCode) -> str:
    assert response.status == status, response.text
    body = response.json()
    assert set(body) == {"error"} and body["error"]["code"] == code.value, body
    return body["error"]["message"]


# --- Nominal -------------------------------------------------------------------------


def test_nominal_report_is_stored_completely(
    stack: Stack, capsys: pytest.CaptureFixture[str]
) -> None:
    device_id = stack.device()
    meta = report_meta(consent={"terms": True, "training": True})
    photo = sample_photo()
    capsys.readouterr()

    body = stack.created(stack.post(meta, photo, device_id=device_id))

    assert TRACKING_NUMBER.fullmatch(body["tracking_number"])
    assert body["tracking_number"].startswith("TC-2032-")
    assert body["status"] == "pending_review"
    assert body["received_at"] == "2032-05-10T08:30:00Z"
    assert body["is_demo"] is False

    row = stack.report(body["id"])
    device_hash = _hash(device_id)
    assert row.owner_key == f"device:{device_hash}"
    assert row.client_uuid == UUID(meta["client_uuid"])
    assert row.tracking_number == body["tracking_number"]
    assert row.status == "pending_review"
    assert (row.lat, row.lng) == pytest.approx(PLATEAU, abs=1e-9)
    assert row.accuracy_m == 12.5
    assert row.heap_size == "medium"
    assert row.comment == meta["comment"]
    assert row.citizen_type == "plastic"
    with Session(stack.engine) as session:
        zone = geo.zone_of(session, *PLATEAU)
    assert zone is not None and row.zone_id == zone.id
    assert row.received_at == FIXED_NOW
    assert row.client_captured_at == datetime(2032, 5, 10, 8, 29, 30, tzinfo=UTC)
    assert row.flag_imprecise_position is False
    assert row.training_consent is True
    assert row.is_demo is False
    # Aucune Organisation ne couvre le Plateau : l'Organisation plateforme.
    assert row.organization_id == PLATFORM_ORGANIZATION_ID

    (photo_row,) = stack.photos_of(body["id"])
    match = OBJECT_KEY.fullmatch(photo_row.object_key)
    assert match, photo_row.object_key
    assert photo_row.id == UUID(match.group(1))  # AD-13 : uuid de la clé = ligne photo
    assert photo_row.sha256 == hashlib.sha256(photo).hexdigest()
    assert (photo_row.width, photo_row.height) == (64, 48)
    assert photo_row.thumb_key is None
    stored = stack.s3.get_object(Bucket=stack.bucket, Key=photo_row.object_key)
    with Image.open(io.BytesIO(stored["Body"].read())) as image:
        assert image.format == "JPEG" and image.size == (64, 48)

    device = stack.device_row(device_id)
    assert device is not None
    assert device.training_consent is True
    assert device.consent_at == device.first_seen_at == FIXED_NOW

    # Ni identité, ni empreinte, ni Position, ni Organisation dans la réponse ou les journaux.
    out = capsys.readouterr().out
    for leaked in (device_id, device_hash, str(PLATEAU[0]), str(PLATEAU[1])):
        assert leaked not in out
        assert leaked not in json.dumps(body)
    assert str(PLATFORM_ORGANIZATION_ID) not in json.dumps(body)
    created = [json.loads(line) for line in out.splitlines() if '"report_created"' in line]
    assert len(created) == 1
    assert created[0]["report_id"] == body["id"]
    assert created[0]["tracking_number"] == body["tracking_number"]
    access = [json.loads(line) for line in out.splitlines() if '"event": "request"' in line]
    assert [(line["route"], line["status"], line["role"]) for line in access] == [
        ("/v1/reports", 201, "device")
    ]


def test_known_device_is_updated(stack: Stack, monkeypatch: pytest.MonkeyPatch) -> None:
    device_id = stack.device()
    first, second, third = (
        FIXED_NOW,
        datetime(2032, 5, 10, 9, 0, tzinfo=UTC),
        datetime(2032, 5, 10, 10, 0, tzinfo=UTC),
    )
    for moment, training in ((first, False), (second, True), (third, True)):
        monkeypatch.setattr(clock, "now", lambda moment=moment: moment)
        meta = report_meta(consent={"terms": True, "training": training})
        stack.created(stack.post(meta, device_id=device_id))
    device = stack.device_row(device_id)
    assert device.first_seen_at == first
    assert device.training_consent is True
    # Le choix a changé à la deuxième création, pas à la troisième.
    assert device.consent_at == second
    rows = stack.scalar("SELECT count(*) FROM devices WHERE device_hash = :h", h=_hash(device_id))
    assert rows == 1


# --- Refus : rien n'est écrit ------------------------------------------------------------


@pytest.mark.parametrize(
    ("meta", "with_photo", "named"),
    [
        (report_meta(), False, "photo"),
        (report_meta(lat=MISSING), True, "meta.lat"),
        (report_meta(heap_size=MISSING), True, "meta.heap_size"),
    ],
    ids=["sans-photo", "sans-lat", "sans-taille"],
)
def test_missing_field_is_named_and_nothing_is_written(
    stack: Stack, meta: dict[str, Any], with_photo: bool, named: str
) -> None:
    before = stack.footprint()
    photo = sample_photo() if with_photo else None
    response = post_report(stack.app, stack.device(), meta, photo)
    assert named in _error(response, 422, ErrorCode.VALIDATION_ERROR)
    assert stack.footprint() == before


def test_comment_of_280_code_points_is_accepted_281_refused(stack: Stack) -> None:
    emoji = "\U0001f5d1"
    comment = "Sacs " + emoji * 5 + "x" * 270
    assert len(comment) == 280
    body = stack.created(stack.post(report_meta(comment=comment)))
    row = stack.report(body["id"])
    assert row.comment == comment and row.comment_chars == 280

    before = stack.footprint()
    message = _error(
        stack.post(report_meta(comment=comment + emoji)), 422, ErrorCode.VALIDATION_ERROR
    )
    assert "meta.comment" in message
    assert stack.footprint() == before


@pytest.mark.parametrize(
    "overrides",
    [
        {"lat": 91},
        {"lng": -181},
        {"accuracy_m": 0},
        {"accuracy_m": -1},
        {"heap_size": "huge"},
        {"waste_type": "paper"},
    ],
    ids=["lat-91", "lng-181", "precision-0", "precision-1", "taille", "type"],
)
def test_out_of_bounds_is_422_and_nothing_is_written(
    stack: Stack, overrides: dict[str, Any]
) -> None:
    before = stack.footprint()
    _error(stack.post(report_meta(**overrides)), 422, ErrorCode.VALIDATION_ERROR)
    assert stack.footprint() == before


@pytest.mark.parametrize(
    "consent",
    [MISSING, {"training": True}, {"terms": False, "training": False}],
    ids=["consentement-absent", "conditions-absentes", "conditions-refusees"],
)
def test_without_terms_consent_is_422_and_nothing_is_written(stack: Stack, consent: Any) -> None:
    before = stack.footprint()
    _error(stack.post(report_meta(consent=consent)), 422, ErrorCode.CONSENT_REQUIRED)
    assert stack.footprint() == before


@pytest.mark.parametrize(
    "device_id",
    [None, "A" * 42, "A" * 42 + "+"],
    ids=["absent", "42-caracteres", "hors-base64url"],
)
def test_invalid_device_id_is_400_and_nothing_is_written(
    stack: Stack, device_id: str | None
) -> None:
    before = stack.footprint()
    response = post_report(stack.app, device_id, report_meta(), sample_photo())
    _error(response, 400, ErrorCode.INVALID_DEVICE_ID)
    assert stack.footprint() == before


def test_authorization_header_is_401_and_nothing_is_written(stack: Stack) -> None:
    before = stack.footprint()
    response = stack.post(headers={"Authorization": "Bearer x"})
    _error(response, 401, ErrorCode.INVALID_TOKEN)
    assert stack.footprint() == before


def test_outside_the_active_zone_is_422_and_nothing_is_written(stack: Stack) -> None:
    before = stack.footprint()
    response = stack.post(report_meta(lat=THIES[0], lng=THIES[1]))
    message = _error(response, 422, ErrorCode.OUTSIDE_ACTIVE_ZONE)
    assert message == DEFAULT_MESSAGES[ErrorCode.OUTSIDE_ACTIVE_ZONE]
    assert message.startswith("TerangaCycle n'est pas encore actif ici")
    assert stack.footprint() == before


def _padded(size: int) -> bytes:
    data = photos.encoded("PNG")
    return data + b"\x00" * (size - len(data))


@pytest.mark.parametrize(
    ("photo", "status", "code"),
    [
        (photos.encoded("GIF"), 415, ErrorCode.UNSUPPORTED_MEDIA_TYPE),
        (_padded(1_048_577), 413, ErrorCode.PHOTO_TOO_LARGE),
        (_padded(3 * 1_048_576), 413, ErrorCode.PHOTO_TOO_LARGE),
        (b"\xff\xd8\xff\xe0" + os.urandom(4096), 422, ErrorCode.PHOTO_UNREADABLE),
    ],
    ids=["gif", "1-mo-plus-1", "3-mo", "illisible"],
)
def test_refused_photo_leaves_neither_row_nor_object(
    stack: Stack, photo: bytes, status: int, code: ErrorCode
) -> None:
    before = stack.footprint()
    _error(stack.post(photo=photo), status, code)
    assert stack.footprint() == before


def test_failure_after_storage_rolls_back_and_deletes_the_object(
    stack: Stack, monkeypatch: pytest.MonkeyPatch
) -> None:
    stored_keys: list[str] = []
    original_ingest = storage.ingest_photo

    def spying_ingest(*args: Any) -> storage.StoredPhoto:
        stored = original_ingest(*args)
        stored_keys.append(stored.object_key)
        assert stored.object_key in stack.objects()  # écrit pendant l'unité
        return stored

    def failing_insert(*args: Any) -> None:
        raise Boom("échec tardif")

    monkeypatch.setattr(storage, "ingest_photo", spying_ingest)
    monkeypatch.setattr(reports_repository, "insert_photo", failing_insert)
    before = stack.footprint()
    _error(stack.post(), 500, ErrorCode.INTERNAL_ERROR)
    assert len(stored_keys) == 1
    assert stored_keys[0] not in stack.objects()
    assert stack.footprint() == before


# --- Organisation responsable -------------------------------------------------------------


def _commune_points(stack: Stack, count: int) -> list[tuple[str, float, float]]:
    """Communes d'arrondissement sans Organisation, avec un point intérieur à chacune,
    dans la Zone active et couvert par cette seule commune d'arrondissement."""
    with stack.engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT c.id, ST_Y(p.pt) AS lat, ST_X(p.pt) AS lng
                FROM zones c
                CROSS JOIN LATERAL (SELECT ST_PointOnSurface(c.geog::geometry) AS pt) p
                WHERE c.kind = 'commune' AND c.parent_id IS NOT NULL
                  AND ST_Covers((SELECT geog FROM zones WHERE id = 'dakar'), p.pt::geography)
                  AND NOT EXISTS (
                      SELECT 1 FROM zones o
                      WHERE o.kind = 'commune' AND o.parent_id IS NOT NULL AND o.id <> c.id
                        AND ST_Covers(o.geog, p.pt::geography))
                  AND NOT EXISTS (
                      SELECT 1 FROM organizations g JOIN zones z ON z.id = g.zone_id
                      WHERE ST_Covers(z.geog, p.pt::geography))
                ORDER BY c.id
                LIMIT :count
                """
            ),
            {"count": count},
        ).all()
    assert len(rows) == count, "pas assez de communes d'arrondissement libres"
    return [(row.id, row.lat, row.lng) for row in rows]


def test_reports_go_to_their_commune_or_to_the_platform(stack: Stack) -> None:
    (c1, *p1), (c2, *p2), (_c3, *p3) = _commune_points(stack, 3)
    org1 = stack.organization("commune", c1)
    org2 = stack.organization("commune", c2)

    expected = {}
    for point, org in ((p1, org1), (p2, org2), (p3, PLATFORM_ORGANIZATION_ID)):
        body = stack.created(stack.post(report_meta(lat=point[0], lng=point[1])))
        assert "organization_id" not in body
        assert str(org) not in json.dumps(body)
        expected[body["id"]] = org
    for report_id, org in expected.items():
        assert stack.report(report_id).organization_id == org


def test_most_precise_active_commune_or_operator_wins(stack: Stack) -> None:
    with stack.engine.connect() as conn:
        # Un quartier, un point intérieur couvert par sa seule commune d'arrondissement.
        quartier = conn.execute(
            text(
                """
                SELECT q.id, q.parent_id, ST_Y(p.pt) AS lat, ST_X(p.pt) AS lng FROM zones q
                CROSS JOIN LATERAL (SELECT ST_PointOnSurface(q.geog::geometry) AS pt) p
                WHERE q.kind = 'quartier'
                  AND ST_Covers((SELECT geog FROM zones WHERE id = q.parent_id), p.pt::geography)
                  AND NOT EXISTS (
                      SELECT 1 FROM zones o
                      WHERE o.kind = 'commune' AND o.parent_id IS NOT NULL
                        AND o.id <> q.parent_id AND ST_Covers(o.geog, p.pt::geography))
                ORDER BY q.id LIMIT 1
                """
            )
        ).one()
    c1 = quartier.parent_id
    (_c3, *p3) = next(point for point in _commune_points(stack, 3) if point[0] != c1)
    early = datetime(2032, 1, 1, tzinfo=UTC)
    # Plus anciennes mais écartées : suspendue, ou d'un type qui ne reçoit pas de Signalement.
    stack.organization("commune", quartier.id, status="suspended", created_at=early)
    stack.organization("collector_group", quartier.id, created_at=early)
    stack.organization("commune", c1)
    operator = stack.organization("operator", quartier.id)
    city = stack.organization("commune", "dakar")

    in_quartier = stack.created(stack.post(report_meta(lat=quartier.lat, lng=quartier.lng)))
    elsewhere = stack.created(stack.post(report_meta(lat=p3[0], lng=p3[1])))
    # Quartier avant commune ; à défaut de commune d'arrondissement, la ville.
    assert stack.report(in_quartier["id"]).organization_id == operator
    assert stack.report(elsewhere["id"]).organization_id == city


# --- Numéro de suivi ------------------------------------------------------------------------


def test_twenty_simultaneous_reports_get_twenty_distinct_numbers(stack: Stack) -> None:
    count = 20
    devices = [stack.device() for _ in range(count)]
    barrier = threading.Barrier(count)

    def send(device_id: str) -> Response:
        barrier.wait(timeout=30)
        return stack.post(device_id=device_id)

    with ThreadPoolExecutor(max_workers=count) as pool:
        responses = list(pool.map(send, devices))
    numbers = [stack.created(response)["tracking_number"] for response in responses]
    assert len(set(numbers)) == count
    assert all(TRACKING_NUMBER.fullmatch(number) for number in numbers)
    stored = stack.scalar(
        "SELECT count(DISTINCT tracking_number) FROM reports WHERE tracking_number = ANY(:n)",
        n=numbers,
    )
    assert stored == count


def test_tracking_year_follows_the_utc_clock(stack: Stack, monkeypatch: pytest.MonkeyPatch) -> None:
    leftover = stack.scalar("SELECT count(*) FROM reports WHERE tracking_number LIKE 'TC-2027-%'")
    if leftover:
        pytest.fail("des Signalements de 2027 existent déjà : test impossible sur cette base")
    with stack.engine.begin() as conn:
        conn.execute(text("DELETE FROM tracking_counters WHERE year = 2027"))

    monkeypatch.setattr(clock, "now", lambda: datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC))
    last = stack.created(stack.post())
    monkeypatch.setattr(clock, "now", lambda: datetime(2027, 1, 1, 0, 0, 0, tzinfo=UTC))
    first = stack.created(stack.post())

    assert last["tracking_number"].startswith("TC-2026-")
    assert last["received_at"] == "2026-12-31T23:59:59Z"
    assert first["tracking_number"] == "TC-2027-000001"
    assert first["received_at"] == "2027-01-01T00:00:00Z"


# --- Drapeau et démonstration ----------------------------------------------------------------


@pytest.mark.parametrize(("accuracy_m", "flagged"), [(51, True), (50, False)])
def test_imprecise_position_flag(stack: Stack, accuracy_m: float, flagged: bool) -> None:
    body = stack.created(stack.post(report_meta(accuracy_m=accuracy_m)))
    row = stack.report(body["id"])
    assert row.flag_imprecise_position is flagged
    assert row.accuracy_m == accuracy_m


@pytest.mark.parametrize("demo_mode", [True, False])
def test_is_demo_follows_demo_mode(
    stack: Stack, monkeypatch: pytest.MonkeyPatch, demo_mode: bool
) -> None:
    monkeypatch.setenv("DEMO_MODE", "true" if demo_mode else "false")
    get_settings.cache_clear()
    body = stack.created(stack.post())
    assert body["is_demo"] is demo_mode
    assert stack.report(body["id"]).is_demo is demo_mode
