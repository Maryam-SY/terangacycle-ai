"""Règles pures de la création d'un Signalement (story 1.11) : Numéro de suivi, drapeau
de Position imprécise, étiquette de démonstration, Organisation plateforme, migration."""

import importlib.util
import re
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

from app.core import demo
from app.core.config import Settings
from app.core.enums import (
    HeapSize,
    OrganizationStatus,
    OrganizationType,
    ReportStatus,
    WasteType,
)
from app.modules.orgs.service import PLATFORM_ORGANIZATION_ID
from app.modules.reports.rules import format_tracking_number, is_imprecise

MIGRATION = Path(__file__).resolve().parents[2] / "migrations" / "versions" / "0003_reports.py"
TRACKING_NUMBER = re.compile(r"TC-[0-9]{4}-[0-9]{6}")


def _migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("migration_0003_reports", MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("year", "sequence", "expected"),
    [
        (2026, 1, "TC-2026-000001"),
        (2027, 42, "TC-2027-000042"),
        (2026, 999_999, "TC-2026-999999"),
    ],
)
def test_tracking_number_format(year: int, sequence: int, expected: str) -> None:
    assert format_tracking_number(year, sequence) == expected
    assert TRACKING_NUMBER.fullmatch(expected)


@pytest.mark.parametrize(
    ("accuracy_m", "flagged"),
    [(51, True), (50.01, True), (50, False), (50.0, False), (12, False)],
)
def test_imprecise_position_flag_is_strictly_above_the_threshold(
    accuracy_m: float, flagged: bool
) -> None:
    assert is_imprecise(accuracy_m, 50) is flagged


@pytest.mark.parametrize("demo_mode", [True, False])
def test_demo_flag_follows_the_given_settings(
    demo_mode: bool, make_settings: Callable[..., Settings]
) -> None:
    settings = make_settings(demo_mode=demo_mode)
    assert demo.flag(settings) is demo_mode
    # Un parent étiqueté démo étiquette aussi l'enfant.
    assert demo.flag(settings, parent_is_demo=True) is True


def test_platform_organization_id_matches_the_migration() -> None:
    migration = _migration()
    assert migration.PLATFORM_ORGANIZATION_ID == str(PLATFORM_ORGANIZATION_ID)
    assert PLATFORM_ORGANIZATION_ID.version == 4


def test_migration_enumerations_match_core_enums() -> None:
    """Les `CHECK` de la migration reprennent exactement les énumérations de core/enums.py
    (vérifié aussi sur la base réelle par tests/integration/test_reports_schema.py)."""
    migration = _migration()
    assert set(migration.ORGANIZATION_TYPES) == {kind.value for kind in OrganizationType}
    assert set(migration.ORGANIZATION_STATUSES) == {s.value for s in OrganizationStatus}
    assert set(migration.REPORT_STATUSES) == {status.value for status in ReportStatus}
    assert set(migration.HEAP_SIZES) == {size.value for size in HeapSize}
    assert set(migration.WASTE_TYPES) == {kind.value for kind in WasteType}


def test_migration_downgrade_drops_its_five_tables() -> None:
    migration = _migration()
    assert migration.down_revision == "0002_zones"
    assert migration.TABLES == (
        "organizations",
        "devices",
        "reports",
        "report_photos",
        "tracking_counters",
    )
