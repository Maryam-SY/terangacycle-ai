# Addendum au PRD : choix techniques et éléments pour l'architecture

> Ce fichier regroupe le « comment » que le PRD ne porte pas. Il est destiné à `bmad-architecture` et aux stories. La source détaillée reste `docs/dossier-technique.md` : ce fichier ne liste que les décisions arrêtées et les **écarts à corriger** par rapport à ce dossier.

## A. Décisions techniques arrêtées (brief, ne pas rouvrir sans Mia)

| Sujet | Décision |
|---|---|
| Style | Monolithe modulaire FastAPI : `auth`, `reports`, `missions`, `lots`, `analytics`, `ai`, `notifications` |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 + GeoAlchemy2, Alembic |
| Données | PostgreSQL 16 + PostGIS, Redis (OTP, limites de débit, files arq), stockage compatible S3 avec URL signées |
| Frontend | PWA React + TypeScript (Vite), vite-plugin-pwa, Dexie, Leaflet, onnxruntime-web, i18next, Tailwind |
| IA | MobileNetV3 (Large par défaut), 5 classes, ONNX INT8, même fichier sur l'appareil et sur le serveur |
| Temps réel | Rafraîchissement toutes les 15 s + Web Push ; pas de WebSocket |
| Hébergement | Docker Compose (hackathon) → AWS (pilote) → hébergeur local (cible), avec plan de sortie |
| API | REST JSON `/v1`, OpenAPI, format d'erreur unique `{error:{code,message,request_id}}` |

## B. Écarts du schéma SQL à corriger (issus de l'audit)

1. **`classifications`** : ajouter `source` (`client` | `server`) ou `client_predicted_type` + `client_confidence`, et un drapeau `disagreement` (FR-14, FR-15).
2. **`reports`** :
   - ajouter `pile_size` (`small` | `medium` | `large`) (FR-7) ;
   - ajouter `device_id_hash`, pour l'idempotence des anonymes (FR-9) ;
   - ajouter `photo_duplicate_of` ;
   - remplacer l'unicité globale de `client_uuid` par une unicité `(author_id ou device_id_hash, client_uuid)`.
3. **Numéro de suivi** : séquence PostgreSQL par année → `TC-{année}-{séquence sur 6 chiffres}`.
4. **`users.phone_hash`** : `HMAC-SHA256(pepper secret, numéro E.164)`. Pas de « hachage salé ».
5. **Jetons de renouvellement** : table `refresh_tokens` (empreinte du jeton, famille, `revoked_at`) pour la rotation avec détection de réutilisation (FR-2).
6. **`users.consent_training`** : booléen et horodatage (FR-4).
7. **Table de conversion** Taille de tas × Type de déchet → Poids estimé (configuration, ou table `weight_estimates`).

## C. Exigences de sécurité de l'audit, liées aux FR

| Audit | FR / NFR | Exigence d'implémentation |
|---|---|---|
| S1 (fuite par idempotence) | FR-9 | Clé unique par auteur ou appareil ; 409 sans contenu pour un autre appelant |
| S2 (téléphone) | §6.1 | HMAC avec pepper dans les secrets ; numéro chiffré en AES-GCM |
| S3 (OTP affiché) | FR-6 | Contrôle au démarrage `ENV=production` + `DEMO_MODE` → arrêt ; test |
| S4 (stockage des jetons) | FR-2 | Jeton d'accès en mémoire ; refresh en cookie `HttpOnly; Secure; SameSite=Strict`, chemin `/v1/auth` |
| S5 (JWT) | FR-2 | Liste blanche d'algorithmes (EdDSA ou RS256), `iss`/`aud`/`exp`, `kid` |
| S6 (OTP) | FR-1 | OTP haché dans Redis, comparaison à temps constant, 5 essais |
| S7 (limitation de débit) | FR-1, FR-10 | Limitation dans l'API (Redis) ; proxys de confiance pour `X-Forwarded-For` |
| S8 (positions publiques) | FR-34 | Agrégation par grille ou par Zone |
| S9 (visages) | FR-4, FR-23 | Consigne de capture + modération avant exposition |
| S10 (moindre privilège en base) | NFR-10 | Rôles `teranga_app` (sans DDL) et `teranga_migrator` |
| S11 (`/docs`, `/readyz`) | NFR-7 | `/docs` désactivé hors démo ; `/readyz` sans détails internes |
| S12 (CPU de classification) | FR-14 | Classification serveur en tâche arq, file bornée |

**Points d'infrastructure à ne pas oublier :**

- La CSP doit inclure `'wasm-unsafe-eval'` pour onnxruntime-web.
- Épingler les images et les actions GitHub.
- Healthcheck sans `curl`.
- `Image.MAX_IMAGE_PIXELS` réglé explicitement.
- Vérifier l'image MinIO utilisable, ou prévoir Garage ou SeaweedFS.

## D. IA : choix de mise en œuvre

- **Interface stable :** `classify(image) -> {predicted_type, confidence, scores, model_version, needs_user_choice}`, identique entre le **Modèle factice** (H24) et le Modèle entraîné (H48).
- **Prétraitement identique** sur le navigateur et le serveur (224×224, normalisation ImageNet) : sinon, Désaccords IA artificiels.
- **Calibration** par température, pour que le Seuil de confiance ait un sens (ECE ≤ 0,10).
- **Découpage du jeu de données** par lieu et par jour de prise de vue ; fiche du Modèle avec les licences des données.

## E. Raisons des choix par défaut (chemin rapide)

- **F1 macro plutôt que top-1 accuracy.** Les classes sont déséquilibrées (le plastique domine). La top-1 accuracy peut atteindre 80 % en sacrifiant le métal ou le verre ; le F1 macro, non.
- **Docker Compose en fin de hackathon.** Moins de pièces mobiles et répétable sur un portable de secours. AWS n'apporte rien à la démo.
- **Pilote à 60 % sur 6 mois.** C'est le chiffre déjà remis au jury dans le Proposal ; le cahier des charges (80 % sur 4 à 6 semaines) est à aligner.
