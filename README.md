# TerangaCycle AI

**Transformer un déchet signalé par un citoyen en ressource tracée, classée par IA et confiée au bon collecteur ou recycleur local, avec des données hébergées et gouvernées au Sénégal.**

Projet présenté au hackathon **« Afrique Makers : l'innovation au service d'une souveraineté technologique durable et inclusive »**.

> 🚧 Projet en cours de construction : la documentation est en place, le code source arrive au fur et à mesure.

---

## Le problème

À Dakar comme dans beaucoup de villes, les dépôts sauvages sont signalés de manière informelle (appels, réseaux sociaux), sans géolocalisation fiable ni suivi. Les récupérateurs informels et les petits recycleurs n'ont aucun outil pour savoir où se trouve la matière valorisable, et les communes manquent de données pour planifier les tournées.

## La solution

Une application web progressive (PWA), utilisable hors-ligne, qui relie citoyens, collecteurs, recycleurs et communes :

```
Signaler → Classifier (IA) → Dispatcher → Collecter → Valoriser → Mesurer l'impact
```

1. **Le citoyen** prend une photo du dépôt : la position GPS est captée automatiquement et un modèle d'IA embarqué propose le type de déchet (plastique, métal, verre, organique, mixte), même sans réseau.
2. **Le collecteur** voit les missions proches, en accepte une, puis prouve la collecte par photo et poids.
3. **Le recycleur** consulte les lots de matière disponibles par type et par zone.
4. **La commune** pilote avec une carte de chaleur, des indicateurs (kg valorisés, délais) et des exports ouverts.

Le cœur du projet n'est pas le signalement mais **la valorisation** : le matching entre déchet, collecteur et recycleur.

## Souveraine, durable, inclusive

| | Ce que fait TerangaCycle AI |
|---|---|
| **Souveraineté** | Modèle IA open source (MobileNetV3 → ONNX) exécuté sur le téléphone ou un serveur local, aucune API d'IA étrangère, données exportables, plan de sortie vers un hébergeur local |
| **Durable** | Économie circulaire : chaque déchet devient une matière tracée, avec des indicateurs d'impact mesurés |
| **Inclusive** | Français et wolof, mode hors-ligne, pictogrammes, canal SMS/WhatsApp, récupérateurs informels intégrés comme acteurs rémunérés |

## Stack technique

| Couche | Technologies |
|---|---|
| Frontend | React + TypeScript (Vite), PWA (Workbox), Dexie/IndexedDB, Leaflet, i18next, Tailwind CSS |
| IA | PyTorch (fine-tuning MobileNetV3), ONNX Runtime (serveur) et onnxruntime-web (navigateur) |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, arq |
| Données | PostgreSQL 16 + PostGIS, Redis, stockage objet compatible S3 (MinIO) |
| Infra | Docker Compose, Caddy ; pilote AWS (Terraform) ; cible : hébergeur local |
| Qualité | pytest, Vitest, Playwright, k6, GitHub Actions, Gitleaks, Bandit, Trivy |

## Documentation

| Document | Contenu |
|---|---|
| [📋 Cahier des charges](docs/cahier-des-charges.md) | Vision, acteurs, périmètre du MVP, 22 user stories, exigences non fonctionnelles, planning, risques, indicateurs d'impact, pitch |
| [🛠️ Dossier technique](docs/dossier-technique.md) | Architecture, modèle de données (SQL), API REST (38 endpoints), conception IA, sécurité, infrastructure, PWA hors-ligne, CI/CD |

## Organisation du dépôt

```
terangacycle-ai/
├── backend/   API FastAPI (à venir)
├── web/       PWA React + TypeScript (à venir)
├── ml/        Entraînement, export ONNX, fiche du modèle (à venir)
├── infra/     Docker Compose, Caddyfile, Terraform (à venir)
└── docs/      Cahier des charges et dossier technique
```

## Feuille de route

- [x] Cahier des charges et dossier technique
- [ ] Squelette du dépôt, CI, `docker compose up` fonctionnel
- [ ] Jeu de photos locales étiqueté et modèle de base évalué
- [ ] MVP : signalement, classification, carte, missions, tableau de bord, hors-ligne
- [ ] Pilote terrain dans un quartier

## Équipe

Projet porté par une équipe de trois personnes : développement fullstack, données et IA, design et pitch.
