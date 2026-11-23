# Revue d'actualité et de compatibilité de l'épine — TerangaCycle AI

- **Date de la revue :** 2026-11-23
- **Objet :** `ARCHITECTURE-SPINE.md` (tableau Stack et toutes les technologies citées dans les AD), et `.memlog.md` (lignes `(version)` et `(assumption)`).
- **Méthode :** interrogation directe des registres le jour même (`npm view`, `https://pypi.org/pypi/<pkg>/json`, API Docker Hub `v2/repositories/.../tags`). Lecture des sources des paquets (`npm pack` et extraction de `onnxruntime-web@1.31.1`, `vite-plugin-pwa@2.0.0`, `workbox-build@7.4.1`, `leaflet.heat@1.0.1`). Résolutions de dépendances rejouées (`npm install --package-lock-only`, `pip install --dry-run`). Lecture de la documentation officielle (Garage, ONNX Runtime Web, arq, PyJWT, Tailwind, openapi-typescript, import-linter, MDN). Les requêtes ne contenaient que des noms de paquets.
- **Non fait :** aucun test d'exécution de conteneur, car le démon Docker n'était pas disponible sur le poste. Les compatibilités Valkey/arq et Garage/boto3 restent donc des **risques à lever par un test d'intégration**. Elles ne sont pas prouvées.

## Verdict

Les numéros de version de l'épine sont exacts : tous ceux de l'échantillon re-vérifié existent et sont les derniers stables, sauf deux écarts mineurs. En revanche, plusieurs **affirmations de compatibilité et d'adéquation n'avaient pas été vérifiées, et deux sont fausses en l'état** :

1. `openapi-typescript` refuse TypeScript 6.0.3 à l'installation.
2. Le précache PWA du Modèle échoue avec la configuration par défaut. En plus, il oublie le binaire WASM d'onnxruntime-web, qui pèse 15 à 30 Mo.

Il faut aussi épingler redis-py en 5.x (pas plus récent), à cause d'arq. Garage ne fournit pas le versionnage d'objets que l'épine promet pour la cible souveraine.

## Synthèse

| # | Sujet | Statut | Gravité |
|---|---|---|---|
| 1 | openapi-typescript 7.13 et TypeScript 6.0.3 | **Faux** : conflit de peer dependency, `npm install` échoue | Haute |
| 2 | vite-plugin-pwa 2.0 : précache du `.onnx` **et** du `.wasm` d'ORT | **Faux** par défaut : le build échoue au-delà de 2 Mio, et le `.wasm` n'est pas prévu | Haute |
| 3 | arq 0.28, redis-py et Valkey 9.2 | **Risque** : arq impose `redis<6`, l'amont est en maintenance seule, Valkey n'est pas testé par l'amont | Moyenne |
| 4 | Garage v2.5 : URL présignées, opérations boto3, mono-nœud | Vérifié, avec **écart** : pas de versionnage ni de SSE, et configuration boto3 à préciser | Moyenne |
| 5 | onnxruntime-web 1.31 : CSP, COOP/COEP, INT8, parité avec Python 1.32 | Vérifié, avec **risques** de configuration et de test doré | Moyenne |
| 6 | Client « généré » (AD-11) : openapi-typescript ne génère que des types | **Lacune** : il faut nommer `openapi-fetch` | Moyenne |
| 7 | Node.js « 24 LTS » | Vérifié, mais **daté** : 24 est en Maintenance LTS, 26 est l'Active LTS | Basse |
| 8 | Leaflet 1.9.4, leaflet.heat 1.0 et React 19 | Vérifié ; react-leaflet 5.0.0 n'est pas nommé ; leaflet.heat 1.0 change d'API | Basse |
| 9 | Tailwind 4 : « un seul thème » | Vérifié ; la forme (`@theme` CSS) est à préciser | Basse |
| 10 | PyJWT 2.15 EdDSA | Vérifié ; l'extra `[crypto]` et le nom d'algorithme sont à préciser | Basse |
| 11 | pydantic-settings « 2.14 » | **Imprécis** : la dernière version est 2.16.3 | Basse |
| 12 | Image `postgis/postgis:16-3.7` | Vérifiée ; **amd64 seulement** | Basse |
| 13 | Idempotence des tâches arq par `_job_id` (AD-8) | **Adéquation partielle** : l'unicité ne dure que pendant `keep_result` | Basse |
| 14 | GeoAlchemy2 0.21 et SQLAlchemy 2.1 | Vérifié (indirectement, par la CI amont) | — |
| 15 | import-linter (AD-1) | Vérifié : 2.17, et les contrats adaptés existent | — |
| 16 | typescript-eslint et TS 6.0 | Vérifié : 8.73.0, `typescript >=4.8.4 <6.1.0` | — |
| 17 | Caddy 2.11.9, `python:3.12-slim`, Valkey 9.2, Garage v2.5.0 (images) | Vérifiés | — |
| 18 | FastAPI 0.165 et OpenAPI 3.1 | Vérifié | — |

---

## 1. openapi-typescript et TypeScript 6.0.3 — **FAUX** (Haute)

- **Constat :**
  - `openapi-typescript@7.13.0` est la dernière version (`latest`, publiée le 2026-02-11, sans version 8). Elle déclare `peerDependencies: { "typescript": "^5.x" }`.
  - Résolution rejouée avec npm 11.19.1 et Node 24.22.2 : `npm install typescript@6.0.3 openapi-typescript@7.13.0` donne `ERESOLVE … peer typescript@"^5.x" from openapi-typescript@7.13.0`. **L'installation échoue.**
  - Avec un `overrides` npm, l'installation passe. La génération fonctionne : sur une spec OpenAPI 3.1 avec `type: ["string","null"]` et `anyOf [number, null]`, le résultat est correct, et `tsc 6.0.3 --strict` passe sur le fichier généré.
- **Source :** `npm view openapi-typescript peerDependencies dist-tags time` ; reproduction locale.
- **Correctif à l'épine** (Stack, ligne TypeScript) :
  > `TypeScript | 6.0.3 (pas 7.0 : typescript-eslint 8.73 exige < 6.1). openapi-typescript 7.13 déclare un peer typescript ^5 : forcer avec "overrides": { "openapi-typescript": { "typescript": "$typescript" } } dans web/package.json (vérifié : génération et tsc OK).`
- Ajouter aussi une ligne `openapi-typescript / openapi-fetch | 7.13 / 0.17` au tableau Stack (voir §6).

## 2. Précache PWA du Modèle et du runtime WASM — **FAUX par défaut** (Haute)

- **Limite de taille par défaut :**
  - Dans `workbox-build@7.4.1`, le schéma fixe `maximumFileSizeToCacheInBytes` à `2097152` (2 Mio).
  - Dans `vite-plugin-pwa@2.0.0`, la source (`chunk-*.js`, `logWorkboxResult`) **lève une erreur de build** quand un fichier dépasse cette limite. C'est le comportement par défaut (`showMaximumFileSizeToCacheInBytesWarning = false`) : le build échoue, ce n'est pas un simple avertissement.
  - Un `.onnx` d'environ 6 Mo **fait donc échouer le build**, si les motifs de fichiers l'incluent.
- **Motifs de fichiers :** le défaut de Workbox est `**/*.{js,wasm,css,html}`. Il ne contient ni `.onnx` ni le `.json` du contrat de Modèle (AD-7). Sans configuration explicite, ces deux fichiers ne sont **pas** précachés, et AD-16 (« chargé … depuis le précache ») est faux.
- **Point oublié par l'épine :** le binaire WASM d'onnxruntime-web, mesuré dans le tarball 1.31.1 :
  - `ort-wasm-simd-threaded.wasm` pèse **14,8 Mo**. C'est celui de l'export `onnxruntime-web/wasm`.
  - L'export par défaut `onnxruntime-web` (`ort.bundle.min.mjs`, qui inclut JSEP/WebGPU) charge `ort-wasm-simd-threaded.jsep.wasm`, soit **29,5 Mo**.
  - La classification hors-ligne (FR-11, FR-17) a besoin de ce `.wasm` en cache. Il dépasse lui aussi les 2 Mio.
- **Compatibilité Vite 8 :** vérifiée. `vite-plugin-pwa@2.0.0` déclare le peer `vite: ^3 … || ^8.0.0`, demande `node >=20.19.0` et dépend de `workbox-build ^7.4.1`.
- **Source :** `npm view vite-plugin-pwa peerDependencies engines` ; lecture des sources de `vite-plugin-pwa-2.0.0.tgz` et de `workbox-build-7.4.1.tgz` ; liste du tarball `onnxruntime-web-1.31.1.tgz` (tailles et table `exports`).
- **Correctif à l'épine** (AD-16, dernière puce, remplacer) :
  > Le Modèle est chargé de façon paresseuse par `features/classify`, depuis le précache. Le runtime est importé par `onnxruntime-web/wasm` (jamais l'export par défaut, qui embarque JSEP/WebGPU, soit un .wasm de 29,5 Mo). Le service worker précache `tc-mnv3-<semver>.onnx`, `tc-mnv3-<semver>.json` et `ort-wasm-simd-threaded.{wasm,mjs}` : `workbox.globPatterns` inclut `onnx,json,wasm,mjs`, et `workbox.maximumFileSizeToCacheInBytes = 20 * 1024 * 1024`. Le build échoue si un de ces fichiers manque au manifeste (test CI).
- Ajouter dans « Conventions » ou dans NFR-12/13 le budget de premier chargement : environ 15 Mo de WASM plus le Modèle, à **mesurer** sur un réseau 3G sénégalais. Ce budget peut remettre en cause la démo hors-ligne si l'installation se fait sur place.

## 3. arq 0.28, redis-py et Valkey 9.2 — **RISQUE** (Moyenne)

- **Constat :**
  - `arq 0.28.0`, publiée le 2026-04-16, exige `redis[hiredis]<6,>=4.2.0` (métadonnées PyPI).
  - La dernière version de redis-py est **8.2.0**, publiée le 2026-11-23. Elle est **incompatible** : `pip install --dry-run arq==0.28.0 redis==8.2.0` donne `ResolutionImpossible`.
  - Le résolveur choisit `redis 5.3.1`, dont la **dernière publication date du 2025-07-25** : plus aucune correction depuis 16 mois. redis 5.3 tire aussi `PyJWT`, ce qui est cohérent avec PyJWT 2.15.
  - Le README d'arq indique : « arq is in maintenance only mode » (issue #510). L'issue #454, qui demande le support des redis-py récents, reste sans suite.
  - Le memlog affirme « arq et redis-py inchangés ». C'est vrai au sens où rien ne change, mais **aucune version de redis-py n'est épinglée dans l'épine**. Un `redis>=6` ajouté pour Valkey (OTP, limites de débit) cassera la résolution.
- **Valkey 9.2 :**
  - L'image `valkey/valkey:9.2` (et `9.2.0`, `-alpine`, `-trixie`) existe pour amd64, arm et arm64. Elle a été mise à jour le 2026-11-19.
  - Valkey se veut compatible avec le protocole Redis OSS 7.2. Les changements de rupture listés pour 9.0 et 9.1 (messages d'erreur, ordre auth/commande, champs `CLUSTER SHARDS`) ne touchent pas un usage simple, sans cluster, comme celui d'arq.
  - **Aucune source amont ne teste arq avec Valkey** : c'est une hypothèse raisonnable, pas une vérification.
- **Source :** PyPI JSON (`arq`, `redis`) ; `pip install --dry-run` ; github.com/python-arq/arq (README) ; notes de compatibilité Valkey (AWS ElastiCache, Percona).
- **Correctif à l'épine :**
  - Tableau Stack, après `arq | 0.28`, ajouter :
    > `redis-py (client, imposé par arq) | 5.3.1 — arq 0.28 exige redis<6 ; ne pas monter tant qu'arq n'a pas levé la borne`
  - Ligne Valkey, garder `[ASSUMPTION]` et compléter :
    > `Valkey 9.2 [ASSUMPTION] — compatibilité arq + redis-py 5.3 à prouver par un test d'intégration CI (conteneur valkey/valkey:9.2.0) : enqueue, job_id dupliqué, retry, cron d'expiration.`
  - Dans « Différé », ajouter :
    > **Remplacement d'arq** (maintenance seule, redis-py figé en 5.x) : à réévaluer avant le pilote. Candidats : SAQ, taskiq. AD-8 isole la file derrière `core/jobs`.

## 4. Garage v2.5 — **VÉRIFIÉ avec écarts** (Moyenne)

- **Ce qui est vérifié** (page officielle « S3 compatibility ») :
  - **URL présignées : implémentées**, avec SigV4.
  - PutObject, GetObject, HeadObject, DeleteObject, CopyObject, ListObjectsV2, CreateBucket, HeadBucket et tout le multipart : implémentés.
  - Adressage en chemin et en sous-domaine : implémentés.
  - Lifecycle : partiel (Expiration et AbortIncompleteMultipartUpload).
  - Cela couvre ce que boto3 utilise pour AD-13 : `put_object`, `get_object`, `head_object`, `delete_object`, `generate_presigned_url('get_object')`. Le presign est calculé côté client, sans appel au serveur.
- **Mono-nœud Docker :**
  - Le guide de démarrage rapide utilise `dxflrs/garage:v2.5.0` avec `garage server --single-node --default-bucket`. L'auto-configuration date de v2.3.0, et les identifiants initiaux passent par `GARAGE_DEFAULT_ACCESS_KEY`, `GARAGE_DEFAULT_SECRET_KEY` et `GARAGE_DEFAULT_BUCKET`.
  - La configuration demande `replication_factor = 1`, `rpc_secret` (32 octets en hex) et `s3_region = "garage"`.
  - `metadata_dir` et `data_dir` valent `/tmp` par défaut : il faut **des volumes**, sinon les données sont perdues.
  - L'image existe pour linux amd64, arm64, arm et 386, mise à jour le 2026-11-23.
  - Le dépôt `minio/minio` est bien en 404 sur Docker Hub, ce qui confirme la justification du memlog.
- **Écarts :**
  - **Pas de versionnage** (« Garage does not (yet) support object versioning ») et **pas de chiffrement côté serveur**, sauf SSE-C.
    - Le diagramme de déploiement promet un « Stockage S3 privé, chiffré, versionné » pour le pilote, et « Garage » pour la cible souveraine. Avec Garage, ces deux propriétés **ne sont pas tenables** nativement.
  - Pas de politiques de bucket ni d'ACL S3 : les droits passent par clé et par bucket. C'est compatible avec « bucket privé », mais il ne faut pas compter sur `PutBucketPolicy`.
  - **boto3 ≥ 1.36 et sommes de contrôle :**
    - boto3 1.44 calcule et valide par défaut des sommes CRC32 (« data integrity protections »). Ce réglage a cassé plusieurs stockages compatibles S3 (Ceph RGW, Storj).
    - **Je n'ai trouvé aucune source qui confirme ou infirme le cas de Garage.** Le risque n'est pas levé.
  - **Hôte des URL signées :**
    - La signature couvre l'en-tête `Host`. Une URL présignée avec l'endpoint interne `http://garage:3900` est inutilisable par la PWA.
    - Une réécriture de chemin par Caddy (`/media/…`) casse la signature.
- **Correctif à l'épine :**
  - AD-13, ajouter à la règle :
    > Le client boto3 est configuré explicitement : `region_name` = `s3_region` de Garage (`garage`), `signature_version="s3v4"`, `addressing_style="path"`, `request_checksum_calculation="when_required"` et `response_checksum_validation="when_required"`. Les URL signées sont produites par un second client dont l'`endpoint_url` est l'hôte public (sous-domaine dédié, relayé par Caddy sans réécriture de chemin et avec l'en-tête Host conservé). Un test d'intégration CI sur `dxflrs/garage:v2.5.0` couvre put, get, head, delete et presign GET.
  - Diagramme de déploiement, cible souveraine : remplacer « Garage » par :
    > Garage (sans versionnage ni SSE : chiffrement du disque (LUKS) et copie quotidienne vers un second stockage)
  - Ou bien : retirer « versionné » de l'exigence quand le stockage est Garage.
  - Compose (Squelette) : préciser que le service `garage` monte des volumes pour `meta` et `data`, et tourne avec `--single-node --default-bucket`.

## 5. onnxruntime-web 1.31 — **VÉRIFIÉ avec risques** (Moyenne)

- **Versions :**
  - `onnxruntime-web` : `latest` est 1.31.1. Il n'existe pas de 1.32 web, seulement `1.33.0-dev`.
  - `onnxruntime` (Python) : 1.32.0, publiée le 2026-11-13, avec des roues `cp312 manylinux_2_28` x86_64 et aarch64. La 1.31.1 existe aussi sur PyPI.
- **COOP/COEP : pas nécessaires** en mono-thread.
  - La source `ort.wasm.min.mjs` contient `crossOriginIsolated)…numThreads=1` : hors isolation cross-origin, ORT passe à un seul thread, avec un simple avertissement si `numThreads > 1` était demandé.
  - La documentation dit que le multi-thread exige « crossOriginIsolated mode ».
  - Recommandation : fixer `ort.env.wasm.numThreads = 1`. Ce réglage est explicite, et il évite d'imposer COEP, qui casserait les tuiles de carte et les URL signées S3 venant d'autres origines.
- **CSP :**
  - `'wasm-unsafe-eval'` est **obligatoire** dans `script-src`. MDN : « If a page has a CSP header and 'wasm-unsafe-eval' isn't specified … WebAssembly is blocked ». ORT utilise `WebAssembly.instantiateStreaming`. On ne trouve ni `eval(` ni `new Function` dans les bundles, donc `'unsafe-eval'` est inutile.
  - Ne **pas** activer `env.wasm.proxy` : il crée un worker depuis un `Blob`, ce qui est incompatible avec une CSP stricte (documentation ORT).
  - Caddy doit servir les `.wasm` en `application/wasm`. C'est le cas par défaut, mais à vérifier en E2E.
- **INT8 dans le navigateur :**
  - Le backend WASM est le CPU EP compilé : il couvre les opérateurs ONNX standard, y compris les opérateurs quantifiés.
  - Aucune table d'opérateurs WASM officielle et récente n'a été trouvée. Le support exact de votre graphe (QDQ statique ou dynamique, `ConvInteger`) n'est **pas** prouvé.
  - Le support d'entrées int8 dans `ConvInteger` est un ajout récent du noyau CPU (#26585).
  - À privilégier : une quantification **statique QDQ** (`quantize_static`, poids s8 et activations u8), plutôt que dynamique.
- **Test doré à 1e-3 (AD-7) :**
  - Python tournera onnxruntime 1.32, le navigateur 1.31.1. Les noyaux INT8 diffèrent selon la plateforme : chemins x86 VNNI/AVX2 côté serveur, WASM SIMD côté navigateur, avec des risques de saturation u8s8.
  - Une tolérance de 1e-3 sur des probabilités issues d'un modèle INT8 est **fragile**.
- **Source :** `npm view onnxruntime-web dist-tags` ; PyPI `onnxruntime` ; tarball 1.31.1 (exports, tailles, grep) ; onnxruntime.ai, « env flags and session options » ; MDN `script-src`.
- **Correctif à l'épine :**
  - Tableau Stack : `onnxruntime (CPU) | 1.31.1` (aligné sur la version web), au lieu de 1.32. Sinon, ajouter : « écart de version accepté, test doré joué dans les deux versions ».
  - AD-7, puce du test doré : ajouter :
    > Le test est joué avec onnxruntime (Python) et onnxruntime-web (Node, backend wasm) **à la même version mineure**, sur l'artefact INT8 réel. Il exige le même `predicted_type` et un écart ≤ 1e-3 sur les probabilités. Le Modèle est quantifié en QDQ statique.
  - AD-16 ou Conventions, ajouter :
    > CSP Caddy : `script-src 'self' 'wasm-unsafe-eval'` ; `ort.env.wasm.numThreads = 1`, `ort.env.wasm.proxy = false` ; pas de COOP/COEP.

## 6. Client « généré » depuis l'OpenAPI (AD-11) — **LACUNE** (Moyenne)

- **Constat :**
  - `openapi-typescript` génère **seulement des types**. Sa documentation cite `openapi-fetch` comme un exemple de client, et ne le présente pas comme une dépendance.
  - La règle « aucun appel `fetch` écrit à la main hors du client généré » suppose un client d'exécution. Sans lui, chaque fonctionnalité écrira son propre `fetch` typé, ce que la règle veut justement empêcher.
  - `openapi-fetch` est à la version 0.17.0 et n'a pas de peer dependency.
- **Compatibilité OpenAPI 3.1 :**
  - Vérifiée. FastAPI 0.165.0 (`fastapi/applications.py`) indique : « FastAPI will generate OpenAPI version 3.1.0 ».
  - openapi-typescript annonce « 3.0 & 3.1 », et le test du §1 le confirme sur les types nullables 3.1.
- **Correctif à l'épine** (AD-11, dernière puce) :
  > Les types sont générés par `openapi-typescript` (7.13) depuis `/openapi.json` (OpenAPI 3.1 de FastAPI) ; le seul client HTTP est une instance `openapi-fetch` (0.17), enveloppée dans `web/src/api/` (injection du jeton, `X-Device-Id`, enveloppe d'erreur). Aucun `fetch` hors de ce client et de l'outbox. La CI échoue si les types générés diffèrent de l'OpenAPI courant.

## 7. Node.js « 24 LTS » — **DATÉ** (Basse)

- **Constat** (`nodejs/Release/schedule.json`) :
  - v24 « Krypton » : LTS le 2025-10-28, **Maintenance depuis le 2026-10-20**, fin le 2028-04-30.
  - v26 « Lithium » : **Active LTS depuis le 2026-10-28**, fin le 2029-04-30.
  - Sur Docker Hub, `node:lts` pointe désormais vers 26 (`lts-lithium`, 26.13.1).
  - Tous les outils acceptent 24 : vite `^20.19 || >=22.12`, vitest `^22.12 || ^24 || >=26`, eslint 10 `>=24`, vite-plugin-pwa `>=20.19`.
- **Correctif :** `Node.js (outillage) | 24 LTS (Maintenance jusqu'au 2028-04-30)`. Sinon, passer à `26 LTS (Active)`, qui est compatible avec les mêmes outils. **Ne pas** écrire `node:lts` dans la CI, qui suit désormais 26.

## 8. Leaflet 1.9.4, leaflet.heat et React 19 — **VÉRIFIÉ, à compléter** (Basse)

- **Leaflet :**
  - `leaflet` : `latest` est 1.9.4 ; `beta` est 2.0.0-beta.5, publiée le 2026-11-19. La phrase « 2.0 encore en bêta » est exacte.
  - `@types/leaflet` : 1.9.22.
- **react-leaflet :**
  - **react-leaflet 5.0.0** (et `@react-leaflet/core 3.0.0`) déclare `leaflet ^1.9.0`, `react ^19.0.0` et `react-dom ^19.0.0`. Elle est compatible avec React 19.3.
  - L'épine **ne la nomme pas**, alors qu'elle est la manière standard d'intégrer Leaflet à React.
- **leaflet.heat :**
  - `leaflet.heat 1.0.1` est un **nouveau majeur**, publié le 2026-11-03 puis le 2026-11-13 par le mainteneur historique, `mourner`. Le dépôt est `Leaflet/Leaflet.heat`.
  - Le paquet est **ESM seul** (`"type": "module"`, export `./src/HeatLayer.js`). Il expose `import {HeatLayer} from 'leaflet.heat'`, qui étend `L.Layer`. Ce n'est plus l'API `L.heatLayer(...)` de la 0.2.
  - Peer : `leaflet ^1.9.0 || ^2.0.0-beta.1`. Le README précise que les types fournis visent **Leaflet 2.0**, d'où des conflits possibles avec `@types/leaflet` 1.9.
  - Le paquet n'a que 3 semaines : c'est un risque de jeunesse.
- **Correctif à l'épine** (Stack) :
  > `Leaflet + react-leaflet + leaflet.heat | 1.9.4 / 5.0 / 1.0.1 — leaflet.heat 1.0 est ESM (new HeatLayer), types écrits pour Leaflet 2 : envelopper dans un composant via @react-leaflet/core (createLayerComponent)`

## 9. Tailwind 4 et « un seul thème » (AD-16) — **VÉRIFIÉ, à préciser** (Basse)

- **Constat :**
  - Tailwind 4.3.5 est configuré d'abord en CSS : les jetons sont déclarés dans `@theme { --color-… }`, qui génère les utilitaires et les variables CSS.
  - `tailwind.config.js` n'est plus lu que par `@config`, décrit comme existant « solely for compatibility with Tailwind CSS v3.x ». `corePlugins`, `safelist` et `separator` ne sont pas supportés.
  - Le plugin `@tailwindcss/vite 4.3.5` déclare le peer `vite ^…||^8`.
- **Correctif** (AD-16, puce des jetons) :
  > Les jetons de design (dont `--color-brand-600: #187A50`) sont définis dans **un seul** bloc `@theme` de `web/src/theme/theme.css` ; pas de `tailwind.config.js` ni de `@config`. L'intégration passe par `@tailwindcss/vite`.

## 10. PyJWT 2.15 et EdDSA (AD-9) — **VÉRIFIÉ, à préciser** (Basse)

- **Constat :**
  - La documentation PyJWT indique : « Both Ed25519 … and Ed448 … are supported ». Le nom d'algorithme JOSE est `EdDSA`.
  - Les algorithmes asymétriques passent par `cryptography`, installée par l'extra `pyjwt[crypto]` (`cryptography>=3.4.0`). La dernière version de cryptography est 50.0.2.
  - Le CHANGELOG de 2.10 à 2.15 ne mentionne pas RFC 9864, qui déprécie l'identifiant `EdDSA` au profit de `Ed25519`. PyJWT n'accepte donc pas encore `alg: Ed25519`.
- **Correctif :**
  - Stack : `PyJWT[crypto] | 2.15 (cryptography 50)`.
  - AD-9 : préciser
    > clé Ed25519 ; `jwt.decode(..., algorithms=["EdDSA"], audience=…, issuer=…)` avec liste d'algorithmes fermée.

## 11. pydantic-settings « 2.14 » — **IMPRÉCIS** (Basse)

- **Constat :** `pydantic` est en 2.14.4 (publiée le 2026-11-19) et `pydantic-settings` en **2.16.3** (publiée le 2026-11-13). La version 2.14 de pydantic-settings existe, mais elle n'est pas la dernière.
- **Correctif :** `Pydantic / pydantic-settings | 2.14 / 2.16`.

## 12. PostgreSQL + PostGIS `postgis/postgis:16-3.7` — **VÉRIFIÉ, une réserve** (Basse)

- **Constat :**
  - Le tag existe et a été mis à jour le 2026-11-21, mais **pour linux/amd64 seulement**, comme tous les tags `postgis/postgis`.
  - Le « portable de secours » du hackathon, s'il est en ARM (Apple Silicon), tournerait PostGIS en émulation (lente) ou ne démarrerait pas.
  - Les tags 17-3.7 et 18-3.7 existent aussi. PostgreSQL 16 reste supporté jusqu'en novembre 2028, ce qui suffit pour le pilote.
- **Correctif :** dans « Déploiement », ajouter :
  > Le portable de secours est x86_64 (l'image `postgis/postgis` n'existe qu'en amd64) ; à défaut, une image PostGIS multi-arch est à valider avant le jour J.

## 13. Idempotence des tâches arq (AD-8) — **ADÉQUATION PARTIELLE** (Basse)

- **Constat** (documentation arq) :
  - `enqueue_job` renvoie `None` si l'identifiant existe, mais un job « cannot be enqueued again until its execution has finished and its result has cleared ».
  - `keep_result` vaut 3600 s par défaut. Au-delà de cette heure, le même `<type>:<entity_id>` peut être **rejoué**.
- **Correctif** (AD-8, puce de l'identifiant) :
  > L'identifiant `<type>:<entity_id>` déduplique les mises en file concurrentes ; l'effet est rendu idempotent **dans le service** (écriture conditionnelle ou contrainte unique), car l'unicité arq expire avec `keep_result`.

## 14. GeoAlchemy2 0.21 et SQLAlchemy 2.1 — **VÉRIFIÉ (indirect)**

- GeoAlchemy2 0.21.0, publiée le 2026-11-04, demande `SQLAlchemy>=1.4`.
- Son `tox.ini` teste `sqla{14,latest}` sur Python 3.10 à 3.13, et la CI « CI success 2026-11-04 » a tourné à la date de la release.
- À cette date, la dernière version de SQLAlchemy était **2.1.6** : 2.1.0 est sortie le 2026-09-24, et SQLAlchemy est aujourd'hui en 2.1.9.
- Alembic 1.20.1 demande `SQLAlchemy>=2.0`. psycopg est en 3.3.9.
- **Aucun correctif.** On peut éventuellement épingler `SQLAlchemy 2.1.x` (sans `>=`).

## 15. import-linter (AD-1) — **VÉRIFIÉ**

- La version 2.17 a été publiée le 2026-11-18. Elle demande Python 3.11 ou plus et `grimp>=3.20`.
- Les contrats intégrés sont : Forbidden, **Protected** (« Prevent modules from being directly imported, except by modules in an allow-list »), Layers, Independence, Private modules et **Acyclic siblings**.
- Le graphe d'AD-1 s'exprime directement : `layers` (router → service → repository) avec containers par module, `protected` ou `forbidden` pour `models`, `repository` et `router`, et `acyclic_siblings` sur `app.modules`.
- **Correctif mineur :** nommer la version dans le tableau Stack (`import-linter | 2.17`) et les types de contrats dans AD-1.

## 16. typescript-eslint et TypeScript 6.0 — **VÉRIFIÉ**

- `typescript-eslint@8.73.0` déclare le peer `typescript >=4.8.4 <6.1.0` et `eslint ^8.57 || ^9 || ^10`. Le choix 6.0.3 est donc exact.
- TypeScript : `latest` est **7.0.2**, et 6.0.3 est la dernière 6.x.
- `react-i18next@18.0.3` accepte `typescript ^5||^6||^7`.
- **Aucun correctif**, hors §1.

## 17. Images Docker — **VÉRIFIÉES**

| Image | Constat (Docker Hub, 2026-11-23) |
|---|---|
| `caddy:2.11.9` | Existe en linux amd64, arm, arm64, ppc64le, riscv64 et s390x (plus windows) ; mise à jour le 2026-11-16 ; variante `2.11.9-alpine` aussi. |
| `python:3.12-slim` / `3.12.16-slim` | Existe ; mise à jour le 2026-11-08. **Base Debian trixie** par défaut (`-bookworm` reste disponible). Python 3.12 est en phase de correctifs de sécurité seulement, jusqu'en octobre 2028. Toutes les dépendances Python ont des roues ou acceptent cp312 (vérifié pour onnxruntime 1.32 et Pillow 13). |
| `valkey/valkey:9.2.0` | Existe (voir §3). `library/valkey` n'existe pas : utiliser l'espace de noms `valkey/`. |
| `dxflrs/garage:v2.5.0` | Existe (voir §4). |
| `postgis/postgis:16-3.7` | Existe, amd64 seulement (voir §12). |

- **Correctif mineur :** écrire les tags exacts et la base Debian dans le Squelette, par exemple `python:3.12.16-slim-trixie`, `valkey/valkey:9.2.0`, `dxflrs/garage:v2.5.0`, `caddy:2.11.9-alpine` et `postgis/postgis:16-3.7`, et les épingler par digest (cohérent avec « images épinglées »).

## 18. FastAPI 0.165 — **VÉRIFIÉ**

- FastAPI 0.165.0 a été publiée le 2026-11-18. Elle demande Python 3.11 ou plus, `starlette>=1.6.0` et `pydantic>=2.9.0`, et génère de l'OpenAPI 3.1.0 (source).

## Re-vérification d'un échantillon des versions du memlog

Toutes les versions de l'échantillon correspondent au registre le 2026-11-23 :

- **npm :** vite 8.3.8, vite-plugin-pwa 2.0.0, react 19.3.1, dexie 4.4.7, onnxruntime-web 1.31.1, @tanstack/react-query 5.108.4, i18next 27.2.5, react-i18next 18.0.3, tailwindcss 4.3.5, vitest 5.1.1, @playwright/test 1.65.1, leaflet 1.9.4, leaflet.heat 1.0.1.
- **PyPI :** fastapi 0.165.0, pydantic 2.14.4, sqlalchemy 2.1.9, geoalchemy2 0.21.0, alembic 1.20.1, psycopg 3.3.9, arq 0.28.0, onnxruntime 1.32.0, pillow 13.0.0, pyjwt 2.15.1, boto3 1.44.9, structlog 26.1.0, torch 2.15.0, torchvision 0.29.2 (roue `py3-none`, `torch>=2.14.0`, donc compatible), pytest 9.2.0.

Seuls écarts : pydantic-settings (§11) et l'absence d'épinglage de redis-py (§3).

## Liste des modifications à apporter à l'épine (récapitulatif)

1. Stack, TypeScript : ajouter l'`overrides` pour openapi-typescript (§1).
2. Stack : ajouter `openapi-typescript / openapi-fetch 7.13 / 0.17`, `redis-py 5.3.1 (imposé par arq)`, `react-leaflet 5.0`, `import-linter 2.17`, `PyJWT[crypto]`, `@tailwindcss/vite` ; corriger pydantic-settings en 2.16 ; aligner `onnxruntime` sur 1.31.1 ou documenter l'écart.
3. AD-16 : imports `onnxruntime-web/wasm`, `globPatterns` et `maximumFileSizeToCacheInBytes` (20 Mio), précache du `.wasm`, jetons dans `@theme` (§2, §9).
4. AD-11 : client d'exécution `openapi-fetch` (§6).
5. AD-13 : configuration boto3 explicite (région `garage`, sommes de contrôle `when_required`, chemin), client de signature sur l'hôte public, test d'intégration Garage (§4).
6. Déploiement : Garage sans versionnage ni SSE pour la cible souveraine ; volumes Garage ; portable de secours x86_64 (§4, §12).
7. AD-7 : test doré à version ORT identique, quantification QDQ statique (§5).
8. Conventions ou AD-16 : CSP `'wasm-unsafe-eval'`, `numThreads = 1`, `proxy = false`, sans COOP/COEP (§5).
9. AD-8 : idempotence dans le service, au-delà de `keep_result` (§13).
10. Valkey : test d'intégration CI ; « Différé » : réévaluer arq avant le pilote (§3).
11. Node : préciser « Maintenance LTS » ou passer à 26 (§7).
