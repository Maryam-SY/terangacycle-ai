---
title: "PRD — TerangaCycle AI"
status: draft
created: 2026-11-23
updated: 2026-11-23
---

# PRD — TerangaCycle AI

## 0. Objet du document

Ce PRD fixe **ce que** TerangaCycle AI doit faire pour la démo du hackathon MakeAfrica (Dakar, 23–28 novembre 2026) et pour le pilote qui suit. Il s'adresse à l'équipe (Mia, Aissatou, Ahmadou) et aux workflows BMAD en aval : spécification UX, architecture, epics et stories.

Il s'appuie sur les sources suivantes, qu'il ne recopie pas :

- `docs/cahier-des-charges.md` : user stories US-01 à US-22 et exigences NF-01 à NF-15 ;
- `docs/dossier-technique.md` : architecture, schéma SQL, API ;
- le Project Proposal (PDF déjà remis au jury) ;
- la maquette Figma de l'équipe (lien partagé hors dépôt), qui fait référence visuelle (7 écrans) ;
- `docs/audit-2026-11-23.md` : incohérences, sécurité, conformité.

Les choix techniques (le « comment ») sont dans `addendum.md`. Le vocabulaire du §3 (Glossaire) est obligatoire. Les inférences non confirmées portent la mention `[ASSUMPTION]` et sont reprises au §12.

## 1. Vision

Un citoyen voit un dépôt sauvage, le prend en photo en moins de 30 secondes, même sans réseau. L'IA embarquée sur son téléphone propose le type de déchet, et un humain confirme. Un collecteur proche reçoit une Mission, se rend sur place et prouve la collecte par des photos avant et après, le poids mesuré et sa position. La commune voit enfin où sont les dépôts, combien de temps ils restent et combien de kilos sont valorisés.

**Thèse.** Le problème n'est pas l'absence de signalement : c'est la **chaîne de confiance** entre le citoyen, le collecteur et la commune. Chaque étape produit une donnée vérifiable : photo, position, classification revue par un humain, preuve géorepérée. Cette chaîne transforme un appel informel en travail traçable. Elle donne aussi aux collecteurs informels un historique crédible de leur travail.

**Souveraine, durable, inclusive.**

- **Souveraine :** le modèle d'IA appartient au projet et tourne sur l'appareil, sans API d'IA étrangère ; les données sont exportables ; l'hébergement est réversible.
- **Durable :** chaque collecte est mesurée en kilos et par matière.
- **Inclusive :** l'application fonctionne hors-ligne sur un Android d'entrée de gamme et intègre les récupérateurs informels comme acteurs de premier rang.

## 2. Utilisateurs cibles

### 2.1 Tâches à accomplir (Jobs To Be Done)

- **Citoyen.** « Quand je vois un dépôt près de chez moi, je veux le signaler sans effort, et savoir que quelqu'un va s'en occuper. » Fonctionnel : moins de 30 s, aucune saisie longue. Émotionnel : ne plus se sentir impuissant.
- **Collecteur.** « Je veux savoir où se trouve la matière près de moi, ce qu'elle contient, et pouvoir prouver mon travail pour être reconnu et payé. »
- **Modérateur.** « Je veux écarter le spam et les erreurs de l'IA vite, sans laisser passer un dépôt réel. »
- **Administrateur commune.** « Je veux savoir où agir en priorité et rendre compte avec des chiffres vérifiables. »
- **Recycleur** (extension). « Je veux anticiper les volumes de matière par type et par zone. »

### 2.2 Non-utilisateurs (v1)

- Les entreprises de collecte qui ont besoin d'optimiser des tournées multi-véhicules.
- Les personnes sans smartphone : leur canal (SMS, WhatsApp) est une extension.
- Le grand public qui consulterait des positions précises de dépôts : la carte publique est agrégée (FR-34).

### 2.3 Parcours utilisateurs clés

> Les personnages sont illustratifs. Les numéros d'écran renvoient à la maquette Figma (1 · Accueil … 7 · Tableau de bord).

- **UJ-1. Awa signale un dépôt de plastique près du marché, sans réseau.**
  - **Persona et contexte :** Awa, 34 ans, commerçante, Android d'entrée de gamme, forfait de données souvent épuisé.
  - **Point de départ :** application installée (PWA), sans compte ; signalement anonyme.
  - **Déroulé :** écran 1, appui sur « Signaler un dépôt » → écran 2, photo et position détectée (précision en mètres) → écran 3, l'IA propose « Plastique, 87 % » ; Awa choisit la Taille de tas « moyen » et envoie.
  - **Moment clé :** écran 4, un accusé de réception « en attente d'envoi » s'affiche immédiatement, avec la frise des 4 états.
  - **Résolution :** au retour du réseau, le Signalement part tout seul et reçoit son Numéro de suivi (par exemple TC-2026-004217). Awa voit plus tard « Validé », puis « Collecté ».
  - **Cas limite :** si la confiance est sous 60 %, l'écran 3 n'affiche aucun type présélectionné et Awa doit en toucher un.

- **UJ-2. Fatou, modératrice à la commune, trie la file du matin.**
  - **Point de départ :** connectée sur navigateur avec le rôle Modérateur.
  - **Déroulé :** File de modération triée par ancienneté → photo, position, Classification serveur, et un drapeau « désaccord IA » quand la Classification locale différait.
  - **Moment clé :** elle valide un Signalement en un clic, ou le rejette avec un motif obligatoire.
  - **Résolution :** le Signalement validé devient visible des collecteurs ; l'action est inscrite au Journal d'audit.

- **UJ-3. Ibrahima, collecteur d'un GIE de pré-collecte, prend et prouve une Mission.**
  - **Point de départ :** connecté par OTP, compte Collecteur vérifié.
  - **Déroulé :** écran 5, missions dans un rayon de 5 km avec type, distance, Poids estimé et confiance → « Accepter la mission » → itinéraire dans l'application de cartes du téléphone.
  - **Arrivée :** sur place, écran 6, photo avant, collecte, photo après, Poids mesuré de 15 kg.
  - **Moment clé :** l'application confirme « vous êtes à moins de 150 m du dépôt » et la collecte est validée.
  - **Résolution :** la Mission entre dans son historique ; le Signalement passe à « Collecté ».
  - **Cas limite :** un autre collecteur a accepté la Mission une seconde avant lui ; Ibrahima voit « Mission déjà prise » et la liste se rafraîchit.

- **UJ-4. M. Ndiaye, chef du service propreté, prépare le point mensuel.**
  - **Point de départ :** connecté sur ordinateur avec le rôle Administrateur commune.
  - **Déroulé :** écran 7 avec 4 indicateurs (Signalements du mois, délai médian, taux de traitement, kg valorisés) → Carte de chaleur filtrée sur le dernier mois → répartition par type.
  - **Moment clé :** l'Export agrégé en CSV part dans son rapport, sans aucune donnée personnelle.
  - **Résolution :** il identifie deux zones prioritaires pour la prochaine tournée.

- **UJ-5. Awa supprime son compte.**
  - Depuis son profil, Awa demande la suppression de son compte. Son numéro est effacé ; ses Signalements restent dans les statistiques sous forme anonymisée.

## 3. Glossaire

- **Citoyen** : personne qui crée un Signalement, connectée ou anonyme.
- **Collecteur** : personne ou structure (GIE, récupérateur informel) qui exécute des Missions. Un **Collecteur vérifié** a été validé par un Administrateur commune ; seul lui peut accepter une Mission.
- **Recycleur** : acteur qui consulte et réserve des Lots de matière (extension).
- **Modérateur** : personnel qui valide ou rejette les Signalements.
- **Administrateur commune** : personnel qui pilote le Tableau de bord, gère les comptes et exporte les données.
- **Personnel** : Modérateur ou Administrateur commune.
- **Signalement** : déclaration d'un dépôt de déchets, avec une photo, une Position, une Taille de tas, un Type de déchet et un commentaire optionnel. Il a un et un seul Statut.
- **Statut** : état d'un Signalement : `en attente de modération` → `validé` ou `rejeté` ; `validé` → `assigné` ; `assigné` → `collecté`, ou retour à `validé` si la Mission est annulée. `rejeté` et `collecté` sont terminaux.
- **Numéro de suivi** : identifiant lisible d'un Signalement au format `TC-AAAA-NNNNNN`, attribué par le serveur.
- **Identifiant client** : UUID généré sur l'appareil à la création d'un Signalement, qui permet un renvoi sans doublon.
- **Position** : coordonnées GPS et précision en mètres, capturées à la création du Signalement ou de la Preuve de collecte.
- **Type de déchet** : une des 5 classes : plastique, métal, verre, organique, mixte.
- **Classification locale** : prédiction du Modèle exécuté sur l'appareil.
- **Classification serveur** : prédiction du même Modèle sur le serveur, sur la même photo ; c'est elle qui fait foi.
- **Seuil de confiance** : 60 %. En dessous, le Citoyen doit choisir le Type de déchet lui-même.
- **Correction** : Type de déchet choisi par un humain qui diffère de la prédiction ; c'est un exemple étiqueté pour le réentraînement.
- **Désaccord IA** : la Classification locale et la Classification serveur donnent des types différents.
- **Modèle** : classifieur d'images versionné, unique, exécuté sur l'appareil et sur le serveur.
- **Taille de tas** : petit, moyen ou grand ; choisie par le Citoyen.
- **Poids estimé** : poids déduit de la Taille de tas et du Type de déchet par une table de conversion.
- **Poids mesuré** : poids saisi par le Collecteur dans la Preuve de collecte.
- **File hors-ligne** : stockage local des Signalements non encore envoyés.
- **Mission** : prise en charge d'un Signalement `validé` par un Collecteur vérifié. Au plus une Mission active par Signalement.
- **Preuve de collecte** : photo avant, photo après, Poids mesuré et Position du Collecteur, horodatés par le serveur.
- **Zone** : découpage administratif (commune, quartier).
- **File de modération** : liste des Signalements `en attente de modération`.
- **Tableau de bord** : vue de l'Administrateur commune (indicateurs, Carte de chaleur, répartition par type).
- **Carte de chaleur** : densité des Signalements, agrégée par cellule de grille ou par Zone.
- **Export agrégé** : fichier CSV ou GeoJSON sans donnée personnelle, avec des positions arrondies.
- **Journal d'audit** : trace horodatée et non modifiable des actions sensibles.
- **Lot de matière** : quantité de matière déclarée par un Collecteur pour les Recycleurs (extension).
- **Données de démonstration** : données fictives, toujours étiquetées comme telles à l'écran.
- **Mode démonstration** : configuration du hackathon où le code OTP s'affiche à l'écran ; interdit en production.

## 4. Fonctionnalités

### 4.1 Accès, identité et consentement

**Description.** On peut signaler sans compte, pour garder le parcours sous 30 s. Les autres rôles se connectent par numéro de téléphone et code à usage unique (OTP) ; il n'y a pas de mot de passe citoyen. Les droits dépendent du rôle et, pour chaque objet, de la propriété. Réalise UJ-1, UJ-3, UJ-5.

#### FR-1 : Connexion par OTP

Un utilisateur peut se connecter avec son numéro de téléphone et un code OTP reçu par SMS.

**Conséquences (testables) :**
- Le code expire après 5 min et n'est valable qu'une fois ; il est invalidé après 5 essais erronés.
- 5 demandes au plus par heure et par numéro, avec une limite par IP et par appareil ; au-delà, réponse 429.
- Un plafond quotidien de coût SMS coupe l'envoi et alerte l'équipe.
- Seuls les numéros sénégalais sont acceptés `[ASSUMPTION : liste de préfixes +221 pour le MVP]`.

#### FR-2 : Session

Un utilisateur connecté garde sa session sans ressaisir de code pendant 30 jours d'activité, et peut se déconnecter.

**Conséquences :**
- Une session volée et révoquée ne peut plus servir.
- La réutilisation d'un jeton de renouvellement déjà utilisé révoque toute la session.
- La déconnexion invalide la session côté serveur.

#### FR-3 : Rôles et contrôle d'accès

Le système applique les rôles Citoyen, Collecteur, Recycleur, Modérateur et Administrateur commune sur chaque action. Il vérifie aussi la propriété de chaque objet : un Citoyen ne voit que ses propres Signalements.

**Conséquences :**
- Un test automatisé appelle chaque route sensible avec chaque rôle et sans jeton ; tout accès non prévu échoue (401 ou 403).
- Un Collecteur ne voit jamais l'auteur d'un Signalement.

#### FR-4 : Consentement

Avant la première capture, le Citoyen voit une information claire qui couvre :
- la géolocalisation ;
- l'envoi de la photo ;
- l'usage des photos et des Corrections pour améliorer le Modèle ;
- la consigne de ne photographier ni personne ni plaque.

**Conséquences :**
- Rien n'est envoyé sans acceptation.
- L'acceptation est horodatée pour un compte, et mémorisée sur l'appareil pour un anonyme.
- Le Citoyen peut refuser l'usage pour le réentraînement sans perdre l'accès au signalement `[ASSUMPTION]`.

#### FR-5 : Gestion de ses données

Un utilisateur connecté peut consulter son profil, changer sa langue et son nom affiché, et supprimer son compte. Réalise UJ-5.

**Conséquences :**
- La suppression efface le numéro et désactive le compte immédiatement ; la purge complète a lieu sous 30 jours.
- Les Signalements de l'utilisateur sont conservés avec un auteur anonymisé.

#### FR-6 : Mode démonstration

Le Mode démonstration affiche le code OTP à l'écran, pour une démo sans passerelle SMS.

**Conséquences :**
- Le service refuse de démarrer si le Mode démonstration est actif en configuration de production.
- Un bandeau « Mode démonstration » est visible sur tous les écrans tant qu'il est actif.

### 4.2 Signalement citoyen

**Description.** C'est le cœur du parcours de 30 s (écrans 1 → 4). Réalise UJ-1.

#### FR-7 : Créer un Signalement

Un Citoyen, connecté ou anonyme, crée un Signalement avec :
- une photo, obligatoire ;
- une Position capturée automatiquement, avec sa précision ;
- une Taille de tas ;
- un commentaire optionnel de 280 caractères au plus.

**Conséquences :**
- Sans photo ou sans Position, l'envoi est impossible.
- Une Position hors du Sénégal est refusée.
- Le serveur attribue le Numéro de suivi et le Statut `en attente de modération`.
- La Zone est déterminée automatiquement à partir de la Position.

#### FR-8 : Photo légère et sans métadonnées

Avant envoi, la photo est compressée sur l'appareil à 300 Ko au plus. Le serveur la revalide, la ré-encode et supprime toutes ses métadonnées (EXIF, GPS).

**Conséquences :**
- Une image corrompue, ou de plus de 12 mégapixels ou 1 Mo, est refusée (413 ou 422).
- La photo stockée ne contient aucune métadonnée EXIF.
- Une photo strictement identique à une photo déjà reçue est signalée en doublon à la modération.

#### FR-9 : Renvoi sans doublon et sans fuite

Chaque Signalement porte un Identifiant client. Un renvoi du même Signalement par le même auteur ou le même appareil renvoie le Signalement existant, sans en créer un second.

**Conséquences :**
- 10 renvois identiques produisent un seul Signalement.
- Un autre utilisateur qui présente le même Identifiant client ne reçoit **aucune** donnée du Signalement existant (409).

#### FR-10 : Limite anti-abus

Un Citoyen anonyme peut créer au plus 10 Signalements par heure et par appareil ou IP ; au-delà, réponse 429.

### 4.3 Classification IA

**Description.** L'IA propose, l'humain confirme. Le Modèle tourne d'abord sur l'appareil, pour un retour immédiat et hors-ligne, puis sur le serveur, dont le résultat fait foi. Réalise UJ-1, UJ-2.

#### FR-11 : Classification locale

Après la capture, le Modèle affiche un Type de déchet et un score de confiance.

**Conséquences :**
- Le résultat s'affiche en moins de 3 s sur un Android à 2 Go de RAM (NF-01), sans réseau une fois le Modèle en cache.
- Chaque Type de déchet a un pictogramme et une couleur.

#### FR-12 : Seuil de confiance

Sous le Seuil de confiance (60 %), aucun type n'est présélectionné et le Citoyen doit en choisir un parmi les 5.

#### FR-13 : Correction

Le Citoyen, et plus tard le Modérateur, peut corriger le Type de déchet en un toucher.

**Conséquences :**
- Chaque Correction est enregistrée avec la prédiction d'origine, la version du Modèle et son auteur.
- Les Corrections sont exportables comme jeu d'exemples étiquetés.

#### FR-14 : Classification serveur

Le serveur reclasse la même photo avec la même version du Modèle. Sa prédiction et la Classification locale sont toutes deux conservées.

**Conséquences :**
- Le Type de déchet retenu est, dans l'ordre : la Correction humaine, sinon la Classification serveur.
- La Classification serveur ne bloque pas la réponse de création : elle peut arriver après (`[ASSUMPTION]`, traitement en tâche de fond).

#### FR-15 : Désaccord IA

Un Désaccord IA est mis en évidence dans la File de modération.

#### FR-16 : Version du Modèle

Chaque classification enregistre la version du Modèle. Le Modèle peut être remplacé (d'un modèle factice au modèle entraîné) sans changer les écrans ni l'API.

### 4.4 File hors-ligne

**Description.** Le réseau est instable : aucun Signalement ne doit être perdu. Réalise UJ-1.

#### FR-17 : Mise en file

Sans réseau, un Signalement complet (photo, Position, type, Taille de tas, commentaire) est enregistré dans la File hors-ligne, et l'écran 4 affiche « en attente d'envoi ».

**Conséquences :**
- En mode avion, 100 % des champs saisis sont conservés, même si l'application est fermée puis rouverte (NF-06).

#### FR-18 : Synchronisation

Au retour du réseau, ou à l'ouverture de l'application, la File hors-ligne s'envoie automatiquement.

**Conséquences :**
- Aucun doublon n'est créé (FR-9).
- En cas d'erreur temporaire (429 ou 5xx), le Signalement reste en file et repart plus tard.
- En cas de refus définitif, le Citoyen voit le motif.

#### FR-19 : Visibilité de la file

Le Citoyen voit le nombre de Signalements en attente et peut relancer l'envoi manuellement.

### 4.5 Suivi et notifications

#### FR-20 : Suivi de ses Signalements

Un Citoyen voit la liste de ses Signalements, avec le Numéro de suivi, le Statut et la frise des 4 états (écrans 1 et 4). Réalise UJ-1.

**Conséquences :**
- Le Statut affiché se met à jour au plus 15 s après le changement, quand l'application est ouverte.
- Un Signalement `rejeté` affiche son motif.

#### FR-21 : Notification de changement

Le Citoyen connecté est notifié dans l'application à chaque changement de Statut, et par notification push s'il l'a autorisée.

**Hors périmètre :** notifications par SMS ou WhatsApp `[NON-GOAL pour le MVP]`.

### 4.6 Modération

#### FR-22 : File de modération

Un Modérateur voit les Signalements `en attente de modération`, les plus anciens d'abord, avec :
- la photo ;
- la Position ;
- la Classification serveur ;
- les drapeaux Désaccord IA et doublon.

Réalise UJ-2.

#### FR-23 : Valider ou rejeter

Le Modérateur valide un Signalement ou le rejette avec un motif obligatoire.

**Conséquences :**
- Toute transition non prévue par le Statut renvoie 409.
- Chaque décision est inscrite au Journal d'audit.
- Un Signalement n'est visible des Collecteurs qu'une fois `validé` : les photos sont donc vues par un humain avant d'être exposées.

### 4.7 Missions

#### FR-24 : Missions proches

Un Collecteur vérifié voit les Signalements `validé` dans un rayon réglable de 1 à 10 km (5 km par défaut), triés par distance, sur une carte et en liste. Chaque élément affiche le type, la distance, le Poids estimé, la confiance et la photo. Réalise UJ-3.

**Conséquences :**
- Aucune information sur l'auteur du Signalement n'est visible.

#### FR-25 : Accepter une Mission

Un Collecteur vérifié accepte une Mission, et le Signalement passe à `assigné`.

**Conséquences :**
- Si deux Collecteurs acceptent en même temps, un seul réussit ; l'autre reçoit « Mission déjà prise » (409).
- Un Collecteur non vérifié ne peut pas accepter de Mission.

#### FR-26 : Annuler une Mission

Le Collecteur peut annuler sa Mission ; le Signalement revient alors à `validé`.

#### FR-27 : Itinéraire

Depuis une Mission, le Collecteur ouvre l'application de cartes de son téléphone sur la Position du Signalement. *(Should)*

#### FR-28 : Assignation manuelle

Un Administrateur commune peut assigner un Signalement `validé` à un Collecteur vérifié, qui en est notifié. *(Should)*

### 4.8 Preuve de collecte

#### FR-29 : Prouver une collecte

Le Collecteur de la Mission soumet une Preuve de collecte. Réalise UJ-3.

**Conséquences :**
- Sans photo avant, photo après et Poids mesuré supérieur à 0, la Preuve est refusée.
- Une Position du Collecteur à plus de 150 m de la Position du Signalement est refusée, avec un message clair.
- Une Preuve acceptée passe la Mission à « terminée » et le Signalement à `collecté`.
- L'horodatage est celui du serveur.

#### FR-30 : Historique du Collecteur

Le Collecteur voit l'historique de ses Missions, en cours et terminées, avec les kg collectés.

### 4.9 Tableau de bord commune

#### FR-31 : Indicateurs

L'Administrateur commune voit 4 indicateurs sur une période choisie. Réalise UJ-4.

| Indicateur | Définition |
|---|---|
| Nombre de Signalements | Total sur la période, dont `validé` |
| Délai médian | Médiane entre la création et le passage à `collecté` |
| Taux de traitement | Part des Signalements `validé` qui sont `collecté` |
| Kg valorisés | Somme des Poids mesurés des Preuves acceptées |

Il voit aussi la répartition par Type de déchet.

#### FR-32 : Carte de chaleur

L'Administrateur commune voit la Carte de chaleur, filtrable par période, Type de déchet et Statut.

**Conséquences :**
- L'affichage prend moins de 2 s pour 5 000 Signalements (NF-03).

#### FR-33 : Export agrégé

L'Administrateur commune télécharge un Export agrégé en CSV et en GeoJSON.

**Conséquences :**
- Le fichier ne contient aucun numéro, nom ni identifiant d'auteur.
- Les positions y sont arrondies `[ASSUMPTION : à 3 décimales, environ 110 m]`.

#### FR-34 : Carte publique agrégée

Tout visiteur voit une carte des Signalements agrégée par cellule ou par Zone, jamais de point précis. *(Should)*

### 4.10 Administration des comptes

#### FR-35 : Gérer les Collecteurs

Un Administrateur commune crée, vérifie et suspend un compte Collecteur, et change le rôle d'un utilisateur.

**Conséquences :**
- Chaque action est inscrite au Journal d'audit.
- Un compte suspendu perd l'accès immédiatement.

#### FR-36 : Consulter le Journal d'audit

Un Administrateur commune consulte le Journal d'audit, filtrable par action et par période.

### 4.11 Données de démonstration

#### FR-37 : Jeu de démonstration étiqueté

Un jeu de Données de démonstration peut être chargé : Zones de Dakar, comptes de test pour chaque rôle, Signalements à divers Statuts.

**Conséquences :**
- Tout écran qui affiche des Données de démonstration porte l'étiquette « Données de démonstration ».
- Le jeu de démonstration se retire en une commande.

### 4.12 Lots de matière (extension, après la porte H48)

#### FR-38 : Déclarer un Lot de matière

Un Collecteur déclare un Lot de matière (type, poids, Zone, photo). *(Should)*

#### FR-39 : Consulter les Lots

Un Recycleur consulte les Lots de matière disponibles, filtrés par type, Zone et poids minimal ; le contact du Collecteur n'est donné qu'après une demande. *(Should)*

#### FR-40 : Réserver un Lot

Un Recycleur demande la réservation d'un Lot ; le Lot passe à « réservé » et le Collecteur est notifié. *(Could)*

## 5. Exigences non fonctionnelles transverses

| ID | Domaine | Exigence | Seuil | Vérification |
|---|---|---|---|---|
| NFR-1 | Performance | Classification locale | < 3 s sur un Android 2 Go | Chronométrage sur 20 photos |
| NFR-2 | Performance | Lecture API | p95 < 300 ms à 50 req/s | k6 |
| NFR-3 | Performance | Carte | < 2 s pour 5 000 points | Mesure manuelle et Lighthouse |
| NFR-4 | Réseau faible | Photo envoyée | ≤ 300 Ko | Test automatique |
| NFR-5 | Réseau faible | Page d'accueil | ≤ 500 Ko hors images et Modèle | Lighthouse |
| NFR-6 | Compatibilité | Appareils | Android 8+ avec Chrome, 2 Go de RAM ; mobile 390×844, tableau de bord 1280×800 | Test sur un appareil réel |
| NFR-7 | Disponibilité | Démo | Service et portable de secours prêts ; sondes de vie et de disponibilité | Répétition |
| NFR-8 | Sécurité | Transport | TLS 1.2 minimum, HSTS | Scan SSL |
| NFR-9 | Sécurité | Contrôle d'accès | 100 % des routes sensibles testées × chaque rôle | CI |
| NFR-10 | Sécurité | Chaîne logicielle | Aucun secret dans Git ; dépendances et image auditées ; versions épinglées | Gitleaks, pip-audit, npm audit, Trivy en CI |
| NFR-11 | Qualité | Code | Couverture backend ≥ 60 %, lint sans erreur | CI |
| NFR-12 | Accessibilité | WCAG 2.1 AA | Contraste ≥ 4,5:1 pour le texte, cibles tactiles ≥ 44 px, libellés pour lecteurs d'écran | Audit Lighthouse et calcul des contrastes |
| NFR-13 | Langue | Interface | Français d'abord ; aucune chaîne en dur (wolof prêt à ajouter) | Revue de code |
| NFR-14 | Observabilité | Journaux | Journaux structurés avec un identifiant de requête ; jamais de jeton ni de numéro complet | Revue des journaux |

## 6. Confidentialité, sécurité et conformité

### 6.1 Données personnelles (minimisation)

**Données collectées :**
- un numéro de téléphone, seulement pour les comptes ;
- la Position du Signalement ;
- la photo ;
- l'IP, dans le Journal d'audit et pour la limitation de débit.

**Protection :**
- le numéro est chiffré au repos, et la recherche passe par une empreinte calculée avec une clé secrète ;
- les photos sont privées et ne sont servies que par des liens temporaires de 5 minutes ;
- les positions précises sont réservées au Personnel et au Collecteur de la Mission.

| Donnée | Durée de conservation `[ASSUMPTION : à valider avec la commune]` |
|---|---|
| Photos de Signalement | 12 mois |
| IP du Journal d'audit | 6 mois |
| Compte supprimé | Purgé sous 30 jours |
| Statistiques agrégées | Sans limite |

### 6.2 Abus et fraude

| Menace | Contrôle exigé |
|---|---|
| Spam | FR-10, File de modération, détection de doublons |
| Fausses preuves | FR-29 (150 m, horodatage serveur, photos), vérification par échantillon du Personnel |
| Fraude aux SMS | FR-1 (limites et plafond de coût) |
| Fichier piégé | FR-8 |
| Accès indus | FR-3 |
| Fuite par renvoi | FR-9 |
| Mode démonstration oublié en production | FR-6 |

### 6.3 Conformité

- **Loi sénégalaise n° 2008-12 sur les données personnelles et CDP :**
  - aucune obligation pour la démo, qui n'utilise que des Données de démonstration ;
  - pour le pilote, déclaration ou demande d'autorisation à la CDP avant la collecte de données réelles ;
  - tout hébergement hors du Sénégal (pilote AWS) est un transfert à couvrir dans ce dossier.
- **WCAG 2.1 AA :** NFR-12. Le jeton Vert de la maquette (`#1F8A5B`) échoue en texte blanc (4,33:1) ; il est remplacé par `#187A50` (5,33:1) `[ASSUMPTION : validation de Mia]`.
- **Licence ouverte du code** : MIT ou AGPL-3.0, à choisir avant le pilote (voir §11).
- **Licences des jeux de données d'entraînement** (TrashNet, TACO) : listées dans la fiche du Modèle.

### 6.4 Souveraineté

- Aucune API d'IA hébergée : le Modèle appartient au projet.
- Données exportables en formats ouverts.
- Déploiement par conteneurs, portable d'un hébergeur à l'autre.
- Plan de sortie documenté vers un hébergement au Sénégal.

## 7. Plateforme et identité visuelle

- **PWA installable** (pas d'application native), mobile d'abord ; tableau de bord sur ordinateur.
- **Référence visuelle :** maquette Figma (écrans 1 à 7), police Inter, jetons de couleur du brief, sauf le vert corrigé (§6.3).
- **Ton :** consignes courtes, en français simple, avec pictogrammes ; des messages d'erreur qui disent quoi faire.
- **Honnêteté :** aucun chiffre de démonstration n'est présenté comme réel, et aucun objectif comme un résultat.

## 8. Non-objectifs

- Paiement mobile réel des Collecteurs.
- Applications natives iOS et Android.
- Entraînement d'un modèle à partir de zéro, ou détection d'objets multiples.
- Optimisation de tournées multi-véhicules.
- Estimation du poids par IA : la table de Taille de tas suffit et reste corrigeable.
- Temps réel par WebSocket : rafraîchissement toutes les 15 s.
- Points citoyens et classements par quartier.
- Interface wolof complète (seule la préparation à la traduction est exigée).

## 9. Périmètre du MVP

### 9.1 Dans le périmètre (démo du hackathon)

Les exigences sont livrées par porte du plan de 72 h.

| Porte | Exigences livrées | État visé |
|---|---|---|
| **H24** | FR-1 à FR-4, FR-6, FR-7 à FR-10, FR-16 (avec un Modèle factice), FR-37 | Signalement relié à la PWA |
| **H48** | FR-11 à FR-15, FR-22 à FR-26, FR-29 | Boucle signaler → modérer → collecter de bout en bout |
| **H60** | FR-5, FR-17 à FR-21, FR-31 à FR-33, FR-35 | Gel des fonctionnalités |

### 9.2 Hors périmètre du MVP

- **FR-27, FR-28, FR-30, FR-34, FR-36 :** seulement si la porte H48 est atteinte en avance.
- **FR-38 à FR-40 (Lots de matière) :** extension.
  `[NOTE FOR PM]` La valorisation est au cœur du discours (« le cœur n'est pas le signalement »), mais elle est hors démo. Il faut assumer clairement ce décalage devant le jury : la démo prouve la chaîne de confiance, et la place de marché vient avec le pilote.
- **Wolof, SMS, WhatsApp :** feuille de route du pilote.

## 10. Indicateurs de réussite

Ce sont des **objectifs à mesurer**, pas des résultats.

**Principaux (hackathon)**
- **SM-1** : boucle complète démontrée en direct, sur des photos réelles : signalement hors-ligne → modération → Mission → Preuve de collecte → Tableau de bord. Valide FR-7, FR-17, FR-23, FR-25, FR-29, FR-31.
- **SM-2** : qualité du Modèle sur un jeu de test local conservé.
  - Seuils : F1 macro ≥ 0,80 et rappel ≥ 0,70 par classe ; la top-1 accuracy est publiée en complément, avec la matrice de confusion.
  - Valide FR-11 et FR-14.
  - `[ASSUMPTION : le Proposal annonce « top-1 accuracy ≥ 80 % » ; le F1 macro est retenu comme métrique principale]`.
- **SM-3** : création d'un Signalement en moins de 30 s, chronométrée. Valide FR-7, FR-11 et FR-12.
- **SM-4** : 100 % des Signalements créés en mode avion arrivent après la reconnexion, sans doublon. Valide FR-17, FR-18 et FR-9.

**Pilote de 6 mois dans une commune**
- **SM-5** : délai médian entre Signalement et collecte de moins de 24 h. Valide FR-24 à FR-29.
- **SM-6** : au moins 60 % des Signalements `validé` passent à `collecté`. Valide FR-25 et FR-29.
- **SM-7** : au moins 20 Collecteurs vérifiés actifs avec un historique. Valide FR-30 et FR-35.
- **SM-8** : la part des classifications corrigées baisse de mois en mois. Valide FR-13 et FR-16.

**Contre-indicateurs (à ne pas optimiser)**
- **SM-C1** : nombre brut de Signalements. Le faire monter récompense le spam ; il équilibre SM-1 et SM-6.
- **SM-C2** : taux de validation en modération. Un taux proche de 100 % signale une modération de complaisance ; il équilibre SM-6.
- **SM-C3** : kg valorisés par Mission. Des poids gonflés feraient monter l'indicateur ; on suit plutôt la part de Preuves contestées lors de l'échantillonnage. Il équilibre SM-5 et SM-6.
- **SM-C4** : part de classifications acceptées sans Correction. Décourager la Correction masquerait les erreurs du Modèle ; il équilibre SM-8.

## 11. Questions ouvertes

1. **MobileNetV3-Large ou Small ?** Tranché par la mesure de latence sur un Android 2 Go à H24. Responsable : Aissatou.
2. **Licence du code :** MIT (adoption) ou AGPL-3.0 (commun numérique) ? Responsable : Mia, avant le pilote.
3. **Passerelle SMS au Sénégal :** couverture et coût à comparer ; le Mode démonstration couvre le hackathon.
4. **Région d'hébergement du pilote :** Le Cap, Paris ou hébergeur sénégalais. Mesure de latence depuis Dakar et dossier CDP.
5. **Âge minimum** pour créer un compte, et texte de consentement à faire relire par un juriste.
6. **Table de conversion Taille de tas → Poids estimé :** valeurs par type à obtenir d'un collecteur.
7. **Inscription au hackathon** et équipe de trois : confirmation à obtenir des organisateurs. Partage Figma en « lecture pour tous ».

## 12. Index des hypothèses

- §4.1 FR-1 : seuls les numéros sénégalais (+221) sont acceptés au MVP.
- §4.1 FR-4 : on peut refuser l'usage pour le réentraînement et continuer à signaler.
- §4.3 FR-14 : la Classification serveur est asynchrone.
- §4.9 FR-33 : arrondi des positions à 3 décimales dans les Exports agrégés.
- §6.1 : durées de conservation à valider avec la commune.
- §6.3 et §7 : jeton Vert corrigé en `#187A50`.
- §10 SM-2 : F1 macro retenu comme métrique principale.
- Décisions par défaut prises en chemin rapide (voir `.memlog.md`) :
  - MobileNetV3-Large par défaut ;
  - rayon de 5 km réglable de 1 à 10 km ;
  - objectif du pilote : 60 % sur 6 mois ;
  - pitch de 1 min 30 ;
  - déploiement final sur Docker Compose plutôt qu'AWS.
