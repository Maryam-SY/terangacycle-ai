# Web

PWA React + TypeScript (Vite), hors-ligne, IA dans le navigateur. Aujourd'hui : la coquille (accueil traduit, page « introuvable », manifeste et service worker).

Voir le [dossier technique, section 7](../docs/dossier-technique.md#7-frontend-pwa-hors-ligne-et-inclusion).

## Commandes

Node 26 (`engines` du `package.json`), dans ce dossier :

```bash
npm ci          # dépendances exactes de package-lock.json
npm run dev     # serveur de développement sur http://localhost:5173
npm test        # Vitest (traductions alignées, thème unique)
npm run build   # tsc puis vite build : dist/ avec manifest.webmanifest et sw.js
npm run lint    # oxlint
```

Construction de référence, sans Node 26 local (depuis la racine du dépôt) :

```bash
docker run --rm -v "$PWD:/repo" -w /repo/web node:26.13.1-trixie-slim@sha256:abe7e5a82b61a8ef67b315b85497c9e65173387ccf2f4a029248184b8e020be5 sh -c "npm ci && npm test && npm run build"
```

Avec la pile Docker, Caddy construit la PWA dans son image (`infra/caddy/Dockerfile`) et la sert sur **`https://app.localhost:<HTTPS_PORT>`** (`https://app.localhost` avec le port 443 par défaut). Chrome affiche un avertissement tant que le CA local de Caddy n'est pas approuvé sur la machine : voir le [README racine](../README.md#démarrer-en-local) (export de `root.crt` ; `docker compose exec caddy caddy trust` ne l'approuve que dans le conteneur).

## Règles

- **Aucun texte en dur** : tout passe par `t()` (`src/i18n/`). `fr.json` d'abord ; `wo.json` a exactement les mêmes clés, ses valeurs restent en français en attendant des locuteurs natifs.
- **Couleurs et police** : uniquement dans `src/theme/theme.css`, un seul bloc `@theme` (Tailwind 4, ni `tailwind.config.*` ni `@config`). Police Inter auto-hébergée (`@fontsource-variable/inter`), aucune ressource externe.
- **Versions exactes** : pas de `^` ni de `~`, `package-lock.json` versionné.
- **Arborescence** : `src/features/<écran>/`, `src/i18n/`, `src/theme/` ; `src/api/` (client généré, story 1.6) et `src/offline/` (Dexie, file hors-ligne) sont réservés.
