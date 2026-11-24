"""Contrats import-linter de `pyproject.toml` (AD-1) : le dépôt les respecte, et ils mordent.

Les cas témoins construisent dans `tmp_path` un paquet `app` minimal (mêmes modules que
le vrai, vides) et y ajoutent quelques fichiers ; `lint-imports` y est lancé avec une
copie du `pyproject.toml` réel, donc avec exactement les contrats du dépôt.
"""

import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]
# Modules métier : les sous-paquets réels de app/modules/.
MODULES = tuple(sorted(p.parent.name for p in (BACKEND / "app" / "modules").glob("*/__init__.py")))
with (BACKEND / "pyproject.toml").open("rb") as _config:
    IMPORTLINTER = tomllib.load(_config)["tool"]["importlinter"]
_CONTRACTS_BY_ID = {contract["id"]: contract for contract in IMPORTLINTER["contracts"]}
# Identifiant -> nom affiché par lint-imports.
CONTRACTS = {contract_id: c["name"] for contract_id, c in _CONTRACTS_BY_ID.items()}
# Flèches de l'épine (AD-1), telles qu'écrites dans la configuration.
SPINE = {
    ("missions", "reports"),
    ("missions", "auth"),
    ("reports", "ai"),
    ("reports", "auth"),
    ("lots", "missions"),
    ("lots", "auth"),
    ("notifications", "auth"),
}
_ARROW = re.compile(r"app\.modules\.(\w+)(?:\.\*\*)? -> app\.modules\.(\w+)\.service")


def _lint_imports_executable() -> str:
    # Script installé à côté de l'interpréteur de l'environnement (uv run, .venv).
    name = "lint-imports.exe" if os.name == "nt" else "lint-imports"
    candidate = Path(sys.executable).with_name(name)
    found = str(candidate) if candidate.is_file() else shutil.which("lint-imports")
    assert found, "lint-imports introuvable : lancer les tests via `uv run`"
    return found


def run_lint_imports(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    # Lignes larges : rich ne coupe pas le résumé ni la liste des imports illégaux.
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "COLUMNS": "200"}
    return subprocess.run(  # noqa: S603 (exécutable de l'environnement, arguments fixes)
        [_lint_imports_executable(), "--no-cache", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def _status(output: str, contract_id: str) -> str | None:
    """« KEPT » ou « BROKEN » pour un contrat, d'après le résumé de lint-imports.

    Ligne du résumé : `<nom> KEPT` ou `<nom> BROKEN`, suivie au besoin du nombre
    d'imports ignorés, par exemple `(1 ignored import)`.
    """
    pattern = re.compile(re.escape(CONTRACTS[contract_id]) + r" (KEPT|BROKEN)(?: \(.*\))?")
    for line in output.splitlines():
        match = pattern.fullmatch(line.strip())
        if match:
            return match.group(1)
    return None


def _write(root: Path, relative: str, content: str = "") -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_witness(root: Path, files: dict[str, str]) -> Path:
    """Paquet `app` témoin : racines de composition, `core`, les 7 modules, puis `files`."""
    for relative in (
        "app/__init__.py",
        "app/main.py",
        "app/worker.py",
        "app/reactions.py",
        "app/core/__init__.py",
        "app/modules/__init__.py",
        *(f"app/modules/{name}/__init__.py" for name in MODULES),
    ):
        _write(root, relative)
    for relative, content in files.items():
        _write(root, relative, content)
    config = root / "pyproject.toml"
    shutil.copyfile(BACKEND / "pyproject.toml", config)
    return config


def _configured_arrows() -> set[tuple[str, str]]:
    """(source, cible) de chaque `ignore_imports` du contrat `protected`."""
    arrows = set()
    for expression in _CONTRACTS_BY_ID["protected"]["ignore_imports"]:
        match = _ARROW.fullmatch(expression)
        assert match, f"ignore_imports inattendu : {expression}"
        arrows.add((match.group(1), match.group(2)))
    return arrows


def _imports(targets: list[str]) -> str:
    return "".join(f"from app.modules.{target} import service as _{target}\n" for target in targets)


def test_layers_containers_are_every_module() -> None:
    containers = set(_CONTRACTS_BY_ID["layers"]["containers"])
    assert MODULES, "aucun module trouvé sous app/modules/"
    assert containers == {f"app.modules.{name}" for name in MODULES}


def test_protected_arrows_are_the_spine() -> None:
    assert _configured_arrows() == SPINE


def test_repository_keeps_all_contracts() -> None:
    assert set(CONTRACTS) == {"layers", "acyclic_siblings", "protected"}
    result = run_lint_imports(BACKEND)
    assert result.returncode == 0, result.stdout + result.stderr
    for contract_id in CONTRACTS:
        assert _status(result.stdout, contract_id) == "KEPT", result.stdout


def test_cross_module_repository_import_breaks_protected(tmp_path: Path) -> None:
    config = make_witness(
        tmp_path,
        {
            "app/modules/reports/repository.py": "VALUE = 1\n",
            "app/modules/missions/service.py": "from app.modules.reports import repository\n",
        },
    )
    result = run_lint_imports(tmp_path, str(config))
    assert result.returncode == 1, result.stdout + result.stderr
    assert _status(result.stdout, "protected") == "BROKEN", result.stdout
    assert "app.modules.missions.service" in result.stdout
    assert "app.modules.reports.repository" in result.stdout


def test_every_spine_arrow_is_allowed(tmp_path: Path) -> None:
    """Chaque flèche de la configuration, depuis un service et depuis un router."""
    sources: dict[str, list[str]] = {}
    for source, target in sorted(_configured_arrows()):
        sources.setdefault(source, []).append(target)
    files = {f"app/modules/{name}/service.py": "" for name in MODULES}
    for source, targets in sources.items():
        files[f"app/modules/{source}/service.py"] = _imports(targets)
        files[f"app/modules/{source}/router.py"] = _imports(targets)
    config = make_witness(tmp_path, files)
    result = run_lint_imports(tmp_path, str(config))
    assert result.returncode == 0, result.stdout + result.stderr
    for contract_id in CONTRACTS:
        assert _status(result.stdout, contract_id) == "KEPT", result.stdout


def test_every_other_arrow_breaks_protected(tmp_path: Path) -> None:
    """Toute paire de modules hors de l'épine, même vers le `service`, est refusée."""
    forbidden = [
        (source, target)
        for source in MODULES
        for target in MODULES
        if source != target and (source, target) not in SPINE
    ]
    files = {
        f"app/modules/{source}/service.py": _imports(
            [target for s, target in forbidden if s == source]
        )
        for source in MODULES
    }
    config = make_witness(tmp_path, files)
    result = run_lint_imports(tmp_path, str(config))
    assert result.returncode == 1, result.stdout + result.stderr
    assert _status(result.stdout, "protected") == "BROKEN", result.stdout
    for source, target in forbidden:
        link = f"app.modules.{source}.service -> app.modules.{target}.service"
        assert link in result.stdout, f"{link} non signalé\n{result.stdout}"


@pytest.mark.parametrize(
    ("files", "broken"),
    [
        pytest.param(
            {
                "app/modules/reports/service.py": "VALUE = 1\n",
                "app/modules/missions/service.py": "from app.modules.reports import service\n",
            },
            set(),
            id="fleche-autorisee-vers-service",
        ),
        pytest.param(
            {
                "app/modules/auth/service.py": "VALUE = 1\n",
                "app/modules/analytics/service.py": "from app.modules.auth import service\n",
            },
            {"protected"},
            id="fleche-non-autorisee",
        ),
        pytest.param(
            {
                "app/modules/reports/service.py": "VALUE = 1\n",
                "app/core/geo.py": "from app.modules.reports import service\n",
            },
            {"protected"},
            id="core-importe-un-module",
        ),
        pytest.param(
            {
                "app/modules/reports/service.py": "VALUE = 1\n",
                "app/modules/reports/repository.py": "from app.modules.reports import service\n",
            },
            {"layers"},
            id="repository-importe-service",
        ),
        pytest.param(
            {
                "app/modules/missions/service.py": "VALUE = 1\n",
                "app/modules/reports/service.py": "from app.modules.missions import service\n",
                "app/modules/missions/router.py": "from app.modules.reports import service\n",
            },
            {"protected", "acyclic_siblings"},
            id="cycle-entre-modules",
        ),
        pytest.param(
            {
                "app/modules/reports/repository.py": "VALUE = 1\n",
                "app/main.py": "from app.modules.reports import repository\n",
            },
            set(),
            id="racine-de-composition",
        ),
    ],
)
def test_witness_contracts(tmp_path: Path, files: dict[str, str], broken: set[str]) -> None:
    config = make_witness(tmp_path, files)
    result = run_lint_imports(tmp_path, str(config))
    assert result.returncode == (1 if broken else 0), result.stdout + result.stderr
    for contract_id in CONTRACTS:
        expected = "BROKEN" if contract_id in broken else "KEPT"
        assert _status(result.stdout, contract_id) == expected, result.stdout
