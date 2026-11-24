"""Documentation OpenAPI coupée en production (AD-23)."""

from collections.abc import Callable

import pytest

from app.core.config import Settings
from app.core.enums import Env
from app.main import create_app
from tests.asgi import request

DOC_PATHS = ["/docs", "/redoc", "/openapi.json"]


@pytest.mark.parametrize("path", DOC_PATHS)
def test_docs_absent_in_prod(path: str, make_settings: Callable[..., Settings]) -> None:
    app = create_app(make_settings(env=Env.PROD))
    response = request(app, "GET", path)
    assert response.status == 404
    assert response.json()["error"]["code"] == "not_found"


@pytest.mark.parametrize("path", DOC_PATHS)
@pytest.mark.parametrize(("env", "demo_mode"), [(Env.DEMO, True), (Env.DEV, False)])
def test_docs_served_outside_prod(
    path: str, env: Env, demo_mode: bool, make_settings: Callable[..., Settings]
) -> None:
    app = create_app(make_settings(env=env, demo_mode=demo_mode))
    response = request(app, "GET", path)
    assert response.status == 200
