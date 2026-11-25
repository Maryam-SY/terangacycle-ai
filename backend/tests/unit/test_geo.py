"""`core.geo` : une Position inutilisable est refusée avant toute requête (story 1.8)."""

import math

import pytest

from app.core import geo


class _NoSession:
    """Session qui échoue si on l'interroge : la validation doit passer avant."""

    def execute(self, *args: object, **kwargs: object) -> None:
        raise AssertionError("requête envoyée malgré une Position invalide")


@pytest.mark.parametrize(
    ("lat", "lng"),
    [
        (math.nan, -17.44),
        (14.69, math.inf),
        (-math.inf, -17.44),
        (90.5, -17.44),
        (14.69, -180.01),
        ("x", -17.44),
    ],
)
def test_invalid_position_is_refused_without_values(lat: object, lng: object) -> None:
    for call in (
        lambda: geo.in_zone(_NoSession(), "dakar", lat, lng),  # type: ignore[arg-type]
        lambda: geo.zone_of(_NoSession(), lat, lng),  # type: ignore[arg-type]
        lambda: geo.zones_covering(_NoSession(), lat, lng),  # type: ignore[arg-type]
    ):
        with pytest.raises(geo.InvalidPositionError) as exc_info:
            call()
        assert isinstance(exc_info.value, ValueError)
        assert "14.69" not in str(exc_info.value) and "17.44" not in str(exc_info.value)


def test_bounds_are_inclusive() -> None:
    assert geo._point_params(90, -180) == {"lat": 90.0, "lng": -180.0}
