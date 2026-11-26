---
title: 'Story 1.12 — Renvoyer un Signalement sans doublon ni fuite'
type: 'feature'
created: '2026-11-25'
status: 'done'
baseline_commit: '61eb579624d12a28591e8c786850bd6a4001e93e'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-11-recevoir-un-signalement-anonyme-et-attribuer-son-numero-de-suivi.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Après une coupure réseau, le téléphone ne sait pas si son envoi est arrivé et renvoie le Signalement. Aujourd'hui, chaque renvoi crée un nouveau Signalement : la commune reçoit des doublons et le compteur de Numéros de suivi s'emballe. Un autre appareil qui présenterait le même Identifiant client ne doit rien apprendre du Signalement d'origine.

**Approach:** l'Identifiant client (`meta.client_uuid`) rend `POST /v1/reports` idempotent par auteur :
- même auteur et même Identifiant client : 200 avec le Signalement existant, sans rien écrire ni modifier ;
- autre auteur : 409 `client_uuid_conflict`, sans aucune donnée ;
- l'unicité est garantie par la base ; les envois parallèles se résolvent sur cette contrainte.

Les critères d'acceptation de référence sont ceux de la section `### Story 1.12` d'`_bmad-output/planning-artifacts/epics.md`.

## Boundaries & Constraints

**Always:**
- **Migration `0004` :** ajoute seulement la contrainte d'unicité sur `(owner_key, client_uuid)`. Ses colonnes sont déclarées dans l'ordre `(client_uuid, owner_key)`, pour que la recherche par seul Identifiant client (cas du conflit) utilise son index. L'ensemble des colonnes est celui des critères d'acceptation.
- **Ordre de traitement :**
  1. principal (story 1.11) ;
  2. lecture et validation de `meta` ;
  3. recherche par `client_uuid` : même `owner_key` → 200 avec l'existant, sans lire ni stocker la photo et sans incrémenter le compteur ; autre `owner_key` → 409 ;
  4. sinon, le parcours de création de la story 1.11, inchangé.
- **Course en parallèle :**
  - l'insertion qui viole la contrainte annule toute l'unité de travail : pas de ligne, compteur inchangé, photo supprimée par `after_rollback` ;
  - le service relit alors l'existant dans une nouvelle unité de travail, et répond 200 (même auteur) ou 409 (autre auteur) ;
  - seule la violation de cette contrainte précise est traitée ainsi (nom de contrainte vérifié) ; toute autre erreur reste une erreur.
- **Réponse du renvoi :** 200, avec exactement les champs du 201 (`id`, `tracking_number`, `status` actuel, `received_at`, `is_demo`) et les valeurs enregistrées à la première réception. Le contenu renvoyé n'est jamais comparé ni appliqué.
- **409 `client_uuid_conflict` :** l'enveloppe d'erreur seule, rien du Signalement d'un autre auteur. Message `errors.client_uuid_conflict` en `fr.json` et `wo.json`, plus `DEFAULT_MESSAGES`.
- **Service :** il prend un `Principal` générique (`kind` : `device` ou `user`, `owner_key`). Un Principal `user` construit dans un test suit les mêmes règles, la route ne produisant encore que des Principaux `device`.
- **Journaux :** un renvoi idempotent porte seulement `id`, `tracking_number` et `replayed=true` ; un conflit, aucun identifiant du Signalement d'origine.
- **Documentation :** README et OpenAPI documentent le 200 et le 409 (`responses=`).

**Never:**
- pas de clé `Idempotency-Key` pour cette route (exemptée par l'architecture) ;
- pas de détection de doublon probable (story 1.14) ni de limite de débit (story 1.15) ;
- aucune mise à jour d'un Signalement existant par un renvoi ;
- aucun mock de base ni de Garage dans les tests d'intégration.

## I/O & Edge-Case Matrix

| Scénario | Entrée | Attendu |
|---|---|---|
| Premier envoi | Appareil A, `client_uuid` U | 201 |
| Renvoi | A, U, même contenu | 200, même `id`, Numéro et Statut ; aucune ligne, aucun objet, compteur inchangé |
| Renvoi modifié | A, U, autre commentaire, autre photo, autre Position | 200 identique ; le Signalement existant n'est pas modifié |
| 10 renvois à la suite | A, U | 1 ligne, 1 objet ; 1 × 201 puis 9 × 200 |
| 10 envois en parallèle | A, U | Exactement 1 × 201 et 9 × 200, même Numéro ; 1 ligne, 1 objet dans le bucket |
| Autre appareil | B, U | 409 `client_uuid_conflict`, enveloppe seule ; Signalement de A inchangé |
| Principal `user` (service) | `user:<id>` avec l'U d'un appareil / son propre U | 409 / 200 avec l'existant |
| 201 perdu | Coupure simulée après le commit, puis renvoi | 200 avec le Numéro de la première réception |

</frozen-after-approval>

## Code Map

- `backend/app/modules/reports/service.py` : `create_report` (story 1.11) et sa signature actuelle, `@transactional`.
- `backend/app/modules/reports/repository.py` : insertions et compteur ; à compléter par une recherche par `client_uuid`.
- `backend/app/modules/reports/router.py` : route synchrone, `responses=`, garde avant le corps.
- `backend/app/core/security.py` : `principal()` et le type du Principal, à rendre générique (`kind`, `owner_key`) sans changer le comportement de la route.
- `backend/app/core/db.py` : `transactional`, `unit_of_work`, `after_rollback`.
- `backend/migrations/versions/0003_reports.py` : modèle ; la nouvelle migration `0004` s'y enchaîne.
- `backend/app/core/errors/codes.py`, `web/src/i18n/fr.json`, `wo.json`, `tests/unit/test_errors.py` (liste codée en dur), `tests/unit/test_error_messages.py`.
- `backend/tests/integration/test_reports_api.py` : modèle des tests sur la pile réelle, avec comptage de la base et du bucket.

## Tasks & Acceptance

**Execution:**
- [x] `backend/migrations/versions/0004_reports_client_uuid_unique.py` : contrainte, downgrade.
- [x] `backend/app/core/security.py` : Principal générique.
- [x] `backend/app/modules/reports/` (service, repository, router) : recherche préalable, gestion de la violation de contrainte, réponse 200, 409.
- [x] `backend/app/core/errors/codes.py` et i18n : `client_uuid_conflict`.
- [x] **Tests :**
  - intégration : chaque ligne de la matrice, avec comptage de la base, du bucket et du compteur ; les 10 envois parallèles par threads réels ; le 201 perdu simulé par un hook `after_commit` qui lève ;
  - service : Principal `user` ;
  - schéma : contrainte présente, avec l'ordre de ses colonnes.
- [x] `README.md` : renvoi idempotent et 409.

**Acceptance Criteria:**
- Tous les critères d'acceptation de la story 1.12 d'`epics.md` sont couverts par au moins un test qui tourne en CI.

## Implementation Notes

- **Contrainte :** `uq_reports_client_uuid_owner_key`, `UNIQUE (client_uuid, owner_key)` ; nom exporté par `reports.repository.CLIENT_UUID_CONSTRAINT` et vérifié contre la migration.
- **Recherche préalable :** deux requêtes indexées : le Signalement de l'auteur (`client_uuid` et `owner_key`), puis, s'il n'y en a pas, la seule existence de l'Identifiant client (préfixe de l'index) : rien du Signalement d'un autre auteur n'est lu.
- **Course :** `insert_report` traduit la seule violation de `CLIENT_UUID_CONSTRAINT` (`UniqueViolation` et nom de contrainte) en `ClientUuidTakenError`. `create_report` reste `@transactional` ; un décorateur privé (`_settle_parallel_sends`) placé autour de son unité intercepte cette erreur après l'annulation (ligne, compteur, photo par `after_rollback`) et relit l'existant dans une nouvelle unité (`_reread_after_race`, `@transactional`). Si l'appelant avait déjà ouvert une unité (`core.db.in_unit_of_work()`, ajouté), l'erreur est relevée : son unité est perdue.
- **Verrou (relecture, passe 1) :** l'unité de la création prend d'abord `pg_advisory_xact_lock(hashtextextended(client_uuid::text, 0))`, avant la recherche : deux envois simultanés du même `client_uuid` (même auteur ou non) se suivent ; le second obtient 200 sans traiter de photo, ou 409. La violation de contrainte reste un filet de sécurité ; si la relecture ne trouve aucun Signalement de l'auteur, 409 (jamais 500).
- **Identifiant client :** UUID version 4 exigé (`UUID4` de Pydantic, 422 `meta.client_uuid`), tiré par `crypto.randomUUID()`.
- **Migration 0004 :** refuse de poser la contrainte s'il existe des paires en double (`DuplicateClientUuidError`, nombre et remède), sans dédoublonnage automatique.
- **Photo :** le service reçoit `read_photo` (lecture bornée à 1 Mo + 1 octet faite par le router), appelée seulement pour une création : un renvoi ne lit ni ne stocke la photo.
- **Réponse :** le service renvoie `ReportOutcome(report, replayed)` ; le router passe à 200 quand `replayed`. OpenAPI : `200` (modèle `ReportCreated`) et `409` dans `responses=`.
- **Principal :** `Principal(kind, owner_key)` ; `owner_key` doit commencer par `<kind>:` ; `device_hash` devient une propriété (`None` pour `user`) ; pas de `touch_device()` pour un Principal `user`.
- **Journaux :** `report_replayed` (`report_id`, `tracking_number`, `replayed=true`) ; `report_client_uuid_conflict` sans aucun champ.
- **201 perdu :** simulé par un effet `after_commit` qui lève une `BaseException` (non absorbée par `_run_hooks_sync`, qui n'attrape que `Exception`).

## Spec Change Log

## Review Triage Log

Passe 1 (26/11/2026). Couches : Blind Hunter (B), Edge Case Hunter (E), Verification Gap (V).

| # | Constat | Verdict | Preuve | Route |
|---|---|---|---|---|
| E1 / B1 / E6 | Deux auteurs envoient le même Identifiant client au même instant : deux 201 | medium | La contrainte vaut par auteur ; le 409 dépend d'une lecture préalable sans verrou | patch (verrou consultatif par Identifiant client) |
| B6 | Les envois perdants stockent puis suppriment une photo pour rien | low | 9 envois et 9 suppressions dans le test à 10 | patch (réglé par le verrou) |
| E3 / B7 | `ClientUuidTakenError` peut remonter en 500 | low | Relecture vide après la course | patch (409) |
| B9 | Identifiant client de toute version accepté ; existence révélée par le 409 | low | Aucun contrôle de version | patch (UUID v4 exigé, documenté) |
| E2 / B2 | Migration bloquée par d'éventuels doublons existants, erreur opaque | low | Aucune vérification avant `ADD CONSTRAINT` | patch (message clair, sans dédoublonnage automatique) |
| B8 | Message 409 propre à l'appareil, alors que les comptes arrivent | low | « depuis cet appareil » | patch |
| B3 / B11 | Ligne 409 absente du tableau principal du README ; ordre des réponses OpenAPI | low | README et `ERROR_RESPONSES` | patch |
| V1 / B12 / B13 | Non testés : renvoi reconnu avant consentement, zone et lecture de la photo sur la route ; intention du test de 201 perdu | medium | Déplacer la recherche ne fait échouer aucun test | patch |
| E4 | Un renvoi ne revérifie ni consentement ni zone | false | Ordre voulu par la spec : le contenu renvoyé est ignoré | rejeté |
| B4 | Aucune gestion côté application (Identifiant client, 200, 409) | low | Objet de la story 1.13 | rejeté (story 1.13) |
| B5 | `wo.json` copie de `fr.json` | false | Interface wolof hors objectifs du hackathon | rejeté |
| B10 | `ReportOutcome` dans `schemas.py` | low | Rangement sans effet | rejeté |
| B2b | Index construit sans `CONCURRENTLY` | low | Table encore petite, aucune donnée de production | rejeté |

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run lint-imports && REQUIRE_INTEGRATION=1 uv run pytest --cov` (backend, pile réelle : base 127.0.0.1:55432, Garage 127.0.0.1:3900) — expected: vert.
- `npx vitest run src/i18n` (web) — expected: vert.
