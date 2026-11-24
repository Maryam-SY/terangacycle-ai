# syntax=docker/dockerfile:1
# Image du bord Caddy : la PWA est construite ici, jamais sur l'hôte, pour que l'image
# se reconstruise à l'identique partout. Contexte : racine du dépôt (seul web/ est envoyé,
# voir Dockerfile.dockerignore). Images de base épinglées par empreinte (AD-28).

# --- Étape de construction : npm ci depuis package-lock.json, puis vite build.
FROM node:26.13.1-trixie-slim@sha256:abe7e5a82b61a8ef67b315b85497c9e65173387ccf2f4a029248184b8e020be5 AS pwa

WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

# --- Étape d'exécution : Caddy et la PWA construite (le Caddyfile est monté par Compose).
FROM caddy:2.11.9-alpine@sha256:003a97808e781aa9f7e75cc2f43d34d461099031faf5e20faefb9f61126836f0

COPY --from=pwa /web/dist /srv/pwa
