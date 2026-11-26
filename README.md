# TerangaCycle AI

**Transformer un déchet signalé par un citoyen en ressource tracée, classée par IA et confiée au bon collecteur ou recycleur local, avec des données hébergées et gouvernées au Sénégal.**

Projet présenté au hackathon **« Afrique Makers : l'innovation au service d'une souveraineté technologique durable et inclusive »**.

> 🚧 Projet en cours de construction : la documentation est en place, le code source arrive au fur et à mesure.

---

## Le problème

À Dakar comme dans beaucoup de villes, les dépôts sauvages sont signalés de manière informelle (appels, réseaux sociaux), sans géolocalisation fiable ni suivi. Les récupérateurs informels et les petits recycleurs n'ont aucun outil pour savoir où se trouve la matière valorisable, et les communes manquent de données pour planifier les tournées.

## La solution

Une application web progressive (PWA), utilisable hors-ligne, qui relie citoyens, collecteurs, recycleurs et communes :

```
Signaler → Classifier (IA) → Dispatcher → Collecter → Valoriser → Mesurer l'impact
```

1. **Le citoyen** prend une photo du dépôt : la position GPS est captée automatiquement et un modèle d'IA embarqué propose le type de déchet (plastique, métal, verre, organique, mixte), même sans réseau.
2. **Le collecteur** voit les missions proches, en accepte une, puis prouve la collecte par photo et poids.
3. **Le recycleur** consulte les lots de matière disponibles par type et par zone.
4. **La commune** pilote avec une carte de chaleur, des indicateurs (kg valorisés, délais) et des exports ouverts.

Le cœur du projet n'est pas le signalement mais **la valorisation** : le matching entre déchet, collecteur et recycleur.

## Souveraine, durable, inclusive

| | Ce que fait TerangaCycle AI |
|---|---|
| **Souveraineté** | Modèle IA open source (MobileNetV3 → ONNX) exécuté sur le téléphone ou un serveur local, aucune API d'IA étrangère, données exportables, plan de sortie vers un hébergeur local |
| **Durable** | Économie circulaire : chaque déchet devient une matière tracée, avec des indicateurs d'impact mesurés |
| **Inclusive** | Français et wolof, mode hors-ligne, pictogrammes, canal SMS/WhatsApp, récupérateurs informels intégrés comme acteurs rémunérés |

## Stack technique

| Couche | Technologies |
|---|---|
| Frontend | React + TypeScript (Vite), PWA (Workbox), Dexie/IndexedDB, Leaflet, i18next, Tailwind CSS |
| IA | PyTorch (fine-tuning MobileNetV3), ONNX Runtime (serveur) et onnxruntime-web (navigateur) |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, arq |
| Données | PostgreSQL 16 + PostGIS, Redis, stockage objet compatible S3 (MinIO) |
| Infra | Docker Compose, Caddy ; pilote AWS (Terraform) ; cible : hébergeur local |
| Qualité | pytest, Vitest, Playwright, k6, GitHub Actions, Gitleaks, Bandit, Trivy |

## Démarrer en local

Prérequis : Docker avec Compose v2.24 ou plus récent, sur une machine x86_64 (l'image `postgis/postgis` n'existe qu'en amd64), et Python 3 pour le script de secrets.

```bash
# 1. Secrets factices dans .env.secrets/ (hors Git) et .env copié de .env.example.
#    À relancer après une mise à jour : il crée les secrets manquants sans rien écraser.
python infra/gen-dev-secrets.py

# 2. Démarrer la pile de démonstration depuis la racine du dépôt
docker compose --profile demo up -d --wait

# 3. Vérifier : db, valkey, garage, api, worker et caddy « healthy »,
#    migrate « Exited (0) »
docker compose --profile demo ps -a
```

Caddy construit la PWA dans son image (`infra/caddy/Dockerfile`, Node 26) : après une modification de `web/`, relancer avec `--build`. Ouvrir ensuite **`https://app.localhost:<HTTPS_PORT>`** dans Chrome (`https://app.localhost` si `HTTPS_PORT=443`, la valeur par défaut). Chrome résout `*.localhost` vers `127.0.0.1` ; `http://` redirige vers `https://`.

**Certificat local.** Pour `*.localhost`, Caddy émet un certificat de son propre CA interne, que la machine ne connaît pas : Chrome affiche d'abord un avertissement, qu'on peut passer en développement. Pour l'éviter, approuver ce CA sur l'hôte. `docker compose exec caddy caddy trust` ne l'installe que dans le conteneur ; pour l'hôte, copier le certificat racine puis l'importer comme autorité de confiance :

```bash
docker compose cp caddy:/data/caddy/pki/authorities/local/root.crt ./caddy-root.crt
# Windows (PowerShell) : Import-Certificate -FilePath .\caddy-root.crt -CertStoreLocation Cert:\CurrentUser\Root
# macOS : sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain caddy-root.crt
# Linux (Chrome) : certutil -d sql:$HOME/.pki/nssdb -A -t C,, -n caddy-local -i caddy-root.crt
```

Le CA est gardé dans le volume `caddy-data` : à refaire après `docker compose down -v`. En démo réelle, `APP_HOST` et `MEDIA_HOST` sont de vrais domaines et Caddy obtient un certificat Let's Encrypt.

Sur `APP_HOST`, Caddy sert la PWA, et relaie vers l'API `/v1/*`, `/healthz` et `/readyz` ; toute autre adresse sans extension renvoie `index.html` (routage côté client), un fichier absent renvoie 404. Sur `MEDIA_HOST` (`media.localhost`), il relaie vers Garage la seule lecture (`GET`, `HEAD`) des photos du bucket `S3_BUCKET` (`/<bucket>/<clé>`, 403 sans signature) ; tout autre chemin reçoit 404 et toute autre méthode 405.

| Adresse | Réponse |
|---|---|
| `/healthz` | Vivacité : `{"status": "ok"}`, sans aucune dépendance |
| `/readyz` | `{"status": "ready"}` si la base, Valkey, le bucket et le battement du worker (moins de 60 s) répondent, sinon 503 `{"status": "not_ready"}` |
| `/v1/config` | Configuration publique : `demo_mode`, `env`, `model_version` |
| `POST /v1/reports` | Signalement anonyme (`X-Device-Id`, `multipart/form-data` : `meta` en JSON et `photo`) : 201 avec `id`, `tracking_number` (`TC-AAAA-NNNNNN`), `status`, `received_at`, `is_demo` ; 200 avec les mêmes champs pour un renvoi du même `meta.client_uuid` |
| `/metrics`, `/v1/ai/*` | Jamais relayées par Caddy (404) ; `/metrics` au format Prometheus sur le réseau Compose seulement (`http://api:8000/metrics`) |

**`POST /v1/reports`** (story 1.11). En-tête `X-Device-Id` : 32 octets aléatoires en base64url, 43 caractères ; aucun `Authorization`. Corps `multipart/form-data` de 2 Mo au plus (Caddy et l'API) :
- `photo` : JPEG, PNG ou WebP, 1 Mo au plus, 12 mégapixels au plus ; stockée ré-encodée en JPEG sans métadonnées ;
- `meta` (JSON, champs inconnus refusés) : `client_uuid` (Identifiant client : UUID version 4, tiré une fois par Signalement avec un générateur cryptographique, `crypto.randomUUID()` ; toute autre version → 422 `meta.client_uuid`), `lat` (−90 à 90), `lng` (−180 à 180), `accuracy_m` (> 0 ; au-delà de `REPORT_ACCURACY_FLAG_M`, drapeau « position imprécise »), `heap_size` (`small`, `medium`, `large`), `comment` facultatif (280 caractères au plus après retrait des blancs de bord ; vide = aucun), `waste_type` facultatif (`plastic`, `metal`, `glass`, `organic`, `mixed`), `captured_at` (ISO 8601 avec fuseau, entre le 01/01/2000 et maintenant + 1 jour ; jamais utilisée pour décider), `consent` : `{terms, training}`.

Erreurs (enveloppe `{"error": {"code", "message", "request_id"}}` ; une requête refusée n'écrit rien). Ordre des contrôles : en-têtes (400, 401, taille du corps 413), `meta` et photo présents (422), Identifiant client déjà reçu (200 ou 409, voir plus bas), consentement, Zone active, puis la photo elle-même (413, 415, 422) :

| Statut | Code | Cas |
|---|---|---|
| 400 | `invalid_device_id` | `X-Device-Id` absent, répété ou mal formé (contrôlé avant le corps, et avant le jeton) |
| 401 | `invalid_token` | en-tête `Authorization` présent (aucun jeton vérifiable avant l'Epic 2) |
| 413 | `photo_too_large` | corps de plus de 2 Mio (`Content-Length`, avant lecture) ou photo de plus de 1 Mo ; Caddy refuse aussi en 413 tout corps de plus de 2 Mo |
| 422 | `validation_error` | `meta` absent, illisible ou invalide, ou photo absente ; le message nomme le champ (`meta.lat`, `photo`), jamais sa valeur |
| 409 | `client_uuid_conflict` | `meta.client_uuid` déjà utilisé par un autre auteur ; l'enveloppe d'erreur seule (contrôlé avant le consentement, la Zone et la photo) |
| 422 | `consent_required` | `consent.terms` absent ou faux |
| 422 | `outside_active_zone` | Position hors de la Zone active (`ACTIVE_ZONE_ID`) |
| 415 | `unsupported_media_type` | photo ni JPEG, ni PNG, ni WebP (format lu dans les octets) |
| 422 | `photo_too_many_pixels`, `photo_unreadable` | photo de plus de 12 mégapixels, ou illisible |
| 503 | `storage_unavailable` | stockage des photos indisponible |

L'Organisation responsable (commune ou opérateur dont la Zone couvre la Position, sinon l'Organisation plateforme) n'est jamais renvoyée.

**Renvoi sans doublon** (story 1.12). `meta.client_uuid` (Identifiant client, généré une fois par Signalement sur le téléphone) rend la route idempotente par auteur ; aucune clé `Idempotency-Key` n'est demandée. Après les contrôles des en-têtes et de `meta`, et avant le consentement, la Zone active et la photo, le Signalement est cherché par son Identifiant client :

| Statut | Cas | Réponse |
|---|---|---|
| 200 | même auteur (même `X-Device-Id`), même `client_uuid` | le Signalement déjà enregistré : mêmes champs qu'en 201, valeurs de la première réception et Statut actuel. Rien n'est écrit (ni ligne, ni photo, ni Numéro consommé) et le contenu renvoyé (photo, Position, commentaire…) est ignoré, même s'il diffère |
| 409 | `client_uuid_conflict` : autre auteur, même `client_uuid` | l'enveloppe d'erreur seule, rien du Signalement existant |

Le client peut donc renvoyer sans risque un envoi dont il n'a pas reçu la réponse (coupure réseau) : il obtient le Numéro de suivi attribué à la première réception. Des envois simultanés du même `client_uuid` se suivent (verrou de transaction sur l'Identifiant client) : un seul 201, puis des 200 pour le même auteur, sans photo stockée, ou 409 pour un autre ; l'unicité `(client_uuid, owner_key)` est en outre garantie par la base (migration `0004`, refusée avec le nombre de paires en double s'il en existe déjà).

La documentation OpenAPI (`/docs`, `/redoc`, `/openapi.json`, absente quand `ENV=prod`) n'est plus relayée par Caddy : ces adresses servent la PWA. Elle reste servie par l'API sur le réseau Compose (`http://api:8000/docs`).

En `ENV=demo` ou `prod`, l'API et le worker refusent de démarrer si un secret de l'inventaire manque dans `.env.secrets/` (le message nomme le secret). Quel que soit `ENV`, l'API refuse aussi de démarrer si `DEVICE_ID_PEPPER` est mal formé (32 octets en base64 attendus) : le générer avec `python infra/gen-dev-secrets.py`. En `dev` sans ce secret, une valeur éphémère est tirée à chaque démarrage : les empreintes d'appareil (`owner_key`) changent alors à chaque redémarrage. Tests de fumée, pile démarrée :
- bord Caddy (chaque cas de la story 1.3 en HTTPS, certificat local non vérifié, plus un `POST /v1/reports` au Plateau qui doit renvoyer 201, story 1.11) : `python backend/scripts/smoke_edge.py` ;
- `/readyz` (arrête puis relance tour à tour `db`, `valkey`, `garage` et `worker`) : `python backend/scripts/smoke_readyz.py`.

Les deux scripts se connectent à `127.0.0.1` en HTTPS avec `APP_HOST` et `HTTPS_PORT` (environnement, sinon `.env`).

Si les ports 80, 443, 5432 ou 3900 sont déjà pris sur la machine, changer `HTTP_PORT`, `HTTPS_PORT`, `DB_LOCAL_PORT` et `GARAGE_LOCAL_PORT` dans `.env`.

| Service | Rôle |
|---|---|
| `caddy` | Bord HTTPS : PWA et API sur `APP_HOST`, photos (Garage) sur `MEDIA_HOST` |
| `api` | API FastAPI (rôle de base `teranga_app`, DML seulement) |
| `worker` | Worker arq, même image que l'API |
| `migrate` | `alembic upgrade head` avec le rôle `teranga_migrator`, puis s'arrête ; `api` et `worker` attendent sa réussite |
| `db` | PostgreSQL 16 + PostGIS, port publié sur `127.0.0.1` seulement |
| `valkey` | Valkey en AOF (file arq, limites de débit) |
| `garage` | Stockage objet S3, un nœud, bucket privé par défaut ; API S3 publiée sur `127.0.0.1` seulement (`GARAGE_LOCAL_PORT`) |

Les rôles `teranga_migrator` et `teranga_app` sont créés par `infra/db/initdb/20-roles.sh` à la création du volume de la base. Après un changement de secret de base, recréer les volumes : `docker compose --profile demo down -v`.

**Backend sans Docker** (dans `backend/`, avec [uv](https://docs.astral.sh/uv/)) :

```bash
uv sync --frozen
uv run ruff check .
uv run pytest tests/unit
```

Tests d'intégration, pile démarrée : mots de passe dans `.env.secrets/`, ports `DB_LOCAL_PORT` (5432 par défaut) et `GARAGE_LOCAL_PORT` (3900 par défaut) et bucket `S3_BUCKET` du `.env`.

```bash
# bash
DB_LOCAL_PORT="$(sed -n 's/^DB_LOCAL_PORT=//p' ../.env)"; DB_LOCAL_PORT="${DB_LOCAL_PORT:-5432}"
export TEST_APP_DATABASE_URL="postgresql://teranga_app:$(cat ../.env.secrets/db_app_password)@localhost:${DB_LOCAL_PORT}/terangacycle"
export TEST_MIGRATOR_DATABASE_URL="postgresql://teranga_migrator:$(cat ../.env.secrets/db_migrator_password)@localhost:${DB_LOCAL_PORT}/terangacycle"
# Garage (core.storage) : API S3 publiée sur 127.0.0.1:GARAGE_LOCAL_PORT.
GARAGE_LOCAL_PORT="$(sed -n 's/^GARAGE_LOCAL_PORT=//p' ../.env)"; GARAGE_LOCAL_PORT="${GARAGE_LOCAL_PORT:-3900}"
S3_BUCKET="$(sed -n 's/^S3_BUCKET=//p' ../.env)"; S3_BUCKET="${S3_BUCKET:-terangacycle-photos}"
export TEST_S3_ENDPOINT="http://127.0.0.1:${GARAGE_LOCAL_PORT}"
export TEST_S3_BUCKET="${S3_BUCKET}"
export TEST_S3_ACCESS_KEY_ID="$(cat ../.env.secrets/s3_access_key_id)"
export TEST_S3_SECRET_ACCESS_KEY="$(cat ../.env.secrets/s3_secret_access_key)"
uv run pytest tests/integration
```

```powershell
# PowerShell
$port = (Select-String -Path ..\.env -Pattern '^DB_LOCAL_PORT=(.+)$').Matches.Groups[1].Value
if (-not $port) { $port = '5432' }
$appPw = (Get-Content ..\.env.secrets\db_app_password -Raw).Trim()
$migratorPw = (Get-Content ..\.env.secrets\db_migrator_password -Raw).Trim()
$env:TEST_APP_DATABASE_URL = "postgresql://teranga_app:${appPw}@localhost:${port}/terangacycle"
$env:TEST_MIGRATOR_DATABASE_URL = "postgresql://teranga_migrator:${migratorPw}@localhost:${port}/terangacycle"
$s3Port = (Select-String -Path ..\.env -Pattern '^GARAGE_LOCAL_PORT=(.+)$').Matches.Groups[1].Value
if (-not $s3Port) { $s3Port = '3900' }
$bucket = (Select-String -Path ..\.env -Pattern '^S3_BUCKET=(.+)$').Matches.Groups[1].Value
if (-not $bucket) { $bucket = 'terangacycle-photos' }
$env:TEST_S3_ENDPOINT = "http://127.0.0.1:${s3Port}"
$env:TEST_S3_BUCKET = $bucket
$env:TEST_S3_ACCESS_KEY_ID = (Get-Content ..\.env.secrets\s3_access_key_id -Raw).Trim()
$env:TEST_S3_SECRET_ACCESS_KEY = (Get-Content ..\.env.secrets\s3_secret_access_key -Raw).Trim()
uv run pytest tests/integration
```

**PWA sans Docker** (dans `web/`, Node 26) : `npm ci`, `npm run dev` (serveur de développement sur le port 5173), `npm test`, `npm run build`. Détails dans [`web/README.md`](web/README.md).

**Arrêter et tout effacer** (conteneurs et volumes) : `docker compose --profile demo down -v`.

## Intégration continue

Le workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) tourne sur chaque pull request vers `main` et chaque push sur `main` ; le job `audit` tourne aussi seul chaque lundi à 06:00 UTC (et à la demande, `workflow_dispatch`), pour voir une faille publiée après la fusion. Il ne demande aucun secret GitHub : les secrets de la pile sont générés à chaque exécution par `infra/gen-dev-secrets.py`. Cinq jobs :

| Job | Vérifications |
|---|---|
| `backend` | `ruff check`, `ruff format --check`, `lint-imports` (contrats d'import), export de l'OpenAPI comparé à `web/src/api/openapi.json`, puis la pile Docker Compose démarrée et `pytest --cov` : tests unitaires, d'architecture et d'intégration, couverture d'au moins 60 % |
| `web` | `npm run lint` (oxlint), `npm test` (Vitest), types du client API régénérés et comparés à `src/api/schema.d.ts`, `npm run build` (Node 26), budget de poids, Playwright et axe |
| `edge` | après `backend` et `web` : image Caddy construite, pile démarrée, `smoke_edge.py` puis `smoke_readyz.py` |
| `hygiene` | Gitleaks 8.30.1 (commits de la PR, tout l'historique sur `main`) avec [`.gitleaks.toml`](.gitleaks.toml) ; `scripts/ci/check_pinning.py` (images par `tag@sha256:`, actions par SHA de commit) ; `scripts/ci/check_repo_hygiene.py` (aucun document interne ni `.env` suivi, motifs de `.gitignore`, `LICENSE`, exceptions d'audit non expirées) |
| `audit` | `pip-audit` 2.10.1 sur les dépendances d'exécution du backend (`uv export --locked --no-dev`), `npm audit --omit=dev` (gravité `high` ou plus), Trivy 0.76.2 sur les images `api` et `caddy` construites (failles `HIGH` et `CRITICAL` corrigeables, secrets laissés dans les images) |

**Secrets et adresses Figma.** Gitleaks applique ses règles par défaut, plus la règle `figma-file-url` : une adresse `figma.com/design/…` (ou `file`, `proto`, `board`, `slides`, `deck`, `make`, `site`) suivie d'une clé de 22 caractères fait échouer `hygiene` (les placeholders `<clé>` ou `{key}` passent). Avant le balayage, le job vérifie que Gitleaks détecte bien une adresse Figma fabriquée. Les faux positifs connus sont listés dans `.gitleaks.toml`, chacun justifié. Gitleaks et Trivy sont téléchargés en version épinglée et vérifiés par leur somme SHA-256 avant extraction.

**Exceptions d'audit datées.** Une vulnérabilité acceptée (pas de correctif, code non atteint) se déclare dans [`security/audit-exceptions.toml`](security/audit-exceptions.toml) : outil (`pip-audit`, `npm-audit` ou `trivy`), identifiant, raison (une ligne) et date d'expiration, au plus 90 jours plus tard. Les jobs en tirent `--ignore-vuln` pour pip-audit, le `.trivyignore` de Trivy et le filtre du rapport de `npm audit`. Le lendemain de la date d'expiration, la CI échoue : il faut corriger, ou renouveler l'exception en la justifiant de nouveau.

**Mises à jour.** [Dependabot](.github/dependabot.yml) propose chaque semaine les mises à jour du backend (`uv`), du web (`npm`), des images de base (`docker`), des images de la pile Compose (`docker-compose`) et des actions (`github-actions`) ; mineures et correctifs sont groupés, et une version n'est proposée que 3 jours après sa publication.

**Licence et signalement.** Code sous [GNU AGPL-3.0](LICENSE). Les vulnérabilités se signalent en privé, voir [SECURITY.md](SECURITY.md).

**Contrats d'import** (`[tool.importlinter]` dans `backend/pyproject.toml`) :
- `layers` : dans chaque module, `router` → `service` → `repository`, jamais l'inverse ;
- `acyclic_siblings` : aucun cycle entre les modules de `app.modules` ;
- `protected` : un module n'importe d'un autre que son `service`, et seulement selon les flèches permises (`missions` → `reports`, `auth` ; `reports` → `ai`, `auth`, `orgs` ; `lots` → `missions`, `auth` ; `notifications` → `auth`) ; `app.core` n'importe aucun module. `app.main`, `app.worker` et `app.reactions`, racines de composition, en sont exclus.
- `s3_access` : seul `app.core.storage` importe `boto3`/`botocore`, plus la sonde `/readyz` (`app.core.health`) avec son propre client.

Dans le web, `fetch` est interdit hors de `web/src/api/` et `web/src/offline/` (règle `no-restricted-globals` d'oxlint, `web/.oxlintrc.json`).

**Client API généré.** La PWA appelle l'API par un client généré depuis l'OpenAPI, versionné avec le code : `web/src/api/openapi.json` (exporté par `backend/scripts/export_openapi.py`) et `web/src/api/schema.d.ts` (types `openapi-typescript`). Après tout changement d'une route, d'un schéma ou d'un code d'erreur, régénérer les deux fichiers puis les committer :

```bash
cd backend && uv run python scripts/export_openapi.py && cd ..
cd web && npm run api:types && cd ..
```

La CI refuse toute différence : le job `backend` relance l'export, le job `web` la génération des types (`git diff --exit-code`).

**Tests d'intégration obligatoires.** Avec `REQUIRE_INTEGRATION=1` (posé par la CI), un test marqué `integration` qui serait ignoré faute de `TEST_APP_DATABASE_URL`, `TEST_MIGRATOR_DATABASE_URL` ou des variables `TEST_S3_*` (Garage) échoue. Sans la variable, il est ignoré comme avant.

**Reproduire la CI en local**, depuis la racine du dépôt :

```bash
# backend (dans backend/, pile démarrée et URL de test posées comme plus haut)
cd backend
uv sync --locked   # échoue si uv.lock n'est plus à jour de pyproject.toml
uv run ruff check . && uv run ruff format --check . && uv run lint-imports
uv run ruff check --config pyproject.toml ../scripts/ci && uv run ruff format --config pyproject.toml --check ../scripts/ci
uv run python scripts/export_openapi.py && git diff --exit-code ../web/src/api/openapi.json
REQUIRE_INTEGRATION=1 uv run pytest --cov
cd ..

# web (dans web/, Node 26)
cd web && npm ci && npm run lint && npm test && npm run api:types && git diff --exit-code src/api/schema.d.ts && npm run build && cd ..

# edge : comme la CI (qui appelle python3 ; sous Windows, `python`)
python3 infra/gen-dev-secrets.py
docker compose --profile demo up -d --build --wait --wait-timeout 300
python3 backend/scripts/smoke_edge.py
python3 backend/scripts/smoke_readyz.py
docker compose --profile demo down -v   # efface aussi les volumes, comme en fin de job

# hygiene : scripts en bibliothèque standard, puis Gitleaks (image officielle)
python3 scripts/ci/check_pinning.py && python3 scripts/ci/check_repo_hygiene.py
docker run --rm -v "$PWD:/repo:ro" \
  zricethezav/gitleaks:v8.30.1@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f \
  git --no-banner --redact --config /repo/.gitleaks.toml /repo

# audit : backend (dans backend/) et web (dans web/)
uv export --locked --no-dev --no-emit-project --format requirements-txt -o /tmp/requirements.txt
uvx pip-audit==2.10.1 --disable-pip --strict -r /tmp/requirements.txt
npm audit --omit=dev --audit-level=high
```

**Protection de la branche `main`** (décisions du 24/11/2026, stories 1.4 et 1.5) : pull request obligatoire (sans approbation exigée), contrôles `backend`, `web`, `edge`, `hygiene` et `audit` obligatoires, force push et suppression de la branche interdits ; l'administratrice en est exemptée (`enforce_admins: false`). À appliquer une fois la CI verte sur une PR, par une personne administratrice du dépôt (`gh` remplace `{owner}/{repo}` par le dépôt courant ; `app_id` 15368 est GitHub Actions, seule source acceptée pour ces contrôles). `strict: false` permet de fusionner une PR qui n'est pas rebasée sur le dernier `main` : les fusions se font en local, depuis un `main` à jour, une fois la CI verte.

```bash
gh api -X PUT repos/{owner}/{repo}/branches/main/protection \
  -H "Accept: application/vnd.github+json" \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": false,
    "checks": [
      { "context": "backend", "app_id": 15368 },
      { "context": "web", "app_id": 15368 },
      { "context": "edge", "app_id": 15368 },
      { "context": "hygiene", "app_id": 15368 },
      { "context": "audit", "app_id": 15368 }
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0,
    "dismiss_stale_reviews": false,
    "require_code_owner_reviews": false
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
```

**Réglages de sécurité du dépôt** (story 1.5), par une personne administratrice : secret scanning et push protection, puis signalement privé des vulnérabilités (le canal de [SECURITY.md](SECURITY.md)).

```bash
gh api -X PATCH repos/{owner}/{repo} \
  -H "Accept: application/vnd.github+json" \
  --input - <<'EOF'
{
  "security_and_analysis": {
    "secret_scanning": { "status": "enabled" },
    "secret_scanning_push_protection": { "status": "enabled" }
  }
}
EOF
gh api -X PUT repos/{owner}/{repo}/private-vulnerability-reporting
```

## Documentation

| Document | Contenu |
|---|---|
| [📋 Cahier des charges](docs/cahier-des-charges.md) | Vision, acteurs, périmètre du MVP, 22 user stories, exigences non fonctionnelles, planning, risques, indicateurs d'impact, pitch |
| [🛠️ Dossier technique](docs/dossier-technique.md) | Architecture, modèle de données (SQL), API REST (38 endpoints), conception IA, sécurité, infrastructure, PWA hors-ligne, CI/CD |

## Organisation du dépôt

```
terangacycle-ai/
├── backend/   API FastAPI (à venir)
├── web/       PWA React + TypeScript (à venir)
├── ml/        Entraînement, export ONNX, fiche du modèle (à venir)
├── infra/     Docker Compose, Caddyfile, Terraform (à venir)
├── scripts/   Contrôles de la CI (scripts/ci/, bibliothèque standard Python)
├── security/  Exceptions d'audit datées
└── docs/      Cahier des charges et dossier technique
```

## Feuille de route

- [x] Cahier des charges et dossier technique
- [ ] Squelette du dépôt, CI, `docker compose up` fonctionnel
- [ ] Jeu de photos locales étiqueté et modèle de base évalué
- [ ] MVP : signalement, classification, carte, missions, tableau de bord, hors-ligne
- [ ] Pilote terrain dans un quartier

## Équipe

Projet porté par une équipe de trois personnes : développement fullstack, données et IA, design et pitch.

## Licence

**Licence :** [GNU Affero General Public License v3.0](LICENSE) (`AGPL-3.0-only`). Pour signaler une vulnérabilité, voir [SECURITY.md](SECURITY.md).
