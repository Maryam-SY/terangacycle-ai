"""Chaque route a une politique d'accès déclarée (AD-9, story 1.6).

Parcourt les routes de `create_app()` : toute route qui n'est ni dans la liste blanche
publique close, ni déclarée dans `core.access.ROUTE_POLICIES`, ni une page de la
documentation OpenAPI fait échouer le test, qui la nomme. La table reste à jour : une
politique ou une entrée publique sans route échoue aussi, sauf les entrées réservées.
"""

import re
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import get_args

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute, iter_route_contexts
from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from app.core.access import (
    DEVICE,
    DOCS_ROUTES,
    INTERNAL,
    PUBLIC_ROUTES,
    RESERVED_PUBLIC_ROUTES,
    ROUTE_POLICIES,
    Policy,
    PolicyKind,
    RouteKey,
    roles,
)
from app.core.config import Settings
from app.core.enums import Env, Role
from app.main import create_app

# Liste blanche close, recopiée à dessein : l'élargir exige de modifier ce test.
EXPECTED_PUBLIC_ROUTES: frozenset[RouteKey] = frozenset(
    {
        ("GET", "/healthz"),
        ("GET", "/readyz"),
        ("GET", "/v1/config"),
        ("POST", "/v1/reports"),
        ("GET", "/v1/public/map"),
    }
)
# Seule la carte publique (story 7.6) reste réservée : `POST /v1/reports` existe (1.11).
EXPECTED_RESERVED: frozenset[RouteKey] = frozenset({("GET", "/v1/public/map")})
IGNORED_METHODS = {"HEAD", "OPTIONS"}
CADDYFILE = Path(__file__).resolve().parents[3] / "infra" / "Caddyfile"
INTERNAL_MATCHER = re.compile(r"^\s*@internal\s+path\s+(.+?)\s*$", re.MULTILINE)
AI_PREFIX = "/v1/ai"


def _fmt(key: RouteKey) -> str:
    return f"{key[0]} {key[1]}"


def app_routes(app: FastAPI) -> tuple[set[RouteKey], list[str]]:
    """(méthode, chemin gabarit) de chaque route ; et les routes qu'aucune politique ne
    peut couvrir : type non pris en charge (Mount, WebSocket…), ou aucune méthode hors
    HEAD et OPTIONS (`methods=None` d'un HTTPEndpoint, par exemple)."""
    keys: set[RouteKey] = set()
    unsupported: list[str] = []
    # FastAPI garde les routers inclus tels quels dans `app.routes` (inclusion paresseuse) :
    # `iter_route_contexts`, celui de la génération de l'OpenAPI, les déplie avec leur
    # chemin effectif (préfixe compris).
    for context in iter_route_contexts(app.routes):
        route = context.original_route
        # Chemin gabarit sans convertisseur : `/v1/reports/{id}`, jamais `{id:int}`.
        path = context.path_format
        if isinstance(route, APIRoute | Route) and path is not None:
            methods = set(context.methods or ()) - IGNORED_METHODS
            if not methods:
                unsupported.append(
                    f"{path} : aucune méthode hors HEAD et OPTIONS "
                    f"(methods={context.methods!r}), politique impossible à déclarer"
                )
            keys.update((method, path) for method in methods)
        else:
            path = getattr(route, "path", "?")
            unsupported.append(f"{type(route).__name__} {path} : type de route non pris en charge")
    return keys, unsupported


def route_table_errors(
    app: FastAPI,
    public: Iterable[RouteKey] = PUBLIC_ROUTES,
    policies: Mapping[RouteKey, Policy] = ROUTE_POLICIES,
    reserved: Iterable[RouteKey] = RESERVED_PUBLIC_ROUTES,
) -> list[str]:
    """Écarts entre les routes de l'application et la table des politiques."""
    public, reserved = frozenset(public), frozenset(reserved)
    routes, errors = app_routes(app)
    for key in sorted(routes - public - policies.keys() - DOCS_ROUTES):
        errors.append(f"{_fmt(key)} : route sans politique d'accès (ROUTE_POLICIES)")
    for key in sorted(public & policies.keys()):
        errors.append(f"{_fmt(key)} : à la fois publique et déclarée dans ROUTE_POLICIES")
    for key in sorted(policies.keys() - routes):
        errors.append(f"{_fmt(key)} : politique orpheline, aucune route de ce nom")
    for key in sorted(public - reserved - routes):
        errors.append(f"{_fmt(key)} : entrée publique orpheline, aucune route de ce nom")
    return errors


def public_whitelist_errors(
    public: Iterable[RouteKey] = PUBLIC_ROUTES,
    reserved: Iterable[RouteKey] = RESERVED_PUBLIC_ROUTES,
) -> list[str]:
    """Écarts entre la liste blanche déclarée et la liste close d'AD-9."""
    public, reserved = frozenset(public), frozenset(reserved)
    errors = [
        f"{_fmt(key)} : publique hors de la liste blanche close"
        for key in sorted(public - EXPECTED_PUBLIC_ROUTES)
    ]
    errors += [
        f"{_fmt(key)} : manque à la liste blanche publique"
        for key in sorted(EXPECTED_PUBLIC_ROUTES - public)
    ]
    if reserved != EXPECTED_RESERVED:
        errors.append(f"entrées réservées inattendues : {sorted(reserved)}")
    return errors


def internal_patterns(caddyfile: str) -> list[str]:
    """Chemins du matcher `@internal path …` du Caddyfile (jamais relayés par Caddy)."""
    return [pattern for line in INTERNAL_MATCHER.findall(caddyfile) for pattern in line.split()]


def caddy_path_matches(pattern: str, path: str) -> bool:
    """Matcher `path` de Caddy : chemin exact, ou préfixe pour un motif en `/*`."""
    if pattern.endswith("*"):
        return path.startswith(pattern[:-1])
    return path == pattern


def internal_exposure_errors(
    routes: Iterable[RouteKey],
    patterns: list[str],
    policies: Mapping[RouteKey, Policy] = ROUTE_POLICIES,
) -> list[str]:
    """Routes `internal` que Caddy relaierait, et routes de /v1/ai non déclarées `internal`."""
    errors = [
        f"{_fmt(key)} : politique internal, mais hors du matcher @internal du Caddyfile"
        for key, policy in sorted(policies.items())
        if policy.kind == "internal"
        and not any(caddy_path_matches(pattern, key[1]) for pattern in patterns)
    ]
    errors += [
        f"{_fmt(key)} : route de {AI_PREFIX} sans politique internal"
        for key in sorted(routes)
        if (key[1] == AI_PREFIX or key[1].startswith(AI_PREFIX + "/"))
        and policies.get(key) != INTERNAL
    ]
    return errors


# --- Table réelle -------------------------------------------------------------------


@pytest.mark.parametrize("env", [Env.DEV, Env.PROD])
def test_every_route_has_an_access_policy(env: Env, make_settings: Callable[..., Settings]) -> None:
    app = create_app(make_settings(env=env))
    errors = route_table_errors(app)
    assert not errors, "table des politiques d'accès :\n" + "\n".join(errors)


def test_route_walk_sees_every_kind_of_route(make_settings: Callable[..., Settings]) -> None:
    """Le parcours voit les routes des routers inclus (préfixe compris) et la documentation,
    présente hors production seulement."""
    dev_routes, _ = app_routes(create_app(make_settings(env=Env.DEV)))
    prod_routes, _ = app_routes(create_app(make_settings(env=Env.PROD)))
    core = {("GET", "/healthz"), ("GET", "/readyz"), ("GET", "/metrics"), ("GET", "/v1/config")}
    assert core <= prod_routes
    assert ("POST", "/v1/reports") in prod_routes
    assert DOCS_ROUTES <= dev_routes
    assert not DOCS_ROUTES & prod_routes


def test_public_whitelist_is_closed() -> None:
    errors = public_whitelist_errors()
    assert not errors, "\n".join(errors)


def test_policies_are_well_formed() -> None:
    for key, policy in ROUTE_POLICIES.items():
        assert isinstance(policy, Policy), key
        assert policy.kind in get_args(PolicyKind), key
        assert all(isinstance(role, Role) for role in policy.roles), key
    assert ROUTE_POLICIES[("GET", "/metrics")].kind == "internal"


def test_internal_routes_are_never_relayed_by_caddy(
    make_settings: Callable[..., Settings],
) -> None:
    patterns = internal_patterns(CADDYFILE.read_text(encoding="utf-8"))
    assert patterns, "matcher @internal introuvable dans infra/Caddyfile"
    routes, _ = app_routes(create_app(make_settings()))
    errors = internal_exposure_errors(routes, patterns)
    assert not errors, "\n".join(errors)


# --- Cas témoins --------------------------------------------------------------------


async def _secret() -> dict[str, str]:
    return {"secret": "x"}


def test_undeclared_route_fails_and_is_named(make_settings: Callable[..., Settings]) -> None:
    app = create_app(make_settings())
    app.add_api_route("/v1/secret", _secret, methods=["GET"])
    errors = route_table_errors(app)
    assert len(errors) == 1
    assert errors[0].startswith("GET /v1/secret")


def test_declared_route_passes(make_settings: Callable[..., Settings]) -> None:
    app = create_app(make_settings())
    app.add_api_route("/v1/secret", _secret, methods=["GET"])
    policies = {**ROUTE_POLICIES, ("GET", "/v1/secret"): roles(Role.MUNICIPAL_ADMIN)}
    assert route_table_errors(app, policies=policies) == []


def test_public_route_outside_whitelist_fails() -> None:
    errors = public_whitelist_errors(PUBLIC_ROUTES | {("GET", "/v1/secret")})
    assert errors == ["GET /v1/secret : publique hors de la liste blanche close"]


def test_whitelist_shrunk_fails() -> None:
    errors = public_whitelist_errors(PUBLIC_ROUTES - {("GET", "/readyz")})
    assert errors == ["GET /readyz : manque à la liste blanche publique"]


def test_orphan_policy_fails(make_settings: Callable[..., Settings]) -> None:
    app = create_app(make_settings())
    policies = {**ROUTE_POLICIES, ("GET", "/v1/ghost"): DEVICE}
    errors = route_table_errors(app, policies=policies)
    assert errors == ["GET /v1/ghost : politique orpheline, aucune route de ce nom"]


def test_reserved_public_entries_may_be_absent(make_settings: Callable[..., Settings]) -> None:
    app = create_app(make_settings())
    routes, _ = app_routes(app)
    assert not (RESERVED_PUBLIC_ROUTES & routes), "entrée réservée créée : retirer ce témoin"
    assert route_table_errors(app) == []
    # Une entrée publique non réservée sans route, elle, est orpheline.
    errors = route_table_errors(app, reserved=frozenset())
    assert errors == ["GET /v1/public/map : entrée publique orpheline, aucune route de ce nom"]


def test_report_creation_is_a_real_public_route(make_settings: Callable[..., Settings]) -> None:
    """Story 1.11 : `POST /v1/reports` est publique et n'est plus réservée ; aucune route
    ne permet de modifier l'Organisation responsable d'un Signalement."""
    routes, _ = app_routes(create_app(make_settings()))
    key = ("POST", "/v1/reports")
    assert key in routes and key in PUBLIC_ROUTES and key not in RESERVED_PUBLIC_ROUTES
    assert key not in ROUTE_POLICIES
    report_routes = {route for route in routes if route[1].startswith("/v1/reports")}
    assert report_routes == {key}
    assert not [route for route in routes if "organization" in route[1] or "/orgs" in route[1]]


def test_route_both_public_and_declared_fails(make_settings: Callable[..., Settings]) -> None:
    app = create_app(make_settings())
    policies = {**ROUTE_POLICIES, ("GET", "/healthz"): DEVICE}
    errors = route_table_errors(app, policies=policies)
    assert errors == ["GET /healthz : à la fois publique et déclarée dans ROUTE_POLICIES"]


def test_unsupported_route_type_fails(make_settings: Callable[..., Settings]) -> None:
    app = create_app(make_settings())
    app.mount("/static", FastAPI())
    errors = route_table_errors(app)
    assert errors == ["Mount /static : type de route non pris en charge"]


def test_policy_rendering() -> None:
    assert str(DEVICE) == "device"
    assert str(roles(Role.MUNICIPAL_ADMIN, Role.MODERATOR)) == "roles:{moderator,municipal_admin}"
    with pytest.raises(ValueError):
        Policy("roles")
    with pytest.raises(ValueError):
        Policy("device", frozenset({Role.CITIZEN}))
    with pytest.raises(ValueError, match="politique inconnue"):
        Policy("public")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="politique inconnue"):
        Policy("Device")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="rôles hors de Role"):
        roles("admin")  # type: ignore[arg-type]


def test_internal_route_outside_caddy_matcher_fails() -> None:
    patterns = ["/metrics", "/metrics/*", "/v1/ai", "/v1/ai/*"]
    policies = {**ROUTE_POLICIES, ("GET", "/v1/debug"): INTERNAL}
    routes = {("GET", "/metrics"), ("GET", "/v1/debug")}
    assert internal_exposure_errors(routes, patterns, policies) == [
        "GET /v1/debug : politique internal, mais hors du matcher @internal du Caddyfile"
    ]


def test_ai_route_without_internal_policy_fails() -> None:
    patterns = ["/v1/ai", "/v1/ai/*"]
    routes = {("POST", "/v1/ai/classify"), ("GET", "/v1/aide")}
    declared = {("POST", "/v1/ai/classify"): DEVICE}
    assert internal_exposure_errors(routes, patterns, declared) == [
        "POST /v1/ai/classify : route de /v1/ai sans politique internal"
    ]
    internal = {("POST", "/v1/ai/classify"): INTERNAL}
    assert internal_exposure_errors(routes, patterns, internal) == []


def test_caddy_internal_matcher_is_parsed() -> None:
    caddyfile = "site {\n\t@internal path /metrics /metrics/* /v1/ai /v1/ai/*\n}\n"
    assert internal_patterns(caddyfile) == ["/metrics", "/metrics/*", "/v1/ai", "/v1/ai/*"]


def test_caddy_bounds_the_report_body() -> None:
    """Story 1.11 : Caddy refuse (413) tout corps de `POST /v1/reports` au-delà de 2 Mo."""
    caddyfile = CADDYFILE.read_text(encoding="utf-8")
    matcher = re.search(r"^\s*@reports\s+path\s+(\S+)\s*$", caddyfile, re.MULTILINE)
    assert matcher and matcher.group(1) == "/v1/reports"
    limit = re.search(r"request_body\s+@reports\s*\{\s*max_size\s+(\S+)\s*\}", caddyfile)
    assert limit and limit.group(1) == "2MB"


class _Endpoint(HTTPEndpoint):
    async def get(self, request: Request) -> PlainTextResponse:
        return PlainTextResponse("x")


async def _item(item_id: int) -> dict[str, int]:
    return {"id": item_id}


def test_route_without_methods_fails_and_is_named(make_settings: Callable[..., Settings]) -> None:
    app = create_app(make_settings())
    app.router.routes.append(Route("/v1/endpoint", _Endpoint))
    errors = route_table_errors(app)
    assert len(errors) == 1
    assert errors[0].startswith("/v1/endpoint : aucune méthode hors HEAD et OPTIONS")


def test_route_with_only_head_or_options_fails(make_settings: Callable[..., Settings]) -> None:
    app = create_app(make_settings())
    app.add_api_route("/v1/probe", _secret, methods=["HEAD", "OPTIONS"])
    errors = route_table_errors(app)
    assert len(errors) == 1
    assert errors[0].startswith("/v1/probe : aucune méthode hors HEAD et OPTIONS")


def test_routes_are_keyed_on_the_template_path(make_settings: Callable[..., Settings]) -> None:
    app = create_app(make_settings())
    app.add_api_route("/v1/items/{item_id:int}", _item, methods=["GET"])
    routes, _ = app_routes(app)
    assert ("GET", "/v1/items/{item_id}") in routes
    policies = {**ROUTE_POLICIES, ("GET", "/v1/items/{item_id}"): DEVICE}
    assert route_table_errors(app, policies=policies) == []
