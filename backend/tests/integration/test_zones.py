"""Table `zones`, règles de `core.geo` et démarrage de l'API sur PostGIS réel (story 1.8).

Exige la pile démarrée et migrée, et les URL `TEST_APP_DATABASE_URL` (rôle teranga_app)
et `TEST_MIGRATOR_DATABASE_URL` (voir `test_db_roles.py`). Sans elles, les tests sont
ignorés, sauf avec `REQUIRE_INTEGRATION=1` (CI) : ils échouent alors.
"""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest
from psycopg import errors as pg_errors
from sqlalchemy import URL, Engine, create_engine, make_url, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.core import geo
from app.core.config import get_settings
from app.core.enums import ZoneKind

pytestmark = pytest.mark.integration

BACKEND = Path(__file__).resolve().parents[2]
# Points de référence (latitude, longitude). Aucun n'est journalisé.
PLATEAU = (14.6708, -17.4381)  # Place de l'Indépendance, commune de Dakar-Plateau
THIES = (14.7910, -16.9359)  # Thiès, à 60 km : hors de la Zone active


def _url_from_env(var: str) -> URL:
    raw = os.environ.get(var)
    if not raw:
        pytest.skip(f"{var} non défini : tests d'intégration ignorés")
    url = make_url(raw)
    if url.drivername in ("postgresql", "postgres"):
        url = url.set(drivername="postgresql+psycopg")
    return url


@pytest.fixture(scope="module")
def app_url() -> URL:
    return _url_from_env("TEST_APP_DATABASE_URL")


@pytest.fixture(scope="module")
def app_engine(app_url: URL) -> Iterator[Engine]:
    engine = create_engine(app_url, hide_parameters=True)
    yield engine
    engine.dispose()


@pytest.fixture
def session(app_engine: Engine) -> Iterator[Session]:
    with Session(app_engine) as session:
        yield session


# --- Données chargées par la migration --------------------------------------------


def test_dakar_its_19_communes_and_quartiers_with_a_commune_parent(session: Session) -> None:
    rows = session.execute(
        text(
            "SELECT z.id, z.kind, z.parent_id, p.kind AS parent_kind "
            "FROM zones z LEFT JOIN zones p ON p.id = z.parent_id"
        )
    ).all()
    by_id = {row.id: row for row in rows}
    assert by_id["dakar"].kind == ZoneKind.COMMUNE and by_id["dakar"].parent_id is None
    communes = [r for r in rows if r.kind == ZoneKind.COMMUNE and r.id != "dakar"]
    assert len(communes) == 19
    assert {r.parent_id for r in communes} == {"dakar"}
    assert "dakar-plateau" in by_id
    quartiers = [r for r in rows if r.kind == ZoneKind.QUARTIER]
    assert quartiers, "aucun quartier chargé"
    assert all(r.parent_kind == ZoneKind.COMMUNE for r in quartiers)


def test_every_zone_geometry_is_a_valid_multipolygon(session: Session) -> None:
    bad = session.execute(
        text(
            "SELECT id FROM zones WHERE NOT ST_IsValid(geog::geometry) "
            "OR GeometryType(geog::geometry) <> 'MULTIPOLYGON' OR ST_SRID(geog) <> 4326"
        )
    ).scalars()
    assert list(bad) == []


# --- Règles de core.geo -----------------------------------------------------------


def test_plateau_is_in_the_active_zone_and_in_its_commune(session: Session) -> None:
    get_settings.cache_clear()
    try:
        assert geo.in_active_zone(session, *PLATEAU)
    finally:
        get_settings.cache_clear()
    zone = geo.zone_of(session, *PLATEAU)
    assert zone is not None
    assert zone.id == "dakar-plateau" or (
        zone.kind is ZoneKind.QUARTIER and zone.parent_id == "dakar-plateau"
    )


def test_thies_is_outside(session: Session) -> None:
    assert not geo.in_zone(session, "dakar", *THIES)
    assert geo.zone_of(session, *THIES) is None


def test_boundary_vertex_is_in_the_zone(session: Session) -> None:
    """Limite incluse : un sommet de la limite de Dakar est dans la Zone."""
    lng, lat = session.execute(
        text(
            "SELECT ST_X(p), ST_Y(p) FROM (SELECT ST_PointN(ST_ExteriorRing("
            "ST_GeometryN(geog::geometry, 1)), 1) AS p FROM zones WHERE id = 'dakar') s"
        )
    ).one()
    assert geo.in_zone(session, "dakar", lat, lng)
    assert geo.zone_of(session, lat, lng) is not None


def test_zone_of_prefers_the_smallest_quartier(session: Session) -> None:
    """Au point intérieur de chaque quartier : un quartier, jamais plus grand que lui."""
    rows = session.execute(
        text(
            "SELECT id, ST_Area(geog) AS area, ST_Y(p) AS lat, ST_X(p) AS lng "
            "FROM (SELECT id, geog, ST_PointOnSurface(geog::geometry) AS p "
            "FROM zones WHERE kind = 'quartier') q"
        )
    ).all()
    areas = {row.id: row.area for row in rows}
    for row in rows:
        zone = geo.zone_of(session, row.lat, row.lng)
        assert zone is not None and zone.kind is ZoneKind.QUARTIER, row.id
        assert areas[zone.id] <= row.area, row.id


def test_unknown_zone_is_an_error(session: Session) -> None:
    with pytest.raises(geo.UnknownZoneError):
        geo.in_zone(session, "inexistante", *PLATEAU)
    with pytest.raises(geo.UnknownZoneError):
        geo.load_active_zone(session, "inexistante")


def test_published_zone_is_simplified_and_covers_the_exact_zone(session: Session) -> None:
    zone = geo.load_active_zone(session, "dakar")
    assert (zone.id, zone.name) == ("dakar", "Dakar")
    assert zone.geometry.type == "MultiPolygon"
    geojson = zone.geometry.model_dump_json()
    exact_points = session.execute(
        text("SELECT ST_NPoints(geog::geometry) FROM zones WHERE id = 'dakar'")
    ).scalar_one()
    published_points = sum(len(ring) for poly in zone.geometry.coordinates for ring in poly)
    assert published_points < exact_points
    assert len(geojson) < 50_000
    # Élargie de 50 m : le polygone publié (jugé à plat par la PWA) couvre la Zone exacte.
    covers = session.execute(
        text(
            "SELECT ST_Covers(ST_SetSRID(ST_GeomFromGeoJSON(:g), 4326), geog::geometry) "
            "FROM zones WHERE id = 'dakar'"
        ),
        {"g": geojson},
    ).scalar_one()
    assert covers


# --- Lecture seule pour teranga_app ------------------------------------------------


def test_app_role_reads_but_cannot_write_zones(app_engine: Engine) -> None:
    with app_engine.connect() as conn:
        privileges = {
            privilege: conn.scalar(
                text("SELECT has_table_privilege('teranga_app', 'zones', :p)"), {"p": privilege}
            )
            for privilege in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE")
        }
    assert privileges == {
        "SELECT": True,
        "INSERT": False,
        "UPDATE": False,
        "DELETE": False,
        "TRUNCATE": False,
    }
    for statement in (
        "UPDATE zones SET name = name WHERE id = 'dakar'",
        "DELETE FROM zones WHERE id = 'dakar'",
        "INSERT INTO zones (id, name, kind, osm_ref, geog) SELECT 'x', name, kind, osm_ref, geog "
        "FROM zones WHERE id = 'dakar'",
    ):
        with app_engine.connect() as conn, pytest.raises(ProgrammingError) as exc_info:
            conn.execute(text(statement))
        assert isinstance(exc_info.value.orig, pg_errors.InsufficientPrivilege), statement


# --- Démarrage réel de l'API (uvicorn) ----------------------------------------------


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _api_env(app_url: URL, **extra: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k.upper() not in {"ENV", "DEMO_MODE"}}
    env.update(
        ENV="dev",
        DATABASE_URL=app_url.render_as_string(hide_password=False),
        SECRETS_DIR="/nonexistent",
        **extra,
    )
    return env


def _uvicorn(port: int) -> list[str]:
    return [
        sys.executable,
        "-m",
        "uvicorn",
        "--factory",
        "app.main:create_app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]


def test_api_refuses_to_start_on_an_unknown_zone(app_url: URL) -> None:
    result = subprocess.run(  # noqa: S603 (interpréteur courant, arguments fixes)
        _uvicorn(_free_port()),
        cwd=BACKEND,
        env=_api_env(app_url, ACTIVE_ZONE_ID="inexistante"),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 1, output
    assert "startup_refused" in output
    assert "ACTIVE_ZONE_ID" in output
    assert app_url.password is not None and app_url.password not in output


def test_api_starts_and_publishes_the_active_zone(app_url: URL) -> None:
    port = _free_port()
    process = subprocess.Popen(  # noqa: S603 (interpréteur courant, arguments fixes)
        _uvicorn(port),
        cwd=BACKEND,
        env=_api_env(app_url),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.monotonic() + 30
        body = None
        while body is None and time.monotonic() < deadline:
            assert process.poll() is None, process.communicate()[0]
            try:
                with urllib.request.urlopen(  # noqa: S310 (URL locale fixe)
                    f"http://127.0.0.1:{port}/v1/config", timeout=2
                ) as response:
                    body = json.loads(response.read())
            except OSError:
                time.sleep(0.3)
        assert body is not None, "l'API n'a pas répondu"
        assert body["active_zone"]["id"] == "dakar"
        assert body["active_zone"]["geometry"]["type"] == "MultiPolygon"
        assert body["report_accuracy_flag_m"] == 50
    finally:
        process.terminate()
        try:
            output = process.communicate(timeout=15)[0]
        except subprocess.TimeoutExpired:
            # Jamais de processus orphelin : arrêt forcé, puis lecture de la sortie.
            process.kill()
            output = process.communicate()[0]
    assert "active_zone_loaded" in output
    assert "startup_refused" not in output
