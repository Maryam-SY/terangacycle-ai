"""Scripts de contrôle de la CI (story 1.5) : `scripts/ci/*.py`, sur des fichiers témoins.

Chaque ligne de la matrice I/O de la story pour `check_pinning.py`, `check_repo_hygiene.py`
et les exceptions d'audit datées, plus la règle Figma de `.gitleaks.toml`.
Toutes les valeurs « secrètes » sont fabriquées à l'exécution : aucune n'est réelle.
"""

import datetime as dt
import importlib
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from types import ModuleType

import pytest

REPO = Path(__file__).resolve().parents[3]
SCRIPTS = REPO / "scripts" / "ci"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

check_pinning: ModuleType = importlib.import_module("check_pinning")
check_repo_hygiene: ModuleType = importlib.import_module("check_repo_hygiene")
audit_exceptions: ModuleType = importlib.import_module("audit_exceptions")

DIGEST = "@sha256:" + "ab" * 32
COMMIT = "@" + "3d3c42e5" * 5
TODAY = dt.date(2026, 11, 24)


def _write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _pinning(root: Path) -> list[str]:
    findings, _ = check_pinning.check(root)
    return [str(finding) for finding in findings]


# --- check_pinning.py ------------------------------------------------------------------


def test_unpinned_images_are_listed(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(tmp_path, "infra/docker-compose.yml", "services:\n  db:\n    image: postgres:16\n")
    _write(tmp_path, "backend/Dockerfile", "FROM node:26\nRUN true\n")
    assert check_pinning.main(["--root", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "infra/docker-compose.yml:3: image non épinglé : postgres:16" in out
    assert "backend/Dockerfile:1: FROM non épinglé : node:26" in out


def test_pinned_references_pass(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(
        tmp_path,
        "compose.yaml",
        f'services:\n  db:\n    image: "postgres:16{DIGEST}"  # épinglée\n'
        "  api:\n    build:\n      context: ../backend\n",
    )
    _write(
        tmp_path,
        "infra/caddy/Dockerfile",
        "# syntax=docker/dockerfile:1\n"
        f"FROM --platform=linux/amd64 node:26{DIGEST} AS pwa\n"
        "FROM pwa AS tests\n"
        f"FROM caddy:2{DIGEST}\n"
        "COPY --from=pwa /web/dist /srv/pwa\n"
        "COPY --from=0 /a /b\n"
        f"COPY --from=ghcr.io/astral-sh/uv:0.13{DIGEST} /uv /bin/uv\n",
    )
    _write(tmp_path, "scratch.Dockerfile", "FROM scratch\nCOPY a /a\n")
    assert check_pinning.main(["--root", str(tmp_path)]) == 0
    assert "3 fichier(s) analysé(s)" in capsys.readouterr().out


def test_copy_from_unpinned_image(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "backend/Dockerfile",
        f"FROM python:3.12{DIGEST} AS builder\n"
        "COPY --from=ghcr.io/astral-sh/uv:latest \\\n    /uv /bin/uv\n",
    )
    assert _pinning(tmp_path) == [
        "backend/Dockerfile:2: COPY --from non épinglé : ghcr.io/astral-sh/uv:latest"
    ]


def test_stage_alias_must_be_declared_before(tmp_path: Path) -> None:
    # `FROM builder` avant la déclaration de l'étape : c'est une image Docker Hub.
    _write(tmp_path, "Dockerfile", f"FROM builder\nFROM python:3.12{DIGEST} AS builder\n")
    assert _pinning(tmp_path) == ["Dockerfile:1: FROM non épinglé : builder"]


def test_build_service_image_needs_pull_policy_build(tmp_path: Path) -> None:
    # Sans `pull_policy: build`, Compose télécharge d'abord l'image nommée, même à côté d'un
    # `build:` : empreinte exigée. `build:` sans `image:` n'a rien à épingler.
    _write(
        tmp_path,
        "docker-compose.yml",
        "services:\n"
        "  api:\n    image: terangacycle-api\n    pull_policy: build\n    build:\n"
        "      context: .\n"
        "  migrate:\n    build: .\n    image: terangacycle-migrate\n"
        "  worker:\n    build: .\n"
        "  cache:\n    image: valkey/valkey:9\n"
        "  other:\n    pull_policy: \"build\"  # construite\n    image: 'terangacycle-other'\n"
        "    build: .\n"
        "  nested:\n    image: terangacycle-nested\n    build:\n      pull_policy: build\n",
    )
    assert _pinning(tmp_path) == [
        "docker-compose.yml:9: image non épinglé : terangacycle-migrate",
        "docker-compose.yml:13: image non épinglé : valkey/valkey:9",
        "docker-compose.yml:19: image non épinglé : terangacycle-nested",
    ]


def test_unpinned_action_is_listed(tmp_path: Path) -> None:
    _write(
        tmp_path,
        ".github/workflows/ci.yml",
        "jobs:\n  a:\n    steps:\n"
        "      - uses: actions/checkout@v7\n"
        f"      - uses: actions/setup-node{COMMIT} # v7.1.0\n"
        "      - uses: ./.github/actions/local\n"
        "      # - uses: commented/out@v1\n"
        "      - uses: 'docker://alpine:3'\n",
    )
    _write(
        tmp_path,
        ".github/actions/local/action.yml",
        "runs:\n  using: composite\n  steps:\n    - uses: owner/repo@main\n",
    )
    assert _pinning(tmp_path) == [
        ".github/actions/local/action.yml:4: uses non épinglé : owner/repo@main",
        ".github/workflows/ci.yml:4: uses non épinglé : actions/checkout@v7",
        ".github/workflows/ci.yml:8: uses non épinglé : docker://alpine:3",
    ]


def test_ignored_files_and_directories(tmp_path: Path) -> None:
    _write(tmp_path, "infra/caddy/Dockerfile.dockerignore", "FROM node:26\n")
    _write(tmp_path, "web/node_modules/pkg/Dockerfile", "FROM node:26\n")
    _write(tmp_path, "TerangaCycle AI/compose.yaml", "services:\n  a:\n    image: x:1\n")
    _write(tmp_path, "docs/notes.yml", "image: postgres:16\n")
    assert _pinning(tmp_path) == []


def test_repository_is_pinned() -> None:
    assert _pinning(REPO) == []


# --- check_repo_hygiene.py -------------------------------------------------------------


GITIGNORE = (
    ".env",
    ".env.*",
    "!.env.example",
    ".env.secrets/",
    "TerangaCycle AI/",
    "*.pem",
    "node_modules/",
)


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)  # noqa: S603, S607


@pytest.fixture
def clean_repo(tmp_path: Path) -> Path:
    # Dépôt Git réel : `git check-ignore` en a besoin.
    _git(tmp_path, "init", "-q")
    _write(tmp_path, ".gitignore", "\n".join(GITIGNORE) + "\n")
    _write(tmp_path, "LICENSE", "                    GNU AFFERO GENERAL PUBLIC LICENSE\n")
    _write(tmp_path, "security/audit-exceptions.toml", "# Aucune exception.\n")
    return tmp_path


def test_clean_repo_passes(clean_repo: Path) -> None:
    tracked = [".gitignore", "LICENSE", ".env.example", "backend/app/main.py"]
    assert check_repo_hygiene.check(clean_repo, TODAY, tracked) == []


def test_internal_documents_tracked_fail(
    clean_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write(clean_repo, "TerangaCycle AI/équipe.md", "noms de l'équipe\n")
    _git(clean_repo, "add", "-f", "TerangaCycle AI/équipe.md", ".gitignore", "LICENSE")
    assert check_repo_hygiene.main(["--root", str(clean_repo)]) == 1
    assert "document interne suivi par Git : TerangaCycle AI/équipe.md" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (".env", "fichier d'environnement suivi par Git : .env"),
        ("web/.env.local", "fichier d'environnement suivi par Git : web/.env.local"),
        (".env.secrets/jwt_signing_keys", "secret suivi par Git : .env.secrets/jwt_signing_keys"),
        # Dossier interne à toute profondeur, quelle que soit la casse.
        (
            "docs/terangacycle ai/notes.md",
            "document interne suivi par Git : docs/terangacycle ai/notes.md",
        ),
        ("TERANGACYCLE AI/x.md", "document interne suivi par Git : TERANGACYCLE AI/x.md"),
        # Clés et certificats.
        ("infra/caddy/root.crt", "clé ou certificat suivi par Git : infra/caddy/root.crt"),
        ("k.PEM", "clé ou certificat suivi par Git : k.PEM"),
        ("secrets/tls.key", "clé ou certificat suivi par Git : secrets/tls.key"),
        ("client.p12", "clé ou certificat suivi par Git : client.p12"),
    ],
)
def test_sensitive_files_tracked_fail(clean_repo: Path, path: str, expected: str) -> None:
    assert check_repo_hygiene.check(clean_repo, TODAY, [".env.example", path]) == [expected]


@pytest.mark.parametrize(
    ("removed", "expected"),
    [
        ("*.pem", ".gitignore n'ignore pas : k.pem"),
        ("node_modules/", ".gitignore n'ignore pas : web/node_modules/x"),
        ("TerangaCycle AI/", ".gitignore n'ignore pas : TerangaCycle AI/x"),
        ("!.env.example", ".gitignore ignore à tort : .env.example"),
    ],
)
def test_gitignore_must_ignore_sensitive_paths(
    clean_repo: Path, removed: str, expected: str
) -> None:
    lines = [line for line in GITIGNORE if line != removed]
    _write(clean_repo, ".gitignore", "\n".join(lines) + "\n")
    assert check_repo_hygiene.check(clean_repo, TODAY, []) == [expected]


def test_gitignore_is_checked_by_effect_not_by_line(clean_repo: Path) -> None:
    # Motifs équivalents écrits autrement : acceptés (`.env.*` couvre déjà `.env.secrets/`).
    _write(
        clean_repo,
        ".gitignore",
        ".env\n.env*\n!.env.example\n**/TerangaCycle AI/**\n**/*.pem\nnode_modules\n",
    )
    assert check_repo_hygiene.check(clean_repo, TODAY, []) == []


def test_missing_gitignore_fails(clean_repo: Path) -> None:
    (clean_repo / ".gitignore").unlink()
    assert check_repo_hygiene.check(clean_repo, TODAY, []) == [".gitignore absent"]


def test_missing_license_fails(clean_repo: Path) -> None:
    (clean_repo / "LICENSE").unlink()
    assert check_repo_hygiene.check(clean_repo, TODAY, []) == ["LICENSE absent"]


def test_other_license_fails(clean_repo: Path) -> None:
    _write(clean_repo, "LICENSE", "MIT License\n")
    assert check_repo_hygiene.check(clean_repo, TODAY, []) == [
        "LICENSE ne contient pas « GNU AFFERO GENERAL PUBLIC LICENSE »"
    ]


def test_repository_is_clean() -> None:
    assert check_repo_hygiene.check(REPO) == []


# --- Exceptions d'audit datées ---------------------------------------------------------


def _exception(tool: str, ident: str, expires: str, reason: str = "Pas de correctif.") -> str:
    return (
        f'[[exception]]\ntool = "{tool}"\nid = "{ident}"\nreason = "{reason}"\n'
        f"expires = {expires}\n\n"
    )


def _exceptions_file(root: Path, *entries: str) -> Path:
    return _write(root, "security/audit-exceptions.toml", "".join(entries))


def test_expired_exception_fails(clean_repo: Path) -> None:
    _exceptions_file(clean_repo, _exception("trivy", "CVE-2026-0001", "2026-11-23"))
    assert check_repo_hygiene.check(clean_repo, TODAY, []) == [
        "security/audit-exceptions.toml : exception n° 1 (CVE-2026-0001) : expirée le 2026-11-23"
    ]


def test_exception_is_valid_through_its_expiry_day(clean_repo: Path) -> None:
    _exceptions_file(
        clean_repo,
        _exception("trivy", "CVE-2026-0001", "2026-11-24"),
        _exception("pip-audit", "PYSEC-2026-1", '"2027-01-31"'),
        # Au plus 90 jours après aujourd'hui ; npm-audit : GHSA ou numéro d'avis.
        _exception("npm-audit", "1096410", "2027-02-22"),
    )
    assert check_repo_hygiene.check(clean_repo, TODAY, []) == []


@pytest.mark.parametrize(
    ("entry", "message"),
    [
        (_exception("trivy", "CVE-2026-0001", "2027-01-31", reason=""), "champs manquants"),
        (_exception("snyk", "CVE-2026-0001", "2027-01-31"), "outil inconnu"),
        (_exception("trivy", "CVE-2026-0001", '"31/01/2027"'), "date ISO"),
        ('[[exception]]\ntool = "trivy"\nid = "CVE-2026-0001"\n', "champs manquants"),
        # `id` recopié dans une option ou un fichier : caractères sûrs seulement.
        (_exception("pip-audit", "PYSEC-2026-1 --ignore-vuln=X", "2027-01-31"), "`id` invalide"),
        (_exception("trivy", "CVE-2026-0001\\nCVE-2026-0002", "2027-01-31"), "`id` invalide"),
        (_exception("npm-audit", "CVE-2026-0001", "2027-01-31"), "`id` npm-audit attendu"),
        (_exception("npm-audit", "GHSA-1234-5678-abcd", "2027-01-31"), "`id` npm-audit attendu"),
        # Une raison sur plusieurs lignes injecterait une ligne dans .trivyignore.
        (
            _exception("trivy", "CVE-2026-0001", "2027-01-31", reason="Raison.\\nCVE-2026-9999"),
            "`reason` doit tenir sur une ligne",
        ),
        (_exception("trivy", "CVE-2026-0001", "2027-02-23"), "à plus de 90 jours"),
    ],
)
def test_invalid_exception_fails(clean_repo: Path, entry: str, message: str) -> None:
    _exceptions_file(clean_repo, entry)
    problems = check_repo_hygiene.check(clean_repo, TODAY, [])
    assert len(problems) == 1 and message in problems[0]


def test_missing_exceptions_file_fails(clean_repo: Path) -> None:
    (clean_repo / "security" / "audit-exceptions.toml").unlink()
    assert check_repo_hygiene.check(clean_repo, TODAY, []) == [
        "security/audit-exceptions.toml : fichier absent"
    ]


def test_exceptions_feed_each_tool(tmp_path: Path) -> None:
    path = _exceptions_file(
        tmp_path,
        _exception("pip-audit", "PYSEC-2026-1", "2027-01-31"),
        _exception("pip-audit", "GHSA-2345-6789-cfgh", "2027-01-31"),
        _exception("trivy", "CVE-2026-0001", "2027-02-20", reason="Paquet système non utilisé."),
        _exception("npm-audit", "GHSA-cfgh-2345-6789", "2027-01-31"),
    )
    exceptions = audit_exceptions.load(path, TODAY)
    assert audit_exceptions.pip_audit_args(exceptions) == (
        "--ignore-vuln=PYSEC-2026-1 --ignore-vuln=GHSA-2345-6789-cfgh"
    )
    # Trivy cesse d'ignorer à 00:00 UTC du jour `exp` : le lendemain de `expires`, comme
    # l'hygiène, qui tient l'exception pour valable jusqu'à sa date incluse.
    trivyignore = audit_exceptions.trivyignore(exceptions).splitlines()
    assert trivyignore[1:] == ["# Paquet système non utilisé.", "CVE-2026-0001 exp:2027-02-21"]


def test_cli_refuses_expired_exception(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = _exceptions_file(tmp_path, _exception("pip-audit", "PYSEC-2020-1", "2020-01-01"))
    assert audit_exceptions.main(["--file", str(path), "pip-audit-args"]) == 1
    assert "expirée le 2020-01-01" in capsys.readouterr().err


def _npm_report(*advisories: tuple[str, str, str]) -> dict[str, object]:
    """Rapport `npm audit --json` (v2) : (paquet, gravité, GHSA) par avis."""
    vulnerabilities: dict[str, object] = {
        name: {
            "name": name,
            "severity": severity,
            "via": [
                {
                    "source": 1000 + index,
                    "name": name,
                    "title": f"Faille de {name}",
                    "url": f"https://github.com/advisories/{ghsa}",
                    "severity": severity,
                }
            ],
        }
        for index, (name, severity, ghsa) in enumerate(advisories)
    }
    # Paquet vulnérable par transitivité seulement : `via` ne nomme que le paquet fautif.
    vulnerabilities["parent"] = {"name": "parent", "severity": "critical", "via": ["crit"]}
    return {"auditReportVersion": 2, "vulnerabilities": vulnerabilities}


def test_npm_audit_filters_by_level_and_exceptions(tmp_path: Path) -> None:
    path = _exceptions_file(tmp_path, _exception("npm-audit", "GHSA-cfgh-2345-6789", "2027-01-31"))
    exceptions = audit_exceptions.load(path, TODAY)
    report = _npm_report(
        ("crit", "critical", "GHSA-cfgh-2345-6789"),  # exception datée
        ("high", "high", "GHSA-2345-6789-cfgh"),
        ("mod", "moderate", "GHSA-6789-cfgh-2345"),  # sous le seuil
    )
    assert audit_exceptions.npm_findings(report, exceptions, "high") == [
        "high : high — Faille de high (GHSA-2345-6789-cfgh)"
    ]
    assert len(audit_exceptions.npm_findings(report, [], "moderate")) == 3


def test_npm_audit_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exceptions = _exceptions_file(tmp_path, "")
    clean = _write(tmp_path, "clean.json", json.dumps(_npm_report()))
    vulnerable = _write(
        tmp_path, "vulnerable.json", json.dumps(_npm_report(("x", "high", "GHSA-2345-6789-cfgh")))
    )
    failed = _write(tmp_path, "failed.json", json.dumps({"error": {"code": "ENOTFOUND"}}))
    base = ["--file", str(exceptions), "npm-audit"]
    assert audit_exceptions.main([*base, str(clean)]) == 0
    assert audit_exceptions.main([*base, str(vulnerable)]) == 1
    assert "GHSA-2345-6789-cfgh" in capsys.readouterr().out
    assert audit_exceptions.main([*base, str(failed)]) == 1
    assert "ENOTFOUND" in capsys.readouterr().err


def test_repository_exceptions_are_valid() -> None:
    audit_exceptions.load()


# --- .gitleaks.toml --------------------------------------------------------------------


def test_gitleaks_config_extends_defaults_with_figma_rule() -> None:
    config = tomllib.loads((REPO / ".gitleaks.toml").read_text(encoding="utf-8"))
    assert config["extend"]["useDefault"] is True
    [rule] = [rule for rule in config["rules"] if rule["id"] == "figma-file-url"]
    pattern = re.compile(rule["regex"])
    file_key = "".join(("Ab3", "dE5", "fG7", "hJ9", "kL1", "mN2", "pQ4", "r"))  # fabriquée
    assert len(file_key) == 22
    for kind in ("design", "file", "proto", "board", "slides", "deck", "make", "site"):
        sample = f"https://www.figma.com/{kind}/{file_key}/Maquettes"
        assert pattern.search(sample), kind
        # Gitleaks ne lance la regex que si un mot-clé figure dans le texte.
        assert all(keyword.lower() in sample.lower() for keyword in rule["keywords"]), kind
    for placeholder in ("<clé>", "{key}", "<clé-de-22-caractères-x>", "{file_key_22_caracteres}"):
        assert not pattern.search(f"https://www.figma.com/design/{placeholder}/Maquettes")
    assert all(allowlist.get("description") for allowlist in config.get("allowlists", []))
