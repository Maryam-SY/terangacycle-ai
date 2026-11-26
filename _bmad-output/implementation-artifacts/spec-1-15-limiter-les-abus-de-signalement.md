---
title: 'Story 1.15 — Limiter les abus de signalement'
type: 'feature'
created: '2026-11-26'
status: 'ready-for-dev'
baseline_commit: 'd1ebcca5ccaa748d5bbf264ff8f9dcebd85e585d'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-12-renvoyer-un-signalement-sans-doublon-ni-fuite.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `POST /v1/reports` est public et anonyme : un seul téléphone, ou un script qui change d'Identifiant d'appareil ou d'en-tête `X-Forwarded-For`, peut noyer la File de modération. Rien ne limite aujourd'hui le nombre de Signalements, et l'API ne voit pas la vraie IP du client derrière Caddy.

**Approach:** créer `core.ratelimit` (fenêtre fixe sur Valkey AOF, vérification et incrément atomiques, clés hachées) et l'appliquer :
- dans `reports.service.create_report`, après la recherche du renvoi idempotent et avant tout traitement : portées `report:device` (Principal `device`) ou `report:user` (Principal `user`), plus `report:ip` ;
- dans `core.security.principal()`, pour un Principal `user` seulement : portée `user:any` sur toute route ;
- dépassement : 429 `rate_limited` avec `Retry-After` (secondes jusqu'à la fin de la fenêtre).

L'IP vient de `request.client.host`, réécrite par uvicorn `--proxy-headers` pour la seule IP de Caddy, qui remplace `X-Forwarded-For`. Les critères d'acceptation de référence sont ceux de la section `### Story 1.15` d'`_bmad-output/planning-artifacts/epics.md`.

## Boundaries & Constraints

**Always:**
- **Réglages nommés** (`Settings` et `.env.example`) : `RATE_REPORT_DEVICE_PER_H=10`, `RATE_REPORT_IP_PER_H=10`, `RATE_REPORT_USER_PER_H=10`, `RATE_USER_ANY_PER_MIN=60` (entiers ≥ 1), lus depuis les réglages de l'application.
- **`core.ratelimit`** : module feuille (`config`, `clock`, `errors`, `logging` seulement) ; client Valkey synchrone (`redis==5.3.1`), mis en cache par URL comme `storage._s3_client` ; clé `rl:<portée>:<empreinte>:<n° de fenêtre>`, fenêtre = `floor(core.clock.now() / durée)`, TTL = fin de fenêtre + marge ; un script Lua vérifie puis incrémente : un refus ne consomme rien. `Retry-After` = secondes restantes arrondies au supérieur, au moins 1, calculées avec `core.clock`.
- **Empreintes :** jamais une IP, un Identifiant d'appareil ni un identifiant de compte en clair dans une clé ou un journal. Appareil : `principal.device_hash` ; IP et compte : HMAC-SHA256 avec la clé DEVICE_ID_PEPPER déjà décodée (`app.state.device_id_key`), séparée par domaine (`ip:`, `user:`), calculée dans `core.security` ; aucun nouveau secret (inventaire AD-26 figé).
- **IP :** seul `core.security` lit `request.client.host` ; le router passe son empreinte au service (`client_ip_digest`, paramètre nommé facultatif, `None` sans client : portée IP ignorée). Aucun code ne lit `X-Forwarded-For`.
- **Ordre dans `create_report`** : verrou et renvoi idempotent (story 1.12, un renvoi ne consomme rien) → limites → consentement, Zone, photo, écriture (inchangés). Un 429 n'écrit ni ligne ni objet et ne lit pas la photo.
- **Seuls les Signalements créés comptent :** chaque jeton accordé dans l'unité de travail est rendu par `after_rollback` (refus ultérieur 422, 413, 415, course perdue, autre portée refusée). `user:any` compte chaque requête, sans remboursement.
- **429 :** `DomainError` accepte des en-têtes facultatifs, repris par son gestionnaire ; code `rate_limited` dans `codes.py`, `DEFAULT_MESSAGES`, `errors.rate_limited` (`fr.json`, `wo.json`) : « Vous avez fait beaucoup de demandes. Merci ! Patientez un peu, puis réessayez. » ; 429 dans les `responses=` de la route.
- **Bord :** uvicorn `--proxy-headers --forwarded-allow-ips=${CADDY_IPV4}` (jamais `*`), Caddy à adresse fixe sur le réseau Compose (sous-réseau déclaré), `header_up X-Forwarded-For {remote_host}` dans le `reverse_proxy` de l'API. Valkey publié sur `127.0.0.1:${VALKEY_LOCAL_PORT:-6379}` seulement, pour les tests d'intégration.
- **PWA (écran 3) :** sur 429, « Vous avez envoyé beaucoup de Signalements. Merci ! Réessayez dans {{minutes}} min. » (clé de l'écran, `minutes = ceil(Retry-After / 60)`, au moins 1), brouillon conservé, message en Encre avec icône rouge.

**Never:**
- aucune limite dans Caddy ; aucune lecture de `X-Forwarded-For` dans le code ;
- `user:any` jamais appliquée à un Principal `device` ;
- pas de portées OTP ni `sms:daily` (Epic 2) ;
- aucun mock de Valkey, de base ni de Garage dans les tests d'intégration.

## I/O & Edge-Case Matrix

| Scénario | Entrée / État | Attendu |
|---|---|---|
| Appareil | 10 créés dans l'heure, même `X-Device-Id` ; 11e | 429 `rate_limited`, `Retry-After` = fin de fenêtre ; ni ligne ni objet, photo non lue |
| IP | 10 créés depuis une IP, 10 appareils ; 11e, nouvel appareil | 429 |
| `X-Forwarded-For` falsifié | Derrière Caddy, 11 envois, 11 XFF et 11 appareils différents | 11e : 429 |
| Renvoi | 10 créés ; renvoi de l'un (même `client_uuid`) | 200 avec l'existant ; compteurs inchangés |
| Échec après limite | 422 `outside_active_zone` ou photo refusée | compteurs rendus (le 10e Signalement reste possible) |
| Fenêtre suivante | horloge + 1 h | 201 |
| Redémarrage | 10 créés ; `api` et `valkey` redémarrés ; 11e | 429 (AOF) |
| `report:user` | Principal `user` construit, 11e création dans l'heure (service) | 429 |
| `user:any` | Principal `user`, 61e requête dans la minute, route quelconque | 429 ; Principal `device` : jamais |
| Clés | Valkey inspecté après les cas ci-dessus | aucune IP ni aucun Identifiant d'appareil en clair dans les clés |
| PWA | 429, `Retry-After: 150` | « Réessayez dans 3 min. », brouillon gardé |

**Décision (26/11/2026, validée par l'utilisatrice) :** si Valkey est indisponible pendant `POST /v1/reports`, la limite est sautée (ouverture en cas de panne) : le Signalement est accepté, la panne est journalisée (`ratelimit_unavailable`, sans donnée personnelle) ; aucune réponse 503 pour cette raison.

</frozen-after-approval>


## Code Map

- `backend/app/modules/reports/service.py` -- `create_report` : insérer les limites juste après `_existing_outcome` (le verrou consultatif garde les envois simultanés du même `client_uuid` en série, donc un seul jeton consommé) ; `CreateReport` et `_settle_parallel_sends` gagnent `client_ip_digest`. Ne pas toucher au chemin de renvoi.
- `backend/app/modules/reports/router.py` -- route `create_report`, `ERROR_RESPONSES`/`RESPONSES` (+ 429), passage de l'empreinte IP ; `ReportUploadGuard` inchangé.
- `backend/app/core/security.py` -- `principal()`, `Principal`, `app_device_id_key` : ajouter les empreintes IP et compte et l'appel `user:any` pour `kind == "user"` (identification séparée en une fonction pour que le test produise un Principal `user`).
- `backend/app/core/errors/__init__.py` -- `DomainError` (+ `headers`), `_domain_error_handler` ; `error_response` sait déjà poser des en-têtes.
- `backend/app/core/errors/codes.py`, `web/src/i18n/fr.json`, `wo.json` -- `rate_limited`.
- `backend/tests/unit/test_errors.py` (liste codée en dur, l. ~236) ; `backend/tests/unit/test_error_messages.py` (l. 65-75 : `rate_limited` sert de code fictif, à remplacer par un autre nom fictif).
- `backend/app/core/config.py` -- `valkey_url` existe ; modèle `report_accuracy_flag_m`.
- `backend/app/core/health.py` -- `_redis()` : modèle de client (délais 3 s), asynchrone ; ne pas le réutiliser (le service est synchrone).
- `backend/tests/asgi.py` -- `"client": ("127.0.0.1", 50000)` codé en dur : paramètre `client_host` ; `backend/tests/reports.py` `post_report` le relaie.
- `backend/tests/integration/test_reports_api.py` -- fixture `stack` : `VALKEY_URL` = `TEST_VALKEY_URL` (base Valkey 15 réservée aux tests, `FLUSHDB` avant et après chaque test) ; le test des 20 créations simultanées relève les plafonds par l'environnement.
- `infra/docker-compose.yml` -- `api.command` (uvicorn), réseau par défaut avec `ipam`, `caddy` `ipv4_address`, `valkey.ports`.
- `infra/Caddyfile` -- `handle @api { reverse_proxy api:8000 }`.
- `.github/workflows/ci.yml` -- étape « URL de test » (+ `TEST_VALKEY_URL`), job `edge` (+ `smoke_ratelimit.py` après `smoke_readyz.py`).
- `backend/scripts/smoke_edge.py`, `smoke_readyz.py` -- modèles (bibliothèque standard, `--address`, redémarrage par `docker compose`). `smoke_edge.py` crée déjà 1 Signalement depuis l'IP du runner : le nouveau script reçoit `--prior-reports 1`.

**Fichiers créés ou modifiés (exhaustif) :**
- créés : `backend/app/core/ratelimit.py`, `backend/tests/integration/test_ratelimit.py`, `backend/tests/unit/test_ratelimit.py`, `backend/scripts/smoke_ratelimit.py` ;
- modifiés (backend et infra) : `backend/app/core/config.py`, `backend/app/core/security.py`, `backend/app/core/errors/__init__.py`, `backend/app/core/errors/codes.py`, `backend/app/modules/reports/service.py`, `backend/app/modules/reports/router.py`, `.env.example`, `infra/docker-compose.yml`, `infra/Caddyfile`, `.github/workflows/ci.yml`, `backend/tests/conftest.py`, `backend/tests/asgi.py`, `backend/tests/reports.py`, `backend/tests/integration/test_reports_api.py`, `backend/tests/unit/test_config.py`, `backend/tests/unit/test_security.py`, `backend/tests/unit/test_errors.py`, `backend/tests/unit/test_error_messages.py`, `web/src/i18n/fr.json`, `web/src/i18n/wo.json`, `README.md` ;
- modifiés (PWA, après la story 1.13, noms de sa spec) : `web/src/features/report/DetailsPage.tsx`, `web/src/features/report/details.ts` et `details.test.ts` (décision d'erreur : 429 → minutes depuis `Retry-After`), `web/src/api/client.ts` et `client.test.ts` (exposer `Retry-After` sur l'erreur), `web/src/api/openapi.json` et `web/src/api/schema.d.ts` (régénérés : 429 ajouté au contrat).
- **Migration :** aucune.

## Tasks & Acceptance

**Execution:**
- [ ] `backend/app/core/ratelimit.py` -- `limit(scope, digest, settings) -> Grant` (refus : `DomainError` 429 avec `Retry-After`), `Grant.refund()` -- brique unique d'AD-20.
- [ ] `backend/app/core/config.py`, `.env.example`, `backend/tests/conftest.py` -- quatre plafonds -- AD-14.
- [ ] `backend/app/core/errors/` et i18n -- en-têtes de `DomainError`, `rate_limited`.
- [ ] `backend/app/core/security.py` -- empreintes IP et compte, `user:any`.
- [ ] `backend/app/modules/reports/` (service, router) -- portées, remboursement `after_rollback`, 429 documenté.
- [ ] `infra/docker-compose.yml`, `infra/Caddyfile`, `.github/workflows/ci.yml` -- proxy de confiance, Valkey sur 127.0.0.1, variables et étape de CI.
- [ ] **Tests :**
  - intégration Valkey réel : atomicité (20 fils sur un plafond de 10 → exactement 10 accordés), TTL, `Retry-After` à horloge simulée, refus sans incrément, `SCAN rl:*` sans valeur en clair ;
  - intégration API : chaque ligne de la matrice hors bord et PWA, avec comptage base et bucket ; `user:any` par une route de test montée sur l'application du test et un Principal `user` produit par la fonction d'identification remplacée ;
  - unitaire : clés, fenêtre, arrondi de `Retry-After`, réglages, `user:any` ignoré pour `device` ;
  - `smoke_ratelimit.py` (job `edge`) : `10 − prior` envois → 201 avec XFF et appareils tous différents, puis 429 ; redémarrage de `valkey` et `api` (attente « healthy »), puis 429 pour un appareil déjà compté (depuis un seul hôte, l'IP est épuisée elle aussi : le test prouve la persistance AOF des compteurs, commune à toutes les portées ; la persistance par appareil repose sur le même mécanisme).
- [ ] PWA (après 1.13) : message de l'écran 3 sur 429 (test Vitest : `Retry-After` 150 → 3 min, 30 → 1 min, brouillon gardé) ; régénération du contrat OpenAPI.
- [ ] `README.md` -- limites, proxy de confiance, `VALKEY_LOCAL_PORT`.

**Acceptance Criteria:**
- Tous les critères d'acceptation de la story 1.15 d'`epics.md` sont couverts par au moins un test qui tourne en CI.
- Given le job `edge` sur une pile neuve, when `smoke_edge.py`, `smoke_readyz.py` puis `smoke_ratelimit.py --prior-reports 1` s'exécutent, then les trois sont verts.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run lint-imports && REQUIRE_INTEGRATION=1 uv run pytest --cov` (backend, pile réelle : base, Garage, Valkey sur 127.0.0.1) -- expected: vert, couverture ≥ 60 %.
- `python backend/scripts/smoke_edge.py && python backend/scripts/smoke_readyz.py && python backend/scripts/smoke_ratelimit.py --prior-reports 1` (pile `demo` neuve) -- expected: code 0.
- `npx vitest run` (web, après 1.13) -- expected: vert.
