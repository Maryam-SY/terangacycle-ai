---
title: 'Story 1.16 — Retirer son consentement au réentraînement'
type: 'feature'
created: '2026-11-26'
status: 'ready-for-dev'
baseline_commit: 'd1ebcca5ccaa748d5bbf264ff8f9dcebd85e585d'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-13-completer-envoyer-et-voir-la-confirmation.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Le choix du réentraînement est fait une fois, sur l'écran de consentement, puis copié sur chaque Signalement. Le Citoyen ne peut pas changer d'avis, et un retrait n'atteindrait pas ses Signalements déjà envoyés (AD-24). Il manque aussi trois briques que les autres stories réutiliseront : l'idempotence des mutations (AD-5), les événements entre modules (AD-21) et la tâche planifiée `retention.sweep` (AD-18).

**Approach:**
- écran Réglages [HORS MAQUETTE], ouvert depuis l'écran 1 : choix actuel, date d'acceptation, interrupteur ;
- `PUT /v1/device/consent` (principal appareil, `Idempotency-Key` exigée) met à jour `devices`. Un retrait émet `TrainingConsentWithdrawn`, et sa réaction passe à faux les Signalements de l'appareil ;
- sans réseau, le choix vaut tout de suite sur le téléphone et l'appel est retenté.

Créés ici : migration `idempotency_records`, `core/idempotency.py`, `core/events.py` (sur `core/jobs.py`, de la story 1.18), la réaction dans `reactions.py` et `retention.sweep`. Les critères d'acceptation de référence sont ceux de la section `### Story 1.16` d'`_bmad-output/planning-artifacts/epics.md`, à respecter intégralement.

## Boundaries & Constraints

**Always:**
- **Migration `0005_idempotency_records` :**
  - elle enchaîne sur `0004` (si la story 1.14 a déjà pris `0005`, prendre le numéro suivant et enchaîner sur sa migration) ;
  - elle crée seulement `idempotency_records`. `response_status` et `response_body` (JSONB) acceptent NULL jusqu'à l'écriture de la réponse. Clé primaire `(principal_key, route_template, key)`, index sur `created_at`. Le downgrade supprime la table.
- **`core.idempotency` :**
  - `require_key` (dépendance) : en-tête `Idempotency-Key` absent ou qui n'est pas un UUID → 400 `idempotency_key_required` ;
  - `execute(principal_key, route_template, key, request_sha256, action)` est `@transactional`. Il insère d'abord (`ON CONFLICT DO NOTHING`, `created_at = core.clock.now()`), puis lance `action` et écrit la réponse avant le commit ;
  - clé déjà présente, même empreinte : la réponse enregistrée est rejouée sans relancer `action`. Autre empreinte : 422 `idempotency_key_reused` ;
  - une erreur annule l'unité, ligne comprise : seules les 2xx restent ;
  - `purge_expired(now)` supprime les lignes plus anciennes que `RETENTION_IDEMPOTENCY_H` (24, nouveau réglage de `Settings`, présent dans `.env.example`).
- **Route `PUT /v1/device/consent`** (module `auth`, route synchrone) :
  - contrôles, dans l'ordre : `principal()` (400 `invalid_device_id`, 401 `invalid_token`), puis `require_key`, puis corps `{"training": bool}` (champs inconnus refusés, 422) ;
  - empreinte : SHA-256 du corps validé et sérialisé ;
  - réponse 200 : `{"training", "consent_at"}` ;
  - déclarée `DEVICE` dans `ROUTE_POLICIES`, et documentée dans l'OpenAPI (`responses=`).
- **`auth.service.set_device_training_consent(device_hash, owner_key, training)`** (`@transactional`) :
  - il crée ou met à jour `devices`, avec `training_consent = training` et `consent_at = core.clock.now()`, même si la valeur ne change pas ;
  - si `training` est faux, il émet `TrainingConsentWithdrawn(event_id, owner_key, withdrawn_at)`, même si l'appareil était déjà à faux : un Signalement envoyé avec `training = false` a pu passer `devices` à faux avant l'arrivée du retrait.
- **Événements :**
  - `core.events.emit(event)` enregistre, sous `after_commit`, la mise en file arq `react` avec `job_id = react:<event_id>` (AD-8) ;
  - la mise en file passe par `core/jobs.py`. La story 1.18 crée ce module et le décrit dans sa spec : utilisable depuis une unité synchrone ou asynchrone, attente d'environ 2 s au plus, échec journalisé `job_enqueue_failed` sans changer la réponse déjà validée. Si la story 1.16 passe avant 1.18, elle crée `core/jobs.py` selon ce même contrat, et 1.18 le réutilise ;
  - en test, `core.jobs` est remplacé par un enregistreur ; la base reste réelle.
- **Réaction (`reactions.py`) :**
  - la tâche worker `react` passe par `asyncio.to_thread` ;
  - `TrainingConsentWithdrawn` → `reports.service.revoke_training_consent(owner_key, received_before=withdrawn_at)` (`@transactional`) : `UPDATE … SET training_consent = false WHERE owner_key = … AND training_consent AND received_at <= …` ;
  - rejouer la réaction ne change rien ; un Signalement créé après un nouvel accord n'est jamais touché.
- **`retention.sweep` :**
  - `cron_jobs` arq, quotidien, nommé `retention.sweep`, `unique` ;
  - il appelle `core.idempotency.purge_expired(core.clock.now())` dans une unité de travail synchrone. Les stories suivantes y ajoutent leurs purges.
- **Codes :** `idempotency_key_required` et `idempotency_key_reused` dans `codes.py`, `DEFAULT_MESSAGES`, `fr.json`, `wo.json` et la liste de `test_errors.py`.
- **Architecture :** un test exige `require_key` sur chaque route `POST`, `PUT`, `PATCH` ou `DELETE` sous `/v1`. Seules exemptions : `/v1/auth/*` et `POST /v1/reports`.
- **Côté PWA, choix local :**
  - `consent.ts` : `setTrainingConsent(training)` change seulement `training` du consentement gardé. `acceptedAt` (date affichée) et `version` restent ;
  - `acceptConsent()` ajoute aussi un changement à la file quand il modifie un `training` déjà gardé (nouvelle version du texte) ;
  - le prochain Signalement lit ce choix (envoi de la story 1.13, `consent` lu au moment de l'envoi).
- **Côté PWA, file d'envoi (`offline/consentSync.ts`, Dexie `meta.consentSync`) :**
  - chaque changement porte sa clé `crypto.randomUUID()`, gardée jusqu'à une réponse 2xx ;
  - la file garde au plus deux entrées, dans l'ordre : `[false]`, `[true]` ou `[false, true]`. Un retrait en attente n'est jamais effacé par un nouvel accord, pour que les Signalements passés soient bien retirés ;
  - elle est vidée à l'ouverture de l'application (`main.tsx`), à l'événement `online` et juste après chaque changement, une seule exécution à la fois ;
  - toute réponse non 2xx laisse l'entrée pour le prochain essai ;
  - l'appel passe par le client généré (`api/device.ts`, en-tête `Idempotency-Key`).
- **Écran Réglages (`/reglages`) :**
  - lien « Réglages » sur l'écran 1 : pictogramme et libellé, cible ≥ 44 px ;
  - l'écran montre le choix actuel en texte, la date d'acceptation (`Intl.DateTimeFormat('fr')`) et un interrupteur (`role="switch"`, libellé accessible). Il n'affiche jamais l'Identifiant d'appareil ;
  - sans consentement gardé : une phrase dit que le choix sera demandé avant le premier signalement, sans interrupteur ;
  - envoi en échec : « Votre choix sera transmis dès le retour du réseau » (`role="status"`). Envoi réussi : confirmation courte.
- **i18n :** textes sous `settings.*` et `home.settings`, jamais sous `consent.*` : l'empreinte `CONSENT_TEXT_SHA256` ne doit pas changer.
- **Client généré :** `openapi.json` et `schema.d.ts` régénérés (dérive contrôlée par la CI de la story 1.13).

**Never:**
- pas de `PUT /v1/me/consent` (Epic 2), pas d'`export_corrections()` ;
- pas de table d'événements côté serveur ; pas d'outbox générale (Epic 6) ;
- pas de revérification d'un nouvel accord sur les Signalements passés : ils restent à faux ;
- aucun mock de base dans les tests d'intégration.

## I/O & Edge-Case Matrix

| Scénario | Entrée / état | Attendu |
|---|---|---|
| Retrait | A (3 Signalements `true`), B (1) ; A : `PUT {"training": false}`, clé K | 200 ; `devices` A à faux, `consent_at = now` ; événement mis en file `react:<id>` ; après réaction : 3 × faux pour A, B vrai |
| Réaction rejouée | Même événement deux fois | Aucun changement au second passage |
| Sans clé | Pas d'`Idempotency-Key`, ou clé non UUID | 400 `idempotency_key_required` ; rien d'écrit |
| Sans appareil | `X-Device-Id` absent ou invalide | 400 `invalid_device_id` |
| Même clé, même corps | K, `{"training": false}` deux fois | Même réponse ; aucun nouvel effet, aucun second événement |
| Même clé, autre corps | K, `{"training": true}` | 422 `idempotency_key_reused` |
| Échec | Corps invalide (422) avec une clé neuve | Aucune ligne `idempotency_records` |
| Après retrait | Nouveau Signalement depuis la PWA | `consent.training = false` envoyé et enregistré |
| Nouvel accord | `PUT {"training": true}` après retrait | Futurs Signalements `true` ; passés restent faux ; aucun événement |
| Accord puis Signalement avant la réaction | Retrait à t0, accord, Signalement à t1 > t0, réaction | Le Signalement de t1 reste vrai |
| Sans réseau | Interrupteur changé hors ligne | Dexie à jour tout de suite ; message « Votre choix sera transmis… » ; renvoi avec la même clé à l'`online` et à l'ouverture, jusqu'à 2xx |
| Retrait puis accord hors ligne | false puis true | File `[false, true]`, envoyés dans cet ordre |
| Purge | Horloge simulée : lignes de 24 h 01 et de 23 h 59 | La première est supprimée, la seconde gardée |
| Première visite | Aucun consentement gardé | Réglages sans interrupteur, phrase explicative |

</frozen-after-approval>

## Code Map

- `backend/migrations/versions/0004_reports_client_uuid_unique.py` : `revision = "0004_reports_client_uuid_unique"`, modèle de migration. Les droits de `teranga_app` sur une nouvelle table viennent des `DEFAULT PRIVILEGES` (`tests/integration/test_db_roles.py`).
- `backend/app/core/db.py` : `transactional`, `unit_of_work`, `after_commit`, `current_session`. Règle : une route ou tâche `async` n'appelle jamais la base directement.
- `backend/app/core/security.py` : `principal()`, `Principal.owner_key`, `Principal.device_hash`.
- `backend/app/core/access.py` : `ROUTE_POLICIES`, `DEVICE`. `tests/architecture/test_route_policies.py` vérifie la table ; son parcours des routes (`iter_route_contexts`) sert de modèle au test d'`Idempotency-Key`.
- `backend/app/modules/auth/repository.py` : `_UPSERT_DEVICE` (ne change `consent_at` que si le choix change ; ne pas le modifier, `touch_device` en dépend). Ajouter une requête propre au PUT.
- `backend/app/modules/reports/service.py` et `repository.py` : ajouter `revoke_training_consent` ; ne pas toucher `create_report`.
- `backend/app/reactions.py` : racine de composition, vide ; import-linter l'autorise à importer `auth` et `reports` (aucune flèche nouvelle).
- `backend/app/worker.py` : `WorkerSettings.functions`, `cron_jobs` (vide), `startup`. `tests/unit/test_worker.py::test_worker_settings_declare_cron_jobs` attend `[]` : à mettre à jour.
- `backend/app/main.py` : `create_app` (router `auth`) ; le `lifespan` ne change que si `core/jobs.py` l'exige.
- `backend/app/core/jobs.py` : créé par la story 1.18 (voir `spec-1-18-…`) ; à réutiliser, ou à créer avec le même contrat si 1.16 passe la première.
- `backend/app/core/config.py` (`Settings`, `valkey_url`) et `tests/unit/test_env_example.py` (alignement de `.env.example`).
- `backend/app/core/errors/codes.py` et `tests/unit/test_errors.py` (liste codée en dur) ; `tests/unit/test_error_messages.py`.
- `infra/Caddyfile` : `@api path /v1/*` relaie déjà le PUT ; aucune modification.
- `web/src/api/client.ts` (story 1.13) : instance unique, `X-Device-Id`, `ApiError`/`NetworkError`.
- `web/src/features/consent/consent.ts` : `StoredConsent`, `getConsent`, `acceptConsent` ; `ConsentPage.tsx` inchangé.
- `web/src/offline/db.ts` : `MetaKey` (ajouter `consentSync`).
- `web/src/features/home/HomePage.tsx`, `web/src/ui/icons.tsx`, `web/src/main.tsx` (`ensureDeviceId` au démarrage, modèle du lancement de la file).

**Fichiers créés ou modifiés (liste complète) :**
- backend, socle : `backend/migrations/versions/0005_idempotency_records.py` (nouveau), `backend/app/core/idempotency.py` (nouveau), `backend/app/core/events.py` (nouveau), `backend/app/core/jobs.py` (nouveau seulement si la story 1.18 n'est pas encore passée), `backend/app/core/errors/codes.py`, `backend/app/core/config.py`, `backend/app/core/access.py`, `.env.example` ;
- backend, modules : `backend/app/modules/auth/router.py` (nouveau), `backend/app/modules/auth/schemas.py` (nouveau), `backend/app/modules/auth/service.py`, `backend/app/modules/auth/repository.py`, `backend/app/modules/reports/service.py`, `backend/app/modules/reports/repository.py` ;
- backend, composition : `backend/app/reactions.py`, `backend/app/worker.py`, `backend/app/main.py` ;
- backend, tests : `backend/tests/integration/test_device_consent_api.py` (nouveau), `backend/tests/integration/test_idempotency.py` (nouveau), `backend/tests/integration/test_retention_sweep.py` (nouveau), `backend/tests/architecture/test_idempotency_routes.py` (nouveau), `backend/tests/unit/test_worker.py`, `backend/tests/unit/test_errors.py` ;
- docs : `README.md` ;
- web, API : `web/src/api/openapi.json` (régénéré), `web/src/api/schema.d.ts` (régénéré), `web/src/api/device.ts` (nouveau), `web/src/api/device.test.ts` (nouveau) ;
- web, hors-ligne : `web/src/offline/db.ts`, `web/src/offline/consentSync.ts` (nouveau), `web/src/offline/consentSync.test.ts` (nouveau) ;
- web, consentement et réglages : `web/src/features/consent/consent.ts`, `web/src/features/consent/consent.test.ts`, `web/src/features/settings/SettingsPage.tsx` (nouveau) ;
- web, coquille : `web/src/features/home/HomePage.tsx`, `web/src/main.tsx`, `web/src/paths.ts`, `web/src/routes.tsx`, `web/src/App.test.tsx`, `web/src/ui/icons.tsx` ;
- web, i18n : `web/src/i18n/fr.json`, `web/src/i18n/wo.json` ;
- web, e2e : `web/e2e/settings.spec.ts` (nouveau).

## Tasks & Acceptance

**Execution:**
- [ ] Migration `0005`, `core/idempotency.py`, codes d'erreur, réglage `RETENTION_IDEMPOTENCY_H`.
- [ ] `core/events.py` (sur `core/jobs.py`), `main.py` (router `auth`), `worker.py` (tâche `react`, `retention.sweep`), `reactions.py`.
- [ ] `modules/auth` (router, schemas, service, repository), `core/access.py` ; `modules/reports` (`revoke_training_consent`).
- [ ] Web : `api/device.ts`, `offline/consentSync.ts`, `consent.ts`, `SettingsPage`, lien de l'accueil, lancement de la file dans `main.tsx`, routes, i18n ; régénérer `openapi.json` et `schema.d.ts`.
- [ ] **Tests :**
  - intégration (base réelle, `core.jobs` enregistreur) : chaque ligne serveur de la matrice ; clés envoyées en parallèle (un seul effet) ; purge à horloge simulée ;
  - architecture : `require_key` sur les mutations, exemptions closes ;
  - unitaires : réglages du worker (`retention.sweep` quotidien, `react` déclarée) ;
  - Vitest : file (`[false, true]`, même clé jusqu'à 2xx, une seule exécution), `setTrainingConsent`, `acceptConsent` ;
  - Playwright `settings.spec.ts` (PUT et POST interceptés, 390×844, axe) : lien de l'accueil, interrupteur, hors ligne puis `online`, rechargement, Signalement suivant à `training = false`.
- [ ] `README.md` : route, `Idempotency-Key`, réponses 400 et 422, `retention.sweep`.

**Acceptance Criteria:**
- Tous les critères d'acceptation de la story 1.16 d'`epics.md` sont couverts par au moins un test qui tourne en CI.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run lint-imports && REQUIRE_INTEGRATION=1 uv run pytest --cov` (backend, pile réelle) — expected: vert.
- `uv run python scripts/export_openapi.py && git diff --exit-code ../web/src/api/openapi.json` (backend) — expected: aucune différence.
- `npm run api:types && git diff --exit-code src/api/schema.d.ts && npm run lint && npm test && npm run build && npm run size && npm run test:e2e` (web) — expected: vert.
