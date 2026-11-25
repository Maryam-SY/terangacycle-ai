"""Aucun service ni repository ne pilote la transaction (AD-17).

Analyse AST de `app/modules/**/service.py` et `repository.py` : aucun appel
`.commit(`, `.rollback(` ni `.begin(` ; seule l'unité de travail de `core.db` valide.
Chaque fonction publique d'un service est `@transactional` : elle rejoint l'unité en
cours, ou en ouvre une.
"""

import ast
from pathlib import Path

import pytest

MODULES = Path(__file__).resolve().parents[2] / "app" / "modules"
FORBIDDEN = {"commit", "rollback", "begin"}
LAYER_FILES = ("service.py", "repository.py")
# Services et repositories créés par la story 1.11 : le test ne peut plus rien sauter.
EXPECTED_LAYER_FILES = {
    f"{module}/{name}" for module in ("auth", "orgs", "reports") for name in LAYER_FILES
}


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


def untransactional_functions(source: str) -> list[str]:
    """Fonctions publiques de premier niveau sans décorateur `transactional`."""

    def is_transactional(decorator: ast.expr) -> bool:
        name = decorator.attr if isinstance(decorator, ast.Attribute) else None
        name = decorator.id if isinstance(decorator, ast.Name) else name
        return name == "transactional"

    return [
        node.name
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and not node.name.startswith("_")
        and not any(is_transactional(d) for d in node.decorator_list)
    ]


def test_services_and_repositories_are_scanned() -> None:
    scanned = {path.relative_to(MODULES).as_posix() for path in _layer_files()}
    assert scanned >= EXPECTED_LAYER_FILES


@pytest.mark.parametrize("path", _layer_files(), ids=lambda p: p.relative_to(MODULES).as_posix())
def test_no_transaction_control_in_services_and_repositories(path: Path) -> None:
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


@pytest.mark.parametrize(
    "path", sorted(MODULES.rglob("service.py")), ids=lambda p: p.relative_to(MODULES).as_posix()
)
def test_public_service_functions_are_transactional(path: Path) -> None:
    missing = untransactional_functions(path.read_text(encoding="utf-8"))
    assert not missing, f"{path.relative_to(MODULES)} : sans @transactional : {missing}"


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("@transactional\ndef f(): pass", []),
        ("@db.transactional\nasync def f(): pass", []),
        ("def f(): pass\ndef _g(): pass", ["f"]),
        ("@other\ndef f(): pass\nX = 1", ["f"]),
    ],
)
def test_transactional_detector(source: str, expected: list[str]) -> None:
    assert untransactional_functions(source) == expected
