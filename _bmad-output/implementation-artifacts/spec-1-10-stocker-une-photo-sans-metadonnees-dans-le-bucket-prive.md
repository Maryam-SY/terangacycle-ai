---
title: 'Story 1.10 — Stocker une photo sans métadonnées dans le bucket privé'
type: 'feature'
created: '2026-11-25'
status: 'done'
baseline_commit: 'b9c589bf643e6efed5c241af3a2fd9eadd2c9d6d'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Le serveur ne sait pas encore recevoir une photo. Sans contrôle, un fichier piégé, une bombe de décompression ou une photo pleine de données EXIF/GPS pourrait être conservée ou exposée, et un échec en cours de transaction laisserait des objets orphelins dans Garage.

**Approach:** Un module `core.storage`, seul à parler S3 pour écrire, offre `ingest_photo(kind, data)` (contrôle des octets, ré-encodage JPEG sans métadonnées, rangement dans le bucket privé, nettoyage par `after_rollback`) et `purge(object_keys)` (suppression par `after_commit`). Ces briques seront appelées par la story 1.11 (Signalement) et l'epic 5 (preuves).

## Boundaries & Constraints

**Always:**
- Contrôles dans cet ordre, tous **avant** l'écriture S3 :
  1. plus de 1 Mo (1 000 000 octets) → 413 `photo_too_large` ;
  2. type lu dans les octets (JPEG `FF D8 FF`, PNG, WebP `RIFF…WEBP`), jamais le nom ni le Content-Type → sinon 415 `unsupported_media_type` ;
  3. plus de 12 000 000 pixels, lu dans l'en-tête avant décodage complet, `Image.MAX_IMAGE_PIXELS` réglé explicitement → 422 `photo_too_many_pixels` ;
  4. décodage impossible ou tronqué → 422 `photo_unreadable`.
- Ré-encodage : `ImageOps.exif_transpose()`, puis RGB (transparence posée sur fond blanc), puis JPEG qualité 85, sans EXIF, GPS, ICC ni XMP.
- Valeur rendue :
  - `object_key` de la forme `<kind>/<yyyy>/<mm>/<uuid>.jpg`, mois UTC de `core.clock.now()`, `<uuid>` = identifiant de la future ligne photo (fourni ou généré, et rendu) ;
  - `sha256` des **octets reçus** ;
  - largeur et hauteur de l'image stockée.
- `ingest_photo` exige une unité de travail en cours. Le nettoyage `after_rollback` est enregistré avant l'envoi S3.
- `purge` ne supprime rien tant que le commit n'est pas fait. Supprimer un objet absent n'est pas une erreur.
- Client S3 configuré comme AD-13 : `s3v4`, path-style, sommes de contrôle `when_required`, région `garage`.
- Aucun octet de photo, clé S3 ni identifiant dans les messages d'erreur. Le journal ne porte que le type d'exception.
- Chaque nouveau code a son message `errors.<code>` dans `fr.json` et `wo.json`. Le message dit au Citoyen quoi faire.

**Never:**
- pas de route HTTP, de table `report_photos` ni de miniature : c'est la story 1.11 ;
- pas d'URL signée ni de client `MEDIA_HOST` (lecture des photos, epic 4) ;
- pas de balayage des orphelins (AD-18, story 1.16) ;
- pas de modification de la sonde `/readyz` ;
- pas de mock de Garage dans les tests d'intégration.

## I/O & Edge-Case Matrix

| Scénario | Entrée | Résultat attendu |
|---|---|---|
| JPEG avec EXIF+GPS, orientation 6 | 800×600 | objet JPEG 600×800 relu sans segment APP1 Exif ; clé `report/2026/11/<uuid>.jpg` |
| PNG transparent / WebP | valides | objet JPEG RGB |
| Trop lourd | 1 000 001 octets | 413 `photo_too_large`, aucun objet |
| Faux type | GIF, PDF, texte renommé `.jpg` | 415 `unsupported_media_type`, aucun objet |
| Trop de pixels | PNG 4000×3001 (≤ 1 Mo) | 422 `photo_too_many_pixels`, aucun objet |
| Corrompue | JPEG tronqué | 422 `photo_unreadable`, aucun objet |
| Rollback | exception après `ingest_photo` | objet supprimé ; nombre d'objets du bucket identique avant/après |
| `purge` puis rollback | — | objet toujours présent |
| `purge` d'une clé absente | — | aucune erreur |

</frozen-after-approval>

## Code Map

- `backend/app/core/db.py` : `after_commit`, `after_rollback`, `_require_uow`, `unit_of_work()`. Un hook en échec est journalisé sans être relancé. À réutiliser tel quel.
- `backend/app/core/errors/codes.py` : `ErrorCode` et `DEFAULT_MESSAGES`. `core/errors/__init__.py` : `DomainError(code, http_status)`.
- `backend/app/core/enums.py` : ajouter `PhotoKind` (`report`, `report_thumb`, `before`, `after`, `lot`, AD-13).
- `backend/app/core/config.py` : `s3_endpoint`, `s3_region`, `s3_bucket`, `s3_access_key_id`, `s3_secret_access_key` existent déjà.
- `backend/app/core/health.py` : `_s3_client` (sonde, délais d'1 s, aucun nouvel essai). **Ne pas toucher** : ses tests le remplacent par monkeypatch.
- `backend/tests/unit/test_error_messages.py` : vérifie déjà la parité codes ↔ `fr.json`/`wo.json`.
- `backend/tests/integration/test_zones.py` : modèle des tests d'intégration (ignorés sans variables, sauf `REQUIRE_INTEGRATION=1`).
- `backend/tests/conftest.py` : `_SETTINGS_ENV_VARS` à compléter si de nouvelles variables sont lues.
- `infra/docker-compose.yml` (service `garage`, S3 sur 3900, non publié) ; `.github/workflows/ci.yml` (exporte `TEST_*_DATABASE_URL`).
- Spine : Pillow 13.0, Garage v2.5.0.

## Tasks & Acceptance

**Execution:**
- [x] `backend/pyproject.toml`, `uv.lock` : ajouter `pillow==13.0.*` (version exacte publiée, verrouillée).
- [x] `backend/app/core/enums.py` : `PhotoKind`.
- [x] `backend/app/core/errors/codes.py` et `web/src/i18n/{fr,wo}.json` : les 4 codes, avec leurs messages. `photo_unreadable` : « Cette photo n'a pas pu être lue. Reprenez-la. »
- [x] `backend/app/core/storage.py` :
  - `StoredPhoto` (`photo_id`, `object_key`, `sha256`, `width`, `height`) ;
  - `ingest_photo(kind, data, photo_id=None)` et `purge(object_keys)` ;
  - client S3 d'écriture mis en cache (délais bornés).
- [x] `infra/docker-compose.yml`, `.env.example` : publier l'API S3 de Garage sur `127.0.0.1:${S3_LOCAL_PORT:-3900}` (comme `DB_LOCAL_PORT`).
- [x] `.github/workflows/ci.yml` : exporter `TEST_S3_ENDPOINT`, `TEST_S3_BUCKET` et les identifiants (masqués) depuis `.env.secrets/`.
- [x] `backend/tests/unit/test_storage.py` : contrôles de la matrice sur de vraies images générées par Pillow (jamais de S3 : l'échec précède l'envoi) ; forme de la clé avec `now` simulé ; `ingest_photo` hors unité de travail → `RuntimeError`.
- [x] `backend/tests/integration/test_storage_garage.py` : sur Garage réel, objet relu sans EXIF, rollback, purge, clé absente, lecture anonyme refusée.

**Acceptance Criteria:**
- Étant donné un objet stocké, quand on fait un `GET` HTTP anonyme sur `<endpoint>/<bucket>/<clé>`, alors la réponse est 403.
- Étant donné `uv run ruff check . && uv run lint-imports && uv run pytest`, alors tout est vert, et la couverture reste ≥ 60 %.

## Implementation Notes

- **Pillow 13.0.0**, épinglé exactement (`pyproject.toml`, `uv.lock`).
- **`core/storage.py`** : `sniff_format` lit les octets ; `Image.open(..., formats=[fmt])` n'essaie que le décodeur du format détecté. `DecompressionBombWarning` est transformé en erreur, donc en `photo_too_many_pixels`. L'image ré-encodée est reconstruite par `Image.frombytes` (`info` vide) : ni EXIF, ni ICC, ni XMP, ni commentaire ne peuvent être recopiés.
- **Échecs de suppression** : `_delete` ne lève jamais. Il journalise `storage_delete_failed` avec le type d'erreur seulement (ni clé ni message). `NoSuchKey` et `404` sont ignorés.
- **Client S3 d'écriture** : délais de 3 s à la connexion et 10 s à la lecture, 3 essais. Il est distinct de celui de la sonde (`health.py`, laissé tel quel).
- **Tests :**
  - `tests/photos.py` fabrique les images de test (bruit, EXIF, GPS, ICC, commentaire) et lit les segments JPEG ;
  - le test d'intégration s'appelle `test_storage_garage.py`, car pytest refuse deux modules de même nom ;
  - `test_errors.py` fige la liste des codes : les 4 codes y sont ajoutés ;
  - `test_layout.py` connaît `core/storage.py`.
- **Garage** : API S3 publiée sur `127.0.0.1:${S3_LOCAL_PORT:-3900}`. La CI exporte `TEST_S3_*` (secret masqué). Le README documente les variables, en bash et en PowerShell.
- **Vérifié en local** :
  - `ruff check`, `ruff format`, `lint-imports` : verts ;
  - `pytest --cov` : 428 réussis, puis `test_errors.py` corrigé et vert ;
  - sur un vrai Garage v2.5.0 (service seul de la pile) : les 8 tests d'intégration passent ;
  - Vitest `src/i18n` : 6 réussis.
  - **Non exécutés en local** : les tests d'intégration base (pas de PostGIS démarré) ; ils tournent en CI.
- **Hors story** : la demande de description vocale en wolof est notée dans `deferred-work.md`.

## Spec Change Log

## Review Triage Log

Passe 1 (25/11/2026). Couches : Blind Hunter (B), Edge Case Hunter (E), Verification Gap (V).

| # | Constat | Verdict | Preuve | Route |
|---|---|---|---|---|
| E1 | Suppression S3 au rollback exécutée sur la boucle asyncio (unité de travail d'une requête) | medium | `_run_hooks_async` appelle l'effet synchrone dans la boucle ; jusqu'à 3 essais × 13 s | patch : `_off_loop` (thread via `asyncio.to_thread`), test sur `async_unit_of_work` |
| E8 / V2 | Couleur transparente tRNS (RGB, gris) posée en noir ; palette transparente non testée | low | Vérifié : PNG RGB + `transparency` → pixel `(0, 0, 0)` | patch : `"transparency" in info` pour tout mode, tests paramétrés |
| V1 | Refus dur de Pillow (> 24 Mpx) jamais testé | low | Seules des images de 12,004 Mpx testées | patch : test 5000 × 5000 |
| V3 | Délais et essais du client d'écriture non vérifiés | low | Le test ne lisait que signature, style et sommes de contrôle | patch : assertions ajoutées |
| B2 | Filtre d'avertissements global (non sûr entre threads) | low | `warnings.catch_warnings` modifie l'état du processus | patch : filtre retiré ; contrôle explicite + `DecompressionBombError` |
| B5 / E9 | Empreinte calculée avant le contrôle du poids | low | `sha256` avant `sanitize_photo` | patch : réordonné |
| B4 | Copie complète des pixels pour vider `info` | low | `tobytes`/`frombytes` | patch : `rgb.info = {}` |
| B1 / E2 / E3 | `photo_id` réutilisé : écrasement, puis suppression au rollback | low | Aucun appelant aujourd'hui ; la 1.11 passe l'id d'une ligne neuve | patch : contrat documenté dans la docstring |
| E6 | `purge("cle")` itère sur les caractères | low | `tuple("abc")` | patch : `TypeError` |
| B10 | Messages par défaut ≠ `fr.json`, sans consigne pour 415 | low | Textes différents pour un même code | patch : alignés sur `fr.json` |
| B6 / V-autre | Docstring vers un fichier renommé | low | `test_storage.py` → `test_storage_garage.py` | patch |
| B7 / E12 | Identifiant de clé S3 non masqué en CI | low | Seul le secret avait `add-mask` | patch |
| B8 / E10 | README : bucket figé | low | La CI lit `S3_BUCKET` du `.env` | patch |
| B13 / E11 | Test de purge sans `finally` ; comptage global du bucket | low | Objet laissé si une assertion échoue ; aucun autre écrivain dans le bucket aujourd'hui | patch (`finally`) ; comptage rejeté |
| B3 | `Image.MAX_IMAGE_PIXELS` global | false | Exigé explicitement par la story (AC 1) ; commentaire ajouté | rejeté |
| B9 | `wo.json` identique à `fr.json` | false | Choix voulu : interface wolof hors hackathon (NFR-P3), seules les clés comptent | rejeté |
| B11 | Rollback après échec du commit non testé | false | Couvert par `test_failed_commit_in_sync_unit_runs_after_rollback` (`test_uow.py:285`) | rejeté |
| B12 / E7 | Modes rares (I;16, F, CMYK) → 500 | false | Vérifié : `convert("RGB")` réussit pour chacun | rejeté |
| B14 | Statuts de suivi incohérents ; `13.0.*` dans les tâches | low | `sprint-status` suit le workflow ; 1.8 périmée est antérieure ; correction de spec exclue | 1.8 : différé ; reste rejeté |
| B15 | Identifiants S3 absents découverts à la première photo | false | `REQUIRED_SECRETS` les exige en demo/prod : refus de démarrer | rejeté |
| E4 | Appelant qui avale l'échec de `put_object` puis commite | low | Mauvais usage improbable ; balayage AD-18 | rejeté |
| E5 | Commit réussi mais accusé perdu : objet supprimé | low | Cas réseau rare, non corrigible ici | rejeté |
| B4-bis | Pas de limite de décodages simultanés | low | Relève de la route (story 1.11) | rejeté |

## Design Notes

**Pixels avant décodage :** `Image.open` ne lit que l'en-tête. On compare `width*height` au plafond avant `load()`. On règle aussi `Image.MAX_IMAGE_PIXELS = 12_000_000`, et on transforme `DecompressionBombWarning`/`Error` en `photo_too_many_pixels` : c'est le filet si un format ment.

**Nettoyage enregistré avant l'envoi :** si `put_object` échoue après une écriture partielle, le rollback tente la suppression. Supprimer un objet absent est sans effet.

**`purge` objet par objet** (`delete_object`), pas `delete_objects` : ce dernier exige une somme de contrôle, dont le support par Garage n'est pas vérifié.

## Verification

**Commands:**
- `cd backend && uv run ruff check . && uv run ruff format --check . && uv run lint-imports` -- expected: vert.
- `cd backend && uv run pytest --cov` -- expected: vert, ≥ 60 %. Avec la pile et les variables `TEST_S3_*` : tests d'intégration exécutés.
