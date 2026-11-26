---
title: 'Story 1.13 — Compléter, envoyer et voir la confirmation'
type: 'feature'
created: '2026-11-26'
status: 'in-review'
baseline_commit: 'd1ebcca5ccaa748d5bbf264ff8f9dcebd85e585d'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-12-renvoyer-un-signalement-sans-doublon-ni-fuite.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Le parcours du Citoyen s'arrête à l'écran 3 provisoire : le brouillon (photo et Position) reste sur le téléphone, rien n'est envoyé et aucun Numéro de suivi n'est montré. La PWA n'a pas non plus de client API généré : `api/config.ts` est écrit à la main.

**Approach:**
- générer le client depuis l'OpenAPI : `backend/scripts/export_openapi.py`, types `openapi-typescript`, une instance unique `openapi-fetch` enveloppée dans `web/src/api/` (`X-Device-Id`, erreurs traduites) ; fichiers versionnés, dérive refusée par la CI ;
- remplacer l'écran 3 : miniature, Taille de tas, `WasteTypePicker` facultatif, commentaire « n/280 », bouton « Envoyer » ;
- appeler `POST /v1/reports`, puis afficher l'écran 4 · Confirmation : Numéro de suivi, Frise de suivi, étiquette démo.

Les critères d'acceptation de référence sont ceux de la section `### Story 1.13` d'`_bmad-output/planning-artifacts/epics.md`, à respecter intégralement.

## Boundaries & Constraints

**Always:**
- **OpenAPI :**
  - `export_openapi.py` construit l'application (`create_app`, réglages `ENV=dev`, sans lifespan ni base) et écrit `web/src/api/openapi.json` (JSON indenté, fin de ligne finale, octets stables d'une exécution à l'autre) ;
  - l'OpenAPI publie `ReportMeta` (et `ReportConsent`, `HeapSize`, `WasteType`) dans `components.schemas`. Dans le corps multipart, `meta` y renvoie, avec `encoding.meta.contentType = application/json`. C'est un post-traitement de `app.openapi()` posé dans `create_app`, fourni par le router `reports`. La validation reste `parse_meta()`, inchangée ;
  - les types sont produits par `web/scripts/gen-api-types.mjs` (API Node d'`openapi-typescript`, transformation `format: binary` → `Blob`) dans `web/src/api/schema.d.ts`, lancé par `npm run api:types`.
- **Dépendances :**
  - `openapi-fetch` 0.17.x en dépendance, `openapi-typescript` 7.13.x en dépendance de développement, versions exactes ;
  - `"overrides": {"openapi-typescript": {"typescript": "$typescript"}}` dans `web/package.json` ;
  - pas de TanStack Query dans cette story.
- **Client (`web/src/api/client.ts`) :**
  - une seule instance `createClient<paths>()`, avec `fetch: (request) => globalThis.fetch(request)` (les tests remplacent `fetch` après l'import) ;
  - un middleware ajoute `X-Device-Id` (`ensureDeviceId()`, Dexie `meta`) à chaque requête, et jamais `Authorization` ;
  - toute réponse non 2xx devient `ApiError { status, code, messageKey }`. `messageKey` vaut `errors.<code>` si le code est connu de `fr.json`, sinon `errors.internal_error`. Une enveloppe absente ou illisible (502 de Caddy) compte comme une erreur 5xx ;
  - une coupure réseau ou un délai dépassé (30 s, `AbortController`) devient `NetworkError` ;
  - `api/config.ts` passe par ce client. Sa validation (`parsePublicConfig`) et sa signature ne changent pas.
- **Brouillon :**
  - `saveDraft()` attribue `clientUuid = crypto.randomUUID()` au brouillon. L'écran 2 n'a pas à changer ;
  - `parseDraft()` exige un UUID v4. Un brouillon d'avant cette story, sans `clientUuid`, est complété à sa première lecture ;
  - le même `clientUuid` part à chaque renvoi, rechargement compris.
- **Écran 3 (`/signaler/details`) :**
  - consentement et brouillon contrôlés comme aujourd'hui ;
  - miniature avec texte alternatif ;
  - Taille de tas (3 options) et Type de déchet facultatif (5 options) : boutons radio, aucun choix présélectionné. Le Type peut être retiré : toucher l'option choisie la désélectionne. Pictogramme et libellé, cibles ≥ 44 × 44 px, état choisi signalé par une coche ;
  - commentaire : compteur « n/280 » en points de code (`[...texte].length`), saisie tronquée à 280 points de code ;
  - Taille, Type et commentaire restent dans l'état de l'écran, pas dans Dexie.
- **« Envoyer » :**
  - désactivé tant que la photo, la Position ou la Taille manque, avec la raison reliée par `aria-describedby` et une région `role="status"` ;
  - désactivé pendant la requête ;
  - `consent` est lu dans Dexie au moment de l'envoi : `terms = hasCurrentConsent()`, `training` du consentement gardé ;
  - `meta` : `client_uuid`, `lat`, `lng`, `accuracy_m`, `captured_at`, `heap_size`, `comment` s'il n'est pas vide, `waste_type` s'il est choisi, `consent` ;
  - `photo` : le Blob du brouillon tel quel (`photo.jpg`, `image/jpeg`).
- **Succès (201 ou 200) :**
  - brouillon effacé ;
  - `navigate(PATHS.confirmation, { replace: true, state: { trackingNumber, isDemo } })`.
- **Écran 4 (`/signaler/confirmation`) :**
  - remerciement et Numéro de suivi `TC-AAAA-NNNNNN` ;
  - Frise de suivi : 4 étapes en `<ol>`, chacune avec pictogramme et libellé. L'étape « Signalé » est courante : `aria-current="step"`, marque visible non colorée ;
  - étiquette « Données de démonstration » si `is_demo` ;
  - « Retour à l'accueil » efface le brouillon (sans erreur s'il est déjà vide) et revient à `/` (`replace`) ;
  - sans état de navigation (lien direct) : retour à l'accueil.
- **Erreurs (messages de `fr.json`, en Encre, icône rouge, focus sur le message) :**
  - 422 `outside_active_zone` : son message et un lien vers l'écran 2 ;
  - 422 `consent_required` : retour à l'écran de consentement ;
  - 413, 415, 422 `photo_*` : message et invitation à reprendre la photo ;
  - erreur réseau ou 5xx : « Envoi impossible pour l'instant. Votre saisie est gardée, réessayez. » et « Réessayer ». La saisie et le brouillon sont gardés, et le même `client_uuid` repart ;
  - tout autre code (400, 409, 422 `validation_error`) : son message `errors.<code>`, brouillon gardé.
- **Composants partagés :**
  - `WasteTypeBadge` et `WasteTypePicker` dans `web/src/features/classify/` ;
  - jetons provisoires `--color-waste-{plastic,metal,glass,organic,mixed}` dans le bloc `@theme`, chacun ≥ 3:1 face à `--color-surface` et au blanc ;
  - les paires de chaque couleur (non textuelles) et de chaque libellé (texte, 4,5:1) sont déclarées dans `contrast-pairs.json` ;
  - aucune couleur hors de `theme.css`.
- **i18n :**
  - textes nouveaux sous `details.*`, `confirmation.*`, `timeline.*`, `heapSize.*`, `wasteType.*`, avec les mêmes clés dans `wo.json` ;
  - garder `details.title`, `details.photoAlt`, `details.position`, `details.back`, dont `e2e/capture.spec.ts` dépend ;
  - retirer `details.soon`.
- **Confidentialité :** ni Position, ni Identifiant d'appareil, ni Numéro de suivi dans la console.
- **Budget :** l'accueil reste ≤ 500 Ko transférés (`npm run size`). Les types générés ne pèsent rien. Seul `openapi-fetch` s'ajoute au bundle.

**Never:**
- pas de file hors-ligne ni de renvoi automatique (Epic 6) ; « Réessayer » est manuel ;
- pas de message 429 (story 1.15), pas de proposition IA (Epic 3), pas de « Mes Signalements » ;
- pas de `fetch` hors de `src/api/` et `src/offline/` ;
- aucun changement du comportement de `POST /v1/reports` : seule sa description OpenAPI change.

## I/O & Edge-Case Matrix

| Scénario | Entrée / état | Attendu |
|---|---|---|
| Nominal | Brouillon, Taille « moyen », sans Type ni commentaire, réseau | `POST` multipart avec `meta` attendu et octets exacts du JPEG ; 201 → écran 4 avec le Numéro ; brouillon effacé |
| Complet | Type « plastique », commentaire de 280 points de code (emojis) | `waste_type` et `comment` envoyés ; la 281e frappe est ignorée, « 280/280 » |
| Type retiré | Type choisi puis touché de nouveau | Aucun Type choisi ; `waste_type` absent |
| Taille manquante | Aucune Taille | « Envoyer » désactivé, raison annoncée ; aucune requête |
| Double appui | Deux touchers rapides | Une seule requête ; un second envoi reçoit 200 → même écran 4 |
| Renvoi | 1er envoi en échec réseau, « Réessayer » | Même `client_uuid` ; 200 → écran 4 |
| Démo | `is_demo: true` | Étiquette « Données de démonstration » visible |
| Hors Zone | 422 `outside_active_zone` | Message et lien vers l'écran 2 |
| Consentement | 422 `consent_required` | Écran de consentement |
| Photo | 413 / 415 / 422 `photo_unreadable` | Message et invitation à reprendre la photo |
| Réseau / 5xx | Coupure, 503, 502 sans enveloppe | Message « Envoi impossible… », « Réessayer », saisie gardée |
| Consentement retiré | `training: false` dans Dexie | `consent.training = false` envoyé |
| Lien direct écran 4 | Sans état | Accueil |
| Brouillon ancien | Sans `clientUuid` | Complété à la lecture, puis stable |

</frozen-after-approval>

## Code Map

- `backend/app/modules/reports/router.py` : `create_report` (`meta: str` en `Form`, `photo: UploadFile`), `RESPONSES`, `ERROR_RESPONSES`. Ajouter seulement la fonction de post-traitement OpenAPI. Ne pas toucher `ReportUploadGuard` ni la logique.
- `backend/app/modules/reports/schemas.py` : `ReportMeta`, `ReportConsent`, `ReportCreated` (sources des schémas publiés ; inchangés).
- `backend/app/main.py` : `create_app()` ; y poser le post-traitement (`app.openapi`). Le `responses={"default": ErrorResponse}` existe déjà.
- `backend/scripts/` : modèle `smoke_readyz.py` ; nouveau `export_openapi.py` (sortie `../web/src/api/openapi.json` relative au script).
- `backend/tests/unit/test_errors.py::test_error_codes_are_exported_in_openapi` : modèle de test sur `app.openapi()`.
- `.github/workflows/ci.yml` : job `backend` (ajouter l'export puis `git diff --exit-code web/src/api/openapi.json`) ; job `web` (ajouter `npm run api:types` puis `git diff --exit-code src/api/schema.d.ts`, avant `npm run build`).
- `web/src/api/config.ts` : `fetchPublicConfig(timeoutMs)`, `CONFIG_PATH`, `parsePublicConfig` ; garder l'API publique. `web/src/offline/publicConfig.test.ts` stube `fetch` et lit `[path, init]` : l'adapter à `fetch(Request)`.
- `web/src/offline/device.ts` : `ensureDeviceId()`. `web/src/offline/draft.ts` : `Draft`, `parseDraft`, `saveDraft`, `getDraft`, `clearDraft`.
- `web/src/features/report/DetailsPage.tsx` : `DetailsPage` → `DetailsLoader` → `DetailsScreen`. Garder la garde de consentement et le chargement ; remplacer l'écran.
- `web/src/features/report/CapturePage.tsx` : modèles `Message`, `Blocked`, `PRIMARY`/`SECONDARY`, gestion du focus (`pendingFocus`) ; ne pas modifier.
- `web/src/features/consent/consent.ts` : `getConsent()`, `hasCurrentConsent()`, `CONSENT_VERSION` ; ne pas modifier. Aucune clé `consent.*` de `fr.json` ne change (empreinte `CONSENT_TEXT_SHA256`).
- `web/src/ui/icons.tsx` (`IconProps`, icônes en `currentColor`), `useFocusOnMount.ts`, `useObjectUrl.ts`.
- `web/src/theme/theme.css`, `contrast-pairs.json`, `contrast.test.ts` (`failingPairs`) ; `web/src/i18n/i18n.test.ts` (mêmes clés fr/wo, aucune couleur hors thème).
- `web/scripts/check-size.mjs` : budget de 500 Ko.
- `web/.oxlintrc.json` et `src/lint.test.ts` : `fetch` permis dans `src/api/` seulement.
- `web/e2e/capture.spec.ts` : modèle (fixture géolocalisation, `page.route`, `expectNoSeriousViolations`, `readDraft`) ; doit passer sans modification.

**Fichiers créés ou modifiés (liste complète) :**
- backend : `backend/scripts/export_openapi.py` (nouveau), `backend/app/main.py`, `backend/app/modules/reports/router.py`, `backend/tests/unit/test_openapi_export.py` (nouveau) ;
- CI et docs : `.github/workflows/ci.yml`, `README.md`, `web/README.md` ;
- web, outillage : `web/package.json`, `web/package-lock.json`, `web/scripts/gen-api-types.mjs` (nouveau) ;
- web, API : `web/src/api/openapi.json` (généré), `web/src/api/schema.d.ts` (généré), `web/src/api/.gitkeep` (supprimé), `web/src/api/client.ts` (nouveau), `web/src/api/client.test.ts` (nouveau), `web/src/api/reports.ts` (nouveau, `sendReport(meta, photo)`), `web/src/api/reports.test.ts` (nouveau), `web/src/api/config.ts` ;
- web, hors-ligne : `web/src/offline/publicConfig.test.ts`, `web/src/offline/draft.ts`, `web/src/offline/draft.test.ts` ;
- web, signalement : `web/src/features/report/DetailsPage.tsx`, `web/src/features/report/details.ts` (nouveau : raison du blocage, troncature, décision d'erreur), `web/src/features/report/details.test.ts` (nouveau), `web/src/features/report/HeapSizePicker.tsx` (nouveau), `web/src/features/report/ConfirmationPage.tsx` (nouveau), `web/src/features/report/TrackingTimeline.tsx` (nouveau) ;
- web, classification : `web/src/features/classify/WasteTypePicker.tsx` (nouveau, `WasteTypeBadge` et `WasteTypePicker`), `web/src/features/classify/wasteTypes.ts` (nouveau : ordre, pictogramme, jeton) ;
- web, routes : `web/src/paths.ts`, `web/src/routes.tsx`, `web/src/App.test.tsx` ;
- web, i18n, thème, icônes : `web/src/i18n/fr.json`, `web/src/i18n/wo.json`, `web/src/theme/theme.css`, `web/src/theme/contrast-pairs.json`, `web/src/ui/icons.tsx` ;
- web, e2e : `web/e2e/report.spec.ts` (nouveau).

## Tasks & Acceptance

**Execution:**
- [x] `backend/scripts/export_openapi.py`, `app/main.py`, `modules/reports/router.py` : export stable et schéma `ReportMeta` publié ; test unitaire (composants présents, `meta` → `ReportMeta`, `encoding`, deux exports identiques, fichier versionné égal à l'export).
- [x] `web/package.json`, `scripts/gen-api-types.mjs`, `src/api/openapi.json`, `src/api/schema.d.ts` : génération, override, script `api:types`.
- [x] `web/src/api/client.ts`, `reports.ts`, `config.ts` : instance unique, `X-Device-Id`, `ApiError`/`NetworkError`, délai ; `sendReport` construit le `FormData` (`meta` en JSON, `photo`).
- [x] `web/src/offline/draft.ts` : `clientUuid`.
- [x] `web/src/features/classify/*`, `features/report/*` (écrans 3 et 4, Frise, Taille), `paths.ts`, `routes.tsx`, `ui/icons.tsx`.
- [x] `web/src/theme/theme.css`, `contrast-pairs.json`, `i18n/fr.json`, `wo.json`.
- [x] `.github/workflows/ci.yml` : contrôles de dérive (OpenAPI et types).
- [x] **Tests :**
  - Vitest : client (en-tête, traduction des codes, enveloppe absente, coupure, délai), `sendReport` (champs, octets exacts), brouillon (`clientUuid` v4, stable, complété), `details.ts` (raisons, points de code, décision par code d'erreur), contraste ;
  - Playwright `report.spec.ts` (`POST /v1/reports` intercepté, 390×844, axe sans violation `critical` ni `serious`, pas de débordement horizontal, cibles ≥ 44 px) : chaque ligne de la matrice.
- [x] `README.md` et `web/README.md` : régénérer le client (`uv run python scripts/export_openapi.py` puis `npm run api:types`) et contrôle CI.

**Acceptance Criteria:**
- Tous les critères d'acceptation de la story 1.13 d'`epics.md` sont couverts par au moins un test qui tourne en CI. Lighthouse est lancé à la main avant la démo, comme décidé à la story 1.7 ; en CI, axe le remplace.
- Modifier un champ de `ReportCreated` sans régénérer les fichiers fait échouer la CI.

## Implementation Notes

- **OpenAPI :** `reports.router.document_report_body()` publie `ReportMeta` (et ses `$defs` : `ReportConsent`, `HeapSize`, `WasteType` ; un nom déjà publié sous une autre forme lève une erreur), fait pointer `meta` vers `ReportMeta`, pose `encoding.meta.contentType = application/json` et ajoute `format: binary` à la photo (FastAPI ne publie que `contentMediaType`, la transformation `Blob` de `gen-api-types.mjs` s'appuie sur `format`). `create_app` enveloppe `app.openapi` (`_post_process_openapi`), résultat gardé en cache comme FastAPI.
- **Export :** `export_openapi.py` ajoute `backend/` à `sys.path` (lancé comme `python scripts/…`), réglages `ENV=dev` sans `DEMO_MODE` (secrets éphémères, journal coupé), écriture en octets UTF-8/LF ; `--output` pour les tests. `.gitattributes` force LF sur `openapi.json` et `schema.d.ts` (comparaison octet pour octet sous Windows avec `core.autocrlf=true`).
- **Client :** origine fictive `http://localhost` sous Node (pas de `location`, `Request` refuse une adresse relative) ; dans le navigateur, `location.origin`. `send()` enveloppe chaque appel (délai, traduction). `ApiError.isServerError` : 5xx ou enveloppe absente. Une réponse 2xx illisible devient `NetworkError`. `fetchPublicConfig` lève désormais `NetworkError`/`ApiError` (l'appelant se replie toujours sur la configuration gardée).
- **Multipart :** `meta` part en texte (un `Blob` serait lu comme un fichier par Starlette et refusé par `Form`), `encoding` reste documentaire ; `Content-Type` laissé au navigateur (FormData).
- **Brouillon :** `saveDraft(NewDraft)` tire l'Identifiant client et renvoie le brouillon ; la complétion d'un ancien brouillon se fait dans une transaction Dexie (`rw`), seulement si `clientUuid` est absent (un `clientUuid` invalide n'est jamais remplacé).
- **Écran 3 :** commentaire borné par `limitComment(précédent, saisi)` : au maximum, toute frappe est ignorée ; un collage trop long est tronqué (pas d'attribut `maxlength`, qui compte en UTF-16). Après une erreur réseau/5xx, le bouton principal devient « Réessayer ». Garde de double appui par `useRef` en plus du bouton désactivé.
- **Couleurs provisoires :** plastique `#1F6FB2`, métal `#59656F`, verre `#0F7C8C`, organique `#8A5A2B`, mixte `#7B4FA0` (≥ 4,3:1 sur surface, blanc et mint) ; paires déclarées aussi face à mint (fond de l'option choisie). Étiquette démo en Ambre (`warning-ink`/`warning-bg`).
- **e2e :** le corps envoyé est lu par un espion de `fetch` dans la page (copies gardées dans `sessionStorage` pour survivre au rechargement), le serveur simulé répond 201 puis 200.

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run lint-imports && uv run pytest tests/unit tests/architecture` (backend) — expected: vert.
- `uv run python scripts/export_openapi.py && git diff --exit-code ../web/src/api/openapi.json` (backend) — expected: aucune différence.
- `npm run api:types && git diff --exit-code src/api/schema.d.ts && npm run lint && npm test && npm run build && npm run size && npm run test:e2e` (web) — expected: vert, budget ≤ 500 Ko.

**Manual checks (if no CLI):**
- Pile démo : un Signalement envoyé depuis un téléphone au Plateau affiche son Numéro et l'étiquette démo.
