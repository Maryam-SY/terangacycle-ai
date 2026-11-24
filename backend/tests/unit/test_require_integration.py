"""`REQUIRE_INTEGRATION` : un test d'intégration sans base échoue au lieu d'être ignoré.

Deux familles de cas, chacun dans un sous-processus pytest :
  - les vrais tests d'intégration, lancés sans URL de base ;
  - des fichiers témoins dans une copie de `tests/` (vrai `conftest.py`, vrai
    `support.py`) sous `tmp_path` : skip à la collecte, fichier de `tests/integration/`
    sans marqueur, session sans aucun test d'intégration.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]
TESTS = BACKEND / "tests"
TARGET = "tests/integration/test_db_roles.py"
DB_URL_VARS = ("TEST_APP_DATABASE_URL", "TEST_MIGRATOR_DATABASE_URL")
MESSAGE = "REQUIRE_INTEGRATION :"


def _run_pytest(
    cwd: Path, require: str | None, *args: str, pythonpath: str | None = None
) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k not in (*DB_URL_VARS, "REQUIRE_INTEGRATION")}
    if require is not None:
        env["REQUIRE_INTEGRATION"] = require
    if pythonpath is not None:
        env["PYTHONPATH"] = pythonpath
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(  # noqa: S603 (interpréteur courant, arguments fixes)
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def _count(output: str, outcome: str) -> int:
    """Nombre de tests d'une issue (`failed`, `error`, `skipped`…) dans le résumé final.

    Seule la dernière ligne de résumé compte (`1 failed, 2 passed in 0.12s`) : d'autres
    lignes, comme `Interrupted: 1 error during collection`, répètent les nombres.
    """
    summaries = [line for line in output.splitlines() if re.search(r" in [\d.]+s\b", line)]
    if not summaries:
        return 0
    return sum(int(n) for n in re.findall(rf"(\d+) {outcome}s?\b", summaries[-1]))


def _witness_tree(root: Path, files: dict[str, str]) -> None:
    """Copie de `tests/` réduite au vrai conftest et à support.py, plus `files`."""
    tests = root / "tests"
    tests.mkdir()
    for name in ("conftest.py", "support.py"):
        shutil.copyfile(TESTS / name, tests / name)
    (root / "pytest.ini").write_text(
        "[pytest]\nmarkers =\n    integration: pile Docker exigée\n", encoding="utf-8"
    )
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _run_witness(root: Path, require: str | None) -> subprocess.CompletedProcess[str]:
    # Le témoin passe avant le backend dans le chemin : `tests.support` y est trouvé,
    # `app` vient du vrai backend.
    pythonpath = os.pathsep.join([str(root), str(BACKEND)])
    return _run_pytest(root, require, "--rootdir", str(root), "tests", pythonpath=pythonpath)


def test_missing_database_fails_when_integration_is_required() -> None:
    result = _run_pytest(BACKEND, "1", TARGET)
    output = result.stdout + result.stderr
    assert result.returncode != 0, output
    assert _count(result.stdout, "skipped") == 0, output
    assert _count(result.stdout, "failed") + _count(result.stdout, "error") >= 1, output
    assert MESSAGE in result.stdout, output


def test_missing_database_skips_otherwise() -> None:
    result = _run_pytest(BACKEND, None, TARGET)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert _count(result.stdout, "failed") + _count(result.stdout, "error") == 0, output
    assert _count(result.stdout, "skipped") >= 1, output


# Skip à la collecte, et test de tests/integration/ sans marqueur qui s'ignore lui-même.
SKIPPING_INTEGRATION = {
    "tests/integration/test_module_skip.py": (
        "import pytest\n\npytest.skip('pas de base', allow_module_level=True)\n"
    ),
    "tests/integration/test_unmarked.py": (
        "import pytest\n\n\ndef test_needs_db():\n    pytest.skip('pas de base')\n"
    ),
}


# Une erreur de collecte interrompt la session : un fichier témoin par exécution.
# Valeurs non canoniques de la variable : casse et espaces ignorés.
@pytest.mark.parametrize(
    ("witness", "require"),
    [
        ("tests/integration/test_module_skip.py", " Yes "),
        ("tests/integration/test_unmarked.py", "1"),
    ],
    ids=["skip-a-la-collecte", "sans-marqueur"],
)
def test_skipped_integration_witness_fails_when_required(
    tmp_path: Path, witness: str, require: str
) -> None:
    _witness_tree(tmp_path, {witness: SKIPPING_INTEGRATION[witness]})
    result = _run_witness(tmp_path, require)
    output = result.stdout + result.stderr
    assert result.returncode != 0, output
    assert _count(result.stdout, "skipped") == 0, output
    assert _count(result.stdout, "failed") + _count(result.stdout, "error") == 1, output
    assert Path(witness).name in result.stdout, output
    assert "test d'intégration ignoré refusé" in result.stdout, output


def test_skipped_integration_witnesses_skip_otherwise(tmp_path: Path) -> None:
    _witness_tree(tmp_path, SKIPPING_INTEGRATION)
    result = _run_witness(tmp_path, None)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert _count(result.stdout, "skipped") >= 2, output


def test_session_without_integration_test_fails_when_required(tmp_path: Path) -> None:
    _witness_tree(tmp_path, {"tests/unit/test_ok.py": "def test_ok():\n    assert True\n"})
    result = _run_witness(tmp_path, "TRUE")
    output = result.stdout + result.stderr
    assert result.returncode != 0, output
    assert "aucun test d'intégration n'a tourné" in result.stdout, output

    result = _run_witness(tmp_path, None)
    assert result.returncode == 0, result.stdout + result.stderr
