# TerangaCycle AI — Dossier technique

> Version du 9 novembre 2026. Partie technique du dossier.
> Les besoins, user stories (US-xx) et exigences non fonctionnelles (NF-xx) référencés ici sont définis dans [cahier-des-charges.md](cahier-des-charges.md).

## Sommaire

1. [Architecture logicielle](#1-architecture-logicielle)
2. [Modèle de données](#2-modèle-de-données)
3. [Spécification de l'API REST](#3-spécification-de-lapi-rest)
4. [Conception IA](#4-conception-ia)
5. [Sécurité et protection des données](#5-sécurité-et-protection-des-données)
6. [Infrastructure, AWS et souveraineté](#6-infrastructure-aws-et-souveraineté)
7. [Frontend PWA, hors-ligne et inclusion](#7-frontend-pwa-hors-ligne-et-inclusion)
8. [Qualité, CI/CD et observabilité](#8-qualité-cicd-et-observabilité)

---

## 1. Architecture logicielle

TerangaCycle est un monolithe modulaire (FastAPI) devant PostgreSQL/PostGIS et un stockage objet, avec le modèle ONNX embarqué dans le navigateur et dans l'API : c'est le plus simple à livrer en 72 h et on peut le découper en services plus tard.

Les services externes (passerelle SMS, Web Push) sont appelés par le module Notifications ; la PWA charge les tuiles de carte directement depuis son fournisseur.

```mermaid
flowchart TB
  subgraph Client
    PWA["PWA React + TypeScript<br/>ONNX Runtime Web · IndexedDB"]
  end
  subgraph Bord
    Proxy["Reverse proxy Caddy<br/>TLS · limitation de débit"]
  end
  subgraph API["API FastAPI (monolithe modulaire)"]
    auth[auth] --- reports[reports] --- missions[missions]
    lots[lots] --- analytics[analytics] --- ai[ai · ONNX Runtime] --- notif[notifications]
  end
  subgraph Données
    PG[("PostgreSQL 16 + PostGIS")]
    Redis[("Redis · arq")]
    S3[("Stockage objet S3<br/>MinIO / Amazon S3")]
  end
  PWA --> Proxy --> API
  API --> PG
  API --> Redis
  API --> S3
  notif -.-> SMS["Passerelle SMS"]
  notif -.-> Push["Web Push"]
  PWA -.-> Tiles["Fournisseur de tuiles"]
```

### Décisions d'architecture

| Sujet | Choix | Alternative écartée | Raison |
|---|---|---|---|
| Style | Monolithe modulaire (modules auth, signalements, missions, lots, analyse, IA, notifications) | Microservices | Un seul déploiement, pas de réseau interne à déboguer, frontières de modules déjà posées pour un découpage ultérieur |
| Backend | Python 3.12, FastAPI, Pydantic v2 | Node.js (NestJS) | Même langage que l'IA, OpenAPI générée, validation stricte des entrées |
| Accès aux données | SQLAlchemy 2, GeoAlchemy2, migrations Alembic | SQL brut partout | Modèle typé, migrations versionnées, requêtes PostGIS disponibles |
| Base | PostgreSQL 16 + PostGIS | MongoDB | Requêtes de proximité et de zone, contraintes d'intégrité, un standard portable |
| Cache et limites | Redis | Mémoire du processus | OTP, compteurs de limitation partagés, petites files |
| Tâches de fond | arq (file Redis) | Celery | Plus léger ; notifications et miniatures hors du chemin de requête |
| Stockage de fichiers | API S3 (MinIO ou Amazon S3) | Disque local | Même code partout, URL signées, réplication |
| Style d'API | REST JSON versionné `/v1` | GraphQL | Mise en cache simple, contrats clairs, outillage de test |
| Mise à jour de l'état | Rafraîchissement périodique (15 s) et Web Push | WebSockets | Suffisant pour le MVP ; Server-Sent Events en extension |
| IA | ONNX Runtime côté API et dans le navigateur | API d'IA hébergée | Souveraineté, hors-ligne, coût nul par requête |

### Modules du backend

- **auth** : OTP, jetons, rôles, journal d'audit.
- **reports** : création idempotente, validation des fichiers, statuts, modération.
- **missions** : acceptation avec verrou, preuves, vérification de position.
- **lots** : déclaration et réservation de matière.
- **analytics** : agrégations PostGIS, exports.
- **ai** : chargement du modèle ONNX, classification, versions, journal des scores.
- **notifications** : Web Push, SMS, messages internes.

Chaque module expose un service (logique métier) et un routeur (HTTP) ; un module n'appelle jamais directement les tables d'un autre, il passe par son service.

### Déroulé d'un signalement

1. La PWA classe la photo avec le modèle local, la compresse, puis place le signalement dans la file locale (le résultat local est envoyé en champ facultatif `client_prediction`).
2. `POST /v1/reports` arrive par le reverse proxy ; l'API contrôle le jeton, la limite de débit et le territoire.
3. L'image est validée et ré-encodée (§5), son SHA-256 est calculé pour détecter un doublon.
4. Le serveur reclasse l'image avec le même modèle : sa prédiction fait foi et la prédiction locale est conservée pour comparaison.
5. Une transaction écrit `reports`, `report_photos` et `classifications` ; `client_uuid` rend l'opération idempotente ; la zone est trouvée par `ST_Contains`.
6. L'image part vers le stockage objet ; la tâche de fond prévient les modérateurs.
7. L'API répond 201 avec le numéro de suivi et la classification.

### Évolution prévue

| Signal | Réaction |
|---|---|
| Classification serveur saturant le processeur | Extraire le module IA en service séparé, ou ne classer côté serveur que les photos sans prédiction locale |
| Lectures de carte lentes | Répliquer la base en lecture, pré-agréger la carte de chaleur dans une table |
| Table `reports` volumineuse | Partitionner par mois, archiver les photos anciennes |
| Plusieurs villes | Isoler les données par commune (colonne `tenant` ou schémas), hébergement local par région |

## 2. Modèle de données

PostgreSQL 16 avec l'extension PostGIS porte tout le modèle : 11 tables, des identifiants UUID, des statuts en énumération et des index géospatiaux pour les requêtes de proximité et de carte de chaleur.

### Entités et relations

| Table | Rôle | Relations principales |
|---|---|---|
| `users` | Compte (citoyen, collecteur, recycleur, admin, modérateur) | 1 à 1 avec `collector_profiles` |
| `collector_profiles` | Profil, zone d'activité, vérification | appartient à `users` |
| `reports` | Signalement géolocalisé | `users` (auteur), `zones` |
| `report_photos` | Photos d'un signalement ou preuve de collecte | appartient à `reports` |
| `classifications` | Prédictions IA et correction humaine | appartient à `reports` |
| `missions` | Prise en charge d'un signalement par un collecteur | `reports`, `users` (collecteur) |
| `material_lots` | Lot de matière valorisable déclaré | `missions`, `users` |
| `lot_requests` | Demande de réservation par un recycleur | `material_lots`, `users` |
| `zones` | Découpage administratif (commune, quartier) | contient des `reports` |
| `notifications` | Messages envoyés aux utilisateurs | `users` |
| `audit_logs` | Journal d'audit des actions sensibles | `users` |

### Schéma SQL (PostgreSQL + PostGIS)

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE user_role AS ENUM ('citizen','collector','recycler','moderator','admin');
CREATE TYPE waste_type AS ENUM ('plastic','metal','glass','organic','mixed');
CREATE TYPE report_status AS ENUM ('pending_review','validated','assigned','collected','rejected');
CREATE TYPE mission_status AS ENUM ('accepted','in_progress','completed','cancelled');
CREATE TYPE lot_status AS ENUM ('available','reserved','sold','withdrawn');

CREATE TABLE zones (
  id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name      TEXT NOT NULL,
  level     TEXT NOT NULL CHECK (level IN ('commune','quartier')),
  parent_id UUID REFERENCES zones(id),
  geom      GEOMETRY(MultiPolygon, 4326) NOT NULL
);
CREATE INDEX zones_geom_gix ON zones USING GIST (geom);

CREATE TABLE users (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  phone_hash   TEXT UNIQUE,          -- hachage salé du numéro
  phone_enc    BYTEA,                -- numéro chiffré (AES-GCM, clé gérée par KMS)
  display_name TEXT,
  role         user_role NOT NULL DEFAULT 'citizen',
  language     TEXT NOT NULL DEFAULT 'fr' CHECK (language IN ('fr','wo')),
  points       INTEGER NOT NULL DEFAULT 0,
  is_active    BOOLEAN NOT NULL DEFAULT TRUE,
  consented_at TIMESTAMPTZ,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at   TIMESTAMPTZ
);

CREATE TABLE collector_profiles (
  user_id        UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  organization   TEXT,
  verified       BOOLEAN NOT NULL DEFAULT FALSE,
  home_zone_id   UUID REFERENCES zones(id),
  accepted_types waste_type[] NOT NULL DEFAULT '{}'
);

CREATE TABLE reports (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tracking_no   TEXT UNIQUE NOT NULL,
  author_id     UUID REFERENCES users(id) ON DELETE SET NULL,
  client_uuid   UUID UNIQUE NOT NULL,          -- idempotence pour la synchro hors-ligne
  location      GEOGRAPHY(Point, 4326) NOT NULL,
  accuracy_m    REAL,
  zone_id       UUID REFERENCES zones(id),
  comment       TEXT CHECK (char_length(comment) <= 280),
  waste_type    waste_type,                    -- type retenu (IA ou corrigé)
  est_weight_kg NUMERIC(8,2),
  status        report_status NOT NULL DEFAULT 'pending_review',
  reject_reason TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX reports_location_gix ON reports USING GIST (location);
CREATE INDEX reports_status_type_idx ON reports (status, waste_type, created_at DESC);
CREATE INDEX reports_zone_idx ON reports (zone_id);

CREATE TABLE report_photos (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id  UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
  kind       TEXT NOT NULL CHECK (kind IN ('report','before','after')),
  object_key TEXT NOT NULL,                    -- clé dans le stockage objet
  sha256     TEXT NOT NULL,
  width      INTEGER,
  height     INTEGER,
  bytes      INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE classifications (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id      UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
  model_version  TEXT NOT NULL,
  predicted_type waste_type NOT NULL,
  confidence     REAL NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  scores         JSONB NOT NULL,               -- score par classe
  corrected_type waste_type,                   -- correction humaine
  corrected_by   UUID REFERENCES users(id),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX classifications_report_idx ON classifications (report_id);

CREATE TABLE missions (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id           UUID NOT NULL REFERENCES reports(id),
  collector_id        UUID NOT NULL REFERENCES users(id),
  status              mission_status NOT NULL DEFAULT 'accepted',
  collected_weight_kg NUMERIC(8,2),
  accepted_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at        TIMESTAMPTZ
);
-- une seule mission active par signalement
CREATE UNIQUE INDEX missions_one_active_per_report
  ON missions (report_id) WHERE status IN ('accepted','in_progress');

CREATE TABLE material_lots (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  mission_id UUID REFERENCES missions(id),
  owner_id   UUID NOT NULL REFERENCES users(id),
  waste_type waste_type NOT NULL,
  weight_kg  NUMERIC(8,2) NOT NULL CHECK (weight_kg > 0),
  zone_id    UUID REFERENCES zones(id),
  status     lot_status NOT NULL DEFAULT 'available',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE lot_requests (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lot_id      UUID NOT NULL REFERENCES material_lots(id) ON DELETE CASCADE,
  recycler_id UUID NOT NULL REFERENCES users(id),
  status      TEXT NOT NULL DEFAULT 'pending',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (lot_id, recycler_id)
);

CREATE TABLE notifications (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  channel    TEXT NOT NULL CHECK (channel IN ('push','sms','whatsapp','in_app')),
  title      TEXT NOT NULL,
  body       TEXT NOT NULL,
  read_at    TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE audit_logs (
  id         BIGSERIAL PRIMARY KEY,
  actor_id   UUID REFERENCES users(id),
  action     TEXT NOT NULL,                    -- ex. report.reject, user.suspend
  entity     TEXT NOT NULL,
  entity_id  UUID,
  details    JSONB,
  ip         INET,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Règles d'intégrité et requêtes clés

- **Idempotence hors-ligne** : `client_uuid` unique ; un renvoi du même signalement retourne l'existant (réponse 200) au lieu d'en créer un second.
- **Une mission active par signalement** : garantie par l'index unique partiel, pas seulement par le code applicatif.
- **Proximité** : `ST_DWithin(location, ST_MakePoint(:lng,:lat)::geography, :rayon_m)` avec tri par `ST_Distance`.
- **Carte de chaleur** : agrégation par cellule (`ST_SnapToGrid`) ou par zone, jamais les points bruts pour l'export public.
- **Suppression de compte** : `deleted_at` renseigné, numéro effacé, signalements conservés sous forme anonymisée (`author_id` à NULL).
- **Réentraînement** : les lignes de `classifications` avec `corrected_type` alimentent le jeu de données d'amélioration du modèle (§4).

## 3. Spécification de l'API REST

L'API expose 38 endpoints JSON sous `/v1`, documentés automatiquement en OpenAPI (FastAPI génère `/docs`) ; chaque route est liée à une user story et protégée par un rôle.

### Conventions

- **Authentification** : jeton d'accès JWT de 15 min dans l'en-tête `Authorization: Bearer`, jeton de rafraîchissement rotatif de 30 jours.
- **Format** : JSON UTF-8, dates ISO 8601 en UTC, coordonnées `{lat, lng}` en WGS84.
- **Pagination** : `?limit=50&cursor=<opaque>` ; réponse `{items, next_cursor}`.
- **Idempotence** : `client_uuid` sur la création de signalement ; en-tête `Idempotency-Key` sur les autres POST sensibles.
- **Limitation de débit** : 60 requêtes/min par utilisateur, 10 signalements/heure par appareil ou IP pour les anonymes.
- **Erreurs** : format unique ci-dessous, codes HTTP standards (400, 401, 403, 404, 409, 422, 429).

```json
{
  "error": {
    "code": "mission_already_taken",
    "message": "Cette mission a déjà été acceptée.",
    "request_id": "7f3c2a9e-1b64-4c0e-9a55-2d1f0c8e4a10"
  }
}
```

### Authentification et profil

| Méthode | Chemin | Rôle | Description | US |
|---|---|---|---|---|
| POST | `/v1/auth/otp/request` | public | Envoie un code à usage unique par SMS (5 demandes/h par numéro) | US-21 |
| POST | `/v1/auth/otp/verify` | public | Vérifie le code, retourne access + refresh | US-21 |
| POST | `/v1/auth/refresh` | public | Renouvelle les jetons (rotation) | US-21 |
| POST | `/v1/auth/logout` | connecté | Révoque le jeton de rafraîchissement | US-21 |
| GET | `/v1/me` | connecté | Profil de l'utilisateur | US-22 |
| PATCH | `/v1/me` | connecté | Langue, nom affiché, consentement | US-06, US-22 |
| DELETE | `/v1/me` | connecté | Suppression et anonymisation du compte | US-22 |

### Signalements

| Méthode | Chemin | Rôle | Description | US |
|---|---|---|---|---|
| POST | `/v1/reports` | citoyen ou anonyme | Crée un signalement (multipart : photo, lat, lng, comment, client_uuid, client_prediction facultatif) ; retourne 201, ou 200 si déjà reçu | US-01, US-04 |
| GET | `/v1/reports/{id}` | auteur, staff | Détail, statut, classification | US-05 |
| GET | `/v1/reports/mine` | citoyen | Mes signalements paginés | US-05 |
| GET | `/v1/reports` | staff | Recherche : bbox, status, type, from, to, zone | US-15 |
| PATCH | `/v1/reports/{id}/classification` | auteur, modérateur | Corrige le type de déchet | US-03 |
| POST | `/v1/reports/{id}/moderation` | modérateur | Valide ou rejette (motif obligatoire) | US-19 |
| POST | `/v1/reports/{id}/assign` | admin | Assigne à un collecteur | US-18 |

### Missions et collecte

| Méthode | Chemin | Rôle | Description | US |
|---|---|---|---|---|
| GET | `/v1/missions/nearby` | collecteur | lat, lng, radius_km (1 à 10), type ; triés par distance | US-08 |
| POST | `/v1/reports/{id}/missions` | collecteur vérifié | Accepte la mission ; 409 si déjà prise | US-09 |
| GET | `/v1/missions/mine` | collecteur | Mes missions en cours et passées | US-08 |
| PATCH | `/v1/missions/{id}` | collecteur | Transition de statut (accepted, in_progress, cancelled) | US-09 |
| POST | `/v1/missions/{id}/proofs` | collecteur | Photo avant/après, position du collecteur (contrôle à 150 m) et poids collecté ; passe à completed | US-10 |

### Lots de matière

| Méthode | Chemin | Rôle | Description | US |
|---|---|---|---|---|
| POST | `/v1/lots` | collecteur | Déclare un lot (type, poids, zone) | US-12 |
| GET | `/v1/lots` | recycleur, collecteur | Liste filtrée par type, zone, poids | US-13 |
| POST | `/v1/lots/{id}/requests` | recycleur | Demande de réservation | US-14 |
| PATCH | `/v1/lots/{id}` | propriétaire | Retire ou marque vendu | US-12 |

### Analyse et export

| Méthode | Chemin | Rôle | Description | US |
|---|---|---|---|---|
| GET | `/v1/analytics/summary` | admin | Totaux, répartition par type, délai moyen, kg collectés | US-16 |
| GET | `/v1/analytics/heatmap` | admin | Cellules agrégées (grille ou zone) selon filtres | US-15 |
| GET | `/v1/analytics/timeseries` | admin | Signalements et collectes par jour ou semaine | US-16 |
| GET | `/v1/exports/reports.csv` | admin | Export agrégé sans donnée personnelle | US-17 |
| GET | `/v1/exports/reports.geojson` | admin | Export GeoJSON avec position arrondie | US-17 |

### Administration, notifications, IA, exploitation

| Méthode | Chemin | Rôle | Description | US |
|---|---|---|---|---|
| GET | `/v1/admin/users` | admin | Liste filtrée des comptes | US-20 |
| PATCH | `/v1/admin/users/{id}` | admin | Vérifie, suspend ou change le rôle | US-20 |
| GET | `/v1/admin/audit-logs` | admin | Journal d'audit paginé | US-20 |
| GET | `/v1/notifications` | connecté | Mes notifications | US-05 |
| POST | `/v1/notifications/{id}/read` | connecté | Marque comme lue | US-05 |
| POST | `/v1/push/subscribe` | connecté | Enregistre l'abonnement Web Push | US-05 |
| POST | `/v1/ai/classify` | service interne | Image en entrée, scores par classe en sortie | US-02 |
| GET | `/v1/zones` | public | Liste des zones (commune, quartier) | US-15 |
| GET | `/healthz` | public | Sonde de vie | NF-07 |
| GET | `/readyz` | public | Sonde de disponibilité (base, stockage, modèle) | NF-07 |

### Exemple : création d'un signalement

```http
POST /v1/reports HTTP/1.1
Content-Type: multipart/form-data; boundary=----x
Authorization: Bearer <jwt>

client_uuid=0b1c9f42-5a1e-4e3b-9d70-3a7a8f8c2e11
lat=14.7167
lng=-17.4677
comment=Dépôt près du marché
photo=<fichier jpeg, 300 Ko max>
```

```json
{
  "id": "c7b1d2e0-8a43-4f1d-b7c2-91e5a0d3f6aa",
  "tracking_no": "TC-2026-004217",
  "status": "pending_review",
  "classification": {
    "model_version": "tc-mnv3-1.0.0",
    "predicted_type": "plastic",
    "confidence": 0.87,
    "scores": { "plastic": 0.87, "mixed": 0.08, "metal": 0.03, "glass": 0.01, "organic": 0.01 },
    "needs_user_choice": false
  },
  "created_at": "2026-11-09T10:14:03Z"
}
```

### Machine à états d'un signalement

```mermaid
stateDiagram-v2
  [*] --> pending_review
  pending_review --> validated: modérateur
  pending_review --> rejected: modérateur
  validated --> assigned: acceptation ou assignation
  assigned --> collected: preuve de collecte
  assigned --> validated: annulation par le collecteur
  rejected --> [*]
  collected --> [*]
```

Toute autre transition retourne 409 et aucune n'est possible depuis `rejected` ou `collected`.

## 4. Conception IA

Le modèle est un MobileNetV3 pré-entraîné sur ImageNet, ajusté (fine-tuning) sur 5 classes, exporté en ONNX et exécuté sur l'appareil ou sur le serveur local : aucune API d'IA étrangère n'est nécessaire.

### Choix et justification

| Décision | Choix | Pourquoi |
|---|---|---|
| Tâche | Classification d'image en 5 classes : plastic, metal, glass, organic, mixed | Réaliste en 72 h ; la détection d'objets multiples demande bien plus d'annotation |
| Architecture | MobileNetV3-Large (ou Small si l'appareil est lent) | Léger, bonne précision par calcul, bien supporté à l'export |
| Entraînement | Transfert d'apprentissage en deux phases | Peu de données locales nécessaires |
| Format | ONNX, quantifié en INT8 | Un seul artefact pour le navigateur (ONNX Runtime Web) et le serveur (ONNX Runtime CPU) |
| Exécution | Sur l'appareil pour le retour immédiat, puis reclassement serveur qui fait foi | Fonctionne hors-ligne ; le serveur garantit que le résultat enregistré ne peut pas être falsifié |
| Estimation du poids | Choix de taille de tas (petit, moyen, grand) avec table de conversion, pas d'IA | Estimer un poids depuis une photo est peu fiable ; la table est transparente et corrigeable |

### Données

1. **Sources publiques** : TrashNet et TACO comme base de départ (vérifier la licence de chacune avant redistribution) ; regrouper leurs catégories vers les 5 classes du projet (par exemple papier et carton vers mixed).
2. **Photos locales** : constituer un jeu de photos prises à Dakar (rue, marché, plage, bac) avec plusieurs téléphones. Objectif minimal de conception : 150 photos par classe pour le test final, davantage pour l'entraînement.
3. **Annotation** : une personne étiquette, une seconde vérifie un échantillon de 20 % ; les cas ambigus vont en mixed.
4. **Découpage** : séparer train, validation et test par lieu et par jour de prise de vue, pas au hasard, pour éviter qu'une même scène se retrouve des deux côtés.
5. **Éthique** : consentement pour l'usage des photos, aucun visage ni plaque lisible conservés, métadonnées EXIF retirées.

### Entraînement

```python
import torch, torch.nn as nn
from torchvision import models, transforms

CLASSES = ["plastic", "metal", "glass", "organic", "mixed"]
NORM = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])

train_tfm = transforms.Compose([
    transforms.RandomResizedCrop(224, scale=(0.6, 1.0)),
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(0.3, 0.3, 0.3, 0.05),  # lumière variable en extérieur
    transforms.ToTensor(), NORM,
])
eval_tfm = transforms.Compose([
    transforms.Resize(256), transforms.CenterCrop(224),
    transforms.ToTensor(), NORM,
])

weights = models.MobileNet_V3_Large_Weights.IMAGENET1K_V2
model = models.mobilenet_v3_large(weights=weights)
model.classifier[3] = nn.Linear(model.classifier[3].in_features, len(CLASSES))

# Phase 1 : seule la tête est entraînée
for p in model.features.parameters():
    p.requires_grad = False
opt = torch.optim.AdamW(model.classifier.parameters(), lr=1e-3, weight_decay=1e-4)
# ... 5 à 8 époques, perte CrossEntropy avec label_smoothing=0.1

# Phase 2 : dégel des derniers blocs, taux d'apprentissage plus faible
for p in model.features[-4:].parameters():
    p.requires_grad = True
opt = torch.optim.AdamW(
    [{"params": model.features[-4:].parameters(), "lr": 1e-4},
     {"params": model.classifier.parameters(), "lr": 3e-4}],
    weight_decay=1e-4)
# ... 10 à 15 époques avec arrêt anticipé sur le F1 macro de validation

# Export ONNX
model.eval()
torch.onnx.export(
    model, torch.randn(1, 3, 224, 224), "tc-mnv3-1.0.0.onnx",
    input_names=["image"], output_names=["logits"],
    dynamic_axes={"image": {0: "batch"}}, opset_version=17)
```

La quantification statique INT8 (`onnxruntime.quantization.quantize_static`) utilise environ 200 images de calibration prises dans le jeu d'entraînement ; la taille attendue est de l'ordre de 6 Mo contre 20 Mo en float32 (à mesurer).

### Inférence côté serveur (fait foi)

```python
import numpy as np, onnxruntime as ort
from PIL import Image

session = ort.InferenceSession("tc-mnv3-1.0.0.onnx", providers=["CPUExecutionProvider"])
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

def classify(path: str) -> dict:
    img = Image.open(path).convert("RGB").resize((224, 224))
    x = (np.asarray(img, dtype=np.float32) / 255.0 - MEAN) / STD
    x = x.transpose(2, 0, 1)[None]
    logits = session.run(None, {"image": x})[0][0]
    probs = np.exp(logits - logits.max()); probs /= probs.sum()
    best = int(probs.argmax())
    return {"predicted_type": CLASSES[best],
            "confidence": float(probs[best]),
            "scores": {c: float(p) for c, p in zip(CLASSES, probs)},
            "needs_user_choice": bool(probs[best] < 0.60)}
```

### Évaluation

| Mesure | Cible de conception | Remarque |
|---|---|---|
| F1 macro sur le jeu de test local | 0,80 ou plus | Objectif à confirmer par mesure, à annoncer au jury avec le chiffre réel |
| Rappel par classe | 0,70 ou plus pour chaque classe | Éviter qu'une classe soit sacrifiée |
| Calibration (ECE) | 0,10 ou moins | Le seuil de 60 % n'a de sens que si les scores sont calibrés (température) |
| Latence | Moins de 3 s sur appareil Android 2 Go | NF-01 |
| Matrice de confusion | Publiée dans la documentation du modèle | Montre honnêtement les confusions (plastic/mixed) |

### Boucle d'amélioration et gouvernance

- **Retour utilisateur** : chaque correction humaine (`classifications.corrected_type`) devient un exemple étiqueté, sous réserve de modération.
- **Surveillance** : suivre la part de signalements corrigés et la distribution des scores ; réentraîner si les corrections dépassent 25 % sur 2 semaines ou chaque mois pendant le déploiement pilote.
- **Versionnage** : un numéro de version dans le nom du fichier et dans chaque ligne de `classifications` ; jeux de données versionnés avec DVC ; fiche du modèle (model card) avec données, limites et métriques.
- **Limites annoncées** : photos sombres, tas mélangés, déchets mouillés ; l'app demande à l'utilisateur de choisir quand la confiance est basse plutôt que de deviner.

## 5. Sécurité et protection des données

Les deux risques majeurs sont l'abus (faux signalements, fausses preuves de collecte, SMS surfacturés) et la fuite de données de localisation ; les contrôles ci-dessous les traitent en priorité, et le reste suit les bonnes pratiques OWASP.

### Modèle de menaces

| Menace | Exemple | Contrôle | Test |
|---|---|---|---|
| Usurpation d'identité | Vol de jeton, rejeu d'un code OTP | JWT court (15 min), refresh rotatif et révocable, OTP à usage unique expirant en 5 min, 5 essais maximum | Tests d'authentification |
| Élévation de privilèges | Un citoyen appelle une route admin | Contrôle de rôle sur chaque route et contrôle de propriété sur chaque objet (BOLA) | Test automatisé « chaque route × chaque rôle » |
| Faux signalements et spam | Envoi massif de photos | Limite de débit par IP, appareil et compte ; file de modération ; hachage SHA-256 pour détecter les doublons ; position limitée au territoire du Sénégal | Test de charge d'abus |
| Fausses preuves de collecte | Un collecteur déclare un poids sans passer sur place | Position de la preuve à 150 m ou moins du signalement, horodatage serveur, photo avant/après, vérification admin par échantillon | Test de géorepérage |
| Fraude aux SMS (SMS pumping) | Demandes OTP en boucle vers des numéros surtaxés | Limite par numéro, IP et appareil ; plafond de coût quotidien ; liste de préfixes autorisés | Test de limites |
| Fichier malveillant | Image piégée, bombe de décompression | Validation du contenu réel, limite de dimensions, ré-encodage, stockage hors du domaine de l'API | Tests de fichiers invalides |
| Injection | SQL, en-têtes, JSON | Requêtes paramétrées (ORM), schémas Pydantic stricts, échappement des sorties | Analyse statique, tests |
| Fuite de localisation | Retrouver le domicile d'un citoyen | Position arrondie dans les exports, auteur jamais exposé aux collecteurs, accès aux positions précises réservé au staff | Revue des réponses d'API |
| Compromission de secrets | Clé dans le dépôt | Gestionnaire de secrets, aucune clé dans Git, analyse de secrets en CI | Gitleaks en CI |
| Chaîne logicielle | Dépendance vulnérable | Audit des dépendances à chaque build, image de conteneur minimale, versions figées | pip-audit, npm audit, Trivy |
| Déni de service | Inondation de requêtes | Limitation au bord (WAF ou reverse proxy), délais d'expiration, pagination bornée | Test de charge |
| Perte de données | Panne ou erreur humaine | Sauvegardes quotidiennes chiffrées, restauration testée, stockage objet versionné | Exercice de restauration |

### Contrôles techniques

- **Transport** : TLS 1.2 minimum (1.3 de préférence), HSTS, redirection HTTP vers HTTPS.
- **En-têtes** : Content-Security-Policy stricte, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, CORS limité aux origines du front.
- **Mots de passe** : aucun mot de passe citoyen ; pour le personnel (admin, modérateur), connexion par OTP plus second facteur ou, à défaut, mot de passe haché avec Argon2id.
- **Données au repos** : disque et base chiffrés ; numéro de téléphone stocké chiffré (AES-GCM) avec un hachage salé pour la recherche ; clés gérées par un service de clés (KMS).
- **Stockage des photos** : bucket privé, aucune URL publique ; accès par URL signée valable 5 minutes.
- **Journalisation** : journal d'audit pour les actions de modération, d'assignation et de gestion de comptes ; aucun jeton ni numéro complet dans les journaux applicatifs.
- **Moindre privilège** : un utilisateur de base de données applicatif sans droit de définition de schéma ; un rôle distinct pour les migrations.

### Validation d'un fichier téléversé

```python
import io
from fastapi import HTTPException
from PIL import Image

MAX_BYTES = 1_000_000        # le client compresse déjà à environ 300 Ko
MAX_PIXELS = 12_000_000      # protection contre les bombes de décompression
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

def sanitize_image(raw: bytes) -> bytes:
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, "image_too_large")
    try:
        probe = Image.open(io.BytesIO(raw))
        probe.verify()                       # détecte les fichiers corrompus
        img = Image.open(io.BytesIO(raw))    # rouvrir après verify()
    except Exception:
        raise HTTPException(422, "invalid_image")
    if img.format not in ALLOWED_FORMATS or img.width * img.height > MAX_PIXELS:
        raise HTTPException(422, "unsupported_image")
    img = img.convert("RGB")
    img.thumbnail((1280, 1280))
    out = io.BytesIO()
    img.save(out, "JPEG", quality=80)        # ré-encodage : supprime les métadonnées EXIF
    return out.getvalue()
```

### Conformité et vie privée

- **Cadre légal** : le Sénégal dispose d'une loi sur la protection des données à caractère personnel (loi n° 2008-12) et d'une autorité de contrôle, la Commission de Protection des Données Personnelles (CDP). Le projet prévoit une déclaration ou une demande d'autorisation avant tout déploiement réel ; à faire valider par un juriste.
- **Minimisation** : seules la position, la photo et un numéro de téléphone (optionnel pour signaler) sont collectés.
- **Consentement** : message clair avant la géolocalisation et l'envoi de photos ; case de consentement horodatée (`users.consented_at`).
- **Conservation** : propositions à valider avec la commune, par exemple photos de signalement 12 mois, statistiques agrégées sans limite, comptes supprimés sous 30 jours après demande.
- **Droits** : accès, rectification et suppression exposés dans l'app (US-22).
- **Visages et plaques** : instruction aux utilisateurs de ne pas photographier de personnes ; floutage automatique prévu après le MVP.

### Équipement de sécurité dans la CI

À chaque pull request : Gitleaks (secrets), Bandit et Semgrep (analyse statique Python), pip-audit et npm audit (dépendances), Trivy (image de conteneur) et un test d'autorisation par rôle. Un échec bloque la fusion.

## 6. Infrastructure, AWS et souveraineté

L'architecture est conçue portable : les mêmes conteneurs tournent sur un serveur du hackathon, sur AWS pour un pilote, ou chez un hébergeur local, ce qui permet d'afficher AWS sans contredire le message de souveraineté.

### Le point à assumer devant le jury

Héberger sur AWS ne rend pas les données « souveraines » au sens strict : le fournisseur et sa juridiction restent étrangers. La réponse crédible n'est pas de le cacher mais de montrer la réversibilité : PostgreSQL standard, stockage compatible S3, conteneurs, aucune API propriétaire d'IA, chiffrement avec des clés que l'organisation contrôle, et un plan de sortie documenté vers un hébergeur local.

### Trois niveaux de déploiement

| Composant | Hackathon (72 h) | Pilote AWS | Cible souveraine |
|---|---|---|---|
| Calcul | Un serveur virtuel unique (ou ordinateur portable de secours) avec Docker Compose | ECS Fargate ou une instance EC2 avec Docker | Serveurs chez un hébergeur local, Docker ou Kubernetes |
| Base de données | PostgreSQL + PostGIS en conteneur | Amazon RDS for PostgreSQL avec PostGIS, sauvegardes automatiques | PostgreSQL + PostGIS auto-hébergé, sauvegardes chiffrées hors site |
| Photos | MinIO (compatible S3) | Amazon S3, bucket privé, chiffrement par clé KMS | MinIO |
| Front PWA | Servi par le reverse proxy | S3 + CloudFront | Reverse proxy ou CDN local |
| IA | ONNX Runtime dans le conteneur API, modèle aussi dans le navigateur | Idem, aucun service d'IA managé | Idem |
| Domaine et TLS | Caddy avec certificats automatiques | Route 53 + ACM + Application Load Balancer | Let's Encrypt |
| Secrets et clés | Fichier d'environnement hors dépôt | Secrets Manager + KMS | Vault ou secrets chiffrés du serveur |
| Supervision | Journaux Docker, sonde de disponibilité | CloudWatch (journaux, alarmes) | Prometheus + Grafana |
| Protection | Limitation de débit dans Caddy | AWS WAF + Shield standard | Pare-feu et fail2ban |

**Choix de région pour le pilote AWS** : la région Afrique (Le Cap, `af-south-1`) est la plus proche géographiquement du continent mais reste éloignée de Dakar, et l'Europe (Paris, `eu-west-3`) offre un éventail de services plus large ; à trancher par une mesure de latence depuis Dakar avant le pilote.

**SMS et notifications** : la livraison des SMS au Sénégal passe par une passerelle ou un agrégateur dont la couverture et le coût sont à comparer (ne pas supposer qu'un service précis est disponible). WhatsApp Business et Web Push complètent le canal.

**Coût** : un pilote d'un site à faible trafic tient en quelques dizaines de dollars par mois (ordre de grandeur, à vérifier avec le calculateur de prix AWS) ; des crédits pour étudiants ou jeunes entreprises existent chez AWS et sont à demander.

### Hackathon : `docker-compose.yml`

```yaml
services:
  proxy:
    image: caddy:2
    ports: ["80:80", "443:443"]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
    depends_on: [api]
  api:
    build: ./backend
    env_file: .env
    environment:
      DATABASE_URL: postgresql+psycopg://teranga:${DB_PASSWORD}@db:5432/teranga
      S3_ENDPOINT: http://minio:9000
      REDIS_URL: redis://redis:6379/0
      MODEL_PATH: /models/tc-mnv3-1.0.0.onnx
    volumes: ["./models:/models:ro"]
    depends_on: [db, minio, redis]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 15s
      retries: 5
  db:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES_USER: teranga
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: teranga
    volumes: ["pgdata:/var/lib/postgresql/data"]
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD}
    volumes: ["miniodata:/data"]
  redis:
    image: redis:7-alpine
volumes:
  caddy_data:
  pgdata:
  miniodata:
```

### Pilote AWS : extrait Terraform (bucket de photos)

```hcl
resource "aws_kms_key" "photos" {
  description         = "TerangaCycle photos"
  enable_key_rotation = true
}

resource "aws_s3_bucket" "photos" {
  bucket = "terangacycle-photos-pilot"
}

resource "aws_s3_bucket_public_access_block" "photos" {
  bucket                  = aws_s3_bucket.photos.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "photos" {
  bucket = aws_s3_bucket.photos.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.photos.arn
    }
  }
}

resource "aws_s3_bucket_versioning" "photos" {
  bucket = aws_s3_bucket.photos.id
  versioning_configuration { status = "Enabled" }
}
```

### Plan de sortie (réversibilité)

1. Les données se réexportent en SQL (`pg_dump`) et en objets S3 standard.
2. Le déploiement est décrit par Docker et Terraform, sans service propriétaire obligatoire.
3. Le modèle IA est un fichier ONNX que le projet possède.
4. Un test de migration vers un serveur local est inscrit dans la feuille de route du pilote.

## 7. Frontend PWA, hors-ligne et inclusion

Une application web progressive (PWA) installable évite deux applications natives, fonctionne sans réseau grâce à un service worker et exécute le modèle IA directement dans le navigateur.

### Stack frontend

| Besoin | Choix | Remarque |
|---|---|---|
| Framework | React + TypeScript avec Vite | Plus simple et plus rapide à configurer pour une PWA que Next.js dans ce contexte |
| PWA et cache | vite-plugin-pwa (Workbox) | Précache de l'interface et du modèle ONNX |
| Données serveur | TanStack Query | Cache, reprise, mises à jour optimistes |
| Stockage local | IndexedDB via Dexie | File d'attente des signalements hors-ligne |
| Carte | Leaflet (+ leaflet.heat) ou MapLibre GL | Leaflet est le plus rapide à prendre en main |
| IA dans le navigateur | onnxruntime-web (WebAssembly) | Modèle en cache après le premier chargement |
| Traduction | i18next (fr, wo) | Fichiers JSON, traduction wolof relue par des locuteurs natifs |
| Interface | Tailwind CSS | Composants simples, cibles tactiles de 44 px |

**Fonds de carte** : le serveur de tuiles public d'OpenStreetMap a une politique d'usage qui interdit une utilisation intensive ; il convient pour la démo, mais un pilote doit passer par ses propres tuiles ou un fournisseur adapté.

### Écrans

| Écran | Acteur | US |
|---|---|---|
| Accueil et bouton « Signaler » | Citoyen | US-01 |
| Capture : photo, position, résultat IA, correction | Citoyen | US-01, US-02, US-03 |
| Suivi de mes signalements | Citoyen | US-05 |
| Carte publique des signalements | Tous | US-15 |
| Missions proches (liste et carte) | Collecteur | US-08, US-09 |
| Détail de mission, preuve et poids | Collecteur | US-10 |
| Lots disponibles | Recycleur | US-13, US-14 |
| Tableau de bord, carte de chaleur, export | Administrateur | US-15, US-16, US-17 |
| File de modération | Modérateur | US-19 |
| Gestion des comptes | Administrateur | US-20 |
| Profil, langue, suppression des données | Tous | US-06, US-22 |

### Parcours de signalement (cible : moins de 30 s)

1. Appui sur « Signaler » : l'appareil photo s'ouvre (`<input type="file" accept="image/*" capture="environment">`).
2. La photo est redimensionnée et compressée à 300 Ko ou moins dans le navigateur ; la position GPS est demandée en parallèle.
3. Le modèle ONNX classe la photo sur l'appareil ; le résultat apparaît avec des pictogrammes ; sous 60 % de confiance, l'utilisateur choisit le type.
4. Un appui sur « Envoyer » met le signalement dans la file locale ; l'envoi part tout de suite si le réseau est présent, sinon plus tard.
5. Un accusé « en attente » est affiché tout de suite ; le numéro de suivi définitif arrive à la synchronisation.

### File d'attente hors-ligne

```ts
import Dexie, { Table } from "dexie";

export interface PendingReport {
  clientUuid: string;
  lat: number;
  lng: number;
  comment?: string;
  photo: Blob;
  createdAt: number;
  attempts: number;
}

class TcDb extends Dexie {
  pending!: Table<PendingReport, string>;
  constructor() {
    super("terangacycle");
    this.version(1).stores({ pending: "clientUuid, createdAt" });
  }
}
export const db = new TcDb();

export async function enqueue(r: Omit<PendingReport, "attempts">) {
  await db.pending.put({ ...r, attempts: 0 });
  void flushQueue();
}

let flushing = false;
export async function flushQueue(getToken: () => string | null = () => null) {
  if (flushing || !navigator.onLine) return;
  flushing = true;
  try {
    for (const r of await db.pending.orderBy("createdAt").toArray()) {
      const form = new FormData();
      form.set("client_uuid", r.clientUuid);
      form.set("lat", String(r.lat));
      form.set("lng", String(r.lng));
      if (r.comment) form.set("comment", r.comment);
      form.set("photo", r.photo, "report.jpg");
      const token = getToken();
      const res = await fetch("/v1/reports", {
        method: "POST",
        body: form,
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (res.ok) {
        await db.pending.delete(r.clientUuid); // 200 ou 201 : idempotent côté serveur
      } else if (res.status === 429 || res.status >= 500) {
        break; // réessayer plus tard
      } else {
        await db.pending.update(r.clientUuid, { attempts: r.attempts + 1 });
      }
    }
  } finally {
    flushing = false;
  }
}

window.addEventListener("online", () => void flushQueue());
```

La Background Sync API relance l'envoi même onglet fermé sur Chrome Android ; Safari ne la prend pas en charge, d'où l'écoute de l'événement `online` et l'envoi à l'ouverture de l'application comme solution de repli.

### Inclusion

- **Langues** : français et wolof ; tous les textes passent par i18next, aucune chaîne en dur. Le wolof est écrit en orthographe officielle et relu par des locuteurs natifs avant la démo.
- **Pictogrammes** : chaque type de déchet a une icône et une couleur distinctes, compréhensibles sans lecture.
- **Faible littératie** : consignes courtes, étapes illustrées, retour sonore optionnel.
- **Appareils modestes** : bundle initial léger, images compressées, aucun chargement de bibliothèque lourde au démarrage de l'écran de signalement.
- **Accessibilité** : contraste AA, cibles de 44 px, étiquettes pour lecteurs d'écran, navigation au clavier sur les écrans d'administration.
- **Canal SMS ou WhatsApp** (extension) : un message avec photo et localisation partagée crée un signalement via un webhook qui appelle les mêmes endpoints.

## 8. Qualité, CI/CD et observabilité

Le pipeline bloque toute fusion qui échoue au lint, aux tests, aux contrôles de sécurité ou au seuil de couverture de 60 %, et le déploiement se fait par une commande reproductible.

### Organisation du dépôt

```
terangacycle/
├── backend/            FastAPI, SQLAlchemy 2, Alembic, Pydantic v2
│   ├── app/            routes, services, modèles, sécurité, ia
│   ├── migrations/     scripts Alembic
│   └── tests/
├── web/                PWA React + TypeScript (Vite)
├── ml/                 notebooks, entraînement, export ONNX, fiche du modèle
├── infra/              docker-compose, Caddyfile, Terraform
├── docs/               cahier des charges, OpenAPI, guide de démo
└── .github/workflows/  CI
```

Stratégie de branches : `main` toujours déployable, branches courtes par fonctionnalité, pull request relue par un coéquipier (même brève pendant le hackathon).

### Stratégie de tests

| Niveau | Outil | Ce qui est testé | Seuil |
|---|---|---|---|
| Unitaire backend | pytest | Règles métier, machine à états, validation des fichiers | 60 % de couverture |
| Intégration API | pytest + base PostGIS réelle | Routes, requêtes de proximité, contraintes d'unicité, idempotence | Chemins critiques couverts |
| Autorisation | pytest paramétré | Chaque route sensible × chaque rôle | 100 % des routes sensibles |
| Frontend | Vitest + Testing Library | Composants clés, file hors-ligne | Chemins critiques |
| De bout en bout | Playwright | Signaler, accepter, collecter, voir sur la carte | 1 scénario complet vert avant la démo |
| Charge | k6 | 50 requêtes/s en lecture, rafale de signalements | NF-02 |
| IA | Script d'évaluation | F1 macro, rappel par classe, latence, sur le jeu de test figé | §4 |
| Hors-ligne | Test manuel en mode avion | Signalement, reconnexion, absence de doublon | NF-06 |

Exemple de test d'autorisation :

```python
import pytest

SENSITIVE = [
    ("GET", "/v1/analytics/summary", "admin"),
    ("GET", "/v1/admin/users", "admin"),
    ("POST", "/v1/reports/{id}/moderation", "moderator"),
    ("POST", "/v1/reports/{id}/missions", "collector"),
]

@pytest.mark.parametrize("method,path,allowed_role", SENSITIVE)
def test_other_roles_are_refused(client, tokens, report_id, method, path, allowed_role):
    for role, token in tokens.items():
        if role == allowed_role:
            continue
        r = client.request(method, path.format(id=report_id),
                           headers={"Authorization": f"Bearer {token}"})
        assert r.status_code in (401, 403), f"{role} a accès à {method} {path}"

def test_anonymous_is_refused(client, report_id):
    for method, path, _ in SENSITIVE:
        assert client.request(method, path.format(id=report_id)).status_code == 401
```

### Intégration continue (GitHub Actions)

```yaml
name: ci
on:
  pull_request:
  push:
    branches: [main]
jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      db:
        image: postgis/postgis:16-3.4
        env:
          POSTGRES_USER: teranga
          POSTGRES_PASSWORD: test
          POSTGRES_DB: teranga_test
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U teranga"
          --health-interval 5s
          --health-retries 10
    env:
      DATABASE_URL: postgresql+psycopg://teranga:test@localhost:5432/teranga_test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12", cache: pip }
      - run: pip install -r backend/requirements-dev.txt
      - run: ruff check backend && ruff format --check backend
      - run: bandit -r backend/app -q
      - run: pip-audit -r backend/requirements.txt
      - run: pytest backend --cov=backend/app --cov-fail-under=60
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: npm, cache-dependency-path: web/package-lock.json }
      - run: npm ci --prefix web
      - run: npm run lint --prefix web
      - run: npm run test --prefix web -- --run
      - run: npm run build --prefix web
      - run: npm audit --prefix web --audit-level=high
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: gitleaks/gitleaks-action@v2
        env: { GITHUB_TOKEN: "${{ secrets.GITHUB_TOKEN }}" }
      - run: docker build -t tc-api ./backend
      - run: >-
          docker run --rm -v /var/run/docker.sock:/var/run/docker.sock
          aquasec/trivy image --exit-code 1 --severity HIGH,CRITICAL tc-api
```

**Déploiement** : sur `main`, une étape distincte construit et pousse l'image, puis exécute sur le serveur `docker compose pull && docker compose up -d` ; les migrations Alembic tournent avant le démarrage de la nouvelle version, et un retour arrière est possible en relançant le tag précédent. Épingler les versions des actions et des images avant le pilote.

### Observabilité

- **Journaux** : JSON structuré avec `request_id`, rôle, route, durée ; aucun jeton ni numéro complet.
- **Métriques** : endpoint `/metrics` (format Prometheus) protégé, ou métriques CloudWatch en pilote AWS.
- **Sondes** : `/healthz` (vivacité) et `/readyz` (base, stockage, modèle chargé).

| Métrique | Pourquoi | Alerte |
|---|---|---|
| Taux d'erreurs 5xx | Santé du service | Plus de 2 % sur 5 min |
| Latence p95 de l'API | NF-02 | Plus de 500 ms sur 10 min |
| Latence de classification serveur | NF-01 | p95 au-dessus de 2 s |
| Distribution des scores de confiance | Détecter une dérive du modèle | Médiane en baisse de 15 points ou plus |
| Part de classifications corrigées | Qualité réelle du modèle | Plus de 25 % sur 2 semaines |
| Signalements en attente de synchronisation (côté client, remontés) | Fiabilité du hors-ligne | Croissance anormale |
| Demandes OTP par heure | Fraude SMS | Au-dessus du plafond défini |
| Espace disque, sauvegarde réussie | Continuité | Échec d'une sauvegarde |
