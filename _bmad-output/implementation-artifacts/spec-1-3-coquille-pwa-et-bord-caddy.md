---
title: 'Story 1.3 — Coquille PWA et bord Caddy'
type: 'feature'
created: '2026-11-24'
status: 'done'
baseline_commit: 'a8ef7a0e0872079c53f6014e7a2155e3333f9b01'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-2-configuration-sondes-et-conventions-d-api.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problème :** il n'existe aucune interface. Chaque écran à venir doit partir des mêmes jetons de couleur, des mêmes textes traduits et du même routage. Caddy ne sert que l'API, en HTTP.

**Approche :** créer `web/` avec `create-vite` (template `react-ts`), `vite-plugin-pwa`, Tailwind 4 (un seul bloc `@theme`), i18next (`fr`, et `wo` avec les mêmes clés), `react-router` 8 et la police Inter auto-hébergée. La coquille affiche un accueil vide entièrement traduit. Caddy sert la PWA construite et l'API sur `APP_HOST` en HTTPS, et relaie `MEDIA_HOST` vers Garage.

## Boundaries & Constraints

**Toujours :**
- Versions exactes de la Stack, avec `package-lock.json` committé et `npm ci` :
  - React 19.3.1, Vite 8.3.8, vite-plugin-pwa 2.0.0, TypeScript 6.0.3 ;
  - Tailwind et `@tailwindcss/vite` 4.3.5 ;
  - i18next 27.2.5, react-i18next 18.0.3, react-router 8.5.2 ;
  - `@fontsource-variable/inter` 5.3.0.
- Node 26 via l'image `node:26.13.1-trixie-slim@sha256:abe7e5a82b61a8ef67b315b85497c9e65173387ccf2f4a029248184b8e020be5`.
- Aucun texte affiché en dur : tout passe par `t()`.
- Aucune couleur hors de `theme.css`.
- Aucune ressource chargée depuis un domaine externe.

**Jamais :**
- Pas de `tailwind.config.js` ni de `@config`.
- La chaîne `#1F8A5B` n'apparaît nulle part dans `web/`.
- Pas de CSP, HSTS ni autres en-têtes de sécurité : la story 8.4 les pose, en une fois, dans le Caddyfile.
- Pas d'écran métier, pas de Dexie, pas de client d'API généré (stories 1.6 et 1.13).
- `/metrics` et `/v1/ai/*` ne sont jamais relayés vers l'extérieur.

## I/O & Edge-Case Matrix

| Scénario | Entrée / État | Résultat attendu | Erreurs |
|---|---|---|---|
| Coquille | `https://<APP_HOST>/` dans Chrome | Accueil traduit (titre et sous-titre de `fr.json`), police Inter, fond `--color-surface` | — |
| Route profonde | `https://<APP_HOST>/n-importe-quoi` | La PWA (`index.html`), le routage client affiche une page « introuvable » traduite | — |
| API | `/v1/config`, `/healthz`, `/readyz` sur `APP_HOST` | Relayés vers `api:8000` | — |
| Surfaces internes | `/metrics`, `/v1/ai/x` depuis l'extérieur | 404 | — |
| Photos | `https://<MEDIA_HOST>/<bucket>/<clé>` | Relayé vers `garage:3900`, en-tête `Host` conservé | 403 de Garage sans signature (attendu) |
| HTTP | `http://<APP_HOST>/` | Redirection vers HTTPS | — |

</frozen-after-approval>

## Code Map

- `infra/Caddyfile` : aujourd'hui `:80`, renvoie 404 sur `/metrics`, puis `reverse_proxy api:8000`. À remplacer.
- `infra/docker-compose.yml` : `caddy` utilise `image: caddy:2.11.9-alpine@sha256:003a…36f0`, publie `${HTTP_PORT:-80}:80`, dépend de `api` (`service_healthy`).
- `.env.example` : ajouter `APP_HOST=app.localhost`, `MEDIA_HOST=media.localhost`, `HTTPS_PORT=443`. Chrome résout `*.localhost` vers 127.0.0.1, et Caddy émet pour ces noms un certificat de son CA interne.
- API : `GET /v1/config`, `/healthz` et `/readyz` existent (story 1.2). FastAPI renvoie lui-même 404 sur `/v1/ai/*`, mais Caddy doit bloquer en amont.
- Garage : S3 sur `garage:3900`, adressage path-style, région `garage`.
- `web/` ne contient que `README.md`. Le Node local est en version 24 : la construction de référence se fait dans le conteneur Node 26.

## Tasks & Acceptance

**Exécution :**
- [x] `web/` : générer avec `npm create vite@9.3.4 -- --template react-ts`, puis épingler exactement toutes les dépendances (sans `^` ni `~`) et ajouter `"engines": {"node": ">=26 <27"}`. Créer les dossiers `src/{api,features,offline,i18n,theme}` (avec `.gitkeep` si vides). Supprimer les fichiers de démonstration du template (logos, compteur, `App.css`).
- [x] `web/vite.config.ts` : `react()`, `tailwindcss()`, `VitePWA({ registerType: 'autoUpdate', manifest })`.
  - Manifeste : nom et nom court tirés du produit (« TerangaCycle AI »), `theme_color` `#0B3D2E`, `background_color` `#F6FAF7`, `display: standalone`, icônes 192 et 512 générées en PNG simples dans `public/`.
  - `workbox.navigateFallbackDenylist` : `/^\/v1\//`, `/^\/healthz/`, `/^\/readyz/`.
- [x] `web/src/theme/theme.css` : `@import "tailwindcss";`, `@import "@fontsource-variable/inter";` et un seul bloc `@theme` :
  - `--font-sans` : Inter Variable ;
  - couleurs : `--color-brand-900: #0B3D2E`, `--color-brand-600: #187A50`, `--color-accent: #F2B705`, `--color-mint: #EAF3EC`, `--color-ink: #14231C`, `--color-muted: #5E7168`, `--color-line: #D5E3D9`, `--color-surface: #F6FAF7`, `--color-warning-ink: #7A5C00`, `--color-warning-bg: #FFF4CC`, `--color-danger: #D9482B`.
- [x] `web/src/i18n/{index.ts,fr.json,wo.json}` : i18next et react-i18next, langue par défaut `fr`, repli `fr`. Clés : `app.name`, `home.title`, `home.subtitle`, `notFound.title`, `notFound.back`. `wo.json` a les mêmes clés ; ses valeurs restent en français, à traduire par des locuteurs natifs.
- [x] `web/src/main.tsx`, `web/src/App.tsx`, `web/src/features/home/HomePage.tsx`, `web/src/features/not-found/NotFoundPage.tsx` : `createBrowserRouter` avec `/` → accueil et `*` → page introuvable. `lang="fr"` dans `index.html`.
- [x] `web/src/i18n/i18n.test.ts` (Vitest 5.1.1) :
  - `fr.json` et `wo.json` ont exactement les mêmes clés ;
  - aucun fichier de `src/` ne contient `#1F8A5B` ;
  - `theme.css` contient un seul `@theme` ;
  - il n'existe ni `tailwind.config.*` ni `@config`.
- [x] `infra/caddy/Dockerfile` (nouveau) : étape `node:26…@sha256` qui lance `npm ci && npm run build` dans `web/` ; étape `caddy:2.11.9-alpine@sha256:003a…36f0` qui copie `dist/` dans `/srv/pwa`.
- [x] `infra/Caddyfile` : hôtes `{$APP_HOST}` et `{$MEDIA_HOST}`, TLS automatique (CA interne pour `*.localhost`).
  - `APP_HOST` :
    - `@internal path /metrics /metrics/* /v1/ai /v1/ai/*` → 404 ;
    - `/v1/*`, `/healthz` et `/readyz` → `reverse_proxy api:8000` ;
    - le reste → `root /srv/pwa`, `try_files {path} /index.html`, `file_server`.
  - `MEDIA_HOST` : `reverse_proxy garage:3900 { header_up Host {host} }`.
- [x] `infra/docker-compose.yml` :
  - `caddy` passe de `image:` à `build:` (contexte racine, `infra/caddy/Dockerfile`) ;
  - ports `${HTTP_PORT:-80}:80` et `${HTTPS_PORT:-443}:443` ;
  - environnement `APP_HOST` et `MEDIA_HOST` ;
  - Garage reçoit `root_domain` cohérent si nécessaire.
- [x] `backend/tests/unit/test_layout.py` : retirer `infra/Caddyfile` de la liste si son chemin change. Sinon, aucun changement backend.
- [x] `README.md` (racine) et `web/README.md` :
  - ouvrir `https://app.localhost:<HTTPS_PORT>` ;
  - avertissement du certificat local, ou `docker compose exec caddy caddy trust` pour l'éviter ;
  - commandes web : `npm ci`, `npm run dev`, `npm test`, `npm run build`.
- [x] `backend/scripts/smoke_edge.py` (nouveau, bibliothèque standard, lancé sur l'hôte) : vérifie chaque ligne de la matrice I/O en HTTPS, sans vérifier le certificat local.

**Critères d'acceptation :**
- Étant donné `web/`, quand on lance `npm ci && npm test && npm run build` dans Node 26, alors tout réussit et `dist/` contient `manifest.webmanifest` et `sw.js`.
- Étant donné la pile démarrée, quand on lance `smoke_edge.py`, alors toutes les lignes de la matrice sont vertes.

## Implementation Notes

- **Gabarit.** `create-vite` 9.3.4 (lancé dans le conteneur Node 26) livre oxlint et TypeScript 7 : TypeScript ramené à 6.0.3, oxlint gardé et épinglé (1.95.0, script `lint`). Autres épinglages hors liste : `@vitejs/plugin-react` 6.3.0, `@types/react` et `@types/react-dom` 19.3.0, `@types/node` 26.6.6. Supprimés : logos, `App.css`, `index.css`, `favicon.svg`, `icons.svg`, `src/assets/`, le README du gabarit. `vite-plugin-pwa` tire `workbox-build`, qui dépend de `glob` 11 (avertissement de dépréciation de npm, sans correction possible sans `overrides`).
- **Tests et types.** Le test lit les fichiers avec `node:fs` : il est exclu de `tsconfig.app.json` et compilé par `tsconfig.node.json` (types Node). `npm test` = `vitest run` (`npm test -- --run` passe aussi). Le test balaie aussi tout `web/` (hors `node_modules`, `dist`) pour `tailwind.config.*`, et vérifie en plus qu'aucune couleur hexadécimale n'est écrite hors de `theme.css` ; l'ancien vert y est écrit en deux morceaux.
- **i18n.** `resources` typées (`src/i18n/i18next.d.ts`) : une clé inconnue est refusée par `tsc`. `document.title` = `t('app.name')` ; `lang` de `<html>` suit la langue. Le `<title>` d'`index.html` garde le nom du produit pour l'affichage avant JavaScript.
- **Fond et police.** `bg-surface font-sans text-ink` sur `<body>` d'`index.html` (détecté par Tailwind) ; aucune couche CSS hors du bloc `@theme`.
- **Redirection HTTP.** Bloc `http://{$APP_HOST}, http://{$MEDIA_HOST}` qui redirige (308) vers `https://{host}:{$HTTPS_PORT}{uri}` : la redirection automatique de Caddy viserait le 443 de l'hôte, faux quand Compose publie 443 sur un autre port. Compose passe `HTTPS_PORT` au conteneur. Les autres noms reçoivent la redirection automatique de Caddy.
- **Host vers Garage.** `header_up Host {hostport}` et non `{host}` : `{host}` retire le port, ce qui casserait la signature d'une URL présignée émise pour `media.localhost:<port>`. Avec 443, identiques. `root_domain` de Garage inchangé (`.s3.garage.localhost`) : `media.localhost` n'y correspond pas, l'adressage reste path-style.
- **Routage Caddy.** Trois `handle` exclusifs (internes → 404, API, PWA). `/docs`, `/redoc`, `/openapi.json` ne sont plus relayés (ils servent la PWA) ; README mis à jour. `caddy` attend aussi `garage` (`service_healthy`).
- **Contexte de construction.** `infra/caddy/Dockerfile.dockerignore` n'envoie que `web/` (sans `node_modules` ni `dist`). Le Caddyfile reste monté par Compose.
- **`smoke_readyz.py`.** Il visait `http://localhost:<HTTP_PORT>/readyz`, désormais redirigé vers `https://localhost/` : il réutilise la connexion de `smoke_edge.py` (127.0.0.1, SNI `APP_HOST`, certificat non vérifié). `--base-url` remplacé par `--address`. Les scripts ne résolvent pas `*.localhost` (Windows ne le fait pas).
- **`caddy trust`.** Exécuté dans le conteneur, il n'approuve le CA que dans le conteneur : le README documente l'export de `root.crt` et son import sur l'hôte. `*.crt` ajouté au `.gitignore`.
- **`test_layout.py`.** Chemin du Caddyfile inchangé : aucun changement.

## Spec Change Log

## Review Triage Log

Passe 1 (24/11/2026). Couches : Blind Hunter (B), Edge Case Hunter (E), Verification Gap (V).

| # | Constat | Verdict | Preuve | Route |
|---|---|---|---|---|
| B1 / E1 / V-autre | README : `caddy` « healthy », mais aucun healthcheck | low | Aucun `healthcheck` sur `caddy` dans `docker-compose.yml` | patch (P1) |
| B2 | Icônes PWA absentes | false | `web/public/icon-192.png` et `icon-512.png` existent, exclus du diff (`*.png`) | rejeté |
| B6 | `package-lock.json` absent | false | Présent (264 ko), exclu volontairement du diff | rejeté |
| B3 / E2 | Un fichier statique manquant renvoie `index.html` en 200 | medium | `try_files {path} /index.html` pour tout chemin ; un ancien `/assets/x.js` répond en HTML, d'où une erreur MIME | patch (P2) |
| B4 | Aucun `Cache-Control` sur la PWA | medium | `index.html`, `sw.js` et le manifeste n'ont aucune directive ; les mises à jour `autoUpdate` dépendent des heuristiques | patch (P2) |
| B5 | `MEDIA_HOST` expose toute l'API S3 de Garage | medium | `reverse_proxy garage:3900` relaie toutes les méthodes et tous les chemins (`/`, autres buckets, `DELETE`, `PUT ?acl`) | patch (P3) |
| B7 / E8 | Contrôle du texte dans le bundle fragile (échappements `\u`) | low | Passe aujourd'hui ; correction directe | patch (P4) |
| B8 / E4–E7 / E9 | Robustesse de `smoke_edge.py` (`.env` entre guillemets, entier invalide, exceptions, socket non fermée) | low | Outil manuel ; un échec reste visible | rejeté |
| B9 / E10 | `wo` déclaré : `lang="wo"` sur un texte français | low | Aucun sélecteur de langue : `wo` est inaccessible | rejeté |
| B10 / E11 / E12 | Trous des tests de garde i18n et des couleurs | low | Faux positifs ou négatifs improbables à ce stade | rejeté |
| B11 / V1 / E17 | Accueil et page « introuvable » jamais rendus par un test | medium | Seuls des tests de fichiers existent ; une route `*` supprimée passerait | patch (P5) |
| B12 / E3 | `web/.env*.local` envoyé dans le contexte de construction | medium | `Dockerfile.dockerignore` réinclut tout `web/` ; une valeur `VITE_*` locale finirait dans le bundle public | patch (P6) |
| B13 | Redirection avec `:443` explicite | low | URL valide ; cosmétique | rejeté |
| E13 | Police Inter absente du précache | medium | `sw.js` ne précache que JS, CSS, HTML, PNG et le manifeste ; hors-ligne, la police retombe sur la police système | patch (P7) |
| E14 | `--base-url` supprimé de `smoke_readyz.py` | low | Outil interne, README à jour | rejeté |
| E15 | Suppression du site `:80` attrape-tout | low | Intentionnel : tout passe par `APP_HOST` | rejeté |
| E16 | `{hostport}` au lieu de `{host}` | false | La matrice exige « `Host` conservé » ; `{hostport}` le conserve, port compris, ce que les URL signées exigent | rejeté |
| V2 | Liste d'exclusion du service worker jamais testée | medium | Une regex fausse détournerait `/v1/*` et `/readyz` vers la PWA, sans échec de test | patch (P8) |
| V3 | Couleurs du manifeste recopiées de `theme.css` sans contrôle | low | Dérive silencieuse possible ; correction directe | patch (P8) |
| V4 | `npm test` jamais lancé avant la construction de l'image | medium | Le Dockerfile ne lance que `npm ci` et `npm run build` ; pas de CI | defer (story 1.4) |

## Design Notes

**PWA construite dans l'image Caddy.** On ne monte pas un `dist/` construit sur l'hôte : l'image se reconstruit à l'identique sur le portable de secours et le serveur de démo. Le Node local reste libre pour le développement (`npm run dev` sur le port 5173).

**HTTPS local.** Caddy émet automatiquement des certificats de son CA interne pour `*.localhost`. Chrome affiche un avertissement tant que ce CA n'est pas approuvé. C'est acceptable en développement et documenté dans le README. En démo réelle, `APP_HOST` est un vrai domaine, et Caddy obtient un certificat Let's Encrypt.

## Verification

**Commandes :**
- `docker run --rm -v <repo>:/repo -w /repo/web node:26.13.1-trixie-slim@sha256:abe7… sh -c "npm ci && npm test -- --run && npm run build"` — attendu : succès.
- `docker compose --profile demo up -d --build --wait` (ports libres via `HTTP_PORT` et `HTTPS_PORT`), puis `python backend/scripts/smoke_edge.py` — attendu : succès.
- Navigateur intégré : ouvrir `https://app.localhost:<HTTPS_PORT>/` — attendu : accueil traduit en Inter, sans erreur dans la console.
