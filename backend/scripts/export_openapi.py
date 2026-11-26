"""Export de l'OpenAPI de l'API pour le client généré de la PWA (story 1.13).

Depuis `backend/` :

    uv run python scripts/export_openapi.py

Construit l'application (`create_app`, réglages `ENV=dev`), sans lifespan ni base, et
écrit `web/src/api/openapi.json` (chemin relatif à ce script) : JSON indenté, fin de ligne
finale, mêmes octets d'une exécution à l'autre. Puis, dans `web/` : `npm run api:types`.
La CI relance l'export et refuse toute différence avec le fichier versionné.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
OUTPUT = BACKEND.parent / "web" / "src" / "api" / "openapi.json"

# Lancé comme `python scripts/export_openapi.py` : le paquet `app` est dans `backend/`.
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.config import load_settings  # noqa: E402
from app.core.enums import Env  # noqa: E402
from app.main import create_app  # noqa: E402


def build_openapi() -> dict[str, Any]:
    """OpenAPI de l'application construite avec des réglages de développement.

    Les secrets éphémères du mode `dev` suffisent : rien n'est démarré ni connecté, et
    aucun réglage n'apparaît dans le document."""
    # Le journal des secrets éphémères n'a pas d'intérêt ici.
    logging.getLogger("app.core.config").setLevel(logging.ERROR)
    settings = load_settings(env=Env.DEV, demo_mode=False, log_level="ERROR")
    return create_app(settings).openapi()


def render(openapi: dict[str, Any]) -> str:
    """Texte stable : indentation de 2, caractères non ASCII gardés, fin de ligne finale."""
    return json.dumps(openapi, indent=2, ensure_ascii=False) + "\n"


def export(output: Path = OUTPUT) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    # Octets écrits tels quels (LF, UTF-8), quel que soit le système.
    output.write_bytes(render(build_openapi()).encode("utf-8"))
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, default=OUTPUT, help="fichier écrit")
    args = parser.parse_args()
    written = export(args.output)
    print(f"OpenAPI écrite : {written}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
