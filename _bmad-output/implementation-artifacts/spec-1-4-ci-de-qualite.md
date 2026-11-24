---
title: 'Story 1.4 — CI de qualité'
type: 'chore'
created: '2026-11-24'
status: 'done'
baseline_commit: '7e02ebc0a3a3675c422701f4200c76854e76234b'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/deferred-work.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problème :** aucune vérification ne tourne sur GitHub. Les tests d'intégration sont ignorés en silence sans base, les tests web ne tournent jamais avant la construction, et rien n'empêche un module d'importer le repository d'un autre.

**Approche :** un workflow `.github/workflows/ci.yml` sur chaque pull request vers `main` et chaque push sur `main`, avec trois jobs :
- **backend** : ruff (lint et format), `lint-imports`, pytest avec couverture d'au moins 60 %, sur la pile réelle démarrée par Docker Compose ;
- **web** : lint, Vitest, construction ;
- **edge** : construction de l'image Caddy et `smoke_edge.py`.

Trois contrats import-linter : `layers`, `acyclic_siblings` et `protected`.

Le lint web reste **oxlint** (choisi en story 1.3) : la règle « pas de `fetch` hors de `web/src/api/` et `web/src/offline/` » y est posée par `no-restricted-globals`, l'équivalent de la règle ESLint d'AD-11.

## Boundaries & Constraints

**Toujours :**
- Chaque action GitHub est épinglée par SHA de commit, avec le tag en commentaire :
  - `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` (v7.0.1) ;
  - `astral-sh/setup-uv@1db35dd8eee11c5894872e0b383ae6c406cf738d` (v10.4.0) ;
  - `actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1` (v7.1.0).
- Node 26 et Python 3.12, comme en local.
- Les tests d'intégration **échouent** au lieu d'être ignorés quand l'environnement `REQUIRE_INTEGRATION=1` est posé sans base configurée. La CI le pose.
- Les secrets de la CI sont générés par `infra/gen-dev-secrets.py`, jamais stockés dans GitHub.
- `permissions: contents: read` au niveau du workflow.
- Dépendances ajoutées et épinglées : `pytest-cov==7.1.0`.

**Jamais :**
- Pas de Gitleaks, pip-audit, npm audit ni Trivy (story 1.5 : hygiène du dépôt).
- Pas de diff OpenAPI ni de test route × rôle (story 1.6 et story 2.5).
- Aucun secret GitHub requis.

## I/O & Edge-Case Matrix

| Scénario | Entrée / État | Résultat attendu | Erreurs |
|---|---|---|---|
| PR saine | Pull request vers `main`, code actuel | Les 3 jobs sont verts | — |
| Import interdit | Paquet témoin dont un module importe `app.modules.<autre>.repository` | `lint-imports` échoue (test d'architecture) | — |
| Dépôt réel | `lint-imports` sur `backend/` | Les 3 contrats passent | — |
| `fetch` interdit | `fetch()` dans `web/src/features/x.ts` | Le lint web échoue | Autorisé dans `src/api/` et `src/offline/` |
| Couverture | Couverture backend < 60 % | Le job backend échoue | — |
| Intégration sans base | `REQUIRE_INTEGRATION=1`, pas de `TEST_*_DATABASE_URL` | Les tests d'intégration échouent (pas de skip) | Sans la variable : skip comme avant |
| Tests web cassés | Clé ajoutée à `fr.json` seulement | Le job web échoue | — |

**Décision de Mia (24/11/2026) — protection de `main` :**
- activer la protection de branche avec les contrôles `backend`, `web` et `edge` obligatoires, sans l'imposer aux administrateurs ;
- la fusion locale signée `noreply` reste possible, et n'a lieu qu'une fois la CI verte ;
- la protection est activée par Mia, ou en son nom après son accord, une fois la CI verte sur la PR de cette story ;
- la story fournit la commande `gh api` correspondante dans le README.

</frozen-after-approval>

## Code Map

- `backend/pyproject.toml` :
  - dépendances de développement : pytest 9.2.0, ruff 0.17.6, import-linter 2.17 ;
  - pytest : `testpaths = ["tests"]`, marqueur `integration` ;
  - ruff configuré.
- `backend/tests/integration/test_db_roles.py` : `_engine_from_env` appelle `pytest.skip` si la variable manque. Ajouter la règle `REQUIRE_INTEGRATION` au même endroit, ou dans `tests/conftest.py`.
- `backend/tests/architecture/test_no_tx_calls.py` : modèle de test d'architecture.
- Modules : `backend/app/modules/{auth,reports,missions,lots,analytics,ai,notifications}`, sans `router`, `service` ni `repository` pour l'instant. `core` ne doit importer aucun module.
- Flèches autorisées par l'épine (AD-1) :
  - `missions` → `reports`, `auth` ;
  - `reports` → `ai`, `auth` ;
  - `lots` → `missions`, `auth` ;
  - `notifications` → `auth` ;
  - `analytics` → aucun module ;
  - `app.main`, `app.worker` et `app.reactions` sont des racines de composition, exclues des contrats.
- `web/package.json` : `lint` = `oxlint`, `test` = `vitest run`. `web/.oxlintrc.json` existe.
- Démarrage de la pile : `python infra/gen-dev-secrets.py && docker compose --profile demo up -d --build --wait`. URL de test : voir le README (port `DB_LOCAL_PORT`). Les ports par défaut 80, 443 et 5432 sont libres sur `ubuntu-latest`.
- `backend/scripts/smoke_edge.py` : bibliothèque standard seulement ; lit `.env` et les variables `HTTP_PORT` et `HTTPS_PORT`.

## Tasks & Acceptance

**Exécution :**
- [ ] `backend/pyproject.toml` (+ `uv.lock`) :
  - ajouter `pytest-cov==7.1.0` ;
  - `[tool.coverage.run] source = ["app"]` et `[tool.coverage.report] fail_under = 60` ;
  - `[tool.importlinter]` avec `root_package = "app"` et 3 contrats : `layers` (`router` → `service` → `repository`, déclaré pour les 7 modules, conteneurs ignorés s'ils sont absents), `acyclic_siblings` sur `app.modules`, `protected` (seul `.service` est importable entre modules, selon les flèches ci-dessus ; `app.core` interdit d'importer `app.modules`).
- [ ] `backend/tests/conftest.py` : avec `REQUIRE_INTEGRATION=1`, le skip d'un test `integration` devient un échec.
- [ ] `backend/tests/architecture/test_import_contracts.py` :
  - copie d'un paquet témoin minimal (`tmp_path`) dont `missions.service` importe `reports.repository` : `lint-imports --config <témoin>` échoue avec le contrat `protected` ;
  - le dépôt réel passe (`lint-imports` à la racine du backend).
- [ ] `web/.oxlintrc.json` : `no-restricted-globals` sur `fetch` en erreur, avec une exception (`overrides`) pour `src/api/**` et `src/offline/**`. Script `web/scripts/check-lint-rule.mjs`, ou test Vitest, qui lance oxlint sur un fichier témoin hors de `api/` et constate l'erreur.
- [ ] `.github/workflows/ci.yml` (supprimer `.gitkeep`) :
  - déclencheurs `pull_request` vers `main` et `push` sur `main` ; `concurrency` qui annule les exécutions obsolètes ;
  - **backend** : setup-uv, `uv sync --frozen`, `ruff check`, `ruff format --check`, `lint-imports` ; puis secrets générés, pile démarrée (`up -d --build --wait`), `REQUIRE_INTEGRATION=1`, URL de test depuis `.env.secrets/`, `pytest --cov` ; `docker compose logs` si échec ; `down -v` toujours ;
  - **web** : setup-node 26, `npm ci`, `npm run lint`, `npm test`, `npm run build` ;
  - **edge** (après backend et web) : pile démarrée, `python backend/scripts/smoke_edge.py` et `python backend/scripts/smoke_readyz.py`.
- [ ] `README.md` : section « Intégration continue » (ce qui tourne, comment le reproduire en local, et la commande `gh api -X PUT repos/<owner>/<repo>/branches/main/protection …` qui rend `backend`, `web` et `edge` obligatoires sans `enforce_admins`).
- [ ] `_bmad-output/implementation-artifacts/deferred-work.md` : ne pas modifier. Les trois entrées concernées seront marquées traitées par l'étape de revue.

**Critères d'acceptation :**
- Étant donné une PR vers `main`, quand la CI s'exécute sur GitHub, alors les jobs `backend`, `web` et `edge` sont verts sur le code actuel.
- Étant donné le dépôt, quand on lance localement `uv run lint-imports` et `uv run pytest --cov`, alors les contrats passent et la couverture est d'au moins 60 %.

## Implementation Notes

## Spec Change Log

## Review Triage Log

Passe 1 (24/11/2026). Couches : Blind Hunter (B), Edge Case Hunter (E), Verification Gap (V).

| # | Constat | Verdict | Preuve | Route |
|---|---|---|---|---|
| B1 | `uv sync --frozen` ne détecte pas un `uv.lock` périmé | medium | `--frozen` installe sans vérifier la cohérence avec `pyproject.toml` ; la CI resterait verte | patch (P1) |
| B2 / E1 | Les pushes successifs sur `main` s'annulent | medium | `cancel-in-progress: true` pour tous les évènements | patch (P2) |
| B3 / V-autre / E11 | `window.fetch`, `globalThis.fetch` et `self.fetch` échappent à la règle | medium | `no-restricted-globals` ne vise que l'identifiant nu `fetch` | patch (P3) |
| B4 | Le job `edge` reconstruit et redémarre toute la pile | low | Coût de temps seulement | rejeté |
| B5 / E8 | `test_require_integration` code en dur « 6 errors » | low | Casse dès qu'un test d'intégration est ajouté ; correction directe | patch (P4) |
| B6 / E5 | Saut à la collecte et zéro test d'intégration passent sous `REQUIRE_INTEGRATION=1` | medium | Le hook ne lit que les rapports d'exécution | patch (P5) |
| E6 | Test placé sous `tests/integration` sans le marqueur | low | Correction directe (critère de chemin) | patch (P5) |
| E4 | `REQUIRE_INTEGRATION=true` ou `yes` non reconnus | low | Correction directe | patch (P5) |
| E7 | Un saut volontaire (marqueur `skip`) deviendrait un échec | low | Aucun n'existe ; peut être ajouté le jour où il sert | rejeté |
| B7 / E10 | Un nouveau module échappe au contrat `layers` | medium | Les `containers` sont listés à la main, sans lien avec `app/modules` | patch (P6) |
| B8 / V1 | Une seule des flèches autorisées est testée ; une faute de frappe passe | medium | `unmatched_ignore_imports_alerting = "none"`, un seul témoin de flèche autorisée | patch (P7) |
| E9 | Retours à la ligne de `rich` selon `COLUMNS` | low | Reproduit avec `COLUMNS=40` ; correction directe | patch (P7) |
| B9 | Protection : champ `contexts` historique, conséquence de `strict: false` non dite | low | N'importe quelle intégration peut satisfaire un statut nommé `backend` | patch (P8) |
| E12 | `strict: false` permet une fusion sur une base périmée | low | La fusion locale part toujours du `main` à jour ; documenté | patch (P8, documentation) |
| B11 | La reproduction locale du job `edge` diffère de la CI | low | `--wait-timeout`, `python3` et `down -v` absents ; correction directe | patch (P8) |
| E3 | `DB_NAME` codé en dur dans les URL de test de la CI | low | Correction directe | patch (P1) |
| E2 | `DB_LOCAL_PORT` entre guillemets ou en double dans `.env` | low | `.env` est copié de `.env.example` en CI | rejeté |
| B10 | Pas de Dependabot pour les actions épinglées | low | Prévu par la story 1.5 (hygiène du dépôt) | rejeté (story 1.5) |
| B12 | Couverture sans artefact ni mesure des branches | low | Le seuil est visible dans le journal | rejeté |
| V2 | Seuil de couverture sans test témoin | low | Couverture actuelle de 94 % ; l'effet du réglage est visible dans chaque journal | rejeté |

## Design Notes

**Pile réelle en CI plutôt que des services GitHub.** Les « services » d'un job GitHub Actions ne savent ni lancer `--single-node` pour Garage, ni monter les scripts d'initialisation. Démarrer la même pile Docker Compose qu'en local garantit que la CI teste exactement ce qui tourne en démo.

**Contrats sans `router`, `service` ni `repository` réels.** Les modules sont encore vides : les contrats sont déclarés avec `ignore_missing` (ou un équivalent), pour être vrais dès maintenant et se resserrer automatiquement à mesure que les stories ajoutent les couches.

## Verification

**Commandes :**
- Dans le conteneur uv : `uv sync --frozen && uv run lint-imports && uv run pytest --cov -q` (pile démarrée, `REQUIRE_INTEGRATION=1` et URL de test posées) — attendu : succès, couverture d'au moins 60 %.
- Dans le conteneur Node 26 : `npm ci && npm run lint && npm test && npm run build` — attendu : succès.
- Sur GitHub : pousser la branche et ouvrir la PR — attendu : `backend`, `web` et `edge` verts.
