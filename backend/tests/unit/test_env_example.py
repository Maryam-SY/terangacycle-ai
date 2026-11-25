"""`.env.example` reste aligné sur `Settings` et ne contient aucun secret (story 1.5).

Les secrets (inventaire AD-26, mots de passe et URL de base) sont lus dans
`/run/secrets/`, jamais dans `.env` : leur nom ne doit pas y apparaître comme variable.
"""

import math
import re
from collections import Counter
from pathlib import Path

import pytest

from app.core.config import REQUIRED_SECRETS, Settings

ENV_EXAMPLE = Path(__file__).resolve().parents[3] / ".env.example"

# `NOM=valeur`, éventuellement commenté (`# NOM=`) : variable documentée mais facultative.
_ASSIGNMENT = re.compile(r"^\s*(?:#\s*)?(?P<name>[A-Z][A-Z0-9_]*)=(?P<value>.*)$")
_SECRET_PREFIXES = ("sk-", "ghp_", "github_pat_", "AKIA", "ASIA", "xox", "-----BEGIN")
_TOKEN = re.compile(r"[A-Za-z0-9+/=_\-]{24,}")


def _variables(text: str) -> dict[str, str]:
    variables = {}
    for line in text.splitlines():
        match = _ASSIGNMENT.match(line)
        if match:
            variables[match["name"]] = match["value"].strip().strip("\"'")
    return variables


def _entropy(value: str) -> float:
    counts = Counter(value)
    return -sum(n / len(value) * math.log2(n / len(value)) for n in counts.values())


def looks_like_secret(value: str) -> bool:
    """Préfixe de jeton connu, ou longue chaîne aléatoire (lettres, chiffres, forte entropie)."""
    if any(value.startswith(prefix) or f"//{prefix}" in value for prefix in _SECRET_PREFIXES):
        return True
    for token in _TOKEN.findall(value):
        if (
            any(c.isdigit() for c in token)
            and any(c.isalpha() for c in token)
            and _entropy(token) >= 3.5
        ):
            return True
    return False


def _is_secret_field(name: str) -> bool:
    # Champ `SecretStr` (mots de passe, URL de base, inventaire AD-26) : lu dans /run/secrets/.
    return name in REQUIRED_SECRETS or "SecretStr" in str(Settings.model_fields[name].annotation)


@pytest.fixture(scope="module")
def variables() -> dict[str, str]:
    return _variables(ENV_EXAMPLE.read_text(encoding="utf-8"))


def test_every_public_setting_is_documented(variables: dict[str, str]) -> None:
    public = [name.upper() for name in Settings.model_fields if not _is_secret_field(name)]
    missing = [name for name in public if name not in variables]
    assert not missing, f"absents de .env.example : {missing}"


def test_no_secret_name_in_env_example(variables: dict[str, str]) -> None:
    secret_names = {name.upper() for name in Settings.model_fields if _is_secret_field(name)}
    assert {name.upper() for name in REQUIRED_SECRETS} <= secret_names
    leaked = sorted(secret_names & variables.keys())
    assert not leaked, f"secrets déclarés dans .env.example (attendus dans /run/secrets) : {leaked}"


def test_no_value_looks_like_a_secret(variables: dict[str, str]) -> None:
    suspicious = sorted(name for name, value in variables.items() if looks_like_secret(value))
    assert not suspicious, f"valeurs qui ressemblent à un secret : {suspicious}"


# Valeurs fabriquées à l'exécution : aucun jeton réel, ni même plausible, dans le dépôt.
@pytest.mark.parametrize(
    "value",
    [
        "sk-" + "a1B2" * 8,
        "ghp_" + "Z9y8" * 9,
        "AKIA" + "QRSTUVWXYZ234567",
        "-----BEGIN " + "PRIVATE KEY-----",
        "x7Kq2mVn9pL4wR8tY3zB6cD1fG5hJ0sA",  # chaîne aléatoire de 32 caractères
        "redis://:" + "Pq7rT2xW9mK4vN8bL3cZ6yH1@valkey:6379/0",
    ],
)
def test_detects_fabricated_secrets(value: str) -> None:
    assert looks_like_secret(value)


@pytest.mark.parametrize(
    "value",
    [
        "demo",
        "INFO",
        "redis://valkey:6379/0",
        "http://garage:3900",
        "terangacycle-photos",
        "app.localhost",
        "teranga_migrator",
        "",
    ],
)
def test_accepts_ordinary_values(value: str) -> None:
    assert not looks_like_secret(value)
