"""Hygiène du dépôt public (story 1.5).

Vérifie :
  - `git ls-files` : aucun document interne (dossier `TerangaCycle AI`, à toute profondeur,
    sans tenir compte de la casse), aucun `.env` ni `.env.secrets/` suivi (seul
    `.env.example` l'est), aucune clé ni certificat (`*.pem`, `*.key`, `*.p12`, `*.crt`) ;
  - `.gitignore` ignore vraiment les chemins sensibles (`git check-ignore --no-index`),
    et pas `.env.example` ;
  - `LICENSE` existe et contient le texte de la GNU AGPL ;
  - les exceptions d'audit de `security/audit-exceptions.toml` sont valides et non expirées.

Usage : python3 scripts/ci/check_repo_hygiene.py [--root <dépôt>]
Code de sortie 1 s'il y a au moins un problème (tous sont listés). Bibliothèque standard seulement.
"""

import argparse
import datetime as dt
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))

import audit_exceptions  # noqa: E402  (module voisin, après l'ajout au chemin)

REPO = Path(__file__).resolve().parents[2]

# Documents internes de l'équipe (noms, clé Figma) : jamais publiés.
INTERNAL_DIR = "terangacycle ai"  # comparé sans tenir compte de la casse

# Clés et certificats : jamais suivis par Git.
KEY_SUFFIXES = (".pem", ".key", ".p12", ".crt")

# Chemins témoins que `.gitignore` doit ignorer, et ceux qu'il doit laisser suivre.
MUST_BE_IGNORED = (
    ".env",
    ".env.local",
    ".env.secrets/x",
    "TerangaCycle AI/x",
    "k.pem",
    "web/node_modules/x",
)
MUST_NOT_BE_IGNORED = (".env.example",)

LICENSE_MARKER = "GNU AFFERO GENERAL PUBLIC LICENSE"
EXCEPTIONS_FILE = PurePosixPath("security/audit-exceptions.toml")


def tracked_files(root: Path) -> list[str]:
    """Chemins suivis par Git (`git ls-files -z`), relatifs à `root`."""
    result = subprocess.run(  # noqa: S603  (commande fixe, sans entrée externe)
        ["git", "-C", str(root), "ls-files", "-z"],  # noqa: S607
        capture_output=True,
        check=True,
    )
    return [path for path in result.stdout.decode("utf-8").split("\0") if path]


def forbidden_tracked(paths: Iterable[str]) -> list[str]:
    problems = []
    for path in paths:
        pure = PurePosixPath(path)
        name = pure.name
        if any(part.casefold() == INTERNAL_DIR for part in pure.parts):
            problems.append(f"document interne suivi par Git : {path}")
        elif ".env.secrets" in pure.parts[:-1]:
            problems.append(f"secret suivi par Git : {path}")
        elif (name == ".env" or name.startswith(".env.")) and name != ".env.example":
            problems.append(f"fichier d'environnement suivi par Git : {path}")
        elif name.lower().endswith(KEY_SUFFIXES):
            problems.append(f"clé ou certificat suivi par Git : {path}")
    return problems


def _is_ignored(root: Path, path: str) -> bool:
    """`git check-ignore --no-index -q` : vrai si `.gitignore` ignore `path`."""
    result = subprocess.run(  # noqa: S603  (commande fixe, chemins témoins constants)
        ["git", "-C", str(root), "check-ignore", "--no-index", "-q", path],  # noqa: S607
        capture_output=True,
    )
    if result.returncode not in (0, 1):
        raise subprocess.CalledProcessError(result.returncode, result.args, stderr=result.stderr)
    return result.returncode == 0


def gitignore_problems(root: Path) -> list[str]:
    if not (root / ".gitignore").is_file():
        return [".gitignore absent"]
    try:
        problems = [
            f".gitignore n'ignore pas : {path}"
            for path in MUST_BE_IGNORED
            if not _is_ignored(root, path)
        ]
        problems += [
            f".gitignore ignore à tort : {path}"
            for path in MUST_NOT_BE_IGNORED
            if _is_ignored(root, path)
        ]
    except (OSError, subprocess.CalledProcessError) as exc:
        return [f"git check-ignore a échoué : {exc}"]
    return problems


def license_problems(root: Path) -> list[str]:
    path = root / "LICENSE"
    if not path.is_file():
        return ["LICENSE absent"]
    if LICENSE_MARKER not in path.read_text(encoding="utf-8", errors="replace"):
        return [f"LICENSE ne contient pas « {LICENSE_MARKER} »"]
    return []


def exception_problems(root: Path, today: dt.date | None = None) -> list[str]:
    try:
        audit_exceptions.load(root / EXCEPTIONS_FILE, today)
    except audit_exceptions.ExceptionsError as exc:
        return [f"{EXCEPTIONS_FILE.parent}/{problem}" for problem in exc.problems]
    return []


def check(
    root: Path, today: dt.date | None = None, tracked: Iterable[str] | None = None
) -> list[str]:
    """Tous les problèmes d'hygiène du dépôt `root` (liste vide si tout va bien)."""
    if tracked is None:
        try:
            tracked = tracked_files(root)
        except (OSError, subprocess.CalledProcessError) as exc:
            return [f"git ls-files a échoué : {exc}"]
    return [
        *forbidden_tracked(tracked),
        *gitignore_problems(root),
        *license_problems(root),
        *exception_problems(root, today),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hygiène du dépôt public.")
    parser.add_argument("--root", type=Path, default=REPO)
    args = parser.parse_args(argv)
    problems = check(args.root.resolve())
    if problems:
        print(f"Hygiène du dépôt : {len(problems)} problème(s) :")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("Hygiène du dépôt : aucun problème.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
