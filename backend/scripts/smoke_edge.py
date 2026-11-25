"""Test de fumée du bord Caddy (story 1.3).

Depuis l'hôte, pile démarrée (`docker compose --profile demo up -d --build --wait`) :

    python backend/scripts/smoke_edge.py

Vérifie chaque ligne de la matrice I/O de la story en HTTPS, sans vérifier le certificat
local (CA interne de Caddy) :
  - coquille : `/` sert la PWA (index.html en `lang="fr"`, manifeste, service worker,
    bundle contenant le titre de `fr.json`, police Inter servie localement), avec
    `Cache-Control` (`no-cache` pour la coquille, immuable pour `/assets/`) ; un fichier
    absent (`/assets/inexistant.js`) reçoit 404, pas index.html ;
  - route profonde : `/n-importe-quoi` et les liens directs `/signaler/…` servent aussi
    index.html (`no-cache`) ; manifeste nommé, icônes 192, 512 et 512 maskable ;
    coquille et bundle compressés (gzip ou zstd) quand le client l'accepte ;
  - API : `/v1/config`, `/healthz`, `/readyz` relayés vers l'API ;
  - surfaces internes : `/metrics`, `/v1/ai/x` (et variantes) → 404 ;
  - photos : `GET`/`HEAD MEDIA_HOST/<bucket>/<clé>` relayé vers Garage → 403 sans
    signature ; tout autre chemin → 404, toute autre méthode → 405, sans atteindre Garage ;
  - HTTP : redirection vers HTTPS.

Les connexions visent `--address` (127.0.0.1 par défaut) avec le nom d'hôte en SNI et
dans `Host` : aucune résolution DNS de `*.localhost` n'est nécessaire.

Bibliothèque standard seulement. Réglages lus dans l'environnement, puis dans le `.env`
de la racine, sinon valeurs par défaut : `APP_HOST`, `MEDIA_HOST`, `HTTP_PORT`,
`HTTPS_PORT`, `S3_BUCKET`. Code de sortie 0 si toutes les lignes sont vertes.
"""

import argparse
import http.client
import json
import os
import re
import socket
import ssl
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULTS = {
    "APP_HOST": "app.localhost",
    "MEDIA_HOST": "media.localhost",
    "HTTP_PORT": "80",
    "HTTPS_PORT": "443",
    "S3_BUCKET": "terangacycle-photos",
}
# /readyz peut mettre quelques secondes à passer à 200 juste après `up --wait`.
READY_TIMEOUT_S = 60


def _setting(name: str) -> str:
    if os.environ.get(name):
        return os.environ[name]
    env_file = REPO / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() == name and value.strip():
                return value.strip()
    return DEFAULTS[name]


@dataclass
class Response:
    status: int
    headers: dict[str, str]
    body: bytes = field(repr=False)

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")


class _SniHTTPSConnection(http.client.HTTPSConnection):
    """Connexion TLS à une adresse fixe, avec un nom d'hôte choisi pour le SNI."""

    def __init__(self, address: str, port: int, server_name: str) -> None:
        context = ssl.create_default_context()
        # Certificat du CA interne de Caddy, non approuvé par l'hôte : non vérifié ici.
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        super().__init__(address, port, timeout=10, context=context)
        self._server_name = server_name

    def connect(self) -> None:
        sock = socket.create_connection((self.host, self.port), self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self._server_name)


@dataclass
class Edge:
    address: str
    app_host: str
    media_host: str
    http_port: int
    https_port: int

    def https(
        self,
        host: str,
        path: str,
        method: str = "GET",
        headers: dict[str, str] | None = None,
    ) -> Response:
        conn = _SniHTTPSConnection(self.address, self.https_port, host)
        host_header = host if self.https_port == 443 else f"{host}:{self.https_port}"
        return _send(conn, method, host_header, path, headers)

    def http(self, host: str, path: str) -> Response:
        conn = http.client.HTTPConnection(self.address, self.http_port, timeout=10)
        host_header = host if self.http_port == 80 else f"{host}:{self.http_port}"
        return _send(conn, "GET", host_header, path)


def _send(
    conn: http.client.HTTPConnection,
    method: str,
    host_header: str,
    path: str,
    headers: dict[str, str] | None = None,
) -> Response:
    try:
        conn.request(method, path, headers={"Host": host_header, **(headers or {})})
        resp = conn.getresponse()
        return Response(resp.status, {k.lower(): v for k, v in resp.getheaders()}, resp.read())
    finally:
        conn.close()


class CheckFailed(AssertionError):
    pass


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailed(message)


NO_CACHE = "no-cache"
IMMUTABLE = "public, max-age=31536000, immutable"


def _expect_cache(resp: Response, expected: str, what: str) -> None:
    value = resp.headers.get("cache-control")
    _expect(value == expected, f"{what} : Cache-Control {value!r}, attendu {expected!r}")


def _is_pwa_index(resp: Response) -> None:
    _expect(resp.status == 200, f"statut {resp.status}, attendu 200")
    _expect("text/html" in resp.headers.get("content-type", ""), "pas du HTML")
    _expect('lang="fr"' in resp.text, 'index.html sans lang="fr"')
    _expect('id="root"' in resp.text, "index.html sans #root")
    _expect_cache(resp, NO_CACHE, "index.html")


def _in_bundle(value: str, bundle: str) -> bool:
    # Le minifieur peut garder l'UTF-8 ou échapper les caractères non ASCII (é).
    return value in bundle or json.dumps(value, ensure_ascii=True)[1:-1] in bundle


def check_shell(edge: Edge) -> None:
    index = edge.https(edge.app_host, "/")
    _is_pwa_index(index)
    _expect('rel="manifest"' in index.text, "manifeste non référencé")
    for path in ("/index.html", "/manifest.webmanifest", "/sw.js", "/registerSW.js"):
        resp = edge.https(edge.app_host, path)
        _expect(resp.status == 200, f"{path} : statut {resp.status}")
        _expect_cache(resp, NO_CACHE, path)
    manifest = json.loads(edge.https(edge.app_host, "/manifest.webmanifest").body)
    _expect(manifest.get("display") == "standalone", "manifeste : display != standalone")
    _expect(manifest.get("name") == "TerangaCycle AI", f"manifeste : nom {manifest.get('name')!r}")
    icons = {(icon.get("sizes"), icon.get("purpose", "any")) for icon in manifest.get("icons", [])}
    for sizes, purpose in (("192x192", "any"), ("512x512", "any"), ("512x512", "maskable")):
        _expect((sizes, purpose) in icons, f"manifeste : icône {sizes} {purpose} absente")

    # Texte traduit : les textes de l'accueil (fr.json) figurent dans le bundle chargé par
    # index.html.
    fr = json.loads((REPO / "web" / "src" / "i18n" / "fr.json").read_text(encoding="utf-8"))
    scripts = re.findall(r'<script[^>]+src="(/assets/[^"]+\.js)"', index.text)
    _expect(bool(scripts), "aucun bundle JS dans index.html")
    responses = [edge.https(edge.app_host, src) for src in scripts]
    for src, resp in zip(scripts, responses, strict=True):
        _expect(resp.status == 200, f"{src} : statut {resp.status}")
        _expect_cache(resp, IMMUTABLE, src)
    bundle = "".join(resp.text for resp in responses)
    for key in ("tagline", "report", "reportHint"):
        _expect(_in_bundle(fr["home"][key], bundle), f"home.{key} de fr.json absent du bundle")

    # Compression (base du budget de poids, web/scripts/check-size.mjs) : la coquille et
    # le bundle sont servis compressés à un client qui l'accepte.
    for path in ("/", scripts[0]):
        resp = edge.https(edge.app_host, path, headers={"Accept-Encoding": "gzip, zstd"})
        encoding = resp.headers.get("content-encoding")
        _expect(encoding in ("gzip", "zstd"), f"{path} : Content-Encoding {encoding!r}")

    # Fichier absent : un vrai 404, jamais index.html (ni mis en cache pour un an).
    for path in ("/assets/inexistant.js", "/assets/inexistant", "/inexistant.png"):
        resp = edge.https(edge.app_host, path)
        _expect(resp.status == 404, f"{path} : statut {resp.status}, attendu 404")
        _expect('id="root"' not in resp.text, f"{path} : index.html servi")
        _expect(resp.headers.get("cache-control") != IMMUTABLE, f"{path} : 404 immuable")

    # Police Inter auto-hébergée, rien chargé depuis un domaine externe.
    styles = re.findall(r'<link[^>]+href="(/assets/[^"]+\.css)"', index.text)
    _expect(bool(styles), "aucune feuille de style dans index.html")
    css = "".join(edge.https(edge.app_host, href).text for href in styles)
    _expect("Inter Variable" in css, "police Inter absente de la feuille de style")
    _expect("--color-surface" in css, "jeton --color-surface absent de la feuille de style")
    _expect(not re.search(r"url\(\s*['\"]?(https?:)?//", css), "ressource CSS externe")
    fonts = re.findall(r"url\(\s*['\"]?(/assets/[^'\")]+\.woff2)", css)
    _expect(bool(fonts), "aucun fichier woff2 local")
    font = edge.https(edge.app_host, fonts[0])
    _expect(font.status == 200, f"{fonts[0]} : statut {font.status}")


def check_deep_route(edge: Edge) -> None:
    _is_pwa_index(edge.https(edge.app_host, "/n-importe-quoi"))
    _is_pwa_index(edge.https(edge.app_host, "/un/chemin/profond"))
    # Liens directs du parcours de signalement : index.html, toujours revalidé.
    for path in ("/signaler", "/signaler/consentement", "/signaler/capture"):
        resp = edge.https(edge.app_host, path)
        _is_pwa_index(resp)
        _expect_cache(resp, NO_CACHE, path)


def check_api(edge: Edge) -> None:
    config = edge.https(edge.app_host, "/v1/config")
    _expect(config.status == 200, f"/v1/config : statut {config.status}")
    _expect("env" in json.loads(config.body), "/v1/config : pas la réponse de l'API")

    healthz = edge.https(edge.app_host, "/healthz")
    _expect(healthz.status == 200, f"/healthz : statut {healthz.status}")
    _expect(json.loads(healthz.body) == {"status": "ok"}, "/healthz : pas la réponse de l'API")

    deadline = time.monotonic() + READY_TIMEOUT_S
    while True:
        readyz = edge.https(edge.app_host, "/readyz")
        if readyz.status == 200 or time.monotonic() > deadline:
            break
        time.sleep(2)
    _expect(readyz.status == 200, f"/readyz : statut {readyz.status}")
    _expect(json.loads(readyz.body) == {"status": "ready"}, "/readyz : pas la réponse de l'API")

    # Une route /v1 inconnue reçoit l'enveloppe d'erreur de l'API, pas index.html.
    unknown = edge.https(edge.app_host, "/v1/inexistant")
    _expect(unknown.status == 404, f"/v1/inexistant : statut {unknown.status}")
    _expect("error" in json.loads(unknown.body), "/v1/inexistant : pas l'enveloppe de l'API")


def check_internal(edge: Edge) -> None:
    for path in ("/metrics", "/metrics/", "/v1/ai", "/v1/ai/x", "/v1/ai/x/y"):
        resp = edge.https(edge.app_host, path)
        _expect(resp.status == 404, f"{path} : statut {resp.status}, attendu 404")
        _expect(b"# HELP" not in resp.body, f"{path} : métriques exposées")
        _expect(b"request_id" not in resp.body, f"{path} : relayé vers l'API")


def check_media(edge: Edge, bucket: str) -> None:
    # Lecture d'un objet du bucket : relayée à Garage, qui refuse sans signature.
    for method in ("GET", "HEAD"):
        resp = edge.https(edge.media_host, f"/{bucket}/smoke/inexistant.jpg", method)
        _expect(resp.status == 403, f"{method} : statut {resp.status}, attendu 403 de Garage")
    resp = edge.https(edge.media_host, f"/{bucket}/smoke/inexistant.jpg")
    _expect("<Error>" in resp.text, "réponse sans erreur S3 : pas Garage")

    # Le reste de l'API S3 est refusé par Caddy, sans atteindre Garage.
    for path in ("/", "/autre-bucket/x", f"/{bucket}"):
        resp = edge.https(edge.media_host, path)
        _expect(resp.status == 404, f"GET {path} : statut {resp.status}, attendu 404")
        _expect("<Error>" not in resp.text, f"GET {path} : relayé vers Garage")
    for method in ("DELETE", "PUT", "POST"):
        resp = edge.https(edge.media_host, f"/{bucket}/x", method)
        _expect(resp.status == 405, f"{method} : statut {resp.status}, attendu 405")
        _expect("<Error>" not in resp.text, f"{method} : relayé vers Garage")


def check_http_redirect(edge: Edge) -> None:
    for host in (edge.app_host, edge.media_host):
        resp = edge.http(host, "/n-importe-quoi?x=1")
        _expect(resp.status in (301, 302, 307, 308), f"{host} : statut {resp.status}")
        location = resp.headers.get("location", "")
        expected = f"https://{host}:{edge.https_port}/n-importe-quoi?x=1"
        _expect(location == expected, f"{host} : Location {location!r}, attendu {expected!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--address", default="127.0.0.1", help="adresse du bord Caddy")
    args = parser.parse_args()

    edge = Edge(
        address=args.address,
        app_host=_setting("APP_HOST"),
        media_host=_setting("MEDIA_HOST"),
        http_port=int(_setting("HTTP_PORT")),
        https_port=int(_setting("HTTPS_PORT")),
    )
    bucket = _setting("S3_BUCKET")
    checks: list[tuple[str, Callable[[], None]]] = [
        ("Coquille", lambda: check_shell(edge)),
        ("Route profonde", lambda: check_deep_route(edge)),
        ("API", lambda: check_api(edge)),
        ("Surfaces internes", lambda: check_internal(edge)),
        ("Photos", lambda: check_media(edge, bucket)),
        ("HTTP", lambda: check_http_redirect(edge)),
    ]

    print(f"Bord : https://{edge.app_host}:{edge.https_port} via {edge.address}")
    ok = True
    for name, check in checks:
        try:
            check()
        except (CheckFailed, OSError, http.client.HTTPException, ValueError) as exc:
            ok = False
            print(f"ÉCHEC  {name} : {exc}")
        else:
            print(f"OK     {name}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
