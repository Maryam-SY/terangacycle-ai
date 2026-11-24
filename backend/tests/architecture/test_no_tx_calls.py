"""Aucun service ni repository ne pilote la transaction (AD-17).

Analyse AST de `app/modules/**/service.py` et `repository.py` : aucun appel
`.commit(`, `.rollback(` ni `.begin(` ; seule l'unité de travail de `core.db` valide.
"""

import ast
from pathlib import Path

import pytest

MODULES = Path(__file__).resolve().parents[2] / "app" / "modules"
FORBIDDEN = {"commit", "rollback", "begin"}
LAYER_FILES = ("service.py", "repository.py")


def forbidden_calls(source: str) -> list[tuple[int, str]]:
    """(ligne, méthode) de chaque appel `<expr>.commit|rollback|begin(...)`."""
    return [
        (node.lineno, node.func.attr)
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in FORBIDDEN
    ]


def _layer_files() -> list[Path]:
    return sorted(p for name in LAYER_FILES for p in MODULES.rglob(name))


@pytest.mark.parametrize(
    "path", _layer_files() or [None], ids=lambda p: str(p.relative_to(MODULES)) if p else "aucun"
)
def test_no_transaction_control_in_services_and_repositories(path: Path | None) -> None:
    if path is None:
        pytest.skip("aucun service ni repository encore")
    calls = forbidden_calls(path.read_text(encoding="utf-8"))
    assert not calls, f"{path.relative_to(MODULES)} pilote la transaction : {calls}"


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("session.commit()", [(1, "commit")]),
        ("self.session.rollback()", [(1, "rollback")]),
        ("with engine.begin() as c:\n    pass", [(1, "begin")]),
        ("get_session().commit()", [(1, "commit")]),
        ("commit()\nsession.add(x)\nsession.flush()", []),
    ],
)
def test_detector(source: str, expected: list[tuple[int, str]]) -> None:
    assert forbidden_calls(source) == expected
