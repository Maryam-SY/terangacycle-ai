---
title: 'Story 1.10 — Stocker une photo sans métadonnées dans le bucket privé'
type: 'feature'
created: '2026-11-25'
status: 'in-review'
baseline_commit: '20ed1f8c0fbec3607fc86020830492acd21993c6'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Le serveur ne sait pas encore recevoir une photo. Il doit pouvoir le faire pour la création du Signalement (story 1.11) et plus tard pour les Preuves. Une photo envoyée par un client modifié peut être énorme, piégée (bombe de décompression), d'un autre format, ou garder ses métadonnées EXIF et GPS. Il ne faut ni la conserver telle quelle, ni l'exposer, ni laisser d'objet orphelin si la transaction échoue.

**Approach:** créer le module `core.storage`, seul à parler S3 (Garage), avec deux fonctions appelées dans une unité de travail :
- `ingest_photo(kind, data)` contrôle les octets reçus (format, poids, pixels, lisibilité), ré-encode en JPEG sans aucune métadonnée après `ImageOps.exif_transpose()`, puis stocke sous `<kind>/<yyyy>/<mm>/<uuid>.jpg`. L'objet est supprimé si la transaction est annulée.
- `purge(object_keys)` supprime des objets seulement après le commit.

Aucune route HTTP dans cette story : elle arrive avec la 1.11.

## Boundaries & Constraints

**Always:**
- **Format** détecté par les octets (signatures JPEG, PNG, WebP), jamais par le nom ni par le type annoncé. Le format lu par Pillow doit correspondre à la signature.
- **Contrôles, dans l'ordre :**
  - au-delà de 1 048 576 octets : 413 `photo_too_large` ;
  - format non pris en charge : 415 `unsupported_media_type` ;
  - en-tête lu sans décoder, largeur × hauteur au-delà de 12 000 000 : 422 `photo_too_many_pixels` ;
  - échec du décodage : 422 `photo_unreadable`.
  - `Image.MAX_IMAGE_PIXELS` est réglé explicitement à 12 000 000.
- **Ré-encodage :**
  - `ImageOps.exif_transpose()`, puis conversion RVB (une transparence devient un fond blanc) ;
  - JPEG de qualité 85, sans EXIF, ni profil ICC, ni XMP, ni commentaire ;
  - type de contenu `image/jpeg`, aucun ACL public.
- **Valeur de retour :** `StoredPhoto(object_key, sha256, width, height)`. Le `sha256` est celui des octets **reçus**, pour la détection de photo identique (story 1.14). La largeur et la hauteur sont celles de l'image stockée.
- **Clé :** l'année et le mois viennent de `core.clock` (UTC) ; l'identifiant est un `uuid4`. `kind` vient d'une énumération `PhotoKind` dans `core/enums.py` (`report`, `proof`).
- **Transactions :**
  - hors d'une unité de travail, les deux fonctions refusent de s'exécuter (erreur de programmation) ;
  - la suppression après annulation passe par `after_rollback`, la purge par `after_commit` ;
  - supprimer un objet absent ne lève pas d'erreur.
- **Client S3 :** un client dédié au stockage (path-style, délais raisonnables, quelques nouveaux essais), distinct de celui de la sonde `/readyz`.
- **Confidentialité :** ni octets ni métadonnées dans les journaux ; un journal de stockage ne porte que la clé.
- **Messages d'erreur :** chaque nouveau code a son message `errors.<code>` en `fr.json` et `wo.json`, qui dit au Citoyen quoi faire ; il est aussi dans `DEFAULT_MESSAGES`.
- **Pillow :** version exacte épinglée avec `uv.lock` ; pip-audit et Trivy doivent rester verts.

**Never:**
- aucune route HTTP, table, Signalement ni miniature (stories 1.11 et 1.18) ;
- aucun accès S3 hors de `core.storage` (la sonde `/readyz` existante garde son client) ;
- aucune URL présignée ;
- aucun mock de Garage pour les tests d'intégration.

## I/O & Edge-Case Matrix

| Scénario | Entrée | Attendu |
|---|---|---|
| JPEG avec EXIF et GPS, orientation 6 | 4000 × 3000, < 1 Mo | Stocké ; relu : JPEG sans EXIF ni GPS, 3000 × 4000 ; clé `report/AAAA/MM/<uuid>.jpg` ; `sha256` des octets reçus |
| PNG avec transparence | PNG valide | Stocké en JPEG, fond blanc |
| WebP | WebP valide | Stocké en JPEG |
| Trop lourd | 1 048 577 octets | 413 `photo_too_large`, aucun objet |
| Autre format | GIF, PDF, texte renommé `.jpg` | 415 `unsupported_media_type`, aucun objet |
| Trop de pixels | En-tête PNG de 5000 × 5000 | 422 `photo_too_many_pixels` sans décodage complet, aucun objet |
| Corrompue | Signature JPEG puis octets aléatoires | 422 `photo_unreadable`, aucun objet |
| Annulation | Exception après `ingest_photo()`, avant le commit | Objet supprimé (comptage du bucket avant/après) |
| Purge | `purge([clé])` puis commit / puis annulation | Supprimé après commit / conservé après annulation |
| Purge d'un absent | Clé inexistante | Aucune erreur |
| Lecture anonyme | GET sans signature sur l'objet | Refusée (403) |

</frozen-after-approval>

## Code Map

- `backend/app/core/db.py` : `unit_of_work()`, `async_unit_of_work()`, `after_commit()`, `after_rollback()`, `_require_uow()`. Réutiliser ces fonctions, ne pas les réécrire.
- `backend/app/core/health.py` : `_s3_client()` montre la configuration Garage attendue (path-style, sommes de contrôle seulement si exigées). La sonde garde son propre client à délai court.
- `backend/app/core/config.py` : `s3_endpoint`, `s3_region`, `s3_bucket`, `s3_access_key_id`, `s3_secret_access_key`.
- `backend/app/core/errors/` : `codes.py` (`ErrorCode`, `DEFAULT_MESSAGES`), et le mécanisme d'erreur métier vers l'enveloppe (à réutiliser).
- `backend/tests/unit/test_error_messages.py` : exige un message `errors.<code>` par code en `fr.json` et `wo.json`.
- `backend/app/core/clock.py` : horloge simulable.
- `backend/app/core/enums.py` : énumérations uniques, à compléter avec `PhotoKind`.
- `infra/docker-compose.yml` et `infra/garage/garage.toml` : Garage v2.5, une seule instance, bucket créé par défaut (`--default-bucket`).
- `backend/tests/integration/` : modèle des tests sur la pile réelle (`REQUIRE_INTEGRATION=1` en CI). Les URL et identifiants de test sont décrits dans `README.md`.
- `pyproject.toml` / `uv.lock` : ajouter Pillow.

## Tasks & Acceptance

**Execution:**
- [ ] `backend/pyproject.toml`, `uv.lock` : Pillow épinglé.
- [ ] `backend/app/core/enums.py` : `PhotoKind`.
- [ ] `backend/app/core/errors/codes.py`, `web/src/i18n/fr.json`, `web/src/i18n/wo.json` : codes `unsupported_media_type`, `photo_too_large`, `photo_too_many_pixels`, `photo_unreadable` et leurs messages.
- [ ] `backend/app/core/storage.py` : client S3 dédié, `ingest_photo()`, `purge()`, `StoredPhoto`, détection du format, contrôles, ré-encodage, hooks de transaction.
- [ ] Tests unitaires : détection du format par les octets, ordre des contrôles, limite de pixels lue dans l'en-tête, ré-encodage sans métadonnées (image construite avec Pillow : EXIF, GPS, orientation 6, ICC), PNG transparent sur fond blanc.
- [ ] Tests d'intégration sur Garage réel : chaque ligne de la matrice, avec relecture de l'objet et comptage du bucket.
- [ ] `.importlinter` et le contrat d'architecture : `core.storage` reste dans `core`, seul importeur de `boto3` hors de la sonde.

**Acceptance Criteria:**
- Étant donné le code backend, quand on cherche `boto3` hors de `core/storage.py` et `core/health.py`, alors on ne le trouve pas (test d'architecture).
- Étant donné la CI, quand `test_error_messages.py` tourne, alors les 4 nouveaux codes ont leur message en `fr.json` et `wo.json`.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run lint-imports && REQUIRE_INTEGRATION=1 uv run pytest --cov` (backend, pile Compose réelle) — expected: vert.
- `npm test` (web, pour la parité `fr`/`wo`) — expected: vert.
- `python -I scripts/ci/check_pinning.py && python -I scripts/ci/check_repo_hygiene.py` — expected: OK.
