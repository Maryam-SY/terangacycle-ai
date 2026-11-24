"""Génère des secrets factices pour la pile locale (démo, développement).

Usage, depuis n'importe quel dossier :

    python infra/gen-dev-secrets.py          # crée ce qui manque, sans rien écraser
    python infra/gen-dev-secrets.py --force  # régénère tous les secrets

Écrit `.env.secrets/` à la racine du dépôt (ignoré par Git), un fichier par secret,
monté dans `/run/secrets/` par Compose : mots de passe de base, secret RPC et clé S3
de Garage (`garage.env`), et tout l'inventaire d'AD-26 lu par l'API et le worker.
Les fichiers `s3_access_key_id` et `s3_secret_access_key` reprennent la clé de
`garage.env` quand il existe déjà. Copie aussi `.env.example` en `.env` s'il
manque. Changer un mot de passe de base après le premier démarrage exige de recréer
le volume (`docker compose --profile demo down -v`) : les rôles sont créés une fois.

Bibliothèque standard seulement : aucune dépendance à installer.
"""

import argparse
import base64
import json
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
# Clé S3 de Garage : un seul jeu indissociable. Repris tel quel si garage.env est
# complet, sinon régénéré en entier (jamais de fichiers s3_* d'une autre clé).
S3_SET = {"garage.env", "s3_access_key_id", "s3_secret_access_key"}


def _password() -> str:
    # Alphabet URL-safe : utilisable tel quel dans une URL de connexion.
    return secrets.token_urlsafe(32)


def _b64_32() -> str:
    """32 octets aléatoires en base64 (peppers, clés AES, graine Ed25519)."""
    return base64.b64encode(secrets.token_bytes(32)).decode("ascii")


def _read_garage_keys(path: Path) -> tuple[str, str] | None:
    """Clé S3 (identifiant, secret) d'un `garage.env` existant, sinon None."""
    if not path.is_file():
        return None
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        name, sep, value = line.partition("=")
        if sep:
            values[name.strip()] = value.strip()
    access = values.get("GARAGE_DEFAULT_ACCESS_KEY")
    secret = values.get("GARAGE_DEFAULT_SECRET_KEY")
    return (access, secret) if access and secret else None


def _build_secrets(s3_keys: tuple[str, str] | None) -> dict[str, str]:
    # Garage : identifiant de clé « GK » + 24 caractères hexadécimaux, secret de 64.
    # `s3_keys` : clé d'un garage.env existant et complet, reprise pour tout le jeu S3.
    access_key, secret_key = s3_keys or ("GK" + secrets.token_hex(12), secrets.token_hex(32))
    return {
        "postgres_password": _password(),
        "db_migrator_password": _password(),
        "db_app_password": _password(),
        "garage_rpc_secret": secrets.token_hex(32),
        # L'image Garage ne lit la clé S3 par défaut que dans l'environnement.
        "garage.env": (
            f"GARAGE_DEFAULT_ACCESS_KEY={access_key}\nGARAGE_DEFAULT_SECRET_KEY={secret_key}\n"
        ),
        # Inventaire AD-26, lu par l'API et le worker dans /run/secrets/.
        "jwt_signing_keys": json.dumps({f"dev-{secrets.token_hex(4)}": _b64_32()}),
        "phone_pepper": _b64_32(),
        "device_id_pepper": _b64_32(),
        "phone_enc_keys": json.dumps({"k1": _b64_32()}),
        "totp_enc_key": _b64_32(),
        # Valeur temporaire : la story 4.9 imposera une vraie clé P-256.
        "vapid_private_key": "dev-placeholder-" + secrets.token_urlsafe(32),
        "s3_access_key_id": access_key,
        "s3_secret_access_key": secret_key,
        "alert_webhook_url": "http://localhost/alert-disabled",
    }


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")
    # Lisible par l'utilisateur non root des conteneurs (postgres, api) ; le dossier,
    # lui, est réservé au propriétaire.
    path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="régénère tous les secrets")
    args = parser.parse_args(argv)

    SECRETS_DIR.mkdir(exist_ok=True)
    if os.name == "posix":
        SECRETS_DIR.chmod(stat.S_IRWXU)

    created, kept, overwritten_db = [], [], []
    s3_keys = None if args.force else _read_garage_keys(SECRETS_DIR / "garage.env")
    for name, value in _build_secrets(s3_keys).items():
        path = SECRETS_DIR / name
        if path.is_dir():
            # Docker crée un dossier vide à la place d'un secret absent lors du montage :
            # on le remplace par le fichier attendu.
            path.rmdir()
        if name in S3_SET:
            # Jeu S3 : chaque fichier doit porter la clé retenue, sinon il est réécrit.
            if path.is_file() and path.read_text(encoding="utf-8") == value:
                kept.append(name)
            else:
                _write(path, value)
                created.append(name)
            continue
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
