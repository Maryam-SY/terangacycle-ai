---
title: 'Story 1.2 — Configuration, sondes et conventions d''API'
type: 'feature'
created: '2026-11-24'
status: 'done'
baseline_commit: '2add01a1da492b50ec6bf1feead74213e26c43b1'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-1-squelette-backend-et-docker-compose.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problème :** le squelette démarre, mais rien ne dit si l'API est vivante ou prête. Il n'y a ni unité de travail, ni format d'erreur commun, ni journal par requête, et la configuration ne bloque pas un secret manquant. Chaque module suivant risquerait d'inventer ses propres règles.

**Approche :** poser dans `core` les briques que tous les modules héritent :
- les sondes `/healthz` et `/readyz` ;
- le battement de cœur (heartbeat) du worker ;
- `/metrics` ;
- l'unité de travail avec `after_commit` et `after_rollback` ;
- l'enveloppe d'erreur et l'énumération des codes ;
- un journal JSON par requête, avec masquage des données sensibles ;
- `GET /v1/config` ;
- la documentation OpenAPI coupée en `prod` ;
- le refus de démarrer sur une configuration invalide ou un secret manquant (inventaire d'AD-26).

## Boundaries & Constraints

**Toujours :**
- `/healthz` ne dépend de rien d'externe.
- `/readyz` et les erreurs ne divulguent jamais de détail interne.
- Le `request_id` est généré par le serveur (UUID4) et renvoyé dans l'en-tête `X-Request-ID`.
- Le message d'un secret manquant nomme le secret, jamais sa valeur.
- Dépendances ajoutées et épinglées exactement dans `uv.lock` : `prometheus-client==0.26.0`, `boto3==1.44.10`.

**Jamais :**
- Aucune route métier.
- Aucune vérification du format cryptographique des clés : ce sont les stories qui les utilisent qui les valident.
- Le contrôle `onnx_sha256` de `/readyz` n'est pas fait ici (story 3.3).
- Pas d'alertes (`core.alerts`, story 2.2).
- `/metrics` n'est jamais exposé par Caddy.

## I/O & Edge-Case Matrix

| Scénario | Entrée / État | Résultat attendu | Erreurs |
|---|---|---|---|
| Vivacité | `GET /healthz`, base arrêtée | 200 `{"status":"ok"}` | — |
| Prêt | Base, Valkey, bucket et battement < 60 s | 200 `{"status":"ready"}` | — |
| Pas prêt | Une dépendance KO, ou battement absent ou ≥ 60 s | 503 `{"status":"not_ready"}`, corps sans détail | Chaque cause testée isolément |
| Route inconnue | `GET /v1/inexistant` | 404 `{"error":{"code":"not_found","message":…,"request_id":…}}` | — |
| Corps invalide | Erreur de validation FastAPI | 422, `code` = `validation_error` | — |
| Exception imprévue | Erreur levée dans une route | 500, `code` = `internal_error`, aucune trace dans le corps | Trace complète dans le journal |
| Config interdite | `ENV=prod` + `DEMO_MODE=true`, `ENV=demo` sans `DEMO_MODE`, `ENV=staging` | Démarrage refusé, code de sortie ≠ 0, message explicite | — |
| Secret manquant | `ENV=demo`, `/run/secrets/phone_pepper` absent | Démarrage refusé : « secret manquant : phone_pepper » | `ENV=dev` : valeur éphémère générée, avertissement |
| Documentation OpenAPI | `ENV=prod` : `/docs`, `/redoc`, `/openapi.json` | 404 | En `demo` ou `dev` : servies |
| Unité de travail | Effet `after_commit` puis exception | Effet non exécuté ; `after_rollback` exécuté | — |
| Masquage | Événement de journal avec `phone`, `token`, `otp`, `x-device-id`, `lat`, `lng` | Valeurs remplacées par `"***"` | — |

</frozen-after-approval>

## Code Map

Repris de la story 1.1, statut done (commit `75d2dd2`) :
- `backend/app/core/config.py` : `Settings` (pydantic-settings, `secrets_dir` = `/run/secrets`), URL de base en `SecretStr`, validateur `ENV`/`DEMO_MODE` déjà présent (le garder et l'étendre).
- `backend/app/core/db.py` : `Base`, `get_engine()`, `get_sessionmaker()`. Y ajouter l'unité de travail.
- `backend/app/core/errors.py` : `DomainError`. À transformer en paquet `core/errors/` (`__init__.py` réexporte `DomainError`, plus `codes.py`).
- `backend/app/core/logging.py` : `configure_logging` (racine JSON ; uvicorn et arq rerouteurés). Y ajouter le processeur de masquage.
- `backend/app/main.py` : `create_app()`.
- `backend/app/worker.py` : `WorkerSettings` (fonction `noop`, `on_startup`).
- `infra/docker-compose.yml` : `caddy` dépend de `api` (démarrage seulement) ; `api` et `worker` sans healthcheck.
- `infra/gen-dev-secrets.py` : bibliothèque standard seulement ; génère aujourd'hui les mots de passe de base, le secret RPC et `garage.env` (clé S3).
- Garage : endpoint `http://garage:3900`, région `garage`, adressage path-style, bucket `S3_BUCKET`.
- Les tests tournent dans le conteneur `ghcr.io/astral-sh/uv:0.13.7-python3.12-trixie-slim` (Application Control bloque les modules natifs sous Windows).

Inventaire AD-26 des fichiers de `/run/secrets/` :

| Fichier | Contenu |
|---|---|
| `jwt_signing_keys` | JSON `{"<kid>": "<graine Ed25519 base64>"}` |
| `phone_pepper`, `device_id_pepper`, `totp_enc_key` | 32 octets en base64 |
| `phone_enc_keys` | JSON `{"<key_id>": "<32 octets base64>"}` |
| `vapid_private_key` | Valeur temporaire en dev et démo ; la story 4.9 imposera une vraie clé P-256 |
| `s3_access_key_id`, `s3_secret_access_key` | Identiques à `garage.env` |
| `alert_webhook_url` | `http://localhost/alert-disabled` en dev et démo |

## Tasks & Acceptance

**Exécution :**
- [x] `backend/app/core/config.py` : inventaire `REQUIRED_SECRETS`.
  - En `demo` et `prod`, tout fichier absent ou vide déclenche une erreur qui nomme les secrets manquants. En `dev`, générer une valeur éphémère et émettre un avertissement.
  - Ajouter les réglages S3 (`s3_endpoint`, `s3_region`, `s3_bucket`) et `model_version: str | None = None`.
- [x] `backend/app/core/errors/{__init__,codes}.py` : `ErrorCode` (StrEnum : `not_found`, `method_not_allowed`, `validation_error`, `internal_error`), modèle `ErrorResponse`, gestionnaires pour `HTTPException`, `RequestValidationError`, `DomainError` et `Exception`.
- [x] `backend/app/core/db.py` : unité de travail.
  - Une session dans un `contextvar`.
  - `get_uow()`, dépendance FastAPI qui ouvre la session, valide le commit en sortie et annule en cas d'exception.
  - `@transactional` : rejoint l'unité en cours, ou en ouvre une pour une tâche.
  - `after_commit(fn, *args)` et `after_rollback(fn, *args)`.
- [x] `backend/app/core/logging.py` : processeur de masquage (clés insensibles à la casse).
- [x] `backend/app/core/http.py` (nouveau) : middleware `request_id` et journal d'accès (`request_id`, `route` = gabarit de route, `method`, `status`, `role` = `anonymous` par défaut, `duration_ms`), et compteurs et histogramme Prometheus.
- [x] `backend/app/core/health.py` (nouveau) : routes `/healthz`, `/readyz` et `/metrics`.
  - `/readyz` lance en parallèle, avec un délai de 2 s par vérification : `SELECT 1`, `PING` de Valkey, `head_bucket` (boto3, path-style, `request_checksum_calculation='when_required'`) et âge de `worker:heartbeat` inférieur à 60 s.
- [x] `backend/app/core/public.py` (nouveau) : route `GET /v1/config` → `{demo_mode, env, model_version}`.
- [x] `backend/app/main.py` : assembler l'application.
  - `docs_url`, `redoc_url` et `openapi_url` valent `None` si `ENV=prod`.
  - Inclure les gestionnaires, le middleware et les routes.
- [x] `backend/app/worker.py` : tâche asyncio lancée au démarrage, qui écrit `worker:heartbeat` (horodatage, TTL de 90 s) toutes les 15 s. `cron_jobs: list = []`. La tâche est arrêtée proprement par `on_shutdown`.
- [x] `infra/gen-dev-secrets.py` : générer tout l'inventaire. Les fichiers S3 reprennent les clés de `garage.env` s'il existe déjà.
- [x] `infra/docker-compose.yml` :
  - healthcheck `api` : `python -c` + `urllib` sur `/healthz` ;
  - healthcheck `worker` : script Python qui vérifie l'âge du battement ;
  - `caddy` attend que `api` soit `service_healthy` ;
  - monter l'inventaire des secrets dans `api` et `worker`.
- [x] Tests :
  - `backend/tests/unit/` : `test_errors.py`, `test_uow.py`, `test_logging_mask.py`, `test_health.py` (vérifications simulées, une à une en échec), `test_config.py` (secrets manquants, dev éphémère, `ENV` invalide), `test_docs_gating.py` ;
  - `backend/tests/architecture/test_no_tx_calls.py` : analyse AST de `app/modules/**/service.py` et `repository.py`, aucun appel `.commit(`, `.rollback(` ni `.begin(`.
- [x] `backend/scripts/smoke_readyz.py` : depuis l'hôte, arrêter tour à tour `db`, `valkey`, `garage` et `worker` (`docker compose stop`/`start`) et vérifier `/readyz` : 503 pendant l'arrêt, 200 après.

**Critères d'acceptation :**
- Étant donné la pile démarrée, quand on lance `docker compose --profile demo up -d --wait`, alors `api` et `worker` sont `healthy` et `GET /readyz` répond 200 au travers de Caddy.
- Étant donné la pile démarrée, quand on appelle `/metrics` depuis le réseau Compose, alors on obtient le format Prometheus ; quand on l'appelle au travers de Caddy, alors on obtient 404.
- Étant donné la pile démarrée, quand on lance `smoke_readyz.py`, alors il réussit pour les 4 dépendances.

## Implementation Notes

- **Service `migrate`.** Il appelait `get_settings()` : en `ENV=demo`, l'inventaire AD-26 (non monté dans `migrate`) bloquait la migration. `MigratorSettings` (sous-classe de `Settings`, `require_secrets = False`) sert à Alembic seulement : règles `ENV`/`DEMO_MODE` gardées, inventaire ni exigé ni monté.
- **Erreur de configuration sans valeur.** `Settings` a `hide_input_in_errors=True` et `load_settings()` traduit la `ValidationError` en `ConfigError` sans entrée. `load_settings_or_exit()` (API à l'import, worker) journalise `startup_refused` et sort avec le code 1, sans trace. Testé par sous-processus (`import app.main` et `import app.worker`).
- **Secrets via l'environnement.** pydantic-settings donne priorité aux variables d'environnement : un secret fourni par variable satisfait la vérification (aucun cas actuel).
- **`get_uow` en `scope="function"`.** Dans FastAPI 0.165, une dépendance `yield` en portée `request` (défaut) sort après l'envoi de la réponse. `UowSession = Annotated[Session, Depends(get_uow, scope="function")]` valide avant l'envoi ; une erreur de commit devient 500. `get_uow` est asynchrone pour que le `contextvar` soit visible par la route (une dépendance synchrone s'exécute dans un thread dont le contexte ne remonte pas). `@transactional` accepte fonctions et coroutines ; une unité synchrone refuse un effet coroutine (`TypeError`). Un effet `after_commit` en échec est journalisé sans annuler le commit ni les effets suivants.
- **500 dans le middleware.** Le middleware ASGI de `core/http.py` intercepte l'exception, journalise la trace (`unhandled_exception`, avec `request_id`) et répond l'enveloppe `internal_error`. Le gestionnaire `Exception` est enregistré en filet de sécurité. Les `HTTPException` hors 404/405/422 (aucune levée aujourd'hui) deviennent `validation_error` (4xx) ou `internal_error` (5xx), l'énumération restant fermée.
- **Journaux.** structlog passe par la bibliothèque standard : un seul gestionnaire JSON, qui suit le `sys.stdout` courant ; les `extra` des bibliothèques sont inclus, donc masqués. Masquage par fragment sur la clé normalisée (minuscules, `_` → `-`) : en sous-chaîne pour `phone`, `token`, `device-id`, `latitude`, `longitude`, `position`, `location`, `password`, `secret`, `pepper`, `cookie`, `authorization` ; en segment entier entre `-` pour `lat`, `lng`, `otp` (`start_lat` masqué, `platform` ou `latency_ms` non). Niveau filtré par la bibliothèque standard, lu à chaque appel. Lignes d'accès des sondes (`/healthz`, `/readyz`, `/metrics`) en DEBUG, toujours comptées. Le journal d'accès d'uvicorn est coupé (`--no-access-log` et logger `uvicorn.access` muet) : il contenait chemin et paramètres. Les deux premières lignes d'arq restent en texte (configurées par la CLI avant `on_startup`).
- **Route des métriques.** Libellé `route` = gabarit ; pour les routes Starlette (documentation), retrouvé par correspondance ; sans route, `<unmatched>` (cardinalité bornée).
- **`head_bucket` hors `core/storage`.** Fait dans `core/health.py`, comme le demande la spec ; à déplacer vers `core/storage` quand la story 1.10 le crée (AD-13).
- **Fabrique uvicorn.** Plus d'application créée à l'import : `uvicorn --factory app.main:create_app` (Dockerfile et Compose).
- **Sonde de base.** Moteur dédié sans pool (`connect_timeout=2`, `statement_timeout=2000`) ; client S3 issu d'une `boto3.session.Session()` en cache, délais de 1 s, sans nouvel essai. Battement refusé s'il est infini, NaN ou plus de 5 s dans le futur.
- **Production.** Un secret contenant un marqueur du générateur (`dev-placeholder`, `dev-ephemeral`, `alert-disabled`, `localhost`) est refusé en `prod`. `MODEL_VERSION` vide vaut `null`. `SettingsError` et `OSError` au démarrage : `startup_refused` avec le type seul.
- **Unité de travail.** Commit protégé de l'annulation (l'issue réelle du commit décide des effets) ; `_current` remis à zéro même si `close()` échoue. `DomainError` n'accepte qu'un `ErrorCode`.
- **Clé S3 du générateur.** `garage.env`, `s3_access_key_id` et `s3_secret_access_key` forment un jeu : repris si `garage.env` est complet (fichiers `s3_*` réalignés), sinon régénérés ensemble.
- **Client de test.** Aucune dépendance de test ajoutée (httpx absent) : `tests/asgi.py` appelle l'application ASGI directement.

## Spec Change Log

## Review Triage Log

Passe 1 (24/11/2026). Couches : Blind Hunter (B), Edge Case Hunter (E), Verification Gap (V). Constats regroupés par cause commune.

| # | Constat | Verdict | Preuve | Route |
|---|---|---|---|---|
| B1 / E8 | Battement daté dans le futur ou `inf` jugé frais | medium | `heartbeat_is_fresh` ne teste que `age < 60` ; un âge négatif ou `-inf` passe | patch (P1) |
| B2 / E15 | Masquage limité aux noms de clés exacts | medium | `_is_sensitive` compare une égalité stricte : `phone_number`, `access_token`, `latitude`, `device_id` passent en clair | patch (P2) |
| E17 / E26 | Texte des exceptions et arguments positionnels des bibliothèques non masqués | medium | `format_exc_info` s'exécute après `mask_sensitive` ; les `%`-args sont déjà fondus dans `event` | defer (story 1.11, première donnée personnelle) |
| E16 | Objets (set, dataclass, modèle pydantic) non masqués | low | Aucun appel actuel ne journalise de tels objets ; la correction ajoute des branches | rejeté |
| B3 | Étiquette `method` de Prometheus non bornée | medium | `scope["method"]` brut ; toute méthode inventée crée une série | patch (P3) |
| B4 / E5 | Délais de `/readyz` incohérents, threads accumulés | medium | Délai de connexion de 5 s et aucun `statement_timeout` face à un `wait_for` de 2 s ; S3 jusqu'à 4 s | patch (P4) |
| E7 | Client boto3 créé depuis la session par défaut, non sûre entre threads | low | Les premiers `/readyz` concurrents la partagent ; correction directe | patch (P4) |
| B5 / E6 | `check_database` ignore les `Settings` injectés | low | Passe par le `get_settings()` global ; sans effet en exécution, une seule configuration existe | rejeté |
| B6 / E21 | `app = create_app()` exécuté à l'import | medium | Un `ENV=prod` ou un `ENV` invalide dans l'environnement de l'hôte interrompt la collecte pytest | patch (P5) |
| B7 / E10 | 401, 403, 413, 429 renvoyés avec le code `validation_error` | low | Aucune route ne lève ces statuts aujourd'hui ; les codes viendront avec leurs stories | rejeté |
| E11 | Corps JSON sur 204 ou 304 | false | Aucune route ne lève `HTTPException(204/304)` | rejeté |
| B8 / E12 | `DomainError` accepte un code hors énumération | low | `code: str` sans contrôle ; correction directe (`ErrorCode(code)`) | patch (P6) |
| B9 | Erreur 422 sans détail des champs | low | L'enveloppe d'AD-11 est fixée à `{code, message, request_id}` | rejeté |
| B10 | Requêtes bloquantes dans une route `async def` avec `UowSession` | medium | Seuls commit, rollback et close passent par le pool de threads | patch (P7, règle documentée) |
| B11 | Échec de commit → 500, `after_rollback`, réponse retenue jusqu'au commit : aucun test | medium | Aucun test ne fait échouer `commit()` | patch (P8) |
| E1 | Annulation pendant le commit asynchrone | medium | `CancelledError` pendant `run_in_threadpool(commit)` lance un rollback concurrent | patch (P9) |
| E2 | `close()` en échec laisse l'unité dans le contexte | low | `_current.reset` est appelé après `close()` dans le même `finally` ; correction directe | patch (P9) |
| E3 / E4 | Fonction synchrone qui renvoie une coroutine, `partial` non détecté | low | Cas improbables ; la correction ajoute des gardes | rejeté |
| B12 / E9 | Identifiants S3 éphémères inutilisables en dev ; deux générateurs de secrets | low | Concerne seulement l'API lancée hors Compose | rejeté |
| B13 | Valeurs de démonstration acceptées en `prod` | medium | `vapid_private_key=dev-placeholder-…` et `alert-disabled` passent le contrôle | patch (P10) |
| B14 / E25 | `garage.env` absent ou partiel → clés S3 désaccordées | low | Garder les fichiers `s3_*` tout en régénérant `garage.env` désaccorde l'API et Garage | patch (P11, régénérer les trois ensemble) |
| B15 | Les sondes inondent le journal d'accès | low | Une ligne INFO toutes les 10 s ; correction directe (niveau DEBUG pour les sondes) | patch (P12) |
| B16 | Healthcheck du worker lourd (FastAPI, boto3) | low | Coût réel mais faible ; refactorisation | rejeté |
| B17 / E13 / E14 | Statut faux dans le journal et les métriques sur annulation ou exception après le début de réponse | low | Aucune réponse en flux aujourd'hui | rejeté |
| B18 | Tests fragiles (seuil d'horloge, paramètre inutile) | low | Pas de CI encore ; aucun impact utilisateur | rejeté |
| E18 | Avertissement dev émis avant la configuration des journaux | low | Une ligne en texte brut, seulement en dev | rejeté |
| E19 | `SettingsError` et `OSError` non captés par `load_settings_or_exit` | low | Trace complète au lieu de `startup_refused` ; correction directe | patch (P13) |
| E20 | `MODEL_VERSION=` vide → `""` au lieu de `null` | low | Correction directe | patch (P13) |
| E22 / E23 / E24 | Robustesse de `smoke_readyz.py` | low | Outil manuel ; un échec reste visible | rejeté |
| V1 | Vraies vérifications de `/readyz` jamais testées | medium | Tous les tests remplacent les fonctions de vérification | patch (P14) |
| V2 | Contrat battement écrit / lu non testé | medium | Aucun test n'appelle `write_heartbeat`, `startup`, `shutdown` ni `main` | patch (P14) |
| V3 | `env.py` avec `MigratorSettings` non testé | medium | Revenir à `get_settings()` casserait `migrate` sans faire échouer un test | patch (P14) |
| V4 | Réutilisation de la clé Garage par le générateur non testée | medium | Aucun test n'importe le script | patch (P11) |
| V5 | Message par défaut de `DomainError` non testé | low | Le seul test passe un message explicite | patch (P6) |

## Design Notes

**Tâches planifiées sans `cron_jobs`.** Le battement ne passe pas par `cron_jobs` : la plus petite granularité d'arq est la seconde, mais une tâche planifiée passe par la file et serait retardée si la file est pleine. Une boucle asyncio dans le processus du worker prouve mieux qu'il est vivant.

**Unité de travail en dépendance FastAPI.** `get_uow()` est une dépendance avec `yield`. La validation du commit a donc lieu avant l'envoi de la réponse, et les `after_commit` s'exécutent ensuite.

## Verification

**Commandes :** dans le conteneur uv, dépôt monté sur `/repo`, dossier de travail `/repo/backend`.
- `uv sync --frozen && uv lock --check && uv run ruff check . && uv run ruff format --check . && uv run pytest -q` — attendu : tout passe.
- Sur l'hôte : `docker compose --profile demo up -d --build --wait` (`HTTP_PORT` et `DB_LOCAL_PORT` libres), puis `python backend/scripts/smoke_readyz.py` — attendu : succès.
