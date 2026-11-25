"""Fixtures communes : environnement neutre, journalisation sur la sortie capturée.

Règle `REQUIRE_INTEGRATION` : voir `pytest_runtest_makereport`.
"""

import os
from collections.abc import Callable, Generator
from pathlib import Path

import pytest

from app.core.config import REQUIRED_SECRETS, Settings
from app.core.logging import configure_logging
from tests.support import fake_secret_value

# Variables qui changeraient le résultat des tests si l'hôte les définissait.
_SETTINGS_ENV_VARS = [
    "ENV",
    "DEMO_MODE",
    "LOG_LEVEL",
    "MODEL_VERSION",
    "S3_ENDPOINT",
    "S3_REGION",
    "S3_BUCKET",
    "VALKEY_URL",
    "ACTIVE_ZONE_ID",
    "REPORT_ACCURACY_FLAG_M",
    *(name.upper() for name in REQUIRED_SECRETS),
]


INTEGRATION_DIR = Path(__file__).resolve().parent / "integration"
_REQUIRE_VALUES = {"1", "true", "yes"}
_integration_ran = pytest.StashKey[bool]()


def integration_required() -> bool:
    """`REQUIRE_INTEGRATION` à 1, true ou yes (posé par la CI) : la pile doit être là."""
    return os.environ.get("REQUIRE_INTEGRATION", "").strip().lower() in _REQUIRE_VALUES


def _under_integration_dir(path: Path) -> bool:
    return path.resolve().is_relative_to(INTEGRATION_DIR)


def _is_integration(item: pytest.Item) -> bool:
    """Marqué `integration`, ou rangé sous tests/integration/ (marqueur oublié)."""
    return item.get_closest_marker("integration") is not None or _under_integration_dir(item.path)


def _refuse_skip(report: pytest.TestReport | pytest.CollectReport) -> None:
    reason = report.longrepr[2] if isinstance(report.longrepr, tuple) else report.longrepr
    report.outcome = "failed"
    report.longrepr = f"REQUIRE_INTEGRATION : test d'intégration ignoré refusé ({reason})"


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    """Avec `REQUIRE_INTEGRATION`, un test d'intégration ignoré devient un échec.

    Sans la variable, rien ne change : un test d'intégration sans base est ignoré.
    """
    report = yield
    if not integration_required() or not _is_integration(item):
        return report
    if report.skipped and not hasattr(report, "wasxfail"):
        _refuse_skip(report)
    elif report.when == "call":
        item.config.stash[_integration_ran] = True
    return report


@pytest.hookimpl(wrapper=True)
def pytest_make_collect_report(
    collector: pytest.Collector,
) -> Generator[None, pytest.CollectReport, pytest.CollectReport]:
    """Avec `REQUIRE_INTEGRATION`, un fichier de tests/integration/ ignoré à la collecte
    (`pytest.skip(..., allow_module_level=True)`) devient une erreur de collecte."""
    report = yield
    if report.skipped and integration_required() and _under_integration_dir(collector.path):
        _refuse_skip(report)
    return report


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Avec `REQUIRE_INTEGRATION`, une session où aucun test d'intégration n'a tourné échoue."""
    config = session.config
    if (
        not integration_required()
        or config.option.collectonly
        or config.stash.get(_integration_ran, False)
    ):
        return
    reporter = config.pluginmanager.get_plugin("terminalreporter")
    if reporter is not None:
        reporter.write_line(
            "REQUIRE_INTEGRATION : aucun test d'intégration n'a tourné.", red=True, bold=True
        )
    if exitstatus == pytest.ExitCode.OK:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


@pytest.fixture(autouse=True)
def _neutral_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in _SETTINGS_ENV_VARS:
        if var in os.environ:
            monkeypatch.delenv(var)
    # Journalisation JSON neutre (le gestionnaire suit sys.stdout, capturé par capsys).
    configure_logging("INFO")


@pytest.fixture
def full_secrets_dir(tmp_path: Path) -> Path:
    """Dossier de secrets contenant tout l'inventaire d'AD-26."""
    directory = tmp_path / "secrets"
    directory.mkdir()
    for name in REQUIRED_SECRETS:
        (directory / name).write_text(fake_secret_value(name) + "\n", encoding="utf-8")
    return directory


@pytest.fixture
def make_settings(full_secrets_dir: Path) -> Callable[..., Settings]:
    """Fabrique de `Settings` complètes (tous les secrets présents)."""

    def factory(**overrides: object) -> Settings:
        return Settings(_secrets_dir=full_secrets_dir, **overrides)  # type: ignore[arg-type]

    return factory
