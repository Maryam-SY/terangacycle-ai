---
title: 'Story 1.17 — Charger et retirer les Données de démonstration en une commande'
type: 'feature'
created: '2026-11-26'
status: 'ready-for-dev'
baseline_commit: 'd1ebcca5ccaa748d5bbf264ff8f9dcebd85e585d'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-11-recevoir-un-signalement-anonyme-et-attribuer-son-numero-de-suivi.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Pour présenter TerangaCycle, il faut une instance remplie de Signalements réalistes, rattachés à des communes. Aujourd'hui, la seule façon d'en créer est de les envoyer un par un, et rien ne permet de les retirer proprement, ni les lignes, ni les objets du bucket, ni les Organisations. Or un chiffre de démonstration ne doit jamais passer pour réel (FR-37, AD-14).

**Approach:** créer la commande `python -m app.cli demo load|purge`, refusée en `ENV=prod`. Chaque module propriétaire de données expose dans son service `load_demo(ctx)` et `purge_demo(ctx)`, et la commande les appelle dans un ordre déclaré dans une liste séparée (point d'extension pour les epics suivants). Le contenu couvre ce qui existe à la fin de l'Epic 1 :
- deux Organisations communes de démonstration ;
- au moins 20 Signalements `pending_review` créés par `reports.service.create_report`, avec leurs photos.

Les critères d'acceptation de référence sont ceux de la section `### Story 1.17` d'`_bmad-output/planning-artifacts/epics.md` (amendement v2.0 compris), à respecter intégralement.

## Boundaries & Constraints

**Always:**
- **Garde de l'environnement :**
  - `ENV=prod` : refus avant toute connexion, message explicite, code de sortie 1, rien de modifié ;
  - usage invalide : code 2 ;
  - en `dev` comme en `demo`, la commande force `demo_mode=True` dans ses propres réglages (`load_settings(demo_mode=True)`, permis hors prod), si bien que `core.demo.flag()` étiquette tout ce qu'elle crée.
- **Point d'extension :**
  - `app/cli/demo_steps.py` déclare `DEMO_STEPS`, une liste ordonnée de `DemoStep(name, load, purge)` ;
  - `load` les appelle dans l'ordre, `purge` à rebours ;
  - un epic suivant (comptes de test, autres Statuts) ajoute une ligne à cette liste, sans toucher `app/cli/demo.py` ;
  - `ctx` = `DemoContext(settings, seed_dir)` défini dans `core/demo.py`.
  - Étapes de l'Epic 1 : `orgs`, `auth` (purge seulement), `reports`.
- **`orgs.service.load_demo` :**
  - deux Organisations `commune`, `active`, `is_demo = true`, UUID fixes, insertion `ON CONFLICT (id) DO NOTHING` ;
  - rattachées aux communes d'arrondissement `grand-yoff` et `parcelles-assainies` (celles qui ont le plus de quartiers dans les données OSM) ;
  - noms suffixés « (démonstration) ».
- **`reports.service.load_demo` :**
  - manifeste `infra/seed/demo/reports.json` : 20 entrées, chacune avec un `client_uuid` fixe, `lat`, `lng`, `accuracy_m`, `heap_size`, `waste_type` facultatif, un commentaire fictif et un fichier photo ;
  - points dans 5 quartiers au moins (3 de Grand Yoff, 2 de Parcelles Assainies), espacés de plus de 100 m deux à deux, pour qu'aucun ne soit Doublon probable (story 1.14) ;
  - une photo distincte par entrée ;
  - chaque entrée passe par `create_report(demo_principal(), meta, read_photo, ctx.settings)` : mêmes contrôles, Numéro, Zone, Organisation responsable, `pending_review` ;
  - `consent = {terms: true, training: false}` : les photos de démonstration ne servent jamais au réentraînement ;
  - chaque Signalement a sa propre unité de travail : une interruption laisse un état que `load` complète et que `purge` retire.
- **Relance de `load` :**
  - `demo_principal()` (`core/demo.py`) a un `owner_key = device:<DEMO_DEVICE_HASH>` constant (SHA-256 d'une chaîne fixe, indépendant du pepper : il ne change ni entre instances ni avec des secrets éphémères) ;
  - les `client_uuid` sont fixes, donc une relance reçoit le renvoi idempotent (story 1.12) : aucun doublon ;
  - le résumé affiché distingue créés et déjà présents.
- **Étiquette héritée (AD-14) :**
  - `create_report` passe `parent_is_demo` à `core.demo.flag`, lu par un nouveau `orgs.service.organization_is_demo(id)` ;
  - un Signalement attribué à une Organisation de démonstration est donc toujours `is_demo`, même reçu hors Mode démonstration ;
  - ainsi, la purge ne peut pas laisser de Signalement réel pointer vers une Organisation retirée.
- **`demo purge` :**
  - rôle `teranga_migrator` : `MIGRATOR_DATABASE_URL` ou le secret `db_migrator_password`, sinon refus explicite (code 1). Le moteur est rebranché pour le processus par un nouveau `core.db.use_database_url()` ;
  - une seule unité de travail, avec suppression dans cet ordre :
    1. `report_photos` des Signalements `is_demo` ;
    2. `reports` `is_demo` ;
    3. la ligne `devices` de `DEMO_DEVICE_HASH` (`auth.service.purge_demo`) ;
    4. les `organizations` `is_demo` (jamais `type = 'platform'`).
  - objets `object_key` et `thumb_key` (si renseignée) retirés par `core.storage.purge()` après le commit ;
  - toute erreur annule tout (code 1, message sans donnée) ;
  - Zones, lignes non étiquetées, Organisation plateforme et compteurs de Numéros intacts.
- **Photos :**
  - dans `infra/seed/demo/`, JPEG ≤ 300 Ko, sans personne, sans plaque, sans EXIF ;
  - licences et sources listées dans `infra/seed/demo/LICENSES.md` ;
  - dossier lu via le nouveau réglage `DEMO_SEED_DIR` (par défaut `<dépôt>/infra/seed`) ;
  - monté en lecture seule dans le service Compose `cli`.
- **Compose :**
  - service `cli` (profil `cli`, même image, `entrypoint: ["python", "-m", "app.cli"]`, `restart: "no"`) ;
  - secrets : ceux de l'application plus `db_migrator_password` ;
  - volume `./seed:/srv/seed:ro`, `DEMO_SEED_DIR=/srv/seed` ;
  - usage : `docker compose --profile demo run --rm cli demo load`.
- **`is_demo` dans l'API :** un test d'architecture parcourt l'OpenAPI. Tout schéma de réponse qui expose un Signalement (il porte `tracking_number`) doit avoir `is_demo`.
- **Architecture :**
  - `app.cli` est une racine de composition (ajoutée à `allowed_importers` du contrat `protected`) ;
  - aucune flèche nouvelle entre modules ;
  - `core` n'importe aucun module.
- **Confidentialité :** journaux et sortie limités aux comptes et aux Numéros de suivi, jamais une Position ni `owner_key`.

**Never:**
- pas de comptes de test, d'autres Statuts, de Missions ni de Preuves (epics suivants, par `DEMO_STEPS`) ;
- pas d'écriture directe dans `reports` au chargement (tout passe par `create_report`) ;
- pas de suppression d'`audit_logs` (inexistant ici, exclu par AD-14) ;
- pas d'invite de confirmation interactive ;
- pas de migration (`is_demo` existe sur `reports` et `organizations`) ;
- aucun mock de base ni de Garage dans les tests d'intégration.

## I/O & Edge-Case Matrix

| Scénario | Entrée / état | Attendu |
|---|---|---|
| Chargement | Base migrée, `ENV=dev` sans `DEMO_MODE` | Code 0 ; 2 Organisations communes `is_demo` ; ≥ 20 Signalements `pending_review` `is_demo`, ≥ 5 quartiers, répartis entre les deux Organisations ; une photo stockée par Signalement |
| Relance | `load` deux fois | Mêmes nombres de lignes, d'objets et de Numéros ; résumé « 0 créé, 20 déjà présents » |
| Purge | Démo chargée, plus un Signalement non étiqueté | Lignes et objets de démonstration retirés (bucket compté avant et après) ; le non étiqueté, les Zones et l'Organisation plateforme restent |
| Purge sans démo | Rien de chargé | Code 0, rien de modifié |
| Production | `ENV=prod`, `load` ou `purge` | Code 1, message explicite, aucune connexion, rien de modifié |
| Rôle absent | `purge` sans URL ni secret du rôle de migration | Code 1, message ; rien de modifié |
| Hors démo | Signalement reçu par l'API, `DEMO_MODE` faux, dans une commune de démonstration | `is_demo` vrai (étiquette du parent) ; retiré par `purge` |
| Zone active différente | `ACTIVE_ZONE_ID` ≠ `dakar` | `load` s'arrête au premier refus `outside_active_zone`, code 1, message |
| Usage | `demo`, `demo foo`, sans argument | Code 2, aide |

**Décision (26/11/2026, validée par l'utilisatrice) :** les 20 photos de démonstration sont des images de remplacement générées par script (aucun téléchargement, aucune licence tierce), distinctes entre elles ; elles seront remplacées plus tard par des photos de l'équipe publiées en CC0. Le manifeste garde un emplacement pour la licence de chaque photo.

</frozen-after-approval>


## Code Map

- `backend/app/core/demo.py` : `flag(settings, parent_is_demo)`. Y ajouter `DemoContext`, `DEMO_DEVICE_HASH` et `demo_principal()` (Principal de `core.security`).
- `backend/app/core/config.py` : `env`, `demo_mode`, `_check_demo_mode` (refuse `demo_mode` en prod, d'où la garde explicite avant le chargement), `migrator_database_url`, `load_settings(**overrides)`, `MigratorSettings`. Ajouter `demo_seed_dir: Path | None = None`. `tests/unit/test_env_example.py` exige le réglage dans `.env.example`.
- `backend/app/core/db.py` : `get_engine`/`get_sessionmaker` (`lru_cache` sur `get_settings().database_url`). Ajouter `use_database_url(url: SecretStr)`, réservé aux commandes ponctuelles, qui remplace le moteur du processus.
- `backend/app/core/storage.py` : `purge(keys)` après commit. Une clé absente n'est pas une erreur, et `report_thumb/` est accepté si la story 1.18 est passée.
- `backend/app/modules/reports/service.py` : `create_report(principal, meta, read_photo, settings)` (verrou `client_uuid`, renvoi `replayed`). Ajouter `load_demo`, `purge_demo`, et `parent_is_demo` dans `demo.flag`. Ne pas changer l'ordre des contrôles.
- `backend/app/modules/reports/repository.py` : ajouter `demo_photo_keys()` et `delete_demo_reports()` (photos puis Signalements).
- `backend/app/modules/reports/schemas.py` : `ReportMeta` (construit depuis le manifeste), `ReportCreated` (porte déjà `is_demo`).
- `backend/app/modules/orgs/service.py`, `repository.py` : `PLATFORM_ORGANIZATION_ID`. Ajouter `load_demo`, `purge_demo` et `organization_is_demo`. Toutes les fonctions publiques d'un service sont `@transactional` (test d'architecture).
- `backend/app/modules/auth/service.py`, `repository.py` : ajouter `purge_demo` (supprime la ligne `devices` de `DEMO_DEVICE_HASH`).
- `backend/migrations/versions/0003_reports.py` : `ck_organizations_platform_is_system` (la plateforme n'est jamais `is_demo`), FK `reports → organizations`.
- `backend/migrations/data/zones-dakar.geojson` : identifiants `grand-yoff` (56 quartiers) et `parcelles-assainies` (20). Points du manifeste choisis à l'écriture (par exemple `ST_PointOnSurface`) et vérifiés par test avec `geo.zones_covering`.
- `backend/pyproject.toml` : `protected.allowed_importers`, à compléter par `app.cli` et `app.cli.**`. `backend/tests/architecture/test_import_contracts.py` (paquet témoin des racines de composition), à ajuster.
- `infra/docker-compose.yml` : `x-backend`, `x-app-secrets`, service `migrate` (modèle du service ponctuel). L'image ne contient pas `infra/`, d'où le montage.
- `backend/scripts/smoke_edge.py` : annonce déjà que `demo purge` retire son Signalement. Aucun changement.
- **Migration :** aucune (la tête reste `0004_reports_client_uuid_unique`).
- **Fichiers touchés (liste complète) :**
  - à créer : `backend/app/cli/__init__.py`, `backend/app/cli/__main__.py`, `backend/app/cli/demo.py`, `backend/app/cli/demo_steps.py`, `infra/seed/demo/reports.json`, `infra/seed/demo/LICENSES.md`, `infra/seed/demo/*.jpg` (20), `backend/tests/unit/test_cli_demo.py`, `backend/tests/integration/test_demo_data.py`, `backend/tests/architecture/test_demo_flag_in_schemas.py` ;
  - à supprimer : `infra/seed/.gitkeep` ;
  - à modifier : `backend/app/core/demo.py`, `backend/app/core/config.py`, `backend/app/core/db.py`, `backend/app/modules/reports/service.py`, `backend/app/modules/reports/repository.py`, `backend/app/modules/orgs/service.py`, `backend/app/modules/orgs/repository.py`, `backend/app/modules/auth/service.py`, `backend/app/modules/auth/repository.py`, `backend/pyproject.toml`, `backend/tests/architecture/test_import_contracts.py`, `backend/tests/conftest.py` (`DEMO_SEED_DIR` dans `_SETTINGS_ENV_VARS`), `infra/docker-compose.yml`, `.env.example`, `.github/workflows/ci.yml` (job `edge` : `load`, relance, `purge` par le service `cli`), `README.md` (section démo).

## Tasks & Acceptance

**Execution:**
- [ ] `backend/app/core/demo.py`, `config.py`, `db.py` : `DemoContext`, `demo_principal`, `DEMO_SEED_DIR`, `use_database_url`.
- [ ] `backend/app/cli/` : analyse des arguments, garde `ENV=prod`, réglages forcés en démo, rôle de migration pour `purge`, exécution ordonnée de `DEMO_STEPS`, résumé et codes de sortie.
- [ ] `backend/app/modules/orgs/`, `auth/`, `reports/` : `load_demo`, `purge_demo`, `organization_is_demo`, `parent_is_demo` dans `create_report`.
- [ ] `infra/seed/demo/` : manifeste, photos et licences (selon la réponse à la question ouverte).
- [ ] `infra/docker-compose.yml`, `.env.example`, `README.md`, `.github/workflows/ci.yml`, `backend/pyproject.toml` : service `cli`, réglage documenté, contrat d'import.
- [ ] **Tests :**
  - unitaires : garde prod (aucune connexion tentée), codes 1 et 2, ordre de `load` et ordre inverse de `purge` sur des étapes témoins, manifeste valide (20 entrées, `client_uuid` uniques, fichiers présents, chaque photo ≤ 300 Ko et sans EXIF, empreintes distinctes, espacement > 100 m) ;
  - intégration sur la pile réelle : chaque ligne de la matrice, avec relecture de la base et comptage du bucket ; quartiers et Organisations vérifiés par `zones_covering` ;
  - architecture : `is_demo` dans chaque schéma de Signalement de l'OpenAPI, contrat `protected`.

**Acceptance Criteria:**
- Tous les critères d'acceptation de la story 1.17 d'`epics.md`, amendement v2.0 compris, sont couverts par au moins un test qui tourne en CI.
- Étant donné le job `edge` de la CI, quand on lance `docker compose --profile demo run --rm cli demo load`, puis une relance, puis `demo purge`, alors les trois commandes réussissent, et `purge` retire aussi le Signalement du test de fumée.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run lint-imports && REQUIRE_INTEGRATION=1 uv run pytest --cov` (backend, pile Compose réelle) — expected: vert.
- `docker compose --profile demo run --rm cli demo load && docker compose --profile demo run --rm cli demo purge` — expected: code 0 deux fois ; `ENV=prod` → code 1.
- `python -I scripts/ci/check_pinning.py && python -I scripts/ci/check_repo_hygiene.py` — expected: OK.
