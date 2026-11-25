"""Exceptions d'audit datées : `security/audit-exceptions.toml` (story 1.5).

Une exception porte un outil, un identifiant, une raison et une date d'expiration.
Une exception invalide ou expirée fait échouer la CI.

Usage (depuis la racine du dépôt) :
    python3 scripts/ci/audit_exceptions.py check
    python3 scripts/ci/audit_exceptions.py pip-audit-args
        → `--ignore-vuln=<id> …` sur une ligne, pour pip-audit
    python3 scripts/ci/audit_exceptions.py trivyignore <fichier>
        → écrit le `.trivyignore` de Trivy
    python3 scripts/ci/audit_exceptions.py npm-audit <rapport.json> [--audit-level high]
        → filtre le rapport `npm audit --json` ; échec s'il reste une vulnérabilité

Bibliothèque standard seulement.
"""

import argparse
import datetime as dt
import json
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEFAULT_FILE = REPO / "security" / "audit-exceptions.toml"

TOOLS = ("pip-audit", "npm-audit", "trivy")
FIELDS = ("tool", "id", "reason", "expires")

# Niveaux de npm audit, du moins au plus grave.
NPM_LEVELS = ("info", "low", "moderate", "high", "critical")
_GHSA = re.compile(r"GHSA(?:-[23456789cfghjmpqrvwx]{4}){3}")
# Identifiant sûr à recopier dans une option ou un fichier (pas d'espace ni de saut de ligne).
_ID = re.compile(r"^[A-Za-z0-9._:-]+$")
# npm audit : avis GitHub (GHSA-xxxx-xxxx-xxxx) ou numéro d'avis du registre.
_NPM_ID = re.compile(rf"^(?:{_GHSA.pattern}|[0-9]+)$")
# Une exception se renouvelle au plus tous les 90 jours, avec une raison relue.
MAX_DAYS = 90


@dataclass(frozen=True)
class AuditException:
    tool: str
    id: str
    reason: str
    expires: dt.date


class ExceptionsError(Exception):
    """Fichier d'exceptions invalide ou exception expirée ; le message liste chaque problème."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__("\n".join(problems))
        self.problems = problems


def today_utc() -> dt.date:
    return dt.datetime.now(dt.UTC).date()


def _parse_date(value: object) -> dt.date | None:
    # Date TOML native (expires = 2027-01-31) ou chaîne ISO ("2027-01-31").
    if isinstance(value, dt.datetime):
        return None
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def load(path: Path = DEFAULT_FILE, today: dt.date | None = None) -> list[AuditException]:
    """Lit et valide les exceptions ; lève `ExceptionsError` si l'une est invalide ou expirée."""
    today = today or today_utc()
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ExceptionsError([f"{path.name} : fichier absent"]) from None
    except tomllib.TOMLDecodeError as exc:
        raise ExceptionsError([f"{path.name} : TOML invalide ({exc})"]) from None

    problems: list[str] = []
    unknown = sorted(set(data) - {"exception"})
    if unknown:
        problems.append(f"{path.name} : clés inconnues : {', '.join(unknown)}")
    entries = data.get("exception", [])
    if not isinstance(entries, list):
        problems.append(f"{path.name} : `exception` doit être un tableau [[exception]]")
        entries = []

    exceptions: list[AuditException] = []
    for index, entry in enumerate(entries, start=1):
        label = f"{path.name} : exception n° {index}"
        if not isinstance(entry, dict):
            problems.append(f"{label} : table attendue")
            continue
        missing = [name for name in FIELDS if not str(entry.get(name, "")).strip()]
        extra = sorted(set(entry) - set(FIELDS))
        if missing:
            problems.append(f"{label} : champs manquants ou vides : {', '.join(missing)}")
        if extra:
            problems.append(f"{label} : champs inconnus : {', '.join(extra)}")
        if missing or extra:
            continue
        ident = str(entry["id"]).strip()
        label = f"{label} ({ident})"
        tool = str(entry["tool"]).strip()
        if tool not in TOOLS:
            problems.append(f"{label} : outil inconnu « {tool} » (attendu : {', '.join(TOOLS)})")
            continue
        if not _ID.fullmatch(ident):
            problems.append(f"{label} : `id` invalide (lettres, chiffres, « . _ : - » seulement)")
            continue
        if tool == "npm-audit" and not _NPM_ID.fullmatch(ident):
            problems.append(f"{label} : `id` npm-audit attendu : GHSA-xxxx-xxxx-xxxx ou numéro")
            continue
        reason = str(entry["reason"])
        # Un saut de ligne injecterait une ligne dans .trivyignore.
        if reason.splitlines() != [reason]:
            problems.append(f"{label} : `reason` doit tenir sur une ligne")
            continue
        expires = _parse_date(entry["expires"])
        if expires is None:
            problems.append(f"{label} : `expires` doit être une date ISO (AAAA-MM-JJ)")
            continue
        if expires < today:
            problems.append(f"{label} : expirée le {expires.isoformat()}")
            continue
        if expires > today + dt.timedelta(days=MAX_DAYS):
            problems.append(
                f"{label} : `expires` à plus de {MAX_DAYS} jours ({expires.isoformat()})"
            )
            continue
        exceptions.append(AuditException(tool, ident, reason.strip(), expires))
    if problems:
        raise ExceptionsError(problems)
    return exceptions


def ids_for(exceptions: list[AuditException], tool: str) -> list[str]:
    return [exc.id for exc in exceptions if exc.tool == tool]


def pip_audit_args(exceptions: list[AuditException]) -> str:
    return " ".join(f"--ignore-vuln={ident}" for ident in ids_for(exceptions, "pip-audit"))


def trivyignore(exceptions: list[AuditException]) -> str:
    """Contenu de `.trivyignore` : la raison en commentaire, l'expiration au format Trivy."""
    lines = ["# Généré par scripts/ci/audit_exceptions.py depuis security/audit-exceptions.toml."]
    for exc in exceptions:
        if exc.tool == "trivy":
            lines.append(f"# {exc.reason}")
            # Trivy cesse d'ignorer à 00:00 UTC du jour `exp` : le lendemain de `expires`,
            # comme le contrôle d'hygiène (exception valable jusqu'à sa date incluse).
            lines.append(f"{exc.id} exp:{(exc.expires + dt.timedelta(days=1)).isoformat()}")
    return "\n".join(lines) + "\n"


def _advisory_ids(advisory: dict[str, object]) -> set[str]:
    ids = {str(advisory["source"])} if advisory.get("source") is not None else set()
    ids.update(_GHSA.findall(str(advisory.get("url", ""))))
    return ids


def npm_findings(
    report: dict[str, object], exceptions: list[AuditException], level: str = "high"
) -> list[str]:
    """Vulnérabilités du rapport `npm audit --json` (v2) au moins de gravité `level`,
    hors exceptions. Lève `ValueError` si le rapport est inexploitable."""
    if "error" in report:
        raise ValueError(f"npm audit a échoué : {json.dumps(report['error'], ensure_ascii=False)}")
    vulnerabilities = report.get("vulnerabilities")
    if not isinstance(vulnerabilities, dict):
        raise ValueError("rapport npm audit sans `vulnerabilities` (format v2 attendu)")
    threshold = NPM_LEVELS.index(level)
    ignored = set(ids_for(exceptions, "npm-audit"))
    findings: dict[str, str] = {}
    for package, entry in vulnerabilities.items():
        # `via` mêle des avis (dict) et des noms de paquets vulnérables par transitivité
        # (str) : seuls les avis comptent, chacun est rattaché à son paquet.
        for advisory in entry.get("via", []) if isinstance(entry, dict) else []:
            if not isinstance(advisory, dict):
                continue
            severity = str(advisory.get("severity", "")).lower()
            if severity not in NPM_LEVELS or NPM_LEVELS.index(severity) < threshold:
                continue
            ids = _advisory_ids(advisory)
            if ids & ignored:
                continue
            key = min(ids, key=lambda i: (not i.startswith("GHSA"), i)) if ids else package
            title = advisory.get("title", "")
            findings[key] = f"{severity} : {advisory.get('name', package)} — {title} ({key})"
    return sorted(findings.values())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="valide les exceptions (échec si expirée)")
    sub.add_parser("pip-audit-args", help="options --ignore-vuln de pip-audit")
    trivy = sub.add_parser("trivyignore", help="écrit le .trivyignore")
    trivy.add_argument("output", type=Path)
    npm = sub.add_parser("npm-audit", help="filtre un rapport npm audit --json")
    npm.add_argument("report", type=Path)
    npm.add_argument("--audit-level", choices=NPM_LEVELS, default="high")
    args = parser.parse_args(argv)

    try:
        exceptions = load(args.file)
    except ExceptionsError as exc:
        for problem in exc.problems:
            print(f"::error::{problem}", file=sys.stderr)
        return 1

    if args.command == "check":
        print(f"Exceptions d'audit : {len(exceptions)} valide(s), aucune expirée.")
    elif args.command == "pip-audit-args":
        print(pip_audit_args(exceptions))
    elif args.command == "trivyignore":
        args.output.write_text(trivyignore(exceptions), encoding="utf-8")
    else:
        try:
            report = json.loads(args.report.read_text(encoding="utf-8"))
            findings = npm_findings(report, exceptions, args.audit_level)
        except (OSError, ValueError) as exc:
            print(f"::error::{exc}", file=sys.stderr)
            return 1
        if findings:
            print(f"npm audit : {len(findings)} vulnérabilité(s) {args.audit_level} ou plus :")
            for finding in findings:
                print(f"  - {finding}")
            return 1
        print(f"npm audit : aucune vulnérabilité {args.audit_level} ou plus (hors exceptions).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
