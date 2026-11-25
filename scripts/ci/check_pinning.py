"""Contrôle d'épinglage (story 1.5) : images par empreinte, actions GitHub par SHA.

Analyse :
  - les fichiers Compose : `image:` doit finir par `@sha256:<64 hex>` ;
  - les Dockerfiles : `FROM` et `COPY --from=<image>`, même règle ;
  - `.github/workflows/*.yml` (et les actions composites) : `uses:` doit viser un SHA
    de commit de 40 caractères.

Exceptions : `FROM <alias d'étape>` ou `FROM scratch`, `COPY --from=<alias ou numéro>`,
`uses: ./…` (action locale), `image:` d'un service en `pull_policy: build` (nom de l'image
construite, jamais téléchargée), service `build:` sans `image:`. Sans `pull_policy: build`,
Compose tente d'abord de télécharger l'image nommée : elle doit alors être épinglée, même
à côté d'un `build:`.

Usage : python3 scripts/ci/check_pinning.py [--root <dépôt>]
Code de sortie 1 s'il reste au moins un élément non épinglé. Bibliothèque standard seulement.
"""

import argparse
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# Dossiers jamais analysés : dépendances, constructions, documents internes non suivis.
SKIP_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "dist",
        "dev-dist",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        "TerangaCycle AI",
    }
)

_COMPOSE_NAME = re.compile(r"^(?:docker-)?compose(?:\.[\w.-]+)?\.ya?ml$")
_DIGEST = re.compile(r"@sha256:[0-9a-f]{64}$")
_COMMIT_SHA = re.compile(r"@[0-9a-f]{40}$")
_KEY_LINE = re.compile(r"^(?P<indent>\s*)(?:-\s+)?(?P<key>[\w.<-]+)\s*:(?:\s|$)")
_IMAGE_LINE = re.compile(r"^(?P<indent>\s*)(?:-\s+)?image\s*:\s*(?P<ref>[^#]*?)\s*(?:#.*)?$")
_USES_LINE = re.compile(r"^\s*(?:-\s+)?uses\s*:\s*(?P<ref>[^#\s]+)")


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    kind: str
    ref: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.kind} non épinglé : {self.ref}"


def _walk(root: Path) -> Iterator[Path]:
    for path in sorted(root.iterdir()):
        if path.is_dir():
            if path.name not in SKIP_DIRS:
                yield from _walk(path)
        elif path.is_file():
            yield path


def is_compose(path: Path) -> bool:
    return bool(_COMPOSE_NAME.match(path.name))


def is_dockerfile(path: Path) -> bool:
    name = path.name
    if name.endswith(".dockerignore"):
        return False
    lower = name.lower()
    return name == "Dockerfile" or name.startswith("Dockerfile.") or lower.endswith(".dockerfile")


def is_workflow(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return False
    if len(parts) < 2 or parts[0] != ".github" or path.suffix not in (".yml", ".yaml"):
        return False
    # Workflows et actions composites du dépôt.
    return parts[1] == "workflows" or path.stem == "action"


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1].strip()
    return value


def _sibling_value(lines: list[str], index: int, indent: int, key: str) -> str | None:
    """Valeur de la clé `key` dans le bloc de la ligne `index` (même indentation), ou None."""
    block_start = index
    while block_start > 0:
        prev = lines[block_start - 1]
        if prev.strip() and not prev.lstrip().startswith("#"):
            if len(prev) - len(prev.lstrip()) < indent:
                break
        block_start -= 1
    # Les lignes de `block_start` à `index` sont toutes indentées d'au moins `indent`.
    for line in lines[block_start:]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        line_indent = len(line) - len(line.lstrip())
        if line_indent < indent:
            break
        match = _KEY_LINE.match(line)
        if match and line_indent == indent and match["key"] == key:
            value = line[match.end() :].split("#", 1)[0]
            return _unquote(value)
    return None


def check_compose(path: Path, rel: str) -> list[Finding]:
    findings = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for number, line in enumerate(lines, start=1):
        if line.lstrip().startswith("#"):
            continue
        match = _IMAGE_LINE.match(line)
        if not match:
            continue
        ref = _unquote(match["ref"])
        if not ref or _DIGEST.search(ref):
            continue
        if _sibling_value(lines, number - 1, len(match["indent"]), "pull_policy") == "build":
            continue
        findings.append(Finding(rel, number, "image", ref))
    return findings


def _instructions(text: str) -> Iterator[tuple[int, str]]:
    """Instructions d'un Dockerfile (continuations `\\` jointes), avec leur première ligne."""
    buffer: list[str] = []
    start = 0
    for number, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not buffer and (not stripped or stripped.startswith("#")):
            continue
        if buffer and stripped.startswith("#"):
            continue
        if not buffer:
            start = number
        if stripped.endswith("\\"):
            buffer.append(stripped[:-1])
            continue
        buffer.append(stripped)
        yield start, " ".join(part.strip() for part in buffer if part.strip())
        buffer = []
    if buffer:
        yield start, " ".join(buffer)


def check_dockerfile(path: Path, rel: str) -> list[Finding]:
    findings = []
    aliases: set[str] = set()
    for number, instruction in _instructions(path.read_text(encoding="utf-8")):
        words = instruction.split()
        keyword = words[0].upper()
        args = words[1:]
        if keyword == "FROM":
            positional = [word for word in args if not word.startswith("--")]
            if not positional:
                continue
            image = positional[0]
            if len(positional) >= 3 and positional[1].upper() == "AS":
                alias = positional[2].lower()
            else:
                alias = None
            if not (
                image.lower() == "scratch" or image.lower() in aliases or _DIGEST.search(image)
            ):
                findings.append(Finding(rel, number, "FROM", image))
            if alias:
                aliases.add(alias)
        elif keyword in ("COPY", "ADD"):
            for word in args:
                if not word.startswith("--from="):
                    continue
                source = _unquote(word.removeprefix("--from="))
                if source.isdigit() or source.lower() in aliases or _DIGEST.search(source):
                    continue
                findings.append(Finding(rel, number, f"{keyword} --from", source))
    return findings


def check_workflow(path: Path, rel: str) -> list[Finding]:
    findings = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.lstrip().startswith("#"):
            continue
        match = _USES_LINE.match(line)
        if not match:
            continue
        ref = _unquote(match["ref"])
        if ref.startswith("./"):
            continue
        if ref.startswith("docker://"):
            if _DIGEST.search(ref):
                continue
        elif _COMMIT_SHA.search(ref):
            continue
        findings.append(Finding(rel, number, "uses", ref))
    return findings


def check(root: Path) -> tuple[list[Finding], int]:
    """Éléments non épinglés sous `root`, et nombre de fichiers analysés."""
    findings: list[Finding] = []
    scanned = 0
    for path in _walk(root):
        rel = path.relative_to(root).as_posix()
        if is_workflow(path, root):
            findings += check_workflow(path, rel)
        elif is_compose(path):
            findings += check_compose(path, rel)
        elif is_dockerfile(path):
            findings += check_dockerfile(path, rel)
        else:
            continue
        scanned += 1
    return findings, scanned


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Contrôle d'épinglage des images et actions.")
    parser.add_argument("--root", type=Path, default=REPO)
    args = parser.parse_args(argv)
    findings, scanned = check(args.root.resolve())
    if findings:
        print(f"Épinglage : {len(findings)} élément(s) non épinglé(s) :")
        for finding in findings:
            print(f"  {finding}")
        return 1
    print(f"Épinglage : {scanned} fichier(s) analysé(s), tout est épinglé.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
