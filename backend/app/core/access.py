"""Politique d'accès déclarée de chaque route (AD-9), vérifiée par un test d'architecture.

Une déclaration, aucune logique d'autorisation : la story 2.5 branchera `require_role`
sur cette table. Toute route de `create_app()` est soit dans la liste blanche publique
close (`PUBLIC_ROUTES`), soit déclarée dans `ROUTE_POLICIES`, soit une page de la
documentation OpenAPI (`DOCS_ROUTES`, coupée en production) ;
`tests/architecture/test_route_policies.py` échoue sinon.

Une route est identifiée par sa méthode et son chemin gabarit : `("GET", "/v1/reports/{id}")`.
"""

from dataclasses import dataclass, field
from typing import Literal, get_args

from app.core.enums import Role

type RouteKey = tuple[str, str]
PolicyKind = Literal["device", "roles", "internal"]


@dataclass(frozen=True)
class Policy:
    """Politique attendue d'une route non publique.

    - `device` : principal appareil (Citoyen anonyme, `X-Device-Id`) ;
    - `roles` : Utilisateur connecté ayant l'un des rôles listés ;
    - `internal` : jamais exposée par Caddy (réseau Compose seulement).
    """

    kind: PolicyKind
    roles: frozenset[Role] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        # Garde à l'exécution : `Policy("public")` contournerait la liste blanche close.
        if self.kind not in get_args(PolicyKind):
            raise ValueError(f"politique inconnue : {self.kind!r}")
        if not all(isinstance(role, Role) for role in self.roles):
            raise ValueError(f"rôles hors de Role : {sorted(map(str, self.roles))}")
        if (self.kind == "roles") != bool(self.roles):
            raise ValueError("seule une politique `roles` liste des rôles, et au moins un")

    def __str__(self) -> str:
        if self.kind == "roles":
            return "roles:{" + ",".join(sorted(self.roles)) + "}"
        return self.kind


DEVICE = Policy("device")
INTERNAL = Policy("internal")


def roles(*allowed: Role) -> Policy:
    """Politique réservée aux rôles donnés : `roles(Role.MODERATOR, Role.MUNICIPAL_ADMIN)`."""
    return Policy("roles", frozenset(allowed))


# Liste blanche publique close (AD-9) : aucune autre route n'est publique.
PUBLIC_ROUTES: frozenset[RouteKey] = frozenset(
    {
        ("GET", "/healthz"),
        ("GET", "/readyz"),
        ("GET", "/v1/config"),
        ("POST", "/v1/reports"),
        ("GET", "/v1/public/map"),
    }
)

# Entrées publiques réservées à des stories ultérieures (carte publique de la story 7.6) :
# leur route peut ne pas encore exister. `POST /v1/reports` existe depuis la story 1.11.
RESERVED_PUBLIC_ROUTES: frozenset[RouteKey] = frozenset(
    {
        ("GET", "/v1/public/map"),
    }
)

# Documentation OpenAPI de FastAPI : exemptée à part, absente en production (AD-23).
DOCS_ROUTES: frozenset[RouteKey] = frozenset(
    {
        ("GET", "/docs"),
        ("GET", "/docs/oauth2-redirect"),
        ("GET", "/redoc"),
        ("GET", "/openapi.json"),
    }
)

# Politique de chaque route non publique. Chaque story qui crée une route l'ajoute ici.
ROUTE_POLICIES: dict[RouteKey, Policy] = {
    ("GET", "/metrics"): INTERNAL,
}
