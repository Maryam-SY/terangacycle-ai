---
title: 'Story 1.18 — Produire la miniature d''une photo de Signalement'
type: 'feature'
created: '2026-11-26'
status: 'ready-for-dev'
baseline_commit: 'd1ebcca5ccaa748d5bbf264ff8f9dcebd85e585d'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-10-stocker-une-photo-sans-metadonnees-dans-le-bucket-prive.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-11-recevoir-un-signalement-anonyme-et-attribuer-son-numero-de-suivi.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Chaque photo de Signalement est stockée en entier (jusqu'à 1 Mo). Les listes de la console et des Collecteurs chargeraient donc des photos lourdes sur un réseau faible. La colonne `report_photos.thumb_key` existe depuis la story 1.11, mais rien ne la remplit, et aucune tâche métier ne passe encore par le worker arq.

**Approach:** après le commit de la création, `reports.service` met en file la tâche arq `thumb:<photo_id>` (AD-8, AD-17). Le worker relit la photo, produit une miniature JPEG d'au plus 30 Ko sous `report_thumb/<aaaa>/<mm>/<uuid>.jpg` (AD-13) et enregistre sa clé. Les critères d'acceptation de référence sont ceux de la section `### Story 1.18` d'`_bmad-output/planning-artifacts/epics.md`, à respecter intégralement.

La story crée aussi :
- `core/jobs.py`, la mise en file arq après commit (brique de l'épine réutilisée par 1.16 et les epics suivants) ;
- le premier `PhotoKind` dérivé, `report_thumb`.

## Boundaries & Constraints

**Always:**
- **Mise en file :**
  - seulement par `core.jobs`, enregistrée par `after_commit` dans l'unité de la création (`create_report`) ;
  - jamais après une annulation ni pour un renvoi idempotent (200 : rien n'est écrit) ;
  - `job_id = thumb:<photo_id>`, `photo_id` = `report_photos.id` (l'`<uuid>` de la clé, AD-13).
- **`core.jobs` :**
  - utilisable depuis une unité synchrone (route `def` dans le pool de threads, script) et depuis une unité asynchrone (comme `core.storage._register`) ;
  - Valkey injoignable : la mise en file attend au plus environ 2 s (pas de boucle de reconnexion arq), puis échoue. L'échec est journalisé (`job_enqueue_failed`, `job_id` seul), et ni la réponse 201 ni le commit déjà fait ne changent ;
  - piste conseillée : depuis un thread de travail anyio, `anyio.from_thread.run` vers un pool arq de la boucle de l'application ; sinon, un pool éphémère sous `asyncio.run`.
- **Clé de la miniature :**
  - déterministe, dérivée de la clé de la photo par `core.storage.thumb_key_for(object_key)` : `report/2026/11/<uuid>.jpg` → `report_thumb/2026/11/<uuid>.jpg` (même année, même mois, même uuid) ;
  - rejouer la tâche réécrit donc le même objet, et ne crée jamais de second objet.
- **Miniature :**
  - plus grand côté de 320 px au plus, sans agrandir une image plus petite ;
  - JPEG sans aucune métadonnée, qualité 75 puis 65, 55, 45, 35 ;
  - si 35 ne suffit pas, côtés réduits de 25 % jusqu'à tenir ;
  - plafond `MAX_THUMB_BYTES = 30 720` octets (30 Kio), garanti par construction ;
  - type `image/jpeg`, aucun ACL ; produite depuis l'objet stocké (déjà nettoyé), jamais depuis les octets reçus.
- **Tâche :**
  - `worker.thumb(ctx, photo_id)` délègue à `reports.service.make_thumbnail(photo_id)` (`@transactional`, synchrone) dans le pool de threads, sans logique propre (AD-8) ;
  - le service verrouille la ligne (`SELECT … FOR UPDATE`) et relit l'état :
    - ligne absente (Signalement retiré) : la tâche s'arrête ;
    - `thumb_key` déjà renseignée : la tâche s'arrête ;
    - sinon : miniature stockée, puis `UPDATE … SET thumb_key = :k WHERE id = :id AND thumb_key IS NULL`.
- **Échecs :**
  - stockage indisponible : `arq.Retry` avec un délai croissant, au plus 5 essais (`max_tries`) ;
  - objet source absent ou illisible : journal `thumb_source_missing` et arrêt, sans nouvel essai.
- **Confidentialité :** les journaux portent seulement `photo_id` et les clés, jamais d'octets ni de métadonnées.
- **Architecture :**
  - seul `core.storage` parle S3 (lecture de l'objet comprise) ;
  - `worker.py` est la racine de composition qui appelle `reports.service` ;
  - aucune flèche nouvelle entre modules.

**Never:**
- pas de lecture de la miniature par URL signée ni de route qui l'expose (stories de la console et des Missions) ;
- pas de balayage des photos sans miniature ni des orphelins (AD-18, plus tard) ;
- pas de miniature pour les Preuves ;
- pas de migration : `thumb_key` et `uq_report_photos_thumb_key` existent (0003) ;
- aucun mock de Garage, de Valkey ni de la base dans les tests d'intégration.

## I/O & Edge-Case Matrix

| Scénario | Entrée / état | Attendu |
|---|---|---|
| Nominal | Création 201 puis commit | Une tâche `thumb:<photo_id>` en file ; après exécution, objet `report_thumb/AAAA/MM/<uuid>.jpg` ≤ 30 720 octets, JPEG sans EXIF ; `thumb_key` renseignée |
| 10 photos de 1 Mo | Photos à forte entropie, stockées par `ingest_photo` | 10 miniatures, chacune ≤ 30 720 octets, plus grand côté ≤ 320 px |
| Petite photo | 64 × 48 | Miniature 64 × 48 (jamais agrandie) |
| Rejeu | Tâche exécutée deux fois, ou deux exécutions concurrentes | Un seul objet sous le préfixe ; `thumb_key` inchangée |
| Annulation | Exception après `ingest_photo`, avant le commit | Aucune tâche en file (ni `arq:job:thumb:<id>`, ni résultat) ; ni ligne ni objet |
| Renvoi idempotent | Même auteur, même `client_uuid` (200) | Aucune nouvelle tâche |
| Ligne retirée | Signalement supprimé avant l'exécution | Arrêt sans écriture ni objet |
| Garage indisponible | Échec S3 pendant la tâche | `Retry`, 5 essais au plus, puis échec journalisé |
| Valkey indisponible | Mise en file impossible | 201 inchangé, `job_enqueue_failed` journalisé, durée de la requête bornée |

</frozen-after-approval>

## Code Map

- `backend/app/core/db.py` : `after_commit`, `_require_uow`, `UnitOfWork.is_async`. À réutiliser, ne pas modifier.
- `backend/app/core/storage.py` : `_OBJECT_KEY` (dérivé de `PhotoKind`, donc `purge()` acceptera `report_thumb/...` sans autre changement), `_put`, `_delete`, `_client_and_bucket`, `_register`, `reencode`/`_flatten` (modèle du ré-encodage sans métadonnée).
  - À ajouter : `thumb_key_for()`, une lecture `_get()`, `make_thumbnail(object_key) -> str` et `MAX_THUMB_BYTES`.
  - `ingest_photo` doit refuser `PhotoKind.REPORT_THUMB` : une miniature n'est jamais un envoi.
- `backend/app/core/enums.py` : `PhotoKind`, à compléter par `REPORT_THUMB = "report_thumb"` (AD-13).
- `backend/app/core/health.py` : `_redis(settings)` montre la connexion Valkey (délais courts).
- `backend/app/core/config.py` : `valkey_url`. Aucun réglage nouveau.
- `backend/app/modules/reports/service.py` : dans `create_report`, après `insert_photo`, enregistrer la mise en file. Ajouter `make_thumbnail(photo_id)` (`@transactional` ; le test d'architecture exige le décorateur sur toute fonction publique). Ne pas toucher à `_settle_parallel_sends` ni à l'ordre des contrôles.
- `backend/app/modules/reports/repository.py` : `lock_photo(photo_id)` (`object_key`, `thumb_key`, `FOR UPDATE`) et `set_thumb_key(photo_id, key)` (conditionnel).
- `backend/app/worker.py` : `WorkerSettings.functions` (aujourd'hui `[noop]`). Ajouter `func(thumb, name="thumb", max_tries=5)`. `cron_jobs` reste `[]` (`test_worker.py` le vérifie).
- `backend/pyproject.toml` : contrats inchangés (`app.worker` est déjà importateur autorisé ; `s3_access` couvre la lecture).
- `backend/tests/integration/test_reports_api.py` : le nettoyage de fin de test supprime aussi le préfixe `report_thumb/2032/05/`, car le worker de la pile Compose traite maintenant les tâches des Signalements créés par les tests.
- `infra/docker-compose.yml` : Valkey n'est pas publié sur l'hôte. Le publier sur `127.0.0.1:${VALKEY_LOCAL_PORT:-6379}`, comme la base et Garage, pour que les tests lisent la file.
- `.github/workflows/ci.yml` : ajouter `TEST_VALKEY_URL` à l'étape « URL de test ». `.env.example` : `VALKEY_LOCAL_PORT=6379`. `README.md` : variables des tests d'intégration.
- **Migration :** aucune (la tête reste `0004_reports_client_uuid_unique`).
- **Fichiers touchés (liste complète) :**
  - à créer : `backend/app/core/jobs.py`, `backend/tests/unit/test_jobs.py`, `backend/tests/unit/test_thumbnail.py`, `backend/tests/integration/test_thumbnails.py` ;
  - à modifier : `backend/app/core/enums.py`, `backend/app/core/storage.py`, `backend/app/modules/reports/service.py`, `backend/app/modules/reports/repository.py`, `backend/app/worker.py`, `backend/tests/unit/test_storage.py`, `backend/tests/unit/test_worker.py`, `backend/tests/integration/test_reports_api.py`, `infra/docker-compose.yml`, `.env.example`, `.github/workflows/ci.yml`, `README.md`.

## Tasks & Acceptance

**Execution:**
- [ ] `backend/app/core/enums.py`, `backend/app/core/storage.py` : `REPORT_THUMB`, `thumb_key_for`, `_get`, `make_thumbnail`, plafond garanti ; refus de `REPORT_THUMB` dans `ingest_photo`.
- [ ] `backend/app/core/jobs.py` : `enqueue_after_commit(function, *args, job_id)`, variantes synchrone et asynchrone, délai borné, échec journalisé.
- [ ] `backend/app/modules/reports/repository.py`, `service.py` : mise en file dans `create_report` ; `make_thumbnail` idempotent sous verrou.
- [ ] `backend/app/worker.py` : tâche `thumb`, `Retry` sur stockage indisponible, `max_tries=5`.
- [ ] `infra/docker-compose.yml`, `.env.example`, `.github/workflows/ci.yml`, `README.md` : Valkey publié sur 127.0.0.1, `TEST_VALKEY_URL`.
- [ ] **Tests :**
  - unitaires : `thumb_key_for` ; plafond sur 10 images de 1 Mo à forte entropie ; pas d'agrandissement ; aucune métadonnée ; `core.jobs` (pas de mise en file après une annulation, délai borné quand Valkey est injoignable) ; liste des fonctions du worker ;
  - intégration sur PostgreSQL, Garage et Valkey réels : chaque ligne de la matrice. La file est relue dans Valkey ; la clé de tâche est acceptée dans n'importe quel état (`arq:job:`, `arq:in-progress:`, `arq:result:`), car le worker de la pile peut l'avoir déjà prise. Le nombre d'objets du préfixe `report_thumb/` est compté avant et après le rejeu.

**Acceptance Criteria:**
- Tous les critères d'acceptation de la story 1.18 d'`epics.md` sont couverts par au moins un test qui tourne en CI.
- Étant donné la pile Compose démarrée, quand un Signalement est créé, alors sa `thumb_key` est renseignée par le worker de la pile en moins de 30 s (test d'intégration avec attente bornée).

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run lint-imports && REQUIRE_INTEGRATION=1 uv run pytest --cov` (backend, pile Compose réelle ; base, Garage et Valkey sur 127.0.0.1) — expected: vert.
- `python -I scripts/ci/check_pinning.py && python -I scripts/ci/check_repo_hygiene.py` — expected: OK.
