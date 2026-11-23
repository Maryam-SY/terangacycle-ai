# Addendum au PRD : choix techniques et éléments pour l'architecture

> Ce fichier regroupe le « comment » que le PRD ne porte pas. Il est destiné à `bmad-architecture` et aux stories. La source détaillée reste `docs/dossier-technique.md` : ce fichier ne liste que les décisions arrêtées et les **écarts à corriger** par rapport à ce dossier. Le vocabulaire est celui du Glossaire du PRD (§3).

## A. Décisions techniques arrêtées (brief, ne pas rouvrir sans Mia)

| Sujet | Décision |
|---|---|
| Style | Monolithe modulaire FastAPI : `auth`, `reports`, `missions`, `lots`, `analytics`, `ai`, `notifications` |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 + GeoAlchemy2, Alembic |
| Données | PostgreSQL 16 + PostGIS, Redis (OTP, limites de débit, files arq), stockage compatible S3 avec URL signées |
| Frontend | PWA React + TypeScript (Vite), vite-plugin-pwa, Dexie, Leaflet, onnxruntime-web, i18next, Tailwind |
| IA | MobileNetV3-Large par défaut, Small si NFR-1 dépasse 3 s à la mesure H24 (décidé) ; 5 classes ; ONNX INT8 ≤ 8 Mo ; même fichier sur l'appareil et sur le serveur |
| Temps réel | Rafraîchissement toutes les 15 s + Web Push ; pas de WebSocket |
| Hébergement | Docker Compose (hackathon) → AWS (pilote) → hébergeur local (cible), avec plan de sortie |
| API | REST JSON `/v1`, OpenAPI, format d'erreur unique `{error:{code,message,request_id}}` ; pagination par curseur (`limit` 50 par défaut, 100 au plus, réponse `{items, next_cursor}`) ; en-tête `Idempotency-Key` sur les POST sensibles (Preuve, acceptation, modération, assignation), portée par utilisateur, durée de vie 24 h ; dates ISO 8601 en UTC ; coordonnées `{lat, lng}` en WGS84 |

## B. Écarts du dossier technique à corriger

### B.1 Schéma SQL (issus de l'audit et des relectures)

1. **`classifications`** : ajouter `source` (`client` | `server`) ou `client_predicted_type` + `client_confidence`, et un drapeau `disagreement` (FR-14, FR-15).
2. **`reports`** :
   - ajouter `pile_size` (`small` | `medium` | `large`) (FR-7) ;
   - ajouter `device_id_hash`, pour l'idempotence et le suivi des anonymes (FR-9, FR-20) ;
   - remplacer l'unicité globale de `client_uuid` par l'unicité du point 11.
3. **Numéro de suivi** : séquence PostgreSQL par année → `TC-{année}-{séquence sur 6 chiffres}` ; la séquence repart à 1 au 1er janvier ; l'année est celle de la réception par le serveur (FR-7).
4. **`users.phone_hash`** : `HMAC-SHA256(pepper secret, numéro E.164)`. Pas de « hachage salé ».
5. **Jetons de renouvellement** : table `refresh_tokens` (empreinte du jeton, famille, `revoked_at`) pour la rotation avec détection de réutilisation (FR-2).
6. **`users.consent_training`** : booléen et horodatage, pour un compte (FR-4) ; le choix est aussi copié sur chaque Signalement (point 10).
7. **Table de conversion** Taille de tas × Type de déchet → Poids estimé (configuration, ou table `weight_estimates`).
8. **Preuve de collecte** : table `collection_proofs` reliée à la Mission, avec la Position du Collecteur `location GEOGRAPHY(Point)`, `accuracy_m`, `weight_kg`, `weight_kind` (`weighed` | `estimated`), `review_status` (`unreviewed` | `confirmed` | `contested`), `review_reason` ; les photos `before` et `after` sont reliées à la Mission, pas seulement au Signalement (FR-29, FR-41).
9. **`missions`** : `status` (`active` | `completed` | `cancelled` | `expired`), `accepted_at`, `expires_at` ; index unique partiel « une Mission `active` par Signalement » conservé (FR-25, FR-42).
10. **`reports`** (suite) : `received_at` (horodatage serveur, origine des délais et de la Cohorte de FR-31), `accuracy_m`, `consent_training` (copié à la création, FR-4), `client_prediction` (type, confiance, `model_version`), `retained_type` (Type de déchet retenu, fixé à la validation, FR-23), `duplicate_of` (photo identique ou proximité ; remplace `photo_duplicate_of`, FR-8 et FR-22), `flags`.
11. **Identifiant d'appareil** : secret aléatoire d'au moins 128 bits généré à l'installation, envoyé dans un en-tête, stocké haché (`device_id_hash`), jamais renvoyé ni journalisé. L'unicité porte sur `(owner_key, client_uuid)`, où `owner_key` est l'empreinte de l'auteur ou de l'appareil calculée à la création ; elle reste valable après anonymisation de l'auteur.
12. **`audit_logs`** en ajout seul : `teranga_app` n'a que INSERT et SELECT (NFR-17).
13. **Retirer `users.points`** (non-objectif, minimisation).
14. **Drapeau de désaccord** : un seul nom, `disagreement` (point 1).
15. **`users.totp_secret`** chiffré pour le Second facteur du Personnel (FR-43).
16. **Zone active** : une seule Zone active configurée (polygone PostGIS) ; contrôle `ST_Contains` à la création (FR-7). Aucune colonne `commune_id` de cloisonnement au MVP (multi-commune : non-objectif).

### B.2 PWA hors-ligne : corrections du code du dossier technique

- Le schéma Dexie stocke 100 % des champs (FR-17) : photo, Position et précision, Taille de tas, Type de déchet choisi, Classification locale (type, score, version), commentaire, Identifiant client, état d'envoi.
- `flushQueue` est toujours appelé avec le jeton courant (si l'utilisateur est connecté) et l'Identifiant d'appareil ; un Signalement créé connecté n'est jamais renvoyé en anonyme.
- 201 et 200 vident l'entrée de la file ; un 4xx définitif (hors 408 et 429) la sort de la file et affiche le motif (FR-18) ; 429, 5xx et erreur réseau déclenchent un nouvel essai avec un délai croissant.
- Background Sync sur Chrome Android, avec replis sur l'événement `online` et sur l'ouverture de l'application.
- Le type `PendingReport` du dossier technique est remplacé par ce schéma.

## C. Exigences de sécurité de l'audit, liées aux FR

| Audit | FR / NFR | Exigence d'implémentation |
|---|---|---|
| S1 (fuite par idempotence) | FR-9 | Clé unique par auteur ou appareil (B.1, point 11) ; 409 sans contenu pour un autre appelant |
| S2 (téléphone) | §6.1 | HMAC avec pepper dans les secrets ; numéro chiffré en AES-GCM |
| S3 (OTP affiché) | FR-6 | Contrôle au démarrage `ENV=production` + `DEMO_MODE` → arrêt ; test |
| S4 (stockage des jetons) | FR-2 | Jeton d'accès en mémoire ; refresh en cookie `HttpOnly; Secure; SameSite=Strict`, chemin `/v1/auth` |
| S5 (JWT) | FR-2 | Liste blanche d'algorithmes (EdDSA ou RS256), `iss`/`aud`/`exp`, `kid` |
| S6 (OTP) | FR-1 | OTP haché dans Redis, comparaison à temps constant, 5 essais |
| S7 (limitation de débit) | FR-1, FR-10 | Limitation dans l'API (Redis) ; proxys de confiance pour `X-Forwarded-For` |
| S8 (positions publiques) | FR-24, FR-34 | Agrégation par grille ou par Zone ; arrondi à 3 décimales avant l'acceptation d'une Mission |
| S9 (visages) | FR-4, FR-7, FR-23, FR-29 | Consigne à chaque capture + modération avant exposition ; purge sous 24 h pour le motif « Personne ou plaque visible » |
| S10 (moindre privilège en base) | NFR-17 | Rôles `teranga_app` (sans DDL, INSERT et SELECT seuls sur `audit_logs`) et `teranga_migrator` |
| S11 (`/docs`, `/readyz`) | NFR-7 | `/docs` et `/openapi.json` désactivés hors démo ; `/readyz` sans détails internes |
| S12 (CPU de classification) | FR-14 | Classification serveur en tâche arq, file bornée |
| Contrat async (S12) | FR-14 | `POST /v1/reports` reçoit `pile_size`, `accuracy_m`, `waste_type` choisi, `client_prediction`, en-têtes d'appareil et d'idempotence ; il répond 201 (création) ou 200 (renvoi) avec `tracking_number`, `status` et `classification.status = pending` |
| Second facteur | FR-43 | TOTP (RFC 6238) ; secret chiffré |
| Suspension | FR-5, FR-35 | Jeton d'accès de 15 min ; `is_active` vérifié à chaque requête (ou liste de révocation dans Redis) |
| Exposition | NFR-7, NFR-8 | `/v1/ai/classify` non exposé par le proxy ; `/metrics` sur le réseau interne ; délai d'expiration et taille maximale du corps au proxy ; photos sur un domaine distinct |

**Points d'infrastructure à ne pas oublier :**

- La CSP doit inclure `'wasm-unsafe-eval'` pour onnxruntime-web (NFR-8).
- Épingler les images par empreinte et les actions GitHub par SHA de commit (NFR-10).
- Healthcheck sans `curl`.
- `Image.MAX_IMAGE_PIXELS` réglé explicitement.

## D. IA : choix de mise en œuvre

- **Interface stable :** `classify(image) -> {predicted_type, confidence, scores, model_version, needs_user_choice}`, identique entre le Modèle entraîné (visé à H24) et le **Modèle factice** (repli à H24).
- **Prétraitement unique** pour l'évaluation, le serveur et le navigateur : redimensionnement du petit côté à 256, recadrage central 224×224, normalisation ImageNet. Un test compare les sorties des trois chaînes sur 20 images (écart de score ≤ 0,01). Sinon, Désaccords IA artificiels.
- **Calibration** par température, pour que le Seuil de confiance ait un sens (ECE ≤ 0,10, SM-2).
- **Découpage du jeu de données** par lieu et par jour de prise de vue ; Jeu de test figé d'au moins 150 photos par classe ; Fiche du Modèle avec les licences des données.
- **Entraînement** en deux phases ; quantification statique INT8 avec environ 200 images de calibration ; fichier ≤ 8 Mo (NFR-5).
- **Annotation** : double vérification de 20 % des photos ; cas ambigus classés `mixte`.
- **Réentraînement au pilote** : manuel, au plus une fois par mois ; export filtré par modération et consentement (FR-13) ; évaluation sur le Jeu de test figé avant toute publication (FR-16).

## E. Raisons des choix par défaut (chemin rapide)

- **F1 macro plutôt que top-1 accuracy.** Les classes sont déséquilibrées (le plastique domine). La top-1 accuracy peut atteindre 80 % en sacrifiant le métal ou le verre ; le F1 macro, non.
- **Docker Compose en fin de hackathon.** Moins de pièces mobiles et répétable sur un portable de secours. AWS n'apporte rien à la démo.
- **Pilote à 60 % sur 6 mois.** C'est le chiffre déjà remis au jury dans le Proposal.

## F. Exploitation et hygiène du dépôt

### F.1 Exploitation

- **Déploiement :** `docker compose pull && docker compose up -d` ; migrations Alembic avant le démarrage de la nouvelle version ; retour arrière en relançant le tag précédent. Python 3.12 exécuté via Docker ou `uv`, quel que soit le Python du poste.
- **Sauvegardes (NFR-15) :** `pg_dump` quotidien chiffré hors site ; versionnement du stockage objet ; exercice de restauration avant les données réelles.
- **Supervision (NFR-16) :** journaux Docker au hackathon, CloudWatch au pilote ; les 4 alertes de NFR-16.
- **Clés :** fichier d'environnement au hackathon ; KMS au pilote ; chiffrement du disque et de la base au pilote (NFR-17).
- **Purge (§6.1) :** tâche arq planifiée chaque nuit ; testée avec une horloge simulée.
- **Fonds de carte :** tuiles publiques d'OpenStreetMap pour la démo seulement ; fournisseur ou serveur propre au pilote.
- **Modularité :** un module n'accède jamais aux tables d'un autre, il passe par son service.
- **Stockage objet :** choisir entre MinIO, Garage et SeaweedFS avant H24 (vérifier qu'une image MinIO utilisable existe).

### F.2 Hygiène du dépôt public (epic E0, porte H24)

- `TerangaCycle AI/` n'est jamais suivi ; test CI : `git ls-files` ne contient aucun chemin `TerangaCycle AI/`.
- `.env.example` liste toutes les variables (`ENV`, `DEMO_MODE`, clés JWT, pepper, clé AES) avec des valeurs factices ; démarrer avec `ENV=production` sans les secrets requis échoue.
- `SECURITY.md` indique un canal privé de signalement et un délai de réponse.
- `main` protégée : PR obligatoire, CI verte requise, pas de *force push* ; *secret scanning*, *push protection* et Dependabot (pip, npm, Docker, GitHub Actions) activés.
- Gitleaks lancé en binaire (licence MIT) plutôt que par `gitleaks-action` si le dépôt passe dans une organisation GitHub.
- `LICENSE` à la racine dès que Mia a tranché (PRD §11, Q1 ; H60).

## G. Actions hors PRD pour l'équipe

Ces actions ne sont pas des exigences du produit. Elles découlent du triage des relectures.

**Project Proposal (PDF remis au jury)**
- Si le PDF peut être redéposé : MobileNetV3-Small devient Large, et « deployment on AWS » devient « Docker Compose, AWS au pilote ».
- Sinon, préparer 5 phrases pour l'oral :
  1. « Large par défaut, Small si la latence dépasse 3 s ; mesure à H24. »
  2. « F1 macro, plus honnête avec des classes déséquilibrées ; la top-1 promise est aussi publiée. »
  3. « Portable d'abord, AWS au pilote, par souveraineté. »
  4. « Vert foncé pour l'accessibilité AA. »
  5. « Mono-commune au pilote, conçu pour être répliqué. » (Zone active, PRD §8.)

**Pitch**
- Obtenir un témoignage de terrain : collecteur ou commune contactés. Responsable à désigner.
- Garder les messages de pitch : sens de *teranga*, complémentarité avec les applications existantes, modèle économique (abonnement des communes, commission sur les Lots de matière, subventions), « chaque correction consentie devient un exemple ».
- Lots de matière : à l'oral, assumer qu'ils viennent avec le pilote, comme dans le Proposal (PRD §9.2).

**Maquette Figma**
- Elle est figée (quota Figma) : ne pas la modifier.
- Reporter dans la spécification UX la liste des nodes (1:2 Accueil, 1:39 Capture, 1:57 Résultat IA, 1:97 Confirmation, 2:2 Missions, 2:35 Preuve, 2:65 Tableau de bord), **sans la clé du fichier**, ainsi que les écrans hors maquette du PRD §7.
- Les captures du Proposal gardent `#1F8A5B` : l'annoncer à l'oral comme correction d'accessibilité.
- Vérifier le partage « Anyone with the link can view ».

**Documents sources**
- **`docs/cahier-des-charges.md` (responsable : Mia) :**
  - critère du pilote (80 % sur 4 à 6 semaines → 60 % sur 6 mois) ;
  - pitch (5 min → 1 min 30) ;
  - délai moyen → Délai médian ;
  - poids estimé → Poids déclaré.
- **`docs/dossier-technique.md` :**
  - marquer comme remplacés le prétraitement (Resize 224 sans recadrage), `PendingReport`, `flushQueue` sans jeton, les 4xx renvoyés sans fin, le reclassement synchrone et le hachage salé du téléphone ;
  - renvoyer vers cet addendum (B, C, D).

**Dépôt (epic E0, avant H24, responsable proposé : Ahmadou)**
- Committer le `.gitignore` modifié.
- Ajouter `.env.example` et `SECURITY.md` (F.2).
- Protéger `main`, activer *secret scanning*, *push protection* et Dependabot.
- Ajouter `LICENSE` dès que Mia a tranché (H60).
- Avant de committer `_bmad-output/`, chercher la clé du fichier Figma dans tous les fichiers. Les rapports de relecture et le triage n'en contiennent pas, mais il faut le vérifier.
- Exécuter Python 3.12 via Docker ou `uv` (le poste a la 3.15).

**Organisation**
- Confirmer l'inscription au hackathon et l'équipe de trois auprès des organisateurs.
- Démo : préparer les 10 photos locales, enregistrer la vidéo avant H60, mettre en cache les tuiles de la zone de démo (exigé par NFR-7 et PRD §9.3, réalisé par l'équipe).
- Commune partenaire : préparer le dossier CDP (déclaration avant les données réelles, transfert hors Sénégal si AWS) ; valider les durées de conservation ; négocier l'incitation des Collecteurs (PRD §11, Q5 et Q7).
