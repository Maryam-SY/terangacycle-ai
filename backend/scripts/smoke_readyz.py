"""Test de fumée de `/readyz` sur la pile Docker (story 1.2).

Depuis l'hôte, pile démarrée (`docker compose --profile demo up -d --wait`) :

    python backend/scripts/smoke_readyz.py

Pour chaque dépendance (`db`, `valkey`, `garage`, `worker`), tour à tour :
`docker compose stop`, attente de 503 sur `/readyz` (via Caddy), puis
`docker compose start`, attente de 200. Le service est redémarré même en cas
d'échec. Code de sortie 0 si les quatre passent.

Bibliothèque standard seulement. Port lu dans `HTTP_PORT` du `.env` (80 par défaut),
ou surchargé par `--base-url`.
"""

import argparse
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SERVICES = ["db", "valkey", "garage", "worker"]
# Le battement du worker vieillit en 60 s au plus : 503 attendu en moins de 120 s.
DOWN_TIMEOUT_S = 120
# Après redémarrage : base et Garage sains, worker relancé et premier battement.
UP_TIMEOUT_S = 240
POLL_S = 2


def _http_port() -> str:
    env_file = REPO / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            name, sep, value = line.partition("=")
            if sep and name.strip() == "HTTP_PORT" and value.strip():
                return value.strip()
    return "80"


def _status(url: str) -> int | None:
    try:
        with urllib.request.urlopen(url, timeout=10) as response:  # noqa: S310 (URL locale)
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return None


def _wait_for(url: str, expected: int, timeout_s: float) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if _status(url) == expected:
            return True
        time.sleep(POLL_S)
    return False


def _compose(*args: str) -> None:
    subprocess.run(  # noqa: S603 (arguments fixes)
        ["docker", "compose", "--profile", "demo", *args],  # noqa: S607
        cwd=REPO,
        check=True,
    )


def _check_service(service: str, url: str) -> bool:
    print(f"--- {service} : arrêt")
    _compose("stop", service)
    try:
        down = _wait_for(url, 503, DOWN_TIMEOUT_S)
        print(f"    /readyz = 503 pendant l'arrêt : {'OK' if down else 'ÉCHEC'}")
    finally:
        print(f"--- {service} : redémarrage")
        _compose("start", service)
    up = _wait_for(url, 200, UP_TIMEOUT_S)
    print(f"    /readyz = 200 après redémarrage : {'OK' if up else 'ÉCHEC'}")
    return down and up


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default=f"http://localhost:{_http_port()}")
    parser.add_argument("--services", nargs="+", default=SERVICES, choices=SERVICES)
    args = parser.parse_args()
    url = args.base_url.rstrip("/") + "/readyz"

    if not _wait_for(url, 200, UP_TIMEOUT_S):
        print(f"ÉCHEC : {url} ne répond pas 200 avant le test.", file=sys.stderr)
        return 1

    results = {service: _check_service(service, url) for service in args.services}
    print()
    for service, ok in results.items():
        print(f"{service:<8} {'OK' if ok else 'ÉCHEC'}")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
