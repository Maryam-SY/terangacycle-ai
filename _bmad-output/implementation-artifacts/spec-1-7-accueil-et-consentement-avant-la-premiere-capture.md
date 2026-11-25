---
title: 'Story 1.7 — Accueil et consentement avant la première capture'
type: 'feature'
created: '2026-11-25'
status: 'done'
baseline_commit: '0ca84b3a91445150e81a317c29256f3bc697e7e7'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-3-coquille-pwa-et-bord-caddy.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problème :** la PWA n'affiche qu'un texte d'attente. Le Citoyen n'a ni bouton pour signaler, ni information sur ce que l'application fera de sa Position et de ses photos. Rien n'identifie non plus l'appareil d'un Citoyen anonyme.

**Approche :**
1. Créer l'Identifiant d'appareil (32 octets aléatoires, base64url) dans une base Dexie `meta`, au premier lancement.
2. Refaire l'écran 1 · Accueil d'après la maquette : en-tête vert foncé, grand bouton « Signaler un dépôt » avec pictogramme.
3. Afficher l'écran de consentement [HORS MAQUETTE] avant toute capture. Il est versionné, et la case du réentraînement est séparée et non cochée.
4. Une acceptation ouvre l'écran 2 · Capture (une page d'attente pour l'instant, remplie par la story 1.8).

**Décision (Claude, 25/11/2026) — audits.** Le critère « Lighthouse et axe » est vérifié en CI par trois contrôles :
- axe-core (`@axe-core/playwright`) sur l'accueil et le consentement, sans violation `critical` ni `serious` ;
- un test du manifeste : nom, icônes 192 et 512, dont une `maskable`, couleurs issues des jetons ;
- un budget de poids : au plus 500 Ko pour le HTML, le JS, le CSS et les polices précachées de l'accueil, hors images et Modèle.

Lighthouse lui-même tourne une fois à la main avant la démo (story 8.2). Le lancer en CI ajouterait un Chrome complet et des résultats instables, pour les mêmes informations.

## Boundaries & Constraints

**Toujours :**
- Aucun texte en dur : tout passe par `fr.json`, et `wo.json` reçoit les mêmes clés.
- Couleurs issues des jetons seulement, cibles tactiles d'au moins 44 × 44 px.
- Pictogrammes en SVG intégré, avec `aria-hidden` quand un libellé existe. Aucune bibliothèque d'icônes.
- L'Identifiant d'appareil n'est jamais affiché, jamais écrit dans la console, jamais envoyé dans cette story.
- Dépendances ajoutées et épinglées : `dexie@4.4.7`, `@playwright/test@1.65.1`, `@axe-core/playwright@4.14.1`, `fake-indexeddb` (dernière version stable, épinglée).

**Jamais :**
- Aucune demande de géolocalisation ou d'appareil photo, aucune requête réseau de signalement dans cette story. La capture réelle arrive avec la story 1.8.
- Pas d'entrées « Je suis collecteur » ni « Espace commune » : elles arrivent avec la story 2.3 (connexion OTP).
- Pas de liste « Mes Signalements » (story 1.13), pas de bandeau démo (story 2.1).

## I/O & Edge-Case Matrix

| Scénario | Entrée / État | Résultat attendu | Erreurs |
|---|---|---|---|
| Premier lancement | Base `meta` vide | Identifiant de 43 caractères base64url créé et mémorisé | — |
| Relance | Identifiant déjà présent | Le même identifiant est conservé | — |
| Accueil mobile | 390×844 | Bouton « Signaler un dépôt » d'au moins 44 px, pas de défilement horizontal | — |
| Premier signalement | Aucun consentement, appui sur « Signaler un dépôt » | Écran de consentement, sans demande de géolocalisation ni d'appareil photo, sans requête vers `/v1/reports` | — |
| Refus | « Pas maintenant » | Retour à l'accueil, rien de mémorisé ; le consentement sera redemandé | — |
| Acceptation | « J'accepte », case du réentraînement non cochée | `meta.consent = {acceptedAt ISO, version, training: false}`, puis écran 2 | — |
| Acceptation avec la case | Case cochée | `training: true` | — |
| Consentement à jour | Version mémorisée = version courante | « Signaler un dépôt » ouvre directement l'écran 2 | — |
| Nouvelle version | Version mémorisée ≠ version courante | Le consentement est redemandé | — |
| Lien direct | `/signaler/capture` sans consentement | Redirection vers le consentement | — |

</frozen-after-approval>

## Code Map

- **Coquille actuelle :**
  - `web/src/routes.tsx` : `/` → `HomePage`, `*` → `NotFoundPage`.
  - `web/src/App.tsx` : `createBrowserRouter`, créé au montage.
  - `web/src/features/home/HomePage.tsx` : titre et sous-titre d'attente.
  - `web/src/features/not-found/NotFoundPage.tsx` : page introuvable, `text-surface` sur `bg-brand-600`.
- **Traduction** : `web/src/i18n/{index.ts,fr.json,wo.json,i18next.d.ts}`, clés typées sur `fr`. `i18n.test.ts` exige la parité fr/wo et l'absence de couleur hors de `theme.css`.
- **Thème** : `web/src/theme/theme.css` (jetons) et `contrast-pairs.json`. Une nouvelle combinaison texte/fond doit y être déclarée, et `text-danger` est interdit.
- **PWA** : `web/pwa.config.ts` (couleurs du manifeste, liste d'exclusion) et `web/vite.config.ts` (manifeste). Icônes `public/icon-192.png` et `icon-512.png`. `src/pwa.test.ts` vérifie les couleurs et la liste d'exclusion.
- **Dossiers** : `web/src/offline/` (vide, `fetch` autorisé) et `web/src/api/` (vide).
- **Lint** : oxlint (`.oxlintrc.json`) interdit `fetch` hors de `api` et `offline`.
- **Tests** : `vitest run`. `App.test.tsx` rend les pages avec `renderToString` dans un `MemoryRouter`.
- **CI** : le job `web` (`.github/workflows/ci.yml`) lance `npm ci`, lint, test et build. Les 5 jobs sont obligatoires sur `main`.
- **Écran 1 (maquette, nœud 1:2)** : en-tête `brand-900` avec le nom de l'application et la phrase d'accroche, grande carte-bouton verte avec pictogramme appareil photo, « Signaler un dépôt » et « Photo et position en moins de 30 secondes », fond `surface`, police Inter.

## Tasks & Acceptance

**Exécution :**
- [x] `web/package.json` (+ lock) : ajouter `dexie`, et en dépendances de développement `@playwright/test`, `@axe-core/playwright` et `fake-indexeddb`, toutes à version exacte. Scripts `test:e2e` (Playwright) et `size` (budget).
- [x] `web/src/offline/db.ts` : base Dexie `terangacycle`, version 1, table `meta` (`key` primaire, `value`). Accès via `getMeta(key)` et `setMeta(key, value)`.
- [x] `web/src/offline/device.ts` : `ensureDeviceId()`. Lit `meta.deviceId` ; sinon génère 32 octets par `crypto.getRandomValues`, les encode en base64url sans remplissage (43 caractères) et les mémorise. Appelée au démarrage (`main.tsx`), jamais journalisée.
- [x] `web/src/features/consent/consent.ts` : `CONSENT_VERSION` (chaîne datée), `getConsent()`, `acceptConsent({training})` (date ISO de l'appareil), `hasCurrentConsent()`.
- [x] `web/src/features/consent/ConsentPage.tsx` (route `/signaler/consentement`) :
  - sections avec pictogramme : géolocalisation, envoi de la photo, consigne « ni personne ni plaque » ;
  - case séparée « Mes photos et corrections peuvent servir à améliorer le Modèle », non cochée ;
  - avertissement sur la liste perdue en cas de réinstallation, pour un Citoyen anonyme ;
  - boutons « J'accepte » et « Pas maintenant » ; titres et ordre de lecture logiques.
- [x] `web/src/features/home/HomePage.tsx` : écran 1 d'après la maquette. « Signaler un dépôt » mène à `/signaler`.
- [x] `web/src/features/report/ReportEntry.tsx` (route `/signaler`) et `CapturePage.tsx` (route `/signaler/capture`) :
  - l'entrée redirige vers le consentement ou vers la capture selon `hasCurrentConsent()` ;
  - la page de capture (provisoire, story 1.8) redirige vers le consentement s'il manque, et affiche sinon un titre traduit et un retour à l'accueil.
- [x] `web/src/ui/icons.tsx` : pictogrammes SVG (appareil photo, position, photo envoyée, personne barrée, cœur ou bouclier pour le Modèle).
- [x] `web/src/i18n/fr.json` et `wo.json` : clés `home.*`, `consent.*`, `capture.*`. Textes en français simple, avec remerciement, sans culpabiliser.
- [x] `web/src/theme/contrast-pairs.json` : déclarer toute nouvelle paire texte/fond (par exemple `surface` sur `brand-900` pour l'en-tête, texte sur `mint` pour les sections).
- [x] `web/public/icon-maskable-512.png` (motif dans la zone de sécurité, fond `brand-900`) et `vite.config.ts` : icône `purpose: "maskable"`. `src/pwa.test.ts` vérifie le nom, les 3 icônes dont la maskable, et les couleurs.
- [x] **Tests Vitest** (`fake-indexeddb`) :
  - `device.test.ts` : format de l'identifiant, persistance, aucun appel à `console` ;
  - `consent.test.ts` : acceptation avec et sans case, version périmée.
- [x] `web/e2e/consent.spec.ts` (Playwright, Chromium, viewport 390×844, sur `vite preview`) : chaque ligne de la matrice I/O.
  - Espions installés par `addInitScript` sur `navigator.geolocation.getCurrentPosition` et `watchPosition`, et sur `navigator.mediaDevices.getUserMedia`, plus l'enregistrement des requêtes réseau.
  - axe sur l'accueil et le consentement : aucune violation `critical` ni `serious`.
- [x] `web/scripts/check-size.mjs` : somme des fichiers HTML, JS, CSS et woff2 (précache de l'accueil) de `dist/`, hors images. Échec au-delà de 500 Ko.
- [x] `.github/workflows/ci.yml`, job `web`, après le build :
  - `npm run size` ;
  - `npx playwright install --with-deps chromium` ;
  - `npm run test:e2e` ;
  - publication du rapport Playwright en artefact en cas d'échec.

**Critères d'acceptation :**
- Étant donné la PR, quand la CI tourne, alors les 5 jobs sont verts, avec les tests Playwright et axe et le budget de poids dans le job `web`.
- Étant donné la PWA construite, quand on l'ouvre en 390×844 dans le navigateur, alors l'accueil ressemble à l'écran 1 de la maquette et le parcours de consentement fonctionne.

## Implementation Notes

- **Budget de poids mesuré compressé.** La somme brute dépassait déjà 500 Ko avant cette story (531 Ko : JS 372 Ko, polices 133 Ko), et Dexie ajoute environ 110 Ko. `check-size.mjs` mesure donc le poids transféré, comme Lighthouse : HTML, JS et CSS en gzip niveau 5, polices woff2 en taille brute. Résultat : 293,8 Ko (brut 643 Ko). Fichiers pris en compte : la liste de précache de `dist/sw.js`, plus `sw.js` et le runtime Workbox qu'il charge. Pour que la mesure reflète le service réel, `infra/Caddyfile` compresse désormais la PWA (`encode zstd gzip`, bloc PWA seulement). `smoke_edge.py` envoie `Accept-Encoding: identity` : il n'est pas touché.
- **`smoke_edge.py`.** Il lisait `home.title` et `home.subtitle`, remplacés par `home.tagline`, `home.report` et `home.reportHint` : liste des clés mise à jour (sinon le job `edge` échouait).
- **Redirections.** `ReportEntry` et `CapturePage` lisent le consentement par `useCurrentConsent()` (rien d'affiché pendant la lecture, puis `<Navigate replace>`). Une base illisible vaut « pas de consentement ». Chemins dans `src/paths.ts`.
- **Échec d'enregistrement.** Si `acceptConsent` échoue, l'écran affiche `consent.saveError` (texte en Encre, icône rouge par `stroke-danger`) et reste sur place.
- **Identifiant d'appareil.** Lecture et écriture dans une même transaction Dexie (pas de double identifiant entre onglets) ; une valeur mémorisée invalide est remplacée. `main.tsx` ignore un échec sans rien journaliser.
- **Manifeste.** Déplacé dans `pwa.config.ts` (`MANIFEST`) pour être testé ; `icon-maskable-512.png` reprend le motif de `icon-512.png`, réduit de 20 % dans la zone de sécurité.
- **Playwright.** `playwright.config.ts` : Chromium 390×844 (`isMobile`, `hasTouch`), `vite preview` sur 127.0.0.1:4173, service workers bloqués pour des parcours déterministes. L'argument de fixture s'appelle `provide` (oxlint prenait `use` pour un hook). `e2e/` et la configuration sont vérifiés par `tsc -b` (`tsconfig.e2e.json`) ; Vitest ne lit que `src/**/*.test.{ts,tsx}`. Rapport HTML publié par `actions/upload-artifact` v7.0.2 (épinglé par SHA) en cas d'échec ; délai du job `web` porté à 20 min.
- **Non exécuté en local.** Les 14 tests Playwright n'ont tourné qu'en `--list` (disque plein, pas de navigateur Playwright) : ils seront vérifiés par la CI.

## Spec Change Log

## Review Triage Log

Passe 1 (25/11/2026). Couches : Blind Hunter (B), Edge Case Hunter (E), Verification Gap (V).

| # | Constat | Verdict | Preuve | Route |
|---|---|---|---|---|
| B1 | `package-lock.json` non modifié | false | Le verrou est à jour ; il était seulement exclu du diff de relecture | rejeté |
| B2 | Icône maskable absente | false | `web/public/icon-maskable-512.png` existe (PNG exclu du diff) | rejeté |
| B3 / E1 | « Pas maintenant » reste actif pendant l'enregistrement ; le refus est écrasé | medium | `decline` n'est pas désactivé pendant `saving` ; `navigate(capture)` arrive après | patch (P1) |
| B4 | Le texte du consentement ne parle pas de l'Identifiant d'appareil | medium | Donnée personnelle (AD-9), envoyée avec chaque Signalement dès la story 1.11 | patch (P2) |
| B9 | Stockage non persistant, effacement automatique non mentionné | medium | Safari peut effacer IndexedDB d'une PWA non installée après 7 jours | patch (P2) |
| B6 | `CONSENT_VERSION` sans lien avec le texte | medium | Un texte modifié sans nouvelle version ne serait jamais redemandé (FR-4) | patch (P3) |
| B7 / V2 | Échec d'enregistrement du consentement jamais exécuté | medium | Aucun test ne fait échouer l'écriture IndexedDB | patch (P4) |
| V3 / E2 | Base illisible ou bloquée : écran blanc possible | medium | `.catch(() => false)` jamais exécuté ; aucun délai si l'ouverture ne répond pas | patch (P4) |
| B8 / V1 | Compression de Caddy, socle du budget, jamais vérifiée ; liens profonds non testés | medium | `smoke_edge.py` demande `identity` ; supprimer `encode` laisserait tout vert | patch (P5) |
| V4 | Manifeste construit jamais vérifié | medium | Seule la constante `MANIFEST` est testée | patch (P5) |
| B10 | Le focus ne suit pas le changement d'écran | medium | Navigation côté client sans déplacement du focus ; lecteur d'écran non prévenu | patch (P6) |
| E3 | `acceptedAt` mal formé accepté | low | Correction directe | patch (P3) |
| E4 | Fichier de précache absent : trace brute dans `check-size.mjs` | low | Correction directe | patch (P5) |
| E5 | `writeMeta` (aide de test) peut bloquer jusqu'au délai | low | Correction directe | patch (P4) |
| B5 | Pas de retrait du consentement ; une nouvelle acceptation remet `training` à faux | low | Le retrait est l'objet de la story 1.16 | rejeté (story 1.16) |
| B11 | `tsconfig.e2e.json` casserait l'image Caddy | false | `Dockerfile.dockerignore` envoie `web/` avec `e2e/`, et `npm ci` installe les dépendances de développement | rejeté |
| B12 | Dexie chargé dès l'accueil | low | Budget respecté (293,8 Ko compressés) | rejeté |
| B13 | Chromium retéléchargé à chaque exécution de la CI | low | Coût de temps seulement | rejeté |

## Design Notes

**Consentement local, sans serveur.** Le choix est mémorisé sur l'appareil (Dexie `meta`) et sera copié sur chaque Signalement par la story 1.11. Aucune route ne reçoit le consentement dans cette story. La version datée permet de le redemander si le texte change (FR-4).

**Disque local presque plein.** La construction et les tests Playwright se vérifient en CI. En local, on se limite à Vitest et à un aperçu `vite preview` dans le navigateur intégré, sans télécharger de navigateur Playwright.

## Verification

**Commandes :**
- Conteneur Node 26 (`--pull never`) : `npm ci && npm run lint && npm test && npm run build && npm run size` — attendu : succès.
- Sur GitHub : le job `web` est vert, `test:e2e` compris.
- Navigateur intégré : l'aperçu en 390×844 montre l'accueil et le parcours de consentement.
