---
title: 'Story 1.1 — Squelette backend et Docker Compose'
type: 'chore'
created: '2026-11-24'
status: 'done'
baseline_commit: '8a41fa90f029db9b4edc9fa0f63544f68b9935be'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-TerangaCycleAI-2026-11-23/ARCHITECTURE-SPINE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problème :** le dépôt ne contient que de la documentation. Aucune story ne peut être livrée sans un backend et une infrastructure communs qui démarrent en une commande.

**Approche :** écrire à la main l'arborescence de l'épine (AD-1) et un `docker-compose.yml` unique (profils `demo` et `prod`) avec 7 services épinglés par empreinte. Ajouter deux rôles PostgreSQL : `teranga_migrator` pour les migrations, `teranga_app` avec des droits DML seulement.

## Boundaries & Constraints

**Toujours :**
- Python 3.12, dépendances à la version exacte de la Stack, gérées par `uv` avec `uv.lock` committé.
- Images référencées par `tag@sha256:`.
- Healthchecks sans `curl`.
- Secrets factices dans `.env.secrets/` (un fichier par secret, hors Git), montés dans `/run/secrets/` par les `secrets:` de Compose.
- Code et noms en anglais ; commentaires et documentation en français.

**Jamais :**
- Ni starter full-stack, ni SQLModel.
- Aucune logique métier, aucune route `/v1`, aucune sonde `/healthz` (story 1.2).
- Aucun secret réel dans Git.
- Aucune table métier : la migration initiale est une base vide.

## I/O & Edge-Case Matrix

| Scénario | Entrée / État | Résultat attendu | Erreurs |
|---|---|---|---|
| Démarrage démo | `docker compose --profile demo up -d` à la racine, `.env` et `.env.secrets/` présents | `db`, `valkey` et `garage` passent à `healthy` ; `migrate` termine avec le code 0 ; `api`, `worker` et `caddy` tournent | — |
| Migration échouée | `alembic upgrade head` en échec | `api` et `worker` ne démarrent pas (`service_completed_successfully`) | Code de sortie ≠ 0 visible dans `docker compose ps` |
| DDL par l'application | `CREATE TABLE` exécuté par `teranga_app` | Refusé (`permission denied`) | Test d'intégration vert |
| Secrets absents | `.env.secrets/` manquant | Compose refuse de démarrer, avec un message nommant le fichier | — |

</frozen-after-approval>

## Code Map

Le dépôt ne contient aucun code : seulement `docs/`, des README et `.gitignore`. Le `.gitignore` ignore déjà `.env.*` (donc `.env.secrets/`) mais garde `.env.example`.

Empreintes vérifiées le 24/11/2026 :

| Image | Empreinte |
|---|---|
| `postgis/postgis:16-3.7` | `sha256:2412104d3a48ad3b76adfa60a71638c93727dcbb49dd5a9207e4e83ab3591716` (amd64 seulement) |
| `valkey/valkey:9.2.0` | `sha256:1c2b25b09f354c66fe994733acdf12fcfd4bdf6f3bd92b88a93a70378d884056` |
| `dxflrs/garage:v2.5.0` | `sha256:677e5b758e4425a325b811c425c026bf35a4bf42f7ddbaa773de3f4fd779a5a5` |
| `caddy:2.11.9-alpine` | `sha256:003a97808e781aa9f7e75cc2f43d34d461099031faf5e20faefb9f61126836f0` |
| `python:3.12.16-slim-trixie` | `sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b` |

Garage v2.5 : `garage server --single-node --default-bucket` lit `GARAGE_DEFAULT_BUCKET`, `GARAGE_DEFAULT_ACCESS_KEY` et `GARAGE_DEFAULT_SECRET_KEY`. Il exige un fichier `garage.toml` (`replication_factor = 1`, `rpc_secret`, `metadata_dir`, `data_dir`, `[s3_api]`). L'image ne contient que le binaire `/garage`.

## Tasks & Acceptance

**Exécution :**
- [x] `backend/pyproject.toml`, `backend/uv.lock` — dépendances épinglées :
  - application : fastapi 0.165.0, uvicorn[standard] 0.54.0, pydantic 2.14.4, pydantic-settings 2.16.x, sqlalchemy 2.1.9, geoalchemy2 0.21.0, alembic 1.20.1, psycopg[binary] 3.3.9, arq 0.28.0 (redis 5.3.1), structlog 26.1.0 ;
  - développement : pytest 9.2.0, ruff 0.17.6, import-linter.
- [x] `backend/app/core/{config,db,errors,logging,clock,enums}.py` — briques minimales :
  - `Settings` lit les variables d'environnement et `/run/secrets/` ;
  - un moteur SQLAlchemy ;
  - `DomainError` ;
  - `structlog` en JSON ;
  - `now()` en UTC ;
  - les énumérations de l'épine (codes en anglais).
- [x] `backend/app/modules/{auth,reports,missions,lots,analytics,ai,notifications}/__init__.py`, `backend/app/reactions.py` (vide), `backend/app/main.py` (application FastAPI sans route) et `backend/app/worker.py` (`WorkerSettings` arq avec une tâche `noop`).
- [x] `backend/migrations/` (Alembic, `env.py` sur `MIGRATOR_DATABASE_URL`, révision `0001_baseline` vide) et `backend/alembic.ini`.
- [x] `backend/Dockerfile` — image unique pour `api`, `worker` et `migrate`, construite par `uv sync --frozen`, utilisateur non root.
- [x] `backend/tests/{unit,integration,authz,architecture}/` et `backend/scripts/`, plus deux tests :
  - `tests/integration/test_db_roles.py` : `CREATE TABLE` refusé à `teranga_app`, autorisé à `teranga_migrator`, extension PostGIS active ;
  - `tests/unit/test_layout.py` : arborescence de l'AC 1.
- [x] `infra/db/initdb/20-roles.sh` — crée `teranga_migrator` (propriétaire du schéma `public`) et `teranga_app` (CONNECT, USAGE, DML seulement), avec `ALTER DEFAULT PRIVILEGES FOR ROLE teranga_migrator` sur les tables et les séquences. Les mots de passe sont lus dans `/run/secrets/`.
- [x] `infra/garage/garage.toml` (configuration un nœud) et `infra/Caddyfile` (`:80`, proxy vers `api:8000`, sans exposition de `/metrics`).
- [x] `infra/docker-compose.yml`, avec les profils `demo` et `prod` :
  - services `caddy`, `api`, `worker`, `migrate`, `db`, `valkey` (`--appendonly yes`, volume) et `garage` (volumes `meta` et `data`) ;
  - healthchecks : `pg_isready`, `valkey-cli ping`, `/garage status` ;
  - dépendances : `migrate` attend `db` healthy ; `api` et `worker` attendent la réussite de `migrate`.
- [x] `compose.yaml` à la racine — `include: infra/docker-compose.yml`, pour que la commande fonctionne depuis la racine.
- [x] `infra/seed/.gitkeep`, `ml/contract/.gitkeep`, `ml/release/.gitkeep`, `.github/workflows/.gitkeep` — dossiers attendus par l'arborescence.
- [x] `.env.example` (variables non secrètes) et `infra/gen-dev-secrets.py` (génère `.env.secrets/` avec des valeurs aléatoires) ; `README.md` mis à jour avec la section « Démarrer en local ».

**Critères d'acceptation :**
- Étant donné un clone vierge, quand on lance `python infra/gen-dev-secrets.py` puis `docker compose --profile demo up -d`, alors `docker compose ps` montre `db`, `valkey` et `garage` à l'état `healthy`, `migrate` en `Exited (0)`, et `api`, `worker` et `caddy` à l'état `running`.
- Étant donné la pile démarrée, quand on lance les tests d'intégration contre `db`, alors ils passent (rôles et PostGIS).
- Étant donné le dépôt, quand on cherche des images sans `@sha256:` dans `infra/docker-compose.yml`, alors on n'en trouve aucune.
- Étant donné `uv.lock`, quand on lance `uv sync --frozen`, alors l'installation réussit sans résolution.

## Implementation Notes

- **Clé S3 par défaut de Garage.** Le binaire v2.5.0 ne lit `GARAGE_DEFAULT_ACCESS_KEY` et `GARAGE_DEFAULT_SECRET_KEY` que dans l'environnement : `*_FILE` est ignoré (vérifié sur l'image épinglée). Le script génère donc `.env.secrets/garage.env`, chargé par `env_file` (`required: true`). C'est la seule entorse à « un fichier par secret ». C'est aussi ce fichier qui fait refuser le démarrage à Compose quand `.env.secrets/` manque, avec un message qui le nomme. Les valeurs restent visibles par `docker inspect garage`.
- **Secret RPC de Garage.** Il n'est pas dans `garage.toml` (versionné) : `rpc_secret_file` pointe vers `/run/secrets/garage_rpc_secret`. `allow_world_readable_secrets = true` est nécessaire parce que les secrets Compose montés depuis l'hôte sont lisibles par tous.
- **Port de `db` (écart avec la Design Note).** Un service `db-prod` sans port, dérivé de `db` par `extends`, a été essayé puis abandonné. Compose active une dépendance `required: false` hors de son profil : en `demo`, deux PostgreSQL ont démarré sur le même volume. Il reste donc un seul `db`, dans les deux profils, publié sur `127.0.0.1:${DB_LOCAL_PORT:-5432}` seulement, jamais sur une interface publique. Si la production doit n'avoir aucun port publié, il faudra le trancher, par exemple avec un fichier de surcharge réservé à `demo`.
- **Images construites.** `api`, `worker` et `migrate` n'ont qu'une clé `build:` (même `backend/Dockerfile`), sans `image:`. Ainsi, la recherche d'images sans `@sha256:` ne trouve rien. Compose construit trois fois la même image, à partir du cache. Le Dockerfile épingle `python:3.12.16-slim-trixie` et `ghcr.io/astral-sh/uv:0.13.7` par empreinte.
- **Secret isolé manquant.** Compose ne vérifie pas l'existence des fichiers de `secrets:`. Si un seul fichier manque, Docker crée un dossier vide à sa place. `gen-dev-secrets.py` remplace ce dossier, et `20-roles.sh` échoue si un mot de passe n'est pas un fichier non vide.
- **Fins de ligne.** `core.autocrlf=true` est actif sur le poste. Le nouveau `.gitattributes` force LF pour `*.sh` et les fichiers lus dans les conteneurs ; sinon, un clone Windows casserait `20-roles.sh`.
- **Journaux.** structlog sort en JSON. Les journaux propres à uvicorn et arq restent dans leur format par défaut, à harmoniser avec la story 1.2.
- **Poste Windows.** Une stratégie Application Control bloque les extensions natives (SQLAlchemy, pytest.exe) dans `backend/.venv`. ruff et les tests ont été lancés dans un conteneur `ghcr.io/astral-sh/uv:0.13.7-python3.12-trixie-slim`, avec `uv sync --frozen`.

## Spec Change Log

## Review Triage Log

Passe 1 (24/11/2026). Couches : Blind Hunter (B), Edge Case Hunter (E), Verification Gap (V).

| # | Constat | Verdict | Preuve | Route |
|---|---|---|---|---|
| E1 | Journaux uvicorn en texte brut malgré le commentaire « JSON » | low | Les loggers `uvicorn.*` ont `propagate=False` et leurs propres handlers ; `configure_logging` ne les touche pas | patch (G1) |
| E2 | Journaux arq imprimés deux fois | low | La CLI `arq` installe un handler sur `arq` (propagation active) ; la racine les réimprime en JSON | patch (G1) |
| E3 | `DATABASE_URL` en `postgresql://` charge psycopg2 absent | low | Réel, mais aucune commande ni doc ne fournit `DATABASE_URL` ; la correction ajoute une branche | rejeté |
| E4 / B3 | Règle `ENV`/`DEMO_MODE` annoncée dans `.env.example`, jamais appliquée | medium | Aucun validateur dans `Settings` ; `ENV=prod` + `DEMO_MODE=true` démarre | patch (G2) |
| E5 | Secret gardé avec un mode restrictif illisible | low | Seulement si l'utilisateur a changé le mode lui-même ; la correction ajoute du code | rejeté |
| E6 | Dossier non vide à la place d'un secret | low | Docker ne crée que des dossiers vides ; cas improbable | rejeté |
| E7 / B15 | `caddy`, `api` et `worker` sans signal de santé (502 transitoire possible) | low | Réel au démarrage, mais la sonde `/healthz` arrive avec la story 1.2 | rejeté (story 1.2) |
| E8 / B8 / V3 | README : port 5432 codé en dur, commandes bash seulement | low | `DB_LOCAL_PORT` documenté puis ignoré dans les URL de test | patch (G5) |
| B1 | `backend/README.md` et `uv.lock` absents du diff | false | Exclus volontairement du diff ; les deux fichiers existent, et l'image se construit | rejeté |
| B2 | `.gitignore` sans `.env`, `.env.secrets/`, `.venv`, caches | false | `git check-ignore` confirme que tous sont ignorés (`.env.*`, `.venv/`, `__pycache__/`, `.gitignore` interne de `.ruff_cache`) | rejeté |
| B4 | URL de base dérivées en `str` : mots de passe visibles dans `repr(settings)` | medium | `database_url` et `migrator_database_url` sont des `str` construits avec `hide_password=False` | patch (G3) |
| B5 | Contrats import-linter absents | low | Aucun module métier n'existe encore à violer ; contrats prévus par la story 1.4 | rejeté (story 1.4) |
| B6 | Profil `prod` identique au profil démo (port de `db` publié dans les deux) | low | Port lié à `127.0.0.1` seulement, aucun déploiement `prod` avant les stories 8.x ; écart documenté dans les Implementation Notes | rejeté |
| B7 | `env.py` ne verra pas les futurs modèles | low | Aucun modèle n'existe ; la première story avec des tables doit les importer | rejeté |
| B9 | `test_reactions_module_is_empty` fragile | low | Faux positif seulement si on réécrit la docstring ; aucun impact utilisateur | rejeté |
| B10 | `test_no_forbidden_dependency` ne regarde pas `uv.lock` | low | Vérifié à la main : `uv.lock` ne contient pas `sqlmodel` | rejeté |
| B11 | `--force` régénère les mots de passe de base sans prévenir | low | Le docstring prévient, mais pas la sortie ; correction directe (un message) | patch (G7) |
| B12 | `10-roles.sh` passe avant `10_postgis.sh` de l'image | low | L'image contient `10_postgis.sh` ; `-` se trie avant `_` ; fonctionne aujourd'hui grâce au superutilisateur | patch (G8) |
| B13 | Tests absents pour `TEMPORARY`, `TRUNCATE`, `CONNECT` d'un autre rôle | low | Les droits sont corrects (non accordés) ; seuls des tests de non-régression manquent | rejeté |
| B14 | `.env.example` en CRLF sur Windows, copié tel quel en `.env` | maybe-false | Dépend du traitement de `\r` par Compose ; correction directe dans `.gitattributes` | patch (G9) |
| V1 | Dérivation des URL de base sans test | medium | Aucun test n'importe `app.core.config` ; une inversion des rôles passerait inaperçue | patch (G4) |
| V2 | Tests d'intégration ignorés en silence, aucune CI | medium | `pytest.skip` sans les variables `TEST_*` ; `.github/workflows/` vide | defer (story 1.4) |

## Design Notes

**Créer les rôles hors Alembic.** `teranga_migrator` ne peut pas créer de rôle. Le script `initdb` est exécuté une seule fois par le superutilisateur, à la création du volume.

**Droits de `teranga_app`.** Les `DEFAULT PRIVILEGES` lui donnent les droits DML sur les tables que créeront les futures migrations, sans action supplémentaire.

**Accès à la base.** `db` n'expose son port que sur `127.0.0.1:5432`, profil `demo` uniquement, pour les tests locaux.

## Verification

**Commandes :**
- `cd backend && uv sync --frozen && uv run ruff check . && uv run pytest tests/unit` — attendu : succès.
- `docker compose --profile demo up -d --wait` — attendu : code 0, services sains.
- `cd backend && uv run pytest tests/integration` (avec `TEST_APP_DATABASE_URL` et `TEST_MIGRATOR_DATABASE_URL` sur `localhost:5432`) — attendu : succès.
- `docker compose --profile demo down -v` — attendu : nettoyage complet.
