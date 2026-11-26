---
title: 'Story 1.14 — Repérer les Doublons probables à la réception'
type: 'feature'
created: '2026-11-26'
status: 'ready-for-dev'
baseline_commit: 'd1ebcca5ccaa748d5bbf264ff8f9dcebd85e585d'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-12-renvoyer-un-signalement-sans-doublon-ni-fuite.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Plusieurs Citoyens signalent souvent le même dépôt, ou une même photo est réutilisée. Aujourd'hui, chaque Signalement arrive seul dans la File de modération : la commune risque d'envoyer deux fois un Collecteur au même endroit, et une photo recyclée (signal de fraude) passe inaperçue.

**Approach:** à la création (`reports.service.create_report`), le serveur calcule une fois la marque de Doublon probable et la stocke dans `reports.duplicate_of_report_id` :
- photo strictement identique (même `sha256` des octets reçus), recherche **globale** : origine = le plus ancien Signalement portant cette photo ;
- sinon, Signalement non terminal de la **même Organisation** reçu depuis moins de `DUPLICATE_WINDOW_H` à au plus `DUPLICATE_RADIUS_M` : origine = le plus proche.

Le Signalement est toujours créé normalement (201) et la réponse ne change pas. `reports.service.photo_seen(sha256)` est exposé aux autres modules. Les critères d'acceptation de référence sont ceux de la section `### Story 1.14` d'`_bmad-output/planning-artifacts/epics.md`, amendement v2.0 compris.

## Boundaries & Constraints

**Always:**
- **Migration `0005_reports_duplicate_of`** (révise `0004_reports_client_uuid_unique`, tête actuelle) : ajoute seulement `reports.duplicate_of_report_id uuid NULL`, sa clé étrangère vers `reports (id)` `ON DELETE SET NULL` (même module, AD-21 ne vise que les clés entre modules ; une suppression d'origine par 1.17 ou 2.9 n'est pas bloquée), `CHECK (duplicate_of_report_id <> id)` et l'index `ix_reports_duplicate_of_report_id` (partiel, `WHERE duplicate_of_report_id IS NOT NULL`). L'index `ix_report_photos_sha256` et l'index GiST `ix_reports_geog`, exigés par les critères, existent déjà (migration `0003`, story 1.11) : ni recréés ni supprimés, leur présence est vérifiée par un test de schéma. Downgrade : retire la colonne et ses objets.
- **Réglages :** `duplicate_radius_m` (entier, défaut 50, 1 à 1000) et `duplicate_window_h` (entier, défaut 72, 1 à 720) dans `Settings`, `DUPLICATE_RADIUS_M=50` et `DUPLICATE_WINDOW_H=72` dans `.env.example`, lus depuis les réglages de l'application (`settings` passé au service), jamais `get_settings()`.
- **Ordre dans `create_report` :** inchangé jusqu'au stockage de la photo (verrou, renvoi idempotent, consentement, Zone, `ingest_photo`) ; la marque est calculée après `responsible_org()` et avant l'insertion, dans la même unité de travail. Un renvoi idempotent (200) n'est jamais marqué ni recalculé.
- **Photo identique :** `report_photos.sha256` = `StoredPhoto.sha256` (octets reçus, AD-13) ; tous Statuts, toutes Organisations, toute ancienneté ; ordre `received_at`, puis `id`. Prioritaire sur la proximité.
- **Proximité :** `ST_DWithin(geog, point::geography, radius)` (limite incluse), même `organization_id`, Statut hors `rejected` et `collected` (`ReportStatus`), `received_at > now − window` (strict) avec `now` = le `received_at` lu une fois par le service (`core.clock`) ; ordre `ST_Distance`, puis `received_at`, puis `id`.
- **Confidentialité :** réponse 201 strictement identique (`ReportCreated` inchangé) ; journaux inchangés (aucun identifiant de l'origine).
- **`photo_seen(sha256) -> bool`** dans `reports.service`, `@transactional` (rejoint l'unité de l'appelant), via le repository ; global, sans `scope`.
- **Concurrence acceptée :** deux Signalements proches reçus au même instant peuvent ne pas se voir (lecture validée) ; aucun verrou ajouté.

**Never:**
- aucun refus ni changement de Statut pour un Doublon probable ; aucun recalcul à la lecture ;
- aucun champ nouveau dans la réponse ni dans l'OpenAPI ;
- pas de limite de débit (1.15), pas d'affichage dans la File de modération (Epic 4) ;
- aucun mock de base ni de Garage dans les tests d'intégration.

## I/O & Edge-Case Matrix

| Scénario | Entrée / État | Attendu |
|---|---|---|
| Photo identique | A existe ; B, autre appareil, mêmes octets, ailleurs dans la Zone | 201, `B.duplicate_of = A` |
| Photo, plusieurs origines | A puis A' (déjà doublon de A) ; C, même photo | `C.duplicate_of = A` (le plus ancien) |
| Photo, autre Organisation | A dans la commune X ; B dans la commune Y, même photo | marqué (recherche globale) |
| Photo, origine terminale ou ancienne | A `rejected`, reçu il y a 30 jours | marqué |
| Proche | A non terminal, même Organisation, il y a 71 h 59 ; B à 49 m | `B.duplicate_of = A` |
| Bornes | 51 m / reçu il y a 72 h 01 / A `rejected` ou `collected` | non marqué |
| Autre Organisation | A à 10 m mais autre `organization_id` | non marqué |
| Plusieurs proches | A à 40 m, A' à 20 m | `duplicate_of = A'` |
| Photo et proximité | A même photo à 2 km ; A' à 10 m | `duplicate_of = A` |
| Renvoi | même appareil, même `client_uuid` | 200 avec l'existant ; aucune ligne, marque de l'existant inchangée |
| Réponse | B marqué / non marqué | mêmes clés et types, octet pour octet hors valeurs |
| `photo_seen` | empreinte connue / inconnue | `True` / `False` |

</frozen-after-approval>

## Code Map

- `backend/app/modules/reports/service.py` -- `create_report` (verrou `lock_client_uuid`, `_existing_outcome`, `_settle_parallel_sends`, `received_at` lu une fois) : insérer le calcul de la marque entre `responsible_org()` et `insert_report` ; ajouter `photo_seen`. Ne pas toucher à l'ordre des contrôles ni au chemin de renvoi.
- `backend/app/modules/reports/repository.py` -- `NewReport` (+ `duplicate_of_report_id`), `_INSERT_REPORT` ; ajouter `find_photo_origin(sha256)`, `find_nearby_origin(organization_id, lat, lng, radius_m, since)`, `photo_exists(sha256)` (SQL `text()` comme l'existant, `ST_MakePoint(:lng, :lat)` comme `_INSERT_REPORT`).
- `backend/app/core/config.py` -- `Settings` : deux champs, modèle `report_accuracy_flag_m`.
- `backend/app/core/enums.py` -- `ReportStatus` (statuts terminaux) : lecture seule, rien à ajouter.
- `backend/migrations/versions/0004_reports_client_uuid_unique.py` -- modèle de migration (SQL brut, downgrade).
- `backend/tests/integration/test_reports_api.py` -- `Stack`, `FIXED_NOW`, `cleanup` (supprime par `owner_key` : les doublons d'un test partent avec lui) ; `Stack.organization()` pour deux communes.
- `backend/tests/reports.py` -- `sample_photo()` renvoie toujours les mêmes octets : tous les Signalements des tests existants deviennent doublons entre eux (sans effet sur leurs assertions) ; ajouter un générateur de photo distincte pour les tests de cette story.
- `backend/tests/integration/test_reports_schema.py` -- `_schema_objects`, `_columns`, `test_migration_0004_adds_only_the_constraint` : modèle du test « 0005 n'ajoute que ceci ».

**Fichiers créés ou modifiés (exhaustif) :**
- créé : `backend/migrations/versions/0005_reports_duplicate_of.py` ;
- modifiés : `backend/app/modules/reports/service.py`, `backend/app/modules/reports/repository.py`, `backend/app/core/config.py`, `.env.example`, `backend/tests/conftest.py` (`_SETTINGS_ENV_VARS`), `backend/tests/unit/test_config.py`, `backend/tests/reports.py`, `backend/tests/integration/test_reports_api.py`, `backend/tests/integration/test_reports_schema.py`, `README.md` (Doublon probable, réglages).
- **Migration :** oui, `0005_reports_duplicate_of`, `down_revision = "0004_reports_client_uuid_unique"`.

## Tasks & Acceptance

**Execution:**
- [ ] `backend/migrations/versions/0005_reports_duplicate_of.py` -- colonne, clé étrangère, `CHECK`, index partiel ; downgrade -- schéma de la marque.
- [ ] `backend/app/core/config.py`, `.env.example`, `backend/tests/conftest.py` -- deux réglages nommés -- AD-14.
- [ ] `backend/app/modules/reports/repository.py` -- trois requêtes et le champ d'insertion -- seul accès aux tables.
- [ ] `backend/app/modules/reports/service.py` -- calcul de la marque, `photo_seen` -- règle AD-19.
- [ ] **Tests :**
  - intégration : chaque ligne de la matrice, avec relecture de `duplicate_of_report_id` ; bornes par horloge simulée (`clock.now`) et points à 49 m et 51 m calculés depuis `PLATEAU` ; deux Organisations communes ; `photo_seen` appelé dans une unité ouverte par le test ;
  - schéma : colonne nullable, clé étrangère `ON DELETE SET NULL`, index partiel, `ix_report_photos_sha256` et `ix_reports_geog` (gist) présents ; 0005 n'ajoute que ses objets et son downgrade les retire ;
  - unitaire (`tests/unit/test_config.py`) : défauts 50 et 72, bornes refusées.
- [ ] `README.md` -- Doublon probable et réglages.

**Acceptance Criteria:**
- Tous les critères d'acceptation de la story 1.14 d'`epics.md`, amendement v2.0 compris, sont couverts par au moins un test qui tourne en CI.
- Given les tests existants des stories 1.11 et 1.12, when la story est livrée, then ils passent sans modification de leurs assertions.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run lint-imports && REQUIRE_INTEGRATION=1 uv run pytest --cov` (backend, pile réelle migrée jusqu'à `0005`) -- expected: vert, couverture ≥ 60 %.
- `uv run alembic upgrade head && uv run alembic downgrade 0004_reports_client_uuid_unique && uv run alembic upgrade head` (rôle `teranga_migrator`) -- expected: sans erreur.
