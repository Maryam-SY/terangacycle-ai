"""Schéma `meta` de `POST /v1/reports` (story 1.11) : champs, bornes, commentaire."""

import json
from datetime import UTC, datetime
from typing import Any

import pytest

from app.core import clock
from app.core.enums import HeapSize, WasteType
from app.core.errors import DomainError, ErrorCode
from app.modules.reports.schemas import COMMENT_MAX_CHARS, ReportCreated, parse_meta
from tests.reports import MISSING, report_meta

# Emoji d'un seul point de code, hors du plan multilingue de base (deux unités UTF-16).
EMOJI = "\U0001f5d1"


def _refused(meta: dict[str, Any] | str) -> DomainError:
    raw = meta if isinstance(meta, str) else json.dumps(meta, ensure_ascii=False)
    with pytest.raises(DomainError) as exc_info:
        parse_meta(raw)
    error = exc_info.value
    assert (error.code, error.http_status) == (ErrorCode.VALIDATION_ERROR, 422)
    return error


def test_valid_meta() -> None:
    meta = parse_meta(json.dumps(report_meta()))
    assert meta.heap_size is HeapSize.MEDIUM
    assert meta.waste_type is WasteType.PLASTIC
    assert meta.consent is not None and meta.consent.terms is True
    assert meta.consent.training is False


def test_optional_fields_may_be_absent() -> None:
    meta = parse_meta(json.dumps(report_meta(comment=MISSING, waste_type=MISSING)))
    assert meta.comment is None and meta.waste_type is None
    meta = parse_meta(json.dumps(report_meta(comment=None, waste_type=None)))
    assert meta.comment is None and meta.waste_type is None


def test_absent_consent_is_left_to_the_consent_rule() -> None:
    """Conditions absentes ou refusées : le schéma laisse passer, le service répond
    `consent_required` (contrôle suivant)."""
    assert parse_meta(json.dumps(report_meta(consent=MISSING))).consent is None
    consent = parse_meta(json.dumps(report_meta(consent={"training": True}))).consent
    assert consent is not None and consent.terms is None
    meta = parse_meta(json.dumps(report_meta(consent={"terms": False, "training": False})))
    assert meta.consent is not None and meta.consent.terms is False


@pytest.mark.parametrize(
    "field",
    ["client_uuid", "lat", "lng", "accuracy_m", "heap_size", "captured_at"],
)
def test_missing_required_field_is_named(field: str) -> None:
    error = _refused(report_meta(**{field: MISSING}))
    assert f"meta.{field}" in error.message


def test_training_choice_is_required_with_the_consent() -> None:
    error = _refused(report_meta(consent={"terms": True}))
    assert "meta.consent.training" in error.message


@pytest.mark.parametrize(
    ("overrides", "named"),
    [
        ({"lat": 91}, "meta.lat"),
        ({"lat": -90.0001}, "meta.lat"),
        ({"lng": -181}, "meta.lng"),
        ({"lng": 180.5}, "meta.lng"),
        ({"accuracy_m": 0}, "meta.accuracy_m"),
        ({"accuracy_m": -1}, "meta.accuracy_m"),
        ({"heap_size": "huge"}, "meta.heap_size"),
        ({"heap_size": "Small"}, "meta.heap_size"),
        ({"waste_type": "paper"}, "meta.waste_type"),
        ({"client_uuid": "pas-un-uuid"}, "meta.client_uuid"),
        ({"captured_at": "2032-05-10T08:29:30"}, "meta.captured_at"),
        ({"lat": "14.67"}, "meta.lat"),
        ({"consent": {"terms": "true", "training": False}}, "meta.consent.terms"),
        ({"inconnu": 1}, "meta.inconnu"),
        ({"comment": "avant\x00après"}, "meta.comment"),
    ],
    ids=[
        "lat-91",
        "lat-sous-90",
        "lng-181",
        "lng-180.5",
        "precision-0",
        "precision-negative",
        "taille-inconnue",
        "taille-casse",
        "type-inconnu",
        "uuid",
        "heure-sans-fuseau",
        "lat-texte",
        "consentement-texte",
        "champ-inconnu",
        "caractere-nul",
    ],
)
def test_out_of_bounds_values_are_refused(overrides: dict[str, Any], named: str) -> None:
    error = _refused(report_meta(**overrides))
    assert named in error.message


def test_bounds_are_inclusive() -> None:
    meta = parse_meta(json.dumps(report_meta(lat=-90, lng=180, accuracy_m=0.01)))
    assert (meta.lat, meta.lng, meta.accuracy_m) == (-90, 180, 0.01)


@pytest.mark.parametrize("raw", ["", "pas du json", "[]", "3", "null", '{"lat": NaN}'])
def test_unreadable_meta_names_meta(raw: str) -> None:
    error = _refused(raw)
    assert "meta" in error.message


def test_comment_is_counted_in_code_points() -> None:
    at_limit = "a" * (COMMENT_MAX_CHARS - 10) + EMOJI * 10
    assert len(at_limit) == COMMENT_MAX_CHARS
    # 290 unités UTF-16 et 310 octets UTF-8, mais 280 points de code : accepté.
    assert len(at_limit.encode("utf-16-le")) // 2 > COMMENT_MAX_CHARS
    assert parse_meta(json.dumps(report_meta(comment=at_limit))).comment == at_limit
    error = _refused(report_meta(comment=at_limit + EMOJI))
    assert "meta.comment" in error.message


def test_refusal_never_echoes_the_value() -> None:
    secret_comment = "Kq9-" + "x" * 300
    error = _refused(report_meta(comment=secret_comment, lat=123.456))
    assert "Kq9" not in error.message and "123.456" not in error.message


def test_created_response_has_exactly_the_public_fields() -> None:
    assert set(ReportCreated.model_fields) == {
        "id",
        "tracking_number",
        "status",
        "received_at",
        "is_demo",
    }


@pytest.mark.parametrize(
    ("comment", "stored"),
    [("", None), ("   ", None), ("\n\t ", None), ("  Sacs  ", "Sacs"), ("a  b", "a  b")],
    ids=["vide", "espaces", "blancs", "bords", "interieur"],
)
def test_blank_comment_is_none_and_edges_are_stripped(comment: str, stored: str | None) -> None:
    assert parse_meta(json.dumps(report_meta(comment=comment))).comment == stored


def test_comment_limit_applies_after_stripping() -> None:
    at_limit = "x" * COMMENT_MAX_CHARS
    meta = parse_meta(json.dumps(report_meta(comment=f"   {at_limit}\n")))
    assert meta.comment == at_limit
    error = _refused(report_meta(comment=f" {at_limit}y "))
    assert "meta.comment" in error.message


@pytest.mark.parametrize(
    ("captured_at", "accepted"),
    [
        ("2000-01-01T00:00:00+00:00", True),
        ("1999-12-31T23:59:59+00:00", False),
        ("0001-01-01T00:00:00+00:00", False),
        ("2032-05-11T08:30:00+00:00", True),  # maintenant + 1 jour
        ("2032-05-11T08:30:01+00:00", False),
        ("9999-12-31T23:59:59+00:00", False),
        ("2032-05-11T09:30:00+01:00", True),  # même instant, autre fuseau
    ],
    ids=["2000", "1999", "an-1", "plus-1-jour", "au-dela", "an-9999", "fuseau"],
)
def test_captured_at_is_bounded(
    captured_at: str, accepted: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(clock, "now", lambda: datetime(2032, 5, 10, 8, 30, tzinfo=UTC))
    raw = json.dumps(report_meta(captured_at=captured_at))
    if accepted:
        assert parse_meta(raw).captured_at == datetime.fromisoformat(captured_at)
    else:
        assert "meta.captured_at" in _refused(raw).message
