---
title: 'Story 1.11 — Recevoir un Signalement anonyme et attribuer son Numéro de suivi'
type: 'feature'
created: '2026-11-26'
status: 'done'
baseline_commit: '292642238893fc0be8449ee00bbbb0a22ca9836b'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-10-stocker-une-photo-sans-metadonnees-dans-le-bucket-prive.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Le serveur ne sait pas encore recevoir un Signalement. Le Citoyen anonyme n'a donc ni Numéro de suivi ni preuve que la commune a reçu son signalement.

**Approach:**
- `POST /v1/reports` (multipart : `meta` JSON + `photo`) identifie l'appareil par `core.security.principal()` ;
- la route valide le consentement, la Position (Zone active) et les champs, puis range la photo par `core.storage.ingest_photo()` ;
- elle enregistre le Signalement `pending_review` avec un Numéro de suivi `TC-AAAA-NNNNNN` et répond 201 ;
- tout se fait dans une seule unité de travail.

**Décision (26/11/2026) :** la miniature (tâche arq `thumb:<photo_id>`) est sortie de cette story. Elle est notée dans `deferred-work.md` et sera livrée juste après. La colonne `report_photos.thumb_key` (nullable) est créée ici.

## Boundaries & Constraints

**Always:**
- Migration `0003_reports`, qui crée seulement :
  - `devices` (`device_hash` en clé, `training_consent`, `consent_at`, `first_seen_at`), propriétaire `auth` ;
  - `reports`, `report_photos` (dont `thumb_key` nullable) et `tracking_counters` (`year` en clé, `n`), propriétaire `reports`.
- Colonnes de `reports` :
  - `id` uuid, `tracking_number` unique, `owner_key`, `client_uuid` ;
  - `geog GEOGRAPHY(Point,4326)`, `accuracy_m > 0`, `client_captured_at` ;
  - `pile_size` (CHECK `small|medium|large`), `comment` (CHECK ≤ 280 caractères), `citizen_type` nullable (CHECK sur les 5 Types) ;
  - `zone_id` (FK `zones`), `status` (CHECK sur `ReportStatus`) ;
  - `received_at`, `training_consent`, `is_demo NOT NULL DEFAULT false`, `flag_imprecise_position`.
  - Les valeurs des CHECK viennent de `core/enums.py`.
  - Pas encore d'unicité `(owner_key, client_uuid)` : c'est la story 1.12.
- `meta` (JSON, schéma Pydantic strict, champs inconnus refusés) :
  - `client_uuid` (UUID), `lat` (−90..90), `lng` (−180..180), `accuracy_m` (> 0), `captured_at` (ISO 8601) ;
  - `pile_size`, `comment` (≤ 280 points de code, facultatif), `waste_type` (facultatif) ;
  - `consent: {terms: bool, training: bool}`.
- Ordre des contrôles, sans rien écrire avant le dernier :
  1. principal ;
  2. `meta` et présence de `photo` ;
  3. `consent.terms` ;
  4. Zone active (`core.geo.in_active_zone`) ;
  5. `ingest_photo` ;
  6. puis les écritures.
- `core.security.principal()` est le seul lecteur de `Authorization` et de `X-Device-Id`.
  - Il renvoie `Principal(kind="device", device_hash, owner_key="device:<hash>")`, avec `device_hash` = HMAC-SHA256(`DEVICE_ID_PEPPER`, id) en hexadécimal.
  - Tant qu'aucun jeton n'existe (epic 2), tout en-tête `Authorization` est invalide : 401 `invalid_token`.
- Numéro de suivi :
  - `INSERT INTO tracking_counters … ON CONFLICT (year) DO UPDATE SET n = n + 1 RETURNING n` ;
  - année = celle de `received_at = core.clock.now()` (UTC) ; 6 chiffres complétés par des zéros.
- `flag_imprecise_position = accuracy_m > REPORT_ACCURACY_FLAG_M` (50 m exactement : pas de drapeau).
- `zone_id = core.geo.zone_of(...)`, le quartier sinon la commune.
- `is_demo = core.demo.flag()`, qui vaut `DEMO_MODE` (le paramètre `parent_is_demo` est prévu pour plus tard).
- `auth.service.touch_device(device_hash, training_consent, now)` crée ou met à jour `devices`. `reports.service.create()` l'appelle, et la flèche `reports → auth.service` est déjà autorisée.
- Services `@transactional`, sans `commit`, `rollback` ni `begin`.
- La route est un `def` synchrone avec `UowSession`. Elle est déclarée publique (déjà dans `PUBLIC_ROUTES`), et `RESERVED_PUBLIC_ROUTES` ne contient plus `POST /v1/reports`.
- Réponse 201 : `id`, `tracking_number`, `status`, `received_at` (ISO 8601 en `Z`), `is_demo`. Jamais `owner_key`, empreinte ni Identifiant d'appareil.
- Les 422 de validation nomment le ou les champs fautifs (par exemple `meta.lat`, `photo`), sans recopier de valeur.
- Nouveaux codes, avec leurs messages `fr.json`/`wo.json` :
  - `invalid_device_id` (400) ;
  - `invalid_token` (401) ;
  - `consent_required` (422) ;
  - `outside_active_zone` (422), message « TerangaCycle n'est pas encore actif ici. »
- Aucune coordonnée, aucun Identifiant d'appareil et aucune empreinte dans les journaux ni les messages d'erreur.

**Never:**
- pas de miniature ni de tâche arq (story différée) ;
- pas de renvoi idempotent ni de 409 `client_uuid_conflict` (story 1.12) ;
- pas de doublons probables (1.14), de limite de débit (1.15), de `report_status_events` ni d'audit (epic 4) ;
- pas de colonnes `client_predicted_*` (epic 3) ;
- pas de PWA (story 1.13).

## I/O & Edge-Case Matrix

| Scénario | Entrée | Résultat attendu |
|---|---|---|
| Nominal | appareil valide, Plateau, ± 12 m, `medium`, JPEG | 201 `TC-2026-000001`, `pending_review` ; lignes `reports`, `report_photos` et `devices` ; objet `report/…` |
| Imprécis | ± 51 m / ± 50 m | 201 ; drapeau vrai / faux |
| Champ manquant | sans `photo`, sans `lat`, sans `pile_size` | 422 `validation_error` nommant le champ ; rien d'écrit |
| Commentaire | 280 / 281 points de code (emoji compris) | 201 / 422 |
| Hors bornes | `lat` 91, `accuracy_m` 0 ou −1, `pile_size` `huge`, `waste_type` `paper` | 422 |
| Sans consentement | `consent.terms` faux ou absent | 422 `consent_required` ; ni ligne ni objet |
| Appareil | en-tête absent, 42 car., caractère hors base64url | 400 `invalid_device_id` |
| Jeton | `Authorization: Bearer x` | 401 `invalid_token` |
| Hors Zone | Thiès | 422 `outside_active_zone` ; ni ligne ni objet |
| Photo refusée | GIF / 1,1 Mo | 415 / 413 ; ni ligne ni objet |
| Panne après stockage | exception avant le commit | aucune ligne ; objet supprimé |
| Concurrence | 20 créations simultanées | 20 numéros distincts |
| Changement d'année | 31/12/2026 23:59:59 puis 01/01/2027 00:00:00 UTC | `TC-2026-…` puis `TC-2027-000001` |
| Démo | `DEMO_MODE` vrai / faux | `is_demo` vrai / faux |

</frozen-after-approval>

## Code Map

- `backend/app/core/access.py:66` : `RESERVED_PUBLIC_ROUTES` (retirer `POST /v1/reports`). `tests/architecture/test_route_policies.py` vérifie la table des routes.
- `backend/app/main.py:create_app()` : inclure le router `reports`. `app.state.settings` est disponible.
- `backend/app/core/db.py` : `UowSession`, `transactional`, `current_session`.
- `backend/app/core/geo.py:123,128` : `in_active_zone`, `zone_of` (lèvent `InvalidPositionError` sur NaN ou hors bornes). `geo.zones` est un exemple de `Table` déclarée pour Alembic.
- `backend/app/core/storage.py` : `ingest_photo(PhotoKind.REPORT, data, photo_id=...)`, avec `photo_id` = id de la ligne `report_photos`.
- `backend/app/core/errors/__init__.py` : `DomainError`, `_validation_exception_handler` (à étendre pour nommer les champs). `tests/unit/test_errors.py:155` fige la liste des codes.
- `backend/app/core/config.py` : `device_id_pepper`, `demo_mode`, `report_accuracy_flag_m`.
- `backend/migrations/versions/0002_zones.py` : style de migration. `infra/db/initdb/20-roles.sh` donne le DML à `teranga_app` par défaut.
- `backend/pyproject.toml` : contrats import-linter (`router → service → repository`) ; `python-multipart` absent, à ajouter (version exacte).
- `backend/tests/integration/test_zones.py` : URL de test, Plateau `(14.6708, -17.4381)`, Thiès `(14.7910, -16.9359)`. `tests/unit/test_storage.py` : faux client S3 et SQLite pour l'unité de travail. `tests/photos.py` : images de test.

## Tasks & Acceptance

**Execution:**
- [x] `backend/pyproject.toml`, `uv.lock` : `python-multipart` épinglé.
- [x] `backend/migrations/versions/0003_reports.py` : les 4 tables, leurs index (`reports.geog` GiST, `owner_key`, `zone_id`, `status`) et un downgrade.
- [x] `backend/app/core/security.py` : `Principal` et `principal()`. `backend/app/core/demo.py` : `flag()`.
- [x] `backend/app/core/errors/codes.py`, `web/src/i18n/{fr,wo}.json`, `tests/unit/test_errors.py` : les 4 codes. `core/errors/__init__.py` : champs nommés dans les 422.
- [x] `backend/app/modules/auth/{models,repository,service}.py` : `devices`, `touch_device()`.
- [x] `backend/app/modules/reports/{models,schemas,repository,service,router}.py` : schéma `ReportMeta`, compteur, `create()`, route.
- [x] `backend/app/core/access.py`, `backend/app/main.py`, `tests/unit/test_layout.py` : branchements.
- [x] Tests unitaires : `principal()`, schéma `meta` (bornes, 280/281, champs inconnus), drapeau 50/51, format du numéro.
- [x] Tests d'intégration `tests/integration/test_reports_create.py`, sur PostGIS et Garage réels :
  - une ligne de test par ligne de la matrice ;
  - « rien d'écrit » vérifié par comptage des lignes et des objets ;
  - concurrence par threads ;
  - horloge simulée ;
  - aucune coordonnée dans les journaux capturés.

**Acceptance Criteria:**
- Étant donné une base migrée, quand on liste les tables, alors `devices`, `reports`, `report_photos` et `tracking_counters` existent en plus des précédentes, et `downgrade` les retire.
- Étant donné `uv run ruff check . && uv run lint-imports && uv run pytest` avec la pile démarrée, alors tout est vert et la couverture reste ≥ 60 %.

## Implementation Notes

- **python-multipart 0.0.34**, épinglé exactement.
- **Pas de `models.py`** : les repositories écrivent en SQL paramétré (`text()`), comme `core/geo`. La migration `0003_reports` reste le seul chemin de schéma (AD-15), et aucune `Table` n'est déclarée dans les métadonnées : rien ne lit ces tables par l'ORM.
- **CHECK de la migration** : les valeurs viennent de `app.core.enums` (`PileSize`, `WasteType`, `ReportStatus`). CHECK supplémentaires : format du Numéro de suivi et de `device_hash`, préfixe de `owner_key`, dimensions et `sha256` des photos. Downgrade et ré-upgrade vérifiés sur PostGIS.
- **`core/security.py`** :
  - `is_valid_device_id` exige la forme canonique (43 caractères base64url qui décodent 32 octets, bits de remplissage nuls) ;
  - `principal` est une dépendance FastAPI, résolue avant la validation du corps (401, puis 400, avant tout 422).
- **`core/errors`** : `field_name()` et `validation_error()` nomment les champs (`photo`, `meta.lat`) sans recopier de valeur. Le gestionnaire des `RequestValidationError` s'en sert aussi.
- **Route** : `meta` est validé par `ReportMeta.model_validate_json` (strict, champs inconnus refusés). `consent` absent vaut refus (`consent_required`). La photo est lue avec un plafond de 1 Mo + 1 octet.
- **Service** :
  - ordre des contrôles : consentement, Zone active (`geo.in_zone` avec `settings.active_zone_id`), `zone_of`, puis `ingest_photo` ;
  - le numéro (`ON CONFLICT … RETURNING n`), `touch_device` et les insertions viennent ensuite ;
  - `settings` est passé par la route (`app.state.settings`) : pas de lecture de `get_settings()` dans la règle métier.
- **`devices.consent_at`** ne change que si le choix de réentraînement change.
- **Tests** :
  - `tests/unit/test_reports_route.py` (45 tests), renommé car pytest refuse deux modules homonymes ;
  - `tests/integration/test_reports_create.py` (27 tests, une ligne par ligne de la matrice ; « rien d'écrit » vérifié par comptage des lignes et des objets) ;
  - `tests/reports_support.py` fournit le formulaire multipart, `meta` et l'appareil.
- **Vérifié en local** :
  - suite complète avec `REQUIRE_INTEGRATION=1` : 538 réussis, couverture 96 % ;
  - ruff, format et import-linter verts ; Vitest `src/i18n` vert.
  - Base locale sur le port 55432 (5432 occupé sur le poste : `.env` local seulement).

## Spec Change Log

## Review Triage Log

Passe 1 (26/11/2026). Couches : Blind Hunter (B), Edge Case Hunter (E), Verification Gap (V).

| # | Constat | Verdict | Preuve | Route |
|---|---|---|---|---|
| B / E | Commentaire avec NUL : 500 au lieu de 422 ; commentaire vide stocké tel quel | medium | PostgreSQL refuse ` ` dans `text` | patch : validateur (NUL refusé, vide → nul), tests |
| E | Précision positive minuscule arrondie à 0 (`real`) : CHECK, puis 500 | low | Colonne `float4` | patch : `double precision` |
| E | Nom d'un champ inconnu recopié dans le 422 | low | `loc` d'`extra_forbidden` = texte du client | patch : « meta (champ inconnu) », test |
| V / B | Mise à jour de `devices` jamais testée | medium | Aucun test n'envoie deux fois depuis le même appareil | patch : test choix, `consent_at`, `first_seen_at` |
| V | `zone_id`, `client_uuid`, `client_captured_at`, `accuracy_m` non vérifiés | medium | `assert row.zone_id` seulement | patch : égalités ajoutées |
| B | Cas de matrice manquants (caractère hors base64url, précision −1) | low | Absents de la table des refus | patch |
| B / V | Appareils de test non nettoyés | low | Fixture `created` | patch |
| B | Test de confidentialité limité à stdout | low | stderr et corps de réponse non lus | patch |
| B / E | « jamais plus en mémoire » faux : la partie est déjà reçue | low | python-multipart reçoit tout avant la route | patch (commentaire) ; limite du corps différée (8.4) |
| B / V | Docstring de migration périmée (`thumb_key`) | low | La colonne est créée ici | patch |
| B | Plafond codé en dur dans un test ; test redondant | low | `1_000_001` | patch |
| V / B | Aucun test automatique du downgrade | low | Aucun test de migration dans le dépôt | différé (test commun à toutes les migrations) |
| B | `in_zone(settings.active_zone_id)` au lieu de `in_active_zone` | low | Même règle (`ST_Covers` exact) avec les réglages de l'app ; `app.state.active_zone` est le polygone élargi de la PWA, inutilisable pour trancher | rejeté |
| B / E | `models.py` absent malgré les tâches | false | Choix noté dans les Implementation Notes : SQL paramétré, comme `core/geo` | rejeté |
| B | Statut du sprint ≠ spec | false | Synchronisé à la présentation | rejeté |
| B | `wo.json` non traduit | false | Interface wolof hors hackathon (NFR-P3) | rejeté |
| B | `DEVICE_ID_PEPPER` absent : 500 à la requête | false | `REQUIRED_SECRETS` l'exige en demo/prod (refus de démarrer) | rejeté |
| E | Poivre éphémère différent par processus en `dev` | low | `dev` seulement, secrets réels exigés ailleurs | rejeté |
| E | Compteur au-delà de 999 999 : 500 | low | Hors de portée d'un pilote | rejeté |
| E | `captured_at` invraisemblable | low | Valeur client en colonne `client_`, affichage seulement (AD-6) | rejeté |
| E | Corps multipart malformé analysé avant le principal | low | Requête malformée et sans appareil : cas marginal | rejeté |
| E | Ordre champs puis consentement | false | Conforme à l'ordre de la spec (forme de `meta` avant `consent.terms`) | rejeté |
| B / E | Comptage global du bucket et de `reports` en test | low | Aucun écrivain concurrent en CI | rejeté |

## Design Notes

**Pourquoi tout valider avant `ingest_photo` :** l'objet S3 est l'effet le plus coûteux à défaire. Hors Zone ou sans consentement, il ne doit jamais être écrit (AC « ni ligne ni objet »). Une panne après l'écriture est couverte par `after_rollback` (story 1.10).

**`meta` en JSON dans un champ de formulaire :** `meta: str = Form()`, puis `ReportMeta.model_validate_json(meta)`. Une `ValidationError` devient 422 `validation_error`, avec les chemins `meta.<champ>` dans le message.

## Verification

**Commands:**
- `cd backend && uv run ruff check . && uv run ruff format --check . && uv run lint-imports` -- expected: vert.
- `cd backend && uv run pytest --cov` (pile `db`, `migrate`, `garage` démarrée, variables `TEST_*`) -- expected: vert, intégration exécutée.
