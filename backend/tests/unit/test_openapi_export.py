"""Export de l'OpenAPI pour le client généré de la PWA (story 1.13).

`ReportMeta` publié dans `components.schemas`, champ `meta` du corps multipart qui y
renvoie (en JSON), photo binaire ; export stable et égal au fichier versionné
`web/src/api/openapi.json`.
"""

import importlib
import json
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from app.core.config import Settings
from app.core.enums import HeapSize, WasteType
from app.main import create_app
from app.modules.reports.router import document_report_body
from app.modules.reports.schemas import ReportMeta

BACKEND = Path(__file__).resolve().parents[2]
SCRIPTS = BACKEND / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

export_openapi: ModuleType = importlib.import_module("export_openapi")
VERSIONED = BACKEND.parent / "web" / "src" / "api" / "openapi.json"
REF = "#/components/schemas/"


@pytest.fixture
def openapi(make_settings: Callable[..., Settings]) -> dict[str, Any]:
    return create_app(make_settings()).openapi()


def _body(openapi: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    content = openapi["paths"]["/v1/reports"]["post"]["requestBody"]["content"]
    multipart = content["multipart/form-data"]
    name = multipart["schema"]["$ref"].removeprefix(REF)
    return multipart, openapi["components"]["schemas"][name]


def test_report_meta_and_its_schemas_are_published(openapi: dict[str, Any]) -> None:
    schemas = openapi["components"]["schemas"]
    for name in ("ReportMeta", "ReportConsent", "HeapSize", "WasteType"):
        assert name in schemas, name
    meta = schemas["ReportMeta"]
    assert set(meta["properties"]) == set(ReportMeta.model_fields)
    assert set(meta["required"]) == {
        "client_uuid",
        "lat",
        "lng",
        "accuracy_m",
        "heap_size",
        "captured_at",
    }
    assert meta["properties"]["heap_size"] == {"$ref": f"{REF}HeapSize"}
    assert set(schemas["HeapSize"]["enum"]) == {size.value for size in HeapSize}
    assert set(schemas["WasteType"]["enum"]) == {kind.value for kind in WasteType}
    assert set(schemas["ReportConsent"]["properties"]) == {"terms", "training"}
    # Aucune référence interne à Pydantic ne reste.
    assert "$defs" not in json.dumps(openapi)


def test_multipart_meta_points_to_report_meta_in_json(openapi: dict[str, Any]) -> None:
    multipart, body = _body(openapi)
    assert body["required"] == ["meta", "photo"]
    assert body["properties"]["meta"]["$ref"] == f"{REF}ReportMeta"
    assert multipart["encoding"] == {"meta": {"contentType": "application/json"}}
    assert body["properties"]["photo"]["format"] == "binary"


def test_post_processing_runs_once_and_is_cached(make_settings: Callable[..., Settings]) -> None:
    app = create_app(make_settings())
    first = app.openapi()
    assert app.openapi() is first
    assert app.openapi_schema is first


def test_post_processing_without_the_route_changes_nothing() -> None:
    openapi: dict[str, Any] = {"paths": {}, "components": {"schemas": {}}}
    assert document_report_body(openapi) == {"paths": {}, "components": {"schemas": {}}}


def test_conflicting_schema_name_is_refused(openapi: dict[str, Any]) -> None:
    # Un autre schéma du même nom qu'un schéma de `ReportMeta` : erreur explicite.
    openapi["components"]["schemas"]["HeapSize"] = {"type": "string", "enum": ["xs"]}
    with pytest.raises(RuntimeError, match="HeapSize"):
        document_report_body(openapi)


def test_two_exports_are_identical(tmp_path: Path) -> None:
    first = export_openapi.export(tmp_path / "a.json").read_bytes()
    second = export_openapi.export(tmp_path / "b.json").read_bytes()
    assert first == second
    assert first.endswith(b"}\n")
    assert b"\r\n" not in first
    assert json.loads(first)["openapi"].startswith("3.")


def test_versioned_file_matches_the_export(tmp_path: Path) -> None:
    exported = export_openapi.export(tmp_path / "openapi.json").read_bytes()
    assert VERSIONED.read_bytes() == exported, (
        "web/src/api/openapi.json n'est pas à jour : lancer "
        "`uv run python scripts/export_openapi.py` puis `npm run api:types` (web/)."
    )
