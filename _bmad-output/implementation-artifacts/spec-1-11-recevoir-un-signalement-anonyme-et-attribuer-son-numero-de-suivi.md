---
title: 'Story 1.11 — Recevoir un Signalement anonyme et attribuer son Numéro de suivi'
type: 'feature'
created: '2026-11-25'
status: 'done'
baseline_commit: 'a4711fd51c9b971bcadc5dcc6499a340e0fa9dce'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-10-stocker-une-photo-sans-metadonnees-dans-le-bucket-prive.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Le serveur ne sait pas encore enregistrer un Signalement. Sans cela, le parcours du Citoyen s'arrête au brouillon sur le téléphone : pas de Numéro de suivi, pas de prise en charge par la commune. Depuis la v2.0, chaque Signalement doit aussi être rattaché dès sa création à l'Organisation responsable (AD-31). C'est cette story qui crée la table `reports`.

**Approach:** créer `POST /v1/reports` (`multipart/form-data` : `meta` en JSON et `photo`), route publique du Citoyen anonyme identifié par `X-Device-Id`. Les critères d'acceptation de référence sont ceux de la section `### Story 1.11` d'`_bmad-output/planning-artifacts/epics.md`, à respecter intégralement.

La story crée aussi :
- la migration `0003` : `organizations` avec la ligne de l'Organisation plateforme, `devices`, `reports`, `report_photos`, `tracking_counters` ;
- le module `orgs` (`responsible_org()`) ;
- `core.security.principal()` et `core.demo.flag()` ;
- les services `auth.service.touch_device()` et `reports.service.create_report()`.

## Boundaries & Constraints

**Always:**
- **Ordre des contrôles, pour qu'un refus n'écrive jamais rien :**
  1. principal : `X-Device-Id` absent ou invalide → 400 `invalid_device_id` ; en-tête `Authorization` présent → 401 `invalid_token` (aucun jeton n'est vérifiable avant l'Epic 2) ;
  2. `meta` absent, illisible ou invalide, ou photo absente → 422 `validation_error` nommant le champ ;
  3. `consent.terms` absent ou faux → 422 `consent_required` ;
  4. Position hors de la Zone active (`core.geo.in_active_zone`) → 422 `outside_active_zone` ;
  5. photo refusée par `ingest_photo()` → 413, 415 ou 422 (story 1.10) ;
  6. écriture.
- **`meta`** (Pydantic, champs inconnus refusés) :
  - `client_uuid` (UUID de l'Identifiant client) ;
  - `lat` (−90 à 90), `lng` (−180 à 180), `accuracy_m` (> 0) ;
  - `heap_size` ∈ `small`, `medium`, `large` ;
  - `comment` facultatif, 280 points de code au plus ;
  - `waste_type` facultatif, parmi les 5 Types de déchet ;
  - `captured_at` (heure de l'appareil, gardée à part, jamais utilisée pour décider) ;
  - `consent` : `{terms, training}`.
  Toutes les énumérations viennent de `core/enums.py`.
- **Lecture de la photo :** on lit au plus 1 048 576 + 1 octets avant de passer la main à `ingest_photo()`. Un client ne peut pas faire charger un fichier énorme en mémoire.
- **Transaction :**
  - la route est synchrone (`def`, exécutée dans le pool de threads) et appelle un service `@transactional` qui utilise l'unité de travail synchrone et `ingest_photo()` ;
  - aucun service ni repository n'appelle `commit`, `rollback` ou `begin` (le test `test_no_tx_calls` devient actif) ;
  - une exception après le stockage annule tout, et l'objet est supprimé (story 1.10).
- **Numéro de suivi :**
  - `TC-AAAA-NNNNNN`, compteur annuel avec `INSERT … ON CONFLICT (year) DO UPDATE SET n = tracking_counters.n + 1 RETURNING n` ;
  - l'année et `received_at` viennent de `core.clock.now()` (UTC) ;
  - `NNNNNN` est complété par des zéros (6 chiffres).
- **Organisation responsable :**
  - `orgs.service.responsible_org(lat, lng)` choisit l'Organisation `active` de type `commune` ou `operator` dont la Zone couvre le point, la plus précise d'abord (quartier, puis commune, puis ville) ;
  - à défaut, l'Organisation plateforme : UUID fixe exporté par `orgs`, ligne insérée par la migration, `is_demo = false`, type `platform`, sans Zone ;
  - jamais renvoyée au Citoyen ; aucune route pour la modifier.
- **Champs calculés par le serveur :**
  - `owner_key = device:<HMAC-SHA256(DEVICE_ID_PEPPER, id)>`, calculé par `core.security.principal()` ;
  - `zone_id = core.geo.zone_of()` ;
  - `flag_imprecise_position = accuracy_m > REPORT_ACCURACY_FLAG_M` (strictement) ;
  - `is_demo = core.demo.flag()` ;
  - statut `pending_review` ;
  - `training_consent` copié de `consent.training` ;
  - `touch_device()` crée ou met à jour `devices`.
- **Réponse 201 :** exactement `id`, `tracking_number`, `status`, `received_at` (ISO 8601 en `Z`), `is_demo`.
- **Codes d'erreur nouveaux :** `invalid_device_id`, `invalid_token`, `consent_required`, `outside_active_zone`. Chacun a un `DEFAULT_MESSAGES` et un `errors.<code>` en `fr.json` et `wo.json` ; `outside_active_zone` = « TerangaCycle n'est pas encore actif ici ».
- **Architecture :**
  - `orgs` est un conteneur du contrat `layers` ;
  - seule flèche ajoutée dans `protected` : `reports → orgs.service` (`reports → auth.service` existe déjà) ;
  - la route passe de `RESERVED_PUBLIC_ROUTES` à une vraie route publique.
- **Confidentialité :**
  - aucune coordonnée, aucun Identifiant d'appareil, aucune empreinte ni aucun `owner_key` dans les journaux ou les réponses ;
  - les journaux portent seulement l'`id` et le `tracking_number`.

**Never:**
- pas d'unicité `(owner_key, client_uuid)` ni de renvoi idempotent (story 1.12) ;
- pas de doublons (1.14), de limites de débit (1.15), de miniature (1.18) ni d'écran PWA d'envoi (1.13) ;
- pas de jeton JWT (Epic 2) ;
- aucun mock de base, de PostGIS ni de Garage dans les tests d'intégration.

## I/O & Edge-Case Matrix

| Scénario | Entrée | Attendu |
|---|---|---|
| Nominal | Appareil valide, consentement, Position au Plateau, `heap_size`, JPEG < 1 Mo | 201 ; ligne `reports` complète, `report_photos` (clé, sha256, taille), `devices` créé ; aucune donnée sensible dans la réponse |
| Champ manquant | Sans photo / sans `lat` / sans `heap_size` | 422 `validation_error` nommant le champ ; rien d'écrit |
| Commentaire | 280 / 281 points de code (avec emojis) | 201 / 422 |
| Bornes | lat 91, lng −181, précision 0 ou −1, Taille ou Type inconnus | 422 |
| Consentement | `terms` absent ou faux | 422 `consent_required` ; ni ligne ni objet |
| Appareil | Sans `X-Device-Id`, 42 caractères, caractère hors base64url | 400 `invalid_device_id` |
| Jeton | `Authorization: Bearer x` | 401 `invalid_token` |
| Hors Zone | Thiès | 422 `outside_active_zone` ; rien d'écrit |
| Photo refusée | GIF, > 1 Mo, illisible | 415 / 413 / 422 ; ni ligne ni objet |
| Organisations | 2 communes actives dans deux communes d'arrondissement, rien sur la troisième | Les deux premiers Signalements prennent leur commune, le troisième l'Organisation plateforme |
| Concurrence | 20 créations simultanées | 20 numéros distincts |
| Changement d'année | Horloge 31/12/2026 23:59:59 puis 01/01/2027 00:00:00 UTC | `TC-2026-…` puis `TC-2027-000001` |
| Précision | 51 m / 50 m | Drapeau / pas de drapeau ; 201 |
| Échec tardif | Exception après le stockage | Aucune ligne ; objet supprimé |
| Démo | `DEMO_MODE` vrai / faux | `is_demo` vrai / faux |

</frozen-after-approval>

## Code Map

- `backend/app/core/access.py` : `PUBLIC_ROUTES` contient déjà `("POST", "/v1/reports")` ; il faut le retirer de `RESERVED_PUBLIC_ROUTES`. Le test `tests/architecture/test_route_policies.py` vérifie la table.
- `backend/app/core/db.py` : `transactional`, `unit_of_work`, `current_session`, `after_rollback`. `tests/architecture/test_no_tx_calls.py` est ignoré faute de service ; il doit devenir actif.
- `backend/app/core/storage.py` : `ingest_photo(PhotoKind.REPORT, data)`, qui renvoie `StoredPhoto`.
- `backend/app/core/geo.py` : `in_active_zone`, `zone_of`, la table `zones` (hiérarchie Dakar → communes → quartiers, `kind`). C'est le modèle à suivre pour `responsible_org`.
- `backend/app/core/config.py` : `device_id_pepper`, `report_accuracy_flag_m`, `demo_mode`, `active_zone_id`.
- `backend/app/core/errors/` : `DomainError`, `ErrorCode`, `DEFAULT_MESSAGES`. Les tests `test_errors.py` (liste codée en dur) et `test_error_messages.py` imposent les messages.
- `backend/app/core/enums.py` : ajouter `OrganizationType`, `OrganizationStatus`, `ReportStatus`, `HeapSize`, `WasteType` s'ils n'existent pas.
- `backend/migrations/versions/0002_zones.py` : modèle de migration, avec les droits et la lecture seule pour `teranga_app`.
- `backend/app/main.py` : inclure les routers des modules.
- `backend/pyproject.toml` `[tool.importlinter]` : `layers` (ajouter `app.modules.orgs`) et `protected` (flèche `reports → orgs.service`).
- `infra/Caddyfile` : vérifier la taille maximale du corps pour `/v1/reports` (photo de 1 Mo plus `meta`).
- `_bmad-output/planning-artifacts/architecture/architecture-TerangaCycleAI-2026-11-23/ARCHITECTURE-SPINE.md` : AD-2 (propriété des tables), AD-9, AD-11, AD-18, AD-31.

## Tasks & Acceptance

**Execution:**
- [x] `backend/migrations/versions/0003_reports.py` : les 5 tables, les contraintes des critères d'acceptation et la ligne de l'Organisation plateforme ; le downgrade supprime les tables.
- [x] `backend/app/core/enums.py`, `core/errors/codes.py`, `web/src/i18n/fr.json`, `web/src/i18n/wo.json` : énumérations et codes avec leurs messages.
- [x] `backend/app/core/security.py` (`principal()`) et `backend/app/core/demo.py` (`flag()`).
- [x] `backend/app/modules/orgs/` (`service.responsible_org`, `repository`, constante de l'Organisation plateforme) et `backend/app/modules/auth/` (`service.touch_device`, `repository`).
- [x] `backend/app/modules/reports/` : `router` (route synchrone), `service.create_report` (`@transactional`), `repository` (compteur, insertions), schémas.
- [x] `backend/app/main.py`, `core/access.py`, `pyproject.toml` (import-linter), et `infra/Caddyfile` si la limite de taille du corps l'exige.
- [x] **Tests :**
  - unitaires : schéma `meta`, principal, format du numéro, seuil du drapeau ;
  - intégration sur PostgreSQL, PostGIS et Garage réels : chaque ligne de la matrice, avec relecture de la base et du bucket ;
  - architecture : routes, `no_tx_calls`, import-linter.
- [x] `backend/scripts/smoke_edge.py` : un `POST /v1/reports` à travers Caddy (photo générée, Position au Plateau) qui doit renvoyer 201.

**Acceptance Criteria:**
- Tous les critères d'acceptation de la story 1.11 d'`epics.md` sont couverts par au moins un test qui tourne en CI.

## Implementation Notes

- **Dépendance :** `python-multipart==0.0.34` (publiée le 16/11/2026) ajoutée et verrouillée : FastAPI ne lit pas de `multipart/form-data` sans elle.
- **`HeapSize` :** l'énumération `PileSize` existante (mêmes valeurs, aucun usage) est renommée `HeapSize`, pour rester définie une seule fois sous le nom du champ `heap_size`.
- **Consentement :** `consent` absent, `consent.terms` absent ou faux → 422 `consent_required` ; quand `consent` est présent, `consent.training` est exigé (AD-24) et son absence donne 422 `validation_error` (`meta.consent.training`).
- **Champ nommé :** le message des 422 `validation_error` nomme les champs (`meta.lat`, `photo`), jamais leur valeur ; le gestionnaire global de FastAPI fait de même (noms assainis, 5 au plus).
- **Réglages de l'application :** la clé DEVICE_ID_PEPPER est décodée une fois au démarrage (32 octets en base64, sinon `startup_refused`, quel que soit `ENV`) depuis `app.state.settings` ; `principal()`, `demo_mode`, `report_accuracy_flag_m` et la Zone active lisent ces mêmes réglages (`request.app.state`), jamais `get_settings()`. Les secrets factices des tests (`tests/support.py`) suivent ce format.
- **Photo :** `report_photos.id` est l'`<uuid>` de la clé `report/<aaaa>/<mm>/<uuid>.jpg` (AD-13).
- **Zones et Organisation responsable :** le service lit une fois `core.geo.zones_covering()` (quartier, commune d'arrondissement, ville ; même ordre que `zone_of`) : la première Zone devient `zone_id`, et la liste est passée à `orgs.service.responsible_org(zones)`, qui choisit par Zone l'Organisation `active` commune ou opérateur la plus ancienne.
- **Horloge :** `received_at` est lu une fois et passé à `ingest_photo(..., at=received_at)` : le Numéro et la clé de la photo ont la même année et le même mois.
- **Corps borné avant lecture :** Caddy refuse tout corps de `/v1/reports` au-delà de 2 Mo (`request_body`) ; dans l'API, la garde `ReportUploadGuard` refuse, sur les seuls en-têtes, `X-Device-Id` absent ou invalide (400), puis `Authorization` (401), puis `Content-Length` au-delà de 2 Mio (413 `photo_too_large`).
- **Commentaire et heure de l'appareil :** commentaire sans blancs de bord, vide → NULL, 280 points de code après retrait ; `captured_at` entre le 01/01/2000 et maintenant + 1 jour.
- **Règles pures** (`format_tracking_number`, `is_imprecise`) dans `reports/rules.py` ; un test d'architecture exige `@transactional` sur toute fonction publique d'un `service.py`.

## Spec Change Log

## Review Triage Log

Passe 1 (25/11/2026). Couches : Blind Hunter (B), Edge Case Hunter (E), Verification Gap (V). CI du premier commit verte (dont l'envoi d'un Signalement à travers Caddy et l'audit de `python-multipart`).

| # | Constat | Verdict | Preuve | Route |
|---|---|---|---|---|
| B1 / E3 / E4 / E11 | Corps multipart lu (et écrit sur disque) avant tout contrôle ; sans `X-Device-Id`, un corps malformé donne 400 `validation_error` | high | FastAPI lit le formulaire avant les dépendances ; aucune limite dans Caddy | patch (limite Caddy 2 Mo + contrôle avant lecture du corps) |
| B2 | Le démarrage valide le pepper d'un objet de réglages, les requêtes en lisent un autre | medium | `app.state.settings` contre `get_settings()` ; clé redécodée à chaque requête | patch |
| B5 | Zone du Signalement et Zone de l'Organisation choisies par deux requêtes d'ordre différent | medium | `zone_of` et `zones_covering` trient différemment | patch (une seule requête) |
| E5 | Mois ou année de la clé de photo et `received_at` lus par deux appels à l'horloge | low | Deux `clock.now()` ; correction directe | patch |
| B6 / E9 | Pas d'index sur `reports.zone_id` ni pour la file de modération ; Organisation plateforme suspendable | medium | Migration 0003 | patch |
| B13 / E8 | Commentaire vide stocké tel quel ; `captured_at` sans bornes | low | Aucune normalisation ; dates proches de l'an 1 ou 9999 | patch |
| B9 | Contrat d'erreur absent de l'OpenAPI et du README | medium | `responses=` absent ; la story 1.13 génère le client depuis l'OpenAPI | patch |
| B3 / E7 | README faux sur le pepper en `dev` ; empreintes qui changent à chaque redémarrage en `dev` | low | Le contrôle de démarrage vaut pour tous les ENV | patch (documentation) |
| B8 | Docstring de `principal()` contraire à la priorité 400 avant 401 | low | Test qui fixe l'ordre inverse de la docstring | patch |
| B12 | Messages français du backend différents de `fr.json` | low | `invalid_device_id`, `outside_active_zone` | patch |
| B10 | Le Signalement du test de bout en bout reste en base ; `is_demo` non vérifié | low | Ligne permanente | patch (vérifier `is_demo`, documenter le retrait par `demo purge`) |
| V1 / V2 / V3 | Non testés : arrondissement prioritaire sur la ville ; plus ancienne Organisation éligible ; message `body` pour un JSON illisible | medium | Inverser le tri ne fait échouer aucun test | patch |
| B4 / E6 | Marge de 50 m côté PWA seulement : refus serveur dans la bande | low | Choix de la story 1.8 : la PWA tolère, le serveur tranche exactement | rejeté |
| E1 / B7 | Compteur saturé au millionième Signalement de l'année : erreur 500 | low | Volume hors de portée du pilote | rejeté |
| E2 | Renvoi du même `client_uuid` crée un doublon | low | Objet de la story 1.12 | rejeté (story 1.12) |
| B8b | `devices` sans `last_seen_at` | low | Colonnes fixées par les critères d'acceptation | rejeté |
| B11 | `wo.json` copie de `fr.json` | false | Interface wolof hors objectifs du hackathon | rejeté |
| E10 | Pas de `router.py` dans `orgs` | low | Couches facultatives dans le contrat `layers` ; aucune route `orgs` avant l'Epic 2 | rejeté |

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run lint-imports && REQUIRE_INTEGRATION=1 uv run pytest --cov` (backend, pile réelle ; base sur 127.0.0.1:55432, Garage sur 127.0.0.1:3900) — expected: vert.
- `npx vitest run src/i18n` (web) — expected: vert.
- `python -I scripts/ci/check_pinning.py && python -I scripts/ci/check_repo_hygiene.py` — expected: OK.
