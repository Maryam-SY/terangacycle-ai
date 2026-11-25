---
title: "PRD — TerangaCycle"
version: 2.0
status: final
created: 2026-11-23
updated: 2026-11-25
---

# PRD — TerangaCycle

## 0. Objet du document

Ce PRD fixe **ce que** TerangaCycle doit faire : d'abord la démo du hackathon MakeAfrica (Dakar, 23–28 novembre 2026), puis un MVP opérationnel et un MVP commercial sur un premier territoire, enfin la place de marché de la matière (lots P0 à P4, §9). Il s'adresse à l'équipe et aux workflows BMAD en aval : spécification UX, architecture, epics et stories.

**Version 2.0 (25/11/2026).** Le produit devient une infrastructure de traçabilité de l'économie circulaire (§1). Le changement est décrit dans `_bmad-output/planning-artifacts/sprint-change-proposal-2026-11-25.md`.

**Confidentialité.** Ce dépôt est public. Les prix des offres, les frais de coordination, la rémunération et la commission sont des **paramètres configurables par contrat**, sans valeur chiffrée dans ce document : « valeurs commerciales hors dépôt ». Aucun nom de personne ni coordonnée n'y figure ; les responsables sont désignés par leur rôle (responsable produit, responsable technique, responsable IA).

Il s'appuie sur les sources suivantes, qu'il ne recopie pas :

- `docs/cahier-des-charges.md` : user stories US-01 à US-22 et exigences NF-01 à NF-15 ;
- `docs/dossier-technique.md` : architecture, schéma SQL, API ;
- le Project Proposal (PDF déjà remis au jury) ;
- le handoff brief de l'équipe (PDF, hors dépôt) ;
- la maquette Figma de l'équipe (lien partagé hors dépôt), qui fait référence visuelle (7 écrans) ;
- `docs/audit-2026-11-23.md` : incohérences, sécurité, conformité ;
- les décisions de l'équipe, journalisées dans `.memlog.md`.

Les choix techniques (le « comment ») sont dans `addendum.md`. Le vocabulaire du §3 (Glossaire) est obligatoire. Les décisions validées par la responsable produit et les décisions par défaut sont journalisées dans `.memlog.md` ; les décisions par défaut restent révisables par la responsable produit. Les inférences non confirmées portent la mention `[ASSUMPTION]` et sont reprises au §12.

## 1. Vision

TerangaCycle est une **infrastructure de traçabilité de l'économie circulaire au Sénégal**. Elle relie ceux qui voient ou produisent des déchets (citoyens, entreprises), ceux qui les collectent (collecteurs et récupérateurs vérifiés), ceux qui en ont la charge (communes, opérateurs) et ceux qui les valorisent (recycleurs). Chaque kilo collecté est prouvé, contrôlé et traçable jusqu'à sa vente.

**Boucle prouvée du MVP.** Un Signalement citoyen ou une Demande de collecte d'entreprise devient une Mission ; la Mission produit une Preuve de collecte ; la Preuve contrôlée produit des kg vérifiés. Le signalement et la mise en relation pour la collecte sont des fonctions de cette infrastructure. On commence par un territoire et cette seule boucle.

Le parcours d'origine reste le premier cas d'usage : un citoyen voit un dépôt sauvage et le prend en photo en moins de 30 secondes, même sans réseau. L'IA embarquée sur son téléphone propose le Type de déchet, et un humain confirme. Un collecteur proche reçoit une Mission, se rend sur place et prouve la collecte (photos avant et après, Poids déclaré, position). La commune voit enfin où sont les dépôts, combien de temps ils restent et combien de kilos sont collectés, par matière.

**Thèse.** Le problème n'est pas l'absence de signalement : c'est la **chaîne de confiance** entre ceux qui produisent, collectent, financent et valorisent. Chaque étape produit une donnée vérifiable : photo, position, classification revue par un humain, preuve géorepérée, contrôle par échantillon. Cette chaîne transforme un appel informel en travail traçable. Elle donne aux collecteurs informels un historique crédible et des rémunérations enregistrées, et aux recycleurs une matière d'origine prouvée.

**Principes.**

- **Souveraine :** le modèle d'IA appartient au projet et tourne sur l'appareil, sans API d'IA étrangère ; les données sont exportables ; l'hébergement est réversible.
- **Durable :** chaque collecte est comptée en kilos, par Type de déchet, et chaque kg vendu remonte à une Preuve de collecte.
- **Inclusive :** l'application fonctionne hors-ligne sur un Android d'entrée de gamme et guide par pictogrammes ; elle intègre les récupérateurs informels comme acteurs de premier rang, rémunérés pour les collectes validées et vendeurs de la matière qu'ils ont prouvée ; le wolof suit pendant le pilote.
- **Neutre financièrement :** TerangaCycle ne détient aucun fonds. Il enregistre ce qui est dû, payé ou contesté ; le client paie lui-même le collecteur.
- **Cloisonnée :** chaque organisation cliente ne voit que ses données, dès le premier jour.

## 2. Utilisateurs cibles

### 2.1 Tâches à accomplir (Jobs To Be Done)

- **Citoyen.** « Quand je vois un dépôt près de chez moi, je veux le signaler sans effort, et savoir que quelqu'un va s'en occuper. » Fonctionnel : moins de 30 s, aucune saisie longue. Émotionnel : ne plus se sentir impuissant.
- **Collecteur.** « Je veux savoir où se trouve la matière près de moi, ce qu'elle contient, et pouvoir prouver mon travail pour être reconnu et payé. »
- **Modérateur.** « Je veux écarter le spam et les erreurs de l'IA vite, sans laisser passer un dépôt réel. »
- **Administrateur d'organisation** (commune ou opérateur). « Je veux savoir où agir en priorité, gérer mes collecteurs et rendre compte avec des chiffres vérifiables. »
- **Gestionnaire d'entreprise** (hôtel, restaurant, marché, supermarché). « Je veux faire collecter mes déchets quand il le faut, et prouver chaque mois ce qui a été collecté et où c'est allé. »
- **Recycleur.** « Je veux acheter une matière dont l'origine est prouvée, par type, quantité et zone. »
- **Super Admin** (équipe TerangaCycle). « Je veux ouvrir et suivre les organisations clientes, leurs contrats, la vérification des acteurs, les litiges et la santé de la plateforme. »

### 2.2 Non-utilisateurs (v1)

- Les entreprises de collecte qui ont besoin d'optimiser des tournées multi-véhicules.
- Les personnes sans smartphone : leur canal (SMS, WhatsApp) est une extension.
- Le grand public qui consulterait des positions précises de dépôts : la carte publique est agrégée (FR-34).

### 2.3 Parcours utilisateurs clés

> Les personnages sont illustratifs. Les numéros d'écran renvoient à la maquette Figma (1 · Accueil … 7 · Tableau de bord) ; les écrans absents de la maquette sont listés au §7.

- **UJ-1. Awa signale un dépôt de plastique près du marché, sans réseau.**
  - **Persona et contexte :** Awa, 34 ans, commerçante, Android d'entrée de gamme, forfait de données souvent épuisé.
  - **Point de départ :** application installée (PWA), sans compte ; signalement anonyme.
  - **Déroulé :** écran 1, appui sur « Signaler un dépôt » → écran 2, photo et Position détectée (précision en mètres) → écran 3, l'IA propose « Plastique, 87 % » ; Awa choisit la Taille de tas « moyen » et envoie.
  - **Moment clé :** écran 4, un accusé de réception « en attente d'envoi » s'affiche sans attendre le réseau.
  - **Résolution :** au retour du réseau, le Signalement part tout seul, reçoit son Numéro de suivi (par exemple TC-2026-004217), et la Frise de suivi apparaît à l'étape « Signalé ». Awa voit plus tard « Validé », puis « Collecté », en rouvrant l'application sur son téléphone.
  - **Cas limite :** si le Score de confiance est sous le Seuil de confiance (60 %), l'écran 3 n'affiche aucun Type de déchet présélectionné et Awa doit en toucher un.

- **UJ-2. Fatou, modératrice à la commune, trie la file du matin.**
  - **Persona et contexte :** Fatou, 29 ans, agente du service propreté, sur ordinateur de bureau avec un réseau stable.
  - **Point de départ :** connectée sur navigateur avec le rôle Modérateur.
  - **Déroulé :** File de modération triée par ancienneté → photo, Position, Classification serveur, et un drapeau « Désaccord IA » quand le Type de déchet envoyé par l'appareil diffère de la Classification serveur.
  - **Moment clé :** elle valide un Signalement en un clic, en confirmant ou en corrigeant le Type de déchet pré-rempli, ou le rejette avec un motif obligatoire.
  - **Résolution :** le Signalement validé devient visible des Collecteurs vérifiés ; l'action est inscrite au Journal d'audit.

- **UJ-3. Ibrahima, collecteur d'un GIE de pré-collecte, prend et prouve une Mission.**
  - **Persona et contexte :** Ibrahima, 41 ans, membre d'un GIE de pré-collecte, Android à 2 Go de RAM, données mobiles limitées.
  - **Point de départ :** connecté par OTP, compte Collecteur vérifié.
  - **Déroulé :** écran 5, Signalements `validé` dans un rayon de 5 km avec Type de déchet, distance, Poids estimé et Score de confiance → « Accepter la mission » → la Position précise s'affiche, puis l'itinéraire s'ouvre dans l'application de cartes du téléphone.
  - **Arrivée :** sur place, écran 6, photo avant, collecte, photo après, Poids déclaré de 15 kg (estimé).
  - **Moment clé :** l'application confirme « vous êtes à moins de 150 m du dépôt » et la Preuve de collecte est acceptée.
  - **Résolution :** la Mission entre dans son historique ; le Signalement passe à « Collecté ».
  - **Cas limite :** un autre Collecteur a accepté la Mission une seconde avant lui ; Ibrahima voit « Mission déjà prise » et la liste se rafraîchit.

- **UJ-4. M. Ndiaye, chef du service propreté, prépare le point mensuel.**
  - **Persona et contexte :** M. Ndiaye, 55 ans, chef du service propreté, rend compte au maire chaque mois.
  - **Point de départ :** connecté sur ordinateur avec le rôle Administrateur d'organisation.
  - **Déroulé :** écran 7 avec les indicateurs de FR-31 (Signalements du mois, Délai médian, Taux de traitement, Kg collectés par Type de déchet, Collecteurs vérifiés actifs) → Carte de chaleur filtrée sur le dernier mois → répartition par Type de déchet.
  - **Moment clé :** l'Export agrégé en CSV part dans son rapport, sans aucune donnée personnelle.
  - **Résolution :** il repère deux zones prioritaires sur la Carte de chaleur pour la prochaine tournée.

- **UJ-5. Moussa supprime son compte.**
  - **Persona et contexte :** Moussa, 52 ans, a créé un compte pour suivre ses Signalements sur deux téléphones.
  - **Déroulé :** depuis son profil, il demande la suppression de son compte.
  - **Résolution :** son numéro est effacé ; ses Signalements validés restent dans les statistiques avec un auteur anonymisé ; ceux encore en attente sont supprimés (FR-5).

- **UJ-6. M. Ndiaye vérifie Ibrahima, récupérateur informel.**
  - **Point de départ :** Ibrahima se présente au service propreté avec son téléphone.
  - **Déroulé :** M. Ndiaye crée le compte Collecteur et le marque vérifié selon les critères retenus (§11, Q7).
  - **Résolution :** Ibrahima peut se connecter et voir les Signalements `validé` proches (UJ-3) ; l'action est inscrite au Journal d'audit. Réalise FR-35.

- **UJ-7. Un gestionnaire d'hôtel demande une collecte ponctuelle.**
  - **Déroulé :** depuis la console, il choisit un Site, les Types de déchet et un créneau. Une Mission d'Origine `collection_request` part chez les Collecteurs éligibles.
  - **Résolution :** il voit la Preuve de collecte et les kg vérifiés de son Site, puis les retrouve dans son rapport mensuel. Réalise FR-56 à FR-61.

- **UJ-8. Le Super Admin ouvre une commune cliente.**
  - **Déroulé :** il crée l'Organisation, lui rattache sa Zone, nomme son premier Administrateur d'organisation et enregistre son Contrat.
  - **Résolution :** les Signalements reçus dans cette Zone sont désormais rattachés à la commune, qui ne voit que ses données. Réalise FR-44, FR-47, FR-50 et FR-51.

- **UJ-9. Ibrahima voit ce qui lui est dû.**
  - **Déroulé :** après sa Preuve acceptée, il voit le Montant dû de sa Mission. Plus tard, le payeur confirme le paiement mobile money avec sa référence, et le Montant passe « payé ».
  - **Cas limite :** s'il n'a rien reçu, il conteste, ce qui ouvre un Litige. Réalise FR-62 à FR-66.

- **UJ-10. Un recycleur achète un Lot de plastique.**
  - **Déroulé :** Ibrahima constitue un Lot avec les kg de plastique qu'il a prouvés. Un Recycleur vérifié filtre les Lots de plastique de sa zone et réserve ce Lot.
  - **Résolution :** il obtient le contact d'Ibrahima, confirme la réception, et la vente est enregistrée. Réalise FR-38 à FR-40 et FR-69 à FR-71.

### 2.4 Rôles et espaces

Les rôles sont portés par une **Appartenance** à une Organisation (FR-45). Une personne peut avoir plusieurs Appartenances. Le Citoyen n'en a aucune.

| Acteur | Espace | Organisation (type) | Vérifié par | Accès |
|---|---|---|---|---|
| Citoyen | mobile `/` | aucune | — | gratuit, avec ou sans compte |
| Collecteur | mobile `/` | commune, opérateur, groupement de collecteurs ou plateforme | l'organisation | gratuit ; rémunéré pour les collectes validées ; vendeur de ses kg vérifiés |
| Modérateur | console `/console` | commune ou opérateur | — | contrat de l'organisation |
| Administrateur d'organisation | console | commune, opérateur ou groupement de collecteurs | plateforme | contrat de l'organisation |
| Gestionnaire d'entreprise | console | entreprise | plateforme | contrat de l'organisation |
| Recycleur | console | recycleur | plateforme | contrat de l'organisation |
| Super Admin | console | plateforme | — | équipe TerangaCycle |

## 3. Glossaire

**Acteurs**
- **Citoyen** : personne qui crée un Signalement, connectée ou anonyme.
- **Collecteur** : personne (récupérateur informel, membre d'un GIE) qui exécute des Missions. Un **Collecteur vérifié** a été validé par une Organisation (commune, opérateur, groupement de collecteurs ou plateforme) dont il est membre ; il n'accepte que les Missions des Organisations qui l'ont vérifié (FR-48).
- **Groupement de collecteurs** : Organisation de type `collector_group` (par exemple un GIE de pré-collecte) dont les Collecteurs sont membres ; il peut vendre leurs kg vérifiés si son Contrat l'y autorise (FR-38).
- **Recycleur** : membre d'une Organisation de type recycleur, vérifiée par la plateforme, qui achète des Lots de matière.
- **Gestionnaire d'entreprise** : membre d'une Organisation de type entreprise ; il gère ses Sites et ses Demandes de collecte.
- **Super Admin** : membre de l'Organisation plateforme (équipe TerangaCycle), distinct de l'Administrateur d'organisation ; il administre toutes les Organisations, et chacun de ses accès à une autre Organisation est audité.
- **Modérateur** : personnel qui valide ou rejette les Signalements.
- **Administrateur d'organisation** : membre d'une commune, d'un opérateur ou d'un groupement de collecteurs, qui pilote le Tableau de bord, gère les membres et exporte les données **de son Organisation**. Remplace « Administrateur commune ».
- **Personnel** : Modérateur ou Administrateur d'organisation d'une commune ou d'un opérateur, pour son Organisation.
- **Utilisateur connecté** : toute personne authentifiée, quel que soit son rôle.
- **Visiteur** : personne non connectée qui consulte la carte publique agrégée (FR-34).
- **Second facteur** : application d'authentification exigée du Personnel en plus de l'OTP (FR-43).

**Organisations et espaces**
- **Organisation** : client ou acteur de la plateforme, de type commune, opérateur, groupement de collecteurs (`collector_group`), entreprise, recycleur ou plateforme. Elle a un statut `active` ou `suspendue`. Une seule Organisation plateforme existe.
- **Appartenance** : lien entre une personne, une Organisation et un rôle, avec un statut et une date de vérification.
- **Organisation responsable** : Organisation à laquelle un Signalement est rattaché à sa réception (FR-47).
- **Portée d'organisation** : ensemble des Organisations dont une personne peut lire ou modifier les objets (FR-46).
- **Espace mobile** : partie de l'application servie sous `/`, pour le Citoyen et le Collecteur.
- **Console web** : partie de l'application servie sous `/console` et chargée séparément, pour le Personnel, le Gestionnaire d'entreprise, le Recycleur et le Super Admin.
- **Site** : lieu d'une entreprise où des déchets sont produits et collectés.
- **Demande de collecte** : demande ponctuelle d'une entreprise pour un Site ; elle crée une Mission.
- **Programme de collecte** : collectes régulières d'un Site, qui créent des Demandes de collecte à échéance.
- **Origine de Mission** : Signalement `validé` (`report`) ou Demande de collecte (`collection_request`).

**Signalement et suivi**
- **Signalement** : déclaration d'un dépôt de déchets, avec une photo, une Position, une Taille de tas, un Type de déchet et un commentaire optionnel. Il a un et un seul Statut.
- **Statut** : état d'un Signalement : `en attente de modération` → `validé` ou `rejeté` ; `validé` → `assigné` ; `assigné` → `collecté`, ou retour à `validé` si la Mission est `annulée` ou `expirée`. `rejeté` et `collecté` sont terminaux. Toute transition non prévue, de Statut ou de Statut de Mission, est refusée et ne modifie rien.
- **Frise de suivi** : affichage du Statut en 4 étapes du chemin nominal : Signalé (`en attente de modération`), Validé (`validé`), Assigné (`assigné`), Collecté (`collecté`). `rejeté` remplace les étapes suivantes, avec son motif. Un Signalement en attente d'envoi n'a pas encore de frise.
- **Numéro de suivi** : identifiant lisible d'un Signalement au format `TC-AAAA-NNNNNN`, attribué par le serveur.
- **Identifiant client** : UUID généré sur l'appareil à la création d'un Signalement, qui permet un renvoi sans doublon.
- **Identifiant d'appareil** : secret aléatoire généré à l'installation de la PWA ; il rattache à l'appareil les Signalements d'un Citoyen anonyme. Il n'est jamais affiché ni renvoyé par le serveur.
- **Position** : coordonnées GPS et précision en mètres, capturées à la création du Signalement ou de la Preuve de collecte.
- **Zone** : découpage administratif (commune, quartier).
- **Zone active** : Zone où le service est ouvert ; Dakar pour la démo, la commune partenaire pour le pilote.
- **Taille de tas** : petit, moyen ou grand ; choisie par le Citoyen.
- **Poids estimé** : poids déduit de la Taille de tas et du Type de déchet par une table de conversion.
- **File hors-ligne** : stockage local des Signalements non encore envoyés.
- **En attente d'envoi** : état, sur l'appareil, d'un Signalement enregistré dans la File hors-ligne et pas encore reçu par le serveur. Ce n'est pas un Statut, et il n'a pas encore de Numéro de suivi.
- **Doublon probable** : Signalement dont la Position est à moins de 50 m d'un Signalement non terminal reçu dans les 72 h précédentes `[ASSUMPTION : 50 m et 72 h, configurables]`, ou dont la photo est strictement identique à une photo déjà reçue.

**Classification IA**
- **Type de déchet** : une des 5 classes : plastique, métal, verre, organique, mixte.
- **Modèle** : classifieur d'images versionné, unique, exécuté sur l'appareil et sur le serveur.
- **Modèle factice** : remplaçant du Modèle qui respecte la même interface et renvoie des prédictions fixes ; il sert de repli à la porte H24.
- **Fiche du Modèle** : document publié avec chaque version du Modèle : données et licence de chaque source, métriques, matrice de confusion, limites connues (SM-2).
- **Jeu de test figé** : photos prises au Sénégal, au moins 150 par classe, découpées par lieu et par jour, jamais utilisées pour l'entraînement (SM-2).
- **Classification locale** : prédiction du Modèle exécuté sur l'appareil.
- **Classification serveur** : prédiction du même Modèle sur le serveur, sur la même photo, calculée en tâche de fond. Elle sert de référence au Désaccord IA et pré-remplit le Type de déchet retenu quand le Citoyen n'a pas choisi.
- **Score de confiance** : probabilité calibrée que le Modèle associe au Type de déchet proposé, affichée en pourcentage.
- **Seuil de confiance** : 60 %. Sous ce Score de confiance, le Citoyen doit choisir le Type de déchet lui-même.
- **Type de déchet retenu** : Type de déchet fixé par le Modérateur à la validation du Signalement ; c'est celui que voient les Collecteurs et que comptent les indicateurs.
- **Correction** : Type de déchet choisi par un humain (Citoyen à la création, Modérateur à la validation) qui diffère de la prédiction ; c'est un exemple étiqueté pour le réentraînement.
- **Désaccord IA** : le Type de déchet envoyé par l'appareil (Classification locale, ou choix du Citoyen) diffère de la Classification serveur. Il n'est calculé que si une Classification locale a été produite.

**Modération**
- **File de modération** : liste des Signalements `en attente de modération`.
- **Drapeau** : marque affichée dans la File de modération : Désaccord IA, Doublon probable, « faible confiance » (Score de confiance local sous le Seuil de confiance) ou « position imprécise » (FR-7).

**Missions et preuves**
- **Mission** : prise en charge d'une Origine (Signalement `validé` ou Demande de collecte) par un Collecteur vérifié. Au plus une Mission `active` par Origine.
- **Statut de Mission** : `active` → `terminée` (Preuve de collecte acceptée), `annulée` (par le Collecteur ou l'Administrateur d'organisation) ou `expirée` (sans Preuve dans le délai de FR-42). `terminée`, `annulée` et `expirée` sont terminaux.
- **Preuve de collecte** : photo avant, photo après, Poids déclaré et Position du Collecteur, horodatés par le serveur. « Preuve » en est l'abréviation admise.
- **Poids déclaré** : poids saisi par le Collecteur dans la Preuve de collecte, avec la mention `pesé` ou `estimé`.
- **Revue de Preuve** : état d'une Preuve de collecte acceptée au regard du contrôle par échantillon : `non revue`, `confirmée` ou `contestée`.

**Commune et données**
- **Tableau de bord** : vue de l'Administrateur d'organisation (indicateurs, Carte de chaleur, répartition par Type de déchet).
- **Cohorte** : ensemble des Signalements reçus par le serveur pendant une période (horodatage serveur de réception) ; base des indicateurs de FR-31.
- **Indicateurs** : Nombre de Signalements, Délai médian, Taux de traitement, Kg collectés et Collecteurs vérifiés actifs, définis en FR-31.
- **Carte de chaleur** : densité des Signalements, agrégée par cellule de grille ou par Zone.
- **Export agrégé** : fichier CSV ou GeoJSON sans donnée personnelle, avec des Positions arrondies.
- **Journal d'audit** : trace horodatée par le serveur, en ajout seul, des actions listées en FR-36 ; aucune entrée ne peut être modifiée ni supprimée.
- **kg vérifiés** : Poids déclaré d'une Preuve de collecte acceptée et non `contestée`.
- **Lot de matière** : quantité de matière constituée **à partir de kg vérifiés** (Éléments de lot) et mise en vente par son vendeur (FR-38).
- **Élément de lot** : part d'un Lot qui reprend une Preuve d'origine et les kg prélevés sur elle.
- **Vendeur** : ayant droit des kg d'une Preuve, fixé à l'acceptation de la Preuve : le Collecteur, son groupement, ou l'Organisation de la Mission si son Contrat le prévoit (FR-38).
- **Statut de Lot** : `disponible` → `réservé` → `vendu` ; `réservé` → `disponible` (réservation annulée) ; `retiré` (terminal).
- **Réservation** : demande d'un Recycleur vérifié qui bloque un Lot `disponible`.
- **Vente** : vente confirmée d'un Lot, avec prix et date ; elle porte la Commission.
- **Commission** : montant enregistré sur une Vente, calculé depuis un paramètre du Contrat du Recycleur ; aucun encaissement.

**Contrats et finance terrain** (aucune détention de fonds)
- **Contrat** : lien entre une Organisation et une offre ; il porte les paramètres commerciaux (prix mensuel, frais de coordination, rémunération, commission, droit de vendre des Lots), sans valeur dans ce document.
- **Facture** : document d'une période de Contrat, en état `émise`, `payée` ou `en retard`.
- **Frais de coordination** et **Rémunération prévue** : montants figés sur une Mission à sa création, calculés depuis le Contrat de son Organisation.
- **Montant dû** : somme due à un Collecteur pour une Mission terminée, en état `dû`, `payé` ou `contesté`.
- **Référence de paiement** : référence de transaction mobile money saisie par le payeur ; jamais vérifiée auprès d'un opérateur de paiement.
- **Litige** : contestation d'une Preuve, d'un Montant dû ou d'une Vente, tranchée par le Super Admin.
- **Alerte de fraude** : signal créé sur une Preuve suspecte (FR-68).
- **Données de démonstration** : données fictives, ou créées en Mode démonstration, toujours étiquetées comme telles à l'écran.
- **Mode démonstration** : configuration du hackathon où le code OTP s'affiche à l'écran et où toute donnée créée est étiquetée Données de démonstration ; interdit en production.

## 4. Fonctionnalités

### 4.1 Accès, identité et consentement

**Description.** On peut signaler sans compte, pour garder le parcours sous 30 s. Les autres rôles se connectent par numéro de téléphone et code à usage unique (OTP) ; il n'y a pas de mot de passe citoyen. Les droits dépendent du rôle et, pour chaque objet, de la propriété. Réalise UJ-1, UJ-3, UJ-5.

#### FR-1 : Connexion par OTP

Un utilisateur peut se connecter avec son numéro de téléphone et un code OTP reçu par SMS.

**Conséquences (testables) :**
- Le code expire après 5 min et n'est valable qu'une fois ; il est invalidé après 5 essais erronés.
- 5 demandes au plus par heure et par numéro, 5 par Identifiant d'appareil et 20 par IP `[ASSUMPTION]` ; au-delà, la demande est refusée (429) avec le délai d'attente.
- Un plafond quotidien de SMS, configurable `[ASSUMPTION : valeur fixée avec la passerelle, §11 Q2]`, coupe l'envoi : la demande est refusée (503) avec un message, et une alerte part sur le canal de l'équipe (NFR-16).
- Le code OTP n'est jamais stocké en clair.
- Seuls les numéros sénégalais sont acceptés `[ASSUMPTION : liste de préfixes +221 pour le MVP]`.

#### FR-2 : Session

Un utilisateur connecté garde sa session sans ressaisir de code pendant 30 jours d'activité, et peut se déconnecter.

**Conséquences :**
- Une session volée et révoquée ne peut plus servir.
- La réutilisation d'un jeton de renouvellement déjà utilisé révoque toute la session.
- La déconnexion invalide la session côté serveur.
- Le jeton d'accès expire au plus 15 min après son émission ; après une déconnexion ou une révocation, le renouvellement est refusé (401).
- Aucun jeton n'est stocké dans `localStorage`, `sessionStorage` ni IndexedDB (test de bout en bout qui inspecte le stockage du navigateur).
- Un jeton signé avec un algorithme hors liste blanche, d'émetteur ou d'audience incorrects, expiré ou de clé inconnue, est refusé (401) ; un test par cas.

#### FR-3 : Rôles et contrôle d'accès

Le système applique les rôles Citoyen, Collecteur, Recycleur, Modérateur et Administrateur d'organisation sur chaque action. Il vérifie aussi la propriété de chaque objet : un Citoyen ne voit que ses propres Signalements.

**Conséquences :**
- Un test automatisé appelle chaque route de NFR-9 avec chaque rôle et sans jeton ; tout accès non prévu échoue (401 ou 403).
- Un Collecteur ne voit jamais l'auteur d'un Signalement.
- Un Citoyen anonyme ne possède que les Signalements créés avec son Identifiant d'appareil. Un Signalement n'est jamais consultable à partir de son seul Numéro de suivi.
- **(v2.0)** Les rôles sont portés par les Appartenances (§2.4, FR-45) et s'appliquent dans la Portée d'organisation (FR-46). Le test route × rôle couvre tous les rôles de §2.4, et un test d'isolement entre organisations s'y ajoute (NFR-9, NFR-18).

#### FR-4 : Consentement

Avant la première capture, le Citoyen voit un écran de consentement qui couvre :
- la géolocalisation ;
- l'envoi de la photo ;
- l'usage des photos et des Corrections pour améliorer le Modèle ;
- la consigne de ne photographier ni personne ni plaque.

**Conséquences :**
- Rien n'est envoyé sans acceptation.
- L'acceptation est horodatée pour un compte, et mémorisée sur l'appareil pour un anonyme.
- Le Citoyen peut refuser l'usage pour le réentraînement sans perdre l'accès au signalement.
- Le choix est enregistré sur chaque Signalement au moment de sa création.
- Le Citoyen peut changer d'avis à tout moment, depuis son profil (connecté) ou les réglages de l'application (anonyme) ; un retrait exclut ses Signalements, passés et futurs, des exports suivants.

#### FR-5 : Gestion de ses données

Un utilisateur connecté peut consulter son profil, changer sa langue et son nom affiché, et supprimer son compte. Réalise UJ-5.

**Conséquences :**
- La suppression efface le numéro et refuse la requête suivante de l'utilisateur (401) ; la purge complète a lieu sous 30 jours.
- Les photos et Positions de ses Signalements `en attente de modération` ou `rejeté` sont supprimées ; ses Signalements ayant atteint `validé` sont conservés avec un auteur anonymisé, parce qu'ils fondent les indicateurs et les Preuves des Collecteurs.
- L'utilisateur consulte les données de son profil et ses Signalements (droit d'accès) et corrige son nom affiché (rectification).
- Un Citoyen anonyme peut retirer, depuis l'appareil d'origine, un Signalement encore `en attente de modération`.

#### FR-6 : Mode démonstration

Le Mode démonstration affiche le code OTP à l'écran, pour une démo sans passerelle SMS.

**Conséquences :**
- Le service refuse de démarrer si le Mode démonstration est actif en configuration de production.
- Un bandeau « Mode démonstration » est visible sur tous les écrans tant qu'il est actif.

#### FR-43 : Second facteur du Personnel *(Must avant le pilote ; hors des portes du hackathon)*

Un Modérateur ou un Administrateur d'organisation se connecte avec l'OTP par SMS et un Second facteur (application d'authentification).

**Conséquences :**
- Sans Second facteur valide, les fonctions du Personnel sont refusées (403).
- L'activation et la réinitialisation du Second facteur sont inscrites au Journal d'audit.
- **(v2.0)** Le Second facteur est aussi obligatoire pour le **Super Admin** dès qu'il y a des données réelles. Il est facultatif en P2 pour le Gestionnaire d'entreprise et le Recycleur.

### 4.2 Signalement citoyen

**Description.** C'est le cœur du parcours de 30 s (écrans 1 → 4). Réalise UJ-1.

#### FR-7 : Créer un Signalement

Un Citoyen, connecté ou anonyme, crée un Signalement avec :
- une photo, obligatoire ;
- une Position capturée automatiquement, avec sa précision ;
- une Taille de tas ;
- un commentaire optionnel de 280 caractères au plus.

**Conséquences :**
- Sans photo, sans Position ou sans Taille de tas, l'envoi est impossible.
- Une Position hors de la Zone active est refusée dès l'écran 2, avant la photo, avec le message « TerangaCycle n'est pas encore actif ici » ; le serveur refuse de même (422) toute Position hors de la Zone active.
- Le serveur attribue le Numéro de suivi et le Statut `en attente de modération`.
- Le Numéro de suivi est unique, au format `TC-AAAA-NNNNNN`, l'année étant celle de la réception par le serveur ; deux créations simultanées obtiennent deux numéros distincts.
- La Zone (quartier) est déterminée automatiquement à partir de la Position.
- Si la précision de la Position dépasse 50 m `[ASSUMPTION]`, l'écran 2 invite à patienter quelques secondes ; le Citoyen peut envoyer quand même, et le Signalement porte le drapeau « position imprécise » dans la File de modération.
- L'écran de capture (écran 2) rappelle à chaque fois la consigne « ni personne ni plaque ».

#### FR-8 : Photo légère et sans métadonnées

Avant envoi, la photo est compressée sur l'appareil à 300 Ko au plus. Le serveur la revalide, la ré-encode et supprime toutes ses métadonnées (EXIF, GPS).

**Conséquences :**
- Une image corrompue, ou de plus de 12 mégapixels ou 1 Mo, est refusée (413 ou 422).
- La photo stockée ne contient aucune métadonnée EXIF.
- Une photo strictement identique à une photo déjà reçue fait du Signalement un Doublon probable.
- Le serveur n'accepte que JPEG, PNG et WebP (415 sinon) ; une photo HEIC est convertie en JPEG sur l'appareil avant l'envoi.

#### FR-9 : Renvoi sans doublon et sans fuite

Chaque Signalement porte un Identifiant client. Un renvoi du même Signalement par le même auteur ou le même appareil renvoie le Signalement existant, sans en créer un second.

**Conséquences :**
- 10 renvois identiques produisent un seul Signalement.
- Un autre utilisateur qui présente le même Identifiant client ne reçoit **aucune** donnée du Signalement existant (409).
- La première réception renvoie 201 ; un renvoi par le même auteur ou le même appareil renvoie 200 avec le même Numéro de suivi.
- La réponse 409 ne contient ni Numéro de suivi, ni Statut, ni Position.

#### FR-10 : Limite anti-abus

Un Citoyen anonyme peut créer au plus 10 Signalements par heure et par Identifiant d'appareil ou par IP ; un Citoyen connecté, au plus 10 par heure et par compte `[ASSUMPTION]`. Tout Utilisateur connecté est limité à 60 requêtes par minute. Au-delà, la réponse est 429.

**Conséquences :**
- L'IP retenue est celle que transmet le proxy de confiance : 11 requêtes portant 11 en-têtes `X-Forwarded-For` différents obtiennent un 429 à la 11e.
- Les compteurs survivent à un redémarrage du service.

### 4.3 Classification IA

**Description.** L'IA propose, l'humain confirme. Le Modèle tourne d'abord sur l'appareil, pour un résultat en moins de 3 s, même hors-ligne, puis sur le serveur, hors de portée du client. Le Modérateur fixe le Type de déchet retenu. Réalise UJ-1, UJ-2.

#### FR-11 : Classification locale

Après la capture, le Modèle affiche un Type de déchet et un Score de confiance.

**Conséquences :**
- Le résultat s'affiche en moins de 3 s sur un Android à 2 Go de RAM (NFR-1), sans réseau une fois le Modèle en cache.
- Chaque Type de déchet a un pictogramme et une couleur.
- Tant que le Modèle n'est pas en cache, le Citoyen peut signaler : il choisit le Type de déchet lui-même, et aucun Désaccord IA n'est calculé pour ce Signalement.

#### FR-12 : Seuil de confiance

Sous le Seuil de confiance (60 %), aucun Type de déchet n'est présélectionné et le Citoyen doit en choisir un parmi les 5.

**Conséquences :**
- Test : avec un Score de confiance forcé à 59 %, aucun Type de déchet n'est présélectionné et l'envoi reste impossible tant qu'aucun n'est choisi ; à 60 %, le Type de déchet proposé est présélectionné.

#### FR-13 : Correction

Le Citoyen, à la création, et le Modérateur, à la validation (FR-23), peuvent corriger le Type de déchet en un toucher.

**Conséquences :**
- Chaque Correction est enregistrée avec la prédiction d'origine, la version du Modèle et son auteur.
- Seules les Corrections de Signalements ayant atteint `validé`, dont l'auteur a accepté l'usage pour le réentraînement, sont exportées comme exemples étiquetés. Test : un Signalement avec refus n'apparaît pas dans l'export.

#### FR-14 : Classification serveur

Le serveur reclasse la même photo avec la même version du Modèle. Sa prédiction et la Classification locale sont toutes deux conservées.

**Conséquences :**
- Le Type de déchet pré-rempli pour le Modérateur est le choix du Citoyen s'il en a fait un, sinon la Classification serveur. Le Type de déchet retenu n'est fixé qu'à la validation (FR-23) : aucun Type de déchet envoyé par l'appareil ne devient définitif sans décision du Personnel.
- La création répond sans attendre la Classification serveur, qui est calculée en tâche de fond ; le traitement d'une photo par le Modèle serveur prend moins de 2 s (p95).
- La file de classification est bornée `[ASSUMPTION : 500 tâches]` ; quand elle est pleine, les nouveaux Signalements sont acceptés et restent « classification serveur en attente » jusqu'à leur reclassement.
- **(v2.0)** Tant que la Classification serveur n'est pas livrée (lot P4), le Type de déchet pré-rempli est le choix du Citoyen, sinon la Classification locale, sinon aucun. Il ne devient définitif que par la décision du Personnel.

#### FR-15 : Désaccord IA

Un Signalement en Désaccord IA porte le drapeau « Désaccord IA » dans la File de modération (FR-22).

**Conséquences :**
- Un Signalement dont le Type de déchet envoyé par l'appareil diffère de la Classification serveur porte le drapeau Désaccord IA. Test : prédiction locale forcée différente → drapeau présent.
- Un Signalement envoyé sans Classification locale (FR-11, Modèle absent du cache) ne porte pas ce drapeau.

#### FR-16 : Version du Modèle

Chaque classification enregistre la version du Modèle. Le Modèle peut être remplacé (du Modèle factice au Modèle entraîné, puis d'une version à la suivante) sans changer les écrans ni l'API.

**Conséquences :**
- Une nouvelle version du Modèle n'est publiée que si elle atteint les seuils de SM-2 sur le Jeu de test figé, et avec sa Fiche du Modèle.
- Pendant le pilote, le Modèle est réentraîné au plus une fois par mois sur les Corrections exportables (FR-13).

### 4.4 File hors-ligne

**Description.** Le réseau est instable : aucun Signalement ne doit être perdu. Réalise UJ-1.

#### FR-17 : Mise en file

Sans réseau, un Signalement complet (photo, Position, Type de déchet, Taille de tas, commentaire) est enregistré dans la File hors-ligne, et l'écran 4 affiche « en attente d'envoi ».

**Conséquences :**
- En mode avion, 100 % des champs saisis sont conservés, même si l'application est fermée puis rouverte (SM-4).

#### FR-18 : Synchronisation

Au retour du réseau, ou à l'ouverture de l'application, la File hors-ligne s'envoie automatiquement.

**Conséquences :**
- Aucun doublon n'est créé (FR-9).
- En cas d'erreur temporaire (429 ou 5xx), le Signalement reste en file et repart plus tard.
- En cas de refus définitif (4xx autre que 408 et 429), le Signalement sort de la File hors-ligne et le Citoyen voit le motif.

#### FR-19 : Visibilité de la file

Le Citoyen voit le nombre de Signalements en attente d'envoi et peut relancer l'envoi manuellement.

**Conséquences :**
- Le compteur affiche le nombre exact de Signalements en attente d'envoi et revient à 0 après une synchronisation réussie.
- Un appui sur « Réessayer » lance une tentative d'envoi dans la seconde, sans attendre le prochain essai automatique ; sans réseau, il affiche « Toujours hors ligne ».

### 4.5 Suivi et notifications

#### FR-20 : Suivi de ses Signalements

Un Citoyen voit la liste de ses Signalements, avec le Numéro de suivi, le Statut et la Frise de suivi (écrans 1 et 4). Un Citoyen connecté voit les Signalements de son compte ; un Citoyen anonyme voit ceux créés depuis son appareil. Réalise UJ-1.

**Conséquences :**
- Le Numéro de suivi s'affiche sur l'écran 4 dès que la réponse du serveur est reçue ; avant, l'écran 4 affiche « en attente d'envoi ».
- Le Statut affiché se met à jour au plus 15 s après le changement, quand l'application est ouverte.
- Un Signalement `rejeté` affiche son motif.
- Un Citoyen anonyme qui réinstalle l'application ou efface les données du navigateur perd sa liste ; l'écran de consentement (FR-4) l'en informe et propose de créer un compte.
- Une requête venant d'un autre appareil, ou qui ne présente que le Numéro de suivi, ne reçoit aucune donnée du Signalement.

#### FR-21 : Notification de changement

À l'ouverture de l'application, le Citoyen, connecté ou anonyme, voit chaque changement de Statut de ses Signalements survenu depuis sa dernière visite. Le Citoyen connecté reçoit aussi une notification push s'il l'a autorisée.

**Conséquences :**
- La notification indique le Numéro de suivi, le nouveau Statut et, pour `rejeté`, le motif.
- La notification push est émise au plus 1 min après le changement de Statut.
- Un Citoyen anonyme ne reçoit pas de notification push `[NON-GOAL pour le MVP]`.

**Hors périmètre :** notifications par SMS ou WhatsApp `[NON-GOAL pour le MVP]`.

### 4.6 Modération

#### FR-22 : File de modération

Un Modérateur voit les Signalements `en attente de modération`, les plus anciens d'abord, avec :
- la photo ;
- la Position et sa précision ;
- le Type de déchet envoyé par l'appareil et son Score de confiance ;
- la Classification serveur ;
- les drapeaux Désaccord IA, Doublon probable, « faible confiance » et « position imprécise ».

Réalise UJ-2.

**Conséquences :**
- Tant que la Classification serveur n'est pas disponible, la File affiche « classification serveur en attente » et le Modérateur peut quand même décider.
- La File peut être filtrée par drapeau ; un Doublon probable renvoie vers le Signalement d'origine.
- La File affiche au plus 50 Signalements par page.

#### FR-23 : Valider ou rejeter

Le Modérateur valide un Signalement ou le rejette avec un motif obligatoire.

**Conséquences :**
- Toute transition non prévue par le Statut renvoie 409.
- Chaque décision est inscrite au Journal d'audit.
- Un Signalement n'est visible des Collecteurs qu'une fois `validé` : les photos sont donc vues par un humain avant d'être exposées.
- En validant, le Modérateur confirme ou corrige le Type de déchet ; une correction est une Correction (FR-13) et est inscrite au Journal d'audit.
- Un rejet pour le motif « doublon » affiche au Citoyen le Numéro de suivi du Signalement d'origine.
- Le motif de rejet « Personne ou plaque visible » existe ; la photo d'un Signalement rejeté pour ce motif est supprimée du stockage sous 24 h, seule la décision restant au Journal d'audit.

### 4.7 Missions

#### FR-24 : Signalements `validé` proches

Un Collecteur vérifié voit les Signalements `validé` dans un rayon réglable de 1 à 10 km (5 km par défaut), triés par distance, sur une carte et en liste. Chaque élément affiche le Type de déchet retenu, la distance, le Poids estimé, le Score de confiance et la photo. Réalise UJ-3.

**Conséquences :**
- Aucune information sur l'auteur du Signalement n'est visible.
- Sans réglage, le rayon est de 5 km ; une valeur hors de 1 à 10 km est refusée (422).
- La liste est filtrable par Type de déchet.
- Le Score de confiance affiché est celui de la Classification serveur ; si le Type de déchet retenu diffère de la Classification serveur, l'élément affiche « Type confirmé par un humain » à la place.
- La liste charge des miniatures de 30 Ko au plus ; la photo complète ne se charge qu'à l'ouverture d'un Signalement.
- Avant l'acceptation, la Position d'un Signalement est donnée arrondie à 3 décimales (environ 110 m) et la distance à 100 m près. Test : un Collecteur vérifié qui n'est pas celui de la Mission ne reçoit jamais plus de 3 décimales.
- Après l'acceptation, le Collecteur de la Mission reçoit la Position précise (FR-27).
- **(v2.0)** Le Collecteur ne voit que les Missions ouvertes (Signalements `validé` et Demandes de collecte) des Organisations qui l'ont vérifié (FR-48). Test : un Collecteur vérifié par A ne voit rien de B.

#### FR-25 : Accepter une Mission

Un Collecteur vérifié accepte une Mission, et le Signalement passe à `assigné`.

**Conséquences :**
- Si deux Collecteurs acceptent en même temps, un seul réussit ; l'autre reçoit « Mission déjà prise » (409).
- Un Collecteur non vérifié ne peut pas accepter de Mission (403).
- Accepter une Mission sur un Signalement qui n'est pas `validé` est refusé (409).
- Un renvoi de la même acceptation par le même Collecteur renvoie la Mission existante, sans erreur.
- **(v2.0)** Ces règles valent pour toute Origine de Mission ; l'exclusivité vaut par Origine. Accepter une Mission d'une Organisation qui n'a pas vérifié le Collecteur est refusé (403).

#### FR-26 : Annuler une Mission

Le Collecteur annule sa Mission `active`, ou un Administrateur d'organisation annule une Mission `active` ; la Mission passe à `annulée` et le Signalement revient à `validé`.

**Conséquences :**
- Annuler une Mission `terminée`, `annulée` ou `expirée` est refusé (409).
- L'annulation est inscrite au Journal d'audit, avec son auteur.

#### FR-27 : Itinéraire

Depuis une Mission, le Collecteur ouvre l'application de cartes de son téléphone sur la Position du Signalement. *(Should)*

**Conséquences :**
- Le bouton d'itinéraire n'apparaît que pour le Collecteur de la Mission `active` ; il ouvre l'application de cartes centrée sur la Position précise du Signalement.

#### FR-28 : Assignation manuelle

Un Administrateur d'organisation peut assigner un Signalement `validé` à un Collecteur vérifié, qui en est notifié. *(Should)*

**Conséquences :**
- L'assignation crée une Mission `active` et passe le Signalement à `assigné`.
- Le Collecteur voit la Mission assignée dans l'application au plus 15 s après l'assignation, quand l'application est ouverte.
- Chaque assignation est inscrite au Journal d'audit.
- **(v2.0)** L'assignation est faite par l'Administrateur de l'Organisation de la Mission, à un Collecteur vérifié par cette Organisation.

#### FR-42 : Expiration d'une Mission *(Should, avant le pilote)*

Une Mission `active` sans Preuve de collecte 48 h après son acceptation `[ASSUMPTION : délai configurable]` passe à `expirée`, et le Signalement revient à `validé`.

**Conséquences :**
- Le Signalement redevient visible des Collecteurs vérifiés dans le rayon (FR-24).
- L'expiration est inscrite au Journal d'audit.
- Test avec une horloge simulée : à 48 h et 1 min, la Mission est `expirée` et le Signalement `validé`.

### 4.8 Preuve de collecte

#### FR-29 : Prouver une collecte

Le Collecteur de la Mission soumet une Preuve de collecte. Réalise UJ-3.

**Conséquences :**
- Sans photo avant, photo après, Poids déclaré supérieur à 0 et mention `pesé` ou `estimé`, la Preuve est refusée.
- La Preuve est refusée si la précision de la Position du Collecteur dépasse 50 m (l'écran 6 invite à réessayer), ou si sa distance à la Position du Signalement dépasse 150 m plus la précision du Signalement, plafonnée à 50 m `[ASSUMPTION : plafond de 50 m]`.
- Le message de refus indique la distance mesurée et le rayon accepté, sans accuser le Collecteur, par exemple : « Vous êtes à 230 m du dépôt ; rapprochez-vous à moins de 150 m. »
- Une Preuve acceptée passe la Mission à `terminée` et le Signalement à `collecté`.
- Une Preuve sur une Mission qui n'est pas `active` est refusée (409) ; une Preuve soumise par un autre Collecteur que celui de la Mission est refusée (403).
- Le renvoi d'une même Preuve après une coupure réseau renvoie la Preuve déjà acceptée : une seule Preuve et un seul Poids déclaré sont enregistrés.
- L'horodatage est celui du serveur.
- Sans réseau, la Preuve ne peut pas être envoyée : l'écran 6 l'indique et garde la saisie tant que l'application reste ouverte ; la Position est capturée au moment de l'envoi `[NON-GOAL pour le MVP : Preuve en File hors-ligne]`.
- Les photos de Preuve ne sont visibles que du Collecteur de la Mission et du Personnel ; l'écran 6 rappelle la consigne « ni personne ni plaque ».

#### FR-30 : Historique du Collecteur

Le Collecteur voit l'historique de ses Missions, en cours et terminées, avec les kg collectés.

**Conséquences :**
- Chaque Mission figure avec sa date, son Type de déchet retenu, son Poids déclaré et son Statut de Mission ; le total des kg collectés est affiché.
- Une Preuve `contestée` (FR-41) y apparaît comme telle.

#### FR-41 : Contrôler une Preuve de collecte par échantillon *(Should, avant le pilote)*

Chaque semaine, le système tire au hasard au moins 5 % des Preuves de collecte acceptées `[ASSUMPTION]`, et au moins une. Un membre du Personnel revoit chacune et la marque `confirmée` ou `contestée` ; le motif est obligatoire pour `contestée`.

**Conséquences :**
- Une Preuve `contestée` est exclue des Kg collectés (FR-31) et apparaît comme telle dans l'historique du Collecteur (FR-30) ; le Signalement reste `collecté`.
- Chaque Revue de Preuve est inscrite au Journal d'audit.
- Le Tableau de bord affiche la part de Preuves `contestée` parmi les Preuves revues ; elle mesure SM-C3.
- Une Preuve dont une photo est strictement identique à une photo déjà reçue (Signalement ou Preuve) est ajoutée d'office à l'échantillon.
- **(v2.0)** Une Preuve `contestée` ne produit **aucun kg valorisable** : elle ne peut entrer dans aucun Lot, et l'Élément de lot qui la contient est gelé (FR-71). Le Montant dû correspondant passe `contesté` et un Litige s'ouvre (FR-66).
- **(v2.0)** L'échantillon tire au moins une Preuve par Organisation qui a des Preuves acceptées dans la semaine.

#### FR-68 : Alertes de fraude

Une photo réutilisée (Signalement ou Preuve, toutes Organisations), un Poids déclaré hors des bornes `[ASSUMPTION : bornes configurables]` ou une Preuve `contestée` crée une Alerte de fraude.

**Conséquences :**
- L'Alerte est visible du Personnel de l'Organisation de la Mission et du Super Admin ; la Preuve concernée est ajoutée à l'échantillon de FR-41.
- Le Personnel classe une Alerte (`examinée`, motif) ; l'action est inscrite au Journal d'audit.

### 4.9 Tableau de bord de l'organisation

#### FR-31 : Indicateurs

L'Administrateur d'organisation voit les indicateurs suivants sur une période choisie. Ils portent sur la Cohorte de la période : les Signalements reçus par le serveur pendant cette période (horodatage serveur de réception). Réalise UJ-4.

| Indicateur | Définition |
|---|---|
| Nombre de Signalements | Signalements de la Cohorte ; dont ayant atteint `validé`, dont `rejeté` |
| Délai médian | Médiane, sur les Signalements de la Cohorte ayant atteint `collecté`, du délai entre la réception par le serveur et l'acceptation de la Preuve de collecte ; affiché avec le nombre de Signalements de la Cohorte encore ouverts |
| Taux de traitement | Signalements de la Cohorte ayant atteint `collecté` ÷ Signalements de la Cohorte ayant atteint `validé`, à la date du calcul |
| Kg collectés | Somme des Poids déclarés des Preuves de collecte acceptées pendant la période et non `contestée` (FR-41), au total et par Type de déchet, avec la part `pesé` |
| Collecteurs vérifiés actifs | Collecteurs vérifiés ayant au moins une Preuve de collecte acceptée pendant la période |

Il voit aussi la répartition des Signalements de la Cohorte par Type de déchet retenu.

**Conséquences :**
- « Ayant atteint » se lit dans l'historique des Statuts : un Signalement `collecté` compte parmi ceux ayant atteint `validé`.
- Sur un jeu d'essai de 10 Signalements ayant atteint `validé`, dont 6 `collecté`, le Taux de traitement affiché est 60 %.
- Un Signalement créé hors-ligne entre dans la Cohorte de sa date de réception par le serveur.
- **(v2.0)** Les indicateurs de FR-31 à FR-33 se calculent dans la Portée d'organisation de la personne. Ils se répartissent aussi par quartier, Type de déchet et période. Le Super Admin voit le total de la plateforme (FR-53).

#### FR-32 : Carte de chaleur

L'Administrateur d'organisation voit la Carte de chaleur, filtrable par période, Type de déchet et Statut.

**Conséquences :**
- L'affichage prend moins de 2 s pour 5 000 Signalements (NFR-3).

#### FR-33 : Export agrégé

L'Administrateur d'organisation télécharge un Export agrégé en CSV et en GeoJSON.

**Conséquences :**
- Le fichier ne contient aucun numéro, nom ni identifiant d'auteur.
- Les Positions y sont arrondies `[ASSUMPTION : à 3 décimales, environ 110 m]`.

#### FR-34 : Carte publique agrégée

Tout Visiteur voit une carte des Signalements agrégée par cellule ou par Zone, jamais de point précis. *(Should)*

**Conséquences :**
- Les cellules mesurent au moins 500 m de côté ; une cellule de moins de 3 Signalements n'est pas affichée `[ASSUMPTION]`.
- Aucune réponse publique de l'API ne contient de coordonnées de Signalement.
- Tant que FR-34 n'est pas livrée, aucune carte n'est accessible sans connexion.

### 4.10 Administration des comptes

#### FR-35 : Gérer les Collecteurs

Un Administrateur d'organisation gère les **Appartenances** de son Organisation : il crée l'Appartenance d'un Collecteur (et son compte s'il n'existe pas), la vérifie, la suspend et change le rôle d'un membre. La suspension d'un **compte** est réservée au Super Admin. Réalise UJ-6.

**Conséquences :**
- Chaque action est inscrite au Journal d'audit.
- La requête suivante d'un compte suspendu est refusée (401).

#### FR-36 : Journal d'audit

Le système inscrit au Journal d'audit, avec l'acteur, l'objet, l'état avant et après et l'horodatage serveur :
- toute transition de Statut et de Statut de Mission, y compris l'expiration automatique (FR-42) ;
- toute décision de modération, toute Correction par un Modérateur et toute Revue de Preuve (FR-41) ;
- toute assignation manuelle (FR-28) ;
- toute création, vérification, suspension, suppression de compte et tout changement de rôle ;
- toute activation ou réinitialisation du Second facteur (FR-43) ;
- tout Export agrégé (FR-33) et tout export des Corrections (FR-13) ;
- toute connexion du Personnel ;
- **(v2.0)** toute action sur une Organisation, une Appartenance, un Contrat, une Facture, un Montant dû, un Litige, un Lot, une Réservation ou une Vente, toute Alerte de fraude, et tout accès du Super Admin aux données d'une autre Organisation.

Chaque entrée porte l'Organisation concernée, sauf pour les actions de plateforme.

Un Administrateur d'organisation consulte le Journal d'audit, filtrable par action et par période *(Should)*. Le Personnel voit l'historique des Statuts dans le détail d'un Signalement.

**Conséquences :**
- Pour chaque action de la liste, un test vérifie qu'une entrée est créée.
- Aucune route ne permet de modifier ni de supprimer une entrée, et le rôle applicatif de la base n'en a pas le droit (NFR-17).

### 4.11 Données de démonstration

#### FR-37 : Jeu de démonstration étiqueté

Un jeu de Données de démonstration peut être chargé : Zones de Dakar, comptes de test pour chaque rôle, Signalements à divers Statuts.

**Conséquences :**
- Tout écran qui affiche des Données de démonstration porte l'étiquette « Données de démonstration ».
- Le jeu de démonstration se retire en une commande.
- Les comptes de test comprennent au moins un Collecteur vérifié, un Modérateur et un Administrateur d'organisation.
- Tant que le Mode démonstration est actif, tout Signalement, toute Mission et toute Preuve de collecte créés sont automatiquement étiquetés Données de démonstration.
- **(v2.0)** Le jeu comprend au moins deux Organisations communes, une entreprise, un groupement de collecteurs et un recycleur de démonstration, avec des comptes de chaque rôle de §2.4. Tout montant de démonstration est manifestement fictif et étiqueté.

### 4.12 Lots de matière (place de marché, lot P3)

**Description.** Le Collecteur vend la matière qu'il a prouvée. Un Lot ne contient que des kg vérifiés, non contestés et non encore vendus, ce que la base garantit. Un Recycleur vérifié consulte, réserve et achète. Aucun flux d'argent ne passe par TerangaCycle. Réalise UJ-10.

#### FR-38 : Constituer un Lot à partir de kg vérifiés

Le vendeur constitue un Lot (Type de déchet, Zone) à partir d'Éléments de lot. Chaque Élément reprend une Preuve d'origine et les kg prélevés sur elle.

**Conséquences :**
- Le vendeur est l'ayant droit des kg, fixé à l'acceptation de la Preuve : l'Organisation de la Mission si son Contrat la désigne comme vendeuse ; sinon le groupement de collecteurs du Collecteur, s'il en est membre et si le Contrat du groupement l'autorise à vendre ; sinon le **Collecteur** lui-même.
- Un Collecteur ne vend que des kg qu'il a lui-même prouvés.
- Seuls des kg vérifiés, non contestés et non encore vendus peuvent entrer dans un Lot ; la règle est vérifiée par la base de données.
- La somme des kg prélevés sur une Preuve ne dépasse jamais son Poids déclaré. Test : 20 prélèvements simultanés sur une même Preuve.
- Un Lot créé a le Statut de Lot `disponible`.

#### FR-39 : Consulter les Lots

Un Recycleur vérifié consulte les Lots `disponible`, filtrés par Type de déchet, quantité minimale et Zone.

**Conséquences :**
- Aucune réponse de la liste ne contient l'identité, le numéro ni le contact du vendeur.
- Un Recycleur non vérifié est refusé (403).

#### FR-40 : Réserver un Lot

Un Recycleur vérifié réserve un Lot `disponible` ; le Lot passe à `réservé` et le vendeur est notifié. Le contact du vendeur n'est donné qu'après la réservation.

**Conséquences :**
- Réserver un Lot déjà `réservé` est refusé (409).
- L'annulation d'une réservation remet le Lot `disponible`.
- Le vendeur voit la réservation au plus 15 s après, quand l'application est ouverte.

#### FR-69 : Vérifier un Recycleur

Le Super Admin vérifie une Organisation recycleur. Sans cette vérification, aucune consultation ni réservation n'est possible.

#### FR-70 : Vente confirmée et commission

Le Recycleur confirme la réception, puis le vendeur confirme la vente (prix, date). La Commission est calculée depuis le paramètre du Contrat du Recycleur et enregistrée sur la Vente, en état seulement.

**Conséquences :**
- Un Lot `vendu` est immuable.
- Aucun encaissement ni transfert n'a lieu par TerangaCycle.

#### FR-71 : Traçabilité des kg

Chaque kg vendu remonte à une Preuve de collecte.

**Conséquences :**
- Si une Preuve est contestée après son entrée dans un Lot non vendu, l'Élément est gelé et le Lot passe `retiré`. Si le Lot est déjà vendu, un Litige s'ouvre.

### 4.13 Organisations et appartenances

**Description.** Chaque client est une Organisation, et chaque donnée métier appartient à une Organisation. Les rôles sont donnés par des Appartenances. Réalise UJ-8.

#### FR-44 : Organisation

Une Organisation a un type (commune, opérateur, groupement de collecteurs, entreprise, recycleur, plateforme), un nom et un statut (`active`, `suspendue`). Une commune ou un opérateur est rattaché à une Zone. Une seule Organisation plateforme existe.

**Conséquences :**
- Une commune sans Zone est refusée (422).
- Une Organisation `suspendue` ne reçoit plus de nouveau Signalement, de Demande de collecte ni de Mission ; ses membres gardent la lecture de son historique.

#### FR-45 : Appartenance et rôle par organisation

Un rôle est donné par une Appartenance (personne, Organisation, rôle, statut, date de vérification). Une personne peut avoir plusieurs Appartenances.

**Conséquences :**
- Un rôle incompatible avec le type de l'Organisation est refusé (par exemple Recycleur dans une commune).
- Le rôle est lu en base à chaque requête, jamais dans le jeton.

#### FR-46 : Cloisonnement des données

Chaque objet métier appartient à une Organisation. Toute lecture, liste ou modification est limitée à la Portée d'organisation de la personne connectée. Le Super Admin fait exception, et chacun de ses accès est audité.

**Conséquences :**
- Un objet d'une autre Organisation répond 404, sans aucune donnée.
- Un test d'isolement, généré depuis la table des routes, prouve qu'un membre de A ne lit, ne liste ni ne modifie rien de B (NFR-18).

#### FR-47 : Organisation responsable d'un Signalement

L'Organisation responsable est déduite de la Position à la réception : la commune ou l'opérateur `active` dont la Zone couvre la Position, en prenant la Zone la plus précise. À défaut, c'est l'Organisation plateforme.

**Conséquences :**
- L'Organisation responsable est fixée à la création et ne change plus.
- Elle n'est jamais renvoyée au Citoyen.

#### FR-48 : Vérification par une organisation

Un Collecteur est vérifié par l'Organisation (commune, opérateur, groupement de collecteurs ou plateforme) dont il est membre. Un Recycleur, un Gestionnaire d'entreprise et l'Administrateur initial d'une Organisation sont vérifiés par la plateforme.

### 4.14 Super Admin et plateforme

**Description.** L'équipe TerangaCycle ouvre et suit les Organisations clientes, leurs Contrats et leurs Factures, sans encaisser. Réalise UJ-8.

#### FR-49 : Super Admin

Le Super Admin est membre de l'Organisation plateforme. Il est distinct de l'Administrateur d'organisation. Le premier Super Admin est créé par une commande d'exploitation.

**Conséquences :**
- Le Second facteur est obligatoire avec des données réelles (FR-43).
- Chaque accès aux données d'une autre Organisation est inscrit au Journal d'audit.

#### FR-50 : Organisations clientes

Le Super Admin crée, modifie, suspend et réactive une Organisation, et nomme son premier Administrateur.

#### FR-51 : Contrats et abonnements

Un Contrat lie une Organisation à une offre : prix mensuel, dates et statut. Il porte aussi les paramètres commerciaux (frais de coordination, rémunération, commission, droit de vendre des Lots).

**Conséquences :**
- Les valeurs sont saisies en base par le Super Admin. Aucune valeur n'est dans le code, la configuration versionnée ni ce document.
- Les montants sont des entiers en FCFA.

#### FR-52 : Factures et échéances (états)

Le système émet une Facture par Contrat et par période, avec un montant, un statut (`émise`, `payée`, `en retard`) et une référence. Le Super Admin marque une Facture `payée` avec sa référence.

**Conséquences :**
- Aucun encaissement, aucune passerelle de paiement.
- Une Facture `émise` dont l'échéance est dépassée passe `en retard` (tâche planifiée), et une alerte part.

#### FR-53 : Tableau de bord plateforme

Le Super Admin voit les indicateurs SM-B1 à SM-B8 (§10), par période et par Organisation.

#### FR-54 : Paramètres et Journal d'audit global

Le Super Admin règle les paramètres non commerciaux de la plateforme et consulte le Journal d'audit de toutes les Organisations, filtrable par Organisation, action et période.

### 4.15 Espaces

#### FR-55 : Espace mobile et console web

Une seule application propose deux espaces, chargés séparément : l'Espace mobile `/` (Citoyen, Collecteur) et la Console web `/console` (Personnel, Gestionnaire d'entreprise, Recycleur, Super Admin).

**Conséquences :**
- Après la connexion, chacun arrive dans son espace. Une personne qui a plusieurs Appartenances de console choisit l'Organisation active.
- Le budget de NFR-5 s'applique à l'Espace mobile seul ; la console n'y est ni chargée ni précachée.

### 4.16 Espace entreprise

**Description.** Une entreprise fait collecter ses déchets et prouve ce qui a été collecté. Réalise UJ-7.

#### FR-56 : Sites

Le Gestionnaire d'entreprise gère les Sites de son entreprise : nom, Position dans la Zone active, contact du site.

#### FR-57 : Déchets déclarés

Pour chaque Site, il déclare les Types de déchet produits et un volume estimé par période.

#### FR-58 : Demande de collecte ponctuelle

Il demande une collecte pour un Site (Types de déchet, volume estimé, créneau souhaité). La Demande crée une Mission d'Origine `collection_request`.

**Conséquences :**
- La Mission est ouverte aux Collecteurs vérifiés par l'Organisation plateforme et par les opérateurs désignés comme prestataires dans le Contrat de l'entreprise.
- Une Demande n'a pas de modération citoyenne ; son statut suit celui de la Mission.

#### FR-59 : Programme de collecte

Il programme des collectes régulières (fréquence, Site, Types de déchet). Une tâche planifiée crée les Demandes à échéance, sans doublon.

#### FR-60 : Suivi des demandes, des prestataires et des preuves

Il suit ses Demandes et leurs Missions : le Collecteur (nom affiché et état de vérification, jamais son numéro), les Preuves (photos, Poids déclaré, méthode) et les kg vérifiés par Site.

#### FR-61 : Rapports mensuels

L'entreprise, et la commune ou l'opérateur, téléchargent un rapport mensuel (kg vérifiés par Type de déchet et par Site ou quartier, Missions terminées, Preuves contestées), sans donnée personnelle.

### 4.17 Finance terrain (aucune détention de fonds)

**Description.** Le système enregistre ce qui est dû, payé ou contesté ; le client paie lui-même le collecteur. Réalise UJ-9.

#### FR-62 : Frais et rémunération prévus

À sa création, une Mission reçoit ses Frais de coordination et sa Rémunération prévue, calculés depuis les paramètres du Contrat de son Organisation.

**Conséquences :**
- Les valeurs sont figées sur la Mission : un changement de Contrat ne modifie pas les Missions existantes.

#### FR-63 : Montant dû

Une Preuve acceptée crée un Montant dû au Collecteur (Mission, Collecteur, montant, payeur, statut `dû`).

#### FR-64 : Paiement confirmé

Le payeur (l'Organisation cliente) enregistre le paiement : Référence de paiement, date, personne qui confirme. Le Montant passe `payé`.

**Conséquences :**
- TerangaCycle ne reçoit, ne détient et ne transfère aucun fonds ; aucune route ne déplace d'argent.
- Toute transition est inscrite au Journal d'audit.

#### FR-65 : Montants du Collecteur

Le Collecteur voit ses Montants dus et payés, et conteste un Montant avec un motif obligatoire, ce qui ouvre un Litige.

#### FR-66 : Litiges

Un Litige porte sur un objet (Preuve, Montant dû, Vente), avec un motif, un statut (`ouvert`, `en instruction`, `tranché`) et une décision motivée du Super Admin.

**Conséquences :**
- Un Montant `contesté` n'est ni `dû` ni `payé` tant que le Litige est ouvert.

#### FR-67 : Suivi des montants

L'Organisation voit ses Montants dus, payés et contestés ; le Super Admin les voit tous. Les deux peuvent les exporter, sans Référence de paiement complète.

## 5. Exigences non fonctionnelles transverses

| ID | Domaine | Exigence | Seuil | Vérification |
|---|---|---|---|---|
| NFR-1 | Performance | Classification locale | < 3 s sur un Android 2 Go | Chronométrage sur 20 photos |
| NFR-2 | Performance | Lecture API | p95 < 300 ms à 50 req/s | k6 |
| NFR-3 | Performance | Carte | < 2 s pour 5 000 points | Mesure manuelle et Lighthouse |
| NFR-4 | Réseau faible | Photo envoyée | ≤ 300 Ko | Test automatique |
| NFR-5 | Réseau faible | Espace mobile | ≤ 500 Ko hors images et Modèle ; Modèle ≤ 8 Mo, téléchargé une seule fois puis mis en cache ; la console n'est ni chargée ni précachée par l'Espace mobile | Lighthouse ; contrôle CI du manifeste de construction |
| NFR-6 | Compatibilité | Appareils | Android 8+ avec Chrome, 2 Go de RAM ; mobile 390×844 ; console 1280×800, navigation complète au clavier | Test sur un appareil réel |
| NFR-7 | Disponibilité | Démo | Service et portable de secours prêts ; vidéo de la démo complète enregistrée avant H60 ; tuiles de la zone de démo disponibles sans réseau ; `/healthz` répond tant que le processus vit ; `/readyz` n'est prêt que si la base, le stockage et le Modèle sont disponibles et ne renvoie qu'un statut global ; hors Mode démonstration, `/docs` et `/openapi.json` ne sont pas exposés | Répétition ; test automatisé des sondes et de l'exposition |
| NFR-8 | Sécurité | Transport et en-têtes | TLS 1.2 minimum, HSTS, redirection HTTP → HTTPS ; CSP dont `script-src` n'autorise que `'self'` et `'wasm-unsafe-eval'` ; `X-Content-Type-Options: nosniff` ; `Referrer-Policy: no-referrer` ; CORS limité aux origines de la PWA ; photos servies depuis un domaine distinct de l'API | Scan SSL et test des en-têtes |
| NFR-9 | Sécurité | Contrôle d'accès | Toutes les routes `/v1` testées × chaque rôle de §2.4 (Collecteur et Recycleur, vérifiés ou non) et sans jeton, sauf une liste blanche publique explicite (`/healthz`, `/readyz`, création anonyme d'un Signalement, carte publique agrégée) | CI : échec si une route n'est ni testée ni dans la liste blanche |
| NFR-10 | Sécurité | Chaîne logicielle | Aucun secret dans Git ; la CI échoue sur toute vulnérabilité critique ou haute non justifiée dans un fichier d'exceptions daté ; images épinglées par empreinte et actions par SHA de commit | Gitleaks, pip-audit, npm audit, Trivy en CI |
| NFR-11 | Qualité | Code | Couverture backend ≥ 60 %, lint sans erreur | CI |
| NFR-12 | Accessibilité | WCAG 2.1 AA | Contraste ≥ 4,5:1 pour le texte (3:1 pour le texte ≥ 18,66 px gras et les éléments non textuels) ; cibles tactiles ≥ 44 px ; libellés pour lecteurs d'écran ; chaque Type de déchet, chaque étape de la Frise de suivi et chaque action principale a un pictogramme accompagné d'un libellé ; navigation complète au clavier sur les écrans du Personnel | Script CI qui calcule chaque paire texte/fond des jetons ; audit Lighthouse |
| NFR-13 | Langue | Interface | Français d'abord ; aucune chaîne en dur (wolof prêt à ajouter) | Revue de code |
| NFR-14 | Observabilité | Journaux | Journaux structurés avec identifiant de requête, rôle, route et durée ; jamais de jeton, de numéro complet ni de Référence de paiement complète | Revue des journaux |
| NFR-15 | Continuité (pilote) | Sauvegarde et restauration | Sauvegarde quotidienne chiffrée de la base et des photos, hors du serveur hôte ; perte maximale de 24 h ; une restauration complète réussie avant la collecte de données réelles ; disponibilité visée de 99 % par mois | Exercice de restauration ; supervision |
| NFR-16 | Supervision (pilote) | Alertes | Une alerte part sur le canal de l'équipe si : le taux de réponses 5xx dépasse 2 % sur 5 min ; une sauvegarde échoue ou le disque est rempli à plus de 85 % `[ASSUMPTION]` ; le plafond SMS est atteint (FR-1) ; la file de Classification serveur est pleine (FR-14) | Déclenchement simulé de chaque alerte |
| NFR-17 | Sécurité | Données au repos et base | Base, photos et sauvegardes chiffrées au repos (pilote) ; l'API se connecte avec un rôle qui ne peut ni modifier le schéma, ni modifier ou supprimer une entrée du Journal d'audit ; aucune colonne ne contient le numéro de téléphone en clair | Test CI (création de table et mise à jour du Journal refusées) ; recherche du numéro en clair dans une copie de la base |
| NFR-18 | Sécurité | Isolement entre organisations | Pour chaque route qui manipule un objet d'Organisation, aucune lecture, liste ni écriture croisée entre deux Organisations | CI : test généré à deux Organisations ; échec si une route n'est pas couverte |

## 6. Confidentialité, sécurité et conformité

### 6.1 Données personnelles (minimisation)

**Données collectées :**
- un numéro de téléphone, seulement pour les comptes ;
- la Position du Signalement ;
- la photo du Signalement et les photos de la Preuve de collecte ;
- la Position du Collecteur dans la Preuve de collecte ;
- l'empreinte de l'Identifiant d'appareil ;
- l'IP, dans le Journal d'audit et pour la limitation de débit ;
- **(v2.0)** les Sites d'entreprise (Position et contact du site), les Montants dus et les Références de paiement, le contact des vendeurs de Lots et des Recycleurs.

Les Références de paiement ne sont visibles que du payeur, du Collecteur concerné et du Super Admin. Le contact d'un vendeur n'est donné qu'au Recycleur qui a réservé son Lot.

**Protection :**
- le numéro est chiffré au repos, et la recherche passe par une empreinte calculée avec une clé secrète ;
- les photos sont privées et ne sont servies que par des liens temporaires de 5 minutes ;
- les Positions précises sont réservées au Personnel et au Collecteur de la Mission (FR-24) ;
- au pilote, la base, les photos et les sauvegardes sont chiffrées au repos, avec des clés contrôlées par l'organisation (NFR-17).

| Donnée | Durée de conservation `[ASSUMPTION : à valider avec la commune]` |
|---|---|
| Photos de Signalement | 12 mois |
| Photos de Signalements `rejeté` | 30 jours ; 24 h si personne ou plaque visible (FR-23) |
| Photos de Preuve de collecte | 12 mois |
| IP du Journal d'audit | 6 mois |
| Compte supprimé | Purgé sous 30 jours |
| Statistiques agrégées | Sans limite |
| Pièces financières (Factures, Montants, Ventes) | Durée légale comptable `[ASSUMPTION : à confirmer]` |

Une tâche planifiée applique ces durées. Test avec une horloge simulée : une photo plus ancienne que sa durée est supprimée et son lien ne fonctionne plus ; une IP de plus de 6 mois est effacée du Journal d'audit.

### 6.2 Abus et fraude

| Menace | Contrôle exigé |
|---|---|
| Spam | FR-10, File de modération, Doublon probable (distance, délai, photo identique) |
| Fausses preuves | FR-29 (150 m, horodatage serveur, photos), FR-41 (échantillon d'au moins 5 %, photos réutilisées) |
| Fraude aux SMS | FR-1 (limites et plafond de SMS) |
| Fichier piégé | FR-8 |
| Accès indus | FR-3 |
| Accès indus au Personnel | FR-43 |
| Fuite par renvoi | FR-9 |
| Mode démonstration oublié en production | FR-6 |
| Faux paiement confirmé | FR-64 à FR-66 (double vue payeur et Collecteur, contestation, Litige) |
| kg gonflés ou réutilisés dans un Lot | FR-38, FR-71, FR-68 |
| Accès entre organisations | FR-46, NFR-18 |

### 6.3 Conformité

- **Loi sénégalaise n° 2008-12 sur les données personnelles et CDP :**
  - aucune obligation pour la démo : elle n'utilise que des comptes de test et des Données de démonstration, y compris les Signalements créés en direct (FR-37), dont les photos ne montrent ni personne ni plaque ;
  - pour le pilote, déclaration ou demande d'autorisation à la CDP avant la collecte de données réelles ;
  - tout hébergement hors du Sénégal (pilote AWS) est un transfert à couvrir dans ce dossier.
- **Aucune détention de fonds :** TerangaCycle n'encaisse aucun fonds pour compte de tiers. Un avis juridique sur la réglementation de la BCEAO est requis avant toute évolution vers un encaissement (§11, Q20). La facturation (forme juridique, TVA) est une question ouverte (§11, Q17).
- **WCAG 2.1 AA :** NFR-12.
  - Le jeton Vert `#1F8A5B` de la maquette est remplacé par `#187A50` dans toutes ses utilisations : fond sous texte blanc (5,33:1), texte sur Fond (5,06:1), pastilles sur Menthe (4,70:1).
  - Le Rouge `#D9482B` (4,28:1 sur blanc) n'est utilisé que pour des aplats, icônes et bordures, ou pour un texte d'au moins 18,66 px en gras ; un message d'erreur s'écrit en Encre avec une icône rouge.
  - Le Jaune `#F2B705` n'est jamais une couleur de texte : il sert de fond sous un texte Encre. Un avertissement textuel utilise Ambre `#7A5C00` sur `#FFF4CC`.
- **Licence ouverte du code** : MIT ou AGPL-3.0 ; fichier `LICENSE` à la racine du dépôt avant la démo (§11, Q1).
- **Licences des jeux de données d'entraînement** (TrashNet, TACO) : listées dans la Fiche du Modèle.

### 6.4 Souveraineté

- Aucune API d'IA hébergée : le Modèle appartient au projet.
- Données exportables en formats ouverts.
- Déploiement par conteneurs, portable d'un hébergeur à l'autre.
- Plan de sortie vérifiable vers un hébergement au Sénégal : export complet de la base et des photos en formats standard ; déploiement décrit par conteneurs ; clés de chiffrement contrôlées par l'organisation ; une restauration complète sur un autre hôte est réalisée avant la fin du pilote (§11, Q3).

## 7. Plateforme et identité visuelle

- **PWA installable** (pas d'application native), une seule application React avec deux espaces chargés séparément (FR-55) : l'Espace mobile `/`, mobile d'abord, et la Console web `/console`, sur ordinateur.
- **Référence visuelle :** maquette Figma (écrans 1 à 7), police Inter, jetons de couleur du brief, avec les règles d'usage du §6.3.
- **Écrans hors maquette :** la maquette Figma est figée. Les éléments suivants sont décrits dans la spécification UX, avec les mêmes jetons (corrigés) et la même police : Taille de tas (écran 3) ; variante « en attente d'envoi » de l'écran 4 ; consentement (FR-4) ; connexion OTP ; File de modération et détail d'un Signalement (UJ-2) ; administration des comptes et Journal d'audit ; bandeau Mode démonstration ; photo et filtre par Type de déchet dans la liste de l'écran 5 ; **(v2.0)** gabarit de la console et sélecteur d'Organisation ; Organisations (Super Admin) ; Membres d'une Organisation ; Alertes de fraude ; Sites, Demandes, Programmes et Rapports (entreprise) ; Contrats, Factures et Tableau de bord plateforme ; Montants du Collecteur (mobile) ; Lots, Réservations et Ventes (mobile pour le Collecteur vendeur, console pour les autres) ; Litiges. Une spécification UX légère de la console est produite avant le lot P2.
- **Libellés de la Frise de suivi** (écran 4) : « Signalé », « Validé par la modération », « Assigné à un collecteur », « Collecté, preuve photo ».
- **Entrées de rôle :** sur l'écran 1, « Je suis collecteur » mène à la connexion OTP de l'Espace mobile, et « Espace professionnel » (qui remplace « Espace commune ») à la connexion de la console.
- **Ton :** consignes courtes, en français simple, avec pictogrammes ; des messages d'erreur qui disent quoi faire. Fidèle à la *teranga* : remercier le Citoyen, ne jamais le culpabiliser ; nommer le Collecteur comme un acteur reconnu ; un refus de Preuve donne la distance mesurée, sans accuser.
- **Honnêteté :** aucun chiffre de démonstration n'est présenté comme réel, et aucun objectif comme un résultat.

## 8. Non-objectifs

- **Détention ou transfert de fonds par TerangaCycle**, et passerelle de paiement : le système enregistre des états (FR-62 à FR-67) ; le client paie le collecteur.
- Applications natives iOS et Android.
- Entraînement d'un modèle à partir de zéro, ou détection d'objets multiples.
- Optimisation de tournées multi-véhicules.
- Estimation du poids par IA : la table de Taille de tas suffit et reste corrigeable.
- Temps réel par WebSocket : rafraîchissement toutes les 15 s.
- Points citoyens et classements par quartier.
- Interface en wolof pendant le hackathon (seule la préparation à la traduction est exigée ; voir §9.2).
- Preuve de collecte hors-ligne : au MVP, le Collecteur doit avoir du réseau sur place (question rouverte pour le pilote, §11, Q8).
- Floutage automatique des visages et des plaques : après le MVP ; la consigne de capture et la modération le compensent.
- Ouverture **à grande échelle** de nombreux territoires, configuration des Types de déchet par Organisation et inscription des Organisations en libre-service : lot P4. Le cloisonnement par Organisation est, lui, dans le MVP (FR-46) ; la Zone active reste unique au MVP.
- Déclenchement automatique du réentraînement sur un seuil de Corrections : le réentraînement du pilote est manuel et mensuel (FR-16).

## 9. Périmètre et lots

### 9.0 Lots de livraison (v2.0)

La **Priorité** (lot) est l'axe de planification. Les portes H24, H48 et H60 du §9.1 ne servent plus qu'à la démo du hackathon.

| Lot | Contenu | Exigences |
|---|---|---|
| **P0 · en cours** | Finir l'Epic 1, avec l'Organisation dès la création d'un Signalement | FR-4, FR-7 à FR-10, FR-37, FR-44 (table), FR-47 |
| **Piste hackathon** | IA minimale (Modèle sur le téléphone, Seuil de confiance, Correction) et File hors-ligne | FR-11, FR-12, FR-13 (partie création), FR-17 à FR-19 |
| **P1 · MVP opérationnel** | Comptes OTP, Organisations, Appartenances, Super Admin minimal, console, audit ; modération, Statuts, notifications ; vérification des Collecteurs, Missions, Preuves, contrôle par échantillon, alertes de fraude ; Tableau de bord et exports | FR-1 à FR-3, FR-5, FR-6, FR-20 à FR-33, FR-35, FR-36, FR-41 à FR-43, FR-45, FR-46, FR-48, FR-49, FR-55, FR-68 |
| **P2 · MVP commercial** | Organisations et contrats ; espace entreprise ; finance terrain ; rapports mensuels | FR-50 à FR-54, FR-56 à FR-67 |
| **P3 · Place de marché** | Recycleurs vérifiés, Lots issus de kg vérifiés et vendus par le Collecteur, réservation, vente, commission | FR-38 à FR-40, FR-69 à FR-71 |
| **P4 · Automatisation** | Reste de l'IA (Classification serveur, pipeline d'entraînement, réentraînement) ; canal SMS citoyen ; analyses ; ouverture de nombreux territoires | FR-13 (export), FR-14 à FR-16, FR-34 si elle n'est pas tirée avant |
| **Post-pilote** | Données ouvertes et interopérabilité (exports standards, API en lecture pour partenaires) | — |

La démo du hackathon montre P0, la piste hackathon et le chemin nominal de P1. Les actions qui précèdent les premières données réelles (sauvegardes, chiffrement, restauration) conditionnent la sortie de P1.

### 9.1 Démo du hackathon (portes)

Les exigences de la démo sont livrées par porte du plan de 72 h.

| Porte | Exigences livrées | État visé |
|---|---|---|
| **H24** | FR-1 à FR-4, FR-6, FR-7 à FR-10, FR-16 (premier Modèle entraîné exporté en ONNX ; Modèle factice en repli), FR-37 | Signalement relié à la PWA |
| **H48** | FR-11 à FR-15, FR-17, FR-18, FR-22 à FR-26, FR-29, FR-36 (inscription au Journal d'audit) | Boucle signaler → modérer → collecter de bout en bout, hors-ligne compris |
| **H60** | FR-5, FR-19 à FR-21, FR-30, FR-31 à FR-33, FR-35 | Gel des fonctionnalités |

### 9.2 Hors périmètre du MVP

- **FR-27, FR-28, FR-34, FR-36 (consultation) :** seulement si la porte H48 est atteinte en avance.
- **FR-41 à FR-43 :** avant le pilote, hors des portes du hackathon.
- **FR-38 à FR-40 et FR-69 à FR-71 (place de marché) :** lot P3 (§9.0).
- **FR-50 à FR-67 (contrats, espace entreprise, finance terrain) :** lot P2 (§9.0).
  `[NOTE FOR PM]` L'incitation des Collecteurs au pilote passe par la Rémunération prévue et les Montants dus (FR-62 à FR-65) ; le payeur et la grille restent à fixer (§11, Q11). Sans elles, SM-7 est à risque.
- **Wolof :** préparation à la traduction au MVP (NFR-13) ; écran de signalement en wolof pendant le pilote (mois 3 à 6), relu par des locuteurs natifs.
- **SMS et WhatsApp :** après le pilote (mois 6 à 12, comme annoncé dans le Proposal).
- **Points citoyens** (US-07), intégration aux systèmes municipaux : feuille de route, sans échéance. Le suivi des paiements des Collecteurs est dans le lot P2 (FR-62 à FR-67).
- **Fonds de carte :** les tuiles publiques d'OpenStreetMap sont réservées à la démo ; le pilote utilise un fournisseur ou un serveur de tuiles propre.

### 9.3 Risques de démo et plans B

| Risque | Plan B exigé | Exigence liée |
|---|---|---|
| Modèle imprécis sur des photos locales | 10 photos locales préparées et testées ; la Correction est montrée comme une fonctionnalité | FR-13, SM-2 |
| Réseau instable dans la salle | Vidéo de la démo complète ; portable de secours servant de serveur ; tuiles en cache | NFR-7 |
| File hors-ligne pas prête | SM-1 commence par la séquence « mode avion » de la vidéo | FR-17, FR-18, SM-1 |
| Porte non atteinte | Couper une extension (Lots de matière, wolof) plutôt que repousser la suite | §9.1 |
| Passerelle SMS indisponible | Mode démonstration pour l'OTP | FR-6 |

## 10. Indicateurs de réussite

Ce sont des **objectifs à mesurer**, pas des résultats.

**Principaux (hackathon)**
- **SM-1** : boucle complète démontrée en direct, sur des photos réelles : signalement hors-ligne → modération → Mission → Preuve de collecte → Tableau de bord. Valide FR-7, FR-17, FR-23, FR-25, FR-29, FR-31.
- **SM-2** : qualité du Modèle sur un Jeu de test figé de photos prises au Sénégal, d'au moins 150 photos par classe, découpé par lieu et par jour, jamais utilisé pour l'entraînement.
  - Seuils : F1 macro ≥ 0,80 et rappel ≥ 0,70 par classe ; calibration ECE ≤ 0,10, condition de validité du Seuil de confiance. La top-1 accuracy est publiée en complément, face à la cible de 80 % du Proposal, avec la matrice de confusion.
  - Si le jeu n'atteint pas 150 photos par classe à H48, les chiffres sont publiés avec la taille réelle du jeu.
  - Une Fiche du Modèle est publiée avec chaque version : données et licence de chaque source, métriques, matrice de confusion, limites connues (photos sombres, tas mélangés, déchets mouillés).
  - Valide FR-11, FR-12 et FR-14.
- **SM-3** : création d'un Signalement en moins de 30 s, de l'appui sur « Signaler un dépôt » (écran 1) à l'accusé de réception (écran 4) ; médiane de 10 essais réalisés par au moins 3 personnes qui découvrent l'application, sur un Android à 2 Go de RAM. Valide FR-7, FR-11 et FR-12.
- **SM-4** : 100 % des Signalements créés en mode avion arrivent après la reconnexion, sans doublon. Valide FR-17, FR-18 et FR-9.

**Pilote de 6 mois dans une commune**
- **SM-5** : Délai médian (FR-31) de moins de 24 h. Valide FR-24 à FR-29 et FR-31.
- **SM-6** : Taux de traitement (FR-31) d'au moins 60 %, calculé sur l'ensemble des Signalements reçus pendant les 6 mois du pilote. Valide FR-25, FR-29 et FR-31.
- **SM-7** : au moins 20 Collecteurs vérifiés actifs avec un historique. Valide FR-30, FR-31 (Collecteurs vérifiés actifs) et FR-35.
- **SM-8** : la part des classifications corrigées baisse de mois en mois. Valide FR-13 et FR-16 (réentraînement mensuel).
- **SM-9** : Kg collectés avec Preuve de collecte, par Type de déchet : suivi mensuel, sans cible. Valide FR-29 et FR-31.

**Indicateurs d'activité (MVP commercial) — suivis, sans cible publiée dans ce dépôt**
- **SM-B1** : clients payants (Organisations avec un Contrat actif). Valide FR-51.
- **SM-B2** : revenu mensuel récurrent. Valide FR-51 et FR-52.
- **SM-B3** : coût moyen par collecte. Valide FR-62.
- **SM-B4** : Missions terminées. Valide FR-29.
- **SM-B5** : Preuves valides (acceptées et non contestées). Valide FR-41.
- **SM-B6** : kg vérifiés. Valide FR-41 et FR-71.
- **SM-B7** : Lots vendus. Valide FR-70.
- **SM-B8** : rémunérations versées (Montants `payé`). Valide FR-64.

**Contre-indicateurs (à ne pas optimiser)**
- **SM-C1** : nombre brut de Signalements. Le faire monter récompense le spam ; il équilibre SM-1 et SM-6.
- **SM-C2** : taux de validation en modération. Un taux proche de 100 % signale une modération de complaisance ; il équilibre SM-6.
- **SM-C3** : kg collectés par Mission. Des poids gonflés feraient monter l'indicateur ; on suit plutôt la part de Preuves `contestée` (FR-41). Il équilibre SM-5 et SM-6.
- **SM-C4** : part de classifications acceptées sans Correction. Décourager la Correction masquerait les erreurs du Modèle ; il équilibre SM-8.
- **SM-C5** : part des Montants confirmés sans aucune contestation. Une part de contestations nulle doit inquiéter autant qu'une part élevée ; il équilibre SM-B8.

## 11. Questions ouvertes

| # | Question | Responsable | Échéance | Revisiter quand |
|---|---|---|---|---|
| 1 | **Licence du code :** MIT (adoption) ou AGPL-3.0 (commun numérique) ? Un fichier `LICENSE` doit être à la racine avant la démo. | Responsable produit | H60 | À la revue de la porte H60, au plus tard |
| 2 | **Passerelle SMS au Sénégal :** couverture, coût, valeur du plafond quotidien de FR-1. Le Mode démonstration couvre le hackathon. | Responsable technique | Avant le pilote | Dès réception des offres de passerelles |
| 3 | **Région d'hébergement du pilote :** Le Cap, Paris ou hébergeur sénégalais ; latence depuis Dakar, dossier CDP, test du plan de sortie (§6.4). | Responsable technique | Avant le pilote | Dès l'accord de la commune partenaire sur le pilote |
| 4 | **Âge minimum** pour créer un compte, et relecture juridique du texte de consentement (FR-4). La démo n'utilise que des comptes de test. | Responsable produit | Avant le pilote | Avant la rédaction finale de l'écran de consentement du pilote |
| 5 | **Cadre légal :** la loi n° 2008-12 a-t-elle été remplacée ou complétée ? Durées de conservation du §6.1 à valider avec la commune. | Responsable produit | Avant le dépôt du dossier CDP | À la première réunion avec la commune partenaire |
| 6 | **Table de conversion Taille de tas → Poids estimé :** table provisoire `[ASSUMPTION]` livrée avec FR-7 ; valeurs réelles à obtenir d'un collecteur. | Responsable technique (table provisoire), responsable produit (valeurs terrain) | H24, puis avant le pilote | Dès le premier entretien avec un collecteur |
| 7 | **Collecteurs au pilote :** incitation (rémunération par la commune, GIE, reconnaissance), enrôlement des récupérateurs informels, critères de « Collecteur vérifié » (pièce d'identité obligatoire ou non). Risque direct sur SM-7. | Responsable produit, avec la commune | Avant le pilote | À la négociation de la convention de pilote avec la commune |
| 8 | **Preuve de collecte hors-ligne au pilote** (§8) : à décider après mesure de la couverture réseau des premiers sites. | Responsable technique | Fin du 1er mois du pilote | Dès que la part de Preuves refusées faute de réseau est mesurée sur les premiers sites |
| 9 | **Jeu de photos locales et Modèle :** dans le dépôt à quelle date ? (SM-2) | Responsable IA | H24 | À la revue de la porte H24 |
| 10 | ~~**Multi-commune**~~ : **fermée le 25/11/2026**, tranchée par FR-46 (cloisonnement par Organisation dès le MVP). L'ouverture à grande échelle est reprise par la Q21. | — | — | — |
| 11 | **Rémunération des Collecteurs :** qui paie, et selon quelle grille (paramètres du Contrat) ? | Responsable produit | Avant le pilote | À la négociation de la convention de pilote |
| 12 | **Prix des abonnements** par type d'Organisation (valeurs hors dépôt). | Responsable produit | Avant le lot P2 | À la première offre commerciale |
| 13 | **Frais de coordination :** forfait ou pourcentage ? | Responsable produit | Avant le lot P2 | À la première offre commerciale |
| 14 | **Commission sur les ventes de Lots :** assiette et payeur (valeur hors dépôt). | Responsable produit | Avant le lot P3 | Au premier recycleur partenaire |
| 15 | **Rôle de l'opérateur public national de gestion des déchets :** Organisation opérateur, partenaire de données ou autre. | Responsable produit | Avant le pilote | Au premier échange formel |
| 16 | **Commune et entreprises du pilote.** | Responsable produit | Avant le pilote | — |
| 17 | **Forme juridique et facturation** (TVA). | Responsable produit | Avant la première Facture réelle | — |
| 18 | **Dossier CDP et région d'hébergement** (reprend la Q3). | Responsable technique | Avant les données réelles | — |
| 19 | **Passerelle SMS :** OTP des comptes réels et canal citoyen (reprend la Q2). | Responsable technique | Avant les comptes réels | — |
| 20 | **Avis juridique BCEAO** avant tout encaissement pour compte de tiers. | Responsable produit | Avant toute évolution vers un encaissement | — |
| 21 | **Ayant droit des kg** entre Collecteur, groupement et Organisation de la Mission : règles fines au-delà de l'ordre de FR-38, et ouverture de nombreux territoires (lot P4). | Responsable produit | Avant le lot P3 | Au premier groupement vendeur |

## 12. Index des hypothèses

Seules les hypothèses encore ouvertes figurent ici. Chacune porte la mention `[ASSUMPTION]` à l'endroit cité.

- §3 Glossaire, Doublon probable : 50 m et 72 h, configurables.
- §4.1 FR-1 : seuls les numéros sénégalais (+221) sont acceptés au MVP.
- §4.1 FR-1 : 5 demandes d'OTP par Identifiant d'appareil et 20 par IP, par heure.
- §4.1 FR-1 : plafond quotidien de SMS, valeur à fixer avec la passerelle (§11, Q2).
- §4.2 FR-7 : précision maximale de 50 m avant le drapeau « position imprécise ».
- §4.2 FR-10 : 10 Signalements par heure et par compte connecté.
- §4.3 FR-14 : file de classification bornée à 500 tâches.
- §4.7 FR-42 : expiration d'une Mission à 48 h, configurable.
- §4.8 FR-29 : tolérance de 150 m plus la précision du Signalement, plafonnée à 50 m.
- §4.8 FR-41 : échantillon d'au moins 5 % des Preuves de collecte.
- §4.9 FR-33 : arrondi des Positions à 3 décimales dans l'Export agrégé (même arrondi que FR-24).
- §4.9 FR-34 : cellules de 500 m, masquées sous 3 Signalements.
- §5 NFR-16 : seuil d'alerte disque à 85 %.
- §6.1 : durées de conservation, à valider avec la commune.
- §11 Q6 : table provisoire Taille de tas → Poids estimé.
- §4.8 FR-68 : bornes du Poids déclaré qui déclenchent une Alerte de fraude, configurables.
- §6.1 : durée de conservation des pièces financières, à confirmer.
