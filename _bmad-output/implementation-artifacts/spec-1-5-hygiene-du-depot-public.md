---
title: 'Story 1.5 — Hygiène du dépôt public'
type: 'chore'
created: '2026-11-24'
status: 'in-review'
baseline_commit: '8d72ec80e2075f03e01a741c535d284b847e9226'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-4-ci-de-qualite.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problème :** le dépôt est public, mais il présente quatre faiblesses :
- rien n'empêche de pousser un secret ou une adresse Figma ;
- rien ne vérifie que les images et les actions restent épinglées ;
- les dépendances ne sont ni auditées ni mises à jour ;
- il n'y a ni licence ni canal de signalement des vulnérabilités.

**Approche :** un job `hygiene` (Gitleaks avec une règle Figma, contrôle d'épinglage, garde `git ls-files`, présence de `LICENSE`) et un job `audit` (pip-audit, npm audit, Trivy sur les images), ajoutés à la CI. S'y ajoutent `LICENSE` en AGPL-3.0, `SECURITY.md`, `.github/dependabot.yml` et un test qui aligne `.env.example` sur `Settings`.

**Décisions de Mia (24/11/2026) :**
- **Licence :** GNU AGPL-3.0, texte officiel complet dans `LICENSE`, `license = "AGPL-3.0-only"` dans `pyproject.toml` et `"license": "AGPL-3.0-only"` dans `package.json`.
- **Réglages GitHub :** Claude les applique par `gh api` :
  - secret scanning et push protection ;
  - signalement privé des vulnérabilités ;
  - sur `main` : pull request obligatoire (0 approbation), contrôles CI obligatoires (`backend`, `web`, `edge`, `hygiene`, `audit`), force push et suppression interdits, administratrice exemptée.

  La sortie de `gh api` est jointe à la PR.

## Boundaries & Constraints

**Toujours :**
- **Binaires téléchargés en CI :** version épinglée et somme SHA-256 vérifiée avant extraction :
  - Gitleaks 8.30.1 (`gitleaks_8.30.1_linux_x64.tar.gz`, `551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb`) ;
  - Trivy 0.76.2 (`trivy_0.76.2_Linux-64bit.tar.gz`, `bc0fc726e017b8927a62b2d3531d7a84ee01769daf5c99ed866dced54089fdbf`).
- **pip-audit 2.10.1**, lancé par `uvx` avec la version épinglée.
- **Exceptions datées :** toute exception d'audit (`.trivyignore`, liste `--ignore-vuln` de pip-audit, `npm audit`) porte un identifiant, une raison et une date d'expiration. Une exception expirée fait échouer la CI.
- **Scripts de contrôle :** en Python, bibliothèque standard seulement, dans `scripts/ci/`, avec leurs tests dans `backend/tests/unit/`.

**Jamais :**
- Aucune clé Figma réelle dans un fichier de test : uniquement des valeurs fabriquées.
- Aucun secret GitHub nécessaire.
- Pas de diff OpenAPI ni de test route × rôle (story 1.6).

## I/O & Edge-Case Matrix

| Scénario | Entrée / État | Résultat attendu | Erreurs |
|---|---|---|---|
| Faux secret | Commit avec une clé AWS factice ou une clé privée PEM factice | `hygiene` échoue en nommant le fichier et la règle | — |
| Adresse Figma | `figma.com/design/<22 caractères>` dans `_bmad-output/x.md` | `hygiene` échoue (règle `figma-file-url`) | Placeholders `<clé>` et `{key}` non détectés |
| Image non épinglée | `image: postgres:16` dans un fichier Compose, `FROM node:26` dans un Dockerfile | Échec qui liste chaque élément | — |
| Action non épinglée | `uses: actions/checkout@v7` | Échec qui liste l'élément | Actions locales `./…` acceptées |
| Fichiers internes suivis | Un chemin `TerangaCycle AI/…` dans `git ls-files` | Échec | — |
| `.env.example` | Champ de `Settings` absent de `.env.example`, ou valeur qui ressemble à un vrai secret | Échec du test | Les secrets AD-26 restent hors de `.env.example` (fichiers `/run/secrets`) |
| `LICENSE` absente | Fichier supprimé | Échec | — |
| Exception d'audit expirée | Date dépassée | Échec | — |

</frozen-after-approval>

## Code Map

- `.github/workflows/ci.yml` (story 1.4) :
  - jobs `backend`, `web` et `edge` ;
  - actions épinglées par SHA (`actions/checkout@3d3c42e5…`, `astral-sh/setup-uv@1db35dd8…`, `actions/setup-node@949feb24…`) ;
  - `permissions: contents: read` ;
  - concurrence annulée seulement pour les PR.
- Fichiers à couvrir par le contrôle d'épinglage :
  - Compose : `infra/docker-compose.yml`, `compose.yaml` (avec `include` seulement) ;
  - Dockerfiles : `backend/Dockerfile`, `infra/caddy/Dockerfile` (lignes `FROM` et `COPY --from=<image>`).
- `backend/app/core/config.py` :
  - `Settings` et `MigratorSettings` ;
  - inventaire `REQUIRED_SECRETS` des secrets AD-26, lus dans `/run/secrets` et jamais dans `.env` ;
  - champs non secrets lus dans l'environnement.
- `.env.example` (racine) : `ENV`, `DEMO_MODE`, `LOG_LEVEL`, `DB_*`, `VALKEY_URL`, `S3_*`, `HTTP_PORT`, `HTTPS_PORT`, `DB_LOCAL_PORT`, `APP_HOST`, `MEDIA_HOST`, `MODEL_VERSION` (commenté).
- `.gitignore` : couvre déjà `TerangaCycle AI/`, `.env`, `.env.*` (sauf `.env.example`), `node_modules/`, `dist/`, `.venv/` et les caches. Ajouter `.env.secrets/` explicitement pour la lisibilité.
- `backend/pyproject.toml` et `web/package.json` : y ajouter le champ licence.
- README : section « Intégration continue », avec la commande de protection de la story 1.4, à mettre à jour avec les nouveaux contrôles.

## Tasks & Acceptance

**Exécution :**
- [x] `LICENSE` : texte officiel complet de la GNU AGPL-3.0, téléchargé depuis gnu.org (`https://www.gnu.org/licenses/agpl-3.0.txt`) et non réécrit. Champs de licence dans `pyproject.toml` et `package.json`. Ligne « Licence » dans le README.
- [x] `SECURITY.md` (français) :
  - canal privé : GitHub « Report a vulnerability » (signalement privé) ;
  - accusé de réception sous 72 h et premier diagnostic sous 7 jours ;
  - ce qu'il ne faut pas faire : pas d'issue publique ni de test sur des données réelles.
- [x] `.github/dependabot.yml` : écosystèmes `pip` (`/backend`), `npm` (`/web`), `docker` (`/backend`, `/infra/caddy`) et `github-actions` (`/`). Fréquence hebdomadaire, mises à jour mineures et correctifs groupés.
- [x] `.gitleaks.toml` : `[extend] useDefault = true`, plus une règle `figma-file-url` (`figma\.com/(?:design|file|proto)/[A-Za-z0-9]{22}`) qui laisse passer les placeholders (`<…>`, `{…}`). Faux positifs connus en `allowlist`, avec une justification en commentaire.
- [x] `scripts/ci/check_pinning.py` : analyse les fichiers Compose (`image:`), les Dockerfiles (`FROM`, `COPY --from=` d'une image) et `.github/workflows/*.yml` (`uses:`), et liste chaque élément non épinglé. Exceptions : `FROM <alias d'étape>`, `uses: ./…` et `build:` sans `image:`. Code de sortie 1 s'il y a au moins un élément.
- [x] `scripts/ci/check_repo_hygiene.py` :
  - `git ls-files` ne contient aucun chemin `TerangaCycle AI/` ;
  - `.gitignore` contient les motifs exigés ;
  - `LICENSE` existe et contient « GNU AFFERO GENERAL PUBLIC LICENSE » ;
  - les exceptions d'audit de `security/audit-exceptions.toml` ne sont pas expirées.
- [x] `security/audit-exceptions.toml` : format `[[exception]]` avec `tool`, `id`, `reason` et `expires` (date ISO). Le fichier peut être vide au départ. Les jobs le lisent pour construire `--ignore-vuln` (pip-audit) et `.trivyignore`.
- [x] `backend/tests/unit/test_env_example.py` : tout champ non secret de `Settings` figure dans `.env.example` (nom en majuscules) ; aucun nom de `REQUIRED_SECRETS` n'y figure ; aucune valeur ne ressemble à un secret (longue chaîne aléatoire, préfixes `sk-`, `ghp_`, `AKIA`, `-----BEGIN`).
- [x] `backend/tests/unit/test_ci_scripts.py` : chaque ligne de la matrice I/O pour `check_pinning.py` et `check_repo_hygiene.py`, sur des fichiers témoins dans `tmp_path`.
- [x] `.github/workflows/ci.yml` :
  - job `hygiene` : Gitleaks sur l'historique (`--log-opts` couvrant les commits de la PR, ou tout l'historique sur `main`), puis `check_pinning.py` et `check_repo_hygiene.py` ;
  - job `audit` : `uvx pip-audit==2.10.1` sur les dépendances exportées (`uv export --locked --no-dev`), `npm audit --omit=dev --audit-level=high`, Trivy (`--severity HIGH,CRITICAL --exit-code 1 --ignore-unfixed`) sur les images `api` et `caddy` construites.
- [x] `README.md` : section « Intégration continue » (jobs `hygiene` et `audit`, exceptions datées, licence), commande de protection mise à jour (5 contrôles, PR obligatoire, pas de force push).
- [x] `.gitignore` : ajouter `.env.secrets/` explicitement.

**Critères d'acceptation :**
- Étant donné la PR de cette story, quand la CI tourne sur GitHub, alors `backend`, `web`, `edge`, `hygiene` et `audit` sont verts. S'il y a des exceptions, elles sont datées et justifiées.
- Étant donné le dépôt, quand on lance `check_pinning.py` et `check_repo_hygiene.py` en local, alors ils réussissent.

## Implementation Notes

- **Dependabot, backend :** écosystème `uv` au lieu de `pip`. L'écosystème `pip` mettrait à jour `pyproject.toml` sans `uv.lock`, et chaque PR échouerait sur `uv sync --locked`. Même dossier (`/backend`), même fréquence, même groupement.
- **Exceptions d'audit :** un module partagé, `scripts/ci/audit_exceptions.py`, lit et valide `security/audit-exceptions.toml` (`check`, `pip-audit-args`, `trivyignore`, `npm-audit`). `check_repo_hygiene.py` l'importe. Une exception reste valable jusqu'à sa date incluse ; le lendemain, la CI échoue.
- **npm audit :** `npm audit` n'a pas d'option d'exception. Le job lance `npm audit --omit=dev --json` et filtre le rapport avec `audit_exceptions.py npm-audit --audit-level high` : même seuil que `--audit-level=high`, exceptions datées en plus, échec si le registre n'a pas répondu.
- **pip-audit :** `uv export --locked --no-dev --no-emit-project` (fichier figé et haché), puis `uvx pip-audit==2.10.1 --disable-pip --strict`.
- **Trivy :** `--scanners vuln,secret` (après revue). Images construites par `docker build` directement (`terangacycle-api:ci`, `terangacycle-caddy:ci`) : ni secrets ni `.env` nécessaires.
- **Gitleaks :** deux faux positifs dans l'historique (règle `generic-api-key`), mis en `[[allowlists]]` restreints au fichier ET à la valeur : empreintes SHA-256 de `_bmad/_config/files-manifest.csv`, mots de passe factices de `backend/tests/unit/test_config.py`. `--redact` en CI (dépôt public).
- **`.env.example` :** `DB_APP_USER` et `DB_MIGRATOR_USER` (champs non secrets de `Settings`) ajoutés en commentaire : les noms des rôles sont fixés par `infra/db/initdb/20-roles.sh`. Le test accepte une variable commentée (`# NOM=`), comme `MODEL_VERSION`.
- **`check_repo_hygiene.py` :** refuse aussi un `.env`, `.env.*` (hors `.env.example`) ou `.env.secrets/…` suivi par Git.
- **Réglages GitHub :** non appliqués à ce stade (accord explicite et PR requis). Les commandes `gh api` (protection de `main` à 5 contrôles, secret scanning, push protection, signalement privé) sont dans le README.
- **Après revue (passe 1) :** Dependabot `docker-compose` pour `/infra` et `cooldown` de 3 jours partout ; `audit` relancé seul chaque lundi (`schedule`) et à la demande (`workflow_dispatch`) ; `id` d'exception validé (GHSA ou numéro pour npm-audit), `reason` sur une ligne, `expires` à 90 jours au plus, `exp:` de Trivy au lendemain de `expires` ; `.gitignore` vérifié par effet (`git check-ignore --no-index`), clés et certificats suivis refusés, dossier interne reconnu à toute profondeur sans tenir compte de la casse ; règle Figma étendue (`board`, `slides`, `deck`, `make`, `site`) et auto-testée par Gitleaks en CI ; Trivy `--scanners vuln,secret` ; ruff sur `scripts/ci` ; `image:` à côté de `build:` exempté seulement avec `pull_policy: build`.

## Spec Change Log

## Review Triage Log

Passe 1 (25/11/2026). Couches : Blind Hunter (B), Edge Case Hunter (E), Verification Gap (V).

| # | Constat | Verdict | Preuve | Route |
|---|---|---|---|---|
| B1 / V-autre / E15 | Images Compose (postgis, valkey, garage) jamais mises à jour par Dependabot | medium | `dependabot.yml` ne couvre que `/backend` et `/infra/caddy` | patch (P1) |
| B2 | L'audit ne tourne jamais sur un `main` inchangé | medium | Seulement `pull_request` et `push` ; une CVE publiée après la fusion reste invisible | patch (P2) |
| B3 / E2 / E3 | `id` des exceptions non validé, `reason` multiligne injecté dans `.trivyignore`, `id` npm de mauvais format | medium | `$ignore` utilisé sans guillemets ; `# {reason}` écrit tel quel | patch (P3) |
| B4 | Aucune limite haute sur `expires` | medium | `2099-12-31` passe : une exception « datée » devient permanente | patch (P3) |
| E1 | Exception Trivy à la date du jour : l'audit échoue alors que `hygiene` la juge valide | low | Trivy cesse d'ignorer à 00:00 UTC le jour d'expiration ; correction directe | patch (P3) |
| B5 / B6 / E13 | Fichiers de clés suivis non détectés ; le `.gitignore` est vérifié ligne par ligne, pas dans son effet | medium | `git add -f` ou une réinclusion `!` passent | patch (P4) |
| E11 | Dossier interne suivi à un chemin imbriqué ou avec une autre casse | low | Correction directe | patch (P4) |
| B7 / E14 | Règle Figma sans `board`, `slides`, `deck`, `make` ni `site` | medium | Ces adresses portent aussi une clé de fichier | patch (P5) |
| V1 | Règle Figma jamais testée par Gitleaks lui-même | medium | Seul le moteur de regex de Python est testé ; mots-clés et fusion avec la configuration par défaut non vérifiés | patch (P5) |
| B11 | Trivy ne cherche pas de secrets dans les images | low | Correction directe (`--scanners vuln,secret`) | patch (P5) |
| B8 / V-autre | `scripts/ci/*.py` hors de ruff | low | Le lint tourne dans `backend/` seulement | patch (P6) |
| E8 / revendication | `image:` exemptée dès qu'un `build:` voisin existe | medium | Compose tire d'abord l'image nommée depuis le registre (usurpation de nom possible) | patch (P7) |
| B14 | Dependabot sans délai de carence | low | Correction directe (`cooldown`) | patch (P1) |
| B9 | Dépendances de pip-audit non verrouillées | low | Outil exécuté isolé, version épinglée | rejeté |
| B10 | Commandes d'audit locales différentes de la CI | low | Documentation seulement | rejeté |
| B12 | `SECURITY.md` sans contact de secours | low | Le signalement privé est activé depuis le 25/11 ; publier un e-mail exposerait une donnée personnelle | rejeté |
| B13 | Alertes Dependabot non activées | low | Réglage hors de l'accord donné ; proposé à Mia | rejeté (proposé) |
| B15 / B16 / B17 / B18 | Différence de périmètre `ls-files` / système de fichiers, triple validation, cas de test manquants, cas limites de `uses:` | low | Cosmétique ou improbable | rejeté |
| E4 / E5 / E6 / E7 / E9 / E10 / E12 | Cas limites des scripts (JSON non objet, `RUN --mount from`, ligne vide de continuation, `container:`, liens symboliques, encodage) | low | Absents du dépôt ; une erreur reste visible | rejeté |
| V2 | Les verrous Trivy et pip-audit ne sont pas testés en négatif | medium | Exigerait une image volontairement vulnérable | defer |
| Revendication | `uv` au lieu de `pip` pour Dependabot | false | Écart volontaire et justifié dans les Implementation Notes (`uv.lock`) | rejeté |

## Design Notes

**Gitleaks en binaire plutôt qu'en action.** L'action officielle exige une licence pour les organisations et change souvent. Le binaire épinglé, vérifié par sa somme SHA-256, donne exactement le même outil en local et en CI.

**Réglages GitHub appliqués hors code.** Les réglages du dépôt ne sont pas versionnés. Claude les applique après accord, et la sortie de `gh api` dans la PR sert de preuve.

## Verification

**Commandes :**
- `python scripts/ci/check_pinning.py && python scripts/ci/check_repo_hygiene.py` — attendu : succès.
- Dans le conteneur uv : `uv run pytest tests/unit/test_env_example.py tests/unit/test_ci_scripts.py` — attendu : succès.
- Gitleaks en local (conteneur `zricethezav/gitleaks` épinglé, ou binaire) : `gitleaks git --config .gitleaks.toml` — attendu : aucune fuite.
- Sur GitHub : les 5 jobs sont verts.
