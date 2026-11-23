---
type: reconciliation
source: docs/dossier-technique.md (version du 9 novembre 2026)
cible: prd.md + addendum.md (prd-TerangaCycleAI-2026-11-23)
date: 2026-11-23
statut: à arbitrer par Mia ; prd.md et addendum.md non modifiés
---

# Réconciliation : dossier technique ↔ PRD et addendum

## 0. Méthode et périmètre

- **Source lue en entier :** `docs/dossier-technique.md` (§1 à §8, 961 lignes). Les références `src L.nnn` renvoient à ses numéros de ligne.
- **Cibles lues en entier :** `prd.md` (40 FR, 14 NFR), `addendum.md` (§A à §E), `.memlog.md`.
- **Règle de tri :**
  - un comportement **observable** (code HTTP, seuil, délai, droit, règle visible par un utilisateur, un exploitant ou un auditeur) relève du **PRD** ;
  - un choix de **mise en œuvre** (table, colonne, outil, bibliothèque, pipeline) relève de l'**addendum**.
- **Écarté, car tranché dans le memlog :**
  - MobileNetV3-Large par défaut ;
  - F1 macro ≥ 0,80 et rappel ≥ 0,70 comme métrique annoncée ;
  - rayon de 5 km réglable de 1 à 10 km ;
  - pilote à 60 % sur 6 mois ;
  - pitch de 1 min 30 ;
  - Docker Compose en fin de hackathon ;
  - S1 à S12 intégrés comme exigences, ce qui couvre notamment le HMAC du téléphone, la limitation dans l'API, la classification serveur en tâche de fond, le cookie de refresh, `/docs` et `/readyz` ;
  - vert `#187A50` ;
  - Lots de matière après H48 ;
  - consentement à H24.

Gravité :
- **H** : bloque l'architecture, les stories ou la crédibilité devant le jury ;
- **M** : exigence vérifiable manquante ;
- **B** : précision utile.

---

## 1. Écarts PRD : comportements exigés par la source et absents du PRD

### 1.1 Règles d'intégrité

| ID | Exigence de la source | État du PRD | Gravité |
|---|---|---|---|
| E-I1 | **Transitions interdites → 409, partout.** « Toute autre transition retourne 409 et aucune n'est possible depuis `rejected` ou `collected` » (src L.404). Les transitions de Mission `accepted`, `in_progress`, `cancelled` et `completed` passent par `PATCH /v1/missions/{id}` (src L.323). | La règle n'existe que dans FR-23, donc pour la modération seule. Rien pour FR-25, FR-26 et FR-29 : accepter un Signalement non `validé`, annuler une Mission terminée, prouver une Mission annulée. Le PRD n'a **aucun Statut de Mission** : « terminée » apparaît dans FR-29, et « en cours » n'existe pas. | H |
| E-I2 | **Idempotence des autres POST sensibles** : en-tête `Idempotency-Key` (src L.278). | Absente. Conséquence observable : un Collecteur sur réseau instable qui renvoie sa Preuve de collecte (FR-29) pourrait doubler les kg valorisés (FR-31). La validation en double clic (FR-23) et l'acceptation répétée (FR-25) ne sont pas couvertes non plus. | H |
| E-I3 | Un renvoi idempotent retourne l'existant en **200**, une création en **201** (src L.262, L.308). | FR-9 dit « renvoie le Signalement existant » sans code. Le client hors-ligne (FR-18) en dépend pour vider sa file. | B |
| E-I4 | **Une seule Mission active par Signalement**, garantie par la base et pas seulement par le code (src L.263). | Le Glossaire et FR-25 couvrent le comportement. La garantie par la base est absente de l'addendum (voir §2.2). | B (PRD) |

### 1.2 Pagination bornée

| ID | Exigence de la source | État du PRD | Gravité |
|---|---|---|---|
| E-P1 | Pagination par curseur, `?limit=50&cursor=…`, réponse `{items, next_cursor}` (src L.277). La « pagination bornée » sert de contrôle anti-déni de service (src L.536). | Absente. Listes concernées : FR-20 (mes Signalements), FR-22 (File de modération), FR-24 (missions proches), FR-30 (historique), FR-35 (comptes), FR-36 (Journal d'audit), FR-21 (notifications). Aucune taille maximale de page n'est fixée. | M |

### 1.3 Limites de débit

| ID | Exigence de la source | État du PRD | Gravité |
|---|---|---|---|
| E-R1 | **60 requêtes/min par utilisateur connecté** (src L.279). | Absente. Le PRD ne limite que l'OTP (FR-1) et le signalement anonyme (FR-10). | M |
| E-R2 | Limite par IP, appareil **et compte** contre le spam (src L.528). | FR-10 ne vise que l'anonyme. Rien ne borne le nombre de Signalements d'un Citoyen connecté, hormis E-R1. | B |

### 1.4 Sécurité

| ID | Exigence de la source | État du PRD | Gravité |
|---|---|---|---|
| E-S1 | **Second facteur pour le Personnel** : OTP plus un second facteur ou, à défaut, mot de passe Argon2id pour l'Administrateur et le Modérateur (src L.543). | Absent. FR-1 applique le même OTP par SMS à tous les rôles. Les comptes qui exportent les données (FR-33), suspendent des comptes (FR-35) et voient les positions précises ne sont donc protégés que par un SMS. | H |
| E-S2 | **En-têtes et transport** : redirection HTTP → HTTPS, CSP stricte, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, CORS limité aux origines du front (src L.541-542). | NFR-8 ne cite que TLS 1.2 et HSTS. | M |
| E-S3 | **Sauvegardes** quotidiennes chiffrées, restauration testée, stockage objet versionné ; alerte en cas d'échec d'une sauvegarde (src L.537, L.961). | Absentes. Aucune NFR de continuité, alors que le pilote porte sur des données réelles. | H |
| E-S4 | **Chiffrement au repos** du disque et de la base ; clés gérées par un service de clés que l'organisation contrôle (src L.544, L.597). | §6.1 ne chiffre que le numéro. | M |
| E-S5 | Journal d'audit pour la modération, **l'assignation** et la gestion des comptes (src L.546). | FR-23 et FR-35 sont couverts. **FR-28 (assignation manuelle) ne journalise pas.** Le caractère « non modifiable » du Journal (Glossaire) n'a aucun critère testable. | M |
| E-S6 | Photos dans un bucket privé, servies par URL signée de 5 min, et **stockage hors du domaine de l'API** (src L.531, L.545). | Les 5 min sont couvertes (§6.1). La séparation de domaine, qui empêche un fichier piégé de s'exécuter dans l'origine de l'API, n'est pas exigée. | B |
| E-S7 | **Vérification des Preuves par échantillon** par le Personnel (src L.529). | Citée en §6.2 et utilisée par SM-C3 (« part de Preuves contestées »), mais **aucune FR** ne décrit qui échantillonne, comment une Preuve est contestée, ni ce qu'il advient du Statut et des kg. SM-C3 n'est donc pas mesurable. | H |
| E-S8 | Session : jeton d'accès de 15 min (src L.275, L.526). | FR-35 exige qu'un compte suspendu perde l'accès « immédiatement ». Avec un jeton sans état de 15 min, ce n'est vrai que si l'architecture vérifie l'état du compte à chaque requête. Il faut préciser le délai acceptable dans le PRD et le mécanisme dans l'addendum. | M |

### 1.5 Conformité et vie privée

| ID | Exigence de la source | État du PRD | Gravité |
|---|---|---|---|
| E-C1 | Droits d'**accès, de rectification et de suppression** exposés dans l'application (src L.584). Le consentement est modifiable via `PATCH /v1/me` (src L.301). | FR-5 couvre la consultation, le nom, la langue et la suppression. Il manque **le retrait ultérieur du consentement au réentraînement** (FR-4 ne prévoit qu'un refus initial) et l'accès à ses propres données au-delà du profil. | M |
| E-C2 | Conservation : photos 12 mois, statistiques sans limite, comptes purgés sous 30 jours (src L.583). | Le tableau du §6.1 est repris, mais le PRD n'exige pas **la purge automatique effective** (critère testable). La durée de conservation des **photos de Preuve** (avant et après) n'est pas fixée. | M |
| E-C3 | Une Correction ne devient un exemple d'entraînement que **« sous réserve de modération »** (src L.513). Le consentement couvre l'usage des photos (src L.427). | FR-13 rend toutes les Corrections exportables, sans filtre de modération ni de consentement (FR-4). | H |
| E-C4 | Floutage automatique des visages et des plaques prévu **après le MVP** (src L.585). | Ni dans les non-objectifs (§8), ni dans la feuille de route du pilote (§9.2). | B |
| E-C5 | Le serveur de tuiles public d'OpenStreetMap interdit un usage intensif : le pilote doit passer par ses propres tuiles ou un fournisseur adapté (src L.726). | Absent. Contrainte de conformité pour le pilote, à placer dans §9.2 ou §6.4. | M |

### 1.6 Évaluation IA

| ID | Exigence de la source | État du PRD | Gravité |
|---|---|---|---|
| E-A1 | **Calibration : ECE ≤ 0,10**. « Le seuil de 60 % n'a de sens que si les scores sont calibrés » (src L.507). | Absente du PRD. Elle n'est que dans l'addendum (§D), comme moyen. Le Seuil de confiance (FR-12) est un comportement observable qui en dépend : ce critère doit figurer dans SM-2. | H |
| E-A2 | Jeu de test : **≥ 150 photos locales par classe**, **figé**, découpé par lieu et par jour (src L.424, L.426, L.857). | SM-2 dit seulement « jeu de test local conservé ». Sans taille minimale, le F1 et le rappel par classe annoncés au jury sont fragiles. | M |
| E-A3 | Latence de la **Classification serveur** : p95 < 2 s (src L.956). | Absente. NFR-1 ne couvre que la Classification locale. Avec une classification serveur asynchrone (S12), ce délai borne aussi le temps avant qu'un Signalement soit modérable. | M |
| E-A4 | La fiche du Modèle annonce les **limites** : photos sombres, tas mélangés, déchets mouillés (src L.515-516). | §6.3 ne mentionne que les licences. Le contenu minimal de la fiche (données, limites, métriques, matrice de confusion) n'est pas exigé. | B |

### 1.7 Boucle de réentraînement

| ID | Exigence de la source | État du PRD | Gravité |
|---|---|---|---|
| E-L1 | **Surveillance et déclenchement** : suivre la part de Signalements corrigés et la distribution des scores ; réentraîner si les Corrections dépassent **25 % sur 2 semaines**, ou chaque mois pendant le pilote (src L.514). | Absent. SM-8 (baisse mensuelle des Corrections) est un objectif, pas une règle de déclenchement. Aucune FR ne décrit le suivi, le seuil, ni la publication d'une nouvelle version (FR-16 permet seulement le remplacement). | H |
| E-L2 | Alerte de **dérive** : médiane des scores de confiance en baisse de 15 points ou plus (src L.957). | Absente. | M |

### 1.8 Observabilité et alertes

| ID | Exigence de la source | État du PRD | Gravité |
|---|---|---|---|
| E-O1 | Tableau de 8 alertes (src L.952-961) :<br>• 5xx > 2 % sur 5 min ;<br>• p95 de l'API > 500 ms sur 10 min ;<br>• p95 de la classification serveur > 2 s ;<br>• dérive des scores ;<br>• Corrections > 25 % sur 2 semaines ;<br>• croissance anormale des Signalements en attente côté client ;<br>• demandes OTP au-dessus du plafond ;<br>• échec d'une sauvegarde et espace disque. | NFR-14 ne couvre que les journaux. Aucune alerte n'est exigée, sauf le plafond de coût SMS (FR-1). | H |
| E-O2 | Les journaux contiennent `request_id`, rôle, route et durée (src L.948). | NFR-14 ne cite que l'identifiant de requête. | B |
| E-O3 | **Remontée de la taille de la File hors-ligne** par le client (src L.959). C'est un comportement de la PWA, observable côté serveur. | Absente de FR-17 à FR-19. | M |
| E-O4 | Endpoint de métriques **protégé** (src L.949). | Absent (voir aussi §2.2). | B |

### 1.9 Sondes `/healthz` et `/readyz`

| ID | Exigence de la source | État du PRD | Gravité |
|---|---|---|---|
| E-H1 | `/healthz` répond si le processus vit. `/readyz` vérifie la base, le stockage et le **Modèle chargé** (src L.357-358, L.950). | NFR-7 dit « sondes de vie et de disponibilité » sans en définir le contenu. Le cas « Modèle absent → non prêt » n'est pas exigé. L'addendum S11 interdit seulement d'exposer les détails internes. | M |

### 1.10 Plan de sortie et réversibilité

| ID | Exigence de la source | État du PRD | Gravité |
|---|---|---|---|
| E-X1 | Plan en 4 points (src L.702-707) :<br>1. export `pg_dump` et objets S3 standard ;<br>2. déploiement décrit par Docker et Terraform ;<br>3. Modèle ONNX possédé par le projet ;<br>4. **test de migration vers un serveur local inscrit dans la feuille de route du pilote**.<br>S'y ajoutent des clés de chiffrement contrôlées par l'organisation (src L.597). | §6.4 dit « plan de sortie documenté », sans critère vérifiable : ni test de migration, ni maîtrise des clés. C'est l'argument central face au jury sur AWS (src L.595-597). | M |

### 1.11 Autres comportements absents ou divergents

| ID | Exigence de la source | État du PRD | Gravité |
|---|---|---|---|
| E-D1 | `GET /v1/reports/mine` est réservé au citoyen **connecté** (src L.310). | **Incohérence interne au PRD.** Dans UJ-1, Awa est **anonyme** et « voit plus tard Validé, puis Collecté ». FR-20 ne dit pas comment un anonyme suit son Signalement (lié à l'appareil ? au Numéro de suivi ?), et aucune route de la source ne le permet. | H |
| E-D2 | Les modérateurs sont prévenus à chaque nouveau Signalement (src L.85). | Absent de FR-22. | B |
| E-D3 | `GET /v1/missions/nearby` accepte un filtre `type` ; le profil collecteur porte `accepted_types` (src L.157, L.320). | FR-24 n'a pas de filtre par Type de déchet. | B |
| E-D4 | Accessibilité : **navigation au clavier** sur les écrans d'administration (src L.823). | Absente de NFR-12. | M |
| E-D5 | §6.1 du PRD : positions précises réservées au Personnel et au **Collecteur de la Mission**. Source : réservées au staff (src L.533). | **Incohérence interne au PRD et à la source.** FR-24 montre à **tout** Collecteur vérifié la position (carte et distance) des Signalements `validé`, avant toute Mission. Il faut trancher : position précise visible avant acceptation, ou position arrondie jusqu'à l'acceptation. | M |
| E-D6 | Wolof écrit et relu par des locuteurs natifs **avant la démo** (src L.819). | Le PRD le met en non-objectif (§8) et dans la feuille de route du pilote (§9.2). L'arbitrage est raisonnable mais **non journalisé dans le memlog**. | B |
| E-D7 | Indicateur `/analytics/summary` en **délai moyen** (src L.339) ; série temporelle par jour ou par semaine (src L.341). | Le PRD retient le délai médian, choix plus robuste à conserver, sans le signaler comme écart. Aucune FR ne couvre la série temporelle : à classer dans le périmètre ou hors périmètre. | B |
| E-D8 | Position dans le Sénégal mais hors de toute Zone connue : la source déduit la Zone par `ST_Contains` (src L.84). | FR-7 ne dit pas ce qui se passe hors des Zones chargées : le jeu de démonstration ne couvre que Dakar. | B |
| E-D9 | Le Modèle quantifié pèse environ 6 Mo (src L.476) et est précaché (src L.718). | NFR-5 exclut le Modèle du budget de 500 Ko sans lui fixer de plafond. Le premier chargement sur un forfait épuisé (UJ-1) n'a pas de cible. | B |

---

## 2. Écarts addendum

### 2.1 Contradictions de l'addendum avec la source : contrôle de justification

| Point de l'addendum | Source | Raison journalisée ? | Verdict |
|---|---|---|---|
| §B4 : `phone_hash` en HMAC avec pepper | « hachage salé » (src L.140, L.544) | Oui : audit S2, couvert par la décision S1-S12 du memlog | Conforme |
| §C S7 : limitation de débit dans l'API (Redis) | Limitation dans Caddy (src L.611) et « au bord » (src L.536) | Oui : S7 | Conforme. Le **délai d'expiration** et la **taille maximale du corps de requête au proxy** (src L.536) ne sont plus portés nulle part (voir §2.2). |
| §C S12 et FR-14 : Classification serveur asynchrone | Synchrone : le 201 contient la classification serveur (src L.83, L.86, L.375-387) | Oui : S12 | Justifié, mais **le contrat de réponse de `POST /v1/reports` n'est pas mis à jour**. Ce que renvoie le 201 (Classification locale ? `classification: pending` ?) n'est dit nulle part. |
| §C S4 : refresh en cookie `HttpOnly` sur `/v1/auth` | Refresh rotatif, sans précision sur le stockage (src L.275) | Oui : S4 | Conforme |
| §C S11 : `/docs` désactivé hors démo | « FastAPI génère `/docs` » (src L.271) | Oui : S11 | Conforme |
| §C : healthcheck sans `curl` | `curl -f` dans le compose (src L.641) | Oui : audit | Conforme |
| §B2 : unicité `(auteur ou appareil, client_uuid)` | `client_uuid UNIQUE` global (src L.164) | Oui : S1 | Conforme. Effet de bord non traité : après suppression d'un compte, `author_id` passe à NULL (src L.266). La clé d'unicité devient alors ambiguë. |
| §D : « prétraitement identique, 224×224 » | `eval_tfm` = Resize 256 + CenterCrop 224 (src L.444-447), mais l'inférence serveur fait `resize((224,224))` sans recadrage (src L.489) | — | **Incohérence de la source non relevée par l'addendum.** L'évaluation (SM-2) et la production ne voient pas la même image : les métriques annoncées au jury ne refléteraient pas le comportement réel. L'addendum doit fixer **un** prétraitement commun à l'évaluation, au serveur et au navigateur. |

**Conclusion :** aucune contradiction injustifiée. Il reste deux trous dans des contradictions justifiées : le contrat de réponse en mode asynchrone, et la protection au bord abandonnée. Il reste aussi une incohérence de la source à corriger : le prétraitement.

### 2.2 Éléments de la source à porter dans l'addendum pour `bmad-architecture`

**API et conventions (à ajouter au §A ou dans un nouveau §F)**
1. Pagination par curseur : `limit` à 50 par défaut, maximum à fixer (100 proposé), réponse `{items, next_cursor}` (src L.277).
2. En-tête `Idempotency-Key` sur les POST sensibles : preuves, acceptation de Mission, modération, assignation. Préciser le stockage de la clé (Redis avec durée de vie, ou table) et sa portée par utilisateur (src L.278).
3. 60 req/min par utilisateur ; 10 Signalements/h par appareil ou IP pour les anonymes (src L.279).
4. Dates ISO 8601 en UTC, coordonnées `{lat, lng}` en WGS84, JSON UTF-8 (src L.276).
5. Contrat de `POST /v1/reports` à compléter :
   - champs de la requête : `pile_size`, `accuracy_m`, `waste_type` choisi ou corrigé, `client_prediction` (type, confiance, `model_version`), identifiant d'appareil ;
   - réponse 201 ou 200 en mode asynchrone (S12).
6. Routes absentes de la source mais exigées par le PRD :
   - carte publique agrégée (FR-34) : `/v1/analytics/heatmap` est réservée à l'admin ;
   - suivi d'un Signalement par un anonyme (E-D1) ;
   - échantillonnage et contestation d'une Preuve (E-S7) ;
   - retrait du consentement (E-C1).
7. `POST /v1/ai/classify` est un « service interne » (src L.355). Préciser qu'il n'est **pas** exposé par le reverse proxy (lien avec S12, épuisement du CPU).
8. Endpoint de métriques Prometheus **protégé** : réseau interne ou authentification (src L.949).

**Schéma (à ajouter au §B)**

9. **Preuve de collecte** : le schéma ne stocke **ni la position du Collecteur ni sa précision** (src L.205-213). FR-29 et l'échantillonnage en ont besoin. Ajouter `proof_location GEOGRAPHY(Point)` et `proof_accuracy_m` à `missions`, ou une table `collection_proofs`. Relier les photos `before` et `after` à la **Mission**, pas seulement au Signalement (src L.183) : une Mission annulée puis reprise mélangerait les photos.
10. Statut de revue de Preuve (`unreviewed`, `confirmed`, `contested`) pour l'échantillonnage (E-S7) et SM-C3.
11. Correspondance des statuts de Mission (`accepted`, `in_progress`, `completed`, `cancelled`) avec le vocabulaire du PRD.
12. Index unique partiel `missions_one_active_per_report` : la règle « une Mission active » est garantie par la base (src L.214-216, L.263). À conserver explicitement.
13. `audit_logs` en **ajout seul** : `teranga_app` a INSERT et SELECT, sans UPDATE ni DELETE. C'est la condition du caractère « non modifiable » du Journal ; à ajouter à S10.
14. Retirer `users.points` (src L.145) : non-objectif « Points citoyens » et minimisation.

**Sécurité (à ajouter au §C)**

15. Mécanisme du second facteur du Personnel (OTP plus TOTP, ou Argon2id à défaut) (src L.543).
16. En-têtes de sécurité : `nosniff`, `Referrer-Policy: no-referrer`, CORS limité aux origines du front, redirection vers HTTPS. La CSP stricte existe déjà avec `'wasm-unsafe-eval'` (src L.541-542).
17. Photos servies depuis un domaine distinct de l'API (src L.531).
18. Jeton d'accès de 15 min (src L.275) et suspension « immédiate » (FR-35) : vérifier `is_active` à chaque requête ou tenir une liste de révocation.
19. Protection au bord conservée malgré S7 : délais d'expiration et taille maximale du corps au proxy (src L.536).
20. Clés : KMS au pilote, Vault ou secrets chiffrés à la cible, fichier d'environnement au hackathon (src L.609). Chiffrement disque et base (src L.544).
21. CI bloquante : **Bandit et Semgrep**, en plus de Gitleaks, pip-audit, npm audit et Trivy (src L.589). Bandit et Semgrep manquent dans NFR-10 comme dans l'addendum.

**IA (à ajouter au §D)**

22. Prétraitement unique pour l'évaluation, le serveur et le navigateur (voir §2.1).
23. Entraînement en deux phases ; quantification statique INT8 avec environ 200 images de calibration ; budget de taille de l'ordre de 6 Mo (src L.416, L.476).
24. Annotation : double vérification de 20 % des photos ; cas ambigus classés en `mixed` (src L.425).
25. Versionnage des jeux de données avec DVC ; numéro de version dans le nom du fichier (src L.515).
26. Chaîne de réentraînement :
    - export des Corrections modérées et consenties ;
    - surveillance de la part de Corrections et de la distribution des scores ;
    - seuil de 25 % sur 2 semaines ;
    - script d'évaluation sur le jeu de test figé, exécuté avant toute publication d'une version (src L.514, L.857).

**Exploitation (nouveau §F proposé)**

27. Déploiement : `docker compose pull && up -d` ; migrations Alembic **avant** le démarrage de la nouvelle version ; retour arrière en relançant le tag précédent (src L.944).
28. Sauvegardes : `pg_dump` quotidien chiffré hors site, versionnement du bucket, exercice de restauration (src L.537, L.604, L.696-699).
29. Observabilité : champs des journaux, `/metrics`, tableau des 8 alertes avec leurs seuils, outil par niveau (journaux Docker, puis CloudWatch, puis Prometheus et Grafana) (src L.610, L.946-961).
30. Sondes : `/readyz` vérifie la base, le stockage et le Modèle chargé (src L.358).
31. Plan de sortie en 4 étapes, dont le test de migration vers un serveur local (src L.702-707).
32. Fonds de carte : tuiles OSM publiques pour la démo seulement ; fournisseur ou serveur propre pour le pilote (src L.726).
33. Tableau « Évolution prévue » (src L.88-95) à reprendre comme signaux de passage à l'échelle. Il ouvre une question pour le pilote : un Administrateur commune est-il limité à **sa** commune (isolation par `tenant`) ?
34. Règle de modularité : un module n'accède jamais aux tables d'un autre, il passe par son service (src L.76).

**PWA hors-ligne (nouveau §G proposé) : défauts du code de la source à ne pas reprendre tels quels**

35. `PendingReport` ne stocke ni la Taille de tas, ni le Type choisi, ni la Classification locale, ni la précision GPS (src L.757-765). FR-17 exige 100 % des champs.
36. `window.addEventListener("online", () => void flushQueue())` appelle `flushQueue` **sans jeton** (src L.812). Un Citoyen connecté renverrait donc en anonyme. Avec l'unicité par auteur ou appareil (S1), le renvoi recevrait un **409** au lieu de 200, ou créerait un doublon. Cela viole FR-9 et SM-4. L'identifiant d'appareil n'est envoyé nulle part non plus.
37. Une erreur 4xx autre que 429 incrémente `attempts` sans jamais sortir le Signalement de la file (src L.803-805). Il est renvoyé indéfiniment. FR-18 exige d'afficher le motif d'un refus définitif.
38. Background Sync sur Chrome Android, avec repli sur l'événement `online` et sur l'ouverture de l'application (src L.815) : à conserver.

---

## 3. Propositions de correction, avec emplacement

> Les ajouts proposés sont en texte prêt à coller. Les nouveaux identifiants (FR-41 et suivants, NFR-15 et suivants) prolongent la numérotation existante. Les valeurs non fixées par la source portent `[ASSUMPTION]`.

### 3.1 Dans `prd.md`

| N° | Emplacement | Correction proposée | Écart |
|---|---|---|---|
| P-1 | §3 Glossaire, après « Statut » | Ajouter **Statut de Mission** : « `acceptée` → `en cours` → `terminée` ; `acceptée` ou `en cours` → `annulée`. `terminée` et `annulée` sont terminaux. » | E-I1 |
| P-2 | §3 Glossaire, « Statut », dernière phrase | Ajouter : « Toute transition non prévue, d'un Signalement ou d'une Mission, est refusée (409) et ne modifie rien. » | E-I1 |
| P-3 | FR-25, FR-26, FR-29 : Conséquences | FR-25 : « Accepter une Mission sur un Signalement qui n'est pas `validé` renvoie 409. »<br>FR-26 : « Annuler une Mission `terminée` ou déjà `annulée` renvoie 409. »<br>FR-29 : « Une Preuve sur une Mission qui n'est pas active renvoie 409 ; une Preuve soumise par un autre Collecteur que celui de la Mission renvoie 403. » | E-I1 |
| P-4 | FR-29 : Conséquences (et FR-23, FR-25) | « Le renvoi d'une même Preuve de collecte, par exemple après une coupure réseau, n'enregistre qu'une Preuve et qu'un Poids mesuré. » Même règle pour une décision de modération et une acceptation répétées. | E-I2 |
| P-5 | FR-9 : Conséquences | « La première réception renvoie 201 ; un renvoi par le même auteur ou le même appareil renvoie 200 avec le même Numéro de suivi. » | E-I3 |
| P-6 | §5, nouvelle **NFR-15** | « Pagination bornée : toute liste est paginée par curseur, 50 éléments par défaut et 100 au plus `[ASSUMPTION]` ; au-delà, la taille est ramenée au maximum. Vérification : test d'API. » | E-P1 |
| P-7 | §5, nouvelle **NFR-16** | « Limite de débit : 60 requêtes par minute par utilisateur connecté ; au-delà, 429. Vérification : test de charge. » | E-R1, E-R2 |
| P-8 | FR-1 : nouvelle Conséquence, ou nouvelle **FR-41 : Connexion renforcée du Personnel** | « Un Modérateur ou un Administrateur commune s'authentifie avec un second facteur en plus de l'OTP par SMS. Sans second facteur, l'accès aux fonctions du Personnel est refusé. » | E-S1 |
| P-9 | §5, **NFR-8** | Compléter : « redirection HTTP → HTTPS ; CSP stricte ; `X-Content-Type-Options: nosniff` ; `Referrer-Policy: no-referrer` ; CORS limité aux origines du front ; photos servies depuis un domaine distinct de l'API. Vérification : scan des en-têtes. » | E-S2, E-S6 |
| P-10 | §5, nouvelle **NFR-17 : Continuité** | « Sauvegarde quotidienne chiffrée de la base, hors du serveur ; stockage des photos versionné ; perte maximale de 24 h `[ASSUMPTION]` ; une restauration complète est réussie au moins une fois avant le pilote ; tout échec de sauvegarde déclenche une alerte. Vérification : exercice de restauration. » | E-S3 |
| P-11 | §6.1 Protection | Ajouter : « disque et base chiffrés au repos ; clés de chiffrement contrôlées par l'organisation. » | E-S4 |
| P-12 | FR-28 : Conséquences | « Chaque assignation est inscrite au Journal d'audit. » | E-S5 |
| P-13 | FR-36 : Conséquences | « Aucune entrée du Journal d'audit ne peut être modifiée ni supprimée par l'application. Vérification : test de mise à jour refusée. » | E-S5 |
| P-14 | §4.8, nouvelle **FR-42 : Contrôler une Preuve par échantillon** *(Should)* | « Le Personnel tire un échantillon de Preuves acceptées et marque chacune `confirmée` ou `contestée` avec un motif. Une Preuve contestée est retirée des kg valorisés (FR-31) et inscrite au Journal d'audit. » Relier SM-C3 à FR-42. | E-S7 |
| P-15 | FR-35 : Conséquences | Remplacer « perd l'accès immédiatement » par « perd l'accès à sa prochaine requête, au plus tard en 1 min `[ASSUMPTION]` ». Sinon, garder « immédiatement » et laisser l'addendum fixer le mécanisme. | E-S8 |
| P-16 | FR-5 : Conséquences | « L'utilisateur peut retirer à tout moment son consentement au réentraînement ; ses photos ne sont alors plus incluses dans les exports d'entraînement. » « L'utilisateur peut consulter ses Signalements et ses données de profil (droit d'accès) et corriger son nom (rectification). » | E-C1 |
| P-17 | §6.1, tableau de conservation | Ajouter une ligne : « Photos de Preuve de collecte : 12 mois `[ASSUMPTION]` ». Ajouter sous le tableau : « La purge est automatique ; un contrôle vérifie qu'aucune photo n'est plus ancienne que la durée fixée. » | E-C2 |
| P-18 | FR-13 : Conséquences | Remplacer « Les Corrections sont exportables… » par : « Seules les Corrections de Signalements modérés, et dont l'auteur a consenti au réentraînement (FR-4), sont exportées comme exemples étiquetés. » | E-C3 |
| P-19 | §8 Non-objectifs, ou §9.2 | « Floutage automatique des visages et des plaques : après le MVP. La consigne de capture (FR-4) et la modération (FR-23) le compensent. » | E-C4 |
| P-20 | §9.2 ou §6.4 | « Pilote : fonds de carte servis par un fournisseur ou un serveur propre ; les tuiles publiques d'OpenStreetMap sont limitées à la démo. » | E-C5 |
| P-21 | §10 **SM-2** | Ajouter :<br>• « calibration ECE ≤ 0,10 (condition de validité du Seuil de confiance) » ;<br>• « jeu de test figé d'au moins 150 photos locales par classe, découpé par lieu et par jour » ;<br>• « fiche du Modèle publiée : données, licences, limites connues, métriques, matrice de confusion ».<br>Ajouter FR-12 à « Valide ». | E-A1, E-A2, E-A4 |
| P-22 | §5, nouvelle **NFR-18** | « Classification serveur : p95 < 2 s par photo. Vérification : métrique et alerte. » | E-A3 |
| P-23 | §4.3, nouvelle **FR-43 : Surveillance du Modèle et réentraînement** | « Le système suit chaque semaine la part de classifications corrigées et la distribution des scores de confiance. Si les Corrections dépassent 25 % sur 2 semaines, ou chaque mois pendant le pilote, un réentraînement est déclenché. Une nouvelle version n'est publiée (FR-16) que si elle atteint les seuils de SM-2 sur le jeu de test figé. » Relier SM-8 à FR-43. | E-L1, E-L2 |
| P-24 | §5, nouvelle **NFR-19 : Alertes** | Tableau des 8 alertes de la source avec leurs seuils :<br>• 5xx > 2 % sur 5 min ;<br>• p95 de l'API > 500 ms sur 10 min ;<br>• p95 de la classification serveur > 2 s ;<br>• médiane des scores en baisse ≥ 15 points ;<br>• Corrections > 25 % sur 2 semaines ;<br>• croissance anormale des files hors-ligne ;<br>• demandes OTP au-dessus du plafond ;<br>• échec de sauvegarde ou disque presque plein.<br>Vérification : déclenchement simulé. | E-O1 |
| P-25 | §5, **NFR-14** | Compléter : « … identifiant de requête, rôle, route, durée ». | E-O2 |
| P-26 | FR-19 : Conséquences | « Le nombre de Signalements en attente sur l'appareil est remonté au serveur à chaque synchronisation (sans donnée personnelle). » | E-O3 |
| P-27 | §5, **NFR-7** | Remplacer « sondes de vie et de disponibilité » par : « `/healthz` répond tant que le processus vit ; `/readyz` n'est prêt que si la base, le stockage et le Modèle sont disponibles ; aucune sonde n'expose de détail interne. » | E-H1 |
| P-28 | §6.4 Souveraineté | Remplacer « Plan de sortie documenté… » par : « Plan de sortie vérifiable : export complet de la base et des photos en formats standard ; déploiement décrit en Docker et Terraform ; clés contrôlées par l'organisation ; un test de migration vers un serveur local est réalisé pendant le pilote. » | E-X1 |
| P-29 | UJ-1 et FR-20 | Trancher le suivi par un anonyme. Option A : FR-20 « Un Citoyen anonyme suit les Signalements envoyés depuis son appareil » `[ASSUMPTION]`. Option B : UJ-1 corrigé, Awa crée un compte pour suivre. | E-D1 |
| P-30 | FR-22 | « Les Modérateurs sont notifiés de l'arrivée de nouveaux Signalements. » *(Should)* | E-D2 |
| P-31 | FR-24 | « … filtrables par Type de déchet. » | E-D3 |
| P-32 | §5, **NFR-12** | Ajouter « navigation complète au clavier sur les écrans du Personnel ». | E-D4 |
| P-33 | FR-24 et §6.1 | Trancher la visibilité des positions avant acceptation : position précise, ou arrondie jusqu'à l'acceptation. Aligner le §6.1. | E-D5 |
| P-34 | `.memlog.md` (journal, pas le PRD) | Journaliser : « Wolof : préparation seule au MVP, contrairement au dossier technique §7 (relecture avant démo) » et « délai médian plutôt que moyen ». | E-D6, E-D7 |
| P-35 | FR-7 : Conséquences | « Une Position au Sénégal mais hors des Zones chargées est acceptée sans Zone et signalée en modération » `[ASSUMPTION]`. | E-D8 |
| P-36 | §5, **NFR-5** | Ajouter « Modèle ≤ 8 Mo, téléchargé une seule fois puis mis en cache » `[ASSUMPTION]`. | E-D9 |

### 3.2 Dans `addendum.md`

| N° | Emplacement | Correction proposée | Réf. |
|---|---|---|---|
| A-1 | §A, ligne « API » | Compléter :<br>• pagination par curseur (`limit` à 50 par défaut, maximum 100) ;<br>• `Idempotency-Key` sur les POST sensibles (portée par utilisateur, durée de vie de 24 h `[ASSUMPTION]`) ;<br>• 60 req/min par utilisateur ;<br>• UTC ISO 8601 ;<br>• `{lat, lng}` en WGS84. | §2.2 n° 1-4 |
| A-2 | §C, après S12 | Contrat de `POST /v1/reports` en mode asynchrone :<br>• champs de la requête : `pile_size`, `accuracy_m`, `waste_type`, `client_prediction`, identifiant d'appareil ;<br>• réponse 201 ou 200 avec `classification.status = pending` et la Classification locale reprise. | §2.1, §2.2 n° 5 |
| A-3 | §C, nouvelles lignes | `/v1/ai/classify` non exposé par le proxy. `/metrics` protégé. Délai d'expiration et taille maximale du corps au proxy. Photos sur un domaine distinct. En-têtes `nosniff`, `Referrer-Policy` et CORS. | n° 7, 8, 16, 17, 19 |
| A-4 | §C, nouvelle ligne « Personnel » | Second facteur : OTP plus TOTP, ou Argon2id à défaut. | n° 15 |
| A-5 | §C, nouvelle ligne « Suspension » | Jeton d'accès de 15 min, et vérification de `is_active` à chaque requête (ou liste de révocation dans Redis) pour respecter FR-35. | n° 18 |
| A-6 | §C S10 | Ajouter : « `teranga_app` n'a que INSERT et SELECT sur `audit_logs`. » | n° 13 |
| A-7 | §B, nouveaux points 8 à 12 | Ajouter :<br>• position et précision de la Preuve ;<br>• photos `before` et `after` reliées à la Mission ;<br>• statut de revue de la Preuve ;<br>• correspondance des statuts de Mission ;<br>• conservation explicite de l'index unique partiel ;<br>• suppression de `users.points` ;<br>• règle de la clé d'unicité après anonymisation d'un auteur. | n° 9-14, §2.1 |
| A-8 | §D, point « Prétraitement » | Corriger l'incohérence de la source : un seul prétraitement (Resize 256 + CenterCrop 224, ou redimensionnement direct à 224) appliqué **à l'identique** à l'évaluation, au serveur et au navigateur, avec un test qui compare les sorties. | §2.1, n° 22 |
| A-9 | §D, nouveaux points | Ajouter :<br>• entraînement en deux phases ;<br>• quantification statique INT8 avec 200 images de calibration ;<br>• budget de taille d'environ 6 Mo ;<br>• double annotation de 20 % ;<br>• DVC ;<br>• chaîne de réentraînement (export filtré par modération et consentement, seuil de 25 %, évaluation sur le jeu figé avant publication). | n° 23-26 |
| A-10 | Nouveau **§F Exploitation** | Ajouter :<br>• déploiement (migrations avant démarrage, retour au tag précédent) ;<br>• sauvegardes et restauration ;<br>• observabilité (champs des journaux, `/metrics`, 8 alertes, outil par niveau de déploiement) ;<br>• contenu de `/readyz` ;<br>• plan de sortie en 4 étapes ;<br>• fonds de carte du pilote ;<br>• clés par niveau (fichier d'environnement, KMS, Vault) ;<br>• chiffrement disque et base ;<br>• CI bloquante avec Bandit et Semgrep ;<br>• règle de modularité ;<br>• signaux d'évolution, dont la question de l'isolation par commune. | n° 20, 21, 27-34 |
| A-11 | Nouveau **§G PWA hors-ligne** | Corriger le code de la source :<br>• schéma Dexie complet (FR-17) ;<br>• `flushQueue` toujours appelé avec le jeton courant et l'identifiant d'appareil ;<br>• un 4xx définitif sort le Signalement de la file et affiche le motif (FR-18) ;<br>• remontée de la taille de la file ;<br>• Background Sync avec replis. | n° 35-38 |
| A-12 | §A ou §F | Routes à ajouter au contrat :<br>• carte publique agrégée (FR-34) ;<br>• suivi par un anonyme, selon P-29 ;<br>• revue des Preuves (FR-42) ;<br>• retrait du consentement ;<br>• décision sur `/analytics/timeseries` (dans ou hors périmètre). | n° 6 |

---

## 4. Synthèse des priorités

1. **E-I1 et E-I2 (H)** : pas de Statut de Mission ; le 409 sur transition interdite ne vaut que pour la modération ; aucune idempotence des Preuves, d'où un risque de kg comptés deux fois.
2. **E-S1, E-S3 et E-S7 (H)** : pas de second facteur pour le Personnel, pas de sauvegarde ni de restauration, pas de FR pour l'échantillonnage des Preuves (SM-C3 non mesurable).
3. **E-A1, E-L1 et E-C3 (H)** : ECE ≤ 0,10, seuil de réentraînement de 25 % et filtre modération plus consentement absents du PRD.
4. **E-O1 (H)**, avec E-H1 et E-X1 : aucune alerte exigée ; sondes et plan de sortie sans critère vérifiable.
5. **E-D1 (H)** : UJ-1 promet un suivi anonyme qu'aucune FR ni aucune route ne permet.
6. **Addendum** : aucune contradiction injustifiée. En revanche :
   - le contrat du 201 en mode asynchrone manque ;
   - la position de la Preuve est absente du schéma ;
   - le prétraitement diffère entre l'évaluation et l'inférence ;
   - le code hors-ligne de la source (renvoi sans jeton, échecs 4xx sans fin) est à corriger avant les stories.
