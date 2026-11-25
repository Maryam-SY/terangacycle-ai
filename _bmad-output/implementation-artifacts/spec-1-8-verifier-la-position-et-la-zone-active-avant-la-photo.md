---
title: 'Story 1.8 — Vérifier la Position et la Zone active avant la photo'
type: 'feature'
created: '2026-11-25'
status: 'done'
baseline_commit: '9372838ec080857b495c0bd9adb159a3177e082e'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-7-accueil-et-consentement-avant-la-premiere-capture.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** L'écran 2 · Capture est une page d'attente. Le Citoyen ne sait ni où il est ni si TerangaCycle est actif là où il se trouve. Il risque donc de photographier un dépôt pour rien. Le serveur n'a aucune Zone.

**Approach:** côté serveur :
- une table `zones` chargée par migration depuis un fichier OpenStreetMap versionné : Dakar, ses 19 communes d'arrondissement, et les quartiers que l'OSM dessine ;
- un module `core.geo` (`in_active_zone`, `zone_of`) ;
- la Zone active et le seuil de précision publiés par `GET /v1/config`.

Côté PWA, l'écran 2 :
- suit la Position en haute précision ;
- vérifie la Zone active sur le polygone simplifié, gardé dans Dexie ;
- ne permet la photo que si la Position est utilisable.

## Boundaries & Constraints

**Always:**
- **Source et licence des données :** OpenStreetMap, ODbL 1.0, « © les contributeurs d'OpenStreetMap ».
  - Les données viennent de l'extraction Overpass du 25/11/2026 : département de Dakar, relation 12982139.
  - Le fichier versionné et sa notice citent la source, la licence, la date de la base OSM, la requête et la commande de reconstruction.
- **Table `zones`, en lecture seule pour `teranga_app` :** la migration retire INSERT, UPDATE et DELETE, que les privilèges par défaut donnent sinon.
- **Hiérarchie des Zones :**
  - Dakar (ville, `kind=commune`, sans parent, identifiant `dakar`) ;
  - les 19 communes d'arrondissement (`commune`, parent Dakar) ;
  - les quartiers (`quartier`, parent = la commune qui contient leur point intérieur).
  - `zone_of` renvoie le quartier le plus petit qui couvre le point, sinon la plus petite commune.
- **Règles géographiques :** `ST_Covers` sur `geography` (limite incluse). La PWA juge sur le polygone simplifié avec une marge de 50 m, de façon tolérante ; le serveur reste l'autorité (422 à la story 1.11).
- **Démarrage de l'API :** l'API charge la Zone active une fois, au démarrage. Elle refuse de démarrer, avec le journal `startup_refused` et le code de sortie 1, si `ACTIVE_ZONE_ID` ne désigne aucune Zone ou si la base est injoignable.
- **Aucune coordonnée** dans la console, les journaux ni les messages d'erreur.
- **Textes et couleurs :**
  - tout texte passe par i18next, en `fr` et `wo` ;
  - couleurs par jetons ; l'invitation à patienter est en `warning-ink` sur `warning-bg`.

**Never:**
- pas de photo, de viseur ni de consigne « ni personne ni plaque » : c'est la story 1.9 ;
- pas de création de Signalement ni de refus 422 : c'est la story 1.11 ;
- pas de client OpenAPI généré : c'est la story 1.13. Un petit lecteur de `/v1/config` dans `web/src/api/` suffit ;
- pas de carte ni de tuiles ;
- pas de `fetch` hors de `src/api/` et `src/offline/` ;
- pas de donnée géographique de l'OSM brute versionnée.

## I/O & Edge-Case Matrix

| Scénario | Entrée / état | Comportement attendu |
|---|---|---|
| Position bonne | Dans la Zone, ± 12 m | « Position détectée, précision ± 12 m » ; déclencheur actif |
| Imprécise | Dans la Zone, ± 80 m | Invitation ambre et « Continuer quand même » ; déclencheur inactif tant qu'on n'a pas continué ou que la précision n'a pas atteint ≤ 50 m |
| Exactement 50 m | ± 50 m | Pas d'invitation |
| Hors Zone | Thiès | Message en Encre avec icône « TerangaCycle n'est pas encore actif ici » ; déclencheur inactif |
| Refus | Permission refusée ou position indisponible | Explication sans culpabiliser et bouton « Réessayer » ; déclencheur inactif |
| Hors ligne | Fetch en échec, configuration dans Dexie | Configuration gardée utilisée |
| Première fois hors ligne | Fetch en échec, Dexie vide | Message « connexion nécessaire une première fois » et « Réessayer » ; déclencheur inactif |
| Limite | Point sur la limite de Dakar | Serveur : dans la Zone |

</frozen-after-approval>

## Code Map

- **Données brutes (hors dépôt) :** `C:\Users\merie\AppData\Local\Temp\claude\bcb25121a63c1030\48ed9e5a-aae8-4b1d-bc0e-88ef99aca601\scratchpad\osm\dakar-osm.json`.
  - Sortie Overpass `out geom`, base OSM `2026-11-25T14:30:28Z`, 142 éléments.
  - Contenu : la relation 12982139, 19 relations `admin_level=8`, des voies et relations `place=suburb|quarter|neighbourhood`, et des `admin_level` 9 et 10.
  - Requête : `rel(12982139);map_to_area->.a;(rel(12982139);rel(area.a)["boundary"="administrative"]["admin_level"~"^(8|9|10)$"];rel(area.a)["place"~"^(suburb|quarter|neighbourhood)$"];way(area.a)["place"~"^(suburb|quarter|neighbourhood)$"];way(area.a)["boundary"="administrative"]["admin_level"~"^(9|10)$"];);out geom;`
- `backend/app/core/config.py` : `Settings`. Ajouter `active_zone_id` (défaut `dakar`, non vide) et `report_accuracy_flag_m` (entier ≥ 1, défaut 50).
- `backend/app/core/public.py` : `PublicConfig` et la route. Les champs s'ajoutent sans changer la route ; la liste blanche est déjà dans `core/access.py:62`.
- `backend/app/main.py` : `create_app()`. Pas encore de lifespan ; uvicorn utilise la fabrique.
- `backend/app/core/db.py` : `Base`, `get_engine()`, `unit_of_work()` et `current_session()`.
- `backend/migrations/versions/0001_baseline.py` : base vide. Le Dockerfile copie `migrations/` et `app/`.
- `infra/db/initdb/20-roles.sh` : les privilèges par défaut donnent le DML à `teranga_app` (d'où le REVOKE).
- `backend/app/core/enums.py` : les énumérations uniques. Ajouter `ZoneKind`.
- **Tests backend :** `backend/tests/asgi.py` ne lance pas le lifespan. Les tests unitaires posent `app.state.active_zone`. Les tests d'intégration (`tests/integration/`, PostGIS réel, `REQUIRE_INTEGRATION=1` en CI) suivent `test_db_roles.py`.
- `backend/scripts/smoke_edge.py` : vérifie `/v1/config`. Étendre aux nouveaux champs.
- **PWA :**
  - `web/src/features/report/CapturePage.tsx` : page provisoire à remplacer, en gardant la garde de consentement et `useFocusOnMount` ;
  - `web/src/offline/db.ts` : ajouter `publicConfig` à `MetaKey` ;
  - `web/src/api/` : vide ;
  - `web/src/ui/icons.tsx`, `web/src/theme/contrast-pairs.json`, `web/src/i18n/{fr,wo}.json`, `web/e2e/consent.spec.ts` (modèle des tests e2e), `web/playwright.config.ts`.

## Tasks & Acceptance

**Execution:**
- [x] `backend/scripts/build_zones.py` et `backend/migrations/data/zones-dakar.geojson`, avec la notice `backend/migrations/data/README.md` :
  - le script transforme la sortie Overpass en GeoJSON : anneaux assemblés, polygones invalides écartés, simplification d'environ 3 m, 6 décimales ;
  - propriétés : `id` (identifiant lisible et unique), `name`, `kind`, `parent_id`, `osm_ref` ;
  - le fichier visé fait au plus 400 Ko.
- [x] `backend/migrations/versions/0002_zones.py` :
  - crée `zones` (`id` texte en clé, `name`, `kind` avec CHECK, `parent_id` clé étrangère, `osm_ref`, `geog GEOGRAPHY(MultiPolygon,4326) NOT NULL`, index GiST) ;
  - charge le fichier et révoque le DML de `teranga_app` ;
  - le downgrade supprime la table.
- [x] `backend/app/core/geo.py` :
  - `in_active_zone(session, lat, lng)` ;
  - `zone_of(session, lat, lng)` ;
  - `load_active_zone(session, zone_id)` : identifiant, nom, GeoJSON simplifié et élargi de 50 m.
- [x] `backend/app/core/config.py`, `public.py` et `main.py` : les réglages ; `PublicConfig.active_zone` et `report_accuracy_flag_m` ; un lifespan qui charge la Zone active ou refuse le démarrage.
- [x] **Tests backend :**
  - unitaires : réglages et forme de `/v1/config` ;
  - intégration : Plateau → quartier ou commune, Thiès hors Zone, sommet de la limite dans la Zone, `teranga_app` sans INSERT ni UPDATE ni DELETE, refus de démarrer sur une Zone inconnue ;
  - `smoke_edge.py` étendu.
- [x] `web/src/api/config.ts` (lecture et validation de `/v1/config`) et `web/src/offline/publicConfig.ts` : réseau d'abord, puis Dexie `meta.publicConfig`.
- [x] `web/src/features/report/{geo.ts,usePosition.ts,CapturePage.tsx}` :
  - `geo.ts` : point dans un MultiPolygon, limite incluse ;
  - `usePosition.ts` : `watchPosition` en haute précision, nettoyage au démontage, Réessayer ;
  - `CapturePage.tsx` : les états de la matrice ; le déclencheur « Prendre la photo » est rendu mais ne fait que signaler que la photo arrive à l'étape suivante.
- [x] **Tests PWA :**
  - Vitest pour `geo.ts`, la configuration hors ligne et les seuils ;
  - Playwright pour chaque ligne de la matrice : géolocalisation simulée, `/v1/config` intercepté, axe sans violation, aucune coordonnée en console.

**Acceptance Criteria:**
- Étant donné une base migrée, quand on liste `zones`, alors Dakar et 19 communes existent, et chaque quartier a une commune pour parent.
- Étant donné `ACTIVE_ZONE_ID=inexistante`, quand l'API démarre, alors elle s'arrête avec le code 1 et `startup_refused`.
- Étant donné un Visiteur sans en-tête, quand il appelle `GET /v1/config`, alors il reçoit `active_zone` (`id`, `name`, `geometry` GeoJSON MultiPolygon) et `report_accuracy_flag_m: 50`, et le test de la table des routes passe.

## Implementation Notes

- **Données.** `build_zones.py` (bibliothèque standard) : 19 communes, 101 quartiers, 21 éléments écartés (3 sans nom, 17 voies ouvertes de niveau 9/10, « Cité du Golf » hors de Dakar), 97,9 Ko. Simplification par voie avant assemblage : deux Zones voisines gardent la même limite. Homonymes suffixés par leur référence OSM. La migration vérifie `ST_IsValid` (bloc `DO`) et reste rendable en `--sql`.
- **Zone publiée.** `ST_Buffer(geog, 50)` puis `ST_SimplifyPreserveTopology` à 0,0001° (~11 m) : 317 points, ~7 Ko ; elle couvre la Zone exacte à plat (`geometry`). Sur `geography`, `ST_Covers` peut dire faux à cause des arcs géodésiques : le test compare à plat, comme la PWA.
- **Code de sortie 1.** uvicorn transforme l'échec d'un lifespan en code 3 : le lifespan journalise `startup_refused` puis appelle `os._exit(1)` (rien n'est encore servi). Vérifié sur un vrai processus uvicorn (base injoignable, Zone inconnue).
- **Journaux.** `hide_parameters=True` sur le moteur de l'API et celui du démarrage : aucune valeur liée (Position) dans un message d'erreur. Raison du refus : type de l'exception seulement.
- **PWA.** La marge de 50 m est dans le polygone publié ; la PWA juge à plat, limite incluse (`multiPolygonCovers`). Décision pure dans `capture.ts`. Précision affichée arrondie vers le haut (50,2 m → « ± 51 m », avec invitation). Une mesure manquée ne fait pas oublier la dernière Position ; seul un refus l'efface. Déclencheur `disabled` décrit par la phrase d'état (`aria-describedby`).
- **Après relecture.** Configuration gardée servie tout de suite, réseau en arrière-plan (au lieu de « réseau d'abord », qui faisait attendre jusqu'à 8 s) ; délai par AbortController. Position gardée après une mesure manquée seulement si elle a moins de 60 s. « Continuer quand même » oublié hors Zone, après une erreur et après « Réessayer ». Région annoncée réduite à une phrase par type d'état. Serveur : `InvalidPositionError`, raisons de refus par SQLSTATE (42P01, 42501), `statement_timeout` au démarrage, seuil ≤ 1000 m ; `build_zones.py` s'arrête si une commune est écartée.
- **consent.spec.ts.** La capture demande désormais la géolocalisation après acceptation : l'assertion « aucun appel » de ce test devient « `watchPosition`, jamais l'appareil photo ».
- **Non exécuté en local.** Les 25 tests Playwright n'ont tourné qu'en `--list` (pas de Chromium) ; écran vérifié à la main dans le navigateur intégré (états imprécis, bon, hors Zone, refus). `test_ci_scripts.py` n'a pas tourné dans le conteneur uv (pas de `git`) ; les scripts `check_pinning.py` et `check_repo_hygiene.py` passent sur l'hôte.

## Spec Change Log

## Review Triage Log

Passe 1 (25/11/2026). Couches : Blind Hunter (B), Edge Case Hunter (E), Verification Gap (V).

| # | Constat | Verdict | Preuve | Route |
|---|---|---|---|---|
| B5 / E7 | « Continuer quand même » n'est jamais réinitialisé | medium | `continuedAnyway` reste vrai après « Réessayer » ou une sortie de Zone | patch (P1) |
| B6 / E8 / V1 | Une Position périmée garde la photo permise indéfiniment ; branche « mesure puis échec » non testée | medium | `usePosition` garde le dernier point sur toute erreur hors refus, sans âge | patch (P2) |
| V2 | Options haute précision jamais vérifiées | medium | `WATCH_OPTIONS` peut disparaître sans qu'aucun test ne rougisse | patch (P2) |
| B4 | La zone `role="status"` relit la précision à chaque mesure | medium | Tout le bloc `Status` est dans la région live, et `watchPosition` met à jour environ chaque seconde | patch (P3) |
| B8 / V3 | Réseau d'abord : jusqu'à 8 s d'attente à chaque visite sur un réseau lent ; options du `fetch` non vérifiées (`objectContaining({})`) | medium | `loadPublicConfig` attend le `fetch` avant le cache | patch (P4) |
| E5 | `AbortSignal.timeout` absent des navigateurs anciens : tout `fetch` lève | low | Chrome < 103, Safari < 16 ; repli direct avec `AbortController` | patch (P4) |
| B2 / E1 | `core.geo` accepte NaN, infini ou hors bornes : erreur PostgreSQL brute | medium | Le cast `::geography` lève une `DataError` ; la story 1.11 passera des coordonnées client | patch (P5) |
| B3 | Refus de démarrer : table absente ou droit manquant confondus avec « base injoignable » | low | `except Exception` générique ; SQLSTATE disponible sans message du pilote | patch (P5) |
| E4 | Démarrage bloqué indéfiniment si la requête attend un verrou | low | Seul `connect_timeout` est borné ; correction d'une option | patch (P5) |
| B13 | `REPORT_ACCURACY_FLAG_M` sans borne haute | low | `ge=1` seulement ; correction directe `le=1000` | patch (P5) |
| E11 | `build_zones.py` écrit le fichier si une commune est écartée, contrairement à sa docstring | low | Commune invalide seulement journalisée, sortie 0 | patch (P6) |
| E16 | uvicorn qui ne s'arrête pas en 15 s : processus orphelin dans le test | low | `communicate(timeout=15)` sans `kill` | patch (P6) |
| B14 | Contrôle de fuite de coordonnées étroit | low | Motif décimal seulement ; aucune vérification des requêtes sortantes | patch (P7) |
| E17 | axe absent de plusieurs états de la matrice | low | `expectNoSeriousViolations` dans 5 tests seulement | patch (P7) |
| B1 / E2 | `in_active_zone` lit `get_settings()`, la route lit `app.state.settings` | low | En production, les deux lisent le même environnement ; la story 1.11 décidera de l'appel | rejeté |
| E3 | `/v1/config` sans lifespan : erreur 500 | false | uvicorn exécute toujours le lifespan ; les tests posent `app.state.active_zone` | rejeté |
| B7 | `parsePublicConfig` strict sur `env` et `model_version` | low | Énumération fermée et contrat versionné ; le client généré (story 1.13) le remplacera | rejeté |
| B9 / E12 | Anneaux non vérifiés entre eux à la construction | low | Échec bruyant à la migration (`ST_IsValid`) et dans les tests d'intégration | rejeté |
| B10 | `wo.json` identique à `fr.json` | false | Choix voulu : l'interface wolof est un non-objectif du hackathon (NFR-P3) ; seules les clés comptent (UX-DR-8) | rejeté |
| B11 | Fichier GeoJSON absent du diff | false | Exclu volontairement du diff de relecture (98 Ko de données) ; il sera committé | rejeté |
| B12 | `ST_Area` recalculé à chaque appel | low | 121 lignes, coût négligeable | rejeté |
| E6 | Précision NaN ou infinie | low | Les navigateurs renvoient une précision finie | rejeté |
| E9 | Navigateur sans géolocalisation : « Réessayer » inutile | low | Sans effet nuisible | rejeté |
| E10 | Nom sans caractère ASCII : identifiant vide | low | Toutes les Zones actuelles ont un nom latin ; contrainte `id_not_blank` en garde | rejeté |
| E13 | Repli sans simplification : limites voisines différentes | low | Écart de quelques mètres, sans effet sur `zone_of` | rejeté |
| E14 | Migration sans rôle `teranga_app` | false | Le rôle est toujours créé par `20-roles.sh` (pile et CI) | rejeté |
| E15 | `smoke_edge.py` : trace Python sur une réponse malformée | low | Le script échoue quand même (code non nul) | rejeté |
| V-autre | `hide_parameters` non testé | low | Aucun appel avec Position avant la story 1.11 | rejeté (story 1.11) |

## Design Notes

**Marge de 50 m côté PWA :** la simplification rogne les bords. Une Position juste à l'intérieur ne doit pas être bloquée par erreur. Le serveur tranche exactement (story 1.11).

**Quartiers :** ils sont partiels dans l'OSM, d'où le repli sur la commune. Deux quartiers qui se chevauchent : le plus petit l'emporte.

## Verification

**Commands:**
- `uv run ruff check . && uv run pytest` (backend, pile Compose réelle) — expected: vert.
- `npm run lint && npm test && npm run build && npm run size && npx playwright test` (web) — expected: vert.
- `python -I scripts/ci/check_pinning.py && python -I scripts/ci/check_repo_hygiene.py` — expected: OK.
