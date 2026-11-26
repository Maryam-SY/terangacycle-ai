"""Arborescence de l'épine (AD-1) et épinglage des dépendances (story 1.1, AC 1)."""

import re
import tomllib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
BACKEND = REPO / "backend"

CORE_MODULES = [
    "config",
    "db",
    "logging",
    "clock",
    "enums",
    "http",
    "health",
    "public",
    "geo",
    "storage",
    "security",
    "demo",
]
BUSINESS_MODULES = ["auth", "reports", "missions", "lots", "analytics", "ai", "notifications"]

EXPECTED_FILES = [
    *(f"backend/app/core/{name}.py" for name in CORE_MODULES),
    # Erreurs : paquet (enveloppe et gestionnaires) et énumération des codes (AD-11).
    "backend/app/core/errors/__init__.py",
    "backend/app/core/errors/codes.py",
    *(f"backend/app/modules/{name}/__init__.py" for name in BUSINESS_MODULES),
    "backend/app/reactions.py",
    "backend/app/main.py",
    "backend/app/worker.py",
    "backend/alembic.ini",
    "backend/migrations/env.py",
    "backend/pyproject.toml",
    "backend/uv.lock",
    "backend/Dockerfile",
    "infra/docker-compose.yml",
    "infra/Caddyfile",
    "compose.yaml",
]

EXPECTED_DIRS = [
    "backend/scripts",
    *(f"backend/tests/{kind}" for kind in ["unit", "integration", "authz", "architecture"]),
    "ml/contract",
    "ml/release",
    "infra/seed",
    ".github/workflows",
]


@pytest.mark.parametrize("relpath", EXPECTED_FILES)
def test_expected_file_exists(relpath: str) -> None:
    assert (REPO / relpath).is_file(), f"fichier manquant : {relpath}"


@pytest.mark.parametrize("relpath", EXPECTED_DIRS)
def test_expected_dir_exists(relpath: str) -> None:
    assert (REPO / relpath).is_dir(), f"dossier manquant : {relpath}"


def _pyproject() -> dict:
    return tomllib.loads((BACKEND / "pyproject.toml").read_text(encoding="utf-8"))


def _all_requirements() -> list[str]:
    data = _pyproject()
    groups = data.get("dependency-groups", {})
    return [*data["project"]["dependencies"], *(r for g in groups.values() for r in g)]


def test_every_dependency_is_pinned_exactly() -> None:
    unpinned = [r for r in _all_requirements() if not re.search(r"==[0-9]", r)]
    assert not unpinned, f"dépendances non épinglées : {unpinned}"


def test_no_forbidden_dependency() -> None:
    # Ni SQLModel ni starter full-stack (décision de l'épine).
    names = [re.split(r"[\[=<>~!; ]", r, maxsplit=1)[0].lower() for r in _all_requirements()]
    assert "sqlmodel" not in names


def test_reactions_module_is_empty() -> None:
    source = (BACKEND / "app" / "reactions.py").read_text(encoding="utf-8")
    code = [
        line
        for line in source.splitlines()
        if line.strip() and not line.lstrip().startswith(("#", '"""'))
    ]
    assert code == [], "reactions.py doit rester vide à ce stade"
