"""Seul `core.storage` parle S3, plus la sonde `/readyz` de `core.health` (story 1.10).

Analyse AST de tout le code Python du backend (application, migrations, scripts) : aucun
import de `boto3` ni de `botocore` hors de `app/core/storage.py` et `app/core/health.py`.
Le contrat import-linter `s3_access` le vérifie aussi, pour le seul paquet `app`.
"""

import ast
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]
SCANNED = ("app", "migrations", "scripts")
ALLOWED = {Path("app/core/storage.py"), Path("app/core/health.py")}
S3_PACKAGES = {"boto3", "botocore"}


def s3_imports(source: str) -> list[tuple[int, str]]:
    """(ligne, module) de chaque import de boto3 ou botocore."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module]
        else:
            continue
        found += [(node.lineno, name) for name in names if name.split(".")[0] in S3_PACKAGES]
    return found


def _python_files() -> list[Path]:
    return sorted(
        path.relative_to(BACKEND)
        for directory in SCANNED
        for path in (BACKEND / directory).rglob("*.py")
    )


def test_only_storage_and_the_probe_import_boto3() -> None:
    offenders = {
        str(path): imports
        for path in _python_files()
        if path not in ALLOWED
        and (imports := s3_imports((BACKEND / path).read_text(encoding="utf-8")))
    }
    assert not offenders, f"S3 hors de core.storage : {offenders}"


def test_storage_does_use_boto3() -> None:
    source = (BACKEND / "app" / "core" / "storage.py").read_text(encoding="utf-8")
    assert {name for _, name in s3_imports(source)} >= {"boto3"}


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("import boto3", [(1, "boto3")]),
        ("import os, botocore.config", [(1, "botocore.config")]),
        ("from botocore.exceptions import ClientError", [(1, "botocore.exceptions")]),
        ("def f():\n    import boto3.session", [(2, "boto3.session")]),
        ("import boto3x\nfrom . import boto3\nfrom app.core import storage", []),
    ],
)
def test_detector(source: str, expected: list[tuple[int, str]]) -> None:
    assert s3_imports(source) == expected
