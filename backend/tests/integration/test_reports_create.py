"""`POST /v1/reports` sur PostGIS et Garage réels (story 1.11) : une ligne de test par
ligne de la matrice de la spec.

Exige la pile démarrée et migrée (`0003_reports`), `TEST_APP_DATABASE_URL` (rôle
teranga_app) et les variables `TEST_S3_*` (voir `test_storage_garage.py`). Sans elles,
les tests sont ignorés, sauf avec `REQUIRE_INTEGRATION=1` (CI) : ils échouent alors.

Chaque test retire ce qu'il a créé (lignes et objets) ; le compteur de 2027 est remis à
zéro avant le test du changement d'année.
"""

import os
import re
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import FastAPI
from sqlalchemy import Engine, create_engine, make_url, text

from app.core import db, storage
from app.core.config import get_settings
from app.main import create_app
from app.modules.reports import service
from tests.asgi import Response
from tests.photos import encode, noise
from tests.reports_support import THIES, meta, new_device_id, post_report, small_jpeg
from tests.support import sample_active_zone

pytestmark = pytest.mark.integration

_S3_VARS = {
    "S3_ENDPOINT": "TEST_S3_ENDPOINT",
    "S3_BUCKET": "TEST_S3_BUCKET",
    "S3_ACCESS_KEY_ID": "TEST_S3_ACCESS_KEY_ID",
    "S3_SECRET_ACCESS_KEY": "TEST_S3_SECRET_ACCESS_KEY",
}
TRACKING = re.compile(r"^TC-(\d{4})-(\d{6})$")


def _required(var: str) -> str:
    value = os.environ.get(var)
    if not value:
        pytest.skip(f"{var} non défini : tests d'intégration ignorés")
    return value


def _clear_caches() -> None:
    get_settings.cache_clear()
    db.get_engine.cache_clear()
    db.get_sessionmaker.cache_clear()
    storage._s3_client.cache_clear()


@pytest.fixture
def stack(monkeypatch: pytest.MonkeyPatch) -> Iterator[Engine]:
    """Réglages pointés sur la pile (base, Garage) ; renvoie un moteur de vérification."""
    url = make_url(_required("TEST_APP_DATABASE_URL"))
    if url.drivername in ("postgresql", "postgres"):
        url = url.set(drivername="postgresql+psycopg")
    monkeypatch.setenv("DATABASE_URL", url.render_as_string(hide_password=False))
    for setting, var in _S3_VARS.items():
        monkeypatch.setenv(setting, _required(var))
    _clear_caches()
    engine = create_engine(url, hide_parameters=True)
    try:
        yield engine
    finally:
        engine.dispose()
        _clear_caches()


@pytest.fixture
def make_app(stack: Engine, monkeypatch: pytest.MonkeyPatch) -> Callable[..., FastAPI]:
    def factory(demo_mode: bool = False) -> FastAPI:
        monkeypatch.setenv("DEMO_MODE", "true" if demo_mode else "false")
        get_settings.cache_clear()
        app = create_app(get_settings())
        app.state.active_zone = sample_active_zone()
        return app

    return factory


@pytest.fixture
def created(stack: Engine) -> Iterator[list[str]]:
    """Numéros de suivi créés par le test : lignes et objets retirés à la fin."""
    numbers: list[str] = []
    yield numbers
    if not numbers:
        return
    client, bucket = storage._client_and_bucket()
    with stack.begin() as conn:
        keys = conn.execute(
            text(
                "SELECT p.object_key FROM report_photos p JOIN reports r ON r.id = p.report_id "
                "WHERE r.tracking_number = ANY(:numbers)"
            ),
            {"numbers": numbers},
        ).scalars()
        for key in list(keys):
            client.delete_object(Bucket=bucket, Key=key)
        owners = conn.execute(
            text("SELECT owner_key FROM reports WHERE tracking_number = ANY(:numbers)"),
            {"numbers": numbers},
        ).scalars()
        hashes = [owner.removeprefix("device:") for owner in owners]
        conn.execute(
            text("DELETE FROM reports WHERE tracking_number = ANY(:numbers)"), {"numbers": numbers}
        )
        conn.execute(
            text(
                "DELETE FROM devices d WHERE d.device_hash = ANY(:hashes) AND NOT EXISTS "
                "(SELECT 1 FROM reports r WHERE r.owner_key = 'device:' || d.device_hash)"
            ),
            {"hashes": hashes},
        )


def _counts(engine: Engine) -> tuple[int, int, int]:
    """(Signalements, photos, objets du bucket)."""
    client, bucket = storage._client_and_bucket()
    pages = client.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix="report/")
    objects = sum(page.get("KeyCount", 0) for page in pages)
    with engine.connect() as conn:
        reports = conn.execute(text("SELECT count(*) FROM reports")).scalar_one()
        photos = conn.execute(text("SELECT count(*) FROM report_photos")).scalar_one()
    return reports, photos, objects


def _ok(response: Response, created: list[str]) -> dict[str, Any]:
    assert response.status == 201, response.text
    body = response.json()
    created.append(body["tracking_number"])
    return body


def _row(engine: Engine, number: str) -> Any:
    with engine.connect() as conn:
        return conn.execute(
            text(
                "SELECT r.*, ST_Y(r.geog::geometry) AS lat, ST_X(r.geog::geometry) AS lng, "
                "p.object_key, p.sha256, p.width, p.height, p.thumb_key "
                "FROM reports r JOIN report_photos p ON p.report_id = r.id "
                "WHERE r.tracking_number = :n"
            ),
            {"n": number},
        ).one()


# --- Nominal ------------------------------------------------------------------------------


def test_nominal_report_is_recorded(
    make_app: Callable[..., FastAPI], stack: Engine, created: list[str]
) -> None:
    app = make_app()
    device = new_device_id()
    sent = meta(comment="Près du marché")
    body = _ok(post_report(app, device_id=device, meta_value=sent), created)

    assert set(body) == {"id", "tracking_number", "status", "received_at", "is_demo"}
    assert TRACKING.fullmatch(body["tracking_number"])
    assert body["status"] == "pending_review"
    assert body["received_at"].endswith("Z")
    assert body["is_demo"] is False

    row = _row(stack, body["tracking_number"])
    assert row.owner_key.startswith("device:") and device not in row.owner_key
    assert row.status == "pending_review"
    assert row.pile_size == "medium" and row.citizen_type is None
    assert row.comment == "Près du marché"
    assert row.flag_imprecise_position is False
    assert row.training_consent is False
    assert str(row.client_uuid) == sent["client_uuid"]
    assert row.client_captured_at == datetime(2026, 11, 26, 9, 30, tzinfo=UTC)
    assert row.accuracy_m == 12
    with stack.connect() as conn:
        zone = conn.execute(
            text("SELECT id, kind, parent_id FROM zones WHERE id = :id"), {"id": row.zone_id}
        ).one()
    # Quartier de Dakar-Plateau s'il y en a un, sinon la commune elle-même.
    assert "dakar-plateau" in (zone.id, zone.parent_id)
    assert abs(row.lat - 14.6708) < 1e-6 and abs(row.lng + 17.4381) < 1e-6
    assert re.fullmatch(r"report/\d{4}/\d{2}/[0-9a-f-]{36}\.jpg", row.object_key)
    assert len(row.sha256) == 64 and row.width == 64 and row.height == 48
    assert row.thumb_key is None  # miniature : story différée

    with stack.connect() as conn:
        device_row = conn.execute(
            text("SELECT * FROM devices WHERE device_hash = :h"),
            {"h": row.owner_key.removeprefix("device:")},
        ).one()
    assert device_row.training_consent is False


def test_citizen_type_and_training_consent_are_kept(
    make_app: Callable[..., FastAPI], stack: Engine, created: list[str]
) -> None:
    body = _ok(
        post_report(
            make_app(),
            meta_value=meta(waste_type="plastic", consent={"terms": True, "training": True}),
        ),
        created,
    )
    row = _row(stack, body["tracking_number"])
    assert row.citizen_type == "plastic"
    assert row.training_consent is True


@pytest.mark.parametrize(("accuracy", "flag"), [(51, True), (50, False)])
def test_imprecise_position_flag(
    make_app: Callable[..., FastAPI], stack: Engine, created: list[str], accuracy: int, flag: bool
) -> None:
    body = _ok(post_report(make_app(), meta_value=meta(accuracy_m=accuracy)), created)
    assert _row(stack, body["tracking_number"]).flag_imprecise_position is flag


def test_comment_of_280_code_points_is_accepted(
    make_app: Callable[..., FastAPI], stack: Engine, created: list[str]
) -> None:
    comment = "🗑" * 280
    body = _ok(post_report(make_app(), meta_value=meta(comment=comment)), created)
    assert _row(stack, body["tracking_number"]).comment == comment


@pytest.mark.parametrize("demo_mode", [True, False])
def test_demo_label_follows_demo_mode(
    make_app: Callable[..., FastAPI], stack: Engine, created: list[str], demo_mode: bool
) -> None:
    body = _ok(post_report(make_app(demo_mode=demo_mode)), created)
    assert body["is_demo"] is demo_mode
    assert _row(stack, body["tracking_number"]).is_demo is demo_mode


# --- Refus : rien n'est écrit -------------------------------------------------------------


@pytest.mark.parametrize(
    ("kwargs", "status", "code"),
    [
        ({"photo": None}, 422, "validation_error"),
        ({"meta_value": meta(lat=...)}, 422, "validation_error"),
        ({"meta_value": meta(pile_size=...)}, 422, "validation_error"),
        ({"meta_value": meta(comment="🗑" * 281)}, 422, "validation_error"),
        ({"meta_value": meta(lat=91)}, 422, "validation_error"),
        ({"meta_value": meta(accuracy_m=0)}, 422, "validation_error"),
        ({"meta_value": meta(accuracy_m=-1)}, 422, "validation_error"),
        ({"meta_value": meta(pile_size="huge")}, 422, "validation_error"),
        ({"meta_value": meta(waste_type="paper")}, 422, "validation_error"),
        ({"meta_value": meta(consent={"terms": False, "training": True})}, 422, "consent_required"),
        ({"meta_value": meta(consent=...)}, 422, "consent_required"),
        ({"device_id": None}, 400, "invalid_device_id"),
        ({"device_id": "A" * 42}, 400, "invalid_device_id"),
        ({"device_id": "A" * 42 + "+"}, 400, "invalid_device_id"),
        ({"extra_headers": {"authorization": "Bearer x"}}, 401, "invalid_token"),
        ({"meta_value": meta(lat=THIES[0], lng=THIES[1])}, 422, "outside_active_zone"),
        ({"photo": encode(noise(8, 8), "GIF")}, 415, "unsupported_media_type"),
        ({"photo": b"\xff\xd8\xff" + b"\x00" * 1_100_000}, 413, "photo_too_large"),
    ],
    ids=[
        "sans-photo",
        "sans-lat",
        "sans-taille",
        "commentaire-281",
        "lat-91",
        "precision-0",
        "precision-negative",
        "taille-inconnue",
        "type-inconnu",
        "sans-consentement",
        "consentement-absent",
        "sans-appareil",
        "appareil-42",
        "appareil-hors-base64url",
        "jeton",
        "hors-zone",
        "gif",
        "trop-lourde",
    ],
)
def test_refused_request_writes_nothing(
    make_app: Callable[..., FastAPI],
    stack: Engine,
    kwargs: dict[str, Any],
    status: int,
    code: str,
) -> None:
    app = make_app()
    before = _counts(stack)
    response = post_report(app, **kwargs)
    assert response.status == status, response.text
    error = response.json()["error"]
    assert error["code"] == code
    if code == "outside_active_zone":
        assert error["message"] == "TerangaCycle n'est pas encore actif ici."
    assert _counts(stack) == before


def test_failure_after_storage_leaves_no_row_and_no_object(
    make_app: Callable[..., FastAPI], stack: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = make_app()

    class Boom(Exception):
        pass

    def failing_insert(photo: Any) -> None:
        raise Boom

    monkeypatch.setattr(service.repository, "insert_photo", failing_insert)
    before = _counts(stack)
    response = post_report(app)
    assert response.status == 500
    assert _counts(stack) == before


# --- Numéro de suivi ----------------------------------------------------------------------


def test_twenty_simultaneous_reports_get_distinct_numbers(
    make_app: Callable[..., FastAPI], created: list[str]
) -> None:
    app = make_app()
    with ThreadPoolExecutor(max_workers=20) as pool:
        responses = list(pool.map(lambda _: post_report(app, photo=small_jpeg()), range(20)))
    bodies = [_ok(response, created) for response in responses]
    numbers = {body["tracking_number"] for body in bodies}
    assert len(numbers) == 20


def test_tracking_year_is_the_utc_reception_year(
    make_app: Callable[..., FastAPI],
    stack: Engine,
    created: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = make_app()
    with stack.begin() as conn:
        conn.execute(text("DELETE FROM tracking_counters WHERE year = 2027"))

    monkeypatch.setattr(service, "now", lambda: datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC))
    last_2026 = _ok(post_report(app), created)["tracking_number"]
    monkeypatch.setattr(service, "now", lambda: datetime(2027, 1, 1, 0, 0, 0, tzinfo=UTC))
    first_2027 = _ok(post_report(app), created)["tracking_number"]

    assert last_2026.startswith("TC-2026-")
    assert first_2027 == "TC-2027-000001"
    with stack.begin() as conn:
        conn.execute(text("DELETE FROM tracking_counters WHERE year = 2027"))


# --- Confidentialité ----------------------------------------------------------------------


def test_no_position_device_id_or_hash_in_logs(
    make_app: Callable[..., FastAPI],
    stack: Engine,
    created: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    app = make_app()
    device = new_device_id()
    capsys.readouterr()
    accepted = post_report(app, device_id=device)
    body = _ok(accepted, created)
    refused = post_report(app, device_id=device, meta_value=meta(lat=THIES[0], lng=THIES[1]))
    captured = capsys.readouterr()
    owner_hash = _row(stack, body["tracking_number"]).owner_key.removeprefix("device:")
    exposed = captured.out + captured.err + accepted.text + refused.text
    for secret in (device, owner_hash, "14.6708", "17.4381", "14.791", "16.9359"):
        assert secret not in exposed


def test_same_device_updates_consent_only_on_change(
    make_app: Callable[..., FastAPI],
    stack: Engine,
    created: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = make_app()
    device = new_device_id()
    instants = [datetime(2026, 11, 26, 10, minute, tzinfo=UTC) for minute in (0, 5, 10)]
    choices = [False, False, True]
    numbers = []
    for instant, training in zip(instants, choices, strict=True):
        monkeypatch.setattr(service, "now", lambda instant=instant: instant)
        consent = {"terms": True, "training": training}
        numbers.append(
            _ok(post_report(app, device_id=device, meta_value=meta(consent=consent)), created)[
                "tracking_number"
            ]
        )
        device_hash = _row(stack, numbers[-1]).owner_key.removeprefix("device:")
        with stack.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM devices WHERE device_hash = :h"), {"h": device_hash}
            ).one()
        assert row.first_seen_at == instants[0]  # jamais modifiée
        assert row.training_consent is training  # dernier choix
        # Même choix : date gardée ; choix changé : date du changement.
        expected_consent_at = instants[2] if training else instants[0]
        assert row.consent_at == expected_consent_at
