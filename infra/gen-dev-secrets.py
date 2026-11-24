"""Génère des secrets factices pour la pile locale (démo, développement).

Usage, depuis n'importe quel dossier :

    python infra/gen-dev-secrets.py          # crée ce qui manque, sans rien écraser
    python infra/gen-dev-secrets.py --force  # régénère tous les secrets

Écrit `.env.secrets/` à la racine du dépôt (ignoré par Git), un fichier par secret,
monté dans `/run/secrets/` par Compose. Copie aussi `.env.example` en `.env` s'il
manque. Changer un mot de passe de base après le premier démarrage exige de recréer
le volume (`docker compose --profile demo down -v`) : les rôles sont créés une fois.

Bibliothèque standard seulement : aucune dépendance à installer.
"""

import argparse
import os
import secrets
import shutil
import stat
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SECRETS_DIR = REPO / ".env.secrets"
# Secrets lus une seule fois, à la création du volume de la base.
DB_SECRETS = {"postgres_password", "db_migrator_password", "db_app_password"}


def _password() -> str:
    # Alphabet URL-safe : utilisable tel quel dans une URL de connexion.
    return secrets.token_urlsafe(32)


def _build_secrets() -> dict[str, str]:
    # Garage : identifiant de clé « GK » + 24 caractères hexadécimaux, secret de 64.
    access_key = "GK" + secrets.token_hex(12)
    secret_key = secrets.token_hex(32)
    return {
        "postgres_password": _password(),
        "db_migrator_password": _password(),
        "db_app_password": _password(),
        "garage_rpc_secret": secrets.token_hex(32),
        # L'image Garage ne lit la clé S3 par défaut que dans l'environnement.
        "garage.env": (
            f"GARAGE_DEFAULT_ACCESS_KEY={access_key}\nGARAGE_DEFAULT_SECRET_KEY={secret_key}\n"
        ),
    }


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")
    # Lisible par l'utilisateur non root des conteneurs (postgres, api) ; le dossier,
    # lui, est réservé au propriétaire.
    path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="régénère tous les secrets")
    args = parser.parse_args()

    SECRETS_DIR.mkdir(exist_ok=True)
    if os.name == "posix":
        SECRETS_DIR.chmod(stat.S_IRWXU)

    created, kept, overwritten_db = [], [], []
    for name, value in _build_secrets().items():
        path = SECRETS_DIR / name
        if path.is_dir():
            # Docker crée un dossier vide à la place d'un secret absent lors du montage :
            # on le remplace par le fichier attendu.
            path.rmdir()
        if path.exists() and not args.force:
            kept.append(name)
            continue
        if path.exists() and name in DB_SECRETS:
            overwritten_db.append(name)
        _write(path, value)
        created.append(name)

    env_file, env_example = REPO / ".env", REPO / ".env.example"
    if not env_file.exists():
        shutil.copyfile(env_example, env_file)
        print("Copié : .env.example -> .env")

    for name in created:
        print(f"Créé : .env.secrets/{name}")
    for name in kept:
        print(f"Gardé : .env.secrets/{name} (utiliser --force pour régénérer)")
    if overwritten_db:
        print(
            "\nATTENTION : mots de passe de base régénérés ("
            + ", ".join(overwritten_db)
            + ").\nLes rôles ne sont créés qu'à l'initialisation du volume : la base existante"
            " refusera les nouveaux mots de passe.\nRecréer le volume (efface les données) :"
            " docker compose --profile demo down -v",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
