"""Chaque code d'erreur a un message traduit dans la PWA (AD-11, story 1.6).

Pour chaque `ErrorCode`, la clé `errors.<code>` existe et n'est pas vide dans
`web/src/i18n/fr.json` et `wo.json` ; l'échec nomme le code et le fichier. À l'inverse,
chaque clé `errors.*` de ces fichiers correspond à un `ErrorCode` (pas de clé orpheline).
"""

import json
from collections.abc import Iterable
from enum import StrEnum
from pathlib import Path
from typing import Any

import pytest

from app.core.errors.codes import ErrorCode

REPO = Path(__file__).resolve().parents[3]
I18N = REPO / "web" / "src" / "i18n"
CATALOGS = ["fr.json", "wo.json"]


def _load(name: str) -> dict[str, Any]:
    return json.loads((I18N / name).read_text(encoding="utf-8"))


def missing_messages(codes: Iterable[str], catalog: dict[str, Any], filename: str) -> list[str]:
    """Codes sans message `errors.<code>` non vide dans le catalogue donné."""
    errors = catalog.get("errors")
    errors = errors if isinstance(errors, dict) else {}
    missing = []
    for code in codes:
        value = errors.get(code)
        if not isinstance(value, str) or not value.strip():
            missing.append(f"{filename} : errors.{code} manquant ou vide")
    return missing


def orphan_messages(codes: Iterable[str], catalog: dict[str, Any], filename: str) -> list[str]:
    """Clés `errors.*` du catalogue sans code correspondant dans l'énumération."""
    errors = catalog.get("errors")
    keys = errors.keys() if isinstance(errors, dict) else ()
    known = set(codes)
    return [
        f"{filename} : errors.{key} ne correspond à aucun ErrorCode"
        for key in sorted(keys)
        if key not in known
    ]


@pytest.mark.parametrize("filename", CATALOGS)
def test_every_error_code_has_a_message(filename: str) -> None:
    missing = missing_messages((code.value for code in ErrorCode), _load(filename), filename)
    assert not missing, "\n".join(missing)


@pytest.mark.parametrize("filename", CATALOGS)
def test_every_error_message_has_a_code(filename: str) -> None:
    orphans = orphan_messages((code.value for code in ErrorCode), _load(filename), filename)
    assert not orphans, "\n".join(orphans)


def test_orphan_message_fails_and_names_key_and_file() -> None:
    catalog = _load("wo.json")
    catalog["errors"] = {**catalog["errors"], "rate_limited": "Réessayez plus tard."}
    orphans = orphan_messages((code.value for code in ErrorCode), catalog, "wo.json")
    assert orphans == ["wo.json : errors.rate_limited ne correspond à aucun ErrorCode"]


def test_extended_enum_fails_and_names_code_and_file() -> None:
    members = {code.name: code.value for code in ErrorCode} | {"RATE_LIMITED": "rate_limited"}
    extended = StrEnum("ExtendedErrorCode", members)
    for filename in CATALOGS:
        missing = missing_messages((code.value for code in extended), _load(filename), filename)
        assert missing == [f"{filename} : errors.rate_limited manquant ou vide"]


@pytest.mark.parametrize("catalog", [{}, {"errors": "x"}, {"errors": {"not_found": "  "}}])
def test_missing_or_blank_message_fails(catalog: dict[str, Any]) -> None:
    assert missing_messages(["not_found"], catalog, "fr.json") == [
        "fr.json : errors.not_found manquant ou vide"
    ]
