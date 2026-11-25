---
title: 'Story 1.6 — Contrôles de contrat en CI'
type: 'chore'
created: '2026-11-25'
status: 'done'
baseline_commit: '294c384414a5f669433cdee87fa7be53fe6874c2'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problème :** rien n'empêche une story d'ajouter une couleur illisible, un code d'erreur sans message traduit, ou une route sans politique d'accès.

**Approche :** trois contrôles, tous exécutés par les jobs existants (`web` et `backend`) :
1. **Contraste :** les paires texte/fond sont déclarées à côté de `theme.css` ; un test calcule leur rapport WCAG depuis les jetons.
2. **Messages d'erreur :** un test backend exige une clé `errors.<code>` dans `fr.json` et `wo.json` pour chaque `ErrorCode`.
3. **Routes :** une table des politiques d'accès dans `core` ; un test d'architecture parcourt les routes de `create_app()` et échoue pour toute route ni publique (liste blanche close) ni déclarée.

## Boundaries & Constraints

**Toujours :**
- **Seuils WCAG 2.1 AA :**
  - 4,5:1 pour le texte normal ;
  - 3:1 pour le texte large (≥ 18,66 px gras ou ≥ 24 px) et pour les éléments non textuels.
- **Calcul :** luminance relative sRGB, formule WCAG, sur les valeurs lues dans `theme.css`. Aucune couleur recopiée dans le test.
- **Liste blanche publique fermée**, exactement : `GET /healthz`, `GET /readyz`, `GET /v1/config`, `POST /v1/reports`, `GET /v1/public/map`. Les deux dernières routes n'existent pas encore : elles restent réservées, et leur absence n'est pas une erreur.
- **Politiques d'accès** : `device` (principal appareil), `roles:{…}` (rôles du Glossaire) ou `internal` (jamais exposée par Caddy, par exemple `/metrics`). La documentation de FastAPI (`/docs`, `/redoc`, `/openapi.json`, `/docs/oauth2-redirect`) est exemptée à part, puisqu'elle est coupée en `prod`.
- **Messages d'erreur :** en français simple, ils disent quoi faire (ton du PRD §7). `wo.json` reçoit les mêmes clés, avec des valeurs françaises en attendant la traduction.

**Jamais :**
- Aucune authentification réelle (story 2.x). La table déclare seulement la politique attendue.
- Pas de client d'API généré (story 1.13).
- Pas de nouvelle couleur.

## I/O & Edge-Case Matrix

| Scénario | Entrée / État | Résultat attendu | Erreurs |
|---|---|---|---|
| Paires réelles | `contrast-pairs.json` actuel | Toutes les paires au seuil | — |
| Témoin rouge | Paire `danger` en texte normal sur blanc (4,28:1) | Échec qui nomme la paire et son rapport | Le même rouge en `non-text` (≥ 3:1) passe |
| Jeton inconnu | Une paire cite `--color-inexistant` | Échec explicite | — |
| Code sans message | `ErrorCode` contient un code absent de `fr.json` | Échec qui nomme le code | — |
| Route non déclarée | Route témoin `GET /v1/secret` ajoutée sans politique | Échec qui nomme `GET /v1/secret` | — |
| Route publique hors liste | Route déclarée « publique » hors liste blanche | Échec | — |
| Politique orpheline | Politique déclarée pour une route qui n'existe pas | Échec (table à jour) | Sauf les entrées réservées de la liste blanche |

</frozen-after-approval>

## Code Map

- `web/src/theme/theme.css` : un seul bloc `@theme`. Couleurs :
  - `--color-brand-900` `#0B3D2E`, `--color-brand-600` `#187A50` ;
  - `--color-accent` `#F2B705`, `--color-mint` `#EAF3EC` ;
  - `--color-ink` `#14231C`, `--color-muted` `#5E7168`, `--color-line` `#D5E3D9`, `--color-surface` `#F6FAF7` ;
  - `--color-warning-ink` `#7A5C00`, `--color-warning-bg` `#FFF4CC`, `--color-danger` `#D9482B`.
  - Le blanc n'est pas un jeton : l'accepter comme valeur littérale `#FFFFFF` dans le fichier de paires.
- `web/src/i18n/{fr,wo}.json` : clés `app`, `home` et `notFound` ; aucune clé `errors`.
- `web/src/i18n/i18n.test.ts` : exige la parité des clés fr/wo et l'absence de couleur hors de `theme.css`. Le fichier de paires est en JSON et ne cite que des noms de jetons (et `#FFFFFF`) : vérifier qu'il ne déclenche pas la garde des couleurs, ou l'exempter nommément.
- `backend/app/core/errors/codes.py` : `ErrorCode` (`not_found`, `method_not_allowed`, `validation_error`, `internal_error`) et `DEFAULT_MESSAGES`.
- `backend/app/main.py` : `create_app()` inclut `health.router` (`/healthz`, `/readyz`, `/metrics`) et `public.router` (`GET /v1/config`).
- `backend/tests/architecture/` : modèle `test_no_tx_calls.py`. `backend/tests/asgi.py` et `conftest.py` savent construire l'application en environnement neutre.

## Tasks & Acceptance

**Exécution :**
- [x] `web/src/theme/contrast-pairs.json` : liste `{name, fg, bg, kind}` (`kind` vaut `text`, `large-text` ou `non-text`). Paires réelles :
  - texte : `ink`/`surface`, `ink`/`white`, `muted`/`surface`, `muted`/`white`, `brand-600`/`surface`, `brand-600`/`mint`, `white`/`brand-600`, `white`/`brand-900`, `brand-900`/`surface`, `warning-ink`/`warning-bg`, `ink`/`accent` ;
  - non textuel : `danger`/`white`, `danger`/`surface`, `brand-600`/`surface`.
- [x] `web/src/theme/contrast.ts` : `parseThemeColors(css)` et `contrastRatio(a, b)` (formule WCAG), plus une fonction de contrôle qui renvoie les paires en échec.
- [x] `web/src/theme/contrast.test.ts` (Vitest) :
  - les paires réelles passent ;
  - la paire témoin `danger` en `text` sur `#FFFFFF` échoue (rapport affiché entre 4,27 et 4,29) ;
  - la même paire en `non-text` passe ;
  - un jeton inconnu échoue ;
  - le rapport de `#187A50` sur blanc vaut 5,33 à 0,01 près.
- [x] `web/src/i18n/fr.json` et `wo.json` : bloc `errors` avec une clé par `ErrorCode`, rédigée pour l'utilisateur (par exemple `internal_error` : « Un problème est survenu de notre côté. Réessayez dans quelques instants. »).
- [x] `backend/tests/unit/test_error_messages.py` : pour chaque `ErrorCode`, `errors.<code>` existe et n'est pas vide dans `web/src/i18n/fr.json` et `wo.json`. Le message d'échec nomme le code et le fichier. Un cas témoin avec une énumération étendue échoue.
- [x] `backend/app/core/access.py` :
  - `PUBLIC_ROUTES` : `frozenset` des 5 couples `(méthode, chemin)` ;
  - `RESERVED_PUBLIC_ROUTES` : `POST /v1/reports`, `GET /v1/public/map` ;
  - `ROUTE_POLICIES` : `dict[(méthode, chemin), Policy]` ; `/metrics` → `internal`.
  - Aucune logique d'autorisation : c'est une déclaration.
- [x] `backend/tests/architecture/test_route_policies.py` :
  - parcourir `create_app().routes` (`APIRoute`, `Route` ; méthodes hors `HEAD` et `OPTIONS`, chemins gabarits) ;
  - échouer pour toute route ni dans `PUBLIC_ROUTES` ni dans `ROUTE_POLICIES` (documentation exemptée), en la nommant ;
  - échouer si `PUBLIC_ROUTES` contient autre chose que la liste close ;
  - échouer pour une politique orpheline, hors entrées réservées ;
  - cas témoin : une application avec `GET /v1/secret` non déclaré échoue en nommant la route.

**Critères d'acceptation :**
- Étant donné la PR, quand la CI tourne, alors les 5 jobs sont verts, avec les nouveaux tests dans `web` et `backend`.
- Étant donné la paire témoin rouge en texte normal sur blanc, quand le contrôle de contraste s'exécute, alors il échoue en la nommant.

## Implementation Notes

- **Rôles :** `Role` (`citizen`, `collector`, `recycler`, `moderator`, `municipal_admin`) ajouté à `core/enums.py` pour typer `roles:{…}` ; la story 2.5 s'y appuie sans le recréer.
- **`core/access.py` :** `Policy(kind, roles)` figé et validé (type hors `device`/`roles`/`internal` ou rôle hors `Role` → `ValueError`), constantes `DEVICE` et `INTERNAL`, fabrique `roles(...)`, et `DOCS_ROUTES` (exemption de la documentation, déclarée à côté de la table).
- **Parcours des routes :** FastAPI 0.165 garde chaque router inclus sous forme de `_IncludedRouter` dans `app.routes` ; le test les déplie avec `fastapi.routing.iter_route_contexts` (celui de la génération de l'OpenAPI) et les identifie par leur chemin gabarit (`path_format`, sans convertisseur). Échouent aussi : un type de route non pris en charge (`Mount`, WebSocket), une route sans méthode hors HEAD/OPTIONS (`HTTPEndpoint`), une route à la fois publique et déclarée, une entrée publique non réservée sans route. Les politiques `internal` sont confrontées au matcher `@internal path …` de `infra/Caddyfile`, et toute route de `/v1/ai` doit être `internal`.
- **Contraste :** jetons lus dans le seul bloc `@theme`, commentaires retirés ; valeur non hexadécimale (3 ou 6 chiffres) ou jeton redéclaré avec une autre valeur → erreur. Seule couleur littérale admise, `#FFFFFF` (« couleur littérale interdite » sinon). `contrast.ts` écrit le blanc en deux morceaux (garde de `i18n.test.ts` intacte, sans exemption) ; le JSON n'est pas parcouru par cette garde. Paires ajustées à l'interface : `surface/brand-600` (bouton de NotFoundPage) au lieu de `white/brand-600`, anneau de focus `brand-900` sur `surface` et `mint` (non textuel) ; la classe `text-danger` est interdite dans `src/`. Rapports les plus proches du seuil texte : `brand-600/mint` 4,70 et `muted/surface` 4,94 ; `danger/white` 4,28.
- **Vérification locale :** la politique Application Control de Windows bloque les DLL de `.venv` ; pytest a tourné dans `ghcr.io/astral-sh/uv:0.13.7-python3.12-trixie-slim`, la PWA dans l'image `node:26.13.1-trixie-slim` de `infra/caddy/Dockerfile`.

## Spec Change Log

## Review Triage Log

Passe 1 (25/11/2026). Couches : Blind Hunter (B), Edge Case Hunter (E), Verification Gap (V).

| # | Constat | Verdict | Preuve | Route |
|---|---|---|---|---|
| B4 / V1 / E4 | `Policy("public")`, `Policy("Device")` ou `roles("admin")` acceptés : contournement de la liste blanche | high | `PolicyKind` est un `Literal` sans contrôle à l'exécution ; le test ne vérifie que `isinstance` | patch (P1) |
| B5 / E1 / E2 | Routes sans méthode déclarée, ou seulement HEAD/OPTIONS, absentes du contrôle | medium | `methods=None` ou un ensemble filtré vide ne produit aucune clé | patch (P2) |
| E3 / revendication | Chemins à convertisseur (`{id:int}`) : clé différente du gabarit | medium | `context.path` garde le convertisseur ; les futures routes `/v1/reports/{id}` seraient signalées à tort | patch (P2) |
| B3 | Les routes `internal` ne sont pas confrontées au `Caddyfile` | medium | Le motif `@internal` est maintenu à part ; une nouvelle route interne sortirait par `/v1/*` | patch (P3) |
| B6 | La paire déclarée `white/brand-600` n'est pas celle affichée (`text-surface` sur `bg-brand-600`) | low | `NotFoundPage.tsx` ; correction directe de la paire | patch (P4) |
| B7 (partie) | Rien n'interdit `text-danger` (rouge en texte, 4,28:1) | medium | Les messages d'erreur arrivent avec les prochaines stories | patch (P4) |
| B12 | Paire non textuelle en double ; anneau de focus non contrôlé | low | `focus-visible:outline-brand-900` existe ; correction directe | patch (P4) |
| B8 / E5 / E6 | Analyse du thème : hors du bloc `@theme`, commentaires lus, redéclarations écrasées, couleurs non hexadécimales ignorées | medium | `TOKEN_DECLARATION` sur tout le fichier, `Map.set` sans contrôle | patch (P5) |
| B9 | Message trompeur pour une couleur littérale autre que le blanc | low | Correction directe | patch (P5) |
| B2 | Clés `errors.*` orphelines non détectées | low | Correction directe (contrôle inverse) | patch (P6) |
| B10 (partie) | Docstring de `codes.py` muette sur `wo.json` | low | Correction directe | patch (P6) |
| B1 | `wo.json` contient du français | low | Choix assumé depuis la story 1.3 : valeurs françaises en attente de traduction par des locuteurs natifs | rejeté |
| B7 (partie) | `--color-line` sans paire | low | Aucun contrôle de formulaire ne l'utilise encore comme limite ; à contrôler avec le premier champ (story 1.13) | rejeté |
| B10 (partie) | Le test backend lit `web/` sans message clair hors du dépôt complet | low | La CI travaille toujours sur le dépôt complet | rejeté |
| B11 | `APIRoute | Route` redondant | low | Cosmétique | rejeté |

## Design Notes

**Pourquoi des tests plutôt qu'un script séparé.** Les jobs `web` (Vitest) et `backend` (pytest) existent et sont obligatoires sur `main` : ajouter des tests suffit pour que chaque contrôle bloque une fusion, sans nouveau job ni nouvel outil.

**Pourquoi une table déclarative avant l'authentification.** La story 2.5 branchera `require_role` sur cette table. Dès maintenant, toute nouvelle route doit déclarer sa politique, ce qui évite une route ouverte par oubli entre deux stories.

## Verification

**Commandes :**
- Dans `backend/` : `uv run pytest tests/unit/test_error_messages.py tests/architecture/test_route_policies.py` — attendu : succès.
- Dans le conteneur Node 26, dossier `web/` : `npm ci && npm run lint && npm test && npm run build` — attendu : succès.
