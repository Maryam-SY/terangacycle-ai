"""Test de fumée de `/readyz` sur la pile Docker (story 1.2).

Depuis l'hôte, pile démarrée (`docker compose --profile demo up -d --wait`) :

    python backend/scripts/smoke_readyz.py

Pour chaque dépendance (`db`, `valkey`, `garage`, `worker`), tour à tour :
`docker compose stop`, attente de 503 sur `/readyz` (via Caddy, en HTTPS sur
`APP_HOST`), puis `docker compose start`, attente de 200. Le service est redémarré
même en cas d'échec. Code de sortie 0 si les quatre passent.

Bibliothèque standard seulement. Connexion comme `smoke_edge.py` : `APP_HOST` et
`HTTPS_PORT` lus dans l'environnement ou le `.env`, certificat local non vérifié,
adresse surchargée par `--address` (127.0.0.1 par défaut).
"""

import argparse
import http.client
import subprocess
import sys
import time
from pathlib import Path

from smoke_edge import Edge, _setting

REPO = Path(__file__).resolve().parents[2]
SERVICES = ["db", "valkey", "garage", "worker"]
# Le battement du worker vieillit en 60 s au plus : 503 attendu en moins de 120 s.
DOWN_TIMEOUT_S = 120
# Après redémarrage : base et Garage sains, worker relancé et premier battement.
UP_TIMEOUT_S = 240
POLL_S = 2


def _status(edge: Edge) -> int | None:
    try:
        return edge.https(edge.app_host, "/readyz").status
    except (OSError, http.client.HTTPException):
        return None


def _wait_for(edge: Edge, expected: int, timeout_s: float) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if _status(edge) == expected:
            return True
        time.sleep(POLL_S)
    return False


def _compose(*args: str) -> None:
    subprocess.run(  # noqa: S603 (arguments fixes)
        ["docker", "compose", "--profile", "demo", *args],  # noqa: S607
        cwd=REPO,
        check=True,
    )


def _check_service(service: str, edge: Edge) -> bool:
    print(f"--- {service} : arrêt")
    _compose("stop", service)
    try:
        down = _wait_for(edge, 503, DOWN_TIMEOUT_S)
        print(f"    /readyz = 503 pendant l'arrêt : {'OK' if down else 'ÉCHEC'}")
    finally:
        print(f"--- {service} : redémarrage")
        _compose("start", service)
    up = _wait_for(edge, 200, UP_TIMEOUT_S)
    print(f"    /readyz = 200 après redémarrage : {'OK' if up else 'ÉCHEC'}")
    return down and up


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--address", default="127.0.0.1", help="adresse du bord Caddy")
    parser.add_argument("--services", nargs="+", default=SERVICES, choices=SERVICES)
    args = parser.parse_args()
    edge = Edge(
        address=args.address,
        app_host=_setting("APP_HOST"),
        media_host=_setting("MEDIA_HOST"),
        http_port=int(_setting("HTTP_PORT")),
        https_port=int(_setting("HTTPS_PORT")),
    )
    url = f"https://{edge.app_host}:{edge.https_port}/readyz"

    if not _wait_for(edge, 200, UP_TIMEOUT_S):
        print(f"ÉCHEC : {url} ne répond pas 200 avant le test.", file=sys.stderr)
        return 1

    results = {service: _check_service(service, edge) for service in args.services}
    print()
    for service, ok in results.items():
        print(f"{service:<8} {'OK' if ok else 'ÉCHEC'}")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
