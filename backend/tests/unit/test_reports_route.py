"""`POST /v1/reports` sans base (story 1.11) : principal, forme de `meta`, champs nommés,
et règles pures (Numéro de suivi, drapeau de précision, étiquette démo).

Les contrôles faits avant le service ne touchent ni la base ni le stockage. L'unité de
travail ouverte par la route tourne sur un SQLite en mémoire ; le service est remplacé
quand un test doit le traverser. Le parcours complet est testé sur PostGIS et Garage
réels par `tests/integration/test_reports_create.py`.
"""

import json
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import db, demo
from app.core.config import Settings
from app.core.security import device_hash, is_valid_device_id, resolve_principal
from app.core.storage import MAX_PHOTO_BYTES
from app.main import create_app
from app.modules.reports import service
from app.modules.reports.router import parse_meta
from tests.reports_support import meta, new_device_id, post_report
from tests.support import sample_active_zone


@pytest.fixture
def app(
    make_settings: Callable[..., Settings], monkeypatch: pytest.MonkeyPatch
) -> Iterator[FastAPI]:
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    monkeypatch.setattr(
        db, "get_sessionmaker", lambda: sessionmaker(bind=engine, expire_on_commit=False)
    )
    application = create_app(make_settings())
    application.state.active_zone = sample_active_zone()
    yield application
    engine.dispose()


@pytest.fixture
def service_calls(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    """Remplace le service : la route est testée seule, sans base ni stockage."""
    calls: list[Any] = []

    def fake_create(*args: Any) -> None:
        calls.append(args)
        raise AssertionError("le service ne doit pas être appelé")

    monkeypatch.setattr(service, "create", fake_create)
    return calls


def _error(response: Any, status: int, code: str) -> dict[str, Any]:
    assert response.status == status, response.text
    error = response.json()["error"]
    assert error["code"] == code
    return error


# --- Identifiant d'appareil et jeton -----------------------------------------------------


def test_generated_device_id_is_valid() -> None:
    raw = new_device_id()
    assert len(raw) == 43
    assert is_valid_device_id(raw)


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "A" * 42,
        "A" * 44,
        "A" * 42 + "+",  # alphabet base64 standard, pas base64url
        "A" * 42 + "=",
        "A" * 42 + "B",  # bits de remplissage non nuls : forme non canonique
        "é" * 43,
    ],
    ids=["vide", "42", "44", "plus", "egal", "non-canonique", "non-ascii"],
)
def test_invalid_device_ids_are_refused(raw: str) -> None:
    assert not is_valid_device_id(raw)


def test_device_hash_is_keyed_hex_and_stable() -> None:
    raw = new_device_id()
    first = device_hash(raw, "poivre-1")
    assert len(first) == 64 and int(first, 16) >= 0
    assert device_hash(raw, "poivre-1") == first
    assert device_hash(raw, "poivre-2") != first  # dépend du secret


def test_principal_owner_key_uses_hash_never_raw_id(make_settings: Callable[..., Settings]) -> None:
    raw = new_device_id()
    principal = resolve_principal(None, raw, make_settings())
    assert principal.kind == "device"
    assert principal.owner_key == f"device:{principal.device_hash}"
    assert raw not in principal.owner_key


def test_missing_device_id_is_400(app: FastAPI, service_calls: list[Any]) -> None:
    _error(post_report(app, device_id=None), 400, "invalid_device_id")
    assert service_calls == []


@pytest.mark.parametrize("raw", ["A" * 42, "A" * 42 + "+", "A" * 42 + "B"])
def test_malformed_device_id_is_400(app: FastAPI, service_calls: list[Any], raw: str) -> None:
    _error(post_report(app, device_id=raw), 400, "invalid_device_id")


def test_any_authorization_header_is_401_before_device_check(
    app: FastAPI, service_calls: list[Any]
) -> None:
    response = post_report(app, device_id=None, extra_headers={"authorization": "Bearer x"})
    _error(response, 401, "invalid_token")


def test_device_id_is_checked_before_the_body(app: FastAPI, service_calls: list[Any]) -> None:
    # Sans appareil et sans photo : l'identité est refusée d'abord.
    _error(post_report(app, device_id=None, photo=None, meta_value=None), 400, "invalid_device_id")


# --- Forme de la requête ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("kwargs", "field"),
    [
        ({"photo": None}, "photo"),
        ({"meta_value": None}, "meta"),
        ({"meta_value": meta(lat=...)}, "meta.lat"),
        ({"meta_value": meta(pile_size=...)}, "meta.pile_size"),
        ({"meta_value": meta(lng=...)}, "meta.lng"),
    ],
    ids=["sans-photo", "sans-meta", "sans-lat", "sans-taille", "sans-lng"],
)
def test_missing_field_is_named_in_422(
    app: FastAPI, service_calls: list[Any], kwargs: dict[str, Any], field: str
) -> None:
    error = _error(post_report(app, **kwargs), 422, "validation_error")
    assert field in error["message"]
    assert service_calls == []


def test_invalid_json_meta_is_422(app: FastAPI, service_calls: list[Any]) -> None:
    error = _error(post_report(app, meta_value="{pas du json"), 422, "validation_error")
    assert "meta" in error["message"]


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"lat": 91}, "meta.lat"),
        ({"lat": -90.5}, "meta.lat"),
        ({"lng": 181}, "meta.lng"),
        ({"accuracy_m": 0}, "meta.accuracy_m"),
        ({"accuracy_m": -1}, "meta.accuracy_m"),
        ({"pile_size": "huge"}, "meta.pile_size"),
        ({"waste_type": "paper"}, "meta.waste_type"),
        ({"client_uuid": "pas-un-uuid"}, "meta.client_uuid"),
        ({"captured_at": "2026-11-26T09:30:00"}, "meta.captured_at"),  # sans fuseau
        ({"inconnu": 1}, "meta (champ inconnu)"),
        ({"consent": {"terms": "oui"}}, "meta.consent.terms"),
    ],
)
def test_out_of_range_values_are_422(
    app: FastAPI, service_calls: list[Any], overrides: dict[str, Any], field: str
) -> None:
    error = _error(post_report(app, meta_value=meta(**overrides)), 422, "validation_error")
    assert field in error["message"]
    # Jamais la valeur reçue dans le message.
    assert "huge" not in error["message"] and "paper" not in error["message"]


def test_comment_limit_counts_code_points() -> None:
    emoji = "🗑️"[0]  # un seul point de code
    assert parse_meta(json.dumps(meta(comment=emoji * 280))).comment == emoji * 280
    assert parse_meta(json.dumps(meta(comment="é" * 280))).comment is not None
    with pytest.raises(Exception) as caught:
        parse_meta(json.dumps(meta(comment=emoji * 281)))
    assert "meta.comment" in str(caught.value)


def test_absent_consent_parses_as_refused() -> None:
    assert parse_meta(json.dumps(meta(consent=...))).consent.terms is False
    assert parse_meta(json.dumps(meta(consent={"training": True}))).consent.terms is False


def test_valid_request_reaches_the_service(app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def fake_create(principal: Any, report_meta: Any, data: bytes, settings: Any) -> Any:
        seen.update(principal=principal, meta=report_meta, size=len(data))
        raise service_error

    from app.core.errors import DomainError, ErrorCode

    service_error = DomainError(ErrorCode.OUTSIDE_ACTIVE_ZONE, 422)
    monkeypatch.setattr(service, "create", fake_create)
    error = _error(post_report(app), 422, "outside_active_zone")
    assert error["message"] == "TerangaCycle n'est pas encore actif ici."
    assert seen["principal"].kind == "device"
    assert seen["meta"].pile_size.value == "medium"
    assert seen["size"] > 0


def test_photo_is_read_with_a_bounded_size(app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    sizes: list[int] = []

    def fake_create(principal: Any, report_meta: Any, data: bytes, settings: Any) -> Any:
        sizes.append(len(data))
        raise AssertionError

    monkeypatch.setattr(service, "create", fake_create)
    post_report(app, photo=b"\xff\xd8\xff" + b"\x00" * 3_000_000)
    assert sizes == [MAX_PHOTO_BYTES + 1]


# --- Règles pures -----------------------------------------------------------------------


def test_tracking_number_format() -> None:
    assert service.tracking_number(2026, 1) == "TC-2026-000001"
    assert service.tracking_number(2027, 4217) == "TC-2027-004217"


@pytest.mark.parametrize(("accuracy", "flag"), [(12, False), (50, False), (50.2, True), (51, True)])
def test_imprecise_flag_is_strictly_above_threshold(accuracy: float, flag: bool) -> None:
    assert service.is_imprecise(accuracy, 50) is flag


def test_demo_flag_follows_demo_mode(make_settings: Callable[..., Settings]) -> None:
    assert demo.flag(settings=make_settings(demo_mode=False)) is False
    assert demo.flag(settings=make_settings(demo_mode=True)) is True
    assert demo.flag(True, settings=make_settings(demo_mode=False)) is True


def test_route_is_documented_as_multipart(app: FastAPI) -> None:
    operation = app.openapi()["paths"]["/v1/reports"]["post"]
    assert "multipart/form-data" in operation["requestBody"]["content"]
    assert "201" in operation["responses"]


def test_unknown_field_name_is_never_echoed(app: FastAPI, service_calls: list[Any]) -> None:
    error = _error(
        post_report(app, meta_value=meta(**{"<script>secret": 1})), 422, "validation_error"
    )
    assert "secret" not in error["message"]


@pytest.mark.parametrize(
    ("comment", "expected"),
    [("   ", None), ("", None), ("Près du marché", "Près du marché")],
    ids=["blancs", "vide", "texte"],
)
def test_blank_comment_is_no_comment(comment: str, expected: str | None) -> None:
    assert parse_meta(json.dumps(meta(comment=comment))).comment == expected


def test_nul_character_in_comment_is_422(app: FastAPI, service_calls: list[Any]) -> None:
    error = _error(post_report(app, meta_value=meta(comment="a\u0000b")), 422, "validation_error")
    assert "meta.comment" in error["message"]
