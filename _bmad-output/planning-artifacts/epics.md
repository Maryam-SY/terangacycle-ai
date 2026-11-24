---
status: final
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-TerangaCycleAI-2026-11-23/prd.md
  - _bmad-output/planning-artifacts/prds/prd-TerangaCycleAI-2026-11-23/addendum.md
  - _bmad-output/planning-artifacts/architecture/architecture-TerangaCycleAI-2026-11-23/ARCHITECTURE-SPINE.md
  - "Maquette Figma (référence UX, lien hors dépôt)"
---

# TerangaCycle AI - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for TerangaCycle AI, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

> **Notes de lecture.**
> - Vocabulaire obligatoire : Glossaire du PRD (§3). Priorité des sources : PRD > épine d'architecture > addendum (l'épine remplace l'addendum pour les noms et formes qu'elle fixe).
> - Pas de document `bmad-ux` : décision de Mia. La référence UX est la maquette Figma figée (7 écrans, nœuds listés dans l'addendum §G, sans clé de fichier), les jetons de design (PRD §6.3 et §7, épine AD-16) et les exigences d'accessibilité et d'inclusion du PRD (NFR-12, NFR-13).
> - Portes du plan de 72 h (PRD §9) : **H24**, **H48**, **H60** = démo du hackathon ; **opt. H48** = seulement si la porte H48 est atteinte en avance ; **pilote** = avant le pilote, hors des portes du hackathon ; **extension** = Lots de matière, après H48.

## Requirements Inventory

### Functional Requirements

**4.1 Accès, identité et consentement**

- FR-1 : Un utilisateur se connecte avec son numéro de téléphone (numéros sénégalais +221 seulement) et un code OTP reçu par SMS ; le code expire après 5 min, sert une seule fois, est invalidé après 5 essais erronés et n'est jamais stocké en clair ; au plus 5 demandes/h par numéro, 5/h par Identifiant d'appareil et 20/h par IP (sinon 429 avec délai d'attente) ; un plafond quotidien de SMS configurable coupe l'envoi (503 + alerte d'équipe). — **H24**
- FR-2 : Un utilisateur connecté garde sa session 30 jours d'activité sans ressaisir de code et peut se déconnecter ; jeton d'accès ≤ 15 min ; déconnexion et révocation invalident la session côté serveur (renouvellement refusé en 401) ; la réutilisation d'un jeton de renouvellement déjà utilisé révoque toute la session ; aucun jeton dans `localStorage`, `sessionStorage` ni IndexedDB ; un jeton d'algorithme hors liste blanche, d'émetteur/audience incorrects, expiré ou de clé inconnue est refusé (401, un test par cas). — **H24**
- FR-3 : Le système applique les rôles Citoyen, Collecteur, Recycleur, Modérateur et Administrateur commune sur chaque action et vérifie la propriété de chaque objet (un Citoyen ne voit que ses Signalements ; un Citoyen anonyme ne possède que ceux créés avec son Identifiant d'appareil ; jamais d'accès par le seul Numéro de suivi ; un Collecteur ne voit jamais l'auteur) ; un test automatisé appelle chaque route × chaque rôle et sans jeton, tout accès non prévu échoue (401/403). — **H24**
- FR-4 : Avant la première capture, le Citoyen voit un écran de consentement (géolocalisation, envoi de la photo, usage des photos et Corrections pour le Modèle, consigne « ni personne ni plaque ») ; rien n'est envoyé sans acceptation ; acceptation horodatée (compte) ou mémorisée sur l'appareil (anonyme) ; le refus du réentraînement ne bloque pas le signalement ; le choix est copié sur chaque Signalement ; il est révocable à tout moment (profil ou réglages), un retrait exclut les Signalements passés et futurs des exports suivants. — **H24**
- FR-5 : Un utilisateur connecté consulte son profil et ses Signalements, change sa langue et son nom affiché, et supprime son compte : numéro effacé, requête suivante refusée (401), purge complète sous 30 jours ; photos et Positions des Signalements `en attente de modération` ou `rejeté` supprimées, Signalements ayant atteint `validé` conservés avec auteur anonymisé ; un Citoyen anonyme peut retirer depuis l'appareil d'origine un Signalement encore `en attente de modération`. — **H60**
- FR-6 : Le Mode démonstration affiche le code OTP à l'écran ; le service refuse de démarrer si le Mode démonstration est actif en configuration de production ; un bandeau « Mode démonstration » est visible sur tous les écrans tant qu'il est actif. — **H24**
- FR-43 : Un Modérateur ou un Administrateur commune se connecte avec l'OTP et un Second facteur (application d'authentification) ; sans Second facteur valide, les fonctions du Personnel sont refusées (403) ; activation et réinitialisation inscrites au Journal d'audit. — **pilote (Must avant le pilote, hors portes du hackathon)**

**4.2 Signalement citoyen**

- FR-7 : Un Citoyen, connecté ou anonyme, crée un Signalement avec photo obligatoire, Position capturée automatiquement avec précision, Taille de tas et commentaire optionnel ≤ 280 caractères ; envoi impossible sans photo, Position ou Taille de tas ; Position hors Zone active refusée dès l'écran 2, avant la photo (« TerangaCycle n'est pas encore actif ici ») et par le serveur (422) ; le serveur attribue un Numéro de suivi unique `TC-AAAA-NNNNNN` (année de réception, deux créations simultanées → deux numéros distincts) et le Statut `en attente de modération` ; Zone (quartier) déduite de la Position ; précision > 50 m → invitation à patienter, envoi possible avec drapeau « position imprécise » ; consigne « ni personne ni plaque » rappelée à chaque capture. — **H24**
- FR-8 : La photo est compressée sur l'appareil à ≤ 300 Ko (HEIC converti en JPEG) ; le serveur n'accepte que JPEG, PNG et WebP (415 sinon), refuse une image corrompue, > 12 Mpx ou > 1 Mo (413/422), la ré-encode et supprime toutes ses métadonnées (EXIF, GPS) ; une photo strictement identique à une photo déjà reçue fait du Signalement un Doublon probable. — **H24**
- FR-9 : Chaque Signalement porte un Identifiant client ; un renvoi par le même auteur ou le même appareil renvoie le Signalement existant (201 à la première réception, 200 ensuite avec le même Numéro de suivi ; 10 renvois → 1 Signalement) ; un autre utilisateur présentant le même Identifiant client reçoit 409 sans Numéro de suivi, Statut ni Position. — **H24**
- FR-10 : Limite anti-abus : 10 Signalements/h par Identifiant d'appareil ou par IP (anonyme), 10/h par compte (connecté), 60 requêtes/min pour tout Utilisateur connecté ; au-delà 429 ; l'IP retenue est celle du proxy de confiance (11 en-têtes `X-Forwarded-For` différents → 429 à la 11e) ; les compteurs survivent à un redémarrage. — **H24**

**4.3 Classification IA**

- FR-11 : Après la capture, le Modèle local affiche un Type de déchet (pictogramme + couleur) et un Score de confiance en < 3 s sur un Android 2 Go, sans réseau une fois le Modèle en cache ; si le Modèle n'est pas en cache, le Citoyen choisit lui-même le Type de déchet et aucun Désaccord IA n'est calculé. — **H48**
- FR-12 : Sous le Seuil de confiance (60 %), aucun Type de déchet n'est présélectionné et l'envoi reste impossible tant que le Citoyen n'en a pas choisi un parmi les 5 ; à 60 %, le type proposé est présélectionné (test à 59 % et 60 %). — **H48**
- FR-13 : Le Citoyen (création) et le Modérateur (validation) corrigent le Type de déchet en un toucher ; chaque Correction est enregistrée avec la prédiction d'origine, la version du Modèle et son auteur ; seules les Corrections de Signalements ayant atteint `validé` et dont l'auteur a consenti au réentraînement sont exportées comme exemples étiquetés. — **H48**
- FR-14 : Le serveur reclasse la même photo avec la même version du Modèle, en tâche de fond (création sans attente ; < 2 s p95 par photo) ; Classifications locale et serveur conservées ; le Type de déchet pré-rempli pour le Modérateur est le choix du Citoyen s'il existe, sinon la Classification serveur ; aucun Type de déchet envoyé par l'appareil ne devient définitif sans décision du Personnel ; file de classification bornée (500 tâches) : au-delà, Signalements acceptés en « classification serveur en attente ». — **H48**
- FR-15 : Un Signalement dont le Type de déchet envoyé par l'appareil diffère de la Classification serveur porte le drapeau « Désaccord IA » dans la File de modération ; pas de drapeau sans Classification locale. — **H48**
- FR-16 : Chaque classification enregistre la version du Modèle ; le Modèle (factice → entraîné → versions suivantes) est remplaçable sans changer écrans ni API ; une version n'est publiée que si elle atteint les seuils de SM-2 sur le Jeu de test figé, avec sa Fiche du Modèle ; au pilote, réentraînement au plus mensuel sur les Corrections exportables. — **H24** (premier Modèle entraîné exporté en ONNX ; Modèle factice en repli)

**4.4 File hors-ligne**

- FR-17 : Sans réseau, un Signalement complet (photo, Position, Type de déchet, Taille de tas, commentaire) est enregistré dans la File hors-ligne et l'écran 4 affiche « en attente d'envoi » ; en mode avion, 100 % des champs sont conservés même après fermeture et réouverture de l'application. — **H48**
- FR-18 : Au retour du réseau ou à l'ouverture de l'application, la File hors-ligne s'envoie automatiquement, sans doublon ; erreur temporaire (429, 5xx) → reste en file et repart plus tard ; refus définitif (4xx hors 408 et 429) → sort de la file et le Citoyen voit le motif. — **H48**
- FR-19 : Le Citoyen voit le nombre exact de Signalements en attente d'envoi (revient à 0 après synchronisation réussie) et peut relancer manuellement : « Réessayer » tente l'envoi dans la seconde, ou affiche « Toujours hors ligne » sans réseau. — **H60**

**4.5 Suivi et notifications**

- FR-20 : Un Citoyen voit la liste de ses Signalements (compte, ou appareil pour l'anonyme) avec Numéro de suivi, Statut et Frise de suivi (écrans 1 et 4) ; le Numéro de suivi apparaît sur l'écran 4 dès la réponse du serveur ; le Statut se met à jour ≤ 15 s après le changement, application ouverte ; un `rejeté` affiche son motif ; l'anonyme qui réinstalle ou efface ses données perd sa liste (l'écran de consentement l'en informe et propose un compte) ; une requête d'un autre appareil ou avec le seul Numéro de suivi ne reçoit aucune donnée. — **H60**
- FR-21 : À l'ouverture de l'application, le Citoyen (connecté ou anonyme) voit chaque changement de Statut survenu depuis sa dernière visite (Numéro de suivi, nouveau Statut, motif si `rejeté`) ; le Citoyen connecté qui l'a autorisée reçoit aussi une notification push ≤ 1 min après le changement ; pas de push pour l'anonyme, ni SMS/WhatsApp (non-objectifs MVP). — **H60**

**4.6 Modération**

- FR-22 : Un Modérateur voit la File de modération (Signalements `en attente de modération`, plus anciens d'abord, ≤ 50 par page) avec photo, Position et précision, Type de déchet envoyé par l'appareil et son Score de confiance, Classification serveur (ou « classification serveur en attente », décision possible quand même) et drapeaux Désaccord IA, Doublon probable, « faible confiance », « position imprécise » ; filtre par drapeau ; un Doublon probable renvoie vers le Signalement d'origine. — **H48**
- FR-23 : Le Modérateur valide (en confirmant ou corrigeant le Type de déchet pré-rempli, une correction étant une Correction auditée) ou rejette avec motif obligatoire ; toute transition non prévue → 409 ; chaque décision au Journal d'audit ; un Signalement n'est visible des Collecteurs qu'une fois `validé` ; un rejet « doublon » affiche au Citoyen le Numéro de suivi d'origine ; motif « Personne ou plaque visible » → photo supprimée du stockage sous 24 h, seule la décision reste au Journal. — **H48**

**4.7 Missions**

- FR-24 : Un Collecteur vérifié voit les Signalements `validé` dans un rayon de 1 à 10 km (5 km par défaut ; hors bornes → 422), triés par distance, sur carte et en liste, filtrables par Type de déchet, avec Type de déchet retenu, distance, Poids estimé, Score de confiance serveur (ou « Type confirmé par un humain » si le retenu diffère) et miniature ≤ 30 Ko (photo complète à l'ouverture) ; aucune information sur l'auteur ; avant acceptation, Position arrondie à 3 décimales et distance à 100 m près (jamais plus de 3 décimales pour un Collecteur hors Mission) ; Position précise après acceptation. — **H48**
- FR-25 : Un Collecteur vérifié accepte une Mission et le Signalement passe à `assigné` ; acceptations simultanées : une seule réussit, l'autre reçoit « Mission déjà prise » (409) ; Collecteur non vérifié → 403 ; Signalement non `validé` → 409 ; renvoi de la même acceptation par le même Collecteur → Mission existante sans erreur. — **H48**
- FR-26 : Le Collecteur annule sa Mission `active`, ou un Administrateur commune annule une Mission `active` : Mission `annulée`, Signalement de retour à `validé` ; annuler une Mission `terminée`, `annulée` ou `expirée` → 409 ; annulation auditée avec son auteur. — **H48**
- FR-27 : Depuis une Mission `active`, son Collecteur (et lui seul) ouvre l'application de cartes du téléphone centrée sur la Position précise du Signalement. — **Should, opt. H48**
- FR-28 : Un Administrateur commune assigne un Signalement `validé` à un Collecteur vérifié : Mission `active`, Signalement `assigné`, Collecteur notifié et voyant la Mission ≤ 15 s après (application ouverte) ; chaque assignation auditée. — **Should, opt. H48**
- FR-42 : Une Mission `active` sans Preuve de collecte 48 h (configurable) après son acceptation passe à `expirée` et le Signalement revient à `validé`, de nouveau visible des Collecteurs du rayon ; expiration auditée ; test à horloge simulée (48 h 01 min). — **Should, pilote**

**4.8 Preuve de collecte**

- FR-29 : Le Collecteur de la Mission soumet une Preuve (photo avant, photo après, Poids déclaré > 0 avec mention `pesé`/`estimé`, Position) horodatée par le serveur ; refus si précision du Collecteur > 50 m ou distance au Signalement > 150 m + précision du Signalement (plafonnée à 50 m), avec un message non accusateur donnant la distance mesurée et le rayon accepté ; Preuve acceptée → Mission `terminée` et Signalement `collecté` ; Mission non `active` → 409, autre Collecteur → 403 ; renvoi après coupure → Preuve déjà acceptée (une seule Preuve et un seul Poids) ; sans réseau, l'écran 6 l'indique et garde la saisie tant que l'application est ouverte (Position capturée à l'envoi ; pas de Preuve hors-ligne au MVP) ; photos de Preuve visibles du seul Collecteur de la Mission et du Personnel ; consigne « ni personne ni plaque » rappelée. — **H48**
- FR-30 : Le Collecteur voit l'historique de ses Missions (en cours et terminées) avec date, Type de déchet retenu, Poids déclaré, Statut de Mission, total des kg collectés, et les Preuves `contestée` signalées comme telles. — **H60**
- FR-41 : Chaque semaine, le système tire au hasard au moins 5 % (et au moins une) des Preuves acceptées, plus d'office toute Preuve dont une photo est identique à une photo déjà reçue ; un membre du Personnel marque chacune `confirmée` ou `contestée` (motif obligatoire) ; une Preuve `contestée` est exclue des Kg collectés et signalée dans l'historique du Collecteur, le Signalement restant `collecté` ; chaque Revue auditée ; le Tableau de bord affiche la part de Preuves `contestée` parmi les revues (SM-C3). — **Should, pilote**

**4.9 Tableau de bord commune**

- FR-31 : L'Administrateur commune voit, sur une période choisie et pour la Cohorte de cette période (horodatage serveur de réception) : Nombre de Signalements (dont ayant atteint `validé`, dont `rejeté`) ; Délai médian réception → acceptation de la Preuve (avec le nombre de Signalements encore ouverts) ; Taux de traitement (`collecté` ÷ ayant atteint `validé`, lu dans l'historique des Statuts ; jeu d'essai 6/10 → 60 %) ; Kg collectés (Preuves acceptées pendant la période, hors `contestée`, total et par Type de déchet, avec part `pesé`) ; Collecteurs vérifiés actifs ; répartition de la Cohorte par Type de déchet retenu ; un Signalement créé hors-ligne entre dans la Cohorte de sa date de réception serveur. — **H60**
- FR-32 : L'Administrateur commune voit la Carte de chaleur filtrable par période, Type de déchet et Statut, affichée en < 2 s pour 5 000 Signalements. — **H60**
- FR-33 : L'Administrateur commune télécharge un Export agrégé CSV et GeoJSON sans numéro, nom ni identifiant d'auteur, Positions arrondies à 3 décimales. — **H60**
- FR-34 : Tout Visiteur voit une carte publique agrégée par cellule (≥ 500 m de côté, masquée sous 3 Signalements) ou par Zone, jamais un point précis ; aucune réponse publique ne contient de coordonnées de Signalement ; tant que FR-34 n'est pas livrée, aucune carte n'est accessible sans connexion. — **Should, opt. H48**

**4.10 Administration des comptes**

- FR-35 : Un Administrateur commune crée, vérifie et suspend un compte Collecteur et change le rôle d'un utilisateur ; chaque action auditée ; la requête suivante d'un compte suspendu est refusée (401). — **H60**
- FR-36 : Le système inscrit au Journal d'audit (acteur, objet, état avant/après, horodatage serveur), en ajout seul, toute transition de Statut et de Statut de Mission (expiration comprise), toute décision de modération, Correction par un Modérateur et Revue de Preuve, toute assignation manuelle, toute création/vérification/suspension/suppression de compte et tout changement de rôle, toute activation/réinitialisation du Second facteur, tout Export agrégé et export des Corrections, toute connexion du Personnel ; un test par action ; aucune route ni le rôle applicatif ne peut modifier ou supprimer une entrée. Consultation par l'Administrateur commune filtrable par action et période (Should) ; historique des Statuts visible du Personnel dans le détail d'un Signalement. — **H48 (inscription) ; consultation : Should, opt. H48**

**4.11 Données de démonstration**

- FR-37 : Un jeu de Données de démonstration (Zones de Dakar, comptes de test de chaque rôle dont au moins un Collecteur vérifié, un Modérateur et un Administrateur commune, Signalements à divers Statuts) se charge et se retire en une commande ; tout écran affichant des Données de démonstration porte l'étiquette « Données de démonstration » ; en Mode démonstration, tout Signalement, Mission et Preuve créés sont automatiquement étiquetés. — **H24**

**4.12 Lots de matière (extension, après H48)**

- FR-38 : Un Collecteur déclare un Lot de matière (Type de déchet, poids > 0, Zone, photo ; sinon 422), créé au Statut de Lot `disponible`. — **Should, extension**
- FR-39 : Un Recycleur consulte les Lots `disponible`, filtrés par Type de déchet, Zone et poids minimal ; aucune réponse de liste ne contient le numéro ni le nom du Collecteur ; contact donné seulement après une demande. — **Should, extension**
- FR-40 : Un Recycleur réserve un Lot, qui passe à `réservé` (réserver un Lot déjà `réservé` → 409) ; le Collecteur voit la réservation ≤ 15 s après, application ouverte. — **Could, extension**

### NonFunctional Requirements

**NFR du PRD (§5)**

- NFR-1 : Performance — Classification locale < 3 s sur un Android 2 Go (chronométrage sur 20 photos).
- NFR-2 : Performance — Lecture API p95 < 300 ms à 50 req/s (k6).
- NFR-3 : Performance — Carte < 2 s pour 5 000 points (mesure manuelle et Lighthouse).
- NFR-4 : Réseau faible — Photo envoyée ≤ 300 Ko (test automatique).
- NFR-5 : Réseau faible — Page d'accueil ≤ 500 Ko hors images et Modèle ; Modèle ≤ 8 Mo, téléchargé une seule fois puis mis en cache (Lighthouse).
- NFR-6 : Compatibilité — Android 8+ avec Chrome, 2 Go de RAM ; mobile 390×844, tableau de bord 1280×800 (test sur appareil réel).
- NFR-7 : Disponibilité (démo) — Service et portable de secours prêts ; vidéo de la démo complète avant H60 ; tuiles de la zone de démo disponibles sans réseau ; `/healthz` répond tant que le processus vit ; `/readyz` prêt seulement si base, stockage et Modèle disponibles, statut global seul ; hors Mode démonstration, `/docs` et `/openapi.json` non exposés (répétition ; test automatisé des sondes et de l'exposition).
- NFR-8 : Sécurité (transport et en-têtes) — TLS 1.2 minimum, HSTS, redirection HTTP → HTTPS ; CSP avec `script-src 'self' 'wasm-unsafe-eval'` uniquement ; `X-Content-Type-Options: nosniff` ; `Referrer-Policy: no-referrer` ; CORS limité aux origines de la PWA ; photos servies depuis un domaine distinct de l'API (scan SSL, test des en-têtes).
- NFR-9 : Sécurité (contrôle d'accès) — Toutes les routes `/v1` testées × chaque rôle et sans jeton, sauf liste blanche publique explicite (`/healthz`, `/readyz`, création anonyme d'un Signalement, carte publique agrégée) ; la CI échoue si une route n'est ni testée ni dans la liste blanche.
- NFR-10 : Sécurité (chaîne logicielle) — Aucun secret dans Git ; CI en échec sur toute vulnérabilité critique ou haute non justifiée dans un fichier d'exceptions daté ; images épinglées par empreinte, actions par SHA de commit (Gitleaks, pip-audit, npm audit, Trivy).
- NFR-11 : Qualité — Couverture backend ≥ 60 %, lint sans erreur (CI).
- NFR-12 : Accessibilité — WCAG 2.1 AA : contraste ≥ 4,5:1 pour le texte (3:1 pour le texte ≥ 18,66 px gras et les éléments non textuels) ; cibles tactiles ≥ 44 px ; libellés pour lecteurs d'écran ; pictogramme + libellé pour chaque Type de déchet, chaque étape de la Frise de suivi et chaque action principale ; navigation complète au clavier sur les écrans du Personnel (script CI calculant chaque paire texte/fond des jetons ; audit Lighthouse).
- NFR-13 : Langue — Français d'abord ; aucune chaîne en dur, wolof prêt à ajouter (revue de code).
- NFR-14 : Observabilité — Journaux structurés avec identifiant de requête, rôle, route et durée ; jamais de jeton ni de numéro complet (revue des journaux).
- NFR-15 : Continuité (pilote) — Sauvegarde quotidienne chiffrée de la base et des photos hors du serveur hôte ; perte maximale 24 h ; restauration complète réussie avant toute donnée réelle ; disponibilité visée 99 %/mois (exercice de restauration ; supervision).
- NFR-16 : Supervision (pilote) — Alerte sur le canal de l'équipe si taux de 5xx > 2 % sur 5 min, échec de sauvegarde, disque > 85 %, plafond SMS atteint (FR-1), file de Classification serveur pleine (FR-14) (déclenchement simulé de chaque alerte).
- NFR-17 : Sécurité (données au repos et base) — Base, photos et sauvegardes chiffrées au repos (pilote) ; l'API se connecte avec un rôle qui ne peut ni modifier le schéma, ni modifier/supprimer une entrée du Journal d'audit ; aucune colonne ne contient le numéro de téléphone en clair (test CI : création de table et mise à jour du Journal refusées ; recherche du numéro en clair dans une copie de la base).

**Exigences transverses du PRD (§6 Confidentialité, sécurité, conformité, souveraineté)**

- NFR-6.1a : Minimisation — Seules sont collectées : numéro de téléphone (comptes seulement), Position du Signalement, photos du Signalement et de la Preuve, Position du Collecteur dans la Preuve, empreinte de l'Identifiant d'appareil, IP (Journal d'audit et limitation de débit).
- NFR-6.1b : Protection des données personnelles — Numéro chiffré au repos, recherche par empreinte à clé secrète ; photos privées servies uniquement par liens temporaires de 5 min ; Positions précises réservées au Personnel et au Collecteur de la Mission ; au pilote, base, photos et sauvegardes chiffrées avec des clés contrôlées par l'organisation.
- NFR-6.1c : Conservation — Photos de Signalement 12 mois ; photos de Signalements `rejeté` 30 jours (24 h si personne ou plaque visible) ; photos de Preuve 12 mois ; IP du Journal d'audit 6 mois ; compte supprimé purgé sous 30 jours ; statistiques agrégées sans limite (durées à valider avec la commune). Appliquées par une tâche planifiée ; test à horloge simulée : photo échue supprimée et lien inopérant, IP de plus de 6 mois effacée.
- NFR-6.2 : Abus et fraude — Contrôles exigés : spam (FR-10, modération, Doublon probable), fausses preuves (FR-29, FR-41), fraude aux SMS (FR-1), fichier piégé (FR-8), accès indus (FR-3, FR-43), fuite par renvoi (FR-9), Mode démonstration oublié en production (FR-6).
- NFR-6.3a : Conformité CDP (loi n° 2008-12) — Démo sur comptes de test et Données de démonstration uniquement ; déclaration ou autorisation CDP avant toute donnée réelle du pilote ; tout hébergement hors Sénégal traité comme transfert dans le dossier.
- NFR-6.3b : Conformité WCAG / jetons — Vert `#187A50` (remplace `#1F8A5B` partout : fond sous texte blanc 5,33:1, texte sur Fond 5,06:1, pastilles sur Menthe 4,70:1) ; Rouge `#D9482B` réservé aux aplats, icônes, bordures ou texte ≥ 18,66 px gras, message d'erreur en Encre avec icône rouge ; Jaune `#F2B705` jamais en texte (fond sous Encre) ; avertissement textuel en Ambre `#7A5C00` sur `#FFF4CC`.
- NFR-6.3c : Licence — Fichier `LICENSE` (MIT ou AGPL-3.0, choix de Mia, §11 Q1) à la racine avant la démo (H60).
- NFR-6.3d : Licences des données — Licences de TrashNet, TACO et de chaque source listées dans la Fiche du Modèle.
- NFR-6.4 : Souveraineté — Aucune API d'IA hébergée ; données exportables en formats ouverts ; déploiement par conteneurs portable ; plan de sortie vérifiable vers un hébergement au Sénégal (export complet base + photos, clés détenues par l'organisation, restauration complète sur un autre hôte avant la fin du pilote).

**Contraintes produit associées (PRD §7, §8, §10)**

- NFR-P1 : Plateforme — PWA installable, mobile d'abord, tableau de bord sur ordinateur ; aucune application native.
- NFR-P2 : Honnêteté — Aucun chiffre de démonstration présenté comme réel, aucun objectif présenté comme un résultat.
- NFR-P3 : Non-objectifs à respecter (ne pas construire) — paiement réel, apps natives, entraînement from scratch / détection multi-objets, tournées multi-véhicules, estimation du poids par IA, WebSocket (rafraîchissement 15 s), points citoyens, UI wolof au hackathon, Preuve hors-ligne, floutage automatique, multi-commune, réentraînement automatique.
- NFR-SM-2 : Qualité du Modèle — Sur un Jeu de test figé (photos du Sénégal, ≥ 150/classe, découpé par lieu et par jour) : F1 macro ≥ 0,80, rappel ≥ 0,70 par classe, ECE ≤ 0,10 ; top-1 et matrice de confusion publiées ; Fiche du Modèle à chaque version.
- NFR-SM-3 : Parcours citoyen — Création d'un Signalement en < 30 s (écran 1 → écran 4), médiane de 10 essais par ≥ 3 nouveaux utilisateurs sur Android 2 Go.
- NFR-SM-4 : Fiabilité hors-ligne — 100 % des Signalements créés en mode avion arrivent après reconnexion, sans doublon.

### Additional Requirements

> Exigences techniques issues de l'épine d'architecture (et de l'addendum quand l'épine ne le remplace pas) qui pèsent sur le découpage. Références AD-n de `ARCHITECTURE-SPINE.md`.

**⚠️ Squelette de départ — Epic 1, Stories 1.1 à 1.3**

- AR-1 : **Pas de starter full-stack** (le template FastAPI officiel impose SQLModel et un autre front ; décision `.memlog.md` de l'architecture). Le **backend est écrit à la main** selon AD-1 (`backend/app/core`, `backend/app/modules/{auth,reports,missions,lots,analytics,ai,notifications}`, `reactions.py`, `main.py`, `worker.py`, `migrations/`, `scripts/`, `tests/{unit,integration,authz,architecture}`). Le **front démarre avec `create-vite` (template `react-ts`) + `vite-plugin-pwa`** (`web/src/{api,features,offline,i18n,theme}`). Plus `ml/` (dont `contract/`, `release/current.json`), `infra/` (`docker-compose.yml`, `Caddyfile`, seed de démo) et `.github/workflows/`. Versions de la Stack de l'épine épinglées dans les fichiers de dépendances (Python 3.12.16 via Docker ou `uv`, Node 26 LTS, React 19.3, Vite 8.3, vite-plugin-pwa 2.0, TypeScript 6.0.3, Tailwind 4.3 via `@tailwindcss/vite`, override `openapi-typescript` → `typescript`).
- AR-2 : **Hygiène du dépôt public (epic E0 de l'addendum, porte H24)** — `.gitignore` committé ; `TerangaCycle AI/` jamais suivi (test CI sur `git ls-files`) ; `.env.example` listant toutes les variables avec valeurs factices ; `SECURITY.md` (canal privé, délai) ; `main` protégée (PR, CI verte, pas de force push), secret scanning, push protection, Dependabot (pip, npm, Docker, Actions) ; vérification de l'absence de clé de fichier Figma avant de committer `_bmad-output/` ; `LICENSE` dès arbitrage (H60).

**Infrastructure et déploiement**

- AR-3 : Un **`docker-compose.yml` unique**, profils `demo` et `prod`, services `caddy`, `api`, `worker` (même image que l'API), `migrate` (usage unique, avant la nouvelle version), `db` (`postgis/postgis:16-3.7`, amd64 seulement), `valkey` (`valkey/valkey:9.2.0`, `appendonly yes` + volume), `garage` (`dxflrs/garage:v2.5.0`, `--single-node --default-bucket`, volumes `meta` et `data`) ; serveur et portable de secours en x86_64 ; healthcheck sans `curl`. (Squelette structurel)
- AR-4 : **Bord HTTP par Caddy seul** — une origine `APP_HOST` pour la PWA et `/v1` (pas de CORS en prod), photos sur `MEDIA_HOST` (sans cookie, `Host` conservé), tuiles sur `TILES_HOST` ; HSTS, CSP exacte d'AD-23, `nosniff`, `Referrer-Policy`, TLS ≥ 1.2, `.wasm` en `application/wasm`, pas de COOP/COEP ; `/metrics` et `/v1/ai/*` internes ; `MAX_BODY_BYTES` ; journaux d'accès sans `Authorization`, `Cookie`, `X-Device-Id`, `Idempotency-Key`, `lat`, `lng` ; `/docs`, `/redoc`, `/openapi.json` à `None` hors `dev`/`demo` ; test de chaque en-tête. (AD-23)
- AR-5 : **Configuration et modes** — tout réglage via `core.config.Settings` ; `ENV ∈ {dev, demo, prod}` ; `DEMO_MODE` seule source du Mode démonstration (exigé par `demo`, refus de démarrer en `prod`) ; un réglage nommé par seuil du PRD (dont les quatre « 50 m » : `REPORT_ACCURACY_FLAG_M`, `PROOF_REPORT_ACCURACY_CAP_M`, `PROOF_COLLECTOR_ACCURACY_MAX_M`, `DUPLICATE_RADIUS_M`) ; `GET /v1/config` public (`demo_mode`, `env`, `model_version`, polygone de la Zone active). (AD-14)
- AR-6 : **Secrets** — inventaire fixe lu depuis `/run/secrets/*` (`JWT_SIGNING_KEYS` Ed25519 par `kid`, `PHONE_PEPPER`, `DEVICE_ID_PEPPER`, `PHONE_ENC_KEYS`, `TOTP_ENC_KEY`, `VAPID_PRIVATE_KEY`, identifiants S3, `ALERT_WEBHOOK_URL`) ; `.env.secrets` hors Git au hackathon, KMS au pilote ; rotation par ajout de `kid`/`key_id` ; un secret manquant bloque le démarrage en `demo`/`prod`. (AD-26)
- AR-7 : **Publication, CI/CD et retour arrière** — image `ghcr.io/<org>/terangacycle-api:<sha>` (API + worker) et PWA statique sur `main` ; déploiement `IMAGE_TAG=<sha>` → `migrate` → `docker compose up -d` ; retour arrière par l'`IMAGE_TAG` précédent. (AD-28)
- AR-8 : **CI bloquante** — ruff, ESLint, pytest, Vitest, couverture ≥ 60 %, **import-linter** (`layers`, `acyclic_siblings`, `protected`), test **route × rôle** généré depuis la table des routes, diff OpenAPI / client généré, test doré du Modèle, intégration Valkey et Garage réels, Gitleaks (binaire), pip-audit, npm audit, Trivy (exceptions datées) ; échec sur toute image non épinglée par empreinte ou action non épinglée par SHA. (AD-1, AD-9, AD-28, NFR-10, NFR-11)

**Architecture du backend**

- AR-9 : **Frontières de module** — un module n'importe d'un autre que `app.modules.<x>.service`, selon les flèches autorisées ; routes → leur propre service ; seuls `reactions.py` et `worker.py` composent hors des flèches ; trois couches `router` → `service` → `repository` ; `core` sans règle métier. (AD-1)
- AR-10 : **Propriété des tables** — un module propriétaire unique par table (`auth` : `users`, `collector_profiles`, `refresh_tokens`, `devices`, `staff_second_factors` ; `reports` : `reports`, `report_photos`, `classifications`, `corrections`, `report_status_events`, `tracking_counters`, `weight_estimates` ; `missions` : `missions`, `proofs`, `proof_reviews` ; `lots` : `material_lots`, `lot_requests` ; `notifications` : `notifications`, `push_subscriptions` ; `core` : `audit_logs`, `audit_log_ips`, `idempotency_records`, `zones`) ; `analytics` ne possède que des vues ; noms de l'épine font foi. (AD-2)
- AR-11 : **Base de données et migrations** — Alembic seul chemin de modification du schéma ; rôles `teranga_migrator` (propriétaire) et `teranga_app` (DML, sans `UPDATE`/`DELETE` sur `audit_logs`, `DELETE` permis sur `audit_log_ips`) ; migrations expand/contract compatibles N-1 ; `recreate_analytics_views()` après toute migration touchant une table d'une vue ; test CI de refus du DDL et de la mise à jour du Journal. (AD-15, NFR-17)
- AR-12 : **Unité de travail** — une session/transaction par requête ou tâche (`contextvar`, `get_uow()`), services `@transactional` qui rejoignent la transaction, jamais de `commit`/`rollback`/`begin` dans un service ou repository ; tout effet externe (arq, push, suppression S3) par `after_commit`, abandonné au rollback ; test « exception après transition dans `accept()` → aucune écriture, tâche ni audit ». (AD-17)
- AR-13 : **Porte unique des Statuts** — `reports.service.transition()` et `missions.service.transition()` seulement : `UPDATE … WHERE status = :from` (0 ligne → 409 `invalid_transition`), ligne `report_status_events` (historique unique, source de FR-21, FR-31, FR-36), audit, effets en `after_commit` ; ordre des verrous Mission puis Signalement ; table de transitions constante testée sur chaque couple ; retrait FR-5 par `withdraw()` (pas une transition). (AD-3)
- AR-14 : **Acceptation exclusive** — index unique partiel `missions(report_id) WHERE status='active'` ; violation → 200 si Mission du même Collecteur, sinon 409 `mission_already_taken` ; aucun verrou applicatif. (AD-4)
- AR-15 : **Idempotence** — Signalements : unicité `(owner_key, client_uuid)` (`owner_key` = `user:<id>` si jeton valide, sinon `device:<hash>`) ; toute autre mutation `/v1` exige `Idempotency-Key` (400 sinon, exemptions closes `/v1/auth/*` et `POST /v1/reports`), stockée en base `idempotency_records` (rejeu si même empreinte, 422 `idempotency_key_reused` sinon, purge 24 h) ; `UNIQUE(proofs.mission_id)`. (AD-5)
- AR-16 : **Le serveur fait autorité** — horodatages (`core.clock`), Numéro de suivi, Classification serveur, distances (`ST_Distance` sur `geography`), Zone active (`ST_Covers`), Statuts ; valeurs client en colonnes `client_*`. (AD-6)
- AR-17 : **Identité et autorisation** — JWT Ed25519 15 min (`iss`, `aud`, `kid`, `sub`, `tv`, `amr`) en mémoire ; renouvellement opaque rotatif haché par famille en cookie `HttpOnly; Secure; SameSite=Strict; Path=/v1/auth` ; `X-Device-Id` 32 octets base64url (sinon 400) ; principal unique `core.security.principal()` ; autorisation `require_role` + contrôle de propriété dans le service (404) ; liste blanche publique close (`/healthz`, `/readyz`, `GET /v1/config`, `POST /v1/reports`, `GET /v1/public/map`) et routes du principal appareil testées comme un rôle. (AD-9)
- AR-18 : **Session, révocation et Second facteur** — `(status, role, token_version)` relus à chaque requête (cache Valkey 60 s) → 401 `session_revoked` ; rôle lu en base ; suspension/suppression/changement de rôle/réinitialisation MFA incrémentent `token_version` ; TOTP RFC 6238 chiffré, `STAFF_MFA_REQUIRED` vrai en prod ; `refreshSession()` unique côté PWA (promesse partagée + `navigator.locks`) ; grâce de 10 s (`refresh_superseded`). (AD-30)
- AR-19 : **Exposition des Positions** — `core.geo.expose(position, level)` avec niveaux `precise`/`approx`/`rounded`/`aggregated`/`none` calculés dans le service ; Position de recherche jamais stockée ni journalisée ; auteur et `owner_key` jamais hors du Personnel ; masquage `structlog` ; test « jamais plus de 3 décimales ». (AD-10)
- AR-20 : **Conventions d'API** — préfixe `/v1`, enveloppe d'erreur unique, codes en énumération (`core/errors/codes.py`) exportés dans l'OpenAPI et présents dans `fr.json` ; pagination `limit`/`cursor` (≤ 100) ; photos uniquement en `multipart/form-data` dans la requête de création (aucune URL présignée en écriture) ; énumérations uniques dans `core/enums.py`. (AD-11, Conventions)
- AR-21 : **Client généré** — `export_openapi.py` → `web/src/api/openapi.json` → types `openapi-typescript` → une instance `openapi-fetch` enveloppée (jeton, `X-Device-Id`, `Idempotency-Key`, erreurs) ; fichiers versionnés, CI en échec si la régénération diffère ; ESLint interdit `fetch` hors `web/src/api/` et `web/src/offline/`. (AD-11)
- AR-22 : **Travail asynchrone (arq)** — Classification serveur, miniatures, notifications, réactions en tâches arq via `after_commit` ; `job_id` normés (`classify:<report_id>:<model_version>`, `thumb:`, `notify:<status_event_id>`, `react:<event_id>`) ; effet idempotent dans le service ; `classification_status ∈ {pending, done, failed}` ; mise en file seulement sous `CLASSIFY_QUEUE_MAX` (500). (AD-8)
- AR-23 : **Tâches planifiées (liste close, `cron_jobs` arq)** — `missions.expire_due` (1 min), `reports.requeue_pending_classifications` (1 min), `reports.purge_person_visible_photos` (1 h), `retention.sweep` (1 j), `auth.purge_deleted_accounts` (1 j), `missions.sample_proofs` (lundi, `secrets.SystemRandom`), `ops.health_sweep` (1 min) ; tout « maintenant » via `core.clock.now()` (horloge simulable) ; acteur d'audit `system:<tâche>` ; Numéro de suivi par compteur annuel `INSERT … ON CONFLICT`. (AD-18)
- AR-24 : **Réactions et événements** — événements Pydantic autosuffisants (`ReportStatusChanged`, `MissionAssigned`, `AccountDeleted`, `TrainingConsentWithdrawn`, `CollectorSuspended`, `LotReserved`) émis sous `after_commit`, réactions idempotentes seulement dans `reactions.py` ; suppression de compte orchestrée (`delete_account` → `on_collector_deleted` → `detach_owner`) ; aucune FK `ON DELETE CASCADE/SET NULL` entre modules. (AD-21)
- AR-25 : **Classifications, Corrections, drapeaux** — colonnes `client_predicted_type/confidence/model_version` (+ `CHECK`), `citizen_type`, `device_type` générée ; table `classifications` unique `(report_id, model_version)` ; table `corrections` écrite à la création ou à la validation seulement ; `retained_type` seulement via `validate()` ; drapeaux en colonnes indexées (`flag_low_confidence`, `flag_imprecise_position`, `duplicate_of_report_id`, `flag_ai_disagreement` `NULL` si versions différentes). (AD-19)
- AR-26 : **Limitation de débit** — dans l'API seulement, `core.ratelimit.limit(scope)` sur Valkey (fenêtre fixe, AOF) ; uvicorn `--proxy-headers --forwarded-allow-ips=<IP Caddy>` ; Caddy remplace `X-Forwarded-For` ; portées `otp:phone`, `otp:device`, `otp:ip`, `sms:daily`, `report:device`, `report:ip`, `report:user`, `user:any` ; 429 `rate_limited` + `Retry-After` ; OTP haché en Valkey (TTL 5 min, comparaison à temps constant). (AD-20)
- AR-27 : **Port SMS** — seul `core.sms.SmsSender` envoie (`DemoSmsSender` avec `demo_otp` / `GatewaySmsSender`, selon `SMS_BACKEND`) ; plafond quotidien vérifié dans le port. (AD-14)
- AR-28 : **Stockage objet** — seul `core/storage` parle S3 (boto3 configuré pour Garage, deux clients interne/public) ; `ingest_photo()` (refus > 1 Mo ou 12 Mpx avant S3, ré-encodage JPEG sans EXIF, `sha256` des octets reçus indexé, `Image.MAX_IMAGE_PIXELS` explicite) ; clés `<kind>/<yyyy>/<mm>/<uuid>.jpg` ; miniatures ; purge par `after_commit`, nettoyage `after_rollback`, balayage des orphelins > 24 h ; bucket privé ; test d'intégration Garage en CI. (AD-13)
- AR-29 : **Journal d'audit** — `core.audit.record(...)` avec `Actor(kind, ref)` ; liste close `AuditAction` (`report.transition`, `report.correction`, `report.withdrawn`, `mission.transition`, `mission.assign`, `proof.review`, `account.create|verify|suspend|delete|role_change`, `mfa.enable|reset`, `staff.login`, `export.aggregate|corrections`, `retention.purge`), un test par action ; aucune FK vers les tables métier ; IP dans `audit_log_ips` purgée à 6 mois. (AD-25)
- AR-30 : **Consentement au réentraînement** — `POST /v1/reports` exige `consent.terms = true` (sinon 422 `consent_required`) et `consent.training` ; valeur courante chez `auth` (`users`/`devices`) ; instantané sur `reports` ; retrait via `PUT /v1/me/consent` ou `PUT /v1/device/consent` → événement `TrainingConsentWithdrawn` ; `export_corrections()` dans `reports`, audité. (AD-24)
- AR-31 : **Vues analytiques** — `v_report_facts`, `v_mission_facts`, `v_collector_facts` dans `modules/analytics/views/*.sql`, colonnes déclarées, sans donnée personnelle, avec `is_demo` (filtré hors Mode démonstration) et `contains_demo_data` dans chaque réponse ; vérifiées en CI après `alembic upgrade head` sur le jeu de démonstration. (AD-22)
- AR-32 : **Données de démonstration** — `is_demo NOT NULL DEFAULT false` sur `users`, `reports`, `missions`, `proofs`, `proof_reviews`, `material_lots`, `lot_requests`, `audit_logs` via `core.demo.flag()` ; `python -m app.cli demo load|purge` (refusé en `prod`, purge sans toucher `audit_logs`). (AD-14, FR-37)
- AR-33 : **Supervision, alertes, sauvegardes** — `core.alerts.raise_alert()` seul, codes clos (`sms_cap_reached`, `classification_queue_full`, `http_5xx_rate`, `backup_failed`, `disk_high`), canal `ALERT_WEBHOOK_URL`, anti-rafale 15 min, test simulé par alerte ; `/metrics` interne ; `/healthz` / `/readyz` (base, Valkey, stockage, `onnx_sha256`, battement worker < 60 s) ; pilote : `pg_dump -Fc` chiffré quotidien + copie du bucket hors hôte (30 j), restauration sur hôte vierge consignée, chiffrement au repos (LUKS avec Garage). (AD-27)
- AR-34 : **Journaux** — `structlog` JSON (`request_id`, `route`, `role`, `duration_ms`) avec masquage de `phone`, `token`, `otp`, `X-Device-Id` et des Positions. (AD-10, NFR-14)
- AR-35 : **Tests sur infrastructure réelle** — `pytest` sur PostGIS, Valkey et Garage en conteneurs ; aucun mock de la base pour les règles métier. (Conventions)

**PWA**

- AR-36 : **Organisation de la PWA** — un dossier par fonctionnalité dans `web/src/features/` ; tout texte par i18next (`fr.json`, `wo.json`) ; jetons dans un seul bloc `@theme` de `web/src/theme/theme.css` (ni `tailwind.config.js` ni `@config`) ; TanStack Query (rafraîchissement 15 s) ; react-leaflet + `leaflet.heat` 1.0 enveloppé par `createLayerComponent`. (AD-16)
- AR-37 : **Outbox hors-ligne** — une seule outbox Dexie, exécutée dans la fenêtre (`online`, ouverture, « Réessayer »), jamais dans le service worker ; identité figée à la mise en file (`device` sans `Authorization` ; `user:<id>` seulement avec la session de cet utilisateur, sinon « en attente de connexion ») ; backoff exponentiel plafonné seulement sur réseau/408/429/5xx ; 401 → `refreshSession()` puis un réessai ; autre 4xx → `failed` avec code affiché ; photos compressées ≤ 300 Ko avant mise en file ; Identifiant d'appareil dans la table Dexie `meta`. (AD-12, AD-9)
- AR-38 : **Runtime IA dans la PWA** — `onnxruntime-web/wasm`, `wasmPaths` locaux, `numThreads = 1`, `proxy = false` ; précache `onnx,json,wasm,mjs` avec plafond 20 Mio et test CI de présence du `.onnx`, du manifeste et de `ort-wasm-simd-threaded.{wasm,mjs}` ; Modèle chargé paresseusement par `features/classify` ; derniers Statuts vus dans Dexie (FR-21). (AD-16)

**IA et Modèle**

- AR-39 : **Contrat du Modèle** — `tc-mnv3-<semver>.onnx` + manifeste JSON validé contre `ml/contract/model-manifest.schema.json` (classes, prétraitement, `temperature`, `confidence_threshold` 0,60) ; `softmax(logits/temperature)` et `needs_user_choice` des deux côtés ; interface `classify(image)` commune au Modèle entraîné et au Modèle factice (`0.0.0-stub`) ; test doré CI sur 20 images × 3 chaînes (écart ≤ 0,01, même `predicted_type`). (AD-7)
- AR-40 : **Distribution du Modèle** — `ml/release/current.json` seule source de version ; artefacts en assets de release GitHub `model-v<semver>` téléchargés par le Dockerfile et le build Vite (vérif. `onnx_sha256`), aucun `.onnx` dans Git ; CI en échec si les versions API/PWA diffèrent ; worker garde la version précédente 30 j ; PWA met à jour son service worker si `GET /v1/config` diffère ; `MODEL_VERSION=0.0.0-stub` en `dev`/`demo`. (AD-29)
- AR-41 : **Chaîne `ml/`** — MobileNetV3-Large par défaut (Small si NFR-1 > 3 s à la mesure H24), 5 classes, ONNX INT8 QDQ statique ≤ 8 Mo (~200 images de calibration) ; prétraitement unique (petit côté 256, recadrage 224, normalisation ImageNet) ; calibration par température ; découpage par lieu et par jour ; Jeu de test figé ; annotation avec double vérification de 20 % ; Fiche du Modèle ; réentraînement manuel mensuel au pilote. (Addendum §D, SM-2)

**Infrastructure de notification**

- AR-42 : **Web Push** — module `notifications` (`notifications`, `push_subscriptions`), clé `VAPID_PRIVATE_KEY`, émission par réaction à `ReportStatusChanged`, idempotente sur `status_event_id`. (AD-8, AD-21, FR-21)

**Points différés (ne pas planifier au MVP)**

- AR-43 : Différés par l'épine — découpage en services, multi-commune, temps réel SSE/WebSocket, orchestrateur, chaîne de réentraînement automatisée, Preuve hors-ligne, Leaflet 2/MapLibre, remplacement d'arq, outbox d'événements transactionnelle (pilote), ORT multi-thread, rattachement des Signalements anonymes à un compte ; **à mesurer avant la démo** : budget de premier chargement (WASM ≈ 15 Mo + Modèle) en 3G.

### UX Design Requirements

> Source : maquette Figma figée (écrans 1 à 7 ; nœuds 1:2 Accueil, 1:39 Capture, 1:57 Résultat IA, 1:97 Confirmation, 2:2 Missions, 2:35 Preuve, 2:65 Tableau de bord — addendum §G), jetons corrigés (PRD §6.3, §7 ; épine AD-16), NFR-12, NFR-13. Les UX-DR marqués **[HORS MAQUETTE — à concevoir]** n'existent pas dans Figma et devront être conçus avec les mêmes jetons et la police Inter.

**Fondations du système de design**

- UX-DR-1 : **Thème Tailwind unique** — un seul bloc `@theme` dans `web/src/theme/theme.css` déclarant la police Inter et les jetons du brief : Vert foncé `#0B3D2E`, Vert (marque) `--color-brand-600: #187A50` (jamais `#1F8A5B`), Jaune `#F2B705`, Menthe `#EAF3EC`, Encre `#14231C`, Gris `#5E7168`, Ligne `#D5E3D9`, Fond `#F6FAF7`, Ambre `#7A5C00` sur `#FFF4CC`, Rouge `#D9482B` ; aucune couleur codée hors du thème. *(Valeurs autres que Vert, Rouge, Jaune et Ambre : issues du brief, à confirmer contre la maquette.)*
- UX-DR-2 : **Règles d'usage des couleurs et script de contraste CI** — Rouge seulement en aplat, icône, bordure ou texte ≥ 18,66 px gras ; message d'erreur en Encre + icône rouge ; Jaune jamais en texte (fond sous Encre, ex. statut « en attente ») ; avertissement textuel en Ambre sur `#FFF4CC` ; un script CI calcule chaque paire texte/fond déclarée et échoue sous 4,5:1 (3:1 pour grand texte et éléments non textuels).
- UX-DR-3 : **Pictogrammes et couleurs des 5 Types de déchet** — composant unique (badge + sélecteur) pour plastique, métal, verre, organique, mixte : pictogramme + libellé i18n + couleur, chaque couleur respectant 3:1 (élément non textuel) et le texte associé 4,5:1 ; utilisé sur les écrans 3, 5, 7, File de modération et Lots. *(Couleurs par type non spécifiées dans les sources : à fixer et valider.)*
- UX-DR-4 : **Composant Frise de suivi** — 4 étapes avec pictogramme + libellé : « Signalé », « Validé par la modération », « Assigné à un collecteur », « Collecté, preuve photo » ; étape courante distinguée autrement que par la couleur ; `rejeté` remplace les étapes suivantes et affiche son motif (et le Numéro de suivi d'origine pour un doublon) ; aucune frise pour un Signalement en attente d'envoi ; lisible par lecteur d'écran (liste ordonnée, état courant annoncé).
- UX-DR-5 : **Bandeau « Mode démonstration »** — visible sur tous les écrans (citoyen, collecteur, Personnel) tant que `GET /v1/config` renvoie `demo_mode = true`, non masquable, contraste AA. [HORS MAQUETTE — à concevoir]
- UX-DR-6 : **Étiquette « Données de démonstration »** — affichée sur tout écran, carte, élément de liste, indicateur ou export qui contient des données `is_demo` / `contains_demo_data` ; aucun chiffre de démonstration présenté comme réel. [HORS MAQUETTE — à concevoir]
- UX-DR-7 : **Cibles tactiles et libellés** — toute cible tactile ≥ 44 × 44 px ; chaque action principale a pictogramme + libellé texte ; libellés accessibles (`aria-label`/texte visible) sur icônes, champs, photos (texte alternatif) ; navigation complète au clavier et focus visible sur les écrans du Personnel ; audit Lighthouse accessibilité.
- UX-DR-8 : **i18n fr/wo** — aucune chaîne en dur : écrans, libellés d'énumérations (Statuts, Types de déchet, Tailles de tas, motifs de rejet), messages d'erreur `errors.<code>` pour chaque code d'API dans `fr.json` ; `wo.json` présent et prêt à remplir ; sélecteur de langue dans le profil ; formats de date et de nombre localisés.
- UX-DR-9 : **Gabarits responsive** — parcours citoyen et collecteur conçus mobile d'abord en 390×844 (Android 8+ Chrome, 2 Go) ; Tableau de bord et écrans du Personnel en 1280×800 ; aucun débordement horizontal.
- UX-DR-10 : **Ton et messages** — consignes courtes en français simple avec pictogrammes ; chaque message d'erreur dit quoi faire ; remercier le Citoyen, ne jamais le culpabiliser ; nommer le Collecteur comme acteur reconnu ; refus de Preuve formulé avec la distance mesurée, sans accuser.

**Écrans de la maquette Figma**

- UX-DR-11 : **Écran 1 · Accueil** (nœud 1:2) — bouton principal « Signaler un dépôt » ; entrées de rôle « Je suis collecteur » et « Espace commune » menant à la connexion OTP ; liste « Mes Signalements » (Numéro de suivi, Statut, Frise) ; compteur des Signalements en attente d'envoi avec bouton « Réessayer » ; changements de Statut depuis la dernière visite (FR-21) ; bandeau/étiquette démo si applicable.
- UX-DR-12 : **Écran 2 · Capture** (nœud 1:39) — viseur photo ; consigne « ni personne ni plaque » à chaque capture ; Position détectée avec précision en mètres ; invitation à patienter si précision > 50 m avec possibilité d'envoyer quand même ; message « TerangaCycle n'est pas encore actif ici » avant la photo si hors Zone active ; compression ≤ 300 Ko et conversion HEIC transparentes.
- UX-DR-13 : **Écran 3 · Résultat IA** (nœud 1:57) — Type de déchet proposé avec pictogramme, couleur et Score de confiance en % ; présélection seulement si score ≥ 60 %, sinon aucun type présélectionné et consigne de choisir ; sélecteur des 5 types en un toucher (Correction) ; état « Modèle non disponible, choisissez le type » si le Modèle n'est pas en cache ; sélecteur de Taille de tas (UX-DR-14) ; commentaire optionnel 280 caractères avec compteur ; bouton d'envoi désactivé tant qu'un champ obligatoire manque.
- UX-DR-14 : **Sélecteur de Taille de tas** (petit, moyen, grand) avec pictogramme + libellé, cibles ≥ 44 px, intégré à l'écran 3. [HORS MAQUETTE — à concevoir]
- UX-DR-15 : **Écran 4 · Confirmation** (nœud 1:97) — accusé de réception avec remerciement, Numéro de suivi `TC-AAAA-NNNNNN` dès la réponse serveur, Frise de suivi à l'étape « Signalé », retour à l'accueil.
- UX-DR-16 : **Variante « en attente d'envoi » de l'écran 4** — accusé immédiat sans réseau, sans Numéro de suivi ni frise, explication que l'envoi partira seul au retour du réseau. [HORS MAQUETTE — à concevoir]
- UX-DR-17 : **Écran 5 · Missions** (nœud 2:2) — carte et liste des Signalements `validé` triés par distance ; réglage du rayon 1–10 km (5 km par défaut) ; chaque élément : pictogramme du Type de déchet retenu, distance (100 m près), Poids estimé, Score de confiance ou « Type confirmé par un humain » ; bouton « Accepter la mission » ; message « Mission déjà prise » avec rafraîchissement de la liste ; après acceptation, Position précise et bouton d'itinéraire (FR-27) ; Mission assignée visible ≤ 15 s. **Miniature photo (≤ 30 Ko) et filtre par Type de déchet [HORS MAQUETTE — à concevoir]**.
- UX-DR-18 : **Écran 6 · Preuve de collecte** (nœud 2:35) — capture photo avant et photo après ; saisie du Poids déclaré (> 0) et choix `pesé`/`estimé` ; capture de la Position à l'envoi avec précision ; confirmation « vous êtes à moins de 150 m du dépôt » ; refus non accusateur donnant distance et rayon (« Vous êtes à 230 m du dépôt ; rapprochez-vous à moins de 150 m. ») ; invitation à réessayer si précision > 50 m ; état sans réseau qui garde la saisie ; consigne « ni personne ni plaque ».
- UX-DR-19 : **Écran 7 · Tableau de bord** (nœud 2:65) — sélecteur de période ; tuiles des 5 indicateurs de FR-31 (Signalements du mois dont validés/rejetés, Délai médian + ouverts, Taux de traitement, Kg collectés par Type avec part `pesé`, Collecteurs vérifiés actifs) ; Carte de chaleur filtrable (période, Type, Statut) en < 2 s pour 5 000 points ; répartition par Type de déchet retenu ; boutons d'Export CSV et GeoJSON ; part de Preuves `contestée` (FR-41, pilote) ; étiquette démo ; 1280×800, navigable au clavier.

**États transverses**

- UX-DR-20 : **États hors-ligne et d'envoi** — indicateur réseau ; états visibles d'un élément de la File hors-ligne : « en attente d'envoi », « en attente de connexion » (Signalement d'un compte sans session), « échec » avec motif (4xx définitif) ; « Réessayer » → tentative dans la seconde ou « Toujours hors ligne » ; compteur exact revenant à 0.
- UX-DR-21 : **États de classification et de chargement** — « classification serveur en attente » (File de modération) ; chargement du Modèle / première mise en cache ; mise à jour du Modèle ou du service worker ; squelettes de chargement et états vides (aucun Signalement, aucune Mission dans le rayon).
- UX-DR-22 : **Notifications** — liste des changements depuis la dernière visite à l'ouverture (Numéro de suivi, nouveau Statut, motif si `rejeté`) ; demande d'autorisation push contextuelle pour le Citoyen connecté (jamais pour l'anonyme). [HORS MAQUETTE — à concevoir]
- UX-DR-23 : **PWA installable** — manifeste (nom, icônes, couleurs de thème issues des jetons), invite d'installation, fonctionnement après installation sans réseau pour le parcours de signalement.

**Écrans absents de la maquette Figma — à concevoir (mêmes jetons, police Inter)**

- UX-DR-24 : **Consentement (FR-4)** — avant la première capture : géolocalisation, envoi de la photo, usage pour le Modèle (case séparée, refusable sans perdre l'accès), consigne « ni personne ni plaque », avertissement que l'anonyme perd sa liste en réinstallant + proposition de créer un compte ; texte juridique à relire (§11 Q4). [HORS MAQUETTE — à concevoir]
- UX-DR-25 : **Connexion OTP** — saisie du numéro (+221), envoi du code, saisie du code, messages 429 (délai d'attente) et 503 (plafond SMS) ; affichage du code OTP à l'écran en Mode démonstration. [HORS MAQUETTE — à concevoir]
- UX-DR-26 : **Second facteur du Personnel (FR-43, pilote)** — enrôlement TOTP (QR / secret), saisie du code, réinitialisation, message 403 `second_factor_required`. [HORS MAQUETTE — à concevoir]
- UX-DR-27 : **File de modération et détail d'un Signalement (UJ-2)** — liste paginée (50) par ancienneté avec photo, Position + précision, Type envoyé + score, Classification serveur, drapeaux (Désaccord IA, Doublon probable avec lien vers l'original, faible confiance, position imprécise) et filtre par drapeau ; détail avec carte, historique des Statuts, actions Valider (type pré-rempli, correction en un clic) et Rejeter (motif obligatoire : spam, pas un déchet, hors zone, doublon, personne ou plaque visible, autre + texte) ; navigation complète au clavier. [HORS MAQUETTE — à concevoir]
- UX-DR-28 : **Administration des comptes et Journal d'audit** — créer, vérifier, suspendre un Collecteur, changer un rôle ; consultation du Journal d'audit filtrable par action et période (Should) ; assignation manuelle d'un Signalement à un Collecteur vérifié (FR-28) ; annulation d'une Mission par l'Administrateur (FR-26). [HORS MAQUETTE — à concevoir]
- UX-DR-29 : **Profil et réglages** — connecté : données du profil, nom affiché (rectification), langue, liste de ses Signalements (droit d'accès), retrait du consentement au réentraînement, suppression du compte avec confirmation et explication des effets ; anonyme : réglages de l'application avec retrait du consentement et retrait d'un Signalement encore `en attente de modération`. [HORS MAQUETTE — à concevoir]
- UX-DR-30 : **Historique du Collecteur (FR-30)** — Missions en cours et terminées (date, Type retenu, Poids déclaré, Statut de Mission, mention `contestée`), total des kg ; annulation de sa Mission `active`. [HORS MAQUETTE — à concevoir ; non listé au PRD §7]
- UX-DR-31 : **Revue de Preuve par échantillon (FR-41, pilote)** — liste des Preuves tirées, photos avant/après, Poids, Position, actions `confirmée` / `contestée` (motif obligatoire). [HORS MAQUETTE — à concevoir ; non listé au PRD §7]
- UX-DR-32 : **Carte publique agrégée (FR-34, Should)** — carte pour Visiteur par cellules ≥ 500 m ou par Zone, sans point précis. [HORS MAQUETTE — à concevoir ; non listé au PRD §7]
- UX-DR-33 : **Lots de matière (FR-38 à FR-40, extension)** — déclaration d'un Lot par le Collecteur, liste filtrable pour le Recycleur, demande de contact et réservation. [HORS MAQUETTE — à concevoir ; non listé au PRD §7]

### FR Coverage Map

FR-1 : Epic 2 (Comptes, accès et journal d'audit)
FR-2 : Epic 2 (Comptes, accès et journal d'audit)
FR-3 : Epic 2 (Comptes, accès et journal d'audit)
FR-4 : Epic 1 (Signaler un dépôt) — partie compte en 2.8
FR-5 : Epic 2 (Comptes, accès et journal d'audit) — Mission d'un Collecteur supprimé en 5.11
FR-6 : Epic 2 (Comptes, accès et journal d'audit)
FR-7 : Epic 1 (Signaler un dépôt)
FR-8 : Epic 1 (Signaler un dépôt)
FR-9 : Epic 1 (Signaler un dépôt)
FR-10 : Epic 1 (Signaler un dépôt)
FR-11 : Epic 3 (L'IA propose le type de déchet)
FR-12 : Epic 3 (L'IA propose le type de déchet)
FR-13 : Epic 3 (L'IA propose le type de déchet) et Epic 4 (export des Corrections, 4.6)
FR-14 : Epic 3 (L'IA propose le type de déchet)
FR-15 : Epic 3 (L'IA propose le type de déchet)
FR-16 : Epic 3 (L'IA propose le type de déchet) et Epic 4 (réentraînement mensuel, 4.11)
FR-17 : Epic 6 (Signaler sans réseau)
FR-18 : Epic 6 (Signaler sans réseau)
FR-19 : Epic 6 (Signaler sans réseau)
FR-20 : Epic 4 (Modérer et suivre un signalement)
FR-21 : Epic 4 (Modérer et suivre un signalement)
FR-22 : Epic 4 (Modérer et suivre un signalement)
FR-23 : Epic 4 (Modérer et suivre un signalement)
FR-24 : Epic 5 (Missions et preuve de collecte)
FR-25 : Epic 5 (Missions et preuve de collecte)
FR-26 : Epic 5 (Missions et preuve de collecte)
FR-27 : Epic 5 (Missions et preuve de collecte)
FR-28 : Epic 5 (Missions et preuve de collecte)
FR-29 : Epic 5 (Missions et preuve de collecte)
FR-30 : Epic 5 (Missions et preuve de collecte)
FR-31 : Epic 7 (Tableau de bord de la commune)
FR-32 : Epic 7 (Tableau de bord de la commune)
FR-33 : Epic 7 (Tableau de bord de la commune)
FR-34 : Epic 7 (Tableau de bord de la commune)
FR-35 : Epic 2 (Comptes, accès et journal d'audit)
FR-36 : Epic 2 (Comptes, accès et journal d'audit)
FR-37 : Epic 1 (Signaler un dépôt) — étendu par 2.5, 4.4, 5.3 et 5.6
FR-38 : Epic 9 (Lots de matière (extension))
FR-39 : Epic 9 (Lots de matière (extension))
FR-40 : Epic 9 (Lots de matière (extension))
FR-41 : Epic 5 (Missions et preuve de collecte)
FR-42 : Epic 5 (Missions et preuve de collecte)
FR-43 : Epic 2 (Comptes, accès et journal d'audit)

## Epic List

### Epic 1 : Signaler un dépôt

Un Citoyen anonyme donne son consentement, photographie un dépôt avec sa Position et reçoit un Numéro de suivi, sur une instance de démonstration étiquetée. Les stories 1.1 à 1.3 montent le squelette (Docker Compose, migrations, configuration, PWA vide), les stories 1.4 à 1.6 la CI.

**Porte :** H24
**FR couvertes :** FR-4, FR-7, FR-8, FR-9, FR-10, FR-37

### Epic 2 : Comptes, accès et journal d'audit

Chacun se connecte par OTP avec son rôle (Mode démonstration au hackathon) ; l'Administrateur commune vérifie les Collecteurs ; chaque action sensible est tracée ; l'utilisateur peut supprimer son compte.

**Porte :** H24 → H60 (FR-43 : pilote)
**FR couvertes :** FR-1, FR-2, FR-3, FR-5, FR-6, FR-35, FR-36, FR-43

### Epic 3 : L'IA propose le type de déchet

Le téléphone classe la photo hors-ligne en moins de 3 s ; sous 60 % le Citoyen choisit ; le serveur reclasse et signale les Désaccords IA. Inclut le pipeline ml/ (entraînement, export ONNX, Fiche du Modèle, test doré).

**Porte :** H24 → H48
**FR couvertes :** FR-11, FR-12, FR-13, FR-14, FR-15, FR-16

### Epic 4 : Modérer et suivre un signalement

Le Modérateur valide ou rejette dans la File de modération et fixe le Type de déchet retenu ; les Corrections validées et consenties sont exportées pour le réentraînement ; le Citoyen suit son Signalement sur la Frise de suivi et reçoit des notifications.

**Porte :** H48 → H60 (4.11 : pilote)
**FR couvertes :** FR-20, FR-21, FR-22, FR-23 ; FR-13 (export des Corrections) et FR-16 (réentraînement mensuel) en complément de l'Epic 3

### Epic 5 : Missions et preuve de collecte

Le Collecteur vérifié voit les Missions proches, en accepte une sans conflit, prouve la collecte (photos, Poids déclaré, Position à 150 m) et garde un historique ; les Preuves sont contrôlées par échantillon et les Missions oubliées expirent.

**Porte :** H48 → H60 (FR-41, FR-42 : pilote)
**FR couvertes :** FR-24, FR-25, FR-26, FR-27, FR-28, FR-29, FR-30, FR-41, FR-42 ; FR-5 en partie (story 5.11)

### Epic 6 : Signaler sans réseau

Un Signalement fait en mode avion est conservé dans la File hors-ligne puis envoyé tout seul au retour du réseau, sans doublon ni perte.

**Porte :** H48
**FR couvertes :** FR-17, FR-18, FR-19

### Epic 7 : Tableau de bord de la commune

L'Administrateur commune voit les Indicateurs, la Carte de chaleur et la répartition par Type de déchet, et exporte en CSV/GeoJSON sans donnée personnelle ; les Visiteurs voient une carte publique agrégée.

**Porte :** H60 (7.1 et 7.6 : opt. H48 si 7.6 est tirée ; 7.7 : pilote)
**FR couvertes :** FR-31, FR-32, FR-33, FR-34

### Epic 8 : Démo fiable et service exploitable

Le jury voit une démo qui tient (plan B, répétition) et la commune peut compter sur le service (test de charge, sauvegardes, alertes, déploiement avec retour arrière). Epic transverse d'exploitation assumé : il ne porte aucune FR.

**Porte :** H48 → H60 pour la démo (8.1 à 8.9) ; pilote (8.10 à 8.15)
**FR couvertes :** aucune FR — NFR et exigences d’architecture (exploitation, démo)

### Epic 9 : Lots de matière (extension)

Le Collecteur déclare un Lot de matière ; le Recycleur le consulte et le réserve.

**Porte :** extension (après H48, hors démo)
**FR couvertes :** FR-38, FR-39, FR-40


<!-- Repeat for each epic in epics_list (N = 1, 2, 3...) -->

## Règles de cohérence entre epics

Les stories ont été rédigées par epic, en parallèle. Les règles ci-dessous priment sur toute mention « créé s'il n'existe pas encore » dans une story. **Chaque table ou brique partagée a un seul propriétaire.** Une autre story qui en a besoin dépend de ce propriétaire ; elle ne la recrée jamais.

| Brique partagée | Story propriétaire | Utilisée par |
|---|---|---|
| Unité de travail, `core.db.after_commit`, worker arq, `GET /v1/config` | 1.2 | toutes |
| `/metrics` interne (compteurs par route et code HTTP) | 1.2 | 8.4, 8.11 |
| `core.storage.ingest_photo()` et `core.storage.purge()` | 1.10 | 1.11, 2.9, 2.10, 4.5, 5.6, 9.1 |
| `core.security.principal()`, `core.demo.flag()` | 1.11 | 1.12, 1.15, 2.x, 4.x, 5.x, 9.x |
| Tâche de miniature `thumb:<photo_id>`, colonne `report_photos.thumb_key` | 1.11 | 2.9, 4.1, 4.5, 5.1 |
| Composant Frise de suivi (4 étapes) | 1.13 | 4.7 (ajoute l'état rejeté, le motif, l'étape courante dynamique) |
| Composant `WasteTypeBadge` / `WasteTypePicker` et jetons `--color-waste-*` | 1.13 | 3.8, 3.12, 4.1, 5.2, 7.3, 8.1 (valeurs définitives), 9.2 |
| `core.idempotency` et table `idempotency_records` | 1.16 | 2.8 à 2.12, 4.3, 4.4, 4.9, 5.3, 5.5, 5.6, 5.9, 5.14, 9.x (`POST /v1/reports` en est exempté) |
| `core/events.py` et `reactions.py` (événements entre modules, AD-21) | 1.16 | 2.8, 2.10, 4.2, 4.10, 5.x |
| Balayage de rétention `retention.sweep` | 1.16 | 2.6, 4.5, 5.6, 8.14 |
| `core.alerts` (liste close des alertes) | 2.2 | 3.13 (journal `classification_queue_full`), 8.11 (complète et teste) |
| Table `users`, comptes de test par rôle (FR-37) | 2.3 / 2.5 | 1.17 (étendu), 4.x, 5.x |
| Colonne `users.display_name` | 2.3 | 2.8, 2.11, 5.5, 5.9 |
| Table `collector_profiles`, `is_verified_collector()` | 2.5 | 5.x, 9.x |
| Table `corrections`, `prefilled_type()` | 3.11 / 3.14 | 4.1, 4.3, 4.6 |
| `reports.service.get_for_staff()` | 3.14 | 4.1 (étend les champs), 4.2, 4.3 |
| `core.storage.signed_url()` (5 min, `MEDIA_HOST`) | 4.1 | 4.5, 5.x, 8.4, 9.x |
| `core.geo.expose()` (niveaux d'exposition des Positions) | 4.1 | 5.x, 7.x, 9.x |
| Liste `GET /v1/staff/reports` et lecture de `GET /v1/moderation/reports/{id}` par l'Administrateur commune | 4.1 | 4.2 (historique), 5.5, 5.9 |
| Table `report_status_events`, événement initial `NULL → pending_review` | 4.2 | 4.6, 4.8, 7.1, 7.2 |
| Émission de `ReportStatusChanged` | 4.2 | 4.10, 5.3, 5.6 |
| Table `weight_estimates`, `reports.service.estimated_weight()` | 5.1 | 5.2, 5.3, 7.1, 7.5 |
| Tuiles `TILES_HOST` de la zone de démo | 5.2 | 7.4, 7.6, 8.7 |
| Route `GET /v1/missions/staff` (Missions `active` pour le Personnel) | 5.5 | 5.9 |
| `missions.service.on_collector_deleted()` et ses réactions (`AccountDeleted`, `CollectorSuspended`) | 5.11 | — |
| `missions.service.photo_seen()` | 5.13 | — |
| Table `proof_reviews` | 5.14 (pilote) | 7.1 : `review_status = unreviewed` tant qu'elle n'existe pas ; 7.7 la branche sur `v_mission_facts` |

**Extensions du jeu de démonstration (FR-37).** La commande de 1.17 est extensible : 2.5 ajoute les comptes de chaque rôle, 4.4 les Signalements `validé` et `rejeté`, 5.3 les Missions `active`, 5.6 les Missions `completed` avec leur Preuve.

**Routes du principal appareil.** La story 2.5 ouvre la liste close avec `PUT /v1/device/consent` ; chaque story qui crée une route du principal appareil l'y ajoute (2.8 `GET /v1/reports/mine`, 2.9 `DELETE /v1/reports/{id}`, 4.8 `GET /v1/reports/mine/changes`). L'entrée `GET /v1/public/map` de la liste blanche publique (story 1.6) est réservée à la story 7.6.

**Fichiers partagés entre epics.** Les epics touchent les mêmes fichiers (`reports.service`, écran 1, `GET /v1/config`, `GET /v1/missions/mine`) parce que chaque porte H24/H48/H60 livre une démo ; la consolidation a été écartée pour cette raison. Le tableau ci-dessus désigne le propriétaire de chaque brique.

**Contrôles de CI non posés par les stories 1.4 à 1.6.** Chacun est ajouté par la story indiquée et devient bloquant dès qu'il existe :

| Contrôle | Story |
|---|---|
| Test route × rôle | 2.5 |
| Test doré du Modèle | 3.10 |
| En-têtes et CSP | 8.4 |
| Trivy, pip-audit, npm audit (exceptions datées) | 8.5 |

**Couleurs des Types de déchet (UX-DR-3).** La story 1.13 crée le composant `WasteTypeBadge` / `WasteTypePicker` et les jetons provisoires `--color-waste-*`. La story 8.1 (porte H48) leur donne leurs valeurs définitives après validation par Mia et vérifie leur contraste.

**Porte de l'Epic 7.** Les stories 7.1 à 7.5 sont à H60 ; si la story 7.6 (Should) est tirée à opt. H48, la story 7.1 l'est avec elle (porte opt. H48), sinon les deux sont à H60 ; 7.7 est pour le pilote.

**Porte de l'Epic 8.** Les stories 8.1 à 8.9 sont nécessaires à la démo, donc à H48–H60 ; 8.1 ne dépend que de 1.13, 3.12, 4.1 et 5.2. Les stories 8.10 à 8.15 sont pour le pilote.

## Questions ouvertes issues de la rédaction des stories

1. **Modèle sous les seuils de SM-2** (3.7, FR-16). La démo garde-t-elle le Modèle factice si le premier Modèle entraîné n'atteint pas F1 macro ≥ 0,80 ? Ou montre-t-on le Modèle entraîné avec ses vrais chiffres ? *Responsable : Mia.*
2. **Sauvegarde planifiée et AD-18** (8.12). Tranchée par la story 8.12 : service planifié du profil `prod` de Docker Compose (AD-18 interdit le cron de l'hôte). À confirmer par Ahmadou à l'implémentation de 8.12. *Responsable : Ahmadou.*
3. **Rôles PostgreSQL.** Ils sont créés par un script d'initialisation hors Alembic, car `teranga_migrator` ne peut pas créer de rôle (story 1.1). *Responsable : Ahmadou.*
4. **Bibliothèque de routage de la PWA.** Elle est absente de la Stack (`react-router` 8 est proposé). Photos HEIC et import depuis la galerie : non prévus au MVP. *Responsable : Mia.*
5. **Polygones des Zones de Dakar.** Source et licence à choisir (story 1.8). *Responsable : Ahmadou.*
6. **Noms de routes et codes d'erreur.** Ceux qui ont été proposés dans les stories sont figés par le client OpenAPI généré dès leur première implémentation. Ils sont à relire une fois.
7. **Cas d'administration non spécifiés dans le PRD.** Ils sont différés au pilote :
   - créer le premier Administrateur commune ;
   - réinitialiser son propre Second facteur ;
   - réactiver un compte suspendu ;
   - empêcher un Administrateur de retirer son propre rôle.
8. **Table de conversion du Poids estimé** (5.1, PRD §11 Q6). Les 15 valeurs `(Taille de tas, Type de déchet) → kg` chargées par la story 5.1 sont provisoires `[ASSUMPTION]` ; elles sont à fournir et à valider avec la commune avant le pilote. *Responsable : Mia.*
9. **Stories lourdes pour un seul agent** (validation 2, M8). 1.11 (tables, route, compteur annuel, miniature, drapeaux, démo), 1.13 (client OpenAPI généré, écrans 3 et 4, deux composants partagés), 2.5 (rôles, générateur route × rôle, propriété, `collector_profiles`, comptes de démo, routage PWA par rôle) et 5.6 (Preuve, géorepérage, démo, rétention). Découpage suggéré : sortir de 1.11 la tâche `thumb:`, de 1.13 la génération du client OpenAPI, de 2.5 les comptes de démo et le routage PWA. Non appliqué : il renumérote de nouveau les Epics 1 et 2 ; à décider avant la planification du sprint. *Responsable : Ahmadou.*

## Epic 1 : Signaler un dépôt

Un Citoyen anonyme donne son consentement, photographie un dépôt avec sa Position et reçoit un Numéro de suivi, sur une instance de démonstration étiquetée. Les stories 1.1 à 1.3 montent le squelette (Docker Compose, migrations, configuration, PWA vide), les stories 1.4 à 1.6 la CI.

> Dans cet epic, la Classification IA n'existe pas encore : le Type de déchet est choisi par le Citoyen ou laissé vide. Aucune story ne dépend d'un epic ultérieur.

### Story 1.1 : Squelette backend et Docker Compose

En tant que développeur de l'équipe,
Je veux un dépôt dont le backend et l'infrastructure démarrent en une commande, selon l'arborescence de l'épine,
Afin de livrer chaque story suivante sur une base commune et conforme.

**Critères d'acceptation :**

**Étant donné** un clone vierge du dépôt
**Quand** on parcourt l'arborescence
**Alors** on trouve, écrits à la main sans starter full-stack ni SQLModel, `backend/app/core/` (`config`, `db`, `errors`, `logging`, `clock`, `enums`), les paquets `backend/app/modules/{auth,reports,missions,lots,analytics,ai,notifications}`, `backend/app/reactions.py` (vide), `backend/app/main.py`, `backend/app/worker.py`, `backend/migrations/` (Alembic), `backend/scripts/`, `backend/tests/{unit,integration,authz,architecture}`
**Et** `ml/contract/`, `ml/release/`, `infra/` (`docker-compose.yml`, `Caddyfile`, `seed/`) et `.github/workflows/` existent
**Et** chaque dépendance Python installée est épinglée à la version exacte de la Stack de l'épine (Python 3.12.16 via l'image `python:3.12.16-slim-trixie` ou `uv`, FastAPI 0.165, SQLAlchemy 2.1, Alembic 1.20, arq 0.28…), avec fichier de verrouillage committé.

**Étant donné** un fichier `.env` copié de `.env.example` et des secrets factices placés dans `.env.secrets` (hors Git), montés dans `/run/secrets/`
**Quand** on lance `docker compose --profile demo up -d`
**Alors** les services `caddy`, `api`, `worker` (même image que l'API), `migrate`, `db` (`postgis/postgis:16-3.7`), `valkey` (`valkey/valkey:9.2.0`, `appendonly yes`, volume) et `garage` (`dxflrs/garage:v2.5.0`, `--single-node --default-bucket`, volumes `meta` et `data`) démarrent, chaque image étant référencée par empreinte `@sha256:`
**Et** `migrate` exécute `alembic upgrade head` avec le rôle `teranga_migrator`, se termine avec le code 0, et `api` et `worker` ne démarrent qu'après sa réussite
**Et** `db`, `valkey` et `garage` possèdent un healthcheck qui n'utilise pas `curl` et passe à l'état `healthy`
**Et** le profil `prod` existe dans le même fichier `docker-compose.yml`.

**Étant donné** la base initialisée
**Quand** on inspecte ses rôles
**Alors** `teranga_migrator` possède le schéma et `teranga_app` (utilisé par l'API et le worker) n'a que des droits DML
**Et** un test d'intégration vérifie qu'un `CREATE TABLE` exécuté par `teranga_app` est refusé
**Et** l'extension PostGIS est active.

**Exigences :** NFR-17, NFR-6.4, AR-1, AR-3, AR-11, AR-35, AD-1, AD-2, AD-15
**Porte :** H24

### Story 1.2 : Configuration, sondes et conventions d'API

En tant que développeur de l'équipe,
Je veux une configuration unique, des sondes de santé, une unité de travail et des conventions d'API communes à tout le backend,
Afin que chaque module suivant hérite des mêmes règles de démarrage, de transaction, d'erreur et de journalisation.

**Critères d'acceptation :**

**Étant donné** l'API démarrée
**Quand** on appelle `GET /healthz`
**Alors** la réponse est 200 `{"status": "ok"}` tant que le processus vit, même si la base, Valkey ou le stockage sont arrêtés
**Et** les services `api` et `worker` de Docker Compose ont un healthcheck sans `curl` qui passe à l'état `healthy`.

**Étant donné** le worker arq (`backend/app/worker.py`, même image que l'API)
**Quand** il tourne
**Alors** il écrit la clé `worker:heartbeat` dans Valkey au moins toutes les 30 s et déclare la liste `cron_jobs` (vide à ce stade) où les tâches planifiées de l'épine seront ajoutées.

**Étant donné** l'API démarrée
**Quand** on appelle `GET /readyz`
**Alors** la réponse est 200 `{"status": "ready"}` seulement si la base, Valkey et le stockage (bucket accessible) répondent et si la clé `worker:heartbeat` a moins de 60 s
**Et** sinon la réponse est 503 `{"status": "not_ready"}`, sans aucun détail interne (un test arrête tour à tour la base, Valkey, Garage et le worker).

**Étant donné** l'API et le worker démarrés
**Quand** on appelle `/metrics` depuis le réseau interne de Compose
**Alors** la réponse expose au format Prometheus les compteurs de requêtes par route et par code HTTP et les durées (route créée par cette story, hors table des routes `/v1`, sans donnée personnelle)
**Et** Caddy ne la relaie pas vers l'extérieur (story 1.3).

**Étant donné** l'unité de travail de `core.db` (`contextvar`, `get_uow()`, décorateur `@transactional`)
**Quand** un service enregistre un effet par `core.db.after_commit()` ou un nettoyage par `core.db.after_rollback()` puis que la requête réussit ou échoue
**Alors** l'effet `after_commit` ne s'exécute qu'après le commit et jamais après une annulation, et le nettoyage `after_rollback` seulement après une annulation (test)
**Et** un test d'architecture vérifie qu'aucun service ni repository n'appelle `commit`, `rollback` ou `begin`.

**Étant donné** la configuration lue uniquement par `core.config.Settings`
**Quand** l'API ou le worker démarre avec `ENV=prod` et `DEMO_MODE=true`, ou `ENV=demo` sans `DEMO_MODE=true`, ou une valeur d'`ENV` hors de `{dev, demo, prod}`
**Alors** le démarrage est refusé (code de sortie non nul, message explicite dans le journal)
**Et** en `demo` ou `prod`, un secret de l'inventaire fixe d'AD-26 absent de `/run/secrets/` bloque le démarrage avec un message qui nomme le secret sans afficher de valeur ; seul `dev` génère des valeurs éphémères.

**Étant donné** un Visiteur sans aucun en-tête
**Quand** il appelle `GET /v1/config`
**Alors** la réponse est 200 avec `demo_mode`, `env` et `model_version` (`null` tant qu'aucun Modèle n'est livré) ; les stories suivantes y ajoutent leurs champs publics sans changer la route.

**Étant donné** l'API démarrée avec `ENV=prod`
**Quand** on appelle `/docs`, `/redoc` ou `/openapi.json`
**Alors** la réponse est 404
**Et** avec `ENV=demo` ou `ENV=dev`, ces trois adresses sont servies.

**Étant donné** une requête vers une route inexistante
**Quand** l'API répond
**Alors** le corps suit l'enveloppe unique `{"error": {"code": "not_found", "message": "…", "request_id": "…"}}`, le code provenant de l'énumération de `core/errors/codes.py`
**Et** chaque requête produit une ligne de journal JSON `structlog` avec `request_id`, `route`, `role` et `duration_ms`
**Et** un test unitaire vérifie que les champs `phone`, `token`, `otp`, l'en-tête `X-Device-Id` et toute Position (`lat`, `lng`) sont masqués dans le journal.

**Exigences :** NFR-7, NFR-14, AR-5, AR-6, AR-12, AR-20, AR-22, AR-23, AR-33, AR-34, AD-8, AD-11, AD-14, AD-17, AD-18, AD-26, AD-27
**Porte :** H24

### Story 1.3 : Coquille PWA et bord Caddy

En tant que développeur de l'équipe,
Je veux une PWA vide, traduite et thémée, servie par Caddy avec les autres origines du service,
Afin que chaque écran suivant parte des mêmes jetons, des mêmes textes i18n et du même routage.

**Critères d'acceptation :**

**Étant donné** le dépôt
**Quand** on parcourt `web/`
**Alors** il est créé par `create-vite` (template `react-ts`) avec `vite-plugin-pwa`, `@tailwindcss/vite` et i18next, avec les dossiers `web/src/{api,features,offline,i18n,theme}`
**Et** chaque dépendance est épinglée à la version exacte de la Stack de l'épine (Node 26 LTS, React 19.3, Vite 8.3, vite-plugin-pwa 2.0, TypeScript 6.0.3, Tailwind 4.3…), avec fichier de verrouillage committé.

**Étant donné** la pile démarrée
**Quand** on ouvre `https://<APP_HOST>/` dans Chrome
**Alors** Caddy sert la coquille de la PWA, dont tout texte vient de `web/src/i18n/fr.json` (`wo.json` existe avec les mêmes clés), en police Inter servie depuis la PWA (aucune police externe)
**Et** les jetons de UX-DR-1 sont déclarés dans un seul bloc `@theme` de `web/src/theme/theme.css`, dont `--color-brand-600: #187A50` ; il n'existe ni `tailwind.config.js` ni `@config`, et la chaîne `#1F8A5B` n'apparaît nulle part dans `web/`.

**Étant donné** le `Caddyfile`
**Quand** on appelle les adresses publiques
**Alors** Caddy relaie `/`, `/v1/*`, `/healthz` et `/readyz`, mais ni `/metrics` ni `/v1/ai/*` (404 depuis l'extérieur), et relaie `MEDIA_HOST` vers Garage en conservant l'en-tête `Host`.

**Exigences :** NFR-13, AR-1, AR-4, AR-36, UX-DR-1, UX-DR-8, AD-16, AD-23
**Porte :** H24

### Story 1.4 : CI de qualité

En tant que développeur de l'équipe,
Je veux une CI qui refuse toute fusion qui casse les tests, la couverture ou les frontières de module,
Afin que chaque story suivante respecte les frontières et la qualité dès H24.

**Critères d'acceptation :**

**Étant donné** une pull request vers `main`
**Quand** la CI (`.github/workflows/ci.yml`) s'exécute
**Alors** elle lance ruff (lint et format), ESLint, pytest sur PostGIS, Valkey et Garage réels en conteneurs, Vitest et `lint-imports`
**Et** elle échoue si la couverture du backend est inférieure à 60 %
**Et** l'échec d'un seul de ces contrôles rend la pull request impossible à fusionner.

**Étant donné** les contrats import-linter `layers` (`router` → `service` → `repository` dans chaque module), `acyclic_siblings` et `protected` (un module n'importe d'un autre que `app.modules.<x>.service`, selon les flèches de l'épine ; `core` n'importe aucun module)
**Quand** un paquet témoin des tests d'architecture importe le `repository` d'un autre module
**Alors** `lint-imports` échoue
**Et** le dépôt réel passe les trois contrats.

**Étant donné** la configuration ESLint de `web/`
**Quand** un fichier hors de `web/src/api/` et de `web/src/offline/` appelle `fetch`
**Alors** ESLint signale une erreur et la CI échoue.

**Exigences :** NFR-11, AR-8, AR-9, AR-21, AR-35, AD-1, AD-11
**Porte :** H24

### Story 1.5 : Hygiène du dépôt public

En tant que développeur de l'équipe,
Je veux un dépôt public sans secret, aux dépendances épinglées et aux réglages GitHub protégés,
Afin que la chaîne logicielle soit sûre dès H24.

**Critères d'acceptation :**

**Étant donné** Gitleaks lancé en binaire (version épinglée, somme de contrôle vérifiée) sur les commits de la pull request
**Quand** un commit contient un faux secret de test, ou une adresse de fichier Figma avec sa clé (règle personnalisée, vérifiée notamment sur `_bmad-output/`)
**Alors** la CI échoue en nommant le fichier et la règle.

**Étant donné** le script de contrôle d'épinglage
**Quand** une image de `docker-compose.yml`, d'un `Dockerfile` ou d'un service de CI n'est pas référencée par `@sha256:`, ou qu'une action `uses:` n'est pas épinglée par un SHA de commit de 40 caractères
**Alors** la CI échoue en listant chaque élément non épinglé.

**Étant donné** le dépôt
**Quand** la CI exécute `git ls-files`
**Alors** aucun chemin ne commence par `TerangaCycle AI/`, sinon elle échoue
**Et** le `.gitignore` committé exclut `TerangaCycle AI/`, `.env`, `.env.secrets` et les dossiers de dépendances et de build.

**Étant donné** `core.config.Settings`
**Quand** un test compare ses champs à `.env.example`
**Alors** chaque variable figure dans `.env.example` avec une valeur factice, et aucune valeur réelle n'y figure
**Et** `SECURITY.md` indique un canal privé de signalement des vulnérabilités et un délai de réponse
**Et** `.github/dependabot.yml` couvre pip, npm, Docker et GitHub Actions.

**Étant donné** les réglages du dépôt GitHub
**Quand** l'équipe les vérifie (sortie de `gh api` jointe à la pull request)
**Alors** `main` est protégée (pull request obligatoire, CI verte requise, pas de force push) et le secret scanning et la push protection sont activés.

**Étant donné** l'arbitrage de Mia sur la licence (MIT ou AGPL-3.0, PRD §11 Q1)
**Quand** il est rendu
**Alors** le fichier `LICENSE` correspondant est ajouté à la racine
**Et** un contrôle CI échoue si `LICENSE` manque, au plus tard à la porte H60.

**Exigences :** NFR-10, NFR-6.3c, AR-2, AR-8, AD-28
**Porte :** H24 (fichier `LICENSE` : H60)

### Story 1.6 : Contrôles de contrat en CI

En tant que développeur de l'équipe,
Je veux que la CI vérifie les contrats transverses (contraste des jetons, messages d'erreur traduits, politique d'accès de chaque route),
Afin qu'aucune story suivante n'ajoute un jeton illisible, un code d'erreur sans message ou une route sans politique d'accès.

**Critères d'acceptation :**

**Étant donné** un fichier de paires texte/fond déclarées à côté de `theme.css`
**Quand** le script de contraste s'exécute en CI
**Alors** il calcule le rapport de chaque paire à partir des jetons et échoue sous 4,5:1 pour du texte, ou sous 3:1 pour du texte ≥ 18,66 px gras et les éléments non textuels
**Et** une paire témoin « Rouge `#D9482B` en texte normal sur blanc » (4,28:1) fait échouer le script.

**Étant donné** l'énumération `core/errors/codes.py`
**Quand** un code n'a pas de clé `errors.<code>` dans `fr.json`
**Alors** la CI échoue en nommant le code manquant.

**Étant donné** la table des routes de l'application
**Quand** une route n'est ni dans la liste blanche publique close (`/healthz`, `/readyz`, `GET /v1/config`, `POST /v1/reports`, `GET /v1/public/map`) ni déclarée avec sa politique d'accès (principal appareil ou rôles) dans la table des politiques
**Alors** le test d'architecture échoue en nommant la route
**Et** l'entrée `GET /v1/public/map` de la liste blanche est réservée à la story 7.6, qui crée la route.

**Exigences :** NFR-9, NFR-12, NFR-13, NFR-6.3b, AR-17, AR-20, UX-DR-2, AD-9, AD-11, AD-16
**Porte :** H24

### Story 1.7 : Accueil et consentement avant la première capture

En tant que Citoyen,
Je veux voir clairement ce que l'application fera de ma Position et de mes photos avant ma première capture, et pouvoir refuser l'usage pour le Modèle,
Afin de signaler en confiance, sans que rien ne parte sans mon accord.

**Critères d'acceptation :**

**Étant donné** le premier lancement de la PWA sur un appareil
**Quand** l'application démarre
**Alors** un Identifiant d'appareil de 32 octets aléatoires (`crypto.getRandomValues`), encodé en base64url (43 caractères), est généré et stocké dans la table Dexie `meta`
**Et** il reste identique après un rechargement ou une fermeture de l'application
**Et** il n'est jamais affiché à l'écran ni écrit dans la console.

**Étant donné** l'écran 1 · Accueil (maquette Figma, nœud 1:2)
**Quand** le Citoyen l'ouvre sur un écran de 390×844
**Alors** il voit le bouton principal « Signaler un dépôt », avec pictogramme et libellé, d'une cible tactile d'au moins 44 × 44 px
**Et** la page ne déborde pas horizontalement.

**Étant donné** un Citoyen qui n'a jamais accepté le consentement
**Quand** il touche « Signaler un dépôt »
**Alors** l'écran de consentement [HORS MAQUETTE] s'affiche avant toute capture et présente : la géolocalisation, l'envoi de la photo, l'usage des photos et des Corrections pour améliorer le Modèle (case séparée, non cochée par défaut), la consigne « ni personne ni plaque » avec pictogramme
**Et** il avertit qu'un Citoyen anonyme perd la liste de ses Signalements s'il réinstalle l'application ou efface ses données
**Et** tous les textes proviennent de `fr.json`.

**Étant donné** l'écran de consentement affiché
**Quand** le Citoyen n'a pas encore accepté
**Alors** l'application n'a demandé ni l'autorisation de géolocalisation, ni celle de l'appareil photo, et n'a envoyé aucune requête de signalement (test Playwright qui espionne `navigator.geolocation`, `navigator.mediaDevices` et le réseau).

**Étant donné** l'écran de consentement affiché
**Quand** le Citoyen touche « Pas maintenant »
**Alors** il revient à l'écran 1, rien n'est mémorisé ni envoyé, et le consentement lui sera redemandé au prochain appui sur « Signaler un dépôt ».

**Étant donné** l'écran de consentement affiché
**Quand** le Citoyen accepte sans cocher la case du réentraînement
**Alors** son acceptation est mémorisée dans Dexie `meta` avec la date de l'appareil (ISO 8601), la version du texte de consentement et `training = false`
**Et** l'accès au signalement n'est pas bloqué : l'application ouvre l'écran 2 · Capture.

**Étant donné** un Citoyen qui a accepté la version courante du consentement
**Quand** il touche de nouveau « Signaler un dépôt », y compris après avoir fermé et rouvert l'application
**Alors** il arrive directement à l'écran 2 sans revoir le consentement
**Et** si la version du texte de consentement change, le consentement lui est redemandé.

**Étant donné** l'écran 1 et l'écran de consentement
**Quand** on lance l'audit d'accessibilité (Lighthouse et axe)
**Alors** aucune violation critique n'est relevée : cibles ≥ 44 px, libellés accessibles sur la case et les boutons, ordre de lecture logique, contrastes issus des jetons.

**Étant donné** la PWA servie par Caddy
**Quand** on l'audite avec Lighthouse sur mobile
**Alors** elle est installable : manifeste avec le nom « TerangaCycle AI », icônes 192 et 512 px (dont une « maskable »), `theme_color` et `background_color` issus des jetons
**Et** la page d'accueil pèse au plus 500 Ko hors images et Modèle.

**Exigences :** FR-4, NFR-5, NFR-6, NFR-12, NFR-13, NFR-P1, NFR-6.1a, AR-36, AR-37, UX-DR-7, UX-DR-8, UX-DR-9, UX-DR-10, UX-DR-11, UX-DR-23, UX-DR-24, AD-9, AD-16, AD-24
**Porte :** H24

### Story 1.8 : Vérifier la Position et la Zone active avant la photo

En tant que Citoyen,
Je veux que l'application capture ma Position avec sa précision et me dise tout de suite si TerangaCycle est actif ici,
Afin de ne pas photographier un dépôt pour rien.

**Critères d'acceptation :**

**Étant donné** une base sans table `zones`
**Quand** la migration Alembic de cette story s'applique
**Alors** elle crée seulement la table `zones` (propriétaire `core/geo` ; `id`, `name`, `kind` ∈ {commune, quartier}, `parent_id`, `geog GEOGRAPHY(MultiPolygon, 4326)`, index GiST), en lecture seule pour `teranga_app`
**Et** elle charge les communes et quartiers de Dakar depuis un fichier versionné dans le dépôt, dont la source et la licence sont citées
**Et** le réglage `ACTIVE_ZONE_ID` désigne la Zone active (Dakar) ; l'API refuse de démarrer s'il ne désigne aucune Zone.

**Étant donné** `core.geo`
**Quand** on teste `in_active_zone(lat, lng)` (`ST_Covers` sur `geography`) et `zone_of(lat, lng)`
**Alors** un point du Plateau est dans la Zone active et `zone_of` renvoie son quartier (à défaut de quartier, sa commune)
**Et** un point de Thiès est hors de la Zone active
**Et** un point situé exactement sur la limite de la Zone active est accepté.

**Étant donné** un Visiteur sans aucun en-tête
**Quand** il appelle `GET /v1/config` (route créée par la story 1.2)
**Alors** la réponse 200 porte en plus `active_zone` (identifiant, nom, polygone simplifié en GeoJSON) et `report_accuracy_flag_m` (valeur du réglage `REPORT_ACCURACY_FLAG_M`, 50)
**Et** la route figure dans la liste blanche publique (le test de la table des routes de la story 1.6 passe).

**Étant donné** un Citoyen qui a accepté le consentement et ouvre l'écran 2 · Capture (maquette Figma, nœud 1:39)
**Quand** l'écran s'affiche
**Alors** la PWA demande la géolocalisation en haute précision et affiche « Position détectée, précision ± N m »
**Et** la réponse de `GET /v1/config` est gardée dans Dexie `meta` et réutilisée si le réseau manque ensuite.

**Étant donné** une Position hors du polygone de la Zone active
**Quand** l'écran 2 la reçoit
**Alors** le message « TerangaCycle n'est pas encore actif ici » s'affiche en Encre avec une icône, avant toute photo
**Et** le déclencheur photo reste désactivé.

**Étant donné** une Position dont la précision dépasse `report_accuracy_flag_m` (50 m)
**Quand** l'écran 2 l'affiche
**Alors** une invitation « Patientez quelques secondes pour une position plus précise » s'affiche en Ambre `#7A5C00` sur `#FFF4CC`, et la Position continue de s'affiner
**Et** l'invitation disparaît dès que la précision atteint 50 m ou moins
**Et** un bouton « Continuer quand même » permet de passer à la photo avec la Position imprécise.

**Étant donné** une géolocalisation refusée ou indisponible
**Quand** l'écran 2 s'affiche
**Alors** un message explique comment autoriser la localisation, sans culpabiliser, avec un bouton « Réessayer »
**Et** aucune photo n'est possible, la Position étant obligatoire.

**Étant donné** une Position capturée
**Quand** on inspecte la console et les journaux
**Alors** aucune coordonnée n'y figure.

**Exigences :** FR-7, NFR-6, NFR-12, NFR-13, NFR-6.1a, AR-5, AR-10, AR-16, AR-19, UX-DR-7, UX-DR-8, UX-DR-10, UX-DR-12, AD-2, AD-6, AD-10, AD-14
**Porte :** H24

### Story 1.9 : Photographier le dépôt en version légère et sans métadonnées

En tant que Citoyen,
Je veux prendre la photo du dépôt depuis l'écran de capture, avec un rappel de la consigne,
Afin d'envoyer une photo légère, sans donnée cachée, même avec un petit forfait.

**Critères d'acceptation :**

**Étant donné** l'écran 2 · Capture (maquette Figma, nœud 1:39) avec une Position dans la Zone active
**Quand** l'écran s'affiche, y compris pour reprendre une photo
**Alors** la consigne « Ni personne ni plaque » est visible avec son pictogramme
**Et** le déclencheur photo (cible ≥ 44 px, pictogramme et libellé) est actif.

**Étant donné** l'écran 2
**Quand** le Citoyen prend la photo
**Alors** la photo vient d'une prise de vue directe avec l'appareil photo arrière (pas d'import depuis la galerie)
**Et** la Position, sa précision et l'horodatage de l'appareil au moment de la prise de vue sont attachés au brouillon avec la photo.

**Étant donné** une photo de 12 Mpx d'environ 4 Mo
**Quand** la PWA la traite
**Alors** l'orientation est appliquée et le résultat est un JPEG d'au plus 300 Ko (307 200 octets), vérifié par un test automatique
**Et** ce JPEG ne contient aucune métadonnée EXIF ni GPS (aucun segment APP1 Exif)
**Et** ces octets sont exactement ceux qui seront envoyés.

**Étant donné** une photo au format HEIC
**Quand** la PWA la traite
**Alors** elle est convertie en JPEG sur l'appareil avant toute autre étape
**Et** si la conversion échoue, le message « Cette photo n'a pas pu être lue. Reprenez-la. » s'affiche et rien n'est gardé.

**Étant donné** une photo traitée
**Quand** l'aperçu s'affiche
**Alors** le Citoyen peut « Reprendre la photo » (la consigne réapparaît) ou « Continuer », le brouillon (photo, Position, précision) étant alors prêt pour l'écran 3
**Et** l'aperçu porte un texte alternatif.

**Exigences :** FR-7, FR-8, NFR-4, NFR-6, NFR-12, NFR-13, UX-DR-7, UX-DR-8, UX-DR-10, UX-DR-12, AD-7, AD-12
**Porte :** H24

### Story 1.10 : Stocker une photo sans métadonnées dans le bucket privé

En tant que Citoyen,
Je veux que toute photo reçue par le serveur soit contrôlée, débarrassée de ses métadonnées et rangée dans un stockage privé,
Afin qu'aucune donnée cachée de ma photo ni aucun fichier piégé ne soit conservé ou exposé.

**Critères d'acceptation :**

**Étant donné** `core.storage.ingest_photo(kind, data)` (seul module qui parle S3, client interne configuré pour Garage)
**Quand** on lui passe un fichier
**Alors** un fichier qui n'est ni JPEG, ni PNG, ni WebP d'après ses octets est refusé en 415 `unsupported_media_type`
**Et** une photo de plus de 1 Mo est refusée en 413 `photo_too_large`, une photo de plus de 12 Mpx en 422 `photo_too_many_pixels` (avant décodage complet, `Image.MAX_IMAGE_PIXELS` réglé explicitement), une image corrompue en 422 `photo_unreadable`
**Et** dans tous ces cas, aucun objet de stockage ne subsiste.

**Étant donné** une photo JPEG acceptée qui contient des métadonnées EXIF et GPS
**Quand** `ingest_photo()` la stocke
**Alors** l'objet est ré-encodé en JPEG après `ImageOps.exif_transpose()`, sans aucune métadonnée EXIF ni GPS (test sur l'objet relu)
**Et** sa clé suit `<kind>/<yyyy>/<mm>/<uuid>.jpg` (`report/…` pour un Signalement), et la fonction renvoie `object_key`, le `sha256` des octets reçus, la largeur et la hauteur
**Et** une lecture anonyme de l'objet dans le bucket est refusée (bucket privé).

**Étant donné** `ingest_photo()` appelé dans une unité de travail (story 1.2)
**Quand** une exception est levée après le stockage et avant le commit
**Alors** l'objet stocké est supprimé par `after_rollback` (comptage du bucket avant/après).

**Étant donné** `core.storage.purge(object_keys)`
**Quand** un service l'appelle dans une unité de travail
**Alors** les objets sont supprimés du bucket seulement par `after_commit`, et rien n'est supprimé si la transaction est annulée (test)
**Et** supprimer un objet déjà absent ne lève pas d'erreur.

**Étant donné** chaque code d'erreur de cette story
**Quand** la CI vérifie `fr.json`
**Alors** chaque code a son message `errors.<code>`, rédigé pour dire au Citoyen quoi faire.

**Exigences :** FR-8, NFR-6.1a, NFR-6.1b, NFR-6.2, AR-12, AR-28, AR-35, UX-DR-10, AD-13, AD-17
**Porte :** H24

### Story 1.11 : Recevoir un Signalement anonyme et attribuer son Numéro de suivi

En tant que Citoyen anonyme,
Je veux que le serveur enregistre mon Signalement et me renvoie un Numéro de suivi,
Afin que mon signalement soit pris en compte par la commune.

**Critères d'acceptation :**

**Étant donné** une base sans tables de signalement
**Quand** la migration Alembic de cette story s'applique
**Alors** elle crée seulement `devices` (propriétaire `auth` ; `device_hash`, `training_consent`, `consent_at`, `first_seen_at`), `reports`, `report_photos` (dont `thumb_key` nullable) et `tracking_counters` (propriétaire `reports`)
**Et** `reports` porte `is_demo NOT NULL DEFAULT false`, un `CHECK` sur la Taille de tas (`small`, `medium`, `large`), un `CHECK` de 280 caractères au plus sur le commentaire, `citizen_type` nullable parmi les 5 Types de déchet et un Statut dont les valeurs viennent de `core/enums.py`.

**Étant donné** un Citoyen anonyme qui présente un `X-Device-Id` valide, `consent.terms = true`, une Position dans la Zone active, une Taille de tas et une photo JPEG de moins de 1 Mo
**Quand** il appelle `POST /v1/reports` en `multipart/form-data` (`meta`, `photo`)
**Alors** la réponse est 201 avec `id`, `tracking_number` au format `TC-AAAA-NNNNNN`, `status = pending_review` (`en attente de modération`), `received_at` (ISO 8601 en `Z`) et `is_demo`
**Et** la ligne `reports` enregistre `owner_key = device:<device_hash>` (`HMAC-SHA256(DEVICE_ID_PEPPER, id)` calculé par `core.security.principal()`, principal unique créé par cette story), l'Identifiant client, la Position, la précision, la Taille de tas, le commentaire, le Type de déchet choisi (nul s'il n'y en a pas), la Zone (quartier) déduite par `core.geo.zone_of`, `received_at = core.clock.now()` et `training_consent` copié de `consent.training`
**Et** `auth.service.touch_device()` crée ou met à jour la ligne `devices` correspondante
**Et** la réponse ne contient ni `owner_key`, ni empreinte, ni Identifiant d'appareil.

**Étant donné** une requête sans photo, sans Position ou sans Taille de tas
**Quand** elle arrive au serveur
**Alors** la réponse est 422 `validation_error` nommant le champ manquant, et rien n'est écrit
**Et** un commentaire de 280 caractères est accepté, un commentaire de 281 caractères est refusé (422), les caractères étant comptés en points de code Unicode
**Et** une latitude ou une longitude hors bornes, une précision nulle ou négative, une Taille de tas ou un Type de déchet hors des valeurs prévues donnent 422.

**Étant donné** une requête avec `consent.terms` absent ou faux
**Quand** elle arrive au serveur
**Alors** la réponse est 422 `consent_required`, et ni ligne ni objet de stockage ne sont créés.

**Étant donné** une requête sans `X-Device-Id`, ou avec un `X-Device-Id` qui n'est pas 43 caractères base64url
**Quand** elle arrive au serveur
**Alors** la réponse est 400 `invalid_device_id`
**Et** une requête portant un en-tête `Authorization` non vérifiable reçoit 401 `invalid_token`.

**Étant donné** une Position hors de la Zone active
**Quand** la requête arrive au serveur
**Alors** la réponse est 422 `outside_active_zone`, dont le message français est « TerangaCycle n'est pas encore actif ici », et rien n'est écrit.

**Étant donné** une photo envoyée
**Quand** `core.storage.ingest_photo()` (story 1.10) la refuse (415, 413 ou 422)
**Alors** la réponse porte ce code et ni ligne ni objet de stockage ne subsistent.

**Étant donné** une photo acceptée
**Quand** le Signalement est enregistré
**Alors** la ligne `report_photos` garde l'`object_key` (`report/<yyyy>/<mm>/<uuid>.jpg`), le `sha256` des octets reçus, la largeur et la hauteur renvoyés par `ingest_photo()`.

**Étant donné** une photo de Signalement stockée
**Quand** la transaction est validée
**Alors** la tâche arq `thumb:<photo_id>` est mise en file par `after_commit` et produit une miniature JPEG d'au plus 30 Ko sous `report_thumb/<yyyy>/<mm>/<uuid>.jpg`, dont la clé est gardée dans `report_photos.thumb_key` (test sur 10 photos de 1 Mo)
**Et** rejouer la tâche ne crée pas de second objet.

**Étant donné** le compteur annuel `tracking_counters`
**Quand** 20 Signalements sont créés simultanément
**Alors** ils obtiennent 20 Numéros de suivi distincts (`INSERT … ON CONFLICT (year) DO UPDATE … RETURNING n`)
**Et** avec une horloge simulée, un Signalement reçu le 31/12/2026 à 23:59:59 UTC obtient `TC-2026-…` et le premier reçu le 01/01/2027 à 00:00:00 UTC obtient `TC-2027-000001`.

**Étant donné** une précision de 51 m
**Quand** le Signalement est créé
**Alors** il porte le drapeau `flag_imprecise_position` (« position imprécise ») et la réponse reste 201
**Et** une précision de 50 m ne pose pas le drapeau.

**Étant donné** une exception levée après le stockage de la photo et avant le commit
**Quand** l'unité de travail se termine
**Alors** aucune ligne n'est écrite, aucune tâche de miniature n'est mise en file et l'objet stocké est supprimé par `after_rollback`
**Et** les services sont `@transactional` et aucun service ni repository n'appelle `commit`, `rollback` ou `begin`.

**Étant donné** l'API en Mode démonstration (`DEMO_MODE = true`)
**Quand** un Signalement est créé
**Alors** il est étiqueté `is_demo = true` par `core.demo.flag()` (créé par cette story), et `is_demo = false` hors Mode démonstration.

**Étant donné** chaque code d'erreur de cette story
**Quand** la CI vérifie `fr.json`
**Alors** chaque code a son message `errors.<code>`, rédigé pour dire au Citoyen quoi faire.

**Exigences :** FR-4, FR-7, FR-8, FR-24 (miniature), FR-37, NFR-9, NFR-6.1a, NFR-6.1b, NFR-6.2, AR-10, AR-12, AR-16, AR-17, AR-19, AR-20, AR-22, AR-23, AR-28, AR-30, AR-32, AR-35, UX-DR-10, AD-2, AD-6, AD-8, AD-9, AD-11, AD-13, AD-14, AD-17, AD-18, AD-24
**Porte :** H24

### Story 1.12 : Renvoyer un Signalement sans doublon ni fuite

En tant que Citoyen,
Je veux pouvoir renvoyer mon Signalement après une coupure sans en créer un second,
Afin que la commune ne reçoive pas de doublon et que personne d'autre ne puisse lire mon Signalement.

**Critères d'acceptation :**

**Étant donné** la table `reports`
**Quand** la migration de cette story s'applique
**Alors** elle ajoute la contrainte d'unicité `(owner_key, client_uuid)`, et rien d'autre.

**Étant donné** un Signalement déjà créé (201) par un appareil
**Quand** le même appareil renvoie `POST /v1/reports` avec le même Identifiant client
**Alors** la réponse est 200 avec le même `id`, le même Numéro de suivi et le même Statut
**Et** aucune nouvelle ligne ni aucun nouvel objet de stockage n'est créé, et le Signalement existant n'est pas modifié, même si le contenu renvoyé diffère.

**Étant donné** un même Signalement
**Quand** il est envoyé 10 fois, d'abord à la suite puis 10 fois en parallèle
**Alors** la base contient un seul Signalement et le bucket un seul objet photo
**Et** en parallèle, exactement une réponse est 201 et les neuf autres sont 200 avec le même Numéro de suivi.

**Étant donné** un Signalement créé par l'appareil A
**Quand** l'appareil B présente le même Identifiant client
**Alors** la réponse est 409 `client_uuid_conflict`, dont le corps se limite à l'enveloppe d'erreur : ni Numéro de suivi, ni Statut, ni Position, ni `id`
**Et** le Signalement de l'appareil A est inchangé.

**Étant donné** `reports.service.create()` appelé avec un Principal de type `user` construit dans le test (`owner_key = user:<id>`)
**Quand** ce Principal présente l'Identifiant client d'un Signalement créé par un appareil
**Alors** le service lève 409 `client_uuid_conflict`
**Et** le même Principal `user` qui renvoie son propre Identifiant client obtient l'existant (200).

**Étant donné** une réponse 201 perdue (coupure simulée après le commit du serveur)
**Quand** le client renvoie le même Signalement
**Alors** il reçoit 200 avec le Numéro de suivi attribué à la première réception.

**Exigences :** FR-9, NFR-6.2, NFR-SM-4, AR-15, AR-17, AD-5, AD-9, AD-17
**Porte :** H24

### Story 1.13 : Compléter, envoyer et voir la confirmation

En tant que Citoyen,
Je veux choisir la Taille de tas, éventuellement le Type de déchet et un commentaire, puis envoyer et voir mon Numéro de suivi,
Afin de savoir que mon Signalement est bien arrivé.

**Critères d'acceptation :**

**Étant donné** l'API de création de Signalement
**Quand** on lance `backend/scripts/export_openapi.py`
**Alors** `web/src/api/openapi.json` et les types `openapi-typescript` sont régénérés, et une instance unique `openapi-fetch` enveloppée dans `web/src/api/` ajoute `X-Device-Id` (lu dans Dexie `meta`) et traduit chaque erreur en message `errors.<code>`
**Et** ces fichiers sont versionnés, et la CI échoue si leur régénération diffère
**Et** `web/package.json` porte l'override `openapi-typescript` → `typescript`.

**Étant donné** un brouillon complet de l'écran 2 (photo et Position)
**Quand** l'écran 3 · Résultat IA (maquette Figma, nœud 1:57), adapté sans proposition IA, s'affiche
**Alors** il montre la miniature de la photo (avec texte alternatif)
**Et** un sélecteur de Taille de tas [HORS MAQUETTE] : petit, moyen, grand, chacun avec pictogramme et libellé, cibles ≥ 44 px, aucun choix présélectionné
**Et** un sélecteur facultatif des 5 Types de déchet (composant `WasteTypePicker`), aucun présélectionné, un choix pouvant être retiré
**Et** un commentaire facultatif avec compteur « n/280 », la saisie s'arrêtant à 280 caractères (points de code).

**Étant donné** le composant unique `WasteTypeBadge` / `WasteTypePicker`, créé par cette story dans `web/src/features/classify/`
**Quand** il affiche les 5 Types de déchet (plastique, métal, verre, organique, mixte)
**Alors** chacun a un pictogramme, un libellé i18n (`fr.json`, clé prête dans `wo.json`) et une couleur déclarée comme jeton provisoire `--color-waste-plastic`, `--color-waste-metal`, `--color-waste-glass`, `--color-waste-organic`, `--color-waste-mixed` dans le bloc `@theme` de `web/src/theme/theme.css`, aucune couleur n'étant codée hors du thème
**Et** le script de contraste vérifie chaque couleur (3:1 face à son fond, élément non textuel) et chaque libellé (4,5:1), et la CI échoue sinon
**Et** chaque option est sélectionnée en un seul toucher, mesure au moins 44 × 44 px et son état sélectionné est signalé autrement que par la couleur (coche).

**Étant donné** l'écran 3
**Quand** la photo, la Position ou la Taille de tas manque
**Alors** le bouton « Envoyer » est désactivé et la raison est annoncée aux lecteurs d'écran.

**Étant donné** le brouillon
**Quand** il est créé
**Alors** un Identifiant client (UUID v4) lui est attribué et conservé pour tout renvoi
**Et** un double appui sur « Envoyer » ne crée qu'un Signalement (bouton désactivé pendant la requête ; un second envoi reçoit 200).

**Étant donné** un brouillon complet et du réseau
**Quand** le Citoyen touche « Envoyer »
**Alors** la PWA appelle `POST /v1/reports` avec `meta` (Identifiant client, Position et précision, horodatage de prise de vue, Taille de tas, commentaire, Type de déchet s'il est choisi, `consent` lu dans Dexie `meta`) et les octets exacts du JPEG de l'écran 2.

**Étant donné** une réponse 201 ou 200
**Quand** l'écran 4 · Confirmation (maquette Figma, nœud 1:97) s'affiche
**Alors** il remercie le Citoyen et montre son Numéro de suivi `TC-AAAA-NNNNNN`
**Et** la Frise de suivi (composant créé par cette story, complété par la story 4.7) affiche ses 4 étapes (« Signalé », « Validé par la modération », « Assigné à un collecteur », « Collecté, preuve photo »), chacune avec pictogramme et libellé, en liste ordonnée, l'étape courante « Signalé » étant distinguée autrement que par la couleur et annoncée aux lecteurs d'écran
**Et** un bouton « Retour à l'accueil » ramène à l'écran 1 et le brouillon est effacé.

**Étant donné** une réponse dont `is_demo` est vrai
**Quand** l'écran 4 s'affiche
**Alors** l'étiquette « Données de démonstration » [HORS MAQUETTE] y est visible, avec un contraste AA.

**Étant donné** une réponse d'erreur
**Quand** l'écran 3 la reçoit
**Alors** 422 `outside_active_zone` affiche « TerangaCycle n'est pas encore actif ici » et propose de revenir à l'écran 2
**Et** 422 `consent_required` ramène à l'écran de consentement
**Et** 413, 415 ou une erreur de photo (422) invite à reprendre la photo
**Et** une erreur réseau ou 5xx affiche « Envoi impossible pour l'instant. Votre saisie est gardée, réessayez. » avec un bouton « Réessayer », le brouillon étant conservé tant que l'application reste ouverte
**Et** chaque message est en Encre avec une icône rouge, issu de `fr.json`, et dit quoi faire sans culpabiliser.

**Étant donné** les écrans 3 et 4 sur 390×844
**Quand** on les audite
**Alors** aucun débordement horizontal n'apparaît, toute cible tactile mesure au moins 44 × 44 px et l'audit d'accessibilité Lighthouse ne relève aucune violation critique.

**Exigences :** FR-7, FR-9, FR-37, NFR-4, NFR-6, NFR-12, NFR-13, NFR-SM-3, NFR-P2, AR-20, AR-21, AR-36, UX-DR-2, UX-DR-3, UX-DR-4, UX-DR-6, UX-DR-7, UX-DR-8, UX-DR-9, UX-DR-10, UX-DR-13, UX-DR-14, UX-DR-15, AD-5, AD-11, AD-16
**Porte :** H24

### Story 1.14 : Repérer les Doublons probables à la réception

En tant que membre du Personnel de la commune,
Je veux que chaque Signalement reçu porte déjà la marque de Doublon probable quand sa photo ou sa Position répète un Signalement existant,
Afin de ne pas envoyer deux fois un Collecteur sur le même dépôt.

**Critères d'acceptation :**

**Étant donné** les tables `reports` et `report_photos`
**Quand** la migration de cette story s'applique
**Alors** elle ajoute un index sur `report_photos.sha256`, la colonne indexée `reports.duplicate_of_report_id` (nullable, interne au module `reports`) et un index GiST sur la Position de `reports` (créé par cette story)
**Et** les réglages nommés `DUPLICATE_RADIUS_M` (50) et `DUPLICATE_WINDOW_H` (72) existent dans `Settings` et `.env.example`.

**Étant donné** un Signalement existant
**Quand** un nouveau Signalement, avec un autre Identifiant client et quel que soit son auteur, arrive avec une photo dont les octets reçus sont strictement identiques (même `sha256`)
**Alors** il est créé normalement (201, `en attente de modération`) avec `duplicate_of_report_id` pointant vers le plus ancien Signalement portant cette photo.

**Étant donné** un Signalement non terminal (ni `rejeté` ni `collecté`) reçu il y a moins de 72 h
**Quand** un nouveau Signalement arrive à 49 m de lui (`ST_DWithin` sur `geography`, horloge `core.clock`)
**Alors** il est marqué Doublon probable du Signalement le plus proche
**Et** à 51 m, ou pour un Signalement reçu il y a 72 h 01 min, ou pour un Signalement terminal, il n'est pas marqué
**Et** si la photo est identique et la Position proche, c'est le Signalement à la photo identique qui est retenu comme origine.

**Étant donné** un Signalement marqué Doublon probable
**Quand** la réponse est renvoyée au Citoyen
**Alors** elle a exactement la même forme qu'une réponse non marquée : aucun champ ne révèle l'existence d'un autre Signalement.

**Étant donné** un renvoi du même Signalement par le même appareil (même Identifiant client)
**Quand** il arrive
**Alors** il renvoie l'existant (200) et n'est pas compté comme Doublon probable.

**Étant donné** un autre module qui a besoin de savoir si une photo a déjà été reçue
**Quand** il appelle `reports.service.photo_seen(sha256)`
**Alors** il obtient la réponse sans lire les tables de `reports`
**Et** la marque est calculée une seule fois à la création, stockée et jamais recalculée à la lecture.

**Exigences :** FR-8, NFR-6.2, AR-25, AR-28, AD-6, AD-13, AD-14, AD-19
**Porte :** H24

### Story 1.15 : Limiter les abus de signalement

En tant que Modérateur,
Je veux que le nombre de Signalements par appareil, par IP et par compte soit limité,
Afin que la File de modération ne soit pas noyée sous le spam.

**Critères d'acceptation :**

**Étant donné** `core.ratelimit.limit(scope)` sur Valkey (fenêtre fixe, opération atomique, clés hachées)
**Quand** on inspecte Valkey et la configuration
**Alors** aucune clé ne contient d'IP ni d'Identifiant d'appareil en clair
**Et** les plafonds sont des réglages nommés de `Settings` (10 Signalements par heure, 60 requêtes par minute) présents dans `.env.example`.

**Étant donné** un Citoyen anonyme qui a créé 10 Signalements dans l'heure avec le même Identifiant d'appareil
**Quand** il en envoie un 11e
**Alors** la réponse est 429 `rate_limited` avec un en-tête `Retry-After` en secondes jusqu'à la fin de la fenêtre
**Et** ni ligne ni objet de stockage n'est créé (la limite s'applique avant le traitement de la photo).

**Étant donné** 10 Signalements créés dans l'heure depuis une même IP avec 10 Identifiants d'appareil différents
**Quand** un 11e arrive de cette IP avec un nouvel Identifiant d'appareil
**Alors** la réponse est 429 `rate_limited`.

**Étant donné** la pile complète derrière Caddy, uvicorn lancé avec `--proxy-headers --forwarded-allow-ips=<IP de Caddy>` (jamais `*`) et Caddy qui remplace `X-Forwarded-For`
**Quand** un même client envoie 11 Signalements portant 11 en-têtes `X-Forwarded-For` différents et 11 Identifiants d'appareil différents
**Alors** le 11e reçoit 429
**Et** le code de l'API ne lit l'IP que depuis `request.client.host`.

**Étant donné** 10 Signalements créés par un appareil dans l'heure
**Quand** on redémarre les services `api` et `valkey`, puis que l'appareil en envoie un 11e
**Alors** la réponse est 429 (compteurs conservés grâce à l'AOF).

**Étant donné** 10 Signalements créés par un appareil dans l'heure
**Quand** l'appareil renvoie l'un d'eux avec le même Identifiant client
**Alors** il reçoit 200 avec l'existant : un renvoi ne consomme pas de quota.

**Étant donné** un Principal de type `user` construit dans le test
**Quand** il crée un 11e Signalement dans l'heure (portée `report:user`), ou émet une 61e requête dans la minute sur une route quelconque (portée `user:any`)
**Alors** il reçoit 429 `rate_limited`
**Et** la portée `user:any` ne s'applique pas à un Citoyen anonyme.

**Étant donné** l'écran 3 de la PWA
**Quand** l'envoi reçoit 429
**Alors** le message « Vous avez envoyé beaucoup de Signalements. Merci ! Réessayez dans N min. » s'affiche, N étant calculé depuis `Retry-After`, et le brouillon est conservé.

**Exigences :** FR-10, NFR-6.2, NFR-12, NFR-13, AR-4, AR-26, UX-DR-10, AD-9, AD-20, AD-23
**Porte :** H24

### Story 1.16 : Retirer son consentement au réentraînement

En tant que Citoyen anonyme,
Je veux changer d'avis à tout moment sur l'usage de mes photos pour améliorer le Modèle, depuis les réglages de l'application,
Afin que mes Signalements, passés et futurs, ne servent plus au réentraînement si je le refuse.

**Critères d'acceptation :**

**Étant donné** l'écran 1
**Quand** le Citoyen touche « Réglages » (pictogramme et libellé, cible ≥ 44 px)
**Alors** l'écran Réglages de l'application [HORS MAQUETTE] affiche son choix actuel pour le réentraînement (lu dans Dexie `meta`), la date de son acceptation et un interrupteur pour le modifier, avec libellés accessibles.

**Étant donné** une base sans table `idempotency_records`
**Quand** la migration de cette story s'applique
**Alors** elle crée seulement `idempotency_records` (propriétaire `core/idempotency` ; `principal_key`, `route_template`, `key`, `request_sha256`, `response_status`, `response_body`, `created_at`, clé primaire sur les trois premiers champs).

**Étant donné** la route `PUT /v1/device/consent` (principal appareil, déclarée dans la table des politiques d'accès)
**Quand** elle est appelée sans `Idempotency-Key`
**Alors** la réponse est 400 `idempotency_key_required`
**Et** sans `X-Device-Id` valide, la réponse est 400 `invalid_device_id`
**Et** un second appel avec la même clé et le même corps rejoue la réponse sans nouvel effet, et un appel avec la même clé et un autre corps reçoit 422 `idempotency_key_reused`
**Et** seules les réponses 2xx sont conservées.

**Étant donné** un appareil A qui a créé 3 Signalements avec `training_consent = true`, et un appareil B qui en a créé 1
**Quand** A appelle `PUT /v1/device/consent` avec `{"training": false}`
**Alors** la réponse est 200, et `devices.training_consent` passe à faux pour A avec `consent_at = core.clock.now()`
**Et** l'événement `TrainingConsentWithdrawn` est émis par `core.events.emit()` sous `after_commit`, traité par la tâche arq `react:<event_id>` dans `reactions.py`, qui appelle `reports.service.revoke_training_consent(owner_key)` (`core/events.py` et le mécanisme de réaction de `reactions.py` sont créés par cette story)
**Et** les 3 Signalements de A ont `training_consent = false`, celui de B reste vrai
**Et** rejouer la réaction ne change rien (idempotence).

**Étant donné** un retrait enregistré
**Quand** le Citoyen crée ensuite un Signalement
**Alors** la PWA envoie `consent.training = false` et le Signalement est enregistré avec `training_consent = false`.

**Étant donné** un Citoyen qui avait retiré son consentement
**Quand** il le redonne (`{"training": true}`)
**Alors** seuls ses Signalements futurs portent `training_consent = true` ; les Signalements passés restent à faux.

**Étant donné** un Citoyen sans réseau
**Quand** il modifie son choix
**Alors** le nouveau choix s'applique immédiatement à ses prochains Signalements (Dexie `meta`)
**Et** le message « Votre choix sera transmis dès le retour du réseau » s'affiche
**Et** l'appel au serveur est retenté, avec la même `Idempotency-Key`, à l'ouverture de l'application et à l'événement `online`, jusqu'à une réponse 2xx.

**Étant donné** le worker
**Quand** la tâche planifiée `retention.sweep` (quotidienne, créée par cette story dans les `cron_jobs` arq ; les stories suivantes y ajoutent leurs purges) s'exécute avec une horloge simulée
**Alors** les entrées `idempotency_records` de plus de 24 h sont supprimées et les plus récentes conservées.

**Exigences :** FR-4, NFR-12, NFR-13, NFR-6.3a, AR-12, AR-15, AR-17, AR-22, AR-23, AR-24, AR-30, UX-DR-7, UX-DR-8, UX-DR-10, UX-DR-29, AD-5, AD-8, AD-9, AD-17, AD-18, AD-21, AD-24
**Porte :** H24

### Story 1.17 : Charger et retirer les Données de démonstration en une commande

En tant que membre de l'équipe qui présente la démo,
Je veux charger puis retirer un jeu de Données de démonstration en une commande,
Afin de montrer une instance réaliste sans jamais présenter un chiffre de démonstration comme réel.

**Critères d'acceptation :**

**Étant donné** une instance en `ENV=demo` ou `ENV=dev`
**Quand** on lance `python -m app.cli demo load`
**Alors** au moins 20 Signalements fictifs, répartis dans au moins 5 quartiers de la Zone active (Dakar), sont créés par `reports.service` avec les mêmes règles qu'un Signalement réel, chacun avec une Taille de tas et une photo libre de droits sans personne ni plaque (stockée dans `infra/seed/`, licences listées), au Statut `en attente de modération`
**Et** chacun porte `is_demo = true`.

**Étant donné** la commande `demo load`
**Quand** chaque module propriétaire de données expose une fonction de chargement de démonstration dans son service
**Alors** la commande les appelle dans un ordre déclaré, de sorte que les modules qui possèdent les comptes de test et les autres Statuts puissent y ajouter leurs données sans modifier la commande.

**Étant donné** des Données de démonstration déjà chargées
**Quand** on relance `demo load`
**Alors** aucun Signalement n'est dupliqué (Identifiants client fixes sous un `owner_key` de démonstration dédié).

**Étant donné** des Données de démonstration chargées et des Signalements non étiquetés
**Quand** on lance `python -m app.cli demo purge` (exécutée avec le rôle `teranga_migrator`)
**Alors** toutes les lignes `is_demo = true` de `reports`, les `report_photos` rattachées à ces Signalements et leurs objets de stockage sont supprimés (comptage du bucket avant/après)
**Et** les lignes non étiquetées et les Zones restent intactes.

**Étant donné** une instance en `ENV=prod`
**Quand** on lance `demo load` ou `demo purge`
**Alors** la commande est refusée (code de sortie non nul, message explicite) et rien n'est modifié.

**Étant donné** les schémas de réponse de l'API
**Quand** un test d'architecture les parcourt
**Alors** chaque schéma qui expose un Signalement porte le champ `is_demo`, afin que la PWA affiche l'étiquette « Données de démonstration » partout où ces données apparaissent.

**Exigences :** FR-37, NFR-P2, NFR-6.3a, AR-32, UX-DR-6, AD-14, AD-15
**Porte :** H24

## Epic 2 : Comptes, accès et journal d'audit

Chacun se connecte par OTP avec son rôle (code affiché à l'écran en Mode démonstration au hackathon) et garde sa session 30 jours sans jeton exposé au navigateur ; chaque route applique le rôle et la propriété de l'objet, vérifiés par un test route × rôle ; chaque action sensible est inscrite au Journal d'audit, en ajout seul ; l'utilisateur gère son profil et peut supprimer son compte ; l'Administrateur commune crée, vérifie et suspend les Collecteurs ; avant le pilote, le Personnel ajoute un Second facteur.

**Prérequis :** Epic 1 livré (squelette, `core.config.Settings`, `core.clock`, unité de travail `core.db` avec `after_commit`, `core.ratelimit` sur Valkey, `core.idempotency.require_key`, `core.security.principal()` pour l'Identifiant d'appareil, `POST /v1/reports` anonyme avec `owner_key = device:<hash>`, `GET /v1/config`, consentement, worker arq, `python -m app.cli demo load|purge`).

**Ordre des portes :** stories 2.1 à 2.5 → **H24** ; 2.6 (inscription au Journal d'audit, nécessaire à l'Epic 4) → **H48** ; 2.7 (consultation du Journal) → **Should, opt. H48**, dont aucune autre story ne dépend ; 2.8 à 2.11 → **H60** ; 2.12 → **pilote**. Les stories H48 de l'Epic 4 ne dépendent que des stories 2.1 à 2.6.

### Story 2.1 : Mode démonstration visible et interdit en production

En tant que membre de l'équipe ou du jury,
Je veux qu'un bandeau « Mode démonstration » soit visible sur tous les écrans et que ce mode ne puisse jamais tourner en production,
Afin de ne jamais confondre la démo avec le service réel ni exposer un code OTP en production.

**Critères d'acceptation :**

**Étant donné** le refus de démarrage `ENV` × `DEMO_MODE` (test de la story 1.2)
**Quand** on l'étend aux 6 combinaisons, pour l'API et pour le worker
**Alors** `ENV=prod` avec `DEMO_MODE=true` et `ENV=demo` avec `DEMO_MODE=false` sont refusés, et `ENV=dev` accepte les deux valeurs ; un test par combinaison `ENV` × `DEMO_MODE` (6 cas).

**Étant donné** `GET /v1/config` qui renvoie `demo_mode = true`
**Quand** j'ouvre n'importe quel écran de la PWA (citoyen, collecteur, Personnel, connexion, profil)
**Alors** un bandeau « Mode démonstration » **[HORS MAQUETTE — UX-DR-5]** s'affiche en haut de l'écran, sans bouton de fermeture, texte issu de `fr.json`
**Et** son contraste est vérifié par le script CI des paires texte/fond (≥ 4,5:1) et il est exposé aux lecteurs d'écran (région nommée).

**Étant donné** `GET /v1/config` qui renvoie `demo_mode = false`
**Quand** j'ouvre n'importe quel écran
**Alors** aucun bandeau n'est affiché.

**Étant donné** la PWA ouverte sans réseau
**Quand** l'écran s'affiche
**Alors** le bandeau suit la dernière réponse de `GET /v1/config` gardée dans Dexie `meta` (story 1.8).

**Exigences :** FR-6, NFR-6.2, NFR-12, NFR-13, AR-5, AR-36, UX-DR-5, UX-DR-2, UX-DR-8, AD-14, AD-16
**Porte :** H24

### Story 2.2 : Demander un code de connexion par SMS

En tant que Collecteur, membre du Personnel ou Citoyen qui veut un compte,
Je veux saisir mon numéro de téléphone et recevoir un code à usage unique,
Afin de me connecter sans mot de passe.

**Critères d'acceptation :**

**Étant donné** l'écran 1
**Quand** je touche « Je suis collecteur » ou « Espace commune »
**Alors** l'écran de connexion OTP **[HORS MAQUETTE — UX-DR-25]** s'ouvre avec l'indicatif +221 affiché et un champ numéro libellé pour les lecteurs d'écran
**Et** chaque cible tactile mesure au moins 44 × 44 px et tous les textes passent par i18next.

**Étant donné** un numéro sénégalais valide (+221 suivi de 9 chiffres, préfixe présent dans le réglage `PHONE_ALLOWED_PREFIXES`, saisi avec ou sans espaces)
**Quand** la PWA appelle `POST /v1/auth/otp/request` avec un `X-Device-Id` valide
**Alors** le serveur génère un code numérique par `secrets` (longueur `OTP_LENGTH`), le stocke **haché** dans Valkey sous l'empreinte HMAC du numéro avec un TTL de 5 min, et l'envoie par `core.sms.SmsSender` uniquement
**Et** un nouveau code demandé pour le même numéro invalide le précédent.

**Étant donné** un numéro étranger ou malformé
**Quand** la demande est envoyée
**Alors** la réponse est 422 `invalid_phone`, aucun SMS ne part et l'écran dit quoi faire (« Saisissez un numéro sénégalais à 9 chiffres »).

**Étant donné** 5 demandes acceptées dans l'heure pour un même numéro
**Quand** une 6e demande arrive
**Alors** la réponse est 429 `rate_limited` avec `Retry-After` (secondes restantes) et l'écran affiche le délai d'attente
**Et** il en va de même à la 6e demande dans l'heure pour un même Identifiant d'appareil et à la 21e pour une même IP (`request.client.host` derrière le proxy de confiance) ; un test par portée (`otp:phone`, `otp:device`, `otp:ip`) ; les compteurs survivent à un redémarrage de Valkey (AOF).

**Étant donné** une demande sans `X-Device-Id` ou avec un `X-Device-Id` hors format (32 octets base64url)
**Quand** elle est envoyée
**Alors** la réponse est 400 `invalid_device_id` et aucun SMS ne part.

**Étant donné** le plafond quotidien `SMS_DAILY_CAP` atteint (portée `sms:daily`, vérifiée dans le port SMS)
**Quand** une demande arrive
**Alors** la réponse est 503 `sms_cap_reached`, aucun SMS ne part et l'écran explique de réessayer plus tard
**Et** `core.alerts.raise_alert("sms_cap_reached")` envoie une alerte sur `ALERT_WEBHOOK_URL` au plus une fois par 15 min (`core.alerts` est créé par cette story) ; test de déclenchement simulé.

**Étant donné** le Mode démonstration actif (`SMS_BACKEND=demo`, `DemoSmsSender`)
**Quand** une demande est acceptée
**Alors** la réponse contient `demo_otp`, que l'écran affiche dans un encadré « Code de démonstration », et aucun SMS réel ne part
**Et** hors Mode démonstration, le champ `demo_otp` est absent du schéma OpenAPI et de la réponse (test).

**Étant donné** les journaux structurés capturés pendant les tests
**Quand** on les inspecte
**Alors** ils ne contiennent ni le numéro complet, ni le code, ni l'Identifiant d'appareil.

**Exigences :** FR-1, FR-6, NFR-6.1a, NFR-6.2, NFR-14, NFR-16, AR-20, AR-26, AR-27, AR-33, AR-34, UX-DR-25, UX-DR-11, UX-DR-7, UX-DR-10, AD-9, AD-14, AD-20, AD-27
**Porte :** H24

### Story 2.3 : Se connecter avec le code OTP

En tant qu'utilisateur qui a reçu un code,
Je veux le saisir pour ouvrir ma session,
Afin d'agir selon mon rôle et de retrouver mes Signalements sur mon compte.

**Critères d'acceptation :**

**Étant donné** un code valide demandé il y a moins de 5 min
**Quand** la PWA appelle `POST /v1/auth/otp/verify` (numéro, code)
**Alors** la réponse 200 contient un jeton d'accès JWT `EdDSA` d'une durée ≤ 15 min (`iss`, `aud`, `kid`, `sub`, `tv`, `amr = ["otp"]`), signé par la clé la plus récente de `JWT_SIGNING_KEYS`, et `user {id, role}`
**Et** le code est consommé : une seconde vérification avec le même code renvoie 401 `otp_expired`.

**Étant donné** un numéro qui n'a pas encore de compte
**Quand** sa première vérification réussit
**Alors** une ligne est créée dans la table `users` (créée par cette story : `id` UUID, `phone_hash` HMAC-SHA256 avec `PHONE_PEPPER`, `phone_enc` AES-GCM avec `key_id` et `nonce` de `PHONE_ENC_KEYS`, `display_name` nullable, `role` = Citoyen, `status = active`, `token_version`, `is_demo` par `core.demo.flag()`, horodatages par `core.clock`)
**Et** aucune colonne ne contient le numéro en clair (test CI : recherche du numéro de test dans une copie de la base → absent).

**Étant donné** un code erroné
**Quand** il est vérifié
**Alors** la réponse est 401 `otp_invalid` (comparaison à temps constant)
**Et** après 5 essais erronés le code est invalidé : un 6e essai, même avec le bon code, renvoie 401 `otp_expired`.

**Étant donné** un code demandé il y a 5 min 01 s (horloge simulée)
**Quand** il est vérifié
**Alors** la réponse est 401 `otp_expired` et l'écran propose « Demander un nouveau code ».

**Étant donné** `core.security.principal()` qui lit désormais `Authorization: Bearer`
**Quand** une requête présente un jeton signé avec un algorithme hors liste blanche (`HS256`, `none`), un émetteur incorrect, une audience incorrecte, un jeton expiré ou un `kid` inconnu
**Alors** chaque cas renvoie 401 `invalid_token` (un test par cas, 5 tests)
**Et** un jeton signé par une ancienne clé encore présente dans `JWT_SIGNING_KEYS` est accepté (test de rotation par ajout de `kid`).

**Étant donné** un Citoyen connecté
**Quand** il crée un Signalement par `POST /v1/reports` avec un jeton valide et son `X-Device-Id`
**Alors** le Signalement porte `owner_key = user:<id>` et `author_user_id` (colonne ajoutée à `reports` par cette story, sans clé étrangère inter-module)
**Et** sans jeton, `owner_key` reste `device:<hash>` ; avec un jeton invalide ou expiré, la réponse est 401 (aucun repli silencieux sur l'appareil).

**Étant donné** l'écran de saisie du code **[HORS MAQUETTE — UX-DR-25]**
**Quand** la vérification échoue
**Alors** le message dit quoi faire (`errors.otp_invalid` : vérifier le SMS et réessayer ; `errors.otp_expired` : demander un nouveau code), en Encre avec icône rouge
**Et** le jeton d'accès n'est gardé qu'en mémoire : un test de bout en bout (Playwright) vérifie qu'après connexion `localStorage`, `sessionStorage` et IndexedDB ne contiennent aucun jeton (la table Dexie `meta` ne contient que l'Identifiant d'appareil).

**Étant donné** les journaux capturés pendant les tests
**Quand** on les inspecte
**Alors** ils ne contiennent ni jeton, ni code, ni numéro complet.

**Exigences :** FR-1, FR-2, NFR-6.1b, NFR-14, NFR-17, AR-6, AR-17, AR-34, UX-DR-25, UX-DR-2, UX-DR-10, AD-5, AD-9, AD-10, AD-20, AD-26
**Porte :** H24

### Story 2.4 : Rester connecté 30 jours et se déconnecter

En tant qu'Utilisateur connecté,
Je veux garder ma session 30 jours d'activité sans ressaisir de code et pouvoir me déconnecter,
Afin d'utiliser l'application au quotidien sans qu'une session volée ou révoquée puisse servir.

**Critères d'acceptation :**

**Étant donné** une vérification OTP réussie
**Quand** la réponse est émise
**Alors** un jeton de renouvellement opaque est posé en cookie `HttpOnly; Secure; SameSite=Strict; Path=/v1/auth`, jamais dans le corps
**Et** il est stocké **haché** dans la table `refresh_tokens` (créée par cette story : famille, utilisateur, empreinte, `amr`, création, dernier usage, rotation, révocation).

**Étant donné** un jeton d'accès expiré
**Quand** un appel de la PWA reçoit 401
**Alors** `refreshSession()` (`web/src/api/session.ts`, seul appelant de `POST /v1/auth/refresh`) obtient un nouveau jeton d'accès puis l'appel est rejoué une seule fois
**Et** à la réouverture de l'application, la session est restaurée par renouvellement, sans ressaisie de code.

**Étant donné** un renouvellement réussi
**Quand** le serveur répond
**Alors** un nouveau jeton de renouvellement remplace l'ancien (rotation), marqué comme remplacé.

**Étant donné** un jeton de renouvellement déjà remplacé
**Quand** il est présenté moins de 10 s (`REFRESH_REUSE_GRACE_S`) après la rotation
**Alors** la réponse est 401 `refresh_superseded` sans révocation de la famille
**Et** présenté plus de 10 s après, il révoque toute la famille (401 `session_revoked`), et le dernier jeton de la famille est lui aussi refusé (401).

**Étant donné** deux onglets ouverts dont le jeton d'accès expire en même temps
**Quand** les deux appellent l'API
**Alors** un seul renouvellement part sur le réseau (promesse partagée + `navigator.locks.request('tc-refresh', …)`) et la famille n'est pas révoquée (test Playwright à deux onglets).

**Étant donné** un renouvellement au 29e jour sans activité (horloge simulée)
**Quand** il est demandé
**Alors** il réussit et la fenêtre de 30 jours repart
**Et** après 30 jours et 1 min sans activité, le renouvellement renvoie 401 et la PWA ramène à la connexion OTP.

**Étant donné** un Utilisateur connecté
**Quand** il touche « Se déconnecter » (`POST /v1/auth/logout`)
**Alors** la famille est révoquée côté serveur, le cookie est effacé, le jeton en mémoire est oublié et la PWA revient à l'écran 1
**Et** un renouvellement avec l'ancien jeton renvoie 401.

**Étant donné** un Utilisateur connecté
**Quand** il choisit « Se déconnecter de tous les appareils » (`POST /v1/auth/logout-all`)
**Alors** `token_version` est incrémenté, toutes ses familles sont révoquées et l'entrée `authz:<user_id>` de Valkey est invalidée par `after_commit`
**Et** la requête suivante avec un jeton d'accès encore valide renvoie 401 `session_revoked`, car `principal()` relit `(status, role, token_version)` dans Valkey (TTL 60 s, repli en base) à chaque requête.

**Étant donné** le test de stockage de la story 2.3
**Quand** il est rejoué après un renouvellement et après une déconnexion
**Alors** aucun jeton n'est trouvé dans `localStorage`, `sessionStorage` ni IndexedDB.

**Exigences :** FR-2, NFR-6.2, AR-12, AR-17, AR-18, UX-DR-7, UX-DR-8, AD-9, AD-17, AD-30
**Porte :** H24

### Story 2.5 : Appliquer les rôles et la propriété sur chaque route

En tant qu'Administrateur commune responsable des données,
Je veux que chaque route applique les rôles Citoyen, Collecteur, Recycleur, Modérateur et Administrateur commune et vérifie la propriété de chaque objet,
Afin qu'aucun accès non prévu ne soit possible, ce que la CI prouve à chaque modification.

**Critères d'acceptation :**

**Étant donné** l'énumération des rôles dans `core/enums.py` (`citizen`, `collector`, `recycler`, `moderator`, `municipal_admin`)
**Quand** une requête authentifiée arrive
**Alors** le rôle est lu en base via le cache `authz:<user_id>` (story 2.4), jamais dans le jeton
**Et** un test qui change le rôle en base en incrémentant `token_version` obtient 401 `session_revoked` à la requête suivante.

**Étant donné** le test de la table des routes (story 1.6, liste blanche publique close)
**Quand** on l'étend dans cette story
**Alors** chaque route `/v1` hors liste blanche déclare soit `require_role(...)`, soit son appartenance à la liste close des routes du principal appareil, ouverte ici avec `PUT /v1/device/consent` (story 1.16) ; chaque story qui crée une route du principal appareil l'y ajoute
**Et** la CI échoue si une route déclarée n'est pas couverte par le générateur route × rôle ci-dessous.

**Étant donné** le test route × rôle généré depuis la table des routes (`backend/tests/authz`)
**Quand** il appelle chaque route avec chaque principal : sans jeton ni appareil, appareil seul, Citoyen, Collecteur non vérifié, Collecteur vérifié, Recycleur, Modérateur, Administrateur commune
**Alors** tout accès non prévu échoue : 401 sans jeton, 403 avec un rôle non autorisé
**Et** les routes ajoutées par les epics suivants sont couvertes automatiquement par le même générateur
**Et** le test route × rôle sans jeton vérifie qu'aucune route renvoyant des coordonnées de Signalement n'est accessible sans jeton, hors `GET /v1/public/map`.

**Étant donné** un objet appartenant à un autre propriétaire (Signalement d'un autre compte ou d'un autre Identifiant d'appareil)
**Quand** il est demandé
**Alors** le contrôle de propriété, fait dans le service avant toute lecture, renvoie 404 sans aucune donnée
**Et** aucune route accessible hors du Personnel n'accepte le Numéro de suivi comme clé de recherche (test sur l'OpenAPI).

**Étant donné** toutes les routes accessibles à un Collecteur ou à un Recycleur
**Quand** leurs schémas de réponse sont inspectés par un test
**Alors** aucun ne contient `author_user_id`, `owner_key`, numéro de téléphone ni nom de l'auteur d'un Signalement.

**Étant donné** la table `collector_profiles` (créée par cette story : utilisateur, `verified_at`, `verified_by`)
**Quand** `auth.service.is_verified_collector(user_id)` est appelé
**Alors** il renvoie vrai seulement pour un Collecteur actif dont `verified_at` est renseigné.

**Étant donné** la commande `python -m app.cli demo load`
**Quand** elle s'exécute
**Alors** elle crée des comptes de test `is_demo = true` pour chaque rôle : au moins un Citoyen, un Collecteur vérifié, un Collecteur non vérifié, un Recycleur, un Modérateur et un Administrateur commune, avec des numéros fictifs d'une plage réservée
**Et** `demo purge` les retire.

**Étant donné** une connexion OTP réussie
**Quand** la PWA reçoit le rôle
**Alors** elle mène le Citoyen à l'écran 1, le Collecteur à l'espace Collecteur et le Personnel à l'espace commune (gabarit 1280×800, navigation au clavier, focus visible)
**Et** un espace dont les fonctions ne sont pas encore livrées affiche un état vide, et une URL d'un autre rôle affiche « Accès refusé », l'API restant la seule barrière.

**Exigences :** FR-3, FR-34, FR-37, NFR-9, NFR-6.2, AR-8, AR-17, AR-19, AR-32, UX-DR-7, UX-DR-9, UX-DR-21, AD-9, AD-10, AD-30
**Porte :** H24

### Story 2.6 : Inscrire les actions sensibles au Journal d'audit

En tant qu'Administrateur commune,
Je veux que chaque action sensible soit inscrite au Journal d'audit, en ajout seul, avec l'acteur, l'objet, l'état avant et après et l'horodatage serveur,
Afin de pouvoir rendre compte de chaque décision et qu'aucune trace ne puisse être effacée.

**Critères d'acceptation :**

**Étant donné** une migration Alembic
**Quand** elle s'applique
**Alors** les tables `audit_logs` (action, `actor_kind`, `actor_ref`, `object_type`, `object_id`, `before`, `after`, `request_id`, `occurred_at`, `is_demo`) et `audit_log_ips` (`audit_log_id`, `ip`, `created_at`) existent, sans clé étrangère vers les tables métier
**Et** `teranga_app` n'a que `INSERT` et `SELECT` sur `audit_logs`, et `INSERT`, `SELECT`, `DELETE` sur `audit_log_ips` ; un test CI vérifie qu'un `UPDATE`, un `DELETE` sur `audit_logs` et un `CREATE TABLE` par `teranga_app` sont refusés.

**Étant donné** `core.audit.record(action, actor, object_type, object_id, before, after, ip=None)` avec `Actor(kind, ref)`, `kind` ∈ {`user`, `device`, `system`}
**Quand** il est appelé dans une requête
**Alors** l'entrée est écrite dans l'unité de travail courante avec l'horodatage de `core.clock.now()` et le `request_id`
**Et** si la transaction est annulée, aucune entrée ne subsiste (test).

**Étant donné** l'énumération close `AuditAction` (`core/audit/actions.py`)
**Quand** on la compare à l'épine
**Alors** elle contient exactement `report.transition`, `report.correction`, `report.withdrawn`, `mission.transition`, `mission.assign`, `proof.review`, `account.create`, `account.verify`, `account.suspend`, `account.delete`, `account.role_change`, `mfa.enable`, `mfa.reset`, `staff.login`, `export.aggregate`, `export.corrections`, `retention.purge`
**Et** `before` et `after` se limitent aux champs modifiés, sans numéro de téléphone ni Position ; l'IP ne va que dans `audit_log_ips`.

**Étant donné** la vérification OTP (story 2.3)
**Quand** un Modérateur ou un Administrateur commune se connecte
**Alors** une entrée `staff.login` (acteur `user`, IP) est inscrite
**Et** la connexion d'un Citoyen ou d'un Collecteur n'en inscrit pas ; la première connexion qui crée un compte inscrit `account.create`.

**Étant donné** le méta-test de couverture du Journal d'audit
**Quand** la CI s'exécute
**Alors** chaque valeur d'`AuditAction` est soit prouvée par un test qui vérifie la création de l'entrée, soit listée dans `PENDING_AUDIT_ACTIONS` (fichier explicite que chaque story productrice vide)
**Et** le méta-test échoue si une valeur n'est dans aucun des deux cas ou si une valeur en attente a déjà son test.

**Étant donné** la table des routes
**Quand** le test d'architecture s'exécute
**Alors** aucune route ne permet de modifier ni de supprimer une entrée du Journal d'audit.

**Étant donné** une IP inscrite il y a 6 mois et 1 jour et une autre il y a 6 mois moins 1 jour (horloge simulée)
**Quand** `core.audit.purge_expired_ips(now)` s'exécute dans la tâche quotidienne `retention.sweep` (créée par la story 1.16)
**Alors** seule la première IP est effacée, l'entrée `audit_logs` restant intacte
**Et** la purge est inscrite par lot (`retention.purge`, nombre, catégorie, acteur `system:retention.sweep`).

**Exigences :** FR-36, NFR-17, NFR-6.1c, AR-11, AR-12, AR-23, AR-29, AR-32, AD-15, AD-17, AD-18, AD-25
**Porte :** H48

### Story 2.7 : Consulter le Journal d'audit

En tant qu'Administrateur commune,
Je veux consulter le Journal d'audit filtré par action et par période,
Afin de vérifier qui a fait quoi et quand, sans pouvoir rien y modifier.

**Critères d'acceptation :**

**Étant donné** des entrées au Journal d'audit
**Quand** l'Administrateur commune appelle `GET /v1/admin/audit-logs?action=&from=&to=&limit=&cursor=`
**Alors** la réponse `{items, next_cursor}` liste les entrées de la plus récente à la plus ancienne (`limit` ≤ 100) avec action, acteur (`kind`, référence, rôle), objet, état avant et après, horodatage serveur et `is_demo`
**Et** aucune IP ni aucun numéro de téléphone n'est renvoyé.

**Étant donné** un filtre `action` hors de `AuditAction`, une date non ISO 8601 ou `from` postérieur à `to`
**Quand** la requête est envoyée
**Alors** la réponse est 422 `invalid_filter`.

**Étant donné** un Citoyen, un Collecteur, un Recycleur ou un Modérateur
**Quand** il appelle la route
**Alors** la réponse est 403 ; sans jeton, 401 (test route × rôle).

**Étant donné** l'espace commune
**Quand** l'Administrateur commune ouvre « Journal d'audit » **[HORS MAQUETTE — UX-DR-28]**
**Alors** il voit un tableau paginé, des filtres par action (libellés i18n) et par période, un état vide « Aucune entrée sur cette période », en 1280×800, entièrement navigable au clavier avec focus visible
**Et** chaque entrée `is_demo` porte l'étiquette « Données de démonstration », et l'écran ne propose aucune action de modification.

**Exigences :** FR-36, NFR-9, NFR-12, NFR-13, AR-20, AR-29, UX-DR-28, UX-DR-6, UX-DR-7, UX-DR-9, AD-11, AD-25
**Porte :** Should, opt. H48

### Story 2.8 : Consulter et rectifier son profil

En tant qu'Utilisateur connecté,
Je veux consulter mon profil et mes Signalements, changer mon nom affiché, ma langue et mon consentement au réentraînement,
Afin d'exercer mes droits d'accès et de rectification.

**Critères d'acceptation :**

**Étant donné** une migration qui ajoute à `users` `locale` (défaut `fr`), `training_consent`, `training_consent_at`, `terms_accepted_at` et `terms_version` (`display_name` existe depuis la story 2.3)
**Quand** l'Utilisateur connecté appelle `GET /v1/me`
**Alors** il reçoit son rôle, son nom affiché, sa langue, son numéro masqué (seuls les 2 derniers chiffres visibles), son consentement au réentraînement horodaté, la date et la version de son acceptation des conditions, sa date de création et `is_demo`
**Et** un principal appareil seul reçoit 401.

**Étant donné** `PATCH /v1/me` avec `Idempotency-Key`
**Quand** il change `display_name` (1 à `DISPLAY_NAME_MAX` caractères après suppression des espaces) ou `locale` ∈ {`fr`, `wo`}
**Alors** la valeur est enregistrée et renvoyée
**Et** un nom vide ou trop long renvoie 422 `invalid_display_name`, une langue inconnue 422 `invalid_locale`, une requête sans `Idempotency-Key` 400 `idempotency_key_required`.

**Étant donné** le sélecteur de langue du profil
**Quand** l'utilisateur choisit une langue
**Alors** i18next bascule immédiatement, le choix est enregistré par `PATCH /v1/me`
**Et** `wo.json` est chargé avec repli sur `fr.json` pour toute clé absente.

**Étant donné** `GET /v1/reports/mine` (créée par cette story et ajoutée à la liste close des routes du principal appareil ; principal compte ou appareil, `limit` ≤ 100, `cursor`)
**Quand** il est appelé
**Alors** il renvoie seulement les Signalements de l'`owner_key` du principal (`user:<id>` avec un jeton valide, sinon `device:<hash>`) avec identifiant, Numéro de suivi, Statut et date de réception, du plus récent au plus ancien
**Et** jamais `owner_key` ni `author_user_id` ; un Signalement anonyme créé auparavant sur l'appareil n'apparaît pas dans la liste du compte (rattachement différé).

**Étant donné** un Citoyen connecté qui crée un Signalement
**Quand** le serveur l'accepte
**Alors** `users.training_consent` prend la valeur envoyée, horodatée
**Et** `PUT /v1/me/consent` avec `training = false` l'enregistre et émet `TrainingConsentWithdrawn` par `core.events.emit()` sous `after_commit` (`core/events.py` et `reactions.py` créés par la story 1.16), dont la réaction idempotente `reports.service.revoke_training_consent()` passe `reports.training_consent` à faux pour tout l'`owner_key` `user:<id>`.

**Étant donné** un Citoyen connecté qui envoie `consent.terms = true` avec une version de texte
**Quand** le serveur accepte le Signalement
**Alors** `users.terms_accepted_at = core.clock.now()` et `terms_version` sont enregistrés s'ils sont absents ou si la version a changé, et `GET /v1/me` les renvoie.

**Étant donné** l'écran Profil **[HORS MAQUETTE — UX-DR-29]**
**Quand** l'Utilisateur connecté l'ouvre
**Alors** il voit ses données, peut modifier son nom affiché et sa langue, voit la liste « Mes Signalements » (Numéro de suivi, Statut), le réglage du consentement au réentraînement avec son explication et le bouton « Se déconnecter »
**Et** chaque cible mesure au moins 44 px, tous les textes passent par i18next, les dates sont localisées.

**Exigences :** FR-5, FR-4, FR-3, NFR-6.1b, NFR-12, NFR-13, AR-15, AR-24, AR-30, AR-36, UX-DR-29, UX-DR-8, UX-DR-7, AD-5, AD-9, AD-10, AD-21, AD-24
**Porte :** H60

### Story 2.9 : Retirer un Signalement anonyme encore en attente

En tant que Citoyen anonyme,
Je veux retirer depuis mon appareil un Signalement encore `en attente de modération`,
Afin d'annuler un envoi fait par erreur sans créer de compte.

**Critères d'acceptation :**

**Étant donné** un Signalement `en attente de modération` créé avec mon Identifiant d'appareil
**Quand** la PWA appelle `DELETE /v1/reports/{id}` (créée par cette story et ajoutée à la liste close des routes du principal appareil) avec ce `X-Device-Id` et une `Idempotency-Key`
**Alors** la réponse est 204 et `reports.service.withdraw()` supprime la ligne, sa Position, ses photos (objet et miniature par `core.storage.purge()` en `after_commit`) et toutes ses lignes dépendantes des tables du module `reports`
**Et** une entrée `report.withdrawn` (acteur `device`) est inscrite au Journal d'audit ; ce retrait n'est pas une transition de Statut.

**Étant donné** le même Signalement
**Quand** la requête vient d'un autre Identifiant d'appareil, ou le Signalement appartient à un compte (`owner_key = user:<id>`)
**Alors** la réponse est 404 sans aucune donnée.

**Étant donné** un Signalement de mon appareil au Statut `validé`, `assigné`, `collecté` ou `rejeté` (Signalements de test insérés directement aux Statuts voulus, valeurs de `core/enums.py`)
**Quand** je demande son retrait
**Alors** la réponse est 409 `report_not_withdrawable` et rien n'est supprimé.

**Étant donné** une exception levée après la suppression dans la même requête (test)
**Quand** la transaction est annulée
**Alors** la ligne existe toujours et aucun objet n'est supprimé du stockage.

**Étant donné** un retrait déjà effectué
**Quand** la même `Idempotency-Key` est rejouée
**Alors** la même réponse 204 est rejouée ; avec une nouvelle clé, la réponse est 404
**Et** l'objet photo et sa miniature n'existent plus dans le bucket (lecture interne → 404).

**Étant donné** le méta-test du Journal d'audit (story 2.6)
**Quand** la CI s'exécute
**Alors** `report.withdrawn` a son test et n'est plus dans `PENDING_AUDIT_ACTIONS`.

**Étant donné** les réglages de l'application d'un Citoyen anonyme **[HORS MAQUETTE — UX-DR-29]**
**Quand** il ouvre la liste de ses Signalements
**Alors** le bouton « Retirer » n'apparaît que sur ceux `en attente de modération`, et une confirmation explique que le retrait est définitif
**Et** après le retrait, la liste est mise à jour et un message remercie sans culpabiliser.

**Exigences :** FR-5, FR-3, AR-12, AR-13, AR-15, AR-28, AR-29, UX-DR-29, UX-DR-10, UX-DR-7, AD-3, AD-5, AD-9, AD-13, AD-17, AD-25
**Porte :** H60

### Story 2.10 : Supprimer son compte

En tant qu'Utilisateur connecté,
Je veux supprimer mon compte depuis mon profil,
Afin que mon numéro soit effacé et que mes Signalements non validés disparaissent.

**Critères d'acceptation :**

**Étant donné** l'écran Profil
**Quand** je touche « Supprimer mon compte »
**Alors** une confirmation explique les effets : numéro effacé, Signalements `en attente de modération` ou `rejeté` supprimés avec leurs photos et Positions, Signalements ayant atteint `validé` conservés avec un auteur anonymisé, purge complète sous 30 jours.

**Étant donné** la confirmation
**Quand** la PWA appelle `DELETE /v1/me` avec `Idempotency-Key`
**Alors** `auth.service.delete_account()` efface `phone_hash` et `phone_enc`, passe `status` à `deleted`, incrémente `token_version`, révoque toutes les familles, invalide `authz:<user_id>` par `after_commit`, inscrit `account.delete` et émet `AccountDeleted`
**Et** la requête suivante avec l'ancien jeton d'accès renvoie 401 `session_revoked`, et le renouvellement 401.

**Étant donné** l'événement `AccountDeleted`
**Quand** la réaction `react:<event_id>` de `reactions.py` s'exécute
**Alors** `reports.service.detach_owner(user_id)` supprime les Signalements `en attente de modération` et `rejeté` de l'utilisateur (ligne, photos, Position, lignes dépendantes, par la même routine que la story 2.9) et met `author_user_id` à `NULL` sur ceux ayant atteint `validé` (`validé`, `assigné`, `collecté`), `owner_key` étant gardé
**Et** un test couvre un Signalement par Statut (les Signalements de test sont insérés directement aux Statuts voulus, valeurs de `core/enums.py`), et rejouer la réaction donne le même résultat.

**Étant donné** l'analyse import-linter
**Quand** la CI s'exécute
**Alors** `auth` n'importe ni `reports` ni `reactions.py`, aucun cycle n'existe, et aucune clé étrangère `ON DELETE CASCADE` ou `SET NULL` ne relie deux modules
**Et** `reactions.py` documente l'ordre d'AD-21 pour que l'epic des Missions (story 5.11) insère `missions.service.on_collector_deleted()` avant `detach_owner` sans modifier `auth`.

**Étant donné** le même numéro après suppression
**Quand** il se reconnecte par OTP
**Alors** un nouveau compte Citoyen est créé, sans lien avec l'ancien.

**Étant donné** un compte supprimé il y a 30 jours et 1 min, et un autre il y a 29 jours (horloge simulée)
**Quand** la tâche quotidienne `auth.purge_deleted_accounts` s'exécute
**Alors** seule la première ligne `users` et ses lignes `auth` dépendantes sont purgées
**Et** la purge est inscrite par lot (`retention.purge`, acteur `system:auth.purge_deleted_accounts`).

**Étant donné** le méta-test du Journal d'audit (story 2.6)
**Quand** la CI s'exécute
**Alors** `account.delete` a son test et n'est plus dans `PENDING_AUDIT_ACTIONS`.

**Exigences :** FR-5, FR-36, NFR-6.1c, AR-12, AR-18, AR-23, AR-24, AR-29, UX-DR-29, UX-DR-10, AD-1, AD-17, AD-18, AD-21, AD-25, AD-30
**Porte :** H60

### Story 2.11 : Gérer les comptes Collecteurs et les rôles

En tant qu'Administrateur commune,
Je veux créer, vérifier et suspendre un compte Collecteur et changer le rôle d'un utilisateur,
Afin que seuls des Collecteurs vérifiés puissent prendre des Missions.

**Critères d'acceptation :**

**Étant donné** l'Administrateur commune dans l'espace commune
**Quand** il appelle `POST /v1/admin/collectors` (numéro, nom affiché ; `Idempotency-Key`)
**Alors** un compte au rôle Collecteur, `status = active`, non vérifié, est créé avec sa ligne `collector_profiles`, et `account.create` est inscrit (acteur : l'Administrateur commune)
**Et** un numéro invalide renvoie 422 `invalid_phone`, un numéro qui a déjà un compte 409 `phone_already_registered`.

**Étant donné** un Collecteur non vérifié
**Quand** l'Administrateur commune appelle `POST /v1/admin/collectors/{id}/verify`
**Alors** `verified_at` et `verified_by` sont renseignés, `account.verify` est inscrit avec l'état avant et après, et `auth.service.is_verified_collector()` renvoie vrai
**Et** vérifier un utilisateur qui n'est pas Collecteur renvoie 409 `not_a_collector` ; vérifier un Collecteur déjà vérifié renvoie 200 sans nouvelle entrée.

**Étant donné** un Collecteur connecté
**Quand** l'Administrateur commune appelle `POST /v1/admin/collectors/{id}/suspend`
**Alors** `status` passe à `suspended`, `token_version` est incrémenté, ses familles sont révoquées, le cache est invalidé par `after_commit`, `account.suspend` est inscrit et `CollectorSuspended` est émis (aucune réaction n'y est abonnée dans cette story ; la story 5.11 y abonne l'annulation de la Mission `active` du Collecteur)
**Et** la requête suivante du Collecteur renvoie 401 `session_revoked`, son renouvellement 401, et une nouvelle vérification OTP 403 `account_suspended`.

**Étant donné** un utilisateur
**Quand** l'Administrateur commune appelle `PUT /v1/admin/users/{id}/role` avec un rôle de l'énumération
**Alors** le rôle est changé, `token_version` incrémenté et `account.role_change` inscrit (rôle avant et après) ; la requête suivante de l'utilisateur renvoie 401 et sa reconnexion porte le nouveau rôle
**Et** un rôle inconnu renvoie 422 ; passer au rôle Collecteur crée une ligne `collector_profiles` non vérifiée.

**Étant donné** un Citoyen, un Collecteur, un Recycleur ou un Modérateur
**Quand** il appelle l'une de ces routes ou `GET /v1/admin/collectors`
**Alors** la réponse est 403 ; sans jeton, 401 (test route × rôle).

**Étant donné** l'écran « Collecteurs » de l'espace commune **[HORS MAQUETTE — UX-DR-28]**
**Quand** l'Administrateur commune l'ouvre
**Alors** il voit la liste paginée (`GET /v1/admin/collectors`) avec nom affiché, numéro masqué, état vérifié et état du compte, un formulaire de création, les actions « Vérifier », « Suspendre » et « Changer le rôle » avec confirmation
**Et** l'écran est en 1280×800, entièrement navigable au clavier avec focus visible, et les comptes `is_demo` portent l'étiquette « Données de démonstration ».

**Étant donné** le méta-test de la story 2.6
**Quand** la CI s'exécute
**Alors** `account.verify`, `account.suspend` et `account.role_change` ont chacune leur test et ne sont plus dans `PENDING_AUDIT_ACTIONS`.

**Exigences :** FR-35, FR-36, FR-3, NFR-9, NFR-12, AR-18, AR-24, AR-29, UX-DR-28, UX-DR-6, UX-DR-7, UX-DR-9, AD-21, AD-25, AD-30
**Porte :** H60

### Story 2.12 : Se connecter avec un Second facteur (Personnel)

En tant que Modérateur ou Administrateur commune,
Je veux me connecter avec l'OTP et une application d'authentification,
Afin qu'un numéro de téléphone détourné ne suffise pas à agir sur les données de la commune.

**Critères d'acceptation :**

**Étant donné** un membre du Personnel connecté par OTP (`amr = ["otp"]`) sans Second facteur
**Quand** il ouvre l'enrôlement **[HORS MAQUETTE — UX-DR-26]** et appelle `POST /v1/auth/totp/enroll`
**Alors** un secret TOTP (RFC 6238, pas de 30 s) est généré, stocké chiffré par `TOTP_ENC_KEY` dans la table `staff_second_factors` (créée par cette story), et affiché une seule fois en QR et en texte
**Et** `POST /v1/auth/totp/confirm` avec un code valide active le Second facteur, inscrit `mfa.enable` et renvoie un jeton d'accès `amr = ["otp", "totp"]` ; un code faux renvoie 401 `totp_invalid`.

**Étant donné** un membre du Personnel dont le Second facteur est actif
**Quand** il se connecte par OTP puis appelle `POST /v1/auth/totp/verify`
**Alors** un code du pas courant ou du pas adjacent (±1) est accepté, un code plus ancien est refusé (401 `totp_invalid`)
**Et** un code déjà utilisé est refusé (401), l'`amr` est mémorisé par la famille de renouvellement et `staff.login` est inscrit avec `amr`.

**Étant donné** `STAFF_MFA_REQUIRED` vrai
**Quand** un Modérateur ou un Administrateur commune appelle une route du Personnel avec un jeton `amr = ["otp"]`
**Alors** la réponse est 403 `second_factor_required` et l'écran mène à la saisie ou à l'enrôlement du Second facteur
**Et** les routes d'enrôlement et de vérification restent accessibles avec `amr = ["otp"]`.

**Étant donné** la configuration
**Quand** l'API démarre
**Alors** `STAFF_MFA_REQUIRED` vaut faux par défaut en `dev` et `demo` et est forcé à vrai en `ENV=prod` (test).

**Étant donné** un membre du Personnel qui a perdu son application d'authentification
**Quand** un Administrateur commune appelle `POST /v1/admin/users/{id}/second-factor/reset` (`Idempotency-Key`)
**Alors** le Second facteur est supprimé, `token_version` incrémenté (la requête suivante de la personne renvoie 401), et `mfa.reset` est inscrit
**Et** un rôle hors Administrateur commune reçoit 403.

**Étant donné** le méta-test de la story 2.6
**Quand** la CI s'exécute
**Alors** `mfa.enable` et `mfa.reset` ont chacune leur test et ne sont plus dans `PENDING_AUDIT_ACTIONS`.

**Exigences :** FR-43, FR-36, NFR-6.2, AR-6, AR-18, AR-29, UX-DR-26, UX-DR-7, UX-DR-10, AD-25, AD-26, AD-30
**Porte :** pilote

## Epic 3 : L'IA propose le type de déchet

Le téléphone du Citoyen classe la photo sans réseau en moins de 3 s et propose un Type de déchet avec son Score de confiance ; sous le Seuil de confiance (60 %), le Citoyen choisit lui-même, et il peut toujours corriger en un toucher. Le serveur reclasse la même photo en tâche de fond avec la même version du Modèle, conserve les deux Classifications et lève le drapeau Désaccord IA. L'équipe IA dispose d'une chaîne `ml/` reproductible (données, entraînement, export ONNX, évaluation sur le Jeu de test figé, Fiche du Modèle, publication) et d'un Modèle factice de repli derrière la même interface, si bien que le Modèle se remplace sans toucher aux écrans ni à l'API.

**Prérequis :** Epic 1 livré (squelette, `POST /v1/reports` anonyme, écrans 1 à 4 avec Taille de tas et commentaire, worker arq, `GET /v1/config`, Données de démonstration).

### Story 3.1 : Contrat du Modèle et Modèle factice

En tant que membre de l'équipe IA,
Je veux un contrat unique du Modèle (manifeste validé, prétraitement et post-traitement de référence) et un Modèle factice qui le respecte,
Afin que l'API et la PWA puissent intégrer la classification dès H24, quel que soit l'état de l'entraînement.

**Critères d'acceptation :**

**Étant donné** le dossier `ml/` initialisé (Python 3.12.16 via `uv`, onnxruntime 1.31.1, PyTorch 2.15 / torchvision 0.29 épinglés)
**Quand** l'équipe IA ouvre `ml/contract/model-manifest.schema.json`
**Alors** le schéma (`schema_version: 1`) exige `model_version` (semver), `kind` ∈ {`trained`, `fake`}, `onnx_sha256`, `classes`, `input` (`size: 224`, `layout: NCHW`, `color: RGB`, `scale: 0-1`, `mean`, `std`, `resize: 256`, `interpolation`), `output.kind: logits`, `temperature` > 0 et `confidence_threshold`
**Et** un test CI valide chaque manifeste présent dans `ml/` contre ce schéma et échoue sur tout champ manquant ou inconnu.

**Étant donné** l'énumération `WasteType` de `backend/app/core/enums.py` (`plastic`, `metal`, `glass`, `organic`, `mixed` ; ajoutée par cette story si absente)
**Quand** la CI compare `classes` du manifeste à `WasteType`
**Alors** le test échoue si une classe manque, est en trop ou si l'ordre diffère de l'ordre des sorties du Modèle
**Et** aucune liste des 5 Types de déchet n'est recopiée en dur dans `ml/` hors du manifeste.

**Étant donné** le module de référence `ml/tc_ml/preprocess.py` et `ml/tc_ml/postprocess.py`
**Quand** une image est prétraitée puis ses logits post-traités
**Alors** le prétraitement applique dans l'ordre : `ImageOps.exif_transpose`, conversion RGB, redimensionnement du petit côté à 256 (interpolation du manifeste), recadrage central 224×224, mise à l'échelle 0-1, normalisation ImageNet (`mean`/`std` du manifeste), tenseur NCHW
**Et** le post-traitement calcule `softmax(logits / temperature)`, `predicted_type` = classe de score maximal, `confidence` = ce score, `needs_user_choice = confidence < confidence_threshold`, le seuil étant lu dans le manifeste uniquement (test : 0,5999 → `true`, 0,6000 → `false`).

**Étant donné** le script `ml/make_stub.py`
**Quand** l'équipe IA l'exécute
**Alors** il produit `tc-mnv3-0.0.0-stub.onnx` (graphe ONNX minimal, < 50 Ko, entrée `1×3×224×224`, sortie `1×5` logits constants qui ignorent le contenu de l'image) et `tc-mnv3-0.0.0-stub.json` (`kind: fake`, `confidence_threshold: 0.60`, `onnx_sha256` exact)
**Et** `ml/release/current.json` contient `{"model_version": "0.0.0-stub"}` et devient la seule source de la version courante.

**Exigences :** FR-16 ; AD-7, AD-29 (AR-39, AR-40) ; Conventions (énumérations).
**Porte :** H24

### Story 3.2 : Publication d'une version du Modèle et récupération par l'API et la PWA

En tant que membre de l'équipe IA,
Je veux publier une version du Modèle comme release GitHub et que l'API et la PWA la récupèrent automatiquement à la construction,
Afin que les deux côtés embarquent exactement la même version, sans aucun fichier `.onnx` dans Git.

**Critères d'acceptation :**

**Étant donné** un couple `.onnx` + manifeste valide (le Modèle factice de la story 3.1)
**Quand** l'équipe IA lance `ml/release/publish.py --version 0.0.0-stub`
**Alors** une release GitHub `model-v0.0.0-stub` est créée avec en assets `tc-mnv3-0.0.0-stub.onnx` et `tc-mnv3-0.0.0-stub.json`
**Et** le script refuse (code de sortie ≠ 0) si le `sha256` du fichier diffère de `onnx_sha256`, si le manifeste est invalide ou si la release existe déjà.

**Étant donné** `ml/release/current.json`
**Quand** le Dockerfile de l'API et le build Vite s'exécutent
**Alors** chacun télécharge les deux assets de la release `model-v<model_version>`, vérifie `onnx_sha256` et échoue au moindre écart
**Et** le Modèle est copié dans l'image API (`/app/models/`) et dans le dossier statique de la PWA (`web/public/model/`, ignoré par Git).

**Étant donné** la CI
**Quand** elle construit l'image API et la PWA
**Alors** elle échoue si la `model_version` embarquée par l'API diffère de celle embarquée par la PWA ou de `current.json`
**Et** elle échoue si `git ls-files` contient un fichier `*.onnx`.

**Étant donné** l'API démarrée avec le Modèle factice
**Quand** un client appelle `GET /v1/config`
**Alors** le champ `model_version` vaut `0.0.0-stub`.

**Exigences :** FR-16 ; AD-29 (AR-40), AD-28 ; NFR-5, NFR-10.
**Porte :** H24

### Story 3.3 : Classification côté serveur par le module `ai`

En tant que membre de l'équipe IA,
Je veux un module `ai` qui charge le Modèle désigné par le manifeste et expose `classify(image)`,
Afin que le serveur classe une photo exactement comme le contrat l'exige, avec le Modèle factice comme avec le Modèle entraîné.

**Critères d'acceptation :**

**Étant donné** le module `backend/app/modules/ai` (sans table, AD-2) et le Modèle factice embarqué
**Quand** `ai.service.classify(image_bytes, model_version=None)` est appelé
**Alors** il renvoie `{predicted_type, confidence, scores, model_version, needs_user_choice}` avec `scores` sur les 5 Types de déchet dont la somme vaut 1 ± 1e-6
**Et** le prétraitement et le post-traitement suivent le manifeste (`resize`, recadrage, `mean`, `std`, `temperature`, `confidence_threshold`) à l'identique de `ml/tc_ml`, vérifié par un test sur 5 images : écart ≤ 1e-3 par classe.

**Étant donné** le démarrage de l'API ou du worker
**Quand** le `sha256` du fichier `.onnx` diffère de `onnx_sha256`, ou que le réglage `CONFIDENCE_THRESHOLD` diffère de `confidence_threshold` du manifeste
**Alors** le processus refuse de démarrer avec un message explicite
**Et** la session onnxruntime (CPU) est créée une seule fois par processus et par version.

**Étant donné** un registre de versions chargées (version courante + versions précédentes déclarées dans l'image avec leur date de retrait)
**Quand** `classify` est appelé avec une `model_version` chargée
**Alors** cette version est utilisée ; avec une version inconnue ou retirée, le résultat porte la version courante
**Et** une version précédente n'est plus chargée 30 jours après la publication de la suivante (test à horloge simulée via `core.clock`).

**Étant donné** les frontières de module
**Quand** import-linter s'exécute
**Alors** seul `reports.service` importe `ai.service` (flèche `reports → ai`) et aucune route publique `/v1/ai/*` n'est exposée par Caddy.

**Étant donné** la sonde `/readyz` de la story 1.2
**Quand** on la complète dans cette story
**Alors** elle n'est prête que si la session du Modèle courant est chargée avec un `onnx_sha256` conforme au manifeste
**Et** un test qui retire le fichier `.onnx` du Modèle courant obtient 503 `{"status": "not_ready"}`, sans détail interne.

**Exigences :** FR-14, FR-16, NFR-7 ; AD-1, AD-7, AD-27, AD-29 (AR-9, AR-33, AR-39, AR-40) ; AD-23.
**Porte :** H24

### Story 3.4 : Préparation des données d'entraînement et Jeu de test figé

En tant que membre de l'équipe IA,
Je veux un jeu de données préparé à partir de TrashNet, TACO et des photos prises au Sénégal, avec un Jeu de test figé découpé par lieu et par jour,
Afin d'entraîner et d'évaluer le Modèle sans fuite entre entraînement et test.

**Critères d'acceptation :**

**Étant donné** le fichier versionné `ml/data/mapping.yaml`
**Quand** `ml/data/prepare.py` s'exécute
**Alors** chaque catégorie source de TrashNet et de TACO est associée explicitement à l'un des 5 Types de déchet ou à `exclu` (aucune valeur par défaut implicite ; le script échoue sur une catégorie non listée)
**Et** les objets TACO sont extraits par recadrage de leur boîte annotée (marge 10 %), les recadrages de moins de 64 px de côté étant exclus.

**Étant donné** les photos locales (prises au Sénégal) annotées avec Type de déchet, lieu et jour de prise de vue, stockées hors de Git dans `ML_DATA_DIR`
**Quand** le découpage est calculé
**Alors** aucun couple (lieu, jour) n'apparaît à la fois dans le Jeu de test figé et dans l'entraînement, la validation ou la calibration
**Et** le Jeu de test figé ne contient que des photos locales, au moins 150 par classe visées ; si une classe en compte moins, le script l'affiche et l'inscrit dans `ml/data/test_set.lock` (taille réelle par classe).

**Étant donné** `ml/data/test_set.lock` (versionné : `sha256`, classe, lieu, jour de chaque photo de test)
**Quand** une commande d'entraînement, de calibration ou de quantification démarre
**Alors** elle échoue si l'empreinte d'une de ses images figure dans le verrou
**Et** toute modification du verrou exige un changement de `test_set_version`, inscrit ensuite dans la Fiche du Modèle.

**Étant donné** l'annotation des photos locales
**Quand** le rapport `ml/data/annotation_report.json` est produit
**Alors** au moins 20 % des photos locales, tirées au hasard avec une graine fixée, ont été annotées une seconde fois par une autre personne, avec le taux d'accord publié
**Et** les cas ambigus sont classés `mixed`.

**Étant donné** `ml/data/sources.yaml`
**Quand** il est lu
**Alors** il liste pour TrashNet, TACO et les photos locales : origine, licence, nombre d'images retenues par classe, et confirmation « ni personne ni plaque » pour les photos locales.

**Exigences :** FR-16 ; SM-2 ; NFR-6.3d ; AR-41 (addendum §D).
**Porte :** H24

### Story 3.5 : Entraînement de MobileNetV3-Large en deux phases et calibration

En tant que membre de l'équipe IA,
Je veux entraîner MobileNetV3-Large pré-entraîné sur ImageNet en deux phases puis le calibrer par température,
Afin d'obtenir un premier Modèle entraîné dont le Score de confiance a un sens pour le Seuil de confiance.

**Critères d'acceptation :**

**Étant donné** les données préparées par la story 3.4
**Quand** l'équipe IA lance `ml/train.py --arch large --seed 42`
**Alors** la phase 1 entraîne seulement la tête de classification à 5 sorties (corps gelé), puis la phase 2 dégèle le corps avec un taux d'apprentissage plus faible
**Et** le prétraitement d'évaluation est celui de `ml/tc_ml/preprocess.py`, les augmentations n'étant appliquées qu'à l'entraînement.

**Étant donné** la fin de la phase 2
**Quand** la calibration s'exécute sur la partie validation (jamais le Jeu de test figé)
**Alors** une `temperature` unique est ajustée par minimisation de la log-vraisemblance négative et enregistrée avec le point de contrôle
**Et** l'ECE sur la validation (15 intervalles) est rapportée avant et après calibration.

**Étant donné** l'option `--arch small`
**Quand** l'équipe IA lance `ml/train.py --arch small --seed 42`
**Alors** la même commande entraîne MobileNetV3-Small sans autre modification du code (test)
**Et** cette option sert si la mesure de latence de la story 3.6 dépasse 3 s.

**Étant donné** une exécution terminée
**Quand** l'équipe IA consulte `ml/runs/<run_id>/`
**Alors** elle y trouve le point de contrôle, la configuration complète (hyperparamètres, graine, versions des bibliothèques, `test_set_version`) et les métriques de validation
**Et** relancer la même commande avec la même graine sur la même machine redonne un F1 macro de validation à ± 0,01.

**Exigences :** FR-16 ; SM-2 ; AR-41 (addendum §A, §D) ; NFR-P3 (pas d'entraînement from scratch).
**Porte :** H24

### Story 3.6 : Export ONNX, quantification INT8 QDQ statique et manifeste

En tant que membre de l'équipe IA,
Je veux exporter le Modèle entraîné en ONNX, le quantifier en INT8 QDQ statique et produire son manifeste,
Afin d'obtenir un artefact de 8 Mo au plus, identique sur l'appareil et sur le serveur.

**Critères d'acceptation :**

**Étant donné** un point de contrôle de la story 3.5
**Quand** `ml/export.py --run <run_id> --version <semver>` s'exécute
**Alors** il exporte un ONNX FP32 dont les logits diffèrent de ceux de PyTorch de 1e-3 au plus par classe sur 20 images de validation
**Et** il quantifie en INT8 au format QDQ statique (onnxruntime 1.31.1) avec environ 200 images de calibration tirées de l'entraînement, jamais du Jeu de test figé (vérifié par `test_set.lock`).

**Étant donné** l'artefact INT8 `tc-mnv3-<semver>.onnx`
**Quand** sa taille est mesurée
**Alors** elle est ≤ 8 Mo, sinon l'export échoue
**Et** le manifeste `tc-mnv3-<semver>.json` (`kind: trained`, `temperature` issue de la calibration, `confidence_threshold: 0.60`, `onnx_sha256`) est valide contre le schéma de la story 3.1.

**Étant donné** la page de banc d'essai `ml/bench/` (onnxruntime-web 1.31.1, `wasm`, `numThreads = 1`) servie localement
**Quand** l'équipe IA la lance dans Chrome sur un Android 2 Go avec 20 photos locales, Modèle déjà en cache
**Alors** la page affiche le temps de chaque classification (prétraitement compris) et le maximum
**Et** si le maximum dépasse 3 s, le résultat est consigné et l'équipe IA réentraîne en `--arch small` (story 3.5) avant toute publication.

**Exigences :** FR-11, FR-16 ; NFR-1, NFR-5 ; AD-7 (AR-39), AR-41.
**Porte :** H24

### Story 3.7 : Évaluation sur le Jeu de test figé, Fiche du Modèle et publication conditionnelle

En tant que membre de l'équipe IA,
Je veux évaluer l'artefact INT8 sur le Jeu de test figé, générer la Fiche du Modèle et ne publier que si les seuils de SM-2 sont atteints,
Afin qu'aucune version du Modèle n'atteigne les Citoyens sans qualité prouvée et documentée.

**Critères d'acceptation :**

**Étant donné** un artefact INT8 et le Jeu de test figé verrouillé
**Quand** `ml/evaluate.py --version <semver>` s'exécute avec onnxruntime (même chaîne que le serveur)
**Alors** il produit `metrics.json` avec : F1 macro, rappel par classe, ECE (15 intervalles, après calibration), top-1 accuracy, matrice de confusion et taille réelle du jeu par classe
**Et** il échoue si `test_set.lock` ne correspond pas aux fichiers présents.

**Étant donné** `metrics.json` et `ml/data/sources.yaml`
**Quand** `ml/model_card.py` génère `tc-mnv3-<semver>.card.md`
**Alors** la Fiche du Modèle contient : sources et licence de chaque source (TrashNet, TACO, photos locales), tailles des découpages, `test_set_version`, F1 macro, rappel par classe, ECE, top-1 comparée à la cible de 80 % du Proposal, matrice de confusion, architecture (Large ou Small), latence mesurée à la story 3.6, limites connues (photos sombres, tas mélangés, déchets mouillés)
**Et** si une classe a moins de 150 photos de test, la Fiche l'indique en tête avec la taille réelle.

**Étant donné** `ml/release/publish.py` étendu au `kind: trained`
**Quand** F1 macro < 0,80, ou un rappel de classe < 0,70, ou ECE > 0,10, ou que la Fiche du Modèle manque
**Alors** la publication est refusée (code de sortie ≠ 0, seuil manquant affiché) — test avec un `metrics.json` à F1 0,79 puis à 0,80
**Et** si tous les seuils sont atteints, la release `model-v<semver>` contient l'ONNX, le manifeste, la Fiche du Modèle et `metrics.json`, et `current.json` ne change que par une PR distincte.

**Exigences :** FR-16 ; SM-2 ; NFR-6.3d ; AD-29 (AR-40), AR-41.
**Porte :** H24 (premier Modèle entraîné visé ; le Modèle factice reste en place si les seuils ne sont pas atteints)

### Story 3.8 : Sélecteur des Types de déchet piloté par la proposition IA

En tant que Citoyen,
Je veux que le sélecteur des Types de déchet présélectionne la proposition de l'IA et l'annonce clairement, tout en me laissant en choisir un autre en un toucher,
Afin de comprendre la proposition de l'IA et de la corriger sans lire de texte long.

**Critères d'acceptation :**

**Étant donné** le composant `WasteTypeBadge` / `WasteTypePicker` et ses jetons `--color-waste-*` (story 1.13)
**Quand** on lui passe une proposition IA (`predicted_type`, `confidence`, `needs_user_choice`)
**Alors** le type proposé est présélectionné si `needs_user_choice` est faux, et aucun type ne l'est sinon
**Et** cette story n'ajoute aucun jeton ni aucune couleur au thème.

**Étant donné** le sélecteur affiché sur un écran 390×844
**Quand** le Citoyen touche un Type de déchet
**Alors** il est sélectionné en un seul toucher, chaque cible mesure au moins 44 × 44 px et l'état sélectionné est signalé autrement que par la couleur (coche et `aria-checked`)
**Et** le groupe est annoncé par un lecteur d'écran comme un groupe de boutons radio étiqueté, l'option proposée par l'IA étant annoncée comme telle.

**Exigences :** FR-11, FR-12, FR-13 ; UX-DR-3, UX-DR-7, UX-DR-8 ; NFR-12, NFR-13.
**Porte :** H48

### Story 3.9 : Classification locale dans la PWA

En tant que Citoyen,
Je veux que mon téléphone classe la photo lui-même, même sans réseau,
Afin d'obtenir une proposition de Type de déchet en moins de 3 s sans consommer de données.

**Critères d'acceptation :**

**Étant donné** `web/src/features/classify`
**Quand** le Modèle est chargé
**Alors** le runtime est importé par `onnxruntime-web/wasm` avec `wasmPaths` vers la PWA, `numThreads = 1`, `proxy = false`, et le Modèle n'est chargé qu'à la première capture (chargement paresseux)
**Et** la fonction `classify(jpegBlob)` renvoie `{predicted_type, confidence, scores, model_version, needs_user_choice}` en appliquant le prétraitement et le post-traitement du manifeste (seuil lu dans le manifeste uniquement).

**Étant donné** la configuration `vite-plugin-pwa`
**Quand** la PWA est construite
**Alors** le précache inclut `onnx,json,wasm,mjs` avec `maximumFileSizeToCacheInBytes` à 20 Mio
**Et** un test CI échoue si le `.onnx`, le manifeste ou `ort-wasm-simd-threaded.{wasm,mjs}` manquent du précache.

**Étant donné** la photo compressée de l'écran 2 (le JPEG orienté et compressé qui sera envoyé)
**Quand** `classify` est appelé
**Alors** il classe exactement ces octets, et non l'image brute de la caméra
**Et** sur un Android 2 Go (Chrome, Android 8+), en mode avion, Modèle en cache, chacune de 20 photos obtient son résultat en moins de 3 s entre la fin de la capture et le retour de `classify` (chronométrage consigné).

**Étant donné** un appareil dont le Modèle n'est pas encore en cache
**Quand** le Citoyen capture une photo sans réseau
**Alors** `classify` renvoie l'état `model_unavailable` sans erreur bloquante
**Et** pendant la première mise en cache en ligne, un état de chargement est exposé à l'interface.

**Exigences :** FR-11 ; NFR-1, NFR-5, NFR-6 ; AD-7, AD-16 (AR-38, AR-39) ; UX-DR-21.
**Porte :** H48

### Story 3.10 : Test doré des trois chaînes de classification

En tant que membre de l'équipe IA,
Je veux un test CI qui compare la classification de `ml/`, du serveur et du navigateur sur les mêmes images,
Afin d'éviter des Désaccords IA artificiels dus à un prétraitement ou un post-traitement divergent.

**Critères d'acceptation :**

**Étant donné** 20 images de référence versionnées dans `ml/contract/golden/` (photos sans personne ni plaque) et l'artefact désigné par `ml/release/current.json`
**Quand** la CI exécute le test doré
**Alors** les trois chaînes — évaluation `ml/` (Python), `ai.service.classify` (onnxruntime 1.31.1) et `features/classify` (onnxruntime-web 1.31.1 sous Node 26) — classent chaque image
**Et** pour chaque image, les trois donnent le même `predicted_type`, le même `needs_user_choice` et un écart de score ≤ 0,01 par classe.

**Étant donné** des logits identiques injectés dans le post-traitement Python et TypeScript
**Quand** les deux calculent `softmax(logits / temperature)`
**Alors** l'écart par classe est ≤ 1e-3
**Et** le cas limite à `confidence` = 0,60 donne `needs_user_choice = false` des deux côtés.

**Étant donné** `current.json` désignant un Modèle `kind: trained`
**Quand** le test doré s'exécute
**Alors** il porte sur l'artefact INT8 QDQ réel (et non sur un FP32)
**Et** la CI bloque la fusion si le test échoue.

**Exigences :** FR-14, FR-15, FR-16 ; AD-7 (AR-39), AD-28 (AR-8).
**Porte :** H48

### Story 3.11 : Enregistrer la Classification locale et la Correction du Citoyen

En tant que Modérateur,
Je veux que chaque Signalement conserve la proposition du Modèle local, son Score de confiance, sa version et le choix éventuel du Citoyen,
Afin de juger la photo en sachant ce que l'IA a proposé et ce que le Citoyen a corrigé.

**Critères d'acceptation :**

**Étant donné** une migration Alembic du module `reports`
**Quand** elle s'applique
**Alors** `reports` gagne `client_predicted_type`, `client_confidence`, `client_model_version` (nuls ou renseignés ensemble, contrainte `CHECK`), la colonne générée `device_type = coalesce(citizen_type, client_predicted_type)` (`citizen_type` existe depuis la story 1.11) et `flag_low_confidence` indexée
**Et** la table `corrections(report_id, actor_kind, actor_ref, original_type, original_source, model_version, corrected_type, created_at)` est créée, propriété de `reports` ; `actor_ref` est l'identifiant du Modérateur auteur de la Correction, `NULL` pour le Citoyen (dont l'auteur est celui du Signalement).

**Étant donné** `POST /v1/reports` avec `classification: {predicted_type, confidence, model_version}` et `citizen_type`
**Quand** le serveur l'accepte
**Alors** ces valeurs sont écrites dans les colonnes `client_*` et `citizen_type` seulement, jamais comme Type de déchet retenu, et le Statut reste `en attente de modération`
**Et** une `confidence` hors [0, 1], un type hors des 5 Types de déchet ou un trio incomplet est refusé en 422.

**Étant donné** un Signalement dont `citizen_type` diffère de `client_predicted_type`
**Quand** il est créé
**Alors** une ligne `corrections` est écrite (`actor_kind = citizen`, `original_source = local`, prédiction d'origine, version du Modèle, type corrigé) dans la même transaction
**Et** aucune ligne n'est écrite si le Citoyen a gardé la proposition ou s'il n'y avait pas de Classification locale.

**Étant donné** un Signalement avec `client_confidence` < 0,60
**Quand** il est créé
**Alors** `flag_low_confidence = true` ; à 0,60, `false` ; sans Classification locale, `false`
**Et** un Signalement envoyé sans Classification locale mais avec `citizen_type` est accepté.

**Exigences :** FR-12, FR-13, FR-14 ; AD-6, AD-19 (AR-16, AR-25) ; AD-2.
**Porte :** H48

### Story 3.12 : Écran 3 · Résultat IA avec Seuil de confiance et Correction

En tant que Citoyen,
Je veux voir le Type de déchet proposé avec son Score de confiance, et le changer en un toucher,
Afin d'envoyer un Signalement juste même quand l'IA hésite ou se trompe.

**Critères d'acceptation :**

**Étant donné** l'écran 3 (nœud Figma 1:57) après une capture, Modèle en cache
**Quand** `classify` renvoie un Score de confiance ≥ 60 %
**Alors** le Type de déchet proposé s'affiche avec pictogramme, couleur, libellé et Score de confiance en pourcentage, et il est présélectionné dans le sélecteur de la story 3.8
**Et** le Score affiché est tronqué à l'entier (0,599 s'affiche « 59 % »), la comparaison au Seuil de confiance se faisant sur la valeur brute.

**Étant donné** un Score de confiance forcé à 59 % (test de composant et test de bout en bout)
**Quand** l'écran 3 s'affiche
**Alors** aucun Type de déchet n'est présélectionné, une consigne demande d'en choisir un parmi les 5, et le bouton d'envoi reste désactivé tant qu'aucun n'est choisi
**Et** avec un score forcé à 60 %, le type proposé est présélectionné et l'envoi est possible (Taille de tas renseignée).

**Étant donné** un Type de déchet présélectionné
**Quand** le Citoyen touche un autre type
**Alors** la sélection change en un toucher et la requête envoie `citizen_type` avec la Classification locale d'origine
**Et** si le Citoyen revient au type proposé, `citizen_type` n'est pas envoyé
**Et** tout choix explicite fait sans présélection (score sous 60 % ou Modèle absent) est envoyé en `citizen_type`, même s'il est égal au type proposé.

**Étant donné** un Modèle absent du cache (`model_unavailable`)
**Quand** l'écran 3 s'affiche
**Alors** il indique « Modèle non disponible, choisissez le type », aucun type n'est présélectionné, l'envoi exige un choix
**Et** la requête ne contient aucun champ `classification`, si bien qu'aucun Désaccord IA ne pourra être calculé.

**Étant donné** l'écran 3 sur 390×844
**Quand** il est audité
**Alors** tous les textes passent par i18next, chaque cible mesure au moins 44 px, l'audit Lighthouse accessibilité ne signale aucune erreur de contraste ni de libellé
**Et** le sélecteur de Taille de tas et le commentaire livrés par l'Epic 1 restent inchangés.

**Étant donné** au moins 3 nouveaux utilisateurs, chacun faisant 10 essais sur un Android 2 Go (Chrome, Android 8+), Modèle en cache
**Quand** on chronomètre chaque création de Signalement de l'écran 1 à l'écran 4
**Alors** la médiane des 30 essais est inférieure à 30 s
**Et** les durées sont consignées avec l'appareil et la version de la PWA.

**Exigences :** FR-11, FR-12, FR-13 ; UX-DR-13, UX-DR-21, UX-DR-7, UX-DR-8, UX-DR-10 ; NFR-12, NFR-13 ; NFR-SM-3.
**Porte :** H48

### Story 3.13 : Classification serveur en tâche de fond

En tant que Modérateur,
Je veux que le serveur reclasse chaque photo avec la même version du Modèle, sans ralentir l'envoi du Citoyen,
Afin de disposer d'une Classification hors de portée du client pour juger le Signalement.

**Critères d'acceptation :**

**Étant donné** une migration du module `reports`
**Quand** elle s'applique
**Alors** la table `classifications(report_id, model_version, predicted_type, confidence, scores, created_at)` existe avec unicité `(report_id, model_version)`, et `reports.classification_status ∈ {pending, done, failed}` (défaut `pending`)
**Et** seule `reports.service.record_server_classification()` écrit dans `classifications`.

**Étant donné** un Signalement créé
**Quand** la transaction est validée
**Alors** la réponse 201 part sans attendre la classification et porte `classification_status: pending`
**Et** la tâche arq `classify:<report_id>:<model_version>` (`keep_result = 0`) est mise en file par `after_commit` seulement, et jamais si la transaction est annulée.

**Étant donné** la tâche en cours d'exécution
**Quand** elle classe la photo stockée (après `ImageOps.exif_transpose()`) par `ai.service.classify`
**Alors** elle utilise `client_model_version` si cette version est chargée, sinon la version courante, et enregistre une Classification serveur avec sa version, puis `classification_status = done`
**Et** une seconde exécution pour le même `(report_id, model_version)` ne crée aucune seconde ligne.

**Étant donné** une file de classification contenant déjà 500 tâches (`CLASSIFY_QUEUE_MAX`)
**Quand** un nouveau Signalement est créé
**Alors** il est accepté (201) et reste `pending` sans mise en file, et un journal structuré `classification_queue_full` est émis
**Et** la tâche planifiée `reports.requeue_pending_classifications` (toutes les minutes) remet en file les `pending` les plus anciens dès qu'il y a de la place.

**Étant donné** une photo illisible ou une erreur répétée
**Quand** la tâche échoue 3 fois
**Alors** `classification_status = failed`, le Signalement reste décidable par le Personnel et n'est plus remis en file.

**Étant donné** 100 photos de Signalement sur le serveur de démonstration
**Quand** le temps de traitement de chaque tâche (`duration_ms`, hors attente en file) est mesuré
**Alors** le p95 est inférieur à 2 s.

**Exigences :** FR-14, FR-16 ; AD-6, AD-7, AD-8, AD-17, AD-18, AD-19, AD-29 (AR-12, AR-22, AR-23, AR-25).
**Porte :** H48

### Story 3.14 : Désaccord IA et Type de déchet pré-rempli pour le Modérateur

En tant que Modérateur,
Je veux qu'un Signalement soit marqué « Désaccord IA » quand le Type de déchet envoyé par l'appareil diffère de la Classification serveur, et que le Type pré-rempli suive une règle unique,
Afin de repérer d'un coup d'œil les Signalements à examiner de près.

**Critères d'acceptation :**

**Étant donné** une migration ajoutant `reports.flag_ai_disagreement` (booléen nullable, indexé)
**Quand** `record_server_classification()` enregistre la Classification serveur
**Alors** `flag_ai_disagreement` vaut `NULL` si `client_model_version` est nul ou différent de la version serveur, sinon `device_type <> predicted_type`
**Et** la valeur est écrite une fois, jamais recalculée à la lecture.

**Étant donné** quatre Signalements de test
**Quand** leur Classification serveur est enregistrée
**Alors** prédiction locale forcée différente de la serveur → `true` ; identique → `false` ; sans Classification locale (Modèle absent du cache) → `NULL` ; version locale différente → `NULL`
**Et** un Citoyen qui a choisi un type (`citizen_type`) différent de la Classification serveur produit `true`, même si la prédiction locale était identique à la serveur.

**Étant donné** `reports.service.prefilled_type(report)`
**Quand** il est appelé
**Alors** il renvoie `citizen_type` s'il existe, sinon le `predicted_type` de la Classification serveur, sinon rien (« classification serveur en attente »)
**Et** ce Type de déchet pré-rempli est exposé dans le modèle de lecture du Personnel (`reports.service.get_for_staff()`), jamais dans une réponse au Citoyen ni au Collecteur.

**Étant donné** un Signalement créé puis classé par le serveur
**Quand** on relit ses données
**Alors** aucun Type de déchet envoyé par l'appareil n'est devenu Type de déchet retenu et le Statut est toujours `en attente de modération`.

**Exigences :** FR-14, FR-15 ; AD-19 (AR-25), AD-10.
**Porte :** H48

### Story 3.15 : Remplacer le Modèle factice par le Modèle entraîné sans toucher aux écrans ni à l'API

En tant que Citoyen,
Je veux que l'application passe au nouveau Modèle dès sa publication, sans mise à jour de ma part,
Afin de bénéficier de meilleures propositions tout en gardant le même parcours.

**Critères d'acceptation :**

**Étant donné** une release `model-v<semver>` publiée par la story 3.7
**Quand** une PR modifie seulement `ml/release/current.json` vers cette version
**Alors** la CI passe sans autre changement : diff OpenAPI vide, aucun fichier de `web/src/features/` ni de `backend/app/modules/` modifié, test doré vert
**Et** après déploiement, `GET /v1/config` renvoie la nouvelle `model_version`.

**Étant donné** une PWA installée avec l'ancien Modèle
**Quand** elle constate à l'ouverture que `GET /v1/config` renvoie une autre `model_version`
**Alors** elle met à jour son service worker, précache le nouveau Modèle et affiche un message non bloquant « Modèle mis à jour » (test Playwright)
**Et** pendant la mise à jour, une capture sans réseau utilise l'ancien Modèle encore en cache.

**Étant donné** un Signalement créé avec l'ancienne `client_model_version` après la montée de version
**Quand** le worker le classe dans les 30 jours
**Alors** la Classification serveur utilise l'ancienne version encore chargée et le Désaccord IA est calculé
**Et** au-delà de 30 jours (horloge simulée), la version courante est utilisée et `flag_ai_disagreement` vaut `NULL`.

**Étant donné** `ENV ∈ {dev, demo}` et `MODEL_VERSION=0.0.0-stub`
**Quand** l'API et le worker démarrent
**Alors** le Modèle factice est utilisé, et ce réglage est refusé au démarrage si `ENV=prod`.

**Exigences :** FR-16, FR-15 ; AD-7, AD-29 (AR-40) ; UX-DR-21 ; NFR-5.
**Porte :** H48

## Epic 4 : Modérer et suivre un signalement

Le Modérateur trie la File de modération (plus anciens d'abord, drapeaux, photo et Position), valide un Signalement en fixant le Type de déchet retenu (pré-rempli par le choix du Citoyen, sinon par la Classification serveur, décision T-03) ou le rejette avec un motif obligatoire ; chaque changement de Statut passe par une porte unique qui l'historise et l'inscrit au Journal d'audit. Le Citoyen, connecté ou anonyme, suit ses Signalements sur la Frise de suivi, voit à l'ouverture les changements survenus depuis sa dernière visite et, s'il est connecté et l'a autorisé, reçoit une notification push.

Les Corrections des Signalements validés et consentis sont exportées comme exemples étiquetés (story 4.6), puis servent au réentraînement mensuel du pilote (story 4.11).

**Prérequis :** Epic 1 livré ; stories 2.1 à 2.6 pour les stories 4.1 à 4.6 (porte H48) ; stories 2.8 (`GET /v1/reports/mine`) et 2.10 (`AccountDeleted`) en plus pour les stories 4.7 à 4.10 (porte H60) ; story 3.7 en plus pour la story 4.11 (pilote). Les stories 3.11 (`corrections`) et 3.14 (`prefilled_type()`, `get_for_staff()`) sont requises par 4.1 et 4.3 ; la Classification serveur (tâche de la story 3.13) n'a pas à être passée : sans elle, la File affiche « classification serveur en attente », le Modérateur décide quand même, et les drapeaux IA (Désaccord IA, « faible confiance ») ne s'affichent que s'ils existent.

### Story 4.1 : Consulter la File de modération

En tant que Modérateur,
Je veux voir les Signalements `en attente de modération`, les plus anciens d'abord, avec photo, Position, Type de déchet et drapeaux,
Afin de les trier vite et de n'exposer aux Collecteurs que des photos vues par un humain.

**Critères d'acceptation :**

**Étant donné** des Signalements à divers Statuts
**Quand** un Modérateur appelle `GET /v1/moderation/queue?limit=&cursor=&flag=`
**Alors** la réponse `{items, next_cursor}` ne contient que des Signalements `en attente de modération`, triés par horodatage serveur de réception croissant (puis par identifiant)
**Et** au plus 50 éléments par page (défaut 50) ; `limit` > 50 renvoie 422 `invalid_limit`.

**Étant donné** un élément de la File
**Quand** il est sérialisé par `reports.service.get_for_staff()` (créé par la story 3.14, étendu ici)
**Alors** il porte le Numéro de suivi, la réception, une URL signée de 5 min de la photo sur `MEDIA_HOST`, la Position précise (`core.geo.expose(…, precise)` ; `core.geo.expose()` et ses niveaux `precise`, `approx`, `rounded`, `aggregated`, `none` sont créés par cette story) et sa précision en mètres, la Zone, la Taille de tas, le commentaire, le Type de déchet envoyé par l'appareil et son Score de confiance, `classification_status` et la Classification serveur, et les drapeaux `ai_disagreement`, `low_confidence`, `imprecise_position`, `duplicate_of` (identifiant et Numéro de suivi du Signalement d'origine), plus `is_demo`
**Et** tout champ dont la donnée n'existe pas (Classification locale absente, Classification serveur pas encore faite, Désaccord IA non calculable) vaut `null`, sans erreur.

**Étant donné** `core.storage.signed_url(object_key, ttl=300)` (créée par cette story, client S3 public, `MEDIA_HOST`)
**Quand** l'URL a plus de 5 min
**Alors** Garage la refuse
**Et** une URL de moins de 5 min sert l'objet sans poser de cookie.

**Étant donné** un Signalement sans Classification serveur (`classification_status = pending` ou `failed`)
**Quand** il s'affiche dans la File
**Alors** la mention « classification serveur en attente » apparaît et les actions de décision restent disponibles
**Et** un drapeau dont la valeur est `null` n'est pas affiché.

**Étant donné** le paramètre `flag` ∈ {`ai_disagreement`, `duplicate`, `low_confidence`, `imprecise_position`} (une ou plusieurs valeurs séparées par des virgules)
**Quand** la File est filtrée
**Alors** seuls les Signalements portant tous ces drapeaux sont renvoyés ; un drapeau encore indisponible donne une liste vide
**Et** une valeur inconnue renvoie 422 `invalid_filter`.

**Étant donné** un Doublon probable
**Quand** le Modérateur suit le lien « Signalement d'origine »
**Alors** `GET /v1/moderation/reports/{id}` (créée par cette story, tout Statut) affiche l'original avec les mêmes champs
**Et** si l'original a été retiré, la réponse est 404 et l'écran affiche « Signalement d'origine retiré ».

**Étant donné** un Modérateur ou un Administrateur commune
**Quand** il appelle `GET /v1/staff/reports?status=&limit=&cursor=` (créée par cette story : Signalements du Statut demandé, plus anciens d'abord, `limit` ≤ 100, mêmes champs que la File) ou `GET /v1/moderation/reports/{id}`
**Alors** il reçoit 200 en lecture seule
**Et** l'Administrateur commune reçoit 403 sur la File (`GET /v1/moderation/queue`) ; les routes de décision des stories 4.3 et 4.4 sont réservées au Modérateur.

**Étant donné** un Citoyen, un Collecteur ou un Recycleur
**Quand** il appelle les routes `/v1/moderation/*` ou `GET /v1/staff/reports`
**Alors** la réponse est 403 ; sans jeton, 401 (test route × rôle de la story 2.5).

**Étant donné** l'espace commune d'un Modérateur
**Quand** il ouvre la File de modération **[HORS MAQUETTE — UX-DR-27]**
**Alors** il voit, en 1280×800, chaque élément avec miniature (story 1.11) et texte alternatif, badge du Type de déchet (pictogramme + libellé, composant `WasteTypeBadge` de la story 1.13), Score de confiance, Position et précision, drapeaux en badges pictogramme + libellé (jamais la couleur seule), filtres par drapeau, pagination et l'état vide « Aucun Signalement en attente »
**Et** la liste se rafraîchit toutes les 15 s, la navigation est complète au clavier (Tab, Entrée pour ouvrir le détail) avec focus visible, et un élément `is_demo` porte l'étiquette « Données de démonstration ».

**Exigences :** FR-22, FR-3, FR-26, FR-28, FR-36, NFR-6.1b, NFR-12, NFR-13, AR-19, AR-20, AR-25, AR-28, UX-DR-27, UX-DR-28, UX-DR-21, UX-DR-3, UX-DR-6, UX-DR-7, UX-DR-9, AD-9, AD-10, AD-11, AD-13, AD-19
**Porte :** H48

### Story 4.2 : Tracer chaque changement de Statut par une porte unique

En tant que membre du Personnel,
Je veux que tout changement de Statut passe par une seule porte qui le vérifie, l'historise et l'inscrit au Journal d'audit, et voir cet historique dans le détail d'un Signalement,
Afin de faire confiance à chaque Statut affiché et de pouvoir rendre compte de chaque décision.

**Critères d'acceptation :**

**Étant donné** la table de transitions constante de `reports` : `pending_review → validated`, `pending_review → rejected`, `validated → assigned`, `assigned → collected`, `assigned → validated`
**Quand** `reports.service.transition(report_id, from_status, to_status, actor, reason, set_fields=None)` est appelée pour chacun des 25 couples de Statuts (test paramétré)
**Alors** les 5 couples prévus réussissent ; les 20 autres renvoient 409 `invalid_transition` sans rien modifier (Statut, historique et Journal d'audit inchangés)
**Et** un test d'architecture vérifie qu'aucun autre code n'écrit `reports.status`.

**Étant donné** une transition prévue
**Quand** elle s'exécute dans l'unité de travail courante
**Alors** elle fait `UPDATE … WHERE id = :id AND status = :from` (avec `set_fields`), écrit une ligne dans `report_status_events` (table créée par cette story : Signalement, Statut de départ, Statut d'arrivée, motif, détail du motif, `actor_kind`, `occurred_at` par `core.clock`) et inscrit `report.transition` (Statut avant et après, acteur) au Journal d'audit
**Et** si l'`UPDATE` ne touche aucune ligne (Statut déjà changé), la réponse est 409 `invalid_transition` et rien n'est écrit.

**Étant donné** une exception levée dans la même requête après l'appel à `transition()` (test)
**Quand** l'unité de travail est annulée
**Alors** il ne reste ni changement de Statut, ni ligne `report_status_events`, ni entrée d'audit, et aucun effet enregistré par `after_commit` n'est exécuté.

**Étant donné** deux transitions concurrentes depuis le même Statut sur le même Signalement
**Quand** elles s'exécutent en parallèle
**Alors** une seule réussit, l'autre reçoit 409 `invalid_transition`
**Et** il n'existe qu'une ligne d'historique et une entrée d'audit.

**Étant donné** la création d'un Signalement (Epic 1)
**Quand** le serveur l'accepte
**Alors** un événement initial `NULL → pending_review` est écrit dans `report_status_events` avec l'horodatage de réception
**Et** une migration crée cet événement initial pour chaque Signalement existant, Données de démonstration comprises.

**Étant donné** le détail d'un Signalement ouvert par un Modérateur ou un Administrateur commune (`GET /v1/moderation/reports/{id}`, story 4.1)
**Quand** il s'affiche
**Alors** l'historique des Statuts (Statut d'arrivée, motif, nature de l'acteur, horodatage) est listé dans l'ordre chronologique, lu dans `report_status_events` uniquement
**Et** aucune route destinée au Citoyen, au Collecteur ou au Recycleur ne renvoie cet historique avec l'acteur.

**Étant donné** une transition réussie
**Quand** l'unité de travail est validée
**Alors** `ReportStatusChanged` (`event_id` de `report_status_events`, Numéro de suivi, `owner_key`, `author_user_id`, nouveau Statut, motif) est émis par `core.events.emit()` (story 1.16) en `after_commit`, sans abonné à ce stade
**Et** aucune émission n'a lieu si la transaction est annulée (test).

**Étant donné** le méta-test du Journal d'audit (story 2.6)
**Quand** la CI s'exécute
**Alors** `report.transition` a son test et n'est plus dans `PENDING_AUDIT_ACTIONS`.

**Exigences :** FR-21, FR-23, FR-36, AR-12, AR-13, AR-16, AR-24, AR-29, UX-DR-27, UX-DR-7, AD-3, AD-6, AD-17, AD-21, AD-25
**Porte :** H48

### Story 4.3 : Valider un Signalement et fixer le Type de déchet retenu

En tant que Modérateur,
Je veux valider un Signalement en confirmant ou en corrigeant en un clic le Type de déchet pré-rempli,
Afin que les Collecteurs ne voient que des Signalements vérifiés, avec le bon Type de déchet retenu.

**Critères d'acceptation :**

**Étant donné** le détail d'un Signalement `en attente de modération`
**Quand** il s'affiche
**Alors** le Type de déchet pré-rempli suit `reports.service.prefilled_type()` (story 3.14) : choix du Citoyen s'il existe, sinon Classification serveur si elle existe, sinon aucun, avec la consigne « Choisissez le Type de déchet »
**Et** le sélecteur des 5 Types de déchet (pictogramme + libellé) permet de corriger en un clic.

**Étant donné** `POST /v1/moderation/reports/{id}/validate` avec `retained_type` et `Idempotency-Key`
**Quand** le Modérateur valide
**Alors** `reports.service.validate()` appelle `transition(pending_review → validated)` avec `retained_type` dans `set_fields` ; la colonne `reports.retained_type` (ajoutée par cette story, `CHECK` non nul dès `validated`, Données de démonstration complétées par la migration) n'est écrite que par ce chemin
**Et** la réponse 200 renvoie le nouveau Statut et le Type de déchet retenu.

**Étant donné** une requête sans `retained_type`, avec un type hors des 5 Types de déchet ou sans `Idempotency-Key`
**Quand** elle est envoyée
**Alors** la réponse est respectivement 422 `retained_type_required`, 422 `invalid_waste_type` ou 400 `idempotency_key_required`, et rien n'est modifié.

**Étant donné** un Type de déchet retenu différent du type pré-rempli
**Quand** la validation réussit
**Alors** une ligne `corrections` est écrite dans la même transaction (`actor_kind = moderator`, `actor_ref` = identifiant du Modérateur, type d'origine, `original_source` = `citizen` ou `server`, version du Modèle si elle existe, type corrigé) et `report.correction` est inscrit au Journal d'audit
**Et** aucune Correction n'est écrite si le type retenu égale le type pré-rempli ou s'il n'y avait aucun type pré-rempli ; la table `corrections` est celle de la story 3.11.

**Étant donné** une validation réussie
**Quand** la même `Idempotency-Key` est rejouée
**Alors** la même réponse 200 est rejouée sans seconde ligne d'historique ni seconde entrée d'audit
**Et** avec une nouvelle clé, la réponse est 409 `invalid_transition`.

**Étant donné** un Signalement `en attente de modération` ou `rejeté`
**Quand** le test route × rôle appelle toute route accessible à un Collecteur ou à un Recycleur
**Alors** aucune réponse ne contient ce Signalement.

**Étant donné** le détail dans l'espace commune **[HORS MAQUETTE — UX-DR-27]**
**Quand** le Modérateur touche « Valider »
**Alors** le Signalement quitte la File, le suivant s'ouvre, et l'action est réalisable entièrement au clavier
**Et** une erreur 409 affiche « Ce Signalement a déjà été traité » et rafraîchit la File.

**Étant donné** le méta-test du Journal d'audit
**Quand** la CI s'exécute
**Alors** `report.correction` a son test et n'est plus dans `PENDING_AUDIT_ACTIONS`.

**Exigences :** FR-23, FR-13, FR-36, FR-3, AR-13, AR-15, AR-25, AR-29, UX-DR-27, UX-DR-3, UX-DR-7, UX-DR-8, AD-3, AD-5, AD-17, AD-19, AD-25
**Porte :** H48

### Story 4.4 : Rejeter un Signalement avec un motif obligatoire

En tant que Modérateur,
Je veux rejeter un Signalement en choisissant un motif obligatoire,
Afin d'écarter le spam, les doublons et les photos inacceptables en expliquant pourquoi au Citoyen.

**Critères d'acceptation :**

**Étant donné** `POST /v1/moderation/reports/{id}/reject` avec `reason` ∈ {`spam`, `not_waste`, `outside_zone`, `duplicate`, `person_or_plate_visible`, `other`} et `Idempotency-Key`
**Quand** le Modérateur rejette un Signalement `en attente de modération`
**Alors** `transition(pending_review → rejected)` enregistre le motif dans `report_status_events` et le Journal d'audit, et la réponse 200 renvoie le Statut `rejeté`.

**Étant donné** une requête sans motif, avec un motif inconnu, ou `other` sans texte non vide
**Quand** elle est envoyée
**Alors** la réponse est respectivement 422 `reject_reason_required`, 422 `invalid_reject_reason` ou 422 `reject_reason_detail_required`, et rien n'est modifié.

**Étant donné** le motif `duplicate`
**Quand** le rejet est envoyé
**Alors** `duplicate_of_report_id` est obligatoire, pré-rempli par l'écran avec le Signalement d'origine du drapeau Doublon probable s'il existe
**Et** son absence renvoie 422 `duplicate_of_required` ; un identifiant inexistant ou égal au Signalement rejeté renvoie 422 `invalid_duplicate_of`
**Et** `reject()` écrit l'identifiant du Signalement d'origine dans le détail du motif de la ligne `report_status_events` du rejet ; c'est la seule source du Numéro de suivi d'origine montré au Citoyen (stories 4.7 et 4.8).

**Étant donné** un Signalement `rejeté`
**Quand** un Modérateur tente de le valider ou de le rejeter de nouveau
**Alors** la réponse est 409 `invalid_transition` (Statut terminal).

**Étant donné** le motif `person_or_plate_visible`
**Quand** le rejet est validé
**Alors** dès cet instant, plus aucune réponse de l'API ne contient d'URL signée pour cette photo, Personnel compris.

**Étant donné** le dialogue « Rejeter » du détail **[HORS MAQUETTE — UX-DR-27]**
**Quand** le Modérateur l'ouvre
**Alors** il voit les 6 motifs (libellés i18n : spam, pas un déchet, hors zone, doublon, personne ou plaque visible, autre), un champ texte obligatoire pour « autre », et pour « doublon » le Numéro de suivi d'origine présélectionné
**Et** le bouton « Rejeter » reste désactivé tant que le motif est incomplet, et tout le dialogue est utilisable au clavier.

**Étant donné** la commande `python -m app.cli demo load`
**Quand** elle s'exécute après les chargements des modules précédents
**Alors** le service `reports` ajoute ses Données de démonstration par ses propres règles (`validate()` et `reject()`) : au moins 5 Signalements `validé` avec Type de déchet retenu et 3 `rejeté` dont un `duplicate`, tous `is_demo = true`
**Et** `demo purge` les retire, et un second `demo load` ne les duplique pas.

**Exigences :** FR-23, FR-36, FR-37, AR-13, AR-15, AR-29, AR-32, UX-DR-27, UX-DR-7, UX-DR-8, UX-DR-10, AD-3, AD-5, AD-10, AD-14, AD-25
**Porte :** H48

### Story 4.5 : Effacer sous 24 h la photo d'un rejet « personne ou plaque visible »

En tant qu'Administrateur commune responsable des données,
Je veux que la photo d'un Signalement rejeté parce qu'une personne ou une plaque y est visible soit supprimée du stockage sous 24 h,
Afin que l'image d'une personne photographiée par erreur ne soit pas conservée.

**Critères d'acceptation :**

**Étant donné** un Signalement rejeté avec le motif `person_or_plate_visible` dont la photo est encore stockée
**Quand** la tâche planifiée `reports.purge_person_visible_photos` s'exécute (toutes les heures, `cron_jobs` arq)
**Alors** l'objet photo et sa miniature éventuelle sont supprimés par `core.storage.purge()` (story 1.10) en `after_commit`, et la ligne photo est marquée purgée (colonne `report_photos.purged_at`, ajoutée par la migration de cette story)
**Et** la décision reste dans `report_status_events` et au Journal d'audit, et la purge est inscrite par lot (`retention.purge`, nombre, catégorie, acteur `system:reports.purge_person_visible_photos`).

**Étant donné** un rejet à l'instant T (horloge simulée)
**Quand** la tâche s'exécute à T + 1 h
**Alors** la photo n'existe plus dans le stockage et l'ancienne URL signée ne fonctionne plus
**Et** le délai garanti reste inférieur à 24 h (test à T + 23 h 59 min sur une exécution manquée puis rattrapée).

**Étant donné** une photo déjà purgée
**Quand** la tâche s'exécute de nouveau
**Alors** rien n'est fait et aucune nouvelle entrée d'audit n'est créée.

**Étant donné** une erreur du stockage pendant la suppression
**Quand** la tâche se termine
**Alors** la ligne photo n'est pas marquée purgée et sera reprise à l'exécution suivante.

**Étant donné** le détail du Signalement dans l'espace commune
**Quand** la photo est purgée
**Alors** l'écran affiche « Photo supprimée (personne ou plaque visible) » à la place de l'image.

**Étant donné** `retention.sweep` (story 1.16) et une horloge simulée
**Quand** la tâche s'exécute
**Alors** les photos (et miniatures) de Signalements `rejeté` depuis plus de `REJECTED_PHOTO_RETENTION_DAYS` (30, date lue dans `report_status_events`) et de Signalements reçus depuis plus de `REPORT_PHOTO_RETENTION_DAYS` (365) sont purgées par `core.storage.purge()`, l'ancienne URL signée ne fonctionne plus, et la purge est inscrite par lot (`retention.purge`)
**Et** une photo de 29 jours après le rejet, ou de 364 jours après la réception, est conservée.

**Exigences :** FR-23, NFR-6.1c, AR-12, AR-23, AR-28, AR-29, UX-DR-27, AD-13, AD-17, AD-18, AD-25
**Porte :** H48

### Story 4.6 : Export des Corrections consenties comme exemples étiquetés

En tant que membre de l'équipe IA,
Je veux exporter les Corrections des Signalements ayant atteint `validé` dont l'auteur a consenti au réentraînement,
Afin de réentraîner le Modèle uniquement sur des exemples vérifiés par un humain et autorisés.

**Critères d'acceptation :**

**Étant donné** `reports.service.export_corrections()` et la commande `python -m app.cli ml export-corrections --out <archive>`
**Quand** l'équipe IA l'exécute
**Alors** l'archive contient un fichier JSONL (`report_id`, `actor_kind`, `original_type`, `original_source`, `model_version`, `corrected_type`, `created_at`, nom de la photo) et les photos stockées correspondantes (JPEG sans EXIF)
**Et** elle ne contient ni Position, ni commentaire, ni auteur (`actor_ref` de la story 3.11 n'est pas exporté), ni `owner_key`, ni Identifiant d'appareil, ni Numéro de suivi.

**Étant donné** un jeu d'essai de Signalements avec Corrections : un ayant atteint `validé` avec consentement, un `validé` sans consentement, un dont le consentement a été retiré après création, un `rejeté`, un `en attente de modération`
**Quand** l'export s'exécute
**Alors** seul le premier apparaît ; « ayant atteint `validé` » se lit dans `report_status_events` (story 4.2 ; un Signalement `collecté` est inclus)
**Et** `training_consent` est évalué au moment de l'export.

**Étant donné** un export réalisé
**Quand** on consulte le Journal d'audit
**Alors** une entrée `export.corrections` (acteur `system:export_corrections`, nombre d'exemples, horodatage serveur) existe
**Et** la commande est refusée si `ENV=prod` et que l'opérateur n'a pas fourni `--confirm`.

**Étant donné** le méta-test du Journal d'audit (story 2.6)
**Quand** la CI s'exécute
**Alors** `export.corrections` a son test et n'est plus dans `PENDING_AUDIT_ACTIONS`.

**Exigences :** FR-13, FR-4, FR-36 ; AD-24, AD-25 (AR-29, AR-30) ; AD-3.
**Porte :** H48

### Story 4.7 : Suivre ses Signalements sur la Frise de suivi

En tant que Citoyen, connecté ou anonyme,
Je veux voir mes Signalements avec leur Numéro de suivi, leur Statut et la Frise de suivi,
Afin de savoir ce que devient chaque dépôt que j'ai signalé.

**Critères d'acceptation :**

**Étant donné** `GET /v1/reports/mine` (story 2.8)
**Quand** il est appelé par le propriétaire
**Alors** chaque élément porte aussi l'étape de la Frise de suivi, et pour un `rejeté` le code et le libellé du motif (texte pour `other`) et, pour un doublon, le Numéro de suivi du Signalement d'origine (lu depuis le détail du motif de l'événement de rejet, story 4.4)
**Et** aucun élément ne contient l'auteur, `owner_key`, la Classification serveur ni l'historique avec acteur.

**Étant donné** le composant Frise de suivi (créé par la story 1.13, complété ici)
**Quand** il affiche un Signalement
**Alors** il montre 4 étapes avec pictogramme + libellé : « Signalé », « Validé par la modération », « Assigné à un collecteur », « Collecté, preuve photo », l'étape courante distinguée autrement que par la couleur (pictogramme et graisse)
**Et** pour un `rejeté`, les étapes suivantes sont remplacées par « Rejeté » avec le motif (et le Numéro de suivi d'origine pour un doublon) ; c'est une liste ordonnée dont l'étape courante est annoncée aux lecteurs d'écran (`aria-current="step"`).

**Étant donné** l'écran 1
**Quand** le Citoyen l'ouvre
**Alors** la liste « Mes Signalements » affiche, du plus récent au plus ancien, Numéro de suivi, Statut et Frise de suivi, avec l'état vide « Vous n'avez pas encore signalé de dépôt »
**Et** un élément `en attente d'envoi` n'a ni Numéro de suivi ni frise (la File hors-ligne de l'Epic 6 complète cet affichage ; sans elle, rien à afficher).

**Étant donné** l'écran 4 après un envoi réussi
**Quand** la réponse du serveur arrive
**Alors** le Numéro de suivi `TC-AAAA-NNNNNN` s'affiche avec la Frise de suivi à l'étape « Signalé ».

**Étant donné** l'application ouverte sur l'écran 1
**Quand** un Modérateur change le Statut d'un de mes Signalements
**Alors** le nouveau Statut s'affiche au plus 15 s après (TanStack Query, rafraîchissement 15 s tant que l'application est visible ; test de bout en bout).

**Étant donné** un Signalement créé sur l'appareil A
**Quand** l'appareil B (autre Identifiant d'appareil) ou un autre compte appelle `GET /v1/reports/mine`
**Alors** ce Signalement n'apparaît pas
**Et** une requête qui ne présente que le Numéro de suivi ne reçoit aucune donnée.

**Étant donné** l'écran de consentement (story 1.7)
**Quand** un Citoyen anonyme le lit
**Alors** il est informé qu'en réinstallant l'application ou en effaçant les données du navigateur il perd sa liste (avertissement de la story 1.7), et un lien « Créer un compte », ajouté par cette story, mène à la connexion OTP.

**Étant donné** un Signalement `is_demo`
**Quand** il s'affiche dans la liste
**Alors** il porte l'étiquette « Données de démonstration ».

**Exigences :** FR-20, FR-23, FR-3, NFR-12, NFR-13, AR-19, AR-36, UX-DR-4, UX-DR-11, UX-DR-15, UX-DR-24, UX-DR-6, UX-DR-7, UX-DR-10, AD-9, AD-10, AD-16
**Porte :** H60

### Story 4.8 : Voir les changements de Statut depuis sa dernière visite

En tant que Citoyen, connecté ou anonyme,
Je veux voir à l'ouverture de l'application chaque changement de Statut de mes Signalements survenu depuis ma dernière visite,
Afin d'être informé sans notification par SMS.

**Critères d'acceptation :**

**Étant donné** `GET /v1/reports/mine/changes?cursor=&limit=` (créée par cette story et ajoutée à la liste close des routes du principal appareil ; principal compte ou appareil)
**Quand** il est appelé
**Alors** il renvoie, dans l'ordre chronologique, les lignes `report_status_events` postérieures au curseur pour les Signalements de l'`owner_key` du principal, hors événement initial de création : identifiant de l'événement, Numéro de suivi, nouveau Statut, motif si `rejeté` (et Numéro de suivi d'origine pour un doublon, lu depuis le détail du motif de l'événement, story 4.4), horodatage
**Et** `next_cursor` est opaque ; aucune donnée d'un autre appareil ou d'un autre compte n'est renvoyée (test).

**Étant donné** le dernier curseur vu mémorisé dans la table Dexie `meta`
**Quand** l'application s'ouvre ou revient au premier plan
**Alors** l'écran 1 affiche un bloc « Depuis votre dernière visite » listant chaque changement (Numéro de suivi, nouveau Statut avec pictogramme + libellé, motif si `rejeté`)
**Et** le curseur est enregistré après affichage : une réouverture sans nouveau changement n'affiche pas le bloc.

**Étant donné** 3 changements sur 2 Signalements survenus application fermée
**Quand** le Citoyen rouvre l'application
**Alors** les 3 changements s'affichent dans l'ordre où ils sont survenus.

**Étant donné** un premier lancement sans curseur mémorisé
**Quand** l'application s'ouvre
**Alors** tous les changements des Signalements du principal sont listés (paginés), puis le curseur est mémorisé.

**Étant donné** un Citoyen anonyme
**Quand** il ouvre l'application
**Alors** il voit ses changements par son Identifiant d'appareil, comme un Citoyen connecté par son compte.

**Exigences :** FR-21, FR-3, AR-13, AR-38, UX-DR-22, UX-DR-11, UX-DR-4, UX-DR-8, AD-3, AD-9, AD-16
**Porte :** H60

### Story 4.9 : S'abonner aux notifications push

En tant que Citoyen connecté,
Je veux autoriser les notifications push de l'application au bon moment, et pouvoir les retirer,
Afin de choisir d'être informé même application fermée.

**Critères d'acceptation :**

**Étant donné** le module `notifications`
**Quand** sa migration s'applique
**Alors** elle crée seulement la table `push_subscriptions` (utilisateur, `endpoint`, `p256dh`, `auth`, création)
**Et** `GET /v1/config` expose la clé publique VAPID, la clé privée étant lue depuis `/run/secrets` (`VAPID_PRIVATE_KEY`).

**Étant donné** un Citoyen connecté qui vient d'envoyer un Signalement, ou qui ouvre son profil
**Quand** la PWA lui propose les notifications **[HORS MAQUETTE — UX-DR-22]**
**Alors** la demande d'autorisation du navigateur n'est déclenchée qu'après son accord dans l'écran, et un refus n'est pas redemandé à chaque ouverture
**Et** un Citoyen anonyme ne voit jamais cette proposition.

**Étant donné** `POST /v1/me/push-subscriptions` avec `Idempotency-Key`
**Quand** un Utilisateur connecté l'appelle
**Alors** l'abonnement est enregistré (un même `endpoint` ne crée qu'une ligne) ; `DELETE /v1/me/push-subscriptions/{id}` le retire
**Et** un principal appareil seul reçoit 401, et l'abonnement d'un autre utilisateur 404.

**Étant donné** l'événement `AccountDeleted` (story 2.10)
**Quand** sa réaction s'exécute
**Alors** les abonnements push de l'utilisateur sont supprimés (réaction idempotente).

**Exigences :** FR-21, FR-5, NFR-6.1a, AR-6, AR-24, AR-42, UX-DR-22, UX-DR-7, UX-DR-8, AD-5, AD-21, AD-26
**Porte :** H60

### Story 4.10 : Recevoir une notification push de changement de Statut

En tant que Citoyen connecté abonné,
Je veux recevoir une notification push quand le Statut d'un de mes Signalements change,
Afin d'être informé même application fermée.

**Critères d'acceptation :**

**Étant donné** le module `notifications`
**Quand** la migration de cette story s'applique
**Alors** elle crée seulement la table `notifications` (unicité sur `status_event_id`, utilisateur, envoi, résultat).

**Étant donné** l'événement `ReportStatusChanged` émis par la story 4.2
**Quand** la réaction de `reactions.py` appelle `notifications.service.push()` par la tâche `notify:<status_event_id>`
**Alors** chaque abonnement de l'auteur reçoit une notification indiquant le Numéro de suivi, le nouveau Statut et, pour `rejeté`, le motif, sans Position, photo ni identité
**Et** si `author_user_id` est nul (Signalement anonyme ou compte supprimé), aucune notification ne part.

**Étant donné** le même événement traité deux fois
**Quand** la tâche se rejoue
**Alors** une seule notification est envoyée (unicité `notifications.status_event_id`).

**Étant donné** un service push de test local
**Quand** un Modérateur valide un Signalement d'un Citoyen connecté abonné
**Alors** la notification est reçue au plus 1 min après l'horodatage du changement de Statut (test d'intégration).

**Étant donné** un service push qui répond 404 ou 410 pour un abonnement
**Quand** l'envoi échoue
**Alors** l'abonnement est supprimé ; une réponse 5xx est réessayée par arq avec un nombre d'essais borné.

**Étant donné** une notification reçue
**Quand** le Citoyen la touche
**Alors** la PWA s'ouvre sur l'écran 1 au Signalement concerné ; le titre et le texte viennent d'i18next.

**Étant donné** l'analyse import-linter
**Quand** la CI s'exécute
**Alors** `reports` n'importe pas `notifications`, `notifications` n'importe que `auth.service`, et seul `reactions.py` relie les deux.

**Exigences :** FR-21, NFR-6.1a, AR-12, AR-22, AR-24, AR-42, UX-DR-22, UX-DR-8, AD-1, AD-8, AD-17, AD-21
**Porte :** H60

### Story 4.11 : Réentraînement mensuel sur les Corrections exportées

En tant que membre de l'équipe IA,
Je veux réentraîner le Modèle au plus une fois par mois sur les Corrections exportables, avec la même porte de publication,
Afin que la part de classifications corrigées baisse pendant le pilote sans jamais dégrader le Modèle publié.

**Critères d'acceptation :**

**Étant donné** une archive produite par la story 4.6
**Quand** `ml/train.py --corrections <archive>` s'exécute
**Alors** les exemples sont ajoutés à l'entraînement ou à la validation, jamais au Jeu de test figé (empreintes vérifiées contre `test_set.lock`)
**Et** la Fiche du Modèle indique le nombre de Corrections utilisées par Type de déchet et la date de l'export.

**Étant donné** la date de la dernière release `model-v*` de `kind: trained`
**Quand** une publication est tentée moins de 30 jours après
**Alors** `publish.py` refuse (réentraînement au plus mensuel)
**Et** le déclenchement reste manuel : aucune tâche planifiée ni seuil de Corrections ne lance l'entraînement.

**Étant donné** un Modèle réentraîné
**Quand** il est évalué sur le même Jeu de test figé
**Alors** la publication suit la porte de la story 3.7 (F1 macro ≥ 0,80, rappel ≥ 0,70 par classe, ECE ≤ 0,10, Fiche du Modèle)
**Et** la Fiche compare ses métriques à celles de la version publiée précédente.

**Exigences :** FR-16, FR-13 ; SM-2, SM-8 ; AR-41 ; NFR-P3 (pas de réentraînement automatique).
**Porte :** pilote

## Epic 5 : Missions et preuve de collecte

Le Collecteur vérifié voit les Signalements `validé` proches sans jamais connaître leur auteur, accepte une Mission sans conflit, prouve la collecte (photo avant, photo après, Poids déclaré, Position à moins de 150 m) et garde l'historique de son travail ; l'Administrateur commune peut annuler ou assigner une Mission ; avant le pilote, les Missions oubliées expirent et les Preuves de collecte sont contrôlées par échantillon.

**Prérequis :** Epic 1 ; stories 2.1 à 2.6 et 4.1 à 4.5 pour les stories H48 (Signalements `validé` avec Type de déchet retenu, Collecteurs vérifiés, porte des Statuts `reports.service.transition()` et émission de `ReportStatusChanged`, Journal d'audit, URL signées, détail d'un Signalement pour le Personnel) ; stories 2.8 à 2.11 en plus pour les stories H60 (5.10, 5.11). La Classification serveur de l'Epic 3 est lue si elle existe (Score de confiance de la story 5.1).
**Écrans :** Figma 5 · Missions (nœud 2:2) et 6 · Preuve de collecte (nœud 2:35) ; historique du Collecteur, revue de Preuve, assignation et annulation par l'Administrateur commune : [HORS MAQUETTE — à concevoir], mêmes jetons et police Inter.
**FR couvertes :** FR-24, FR-25, FR-26, FR-27, FR-28, FR-29, FR-30, FR-41, FR-42 ; FR-5 en partie (Mission d'un Collecteur supprimé, story 5.11)
**Porte :** H48 → H60 ; FR-27 et FR-28 : Should, opt. H48 ; FR-41 et FR-42 : pilote.

### Story 5.1 : Lister les Signalements `validé` proches d'un Collecteur vérifié

En tant que Collecteur vérifié,
Je veux obtenir la liste des Signalements `validé` dans un rayon autour de moi, triés par distance,
Afin de choisir où collecter sans connaître l'auteur ni la Position exacte avant d'accepter.

**Critères d'acceptation :**

**Étant donné** une base sans table `weight_estimates`
**Quand** la migration de cette story s'applique
**Alors** elle crée seulement `weight_estimates` (propriétaire `reports` ; `heap_size` ∈ {small, medium, large}, `waste_type` ∈ `WasteType`, `kg NUMERIC(6,1) > 0`, unicité `(heap_size, waste_type)`), chargée depuis un fichier versionné de valeurs provisoires `[ASSUMPTION, PRD §11 Q6]`
**Et** `reports.service.estimated_weight(report)` renvoie le kg de `(heap_size, retained_type)` ; la table couvre les 15 couples (test).

**Étant donné** un Collecteur vérifié connecté et, dans la Zone active, des Signalements aux Statuts `en attente de modération`, `validé`, `rejeté`, `assigné` et `collecté`
**Quand** il appelle `GET /v1/missions/candidates?lat=&lng=` sans `radius_km`
**Alors** la réponse ne contient que des Signalements `validé` situés à 5 km au plus (`ST_DWithin` sur `geography`), triés par distance croissante, paginés (`limit` ≤ 100, `{items, next_cursor}`)
**Et** chaque élément porte l'identifiant du Signalement, le Type de déchet retenu, la distance arrondie à 100 m près (calculée par le serveur sur la Position exacte), le Poids estimé, la Taille de tas, `is_demo` et une URL signée de 5 min vers la miniature

**Étant donné** un Collecteur vérifié
**Quand** il envoie successivement `radius_km=1`, `radius_km=10`, `radius_km=0.9` et `radius_km=10.1`
**Alors** les deux premières requêtes réussissent (200)
**Et** les deux dernières sont refusées (422) avec l'enveloppe d'erreur unique `{"error": {"code", "message", "request_id"}}`

**Étant donné** des Signalements `validé` de Types de déchet retenus différents
**Quand** le Collecteur ajoute le filtre `type=plastic`
**Alors** seuls les Signalements dont le Type de déchet retenu est plastique sont renvoyés, toujours triés par distance

**Étant donné** un Signalement dont le Type de déchet retenu est égal à la Classification serveur, et un autre dont le Type de déchet retenu en diffère
**Quand** la liste est renvoyée
**Alors** le premier porte le Score de confiance de la Classification serveur
**Et** le second porte `human_confirmed = true` sans Score de confiance (affiché « Type confirmé par un humain »)

**Étant donné** n'importe quelle réponse de `GET /v1/missions/candidates` ou de `GET /v1/missions/candidates/<report_id>`
**Quand** elle est sérialisée
**Alors** chaque Position passe par `core.geo.expose(position, "approx")` et ne compte jamais plus de 3 décimales
**Et** aucun champ ne contient l'auteur, `author_user_id`, `owner_key`, l'Identifiant d'appareil ni la précision d'origine
**Et** le test « jamais plus de 3 décimales » d'AD-10 parcourt toutes les valeurs de coordonnées et de distance de ces deux routes

**Étant donné** un Collecteur vérifié qui ouvre un Signalement de la liste
**Quand** il appelle `GET /v1/missions/candidates/<report_id>`
**Alors** il reçoit les mêmes champs plus une URL signée de 5 min vers la photo complète
**Et** un Signalement qui n'est pas `validé` ou qui n'existe pas renvoie 404

**Étant donné** une photo de Signalement reçue
**Quand** la liste est renvoyée
**Alors** l'URL signée de chaque élément pointe vers la miniature de la tâche arq `thumb:<photo_id>` (story 1.11, 30 Ko au plus)
**Et** la liste ne renvoie jamais l'URL de la photo complète

**Étant donné** la Position de recherche envoyée par le Collecteur
**Quand** la requête est traitée
**Alors** cette Position n'est écrite ni en base, ni dans les journaux `structlog`, ni dans les journaux d'accès de Caddy (test : aucune valeur `lat`/`lng` de la requête dans les journaux capturés)

**Étant donné** un Collecteur non vérifié, un Citoyen, un Recycleur, un Modérateur, un Administrateur commune, et une requête sans jeton
**Quand** ils appellent ces deux routes
**Alors** les rôles connectés reçoivent 403 et la requête sans jeton 401
**Et** les deux routes figurent dans le test « route × rôle » généré depuis la table des routes

**Exigences :** FR-24, FR-3, NFR-9, AD-1 (`missions` → `reports.service`), AD-2, AD-6, AD-8, AD-10, AD-11, AD-13, AR-10, AR-19, AR-20
**Porte :** H48

### Story 5.2 : Écran 5 · Missions : carte et liste des Signalements proches

En tant que Collecteur vérifié,
Je veux voir sur une carte et dans une liste les Signalements `validé` autour de moi, avec leur Type de déchet, leur distance et leur Poids estimé,
Afin de repérer depuis mon téléphone la matière la plus proche et la plus utile.

**Critères d'acceptation :**

**Étant donné** un Collecteur vérifié connecté sur un écran de 390×844 qui autorise la géolocalisation
**Quand** il ouvre l'écran 5 · Missions
**Alors** la carte (react-leaflet, tuiles de `TILES_HOST`) et la liste affichent les Signalements renvoyés par `GET /v1/missions/candidates`, triés par distance, avec un rayon de 5 km présélectionné
**Et** chaque élément affiche le badge du Type de déchet retenu (pictogramme + libellé + couleur, composant `WasteTypeBadge` de la story 1.13), la distance (« 800 m », « 1,2 km »), le Poids estimé (« ≈ 15 kg », story 5.1), le Score de confiance (« 87 % ») ou « Type confirmé par un humain », et la miniature chargée paresseusement

**Étant donné** l'emprise de la Zone active définie dans `infra/` (zooms 11 à 17)
**Quand** les tuiles sont préparées
**Alors** elles sont générées depuis un extrait OpenStreetMap, sans téléchargement massif depuis les serveurs publics d'OSM, servies par Caddy sur `TILES_HOST`, et l'attribution « © OpenStreetMap contributors » est affichée sur chaque carte

**Étant donné** l'écran 5 affiché
**Quand** le Collecteur règle le rayon (de 1 à 10 km, par pas de 1 km)
**Alors** la carte et la liste se rechargent avec ce rayon
**Et** aucune valeur hors de 1 à 10 km ne peut être choisie

**Étant donné** l'écran 5 affiché
**Quand** le Collecteur choisit un Type de déchet dans le filtre [HORS MAQUETTE] (5 types + « Tous »)
**Alors** seuls les Signalements de ce Type de déchet retenu restent sur la carte et dans la liste, combinés avec le rayon choisi

**Étant donné** un élément de la liste ou un marqueur de la carte
**Quand** le Collecteur l'ouvre
**Alors** le détail affiche la photo complète, le Type de déchet retenu, le Poids estimé, la Taille de tas et une zone approximative (cercle d'environ 110 m) au lieu d'un point précis
**Et** aucune information sur l'auteur n'apparaît

**Étant donné** l'écran 5 ouvert
**Quand** 15 s s'écoulent
**Alors** la liste est rafraîchie par TanStack Query (test à minuterie simulée), sans WebSocket

**Étant donné** aucun Signalement `validé` dans le rayon
**Quand** la liste est vide
**Alors** l'écran affiche l'état vide « Aucun dépôt validé dans ce rayon » avec l'action « Élargir à 10 km » (UX-DR-21)
**Et** un squelette de chargement s'affiche pendant la requête

**Étant donné** la géolocalisation refusée ou indisponible
**Quand** l'écran 5 s'ouvre
**Alors** un message explique comment activer la localisation et aucune requête n'est envoyée avec une Position par défaut

**Étant donné** un Collecteur dont le compte n'est pas vérifié
**Quand** l'API répond 403
**Alors** l'écran affiche « Votre compte collecteur attend sa vérification par la commune » sans liste

**Étant donné** l'appareil hors réseau
**Quand** l'écran 5 est ouvert
**Alors** la dernière liste chargée reste visible avec l'heure de sa mise à jour et la mention « Hors ligne »
**Et** la Position de recherche n'est stockée ni dans Dexie, ni dans `localStorage`, ni dans `sessionStorage`

**Étant donné** des Signalements `is_demo`
**Quand** ils sont affichés
**Alors** chaque élément porte l'étiquette « Données de démonstration » (UX-DR-6)
**Et** toute cible tactile mesure au moins 44 × 44 px, chaque action a pictogramme + libellé, et aucun texte n'est en dur (clés `fr.json`)

**Exigences :** FR-24, UX-DR-17, UX-DR-3, UX-DR-6, UX-DR-7, UX-DR-8, UX-DR-9, UX-DR-21, NFR-6, NFR-7, NFR-12, NFR-13, NFR-6.4, AR-4, AD-16, AD-23 (`TILES_HOST`)
**Porte :** H48

### Story 5.3 : Accepter une Mission de façon exclusive

En tant que Collecteur vérifié,
Je veux accepter une Mission sur un Signalement `validé` et être le seul à l'obtenir,
Afin de me déplacer sans risquer qu'un autre Collecteur prenne le même dépôt.

**Critères d'acceptation :**

**Étant donné** la base au schéma courant
**Quand** la migration Alembic de cette story s'applique
**Alors** la table `missions` existe (identifiant, `report_id`, `collector_id`, `status` contraint à `active`, `completed`, `cancelled`, `expired`, `accepted_at`, `ended_at`, `is_demo`) avec l'index unique partiel `missions(report_id) WHERE status = 'active'`
**Et** seul le module `missions` y écrit, et `missions.service.transition()` porte une table de transitions constante (`active` → `completed`, `cancelled`, `expired`) testée sur chaque couple : tout autre couple renvoie 409 `invalid_transition` sans rien modifier

**Étant donné** un Collecteur vérifié et un Signalement `validé`
**Quand** il appelle `POST /v1/missions` avec `{report_id}` et un en-tête `Idempotency-Key`
**Alors** il reçoit 201 avec une Mission `active`, `accepted_at` = `core.clock.now()`
**Et** dans la même unité de travail, le Signalement passe à `assigné` par `reports.service.transition(validated → assigned)`, avec une ligne `report_status_events` et une entrée `report.transition` au Journal d'audit (acteur : le Collecteur)
**Et** `ReportStatusChanged` n'est émis qu'après le commit, et `is_demo` vaut `core.demo.flag(report.is_demo)`

**Étant donné** deux Collecteurs vérifiés différents qui acceptent le même Signalement en parallèle (deux transactions simultanées, répété 20 fois)
**Quand** les deux requêtes aboutissent
**Alors** une seule reçoit 201 et l'autre 409 `mission_already_taken`
**Et** il n'existe jamais plus d'une Mission `active` pour ce Signalement, sans aucun verrou applicatif

**Étant donné** un Collecteur qui a déjà accepté la Mission
**Quand** il renvoie la même requête avec la même `Idempotency-Key`
**Alors** la réponse d'origine est rejouée
**Et** s'il la renvoie avec une autre `Idempotency-Key`, il reçoit 200 avec sa Mission `active` existante, sans seconde Mission ni second événement

**Étant donné** une requête sans `Idempotency-Key`, ou avec une clé déjà utilisée pour un autre contenu
**Quand** elle est reçue
**Alors** elle est refusée respectivement en 400 `idempotency_key_required` et 422 `idempotency_key_reused`

**Étant donné** un Collecteur non vérifié
**Quand** il tente d'accepter une Mission
**Alors** il reçoit 403
**Et** une acceptation sur un Signalement `en attente de modération`, `rejeté` ou `collecté` renvoie 409 et ne modifie rien ; un Signalement inexistant renvoie 404

**Étant donné** une exception injectée après `reports.service.transition()` dans `missions.service.accept()`
**Quand** la requête échoue
**Alors** il n'existe ni ligne `missions`, ni ligne `report_status_events`, ni entrée d'audit, ni tâche arq, et le Signalement reste `validé` (AD-17)

**Étant donné** le Collecteur d'une Mission `active`
**Quand** il appelle `GET /v1/missions/<id>` ou `GET /v1/missions/mine?status=active`
**Alors** il reçoit la Position précise du Signalement (`expose(..., "precise")`), la photo complète (URL signée de 5 min), le Type de déchet retenu, le Poids estimé et la Taille de tas
**Et** un autre Collecteur reçoit 404 sur `GET /v1/missions/<id>`, et une Mission qui n'est plus `active` ne renvoie plus que la Position à 3 décimales

**Étant donné** la commande `python -m app.cli demo load`
**Quand** elle s'exécute après les chargements des modules précédents
**Alors** le service `missions` ajoute ses Données de démonstration par ses propres règles (`accept()`) : au moins 2 Missions `active`, toutes `is_demo = true`
**Et** `demo purge` les retire, et un second `demo load` ne les duplique pas

**Exigences :** FR-25, FR-24 (Position précise après acceptation), FR-36, FR-37, AD-3, AD-4, AD-5, AD-9, AD-10, AD-14, AD-17, AR-13, AR-14, AR-15, AR-32, NFR-9
**Porte :** H48

### Story 5.4 : Accepter une Mission depuis l'écran 5 et voir la Position précise

En tant que Collecteur vérifié,
Je veux accepter une Mission en un toucher et voir aussitôt où se trouve exactement le dépôt,
Afin de partir collecter sans perdre de temps.

**Critères d'acceptation :**

**Étant donné** le détail d'un Signalement ouvert depuis l'écran 5
**Quand** le Collecteur touche « Accepter la mission » (pictogramme + libellé, cible ≥ 44 px)
**Alors** l'application envoie `POST /v1/missions` avec une `Idempotency-Key` générée pour ce geste, et le bouton reste désactivé pendant la requête (deux touchers rapides → une seule requête)
**Et** en cas d'erreur réseau, le nouvel essai réutilise la même `Idempotency-Key`

**Étant donné** une acceptation réussie (201 ou 200)
**Quand** la réponse arrive
**Alors** la vue « Mission en cours » affiche le marqueur précis du Signalement, la photo complète, le Type de déchet retenu et le Poids estimé
**Et** la Mission apparaît dans la section « Mes Missions en cours » de l'écran 5

**Étant donné** un autre Collecteur qui a pris la Mission une seconde avant
**Quand** l'API répond 409 `mission_already_taken`
**Alors** l'écran affiche « Mission déjà prise » (clé `errors.mission_already_taken`) et rafraîchit immédiatement la liste, d'où l'élément disparaît

**Étant donné** un Signalement qui n'est plus `validé`
**Quand** l'API répond 409 `invalid_transition`
**Alors** l'écran affiche « Ce dépôt n'est plus disponible » et rafraîchit la liste

**Étant donné** une coupure réseau après l'envoi d'une acceptation que le serveur a enregistrée
**Quand** le Collecteur réessaie
**Alors** la réponse rejouée affiche sa Mission, jamais « Mission déjà prise »

**Étant donné** l'appareil hors réseau
**Quand** le Collecteur touche « Accepter la mission »
**Alors** l'écran affiche « Pas de réseau : la mission n'est pas encore acceptée » et rien n'est mis en File hors-ligne

**Étant donné** la section « Mes Missions en cours »
**Quand** l'écran 5 reste ouvert
**Alors** elle est rafraîchie toutes les 15 s
**Et** tous les textes viennent de `fr.json` et les messages disent quoi faire (UX-DR-10)

**Exigences :** FR-25, FR-24, UX-DR-17, UX-DR-7, UX-DR-8, UX-DR-10, AD-5, AD-11, AD-12 (pas d'outbox pour les Missions)
**Porte :** H48

### Story 5.5 : Annuler une Mission `active`

En tant que Collecteur vérifié ou Administrateur commune,
Je veux annuler une Mission `active`,
Afin que le dépôt redevienne disponible pour un autre Collecteur quand la collecte ne peut pas avoir lieu.

**Critères d'acceptation :**

**Étant donné** le Collecteur d'une Mission `active`
**Quand** il appelle `POST /v1/missions/<id>/cancel` avec une `Idempotency-Key`
**Alors** la Mission passe à `annulée` (`ended_at` = `core.clock.now()`) et le Signalement revient à `validé`, dans la même unité de travail, verrous pris dans l'ordre Mission puis Signalement
**Et** le Journal d'audit reçoit une entrée `mission.transition` et une entrée `report.transition` dont l'acteur est le Collecteur, et `report_status_events` reçoit une ligne

**Étant donné** un Administrateur commune et une Mission `active` de n'importe quel Collecteur
**Quand** il l'annule par la même route
**Alors** le résultat est identique et l'acteur audité est l'Administrateur commune

**Étant donné** une Mission `terminée`, `annulée` ou `expirée`
**Quand** son Collecteur ou un Administrateur commune tente de l'annuler
**Alors** la requête est refusée (409 `invalid_transition`) et rien n'est modifié

**Étant donné** un autre Collecteur, un Citoyen, un Modérateur ou un Recycleur
**Quand** il tente d'annuler la Mission
**Alors** l'autre Collecteur reçoit 404 et les autres rôles 403

**Étant donné** une annulation par le Collecteur et une annulation par l'Administrateur commune envoyées en parallèle (répété 50 fois)
**Quand** elles aboutissent
**Alors** une seule réussit, l'autre reçoit 409, sans interblocage

**Étant donné** une Mission annulée
**Quand** un Collecteur vérifié du rayon recharge l'écran 5
**Alors** le Signalement réapparaît dans `GET /v1/missions/candidates`, avec sa Position à 3 décimales
**Et** l'ancien Collecteur ne reçoit plus que la Position à 3 décimales

**Étant donné** la vue « Mission en cours » sur l'écran 5
**Quand** le Collecteur touche « Annuler la mission » puis confirme dans la boîte de dialogue
**Alors** la Mission quitte « Mes Missions en cours » et l'écran revient à la liste

**Étant donné** `GET /v1/missions/staff?status=&report_id=&cursor=` (créée par cette story ; Modérateur et Administrateur commune, au test route × rôle)
**Quand** elle est appelée
**Alors** elle renvoie les Missions demandées avec `report_id`, le nom affiché du Collecteur (ou son identifiant court s'il n'en a pas), la date d'acceptation et le Statut de Mission, sans numéro de téléphone
**Et** un Collecteur, un Citoyen ou un Recycleur reçoit 403, et une requête sans jeton 401

**Étant donné** un Signalement `assigné` trouvé par l'Administrateur commune dans `GET /v1/staff/reports?status=assigned` (story 4.1) et ouvert dans son détail (`GET /v1/moderation/reports/{id}`), dans l'espace du Personnel (1280×800) [HORS MAQUETTE]
**Quand** un Administrateur commune l'ouvre
**Alors** il voit la Mission `active` lue par `GET /v1/missions/staff?report_id=` (nom affiché du Collecteur, ou son identifiant court s'il n'en a pas ; date d'acceptation) et un bouton « Annuler la Mission » avec confirmation, utilisable au clavier
**Et** un Modérateur ne voit pas ce bouton

**Étant donné** le méta-test du Journal d'audit (story 2.6)
**Quand** la CI s'exécute
**Alors** `mission.transition` a son test et n'est plus dans `PENDING_AUDIT_ACTIONS`

**Exigences :** FR-26, FR-36, UX-DR-28 (annulation par l'Administrateur), UX-DR-17, AD-3, AD-5, AD-9, AD-17, AD-25
**Porte :** H48

### Story 5.6 : Soumettre une Preuve de collecte géorepérée

En tant que Collecteur vérifié,
Je veux soumettre une Preuve de collecte (photo avant, photo après, Poids déclaré, Position) que le serveur vérifie,
Afin que mon travail soit reconnu sur des éléments vérifiables.

**Critères d'acceptation :**

**Étant donné** la base au schéma courant
**Quand** la migration Alembic de cette story s'applique
**Alors** la table `proofs` existe avec `UNIQUE (mission_id)`, les clés et les `before_sha256` / `after_sha256` indexés des deux photos, `weight_kg NUMERIC(8,2) CHECK (weight_kg > 0)`, `weight_kind` (`weighed`, `estimated`), la Position du Collecteur (`GEOGRAPHY(Point, 4326)`) et sa précision, la distance et le rayon accepté calculés, `received_at`, `photos_purged_at` (nul), les valeurs `client_*` et `is_demo`

**Étant donné** le Collecteur d'une Mission `active`
**Quand** il appelle `POST /v1/missions/<id>/proof` en `multipart/form-data` (`meta` : `weight_kg`, `weight_kind`, `position {lat, lng, accuracy_m}`, `client_captured_at` ; `photo_before` ; `photo_after`) avec une `Idempotency-Key`, depuis une Position acceptée
**Alors** il reçoit 201 ; `received_at` = `core.clock.now()` et l'heure du client n'est gardée qu'en `client_captured_at`
**Et** dans la même unité de travail, après le verrou de la Mission puis du Signalement, la Mission passe à `terminée` et le Signalement à `collecté` (deux transitions auditées, une ligne `report_status_events`, `ReportStatusChanged` émis après le commit)

**Étant donné** les réglages `PROOF_RADIUS_M = 150`, `PROOF_REPORT_ACCURACY_CAP_M = 50` et `PROOF_COLLECTOR_ACCURACY_MAX_M = 50`, et des Positions construites à distance connue
**Quand** le serveur calcule la distance par `ST_Distance` sur `geography` et le rayon accepté = 150 m + min(précision du Signalement, 50 m)
**Alors** les cas suivants donnent le résultat attendu :

| Précision du Signalement | Rayon accepté | Distance mesurée | Précision du Collecteur | Résultat |
|---|---|---|---|---|
| 20 m | 170 m | 169 m | 10 m | acceptée (201) |
| 20 m | 170 m | 171 m | 10 m | refusée (422 `proof_too_far`) |
| 80 m | 200 m | 199 m | 10 m | acceptée (201) |
| 80 m | 200 m | 201 m | 10 m | refusée (422 `proof_too_far`) |
| 20 m | 170 m | 20 m | 50 m | acceptée (201) |
| 20 m | 170 m | 20 m | 51 m | refusée (422 `proof_position_imprecise`) |

**Et** un refus `proof_too_far` renvoie `distance_m` (arrondie au mètre) et `accepted_radius_m` ; un refus `proof_position_imprecise` renvoie `accuracy_m` et `max_accuracy_m`
**Et** les messages `errors.proof_too_far` et `errors.proof_position_imprecise` de `fr.json` donnent la distance mesurée et le rayon accepté sans accuser (« Vous êtes à 230 m du dépôt ; rapprochez-vous à moins de 170 m. »)
**Et** un refus ne modifie ni la Mission ni le Signalement, et les photos déjà écrites sont supprimées du stockage (`after_rollback`)

**Étant donné** une Preuve sans photo avant, sans photo après, avec un Poids déclaré ≤ 0 ou sans mention `pesé`/`estimé`
**Quand** elle est envoyée
**Alors** elle est refusée (422)
**Et** chaque photo passe par `core.storage.ingest_photo()` (types `before` et `after`) : 415 hors JPEG, PNG et WebP ; 413 ou 422 au-delà de 1 Mo ou 12 Mpx ; ré-encodage JPEG sans EXIF ; `sha256` des octets reçus enregistré

**Étant donné** une Mission `terminée`, `annulée` ou `expirée`
**Quand** son Collecteur envoie une Preuve
**Alors** il reçoit 409 `invalid_transition`
**Et** une Preuve envoyée par un autre Collecteur que celui de la Mission reçoit 403, et une requête sans `Idempotency-Key` reçoit 400

**Étant donné** une Preuve acceptée dont la réponse a été perdue par une coupure réseau
**Quand** le Collecteur renvoie la même requête avec la même `Idempotency-Key`
**Alors** la réponse d'origine est rejouée et il n'existe qu'une ligne `proofs` et un seul Poids déclaré
**Et** deux envois parallèles avec la même clé produisent une seule Preuve ; un envoi avec une autre clé reçoit 409 et `UNIQUE (proofs.mission_id)` garantit toujours une seule Preuve

**Étant donné** une Preuve acceptée
**Quand** le Collecteur de la Mission ou un membre du Personnel appelle `GET /v1/missions/<id>/proof`
**Alors** il reçoit les URL signées de 5 min des deux photos, le Poids déclaré, la mention, la Position du Collecteur, la distance et le rayon accepté
**Et** un autre Collecteur, l'auteur du Signalement, un Citoyen ou un Recycleur ne reçoivent ni photo ni Position (404 ou 403, test « route × rôle »)

**Étant donné** une valeur de distance ou de statut envoyée par le client dans `meta`
**Quand** la Preuve est traitée
**Alors** elle est ignorée pour la décision ; seule la distance calculée par le serveur est stockée et utilisée
**Et** en Mode démonstration la Preuve porte `is_demo = true`

**Étant donné** la commande `python -m app.cli demo load`
**Quand** elle s'exécute après les chargements des modules précédents
**Alors** le service `missions` ajoute au moins 2 Missions `completed` de démonstration en acceptant une Mission puis en soumettant sa Preuve par `submit_proof()`, avec les mêmes règles qu'une Preuve réelle, toutes `is_demo = true`
**Et** `demo purge` les retire avec leurs photos, et un second `demo load` ne les duplique pas

**Étant donné** `retention.sweep` (story 1.16) et une horloge simulée
**Quand** la tâche s'exécute
**Alors** les photos avant et après des Preuves reçues depuis plus de `PROOF_PHOTO_RETENTION_DAYS` (365) sont purgées par `core.storage.purge()`, l'ancienne URL signée ne fonctionne plus, et la purge est inscrite par lot (`retention.purge`)
**Et** la ligne `proofs` (Poids déclaré, distance) est conservée et marquée par `photos_purged_at` (colonne créée avec la table par cette story), si bien qu'un second passage ne purge ni n'inscrit rien

**Exigences :** FR-29, FR-36, FR-37, NFR-6.1b, NFR-6.1c, NFR-6.2, AD-3, AD-5, AD-6, AD-10, AD-11, AD-13, AD-14, AD-17, AD-18, AR-16, AR-23, AR-28, AR-32, UX-DR-10
**Porte :** H48

### Story 5.7 : Écran 6 · Preuve de collecte

En tant que Collecteur vérifié,
Je veux saisir ma Preuve de collecte sur place en quelques gestes, même si le réseau coupe,
Afin de prouver mon travail sans ressaisir ni être accusé à tort.

**Critères d'acceptation :**

**Étant donné** la vue « Mission en cours » d'une Mission `active`
**Quand** le Collecteur touche « Prouver la collecte »
**Alors** l'écran 6 (390×844) propose la photo avant, la photo après, le Poids déclaré (clavier numérique, virgule décimale, > 0) et le choix `pesé` / `estimé` (pictogramme + libellé, aucun choix présélectionné)
**Et** la consigne « ni personne ni plaque » est visible à chaque capture, et le bouton « Envoyer la preuve » reste désactivé tant qu'un champ manque

**Étant donné** une photo prise par l'appareil
**Quand** elle est préparée pour l'envoi
**Alors** elle est compressée à 300 Ko au plus (HEIC converti en JPEG) avec le module de capture existant (test automatique)

**Étant donné** le formulaire complet
**Quand** le Collecteur touche « Envoyer la preuve »
**Alors** la Position est capturée à cet instant et sa précision est affichée en mètres
**Et** si la précision dépasse 50 m, l'écran affiche « Position imprécise (± 64 m) : patientez quelques secondes puis réessayez » et n'envoie rien

**Étant donné** une Preuve acceptée (201)
**Quand** la réponse arrive
**Alors** l'écran affiche « Merci ! Vous êtes à moins de 150 m du dépôt : la collecte est prouvée. » et la Mission apparaît `terminée`

**Étant donné** une réponse 422 `proof_too_far`
**Quand** elle arrive
**Alors** l'écran affiche le message avec la distance et le rayon renvoyés par le serveur (« Vous êtes à 230 m du dépôt ; rapprochez-vous à moins de 170 m. »), sans mot accusateur
**Et** les photos et le Poids déclaré restent saisis pour un nouvel essai

**Étant donné** l'appareil hors réseau ou une erreur réseau à l'envoi
**Quand** le Collecteur touche « Envoyer la preuve »
**Alors** l'écran affiche « Pas de réseau : votre preuve n'est pas encore envoyée. Gardez l'application ouverte et réessayez. »
**Et** la saisie reste en mémoire tant que l'application est ouverte, rien n'est écrit dans Dexie ni dans la File hors-ligne (test), et la Position est recapturée au prochain envoi

**Étant donné** un premier envoi pour cet écran
**Quand** l'application génère l'`Idempotency-Key`
**Alors** chaque nouvel essai réutilise cette clé jusqu'à un succès ou un refus définitif
**Et** après une coupure survenue alors que le serveur avait accepté la Preuve, le nouvel essai affiche le succès sans créer de seconde Preuve

**Étant donné** une réponse 409 (Mission annulée ou expirée entre-temps)
**Quand** elle arrive
**Alors** l'écran affiche « Cette mission n'est plus active » et revient à l'écran 5

**Étant donné** l'écran 6
**Quand** il est audité
**Alors** chaque cible tactile mesure au moins 44 × 44 px, chaque photo a un texte alternatif, aucun texte n'est en dur et le bandeau « Mode démonstration » reste visible s'il est actif

**Exigences :** FR-29, UX-DR-18, UX-DR-7, UX-DR-8, UX-DR-9, UX-DR-10, NFR-4, NFR-12, NFR-P3 (pas de Preuve hors-ligne), AD-5
**Porte :** H48

### Story 5.8 : Ouvrir l'itinéraire vers une Mission `active`

En tant que Collecteur vérifié,
Je veux ouvrir l'application de cartes de mon téléphone sur la Position du dépôt de ma Mission,
Afin de m'y rendre sans recopier d'adresse.

**Critères d'acceptation :**

**Étant donné** le Collecteur d'une Mission `active` sur la vue « Mission en cours »
**Quand** il touche « Itinéraire » (pictogramme + libellé, cible ≥ 44 px)
**Alors** l'application ouvre un lien `geo:<lat>,<lng>?q=<lat>,<lng>` avec la Position précise renvoyée par `GET /v1/missions/<id>`, ce qui ouvre l'application de cartes du téléphone centrée sur le dépôt
**Et** si aucun gestionnaire `geo:` n'est disponible, l'écran affiche les coordonnées avec un bouton « Copier »

**Étant donné** un Signalement non encore accepté, une Mission `terminée`, `annulée` ou `expirée`, ou un écran du Personnel
**Quand** l'écran s'affiche
**Alors** le bouton « Itinéraire » n'existe pas (test de composant pour chaque cas)

**Étant donné** le composant d'itinéraire
**Quand** il construit le lien
**Alors** il n'utilise que la Position d'une réponse de Mission `active` et n'appelle aucun service tiers depuis l'application

**Exigences :** FR-27, UX-DR-17, AD-10
**Porte :** Should, opt. H48

### Story 5.9 : Assigner un Signalement `validé` à un Collecteur vérifié

En tant qu'Administrateur commune,
Je veux assigner un Signalement `validé` à un Collecteur vérifié de mon choix,
Afin de faire traiter un dépôt prioritaire sans attendre qu'un Collecteur l'accepte.

**Critères d'acceptation :**

**Étant donné** un Administrateur commune, un Signalement `validé` et un Collecteur vérifié actif
**Quand** il appelle `POST /v1/missions/assignments` avec `{report_id, collector_id}` et une `Idempotency-Key`
**Alors** il reçoit 201 avec une Mission `active` au nom de ce Collecteur, et le Signalement passe à `assigné` dans la même unité de travail, sous le même index unique partiel qu'à l'acceptation
**Et** le Journal d'audit reçoit `mission.assign` (acteur : l'Administrateur commune ; après : `report_id`, `collector_id`) et `report.transition`, et `MissionAssigned` est émis après le commit, sans réaction abonnée au MVP

**Étant donné** un Signalement qui a déjà une Mission `active`
**Quand** l'Administrateur commune l'assigne
**Alors** il reçoit 409 `mission_already_taken`
**Et** un Signalement qui n'est pas `validé` renvoie 409 `invalid_transition`

**Étant donné** un `collector_id` qui désigne un compte non vérifié, suspendu ou qui n'a pas le rôle Collecteur
**Quand** l'assignation est demandée
**Alors** elle est refusée (422, code dédié présent dans `core/errors/codes.py` et `fr.json`) et rien n'est créé

**Étant donné** un Modérateur, un Collecteur, un Citoyen ou un Recycleur
**Quand** il appelle cette route
**Alors** il reçoit 403 (test « route × rôle »)

**Étant donné** le Collecteur assigné avec l'application ouverte sur l'écran 5
**Quand** l'assignation est validée
**Alors** la Mission apparaît dans « Mes Missions en cours » avec la mention « Assignée par la commune » au plus 15 s après (rafraîchissement de 15 s, test à minuterie simulée)
**Et** la notification du Collecteur au MVP est cette apparition dans la liste en 15 s au plus ; aucune réaction n'est abonnée à `MissionAssigned`

**Étant donné** un Signalement `validé` trouvé par l'Administrateur commune dans `GET /v1/staff/reports?status=validated` (story 4.1) et ouvert dans son détail, dans l'espace du Personnel (1280×800) [HORS MAQUETTE]
**Quand** l'Administrateur commune choisit « Assigner à un collecteur »
**Alors** il choisit un Collecteur dans la liste des Collecteurs vérifiés actifs (nom affiché, recherche par nom), confirme, et voit la Mission créée
**Et** la liste vient de `GET /v1/missions/assignable-collectors` (créée par cette story, Administrateur commune seulement, par `auth.service` : Collecteurs vérifiés actifs, nom affiché, sans numéro), couverte par le test route × rôle
**Et** tout le parcours est utilisable au clavier avec un focus visible, et un Modérateur ne voit pas l'action

**Étant donné** le méta-test du Journal d'audit (story 2.6)
**Quand** la CI s'exécute
**Alors** `mission.assign` a son test et n'est plus dans `PENDING_AUDIT_ACTIONS`

**Exigences :** FR-28, FR-36, UX-DR-28 (assignation manuelle), UX-DR-17, AD-4, AD-5, AD-9, AD-21, AD-25
**Porte :** Should, opt. H48

### Story 5.10 : Historique des Missions du Collecteur

En tant que Collecteur vérifié,
Je veux retrouver toutes mes Missions et le total des kilos que j'ai collectés,
Afin de disposer d'un historique crédible de mon travail.

**Critères d'acceptation :**

**Étant donné** un Collecteur avec des Missions de tous Statuts de Mission
**Quand** il appelle `GET /v1/missions/mine` (paginé, plus récentes d'abord, filtre `status` facultatif)
**Alors** chaque élément porte la date d'acceptation, la date de fin, le Type de déchet retenu, le Statut de Mission et, pour une Mission `terminée`, le Poids déclaré et sa mention `pesé`/`estimé`
**Et** la réponse porte `total_kg`, somme des Poids déclarés de ses Missions `terminée`

**Étant donné** un jeu d'essai de 3 Missions `terminée` (10 kg, 15,5 kg et 17 kg), 1 `annulée` et 1 `active`
**Quand** le Collecteur lit son historique
**Alors** il voit 5 Missions et un total de 42,5 kg

**Étant donné** deux Collecteurs
**Quand** chacun appelle la route
**Alors** aucun ne reçoit une Mission de l'autre
**Et** les autres rôles reçoivent 403, et aucune Position n'est renvoyée pour une Mission qui n'est pas `active`

**Étant donné** l'écran « Mes missions » [HORS MAQUETTE] ouvert depuis l'écran 5 (390×844)
**Quand** il s'affiche
**Alors** il montre les sections « En cours » et « Terminées » (les Missions `annulée` et `expirée` y figurent avec leur libellé), chaque ligne avec date, badge du Type de déchet retenu, Poids déclaré et Statut de Mission, et le total « 42,5 kg collectés » au format local
**Et** une Mission `active` ouvre la vue « Mission en cours », d'où le Collecteur peut l'annuler

**Étant donné** un Collecteur sans Mission
**Quand** l'écran s'affiche
**Alors** un état vide invite à consulter l'écran 5
**Et** les cibles tactiles mesurent au moins 44 px et aucun texte n'est en dur

**Exigences :** FR-30 (sans la mention `contestée`, livrée par la Story 5.15), UX-DR-30, UX-DR-8, AD-10
**Porte :** H60

### Story 5.11 : Libérer la Mission `active` d'un Collecteur supprimé ou suspendu

En tant qu'Administrateur commune,
Je veux que la Mission `active` d'un Collecteur qui supprime son compte ou qui est suspendu soit annulée d'elle-même,
Afin que le dépôt redevienne disponible pour les autres Collecteurs sans intervention.

**Critères d'acceptation :**

**Étant donné** `missions.service.on_collector_deleted(user_id)` (créé par cette story)
**Quand** il est appelé pour un Collecteur qui a une Mission `active`
**Alors** il annule sa Mission par `missions.service.transition(active → cancelled)` (`mission.transition`, acteur `system:account_deleted`), et le Signalement revient à `validé` (`report.transition`, ligne `report_status_events`), verrous dans l'ordre Mission puis Signalement
**Et** un Collecteur sans Mission `active` ne produit aucune écriture.

**Étant donné** un Collecteur qui a une Mission `active` et supprime son compte (story 2.10)
**Quand** la réaction `AccountDeleted` s'exécute
**Alors** `missions.service.on_collector_deleted(user_id)` annule sa Mission, le Signalement revient à `validé`, puis `reports.service.detach_owner` s'exécute, dans cet ordre dans `reactions.py` (AD-21)
**Et** rejouer la réaction ne change rien.

**Étant donné** un Collecteur qui a une Mission `active` et est suspendu par l'Administrateur commune (story 2.11)
**Quand** la réaction `CollectorSuspended` s'exécute
**Alors** `missions.service.on_collector_deleted(user_id)` annule sa Mission de la même façon (acteur `system:collector_suspended`)
**Et** rejouer la réaction ne change rien.

**Étant donné** une Mission ainsi annulée
**Quand** un Collecteur vérifié du rayon appelle `GET /v1/missions/candidates`
**Alors** le Signalement y figure de nouveau, avec sa Position à 3 décimales.

**Étant donné** l'analyse import-linter
**Quand** la CI s'exécute
**Alors** `auth` n'importe pas `missions`, et seul `reactions.py` relie `AccountDeleted` et `CollectorSuspended` à `missions.service`.

**Exigences :** FR-5, FR-26, FR-35, FR-36, AR-13, AR-24, AD-1, AD-3, AD-17, AD-21, AD-25
**Porte :** H60

### Story 5.12 : Expirer les Missions sans Preuve après 48 h

En tant qu'Administrateur commune,
Je veux qu'une Mission restée sans Preuve de collecte expire seule,
Afin qu'un dépôt ne reste pas bloqué par un Collecteur qui ne viendra pas.

**Critères d'acceptation :**

**Étant donné** le réglage `MISSION_EXPIRY_H` (48 par défaut, configurable)
**Quand** la tâche planifiée `missions.expire_due` (`cron_jobs` arq de `worker.py`, toutes les minutes) s'exécute
**Alors** chaque Mission `active` dont `accepted_at` + 48 h ≤ `core.clock.now()` passe à `expirée` par `missions.service.transition()`, et son Signalement revient à `validé` par `reports.service.transition()`, dans une unité de travail par Mission, verrous dans l'ordre Mission puis Signalement
**Et** le Journal d'audit reçoit `mission.transition` et `report.transition` avec l'acteur `system:missions.expire_due`, et `report_status_events` une ligne de motif `mission_expired`

**Étant donné** une Mission acceptée à l'instant T et une horloge simulée
**Quand** la tâche s'exécute à T + 47 h 59 min puis à T + 48 h 01 min
**Alors** la Mission est encore `active` au premier passage
**Et** elle est `expirée` et le Signalement `validé` au second passage

**Étant donné** une Mission expirée
**Quand** un Collecteur vérifié dans le rayon appelle `GET /v1/missions/candidates`
**Alors** le Signalement y figure de nouveau

**Étant donné** deux exécutions concurrentes de la tâche
**Quand** elles traitent la même Mission échue
**Alors** une seule transition et une seule paire d'entrées d'audit sont produites

**Étant donné** une Preuve de collecte acceptée juste avant le passage de la tâche
**Quand** la tâche s'exécute
**Alors** la Mission `terminée` n'est pas touchée (condition `status = 'active'`)
**Et** une Preuve envoyée après l'expiration reçoit 409

**Étant donné** l'historique du Collecteur
**Quand** une de ses Missions a expiré
**Alors** elle y figure avec le Statut de Mission `expirée`

**Exigences :** FR-42, FR-36, AD-3, AD-17, AD-18, AD-25, AR-23
**Porte :** pilote

### Story 5.13 : Tirer chaque semaine l'échantillon de Preuves à revoir

En tant que membre du Personnel,
Je veux qu'un échantillon aléatoire de Preuves de collecte, plus toute Preuve à photo réutilisée, me soit proposé chaque semaine,
Afin de détecter les fausses preuves sans tout revoir.

**Critères d'acceptation :**

**Étant donné** la base au schéma courant
**Quand** la migration Alembic de cette story s'applique
**Alors** `proofs` reçoit `sampled_at` (nul par défaut) et `sample_reason` (`random` ou `identical_photo`), indexés

**Étant donné** une semaine ISO terminée (du lundi 00:00 UTC au lundi suivant 00:00 UTC) contenant N Preuves acceptées non encore tirées
**Quand** la tâche planifiée `missions.sample_proofs` s'exécute le lundi
**Alors** elle tire au hasard par `secrets.SystemRandom` n = max(1, ⌈0,05 × N⌉) Preuves si N ≥ 1, et aucune si N = 0
**Et** les cas N = 0, 1, 20, 21, 40 et 100 donnent n = 0, 1, 1, 2, 2 et 5

**Étant donné** une Preuve de la semaine dont `before_sha256` ou `after_sha256` est identique à l'empreinte d'une photo reçue plus tôt (Signalement via `reports.service.photo_seen()`, ou autre Preuve via `missions.service.photo_seen()`, créé par cette story)
**Quand** la tâche s'exécute
**Alors** cette Preuve est ajoutée d'office avec `sample_reason = identical_photo`, en plus des n Preuves tirées parmi les autres

**Étant donné** une semaine déjà tirée
**Quand** la tâche s'exécute de nouveau (même lundi ou lundi suivant)
**Alors** aucune Preuve de cette semaine n'est tirée une seconde fois
**Et** une semaine non tirée parce que le worker était arrêté est rattrapée au passage suivant (test à horloge simulée)

**Étant donné** le tirage
**Quand** il s'exécute
**Alors** il passe par une source aléatoire injectable (`secrets.SystemRandom` en exécution, générateur fixé en test) et la Revue de Preuve de chaque Preuve tirée vaut `non revue`
**Et** le tirage n'écrit que dans `proofs` (module `missions`) et ne modifie ni la Mission ni le Signalement

**Exigences :** FR-41 (tirage), NFR-6.2, AD-13 (`photo_seen`), AD-18, AR-23
**Porte :** pilote

### Story 5.14 : Revoir une Preuve tirée : `confirmée` ou `contestée`

En tant que membre du Personnel,
Je veux marquer chaque Preuve tirée `confirmée` ou `contestée` avec un motif,
Afin d'écarter des Kg collectés les poids douteux tout en gardant une trace de chaque décision.

**Critères d'acceptation :**

**Étant donné** la base au schéma courant
**Quand** la migration Alembic de cette story s'applique
**Alors** la table `proof_reviews` existe (une ligne par revue : `proof_id`, `status` `confirmed` ou `contested`, `reason`, `reviewer_user_id`, `reviewed_at`, `is_demo`) avec `CHECK (status <> 'contested' OR reason IS NOT NULL)`
**Et** la Revue de Preuve courante est la dernière ligne, `non revue` s'il n'y en a aucune ; la migration ne modifie aucune colonne lue par une vue analytique (la lecture de `proof_reviews` par `v_mission_facts` est ajoutée par la story 7.7)

**Étant donné** un Modérateur ou un Administrateur commune
**Quand** il appelle `GET /v1/proofs/samples?review_status=unreviewed`
**Alors** il reçoit les Preuves tirées, plus anciennes d'abord, paginées, avec les URL signées de 5 min des photos avant et après, le Poids déclaré et sa mention, la Position du Collecteur, la Position précise du Signalement, la distance mesurée, le Type de déchet retenu, `sample_reason` et, pour une photo identique, la référence de la photo d'origine

**Étant donné** une Preuve tirée
**Quand** un membre du Personnel appelle `POST /v1/proofs/<id>/reviews` avec `{status: "contested"}` sans motif
**Alors** il reçoit 422
**Et** avec un motif, il reçoit 201, le Journal d'audit reçoit `proof.review` (avant/après : Revue de Preuve), et le Signalement reste `collecté` sans nouvelle ligne `report_status_events`

**Étant donné** une Preuve non tirée
**Quand** une revue est demandée
**Alors** elle est refusée (409) ; une requête sans `Idempotency-Key` reçoit 400

**Étant donné** une Preuve déjà revue
**Quand** une nouvelle revue est enregistrée
**Alors** une nouvelle ligne est ajoutée et devient la Revue de Preuve courante, et chaque revue est auditée

**Étant donné** un Collecteur, un Citoyen ou un Recycleur
**Quand** il appelle ces routes
**Alors** il reçoit 403 (test « route × rôle »)

**Étant donné** un Collecteur avec 3 Missions `terminée` de 10 kg, 15,5 kg et 17 kg, dont la Preuve de 15,5 kg est `contestée`
**Quand** il appelle `GET /v1/missions/mine`
**Alors** chaque élément porte sa Revue de Preuve et la Mission contestée est marquée `contested`
**Et** `total_kg` vaut 27 kg (Preuves `contestée` exclues)

**Étant donné** 20 Preuves revues sur une période, dont 3 `contestée`
**Quand** un Administrateur commune appelle `GET /v1/proofs/samples/stats?from=&to=`
**Alors** il reçoit `reviewed = 20`, `contested = 3` et `contested_share = 0.15` (part de Preuves `contestée` parmi les revues, SM-C3), avec `contains_demo_data`

**Étant donné** le méta-test du Journal d'audit (story 2.6)
**Quand** la CI s'exécute
**Alors** `proof.review` a son test et n'est plus dans `PENDING_AUDIT_ACTIONS`

**Exigences :** FR-41 (revue, exclusion, part contestée), FR-30 (mention `contestée`, API), FR-36, AD-2, AD-5, AD-10, AD-25
**Porte :** pilote

### Story 5.15 : Écran de revue des Preuves et mention `contestée` dans l'historique

En tant que membre du Personnel,
Je veux revoir les Preuves tirées sur un écran clair, utilisable au clavier, et que le Collecteur voie le résultat dans son historique,
Afin de décider vite et sans erreur, et que chaque Collecteur sache quelles Preuves ont été contestées.

**Critères d'acceptation :**

**Étant donné** un membre du Personnel connecté sur un écran de 1280×800
**Quand** il ouvre « Revue des preuves » [HORS MAQUETTE]
**Alors** il voit la liste des Preuves tirées `non revue` (filtre par Revue de Preuve) et, pour la Preuve ouverte, les photos avant et après côte à côte (avec texte alternatif), le Poids déclaré et sa mention, la distance mesurée et le rayon accepté, une carte avec la Position du Signalement et celle du Collecteur, et le motif « photo identique » avec un lien vers la photo d'origine

**Étant donné** une Preuve ouverte
**Quand** il choisit « Confirmer »
**Alors** la revue est enregistrée, la Preuve quitte la liste « à revoir » et la suivante s'ouvre

**Étant donné** une Preuve ouverte
**Quand** il choisit « Contester »
**Alors** un champ de motif obligatoire apparaît, et la validation reste désactivée tant qu'il est vide

**Étant donné** l'écran de revue
**Quand** il est parcouru uniquement au clavier
**Alors** chaque action est atteignable, le focus est visible et l'audit Lighthouse d'accessibilité ne signale aucune erreur de contraste ni de libellé

**Étant donné** un Collecteur dont une Preuve est `contestée`
**Quand** il ouvre « Mes missions »
**Alors** la Mission porte la mention « Preuve contestée » (pictogramme + libellé, texte Ambre `#7A5C00` sur `#FFF4CC`)
**Et** le total affiché exclut cette Mission et l'indique (« hors preuves contestées »)

**Exigences :** FR-41, FR-30, UX-DR-31, UX-DR-30, UX-DR-2, UX-DR-7, UX-DR-8, NFR-12
**Porte :** pilote

## Epic 6 : Signaler sans réseau

Un Signalement fait en mode avion est conservé dans la File hors-ligne puis envoyé tout seul au retour du réseau, sans doublon ni perte. Cet epic suppose Epic 1 terminé ; il utilise la session d'Epic 2 (`refreshSession()`) si les comptes sont livrés, et sinon l'envoi par Identifiant d'appareil (`X-Device-Id`) seul.

### Story 6.1 : Garder un Signalement sur le téléphone quand le réseau manque

En tant que Citoyen,
Je veux que mon Signalement soit enregistré sur mon téléphone quand je n'ai pas de réseau, et qu'un accusé s'affiche tout de suite,
Afin de ne rien perdre et de ne pas attendre le réseau devant le dépôt.

**Critères d'acceptation :**

**Étant donné** la base Dexie de la PWA (table `meta` d'Epic 1)
**Quand** la nouvelle version du schéma Dexie s'applique
**Alors** elle ajoute une seule table `outbox` (la File hors-ligne), de clé l'Identifiant client, qui stocke 100 % des champs : photo (Blob JPEG), Position et précision, horodatage de prise de vue, Taille de tas, Type de déchet choisi, Classification locale (type, score, version du Modèle) quand l'écran 3 en a produit une, commentaire, `consent` (`terms`, `training`), identité, état (`pending`, `sending`, `waiting_login`, `failed`), nombre d'essais, date du prochain essai, dernier code d'erreur et date de mise en file
**Et** la table `meta` et l'Identifiant d'appareil sont conservés lors de la mise à jour du schéma.

**Étant donné** un brouillon complet à l'écran 3
**Quand** le Citoyen touche « Envoyer », avec ou sans réseau
**Alors** le Signalement est d'abord écrit dans la File hors-ligne (transaction Dexie), puis l'envoi est déclenché depuis la File hors-ligne
**Et** aucun autre code de la PWA n'appelle `POST /v1/reports` : l'envoi direct de la Story 1.13 est remplacé par ce chemin unique (test d'architecture sur `web/src/`).

**Étant donné** une photo de plus de 300 Ko (307 200 octets)
**Quand** on tente de la mettre en file
**Alors** la mise en file est refusée par une assertion de la File hors-ligne, et le Citoyen est invité à reprendre la photo (la compression a lieu avant l'entrée).

**Étant donné** un Citoyen sans session au moment de la mise en file
**Quand** le Signalement entre dans la File hors-ligne
**Alors** son identité est figée à `device`
**Et** si une session d'Utilisateur connecté est active (comptes d'Epic 2), l'identité est figée à `user:<id>` de cet utilisateur
**Et** l'identité d'un élément n'est jamais modifiée ensuite.

**Étant donné** un téléphone en mode avion
**Quand** le Citoyen touche « Envoyer »
**Alors** la variante « en attente d'envoi » de l'écran 4 [HORS MAQUETTE] s'affiche dès la mise en file, sans attendre le réseau
**Et** elle remercie le Citoyen, explique que le Signalement est enregistré sur le téléphone et partira tout seul au retour du réseau, et n'affiche ni Numéro de suivi ni Frise de suivi
**Et** un bouton « Retour à l'accueil » ramène à l'écran 1.

**Étant donné** un téléphone en ligne dont la requête d'envoi échoue (erreur réseau ou délai dépassé)
**Quand** l'échec survient
**Alors** la même variante « en attente d'envoi » s'affiche
**Et** si une réponse 201 ou 200 arrive pendant que l'écran 4 est affiché, il passe à la confirmation normale (Numéro de suivi et Frise de suivi à l'étape « Signalé »).

**Étant donné** un Signalement créé en mode avion
**Quand** le Citoyen ferme l'application puis la rouvre, toujours en mode avion
**Alors** l'élément est présent dans la File hors-ligne avec 100 % de ses champs identiques, photo comprise (même `sha256` des octets), vérifié par un test Playwright en contexte hors ligne.

**Étant donné** une PWA installée qui a été ouverte une première fois avec du réseau
**Quand** le Citoyen l'ouvre en mode avion
**Alors** la coquille de l'application et la configuration (polygone de la Zone active, seuil de précision) sont disponibles depuis le cache, et le parcours écran 1 → écran 4 fonctionne entièrement sans réseau
**Et** si la configuration n'a jamais été mise en cache, l'écran 2 affiche « Connexion nécessaire pour la première utilisation ».

**Étant donné** la première mise en file sur un appareil
**Quand** elle a lieu
**Alors** la PWA demande un stockage persistant (`navigator.storage.persist()`), et un refus ne bloque pas le signalement.

**Étant donné** des éléments `device` encore dans la File hors-ligne avec `consent.training = true`
**Quand** le Citoyen retire son consentement au réentraînement dans les réglages (Story 1.16)
**Alors** ces éléments passent à `consent.training = false` avant leur envoi.

**Exigences :** FR-17, FR-4, NFR-4, NFR-6, NFR-12, NFR-13, NFR-SM-4, NFR-P1, AR-21, AR-37, UX-DR-7, UX-DR-8, UX-DR-10, UX-DR-16, UX-DR-23, AD-9, AD-12, AD-16
**Porte :** H48

### Story 6.2 : Envoyer automatiquement la File hors-ligne, sans doublon

En tant que Citoyen,
Je veux que mes Signalements en attente partent tout seuls au retour du réseau ou à l'ouverture de l'application,
Afin que la commune les reçoive sans que j'y pense, une seule fois chacun.

**Critères d'acceptation :**

**Étant donné** des éléments `pending` dans la File hors-ligne
**Quand** survient l'événement `online`, l'ouverture de l'application, une nouvelle mise en file ou l'échéance du prochain essai
**Alors** la File hors-ligne s'exécute dans la fenêtre de l'application
**Et** jamais dans le service worker : le code du service worker ne référence ni la File hors-ligne ni `/v1/reports`, et aucune synchronisation en arrière-plan (Background Sync) n'est enregistrée (test sur le bundle).

**Étant donné** l'application ouverte dans deux onglets
**Quand** la File hors-ligne s'exécute
**Alors** un seul exécutant tourne à la fois (`navigator.locks`, verrou `tc-outbox`) et les éléments partent un par un, dans l'ordre de mise en file, à l'état `sending` pendant leur requête
**Et** un élément resté `sending` parce que l'application a été fermée repasse `pending` à l'ouverture suivante et repart avec le même Identifiant client.

**Étant donné** un élément de la File hors-ligne
**Quand** le serveur répond 201 ou 200
**Alors** l'élément et sa photo sont retirés de la File hors-ligne
**Et** si la variante « en attente d'envoi » de l'écran 4 est affichée, elle passe à la confirmation avec le Numéro de suivi ; sinon l'écran 1 affiche « Votre Signalement TC-AAAA-NNNNNN est bien arrivé. Merci ! ».

**Étant donné** un élément de la File hors-ligne
**Quand** l'envoi échoue par erreur réseau, 408, 429 ou 5xx
**Alors** l'élément reste `pending`, son nombre d'essais augmente et son prochain essai est retardé selon un backoff exponentiel plafonné (base et plafond en réglages de la PWA)
**Et** après un 429, le prochain essai n'a pas lieu avant la durée indiquée par `Retry-After`
**Et** il n'y a pas de nombre maximal d'essais.

**Étant donné** un élément d'identité `device`
**Quand** il est envoyé
**Alors** la requête porte `X-Device-Id` et aucun en-tête `Authorization`, même si un utilisateur est connecté entre-temps.

**Étant donné** un élément d'identité `user:<id>` (comptes d'Epic 2)
**Quand** aucune session de cet utilisateur n'est active (pas de session, ou session d'un autre utilisateur)
**Alors** l'élément passe « en attente de connexion » (`waiting_login`), n'est pas envoyé et n'est pas un échec
**Et** il repart automatiquement dès que la session de cet utilisateur est rétablie
**Et** s'il reçoit 401, la File hors-ligne appelle `refreshSession()` puis réessaie une seule fois ; si le renouvellement est refusé, l'élément passe « en attente de connexion ».

**Étant donné** un élément de la File hors-ligne
**Quand** le serveur répond par un refus définitif (4xx autre que 408 et 429 : par exemple 400, 409, 413, 415, 422)
**Alors** l'élément passe à l'état `failed`, sort des éléments en attente d'envoi et n'est plus jamais retenté automatiquement
**Et** l'écran 1 le liste dans « Non envoyés » avec le motif issu de `errors.<code>` (par exemple « TerangaCycle n'est pas encore actif ici ») et un bouton « Supprimer » qui le retire avec sa photo.

**Étant donné** 10 Signalements créés en mode avion
**Quand** le réseau revient
**Alors** le serveur contient exactement 10 nouveaux Signalements, sans doublon, et la File hors-ligne est vide
**Et** si une réponse est perdue après le commit du serveur (coupure simulée), le renvoi reçoit 200 avec le même Numéro de suivi et un seul Signalement existe.

**Étant donné** 12 Signalements créés en mode avion par le même appareil
**Quand** le réseau revient
**Alors** 10 sont reçus, les 2 suivants reçoivent 429 et restent `pending`
**Et** ils sont reçus après l'expiration de `Retry-After` (test avec horloge simulée ou plafond réduit).

**Exigences :** FR-18, FR-9, NFR-SM-4, AR-18, AR-21, AR-37, UX-DR-10, UX-DR-20, AD-5, AD-6, AD-12, AD-30
**Porte :** H48

### Story 6.3 : Voir les Signalements en attente et relancer l'envoi

En tant que Citoyen,
Je veux voir combien de Signalements attendent d'être envoyés et pouvoir relancer l'envoi moi-même,
Afin d'être rassuré quand je retrouve du réseau.

**Critères d'acceptation :**

**Étant donné** l'écran 1 · Accueil (maquette Figma, nœud 1:2, compteur et bouton « Réessayer »)
**Quand** la File hors-ligne contient des éléments `pending`, `sending` ou `waiting_login`
**Alors** le compteur affiche leur nombre exact, mis à jour en moins d'1 s après chaque changement de la File hors-ligne
**Et** les éléments « en attente de connexion » sont signalés comme tels, et les éléments `failed` ne sont pas comptés.

**Étant donné** 3 Signalements en attente d'envoi
**Quand** la synchronisation réussit
**Alors** le compteur revient à 0 et le message « Tous vos Signalements sont envoyés » s'affiche.

**Étant donné** des éléments `pending` dont le prochain essai automatique est lointain, et du réseau
**Quand** le Citoyen touche « Réessayer » (pictogramme et libellé, cible ≥ 44 px)
**Alors** une tentative d'envoi part en moins d'1 s, sans attendre le prochain essai automatique (requête observée en test moins de 1 000 ms après l'appui)
**Et** les éléments « en attente de connexion » et `failed` ne sont pas concernés.

**Étant donné** un téléphone sans réseau
**Quand** le Citoyen touche « Réessayer »
**Alors** le message « Toujours hors ligne » s'affiche et est annoncé aux lecteurs d'écran (région `aria-live` polie)
**Et** les éléments restent dans la File hors-ligne, inchangés.

**Étant donné** le bouton « Réessayer »
**Quand** le Citoyen le touche deux fois rapidement
**Alors** une seule exécution de la File hors-ligne a lieu (verrou `tc-outbox`).

**Étant donné** l'écran 1
**Quand** l'état du réseau change
**Alors** un indicateur réseau affiche « En ligne » ou « Hors ligne » avec pictogramme et libellé, jamais par la seule couleur.

**Étant donné** l'écran 1 sur 390×844
**Quand** on l'audite
**Alors** le compteur est annoncé aux lecteurs d'écran, aucun débordement horizontal n'apparaît et l'audit d'accessibilité Lighthouse ne relève aucune violation critique ; tous les textes viennent de `fr.json`.

**Exigences :** FR-19, NFR-6, NFR-12, NFR-13, AR-37, UX-DR-7, UX-DR-8, UX-DR-9, UX-DR-11, UX-DR-20, AD-12
**Porte :** H60

## Epic 7 : Tableau de bord de la commune

L'Administrateur commune voit, pour une période choisie, les Indicateurs de la Cohorte, la Carte de chaleur et la répartition par Type de déchet retenu, et télécharge un Export agrégé CSV ou GeoJSON sans aucune donnée personnelle ; les Visiteurs voient une carte publique agrégée, jamais un point précis. Tout repose sur des vues analytiques en lecture seule (AD-22) et fonctionne aussi bien sur les Signalements collectés que sur les Données de démonstration, toujours étiquetées comme telles.

**Prérequis :** stories H24 à H60 des Epics 1, 2, 4 et 5 (Signalements, historique des Statuts `report_status_events`, Missions, Preuves de collecte, Poids estimé, tuiles `TILES_HOST`, Collecteurs vérifiés, Données de démonstration chargeables par `python -m app.cli demo load`) ; stories 5.14 et 5.15 (pilote) en plus pour la story 7.7.

### Story 7.1 : Vues analytiques en lecture seule

En tant qu'Administrateur commune,
Je veux que les Indicateurs soient calculés sur des vues analytiques déclarées, sans donnée personnelle,
Afin que les chiffres restent justes et stables quelle que soit l'évolution des autres modules.

**Critères d'acceptation :**

**Étant donné** le module `analytics` (aucune table, AD-2)
**Quand** une migration Alembic appelle `recreate_analytics_views()`
**Alors** les vues `v_report_facts`, `v_mission_facts` et `v_collector_facts` sont créées depuis `backend/app/modules/analytics/views/*.sql`, avec une liste de colonnes déclarée et sans `CASCADE`
**Et** `v_report_facts` expose les jalons lus dans `report_status_events` (`received_at`, `validated_at`, `rejected_at`, `assigned_at`, `collected_at`), le Statut courant, le Type de déchet retenu, la Taille de tas, le Poids estimé (`weight_estimates`, story 5.1), la Zone, la Position arrondie à 3 décimales (jamais la Position précise) et `is_demo`.

**Étant donné** `v_mission_facts`
**Quand** elle est lue
**Alors** elle expose `accepted_at` (acceptation de la Preuve de collecte), `weight_kg`, `weight_kind` (`weighed`/`estimated`), `review_status` (toujours `unreviewed` tant que la table `proof_reviews` n'existe pas ; la story 7.7 la branche), `retained_type`, l'identifiant interne du Collecteur et `is_demo`
**Et** `v_collector_facts` expose les Collecteurs vérifiés (identifiant interne, statut de vérification, `is_demo`) sans numéro ni nom.

**Étant donné** la CI
**Quand** elle exécute `alembic upgrade head` puis charge les Données de démonstration
**Alors** chaque vue est vérifiée contre son contrat (noms et types de colonnes) et la CI échoue à tout écart
**Et** un test échoue si une vue expose une colonne de numéro de téléphone, de nom, `author_user_id`, `owner_key`, `device_hash`, commentaire ou clé de photo.

**Étant donné** le rôle `teranga_app`
**Quand** il tente un `INSERT`, `UPDATE` ou `DELETE` sur une vue
**Alors** l'opération est refusée.

**Exigences :** FR-31, FR-32, FR-33, FR-34, FR-37 ; AD-2, AD-15, AD-22 (AR-10, AR-11, AR-31).
**Porte :** H60 ; opt. H48 si la story 7.6 est tirée à opt. H48 (ses prérequis 4.2, 5.1, 5.3 et 5.6 sont tous à H48)

### Story 7.2 : Calcul des Indicateurs de la Cohorte

En tant qu'Administrateur commune,
Je veux obtenir les Indicateurs de FR-31 pour la Cohorte d'une période choisie,
Afin de rendre compte au maire avec des chiffres vérifiables.

**Critères d'acceptation :**

**Étant donné** `GET /v1/analytics/indicators?from=<date>&to=<date>` (dates UTC incluses ; défaut : mois civil en cours)
**Quand** l'Administrateur commune l'appelle
**Alors** la réponse contient, pour la Cohorte (Signalements dont `received_at` serveur tombe dans la période) : Nombre de Signalements, dont ayant atteint `validé`, dont `rejeté` ; Délai médian ; nombre de Signalements de la Cohorte encore ouverts ; Taux de traitement ; Kg collectés (total, par Type de déchet, part `pesé`) ; Collecteurs vérifiés actifs ; répartition de la Cohorte par Type de déchet retenu (plus « sans Type retenu »)
**Et** `from` postérieur à `to`, ou une période de plus de 366 jours, renvoie 422.

**Étant donné** un jeu d'essai de 10 Signalements de la Cohorte ayant atteint `validé`, dont 6 `collecté`
**Quand** les Indicateurs sont calculés
**Alors** le Taux de traitement vaut 60 %
**Et** « ayant atteint » se lit dans l'historique des Statuts : un Signalement `assigné` ou `collecté` compte parmi ceux ayant atteint `validé` ; sans Signalement ayant atteint `validé`, le Taux est « non calculable » et non 0 %.

**Étant donné** des Signalements de la Cohorte ayant atteint `collecté` avec des délais connus (1 h, 3 h, 10 h)
**Quand** le Délai médian est calculé
**Alors** il vaut 3 h (réception serveur → acceptation de la Preuve de collecte)
**Et** les Signalements encore ouverts (ni `collecté` ni `rejeté`) sont comptés à part.

**Étant donné** des Preuves de collecte acceptées pendant la période
**Quand** les Kg collectés sont calculés
**Alors** ils somment les Poids déclarés des Preuves acceptées dans la période (et non de la Cohorte), au total et par Type de déchet retenu, avec la part `pesé` en pourcentage des kg (Kg collectés = Preuves dont `review_status` ≠ `contested` dans `v_mission_facts`)
**Et** les Collecteurs vérifiés actifs sont ceux ayant au moins une Preuve de collecte acceptée dans la période.

**Étant donné** un Signalement créé hors-ligne le 31 mars et reçu par le serveur le 1er avril
**Quand** la période est avril
**Alors** il appartient à la Cohorte d'avril.

**Étant donné** le contrôle d'accès
**Quand** un Citoyen, un Collecteur, un Modérateur ou une requête sans jeton appelle la route
**Alors** la réponse est 403 (ou 401 sans jeton) et la route figure dans le test route × rôle
**Et** hors Mode démonstration, les lignes `is_demo` sont exclues ; chaque réponse porte `contains_demo_data`.

**Exigences :** FR-31, FR-37 ; AD-9, AD-22 (AR-17, AR-31) ; NFR-9 ; SM-5, SM-6, SM-7, SM-9.
**Porte :** H60

### Story 7.3 : Écran 7 · Tableau de bord des Indicateurs

En tant qu'Administrateur commune,
Je veux voir les Indicateurs et la répartition par Type de déchet sur un écran unique, pour la période de mon choix,
Afin de préparer mon point mensuel en quelques minutes.

**Critères d'acceptation :**

**Étant donné** l'écran 7 (nœud Figma 2:65) sur un écran 1280×800
**Quand** l'Administrateur commune l'ouvre
**Alors** il voit un sélecteur de période (mois en cours par défaut) et les 5 tuiles : Nombre de Signalements (dont validés, dont rejetés), Délai médian (avec le nombre encore ouverts), Taux de traitement, Kg collectés par Type de déchet avec part `pesé`, Collecteurs vérifiés actifs
**Et** la répartition de la Cohorte par Type de déchet retenu utilise le composant `WasteTypeBadge` et les jetons `--color-waste-*` de la story 1.13 (pictogramme + libellé + couleur) et montre aussi les valeurs en chiffres.

**Étant donné** une réponse avec `contains_demo_data = true`
**Quand** l'écran s'affiche
**Alors** l'étiquette « Données de démonstration » est visible en haut de l'écran et sur chaque tuile, lisible par un lecteur d'écran
**Et** aucun libellé ne présente un chiffre de démonstration comme réel ni un objectif comme un résultat.

**Étant donné** un changement de période
**Quand** l'Administrateur commune valide la nouvelle période
**Alors** les tuiles et la répartition se mettent à jour, avec un squelette de chargement puis un état vide explicite si la Cohorte est vide
**Et** un Taux « non calculable » s'affiche « — » avec une explication, jamais « 0 % ».

**Étant donné** la navigation au clavier
**Quand** l'Administrateur commune parcourt l'écran avec Tab
**Alors** chaque contrôle est atteignable avec un focus visible, tous les textes passent par i18next (dates et nombres localisés en français), et l'audit Lighthouse accessibilité ne relève aucune erreur
**Et** aucun débordement horizontal n'apparaît à 1280×800.

**Exigences :** FR-31, FR-37 ; UX-DR-19, UX-DR-6, UX-DR-3, UX-DR-7, UX-DR-8, UX-DR-9 ; NFR-6, NFR-12, NFR-13 ; NFR-P2.
**Porte :** H60

### Story 7.4 : Carte de chaleur filtrable

En tant qu'Administrateur commune,
Je veux une Carte de chaleur des Signalements filtrable par période, Type de déchet et Statut,
Afin de repérer les zones où agir en priorité.

**Critères d'acceptation :**

**Étant donné** `GET /v1/analytics/heatmap?from=&to=&type=&status=` (Administrateur commune seulement)
**Quand** elle est appelée
**Alors** elle renvoie des cellules agrégées `{lat, lng, count}` (Positions arrondies à 3 décimales, groupées en base), jamais une ligne par Signalement avec Position précise
**Et** `type` filtre sur le Type de déchet retenu, `status` sur le Statut courant, la période sur la réception serveur ; une valeur hors énumération renvoie 422.

**Étant donné** l'écran 7, le fond de carte des tuiles `TILES_HOST` (story 5.2) et la couche `leaflet.heat` 1.0 enveloppée par `createLayerComponent` (react-leaflet)
**Quand** l'Administrateur commune change un filtre
**Alors** la carte se redessine selon les filtres, avec une légende textuelle et un résumé accessible (nombre de Signalements affichés)
**Et** l'étiquette « Données de démonstration » apparaît sur la carte si `contains_demo_data = true`.

**Étant donné** un jeu de 5 000 Signalements générés dans la Zone active (script de seed de performance, `is_demo`)
**Quand** l'Administrateur commune ouvre la carte ou change un filtre sur 1280×800
**Alors** la Carte de chaleur est affichée en moins de 2 s, du changement de filtre au dessin de la couche (mesure `performance.mark` consignée sur 10 essais, et audit Lighthouse)
**Et** la réponse de l'API pour ces 5 000 Signalements est inférieure à 300 ms au p95.

**Étant donné** un Citoyen, un Collecteur, un Modérateur ou une requête sans jeton
**Quand** il appelle la route
**Alors** il reçoit 403 (401 sans jeton), testé dans le test route × rôle.

**Exigences :** FR-32 ; NFR-3, NFR-2, NFR-9 ; AD-10, AD-16, AD-22 (AR-19, AR-36) ; UX-DR-19, UX-DR-6.
**Porte :** H60

### Story 7.5 : Export agrégé CSV et GeoJSON

En tant qu'Administrateur commune,
Je veux télécharger un Export agrégé en CSV ou en GeoJSON pour une période,
Afin de l'intégrer à mon rapport sans exposer aucune donnée personnelle.

**Critères d'acceptation :**

**Étant donné** `GET /v1/analytics/export?format=csv|geojson&from=&to=` (Administrateur commune seulement) et les boutons « Exporter CSV » et « Exporter GeoJSON » de l'écran 7
**Quand** l'Administrateur commune télécharge un export
**Alors** chaque ligne (ou entité) contient : date de réception (au jour), Zone, Statut, Type de déchet retenu, Taille de tas, Poids estimé, Poids déclaré et mention `pesé`/`estimé` le cas échéant, Position arrondie à 3 décimales, `is_demo`
**Et** le fichier ne contient ni numéro, ni nom, ni identifiant d'auteur, ni `owner_key`, ni Identifiant d'appareil, ni Numéro de suivi, ni commentaire, ni lien de photo.

**Étant donné** un export CSV et un export GeoJSON sur les Données de démonstration
**Quand** un test analyse chaque coordonnée
**Alors** aucune n'a plus de 3 décimales (CSV et `coordinates` GeoJSON)
**Et** le GeoJSON est une `FeatureCollection` valide (RFC 7946) de points.

**Étant donné** un export réalisé
**Quand** on consulte le Journal d'audit
**Alors** une entrée `export.aggregate` existe avec l'acteur, le format, la période et le nombre de lignes, sans donnée personnelle
**Et** le méta-test du Journal d'audit (story 2.6) prouve `export.aggregate`, qui n'est plus dans `PENDING_AUDIT_ACTIONS`.

**Étant donné** un export contenant des lignes `is_demo`
**Quand** le fichier est produit
**Alors** son nom contient `donnees-de-demonstration` et la première ligne du CSV (ou la propriété `contains_demo_data` du GeoJSON) le signale
**Et** hors Mode démonstration, les lignes `is_demo` sont exclues.

**Étant donné** un Citoyen, un Collecteur, un Modérateur ou une requête sans jeton
**Quand** il appelle la route
**Alors** il reçoit 403 (401 sans jeton), testé dans le test route × rôle.

**Exigences :** FR-33, FR-36, FR-37 ; AD-10 (niveau `rounded`), AD-22, AD-25 (AR-19, AR-29, AR-31) ; NFR-6.1a, NFR-6.4 ; UX-DR-19, UX-DR-6.
**Porte :** H60

### Story 7.6 : Carte publique agrégée pour les Visiteurs

En tant que Visiteur,
Je veux voir sans me connecter où se concentrent les dépôts signalés, par cellule ou par Zone,
Afin de constater l'action de la commune sans qu'aucun dépôt ne soit localisable précisément.

**Critères d'acceptation :**

**Étant donné** `GET /v1/public/map?by=cell|zone` (liste blanche publique)
**Quand** un Visiteur l'appelle sans jeton
**Alors** la réponse contient des cellules carrées d'au moins 500 m de côté (grille fixe en mètres, polygones et nombre de Signalements) ou des Zones (polygone et nombre), calculées sur les Signalements ayant atteint `validé`
**Et** toute cellule ou Zone de moins de 3 Signalements est absente de la réponse.

**Étant donné** un jeu d'essai de Signalements de Positions connues
**Quand** un test analyse toute la réponse publique
**Alors** aucune coordonnée de la réponse ne correspond à la Position d'un Signalement (toute coordonnée est un sommet de la grille de 500 m ou d'un polygone de Zone)
**Et** aucun champ n'expose d'identifiant, de Numéro de suivi, de photo, de date précise ni de Statut individuel.

**Étant donné** la page publique `/carte` de la PWA (accessible sans connexion)
**Quand** un Visiteur l'ouvre sur mobile 390×844 ou ordinateur
**Alors** il voit les cellules ou les Zones colorées selon leur nombre, une légende et la mention « Carte agrégée : aucun dépôt n'est localisé précisément »
**Et** l'étiquette « Données de démonstration » apparaît si la réponse porte `contains_demo_data = true` ; hors Mode démonstration, les Signalements `is_demo` sont exclus.

**Étant donné** l'ensemble des routes
**Quand** le test route × rôle s'exécute sans jeton
**Alors** `GET /v1/public/map` est la seule route cartographique accessible, et la Carte de chaleur et toute autre carte renvoient 401.

**Exigences :** FR-34 ; NFR-9 ; AD-9, AD-10 (niveau `aggregated`), AD-22 (AR-17, AR-19) ; UX-DR-32, UX-DR-6, UX-DR-9.
**Porte :** opt. H48 avec 7.1 (Should ; la story 7.1 passe alors elle aussi à opt. H48, voir sa porte), sinon après H60 ; prérequis : story 7.1

### Story 7.7 : Part des Preuves contestées sur le Tableau de bord

En tant qu'Administrateur commune,
Je veux voir la part de Preuves de collecte `contestée` parmi les Preuves revues,
Afin de surveiller la fiabilité des Poids déclarés plutôt que de pousser les kg par Mission.

**Critères d'acceptation :**

**Étant donné** la table `proof_reviews` (story 5.14)
**Quand** la migration de cette story s'applique
**Alors** `v_mission_facts.review_status` lit la Revue de Preuve courante (`confirmed`, `contested`, ou `unreviewed` sans revue) et la vue est recréée par `recreate_analytics_views()` (story 7.1)
**Et** le contrôle CI des contrats de vues de la story 7.1 passe.

**Étant donné** des Preuves acceptées dans la période dont une `contestée` (story 5.14)
**Quand** les Indicateurs sont calculés
**Alors** les Kg collectés l'excluent, au total et par Type de déchet.

**Étant donné** des Revues de Preuve sur la période (par exemple 20 Preuves revues dont 3 `contestée`)
**Quand** l'Administrateur commune appelle `GET /v1/analytics/indicators`
**Alors** la réponse contient la part de Preuves `contestée` parmi les Preuves revues de la période : 15 %, avec le nombre de Preuves revues
**Et** sans Preuve revue, la part est « non calculable ».

**Étant donné** l'écran 7
**Quand** il s'affiche
**Alors** une tuile « Preuves contestées » montre la part et le nombre de Preuves revues, avec l'étiquette « Données de démonstration » si applicable
**Et** la tuile est atteignable au clavier et lisible par un lecteur d'écran.

**Exigences :** FR-41, FR-31 ; SM-C3 ; AD-15, AD-22 (AR-11, AR-31) ; UX-DR-19.
**Porte :** pilote

## Epic 8 : Démo fiable et service exploitable

Le jury voit une démo qui tient même si le réseau tombe (serveur, portable de secours, vidéo, photos préparées, pitch répété et honnête), et l'Administrateur commune peut compter sur un service mesuré, durci, publié de façon réversible, supervisé, sauvegardé et restaurable avant toute donnée réelle du pilote.

**Prérequis :** 8.1 : stories 1.13, 3.12, 4.1, 5.2 ; 8.2 à 8.9 : stories H24 à H60 des Epics 1 à 7 (squelette Docker Compose et CI, parcours complet signaler → modérer → collecter → Tableau de bord, Mode démonstration et Données de démonstration) ; 8.10 à 8.15 : 8.1 à 8.9.
**Acteurs :** jury, Administrateur commune, équipe.
**FR couvertes :** aucune — NFR-2, NFR-5, NFR-7, NFR-8, NFR-10, NFR-15, NFR-16, NFR-17 (chiffrement au repos), NFR-P2, NFR-6.4, PRD §9.3 ; AR-3, AR-4, AR-6, AR-7, AR-33, AR-43 ; UX-DR-3.
**Porte :** démo (Stories 8.1 à 8.9) : H48 à H60 ; exploitation (Stories 8.10 à 8.15) : pilote.

### Story 8.1 : Couleurs validées des 5 Types de déchet

En tant que membre de l'équipe (design),
Je veux fixer une couleur par Type de déchet, conforme aux contrastes WCAG et validée sur les écrans,
Afin que Citoyens, Collecteurs et Personnel reconnaissent chaque matière d'un coup d'œil, sans dépendre de la seule couleur.

**Critères d'acceptation :**

**Étant donné** le bloc `@theme` unique de `web/src/theme/theme.css` et les cinq jetons provisoires `--color-waste-plastic`, `--color-waste-metal`, `--color-waste-glass`, `--color-waste-organic`, `--color-waste-mixed` déclarés par la story 1.13
**Quand** la story est livrée
**Alors** ces cinq jetons reçoivent leurs valeurs définitives, sans nouveau jeton ni changement de nom
**Et** aucune couleur de Type de déchet n'est déclarée ailleurs (test CI : aucune valeur hexadécimale hors de `theme.css` dans `web/src`)

**Étant donné** le script CI de contraste de UX-DR-2
**Quand** il calcule les paires déclarées
**Alors** chaque couleur de type atteint au moins 3:1 en élément non textuel contre Fond `#F6FAF7`, blanc `#FFFFFF` et Menthe `#EAF3EC`
**Et** le libellé écrit sur ou à côté du badge atteint au moins 4,5:1 contre son fond
**Et** le script échoue si l'on remplace une couleur par une valeur de contraste insuffisant (test négatif)

**Étant donné** les couleurs réservées du thème
**Quand** les couleurs de type sont choisies
**Alors** aucune n'est égale au Rouge `#D9482B` (erreur), au Jaune `#F2B705` (en attente) ni au Vert `#187A50` (marque)

**Étant donné** le composant unique `WasteTypeBadge` / `WasteTypePicker` (story 1.13)
**Quand** il est affiché sur les écrans 3 et 5 (390×844) et la File de modération (1280×800)
**Alors** il utilise les cinq jetons, toujours avec pictogramme + libellé i18n
**Et** des captures de ces trois écrans, en vision normale et sous les simulations deutéranopie, protanopie et tritanopie de Chrome DevTools, sont jointes à la revue et validées par Mia, choix consigné dans `.memlog.md`

**Exigences :** UX-DR-3, UX-DR-1, UX-DR-2, NFR-12, NFR-6.3b, AD-16
**Porte :** H48

### Story 8.2 : Mesurer et tenir le budget de premier chargement en 3G

En tant que membre de l'équipe,
Je veux mesurer le premier chargement de la PWA (WASM d'environ 15 Mo et Modèle) sur un réseau 3G,
Afin de savoir avant la démo ce que vit un Citoyen sur un Android d'entrée de gamme et de garantir que le signalement n'attend jamais le Modèle.

**Critères d'acceptation :**

**Étant donné** la PWA construite en production et servie par Caddy
**Quand** la CI mesure le bundle
**Alors** la page d'accueil pèse au plus 500 Ko transférés hors images et Modèle, le fichier `.onnx` au plus 8 Mo et la précache au plus 20 Mio, sinon la CI échoue

**Étant donné** un Android 8+ avec Chrome et 2 Go de RAM, cache vidé, et le profil réseau 3G de Chrome DevTools (1,6 Mb/s descendant, 750 kb/s montant, 562,5 ms de latence)
**Quand** l'équipe ouvre la PWA pour la première fois, puis une seconde fois
**Alors** elle mesure et consigne pour chaque visite : temps jusqu'à l'écran 1 utilisable, temps jusqu'à la mise en cache complète du WASM et du Modèle, octets transférés
**Et** à la seconde visite, le `.onnx` et les `.wasm` viennent de la précache (0 octet réseau pour ces fichiers) et le parcours de signalement fonctionne en mode avion

**Étant donné** un premier chargement où le Modèle n'est pas encore en cache
**Quand** un test Playwright retarde de 60 s la réponse du `.onnx` sous le même profil 3G
**Alors** le Citoyen passe de l'écran 1 à l'écran 3 sans attendre, choisit lui-même le Type de déchet et envoie le Signalement

**Étant donné** les mesures consignées
**Quand** l'une dépasse un budget de NFR-5
**Alors** l'équipe ouvre une issue avec la cause et l'action, et la liste de préparation de la démo exige que chaque téléphone de démo ait la PWA installée et le Modèle en cache avant le pitch

**Exigences :** NFR-5, NFR-6, AR-43, AR-38, AD-16, AD-29, FR-11 (repli sans Modèle)
**Porte :** H60

### Story 8.3 : Test de charge k6 de la lecture API

En tant que membre de l'équipe,
Je veux un test de charge k6 reproductible sur les routes de lecture,
Afin de prouver que l'API tient p95 < 300 ms à 50 requêtes par seconde.

**Critères d'acceptation :**

**Étant donné** l'instance au profil `demo` chargée avec 5 000 Signalements de Données de démonstration et au moins 100 comptes de test étiquetés
**Quand** le script `infra/load/k6-read.js` s'exécute (1 min de montée, puis 5 min à 50 requêtes/s en `constant-arrival-rate`)
**Alors** il répartit la charge entre `GET /v1/config`, `GET /v1/missions/candidates`, `GET /v1/reports/mine`, la File de modération et les indicateurs du Tableau de bord, chaque requête étiquetée par route
**Et** chaque compte reste sous 60 requêtes/min (aucun 429 attendu ; un 429 compte comme échec)

**Étant donné** les seuils k6 `http_req_duration p(95) < 300` (global et par route) et `http_req_failed < 1 %`
**Quand** un seuil est dépassé
**Alors** k6 sort avec un code non nul et le rapport désigne les routes en cause

**Étant donné** la machine qui exécute k6
**Quand** le test démarre
**Alors** elle est sur le même réseau que le serveur, et la latence réseau de base (ping) est consignée avec le résultat

**Étant donné** le dépôt
**Quand** un membre de l'équipe lance le workflow GitHub manuel (`workflow_dispatch`) de test de charge
**Alors** le résumé JSON de k6 est archivé comme artefact, et le résultat de la dernière exécution avant la démo est consigné dans le dossier de démo
**Et** les comptes de test de charge sont retirés par `python -m app.cli demo purge`

**Exigences :** NFR-2, AD-8, AD-20, AR-32
**Porte :** H60

### Story 8.4 : Bord HTTP durci et vérifié

En tant qu'Administrateur commune,
Je veux que le bord HTTP applique et prouve les protections exigées,
Afin que ni le jury ni un attaquant ne trouvent d'en-tête manquant, de surface interne exposée ou de donnée personnelle dans les journaux.

**Critères d'acceptation :**

**Étant donné** la pile Docker Compose démarrée en CI avec Caddy
**Quand** le test du bord HTTP s'exécute
**Alors** il vérifie la valeur exacte de chaque en-tête posé par Caddy seul : HSTS (`max-age` ≥ 31536000), la CSP d'AD-23 (`default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; img-src 'self' blob: data: https://<MEDIA_HOST> https://<TILES_HOST>; connect-src 'self' https://<MEDIA_HOST>; worker-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'`), `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`
**Et** l'absence de COOP et COEP, un `.wasm` servi en `application/wasm`, et aucun en-tête posé deux fois

**Étant donné** une requête HTTP ou une poignée de main TLS
**Quand** le test l'envoie
**Alors** HTTP est redirigé vers HTTPS (301 ou 308), TLS 1.0 et 1.1 sont refusés, TLS 1.2 et 1.3 acceptés

**Étant donné** `ENV=prod`
**Quand** le test appelle `/docs`, `/redoc` et `/openapi.json`, puis `/metrics` et `/v1/ai/*` depuis l'extérieur
**Alors** toutes ces routes sont refusées (404 ou 403) ; `/metrics` reste joignable depuis le réseau interne de Compose
**Et** avec `ENV=demo`, `/docs` est servi
**Et** une requête d'une origine étrangère ne reçoit aucun `Access-Control-Allow-Origin`

**Étant donné** une photo servie par `MEDIA_HOST`
**Quand** le test la lit par URL signée
**Alors** la réponse ne pose aucun cookie et l'URL est refusée au-delà de 5 min

**Étant donné** une requête portant `Authorization`, `Cookie`, `X-Device-Id`, `Idempotency-Key` et `?lat=14.69&lng=-17.44`
**Quand** le test lit les journaux d'accès de Caddy
**Alors** aucune de ces valeurs n'y figure
**Et** un corps supérieur à `MAX_BODY_BYTES` est refusé (413) par Caddy

**Étant donné** la base, Valkey, le stockage ou le Modèle indisponible tour à tour
**Quand** le test appelle `/readyz`, puis `/healthz`
**Alors** `/readyz` répond « non prêt » avec un statut global seul, sans détail par composant, et `/healthz` répond tant que le processus vit

**Étant donné** la PWA sous cette CSP
**Quand** un test Playwright lance une classification
**Alors** le WASM se charge sans aucune violation CSP dans la console
**Et** un scan SSL du domaine de démo est archivé, sans protocole inférieur à TLS 1.2

**Exigences :** NFR-7, NFR-8, NFR-14, AD-23, AR-4, AD-13
**Porte :** H60

### Story 8.5 : Publier par empreinte et revenir en arrière en une commande

En tant que membre de l'équipe,
Je veux publier chaque version par empreinte et pouvoir revenir à la précédente en une commande,
Afin de déployer sans crainte avant la démo et pendant le pilote.

**Critères d'acceptation :**

**Étant donné** une fusion sur `main` avec la CI verte
**Quand** le workflow de publication s'exécute
**Alors** il publie `ghcr.io/<org>/terangacycle-api:<sha>` (API et worker) et la PWA statique de ce même `<sha>`, et consigne l'empreinte `sha256` de l'image

**Étant donné** le workflow de publication
**Quand** la CI l'analyse
**Alors** le contrôle d'épinglage de la story 1.5 couvre aussi ce workflow (images par `@sha256:`, actions par SHA de commit)

**Étant donné** pip-audit, npm audit et Trivy (image API) en CI
**Quand** une vulnérabilité critique ou haute est détectée
**Alors** la CI échoue, sauf si elle figure dans `security/exceptions.yaml` avec justification et date d'expiration non dépassée (test négatif avec une exception échue)

**Étant donné** le script `infra/deploy.sh <sha>`
**Quand** il s'exécute
**Alors** il fixe `IMAGE_TAG=<sha>`, tire les images, lance le service `migrate` (usage unique), puis `docker compose up -d`
**Et** si `migrate` échoue, le script s'arrête et la version en place continue de servir ; si `/readyz` n'est pas prêt sous 60 s, il sort en erreur et affiche la commande de retour arrière

**Étant donné** une version N déployée et une version N+1 contenant une migration d'expansion (colonne ajoutée, nullable)
**Quand** l'équipe déploie N+1, puis exécute `infra/deploy.sh <sha de N>`
**Alors** N tourne sur le schéma de N+1, `/readyz` est prêt, et un test de fumée crée puis relit un Signalement
**Et** l'exercice est chronométré et consigné, avec un retour arrière effectif en 5 min au plus

**Étant donné** une migration qui supprime ou renomme une colonne
**Quand** la CI l'analyse
**Alors** la suite de fumée de la version précédente est rejouée sur le nouveau schéma et doit passer (règle expand/contract)

**Exigences :** AD-28, AD-15, NFR-10, NFR-11, AR-7, AR-8, AR-11
**Porte :** H60

### Story 8.6 : Déployer l'instance de démonstration sur le serveur

En tant que jury,
Je veux voir la démo tourner sur un vrai serveur, accessible depuis un téléphone Android sur réseau mobile,
Afin de juger un service réel et non une maquette.

**Critères d'acceptation :**

**Étant donné** un serveur x86_64 et le profil Compose `demo`
**Quand** l'équipe exécute `infra/deploy.sh <sha>` avec `ENV=demo` et `DEMO_MODE=true`
**Alors** les services `caddy`, `api`, `worker`, `migrate`, `db`, `valkey` et `garage` démarrent avec les images par empreinte, et `/readyz` est prêt
**Et** les secrets viennent de `.env.secrets` (hors Git) montés dans `/run/secrets/*`

**Étant donné** les noms `APP_HOST`, `MEDIA_HOST` et `TILES_HOST` de la démo
**Quand** un Android 8+ avec Chrome et 2 Go de RAM les ouvre sur réseau mobile
**Alors** les certificats sont valides sans avertissement et la PWA est installable

**Étant donné** l'instance démarrée
**Quand** l'équipe exécute `python -m app.cli demo load`
**Alors** chaque écran affiche le bandeau « Mode démonstration » et l'étiquette « Données de démonstration », et les comptes de test de chaque rôle se connectent avec le code OTP affiché à l'écran

**Étant donné** l'instance chargée
**Quand** le script Playwright de la boucle SM-1 s'exécute contre le serveur (Signalement hors-ligne → modération → Mission → Preuve de collecte → Tableau de bord), puis la même boucle à la main sur un Android réel
**Alors** les deux passent

**Étant donné** l'instance en service
**Quand** l'équipe exécute `docker compose restart`
**Alors** les données, les photos et les compteurs de limitation de débit sont conservés (volumes, Valkey en AOF)
**Et** `demo purge` suivi de `demo load` remet l'état initial de la démo en 2 min au plus

**Exigences :** NFR-7, NFR-6, AR-3, AR-5, AR-32, FR-37 (référence), FR-6 (référence), SM-1, AD-14
**Porte :** H60

### Story 8.7 : Portable de secours et tuiles de la zone de démo sans Internet

En tant que jury,
Je veux que la démo continue même si le réseau de la salle tombe,
Afin de voir la boucle complète quoi qu'il arrive.

**Critères d'acceptation :**

**Étant donné** un portable x86_64 préparé
**Quand** l'équipe lance `docker compose --profile demo up -d` avec les mêmes empreintes d'images et le même jeu de Données de démonstration que le serveur
**Alors** `/readyz` est prêt en 3 min au plus

**Étant donné** le portable sans aucun accès à Internet, qui fournit un point d'accès Wi-Fi et un résolveur DNS local renvoyant `APP_HOST`, `MEDIA_HOST` et `TILES_HOST` vers son adresse
**Quand** un téléphone de démo se connecte à ce Wi-Fi
**Alors** la PWA s'ouvre en HTTPS sans avertissement, grâce à un certificat valide pour ces noms obtenu à l'avance (défi DNS), jamais un certificat auto-signé
**Et** la boucle SM-1 complète passe sur un Android réel, câble Internet débranché

**Étant donné** les tuiles de la zone de démo préparées par la story 5.2
**Quand** le portable est préparé
**Alors** elles sont copiées sur le portable et servies par son Caddy sur `TILES_HOST`, comme sur le serveur

**Étant donné** Internet coupé
**Quand** l'écran 5 et la Carte de chaleur s'affichent dans l'emprise et les zooms préparés
**Alors** aucune requête de tuile n'échoue (journal réseau sans 404 ni erreur)

**Étant donné** la procédure de bascule du serveur vers le portable
**Quand** l'équipe la répète
**Alors** elle tient en 5 min au plus, chronométrées et consignées
**Et** la procédure rappelle que le portable repart du jeu de Données de démonstration (les données créées en direct sur le serveur n'y sont pas)

**Exigences :** NFR-7, PRD §9.3 (réseau instable), AR-3, AD-23 (`TILES_HOST`), NFR-6.4
**Porte :** H60

### Story 8.8 : Plans B : vidéo de la démo complète et 10 photos locales préparées

En tant que membre de l'équipe,
Je veux une vidéo de la démo complète et 10 photos locales testées avec le Modèle,
Afin de pouvoir montrer la boucle même si le réseau, la File hors-ligne ou le Modèle font défaut.

**Critères d'acceptation :**

**Étant donné** l'instance de démonstration
**Quand** l'équipe enregistre la vidéo avant H60
**Alors** la vidéo montre la boucle SM-1 complète et commence par la séquence « mode avion » (Signalement hors-ligne, puis envoi au retour du réseau)
**Et** le bandeau « Mode démonstration » et l'étiquette « Données de démonstration » sont visibles sur chaque écran montrant des données, et aucune photo ne montre de personne ni de plaque

**Étant donné** la vidéo finale (MP4 H.264, 1080p)
**Quand** elle est stockée
**Alors** elle existe en au moins deux copies hors ligne (portable du présentateur et clé USB) et sa lecture est testée sans réseau sur le matériel de projection

**Étant donné** 10 photos prises au Sénégal, 2 par Type de déchet, sans personne ni plaque
**Quand** chacune passe dans le Modèle de la version déployée
**Alors** le Type de déchet proposé et le Score de confiance de chaque photo sont consignés
**Et** le pitch utilise au moins une photo bien classée au-dessus de 60 % et une photo qui montre la Correction comme une fonctionnalité (Score sous 60 % ou type corrigé)
**Et** les 10 photos sont présentes dans la galerie de chaque téléphone de démo et sur le portable

**Étant donné** la passerelle SMS indisponible
**Quand** un compte de test se connecte
**Alors** le Mode démonstration affiche le code OTP à l'écran et la connexion aboutit sans SMS

**Étant donné** le tableau des risques du PRD §9.3
**Quand** la liste des plans B est rédigée dans le dossier de démo
**Alors** chaque risque a son plan B, la personne qui le déclenche et le geste à faire, en une ligne chacun

**Exigences :** NFR-7, PRD §9.3, SM-1, SM-2, FR-13 (Correction montrée), FR-6 (référence), NFR-6.3a, NFR-P2
**Porte :** H60

### Story 8.9 : Répétition chronométrée du pitch de 1 min 30 avec données étiquetées

En tant que jury,
Je veux une démo de 1 min 30 claire et honnête,
Afin de juger la chaîne de confiance sur pièces, sans chiffre fictif présenté comme réel.

**Critères d'acceptation :**

**Étant donné** le script du pitch
**Quand** il est rédigé
**Alors** il découpe 90 s au plus en séquences minutées (qui parle, quel écran, quelle action)

**Étant donné** l'instance de démonstration remise à zéro (`demo purge` puis `demo load`) avant chaque répétition
**Quand** l'équipe répète au moins 3 fois sur le serveur avec les vrais téléphones
**Alors** chaque durée est chronométrée et consignée, et les deux dernières répétitions tiennent en 90 s au plus

**Étant donné** les plans B
**Quand** l'équipe fait une répétition sur le portable de secours, puis une répétition où elle bascule vers la vidéo à un moment tiré au sort
**Alors** les deux aboutissent et la bascule vers la vidéo prend 10 s au plus

**Étant donné** chaque répétition
**Quand** un membre de l'équipe qui ne présente pas la relit avec une liste de contrôle
**Alors** chaque écran montré porte le bandeau ou l'étiquette de démonstration
**Et** chaque chiffre prononcé est présenté comme Données de démonstration ou comme objectif à mesurer (SM-1 à SM-9), jamais comme un résultat réel

**Étant donné** le jour du pitch
**Quand** la liste de préparation est vérifiée
**Alors** chaque téléphone a la PWA installée, le Modèle en cache, une batterie d'au moins 80 % et les notifications système coupées

**Exigences :** NFR-P2, NFR-7, UX-DR-5, UX-DR-6, SM-1, PRD §7 (honnêteté)
**Porte :** H60

### Story 8.10 : Secrets et clés tenus par l'organisation, rotation éprouvée

En tant qu'Administrateur commune,
Je veux que les secrets du service soient tenus par l'organisation et puissent tourner sans perte de données,
Afin qu'une fuite ou un départ ne compromette ni les comptes ni les numéros de téléphone.

**Critères d'acceptation :**

**Étant donné** le refus de démarrage sur secret manquant (test de la story 1.2) et l'inventaire fixe d'AD-26 (`JWT_SIGNING_KEYS`, `PHONE_PEPPER`, `DEVICE_ID_PEPPER`, `PHONE_ENC_KEYS`, `TOTP_ENC_KEY`, `VAPID_PRIVATE_KEY`, identifiants S3, `ALERT_WEBHOOK_URL`)
**Quand** on l'étend aux secrets provisionnés par le KMS du pilote
**Alors** l'API en `prod` lit chaque secret depuis `/run/secrets/*` alimenté par le KMS, et refuse toujours de démarrer si l'un manque (un test par secret)

**Étant donné** le dépôt et les images publiées
**Quand** Gitleaks (historique complet) et Trivy (détection de secrets) s'exécutent
**Alors** aucun secret n'est trouvé, et `docker image inspect` ne contient aucune valeur de secret

**Étant donné** l'environnement du pilote
**Quand** les secrets sont provisionnés
**Alors** ils sont dans le KMS ou le gestionnaire de secrets de l'hébergeur, sur un compte de l'organisation (aucun compte personnel), et la liste des rôles qui y accèdent est consignée

**Étant donné** une nouvelle clé JWT ajoutée sous un nouveau `kid`
**Quand** l'API redémarre
**Alors** les nouveaux jetons sont signés avec la clé la plus récente et les jetons signés avec l'ancien `kid` restent acceptés jusqu'à leur expiration
**Et** après retrait de l'ancienne clé, un jeton signé avec elle est refusé (401)

**Étant donné** une nouvelle clé AES-GCM ajoutée à `PHONE_ENC_KEYS` (même procédure pour `TOTP_ENC_KEY`)
**Quand** le script de réécriture s'exécute
**Alors** les nouvelles écritures portent le nouveau `key_id`, les anciennes valeurs restent lisibles pendant la réécriture, puis toutes portent le nouveau `key_id`
**Et** les comptes de test se connectent à chaque étape, et l'ancienne clé peut alors être retirée

**Étant donné** la procédure de rotation
**Quand** elle est documentée et exécutée une fois sur l'environnement de préproduction du pilote
**Alors** l'exercice est consigné, et la procédure rappelle qu'un pepper HMAC ne change jamais sans migration de recalcul

**Exigences :** AD-26, NFR-10, NFR-17, NFR-6.1b, NFR-6.4, AR-6, AD-30
**Porte :** pilote

### Story 8.11 : Supervision et alertes de l'équipe

En tant qu'Administrateur commune,
Je veux que l'équipe soit alertée dès qu'un incident menace le service,
Afin de réagir avant que les Citoyens et les Collecteurs ne le subissent.

**Critères d'acceptation :**

**Étant donné** le code du backend
**Quand** la CI l'analyse
**Alors** seul `core.alerts.raise_alert(code, context)` envoie vers `ALERT_WEBHOOK_URL` (test d'architecture), et les codes forment la liste close `sms_cap_reached`, `classification_queue_full`, `http_5xx_rate`, `backup_failed`, `disk_high`

**Étant donné** la tâche planifiée `ops.health_sweep` (toutes les minutes)
**Quand** elle calcule le taux de 5xx sur les 5 dernières minutes depuis les compteurs de `/metrics`
**Alors** 21 réponses 5xx sur 1 000 (2,1 %) déclenchent `http_5xx_rate` et 20 sur 1 000 (2,0 %) ne déclenchent rien
**Et** aucune alerte de taux ne part sous 20 requêtes dans la fenêtre

**Étant donné** l'occupation des volumes de la base et du stockage
**Quand** `ops.health_sweep` mesure 86 % puis 85 %
**Alors** 86 % déclenche `disk_high` et 85 % ne déclenche rien

**Étant donné** chacun des cinq codes
**Quand** un test simule son déclenchement (plafond SMS atteint, file de Classification serveur pleine, taux de 5xx, sauvegarde en échec, disque plein) avec un faux serveur de webhook
**Alors** le webhook reçoit un message avec le code, l'environnement, l'horodatage et un contexte court
**Et** le message ne contient jamais de numéro de téléphone, de jeton, de Position ni d'Identifiant d'appareil

**Étant donné** une horloge simulée
**Quand** le même code est levé deux fois en 15 min, puis une fois après 15 min
**Alors** un seul message part dans les 15 premières minutes et un second ensuite ; deux codes différents ne se bloquent pas

**Étant donné** le webhook injoignable
**Quand** une alerte est levée
**Alors** l'échec est journalisé, l'API et le worker continuent, et l'alerte est retentée au passage suivant

**Étant donné** le battement `worker:heartbeat`
**Quand** il a plus de 60 s
**Alors** `/readyz` n'est plus prêt

**Étant donné** une sonde externe qui interroge `/healthz` toutes les minutes depuis un autre hôte
**Quand** on génère le rapport de disponibilité sur une période (test sur 24 h simulées avec 15 min de panne)
**Alors** il affiche 98,96 % et la cible de 99 %
**Et** le premier rapport mensuel réel est une tâche d'exploitation, hors story

**Exigences :** NFR-16, NFR-15 (disponibilité), NFR-14, AD-27, AD-18, AR-33, FR-1 et FR-14 (alertes, référence)
**Porte :** pilote

### Story 8.12 : Sauvegardes quotidiennes chiffrées hors de l'hôte

En tant qu'Administrateur commune,
Je veux une sauvegarde quotidienne chiffrée de la base et des photos, conservée hors du serveur,
Afin de ne jamais perdre plus de 24 h de données.

**Critères d'acceptation :**

**Étant donné** l'environnement `prod`
**Quand** la sauvegarde quotidienne s'exécute (service planifié du profil `prod` de `docker-compose.yml`)
**Alors** elle produit un `pg_dump -Fc` chiffré avec une clé publique de l'organisation (la clé privée n'est pas sur l'hôte) et copie tous les objets du bucket, vers un stockage hors de l'hôte appartenant à un autre compte
**Et** chaque exécution journalise taille, durée et empreinte `sha256`, sans donnée personnelle

**Étant donné** `BACKUP_RETENTION_DAYS = 30` et une horloge simulée
**Quand** une sauvegarde a 31 jours
**Alors** elle est supprimée de la destination, et celles de 30 jours ou moins sont conservées

**Étant donné** une destination injoignable, une erreur de `pg_dump` ou une erreur de chiffrement (un test par cas)
**Quand** la sauvegarde échoue
**Alors** `core.alerts.raise_alert("backup_failed", ...)` est appelé

**Étant donné** la dernière sauvegarde réussie
**Quand** `ops.health_sweep` constate qu'elle a plus de 25 h
**Alors** `backup_failed` est levé (perte maximale de 24 h, marge d'1 h)

**Étant donné** un fichier de sauvegarde à la destination
**Quand** on tente de le lire sans la clé privée
**Alors** `pg_restore --list` échoue et aucune chaîne en clair d'une table métier n'y figure

**Exigences :** NFR-15, NFR-17, NFR-16, AD-27, NFR-6.4
**Porte :** pilote

### Story 8.13 : Chiffrement au repos de la base et des photos

En tant qu'Administrateur commune,
Je veux que la base, les photos et le cache soient chiffrés sur disque avec des clés de l'organisation,
Afin qu'un disque volé ou un hôte compromis à froid ne livre aucune donnée personnelle.

**Critères d'acceptation :**

**Étant donné** l'hôte du pilote (base auto-hébergée)
**Quand** les volumes de `db`, `garage` et `valkey` sont provisionnés
**Alors** ils résident sur un disque chiffré LUKS dont la clé est détenue par l'organisation
**Et** si la base est managée (§11 Q3), le chiffrement au repos du fournisseur est activé avec une clé gérée par l'organisation, et ce choix est consigné

**Étant donné** l'hôte redémarré
**Quand** la clé n'a pas été fournie
**Alors** les volumes ne sont pas montés et les services ne démarrent pas ; la procédure de déverrouillage est documentée et répétée une fois

**Étant donné** une lecture brute du périphérique chiffré
**Quand** on y cherche un Numéro de suivi connu et l'en-tête JPEG `FF D8 FF`
**Alors** aucun n'est trouvé

**Étant donné** les clés de chiffrement
**Quand** la procédure de garde est vérifiée
**Alors** chaque clé existe en deux exemplaires conservés séparément par l'organisation, et la procédure en cas de perte est consignée

**Exigences :** NFR-17, NFR-6.1b, AD-27, AD-26
**Porte :** pilote

### Story 8.14 : Restauration complète testée sur un hôte vierge

En tant qu'Administrateur commune,
Je veux qu'une restauration complète ait réussi sur un hôte vierge avant la première donnée réelle,
Afin d'être sûr de pouvoir reprendre le service et de pouvoir quitter l'hébergeur à tout moment.

**Critères d'acceptation :**

**Étant donné** un hôte qui n'a jamais porté le service, le dépôt, les images par empreinte, les sauvegardes et les clés de l'organisation
**Quand** l'équipe restaure la base (`pg_restore`) et le bucket, démarre le profil `prod`, puis exécute `retention.sweep` avant d'ouvrir le trafic
**Alors** `/readyz` est prêt

**Étant donné** l'instance restaurée
**Quand** l'équipe la compare à la source à l'heure de la sauvegarde
**Alors** le nombre de lignes de chaque table est identique, l'empreinte `sha256` de 20 photos tirées au hasard est identique, des URL signées s'ouvrent, et les comptes de test se connectent (numéros déchiffrés)
**Et** le nombre d'entrées du Journal d'audit est identique et aucune n'a été modifiée

**Étant donné** l'exercice terminé
**Quand** il est consigné
**Alors** le compte rendu donne la durée de restauration mesurée et la perte de données (écart entre la sauvegarde et l'incident simulé), au plus 24 h
**Et** la collecte de données réelles du pilote ne s'ouvre qu'après ce compte rendu et la déclaration à la CDP

**Exigences :** NFR-15, NFR-6.4, NFR-6.3a, AD-27, AD-18
**Porte :** pilote

### Story 8.15 : Restauration de sortie vers un autre hébergeur

En tant qu'Administrateur commune,
Je veux qu'une restauration complète ait réussi chez un autre hébergeur avant la fin du pilote,
Afin de prouver que la commune peut quitter l'hébergeur actuel, par exemple pour un hébergement au Sénégal.

**Critères d'acceptation :**

**Étant donné** le plan de sortie du PRD §6.4, la procédure de restauration de la story 8.14, un export complet (base et photos) et les clés détenues par l'organisation
**Quand** l'équipe restaure le service sur un hôte d'un autre hébergeur (cible : hébergement au Sénégal)
**Alors** `/readyz` est prêt et les contrôles de comparaison de la story 8.14 (nombre de lignes, empreintes de 20 photos, URL signées, connexion des comptes de test, Journal d'audit inchangé) passent

**Étant donné** l'exercice terminé
**Quand** il est consigné
**Alors** le compte rendu donne l'hébergeur cible, la durée de restauration, les écarts constatés et les formats ouverts utilisés pour l'export
**Et** il est joint au dossier de fin de pilote

**Exigences :** NFR-6.4, NFR-15, AD-27, AD-28
**Porte :** pilote (avant la fin du pilote)

## Epic 9 : Lots de matière (extension)

Le Collecteur déclare la matière qu'il a récupérée en Lots de matière ; le Recycleur consulte les Lots `disponible` sans voir l'identité du Collecteur, obtient son contact sur demande et réserve un Lot.

**Prérequis :** stories H24 à H48 des Epics 1, 2, 4 et 5 (Zones de la Zone active, rôles Collecteur et Recycleur, Collecteurs vérifiés, composant Type de déchet, capture et compression de photo, `core.storage.ingest_photo()`, URL signées).
**Écrans :** [HORS MAQUETTE — à concevoir] (UX-DR-33), mêmes jetons et police Inter.
**FR couvertes :** FR-38, FR-39, FR-40
**Porte :** extension (après H48, hors démo) ; FR-38 et FR-39 : Should ; FR-40 : Could.

### Story 9.1 : Déclarer un Lot de matière (API)

En tant que Collecteur vérifié,
Je veux déclarer un Lot de matière avec son Type de déchet, son poids, sa Zone et une photo,
Afin de le proposer aux Recycleurs.

**Critères d'acceptation :**

**Étant donné** la base au schéma courant
**Quand** la migration Alembic de cette story s'applique
**Alors** la table `material_lots` existe (identifiant, `collector_id`, `waste_type`, `weight_kg NUMERIC(8,2) CHECK (weight_kg > 0)`, `zone_id`, clé et `sha256` de la photo, `status` contraint à `available` ou `reserved` et valant `available` par défaut, `created_at`, `is_demo`), écrite par le seul module `lots`

**Étant donné** un Collecteur vérifié
**Quand** il appelle `POST /v1/lots` en `multipart/form-data` (`meta` : `waste_type`, `weight_kg`, `zone_id` ; `photo`) avec une `Idempotency-Key`
**Alors** il reçoit 201 avec un Lot au Statut de Lot `disponible`, `created_at` = `core.clock.now()`, et `is_demo` vrai en Mode démonstration
**Et** un renvoi avec la même clé rejoue la réponse sans créer de second Lot

**Étant donné** une déclaration sans Type de déchet, avec un poids ≤ 0, sans Zone, avec une Zone hors de la Zone active, ou sans photo (un test par cas)
**Quand** elle est envoyée
**Alors** elle est refusée (422) et rien n'est créé
**Et** la photo passe par `core.storage.ingest_photo()` (type `lot`) : 415 hors JPEG, PNG et WebP ; 413 ou 422 au-delà de 1 Mo ou 12 Mpx ; métadonnées supprimées

**Étant donné** un Collecteur vérifié
**Quand** il appelle `GET /v1/zones` puis `GET /v1/lots/mine`
**Alors** il reçoit la liste des Zones (quartiers) de la Zone active, puis ses seuls Lots, plus récents d'abord, paginés

**Étant donné** un Collecteur non vérifié, un Citoyen, un Recycleur ou un membre du Personnel
**Quand** il appelle `POST /v1/lots`
**Alors** il reçoit 403 (test « route × rôle »)

**Exigences :** FR-38, AD-2, AD-5, AD-11, AD-13, AD-14, NFR-9
**Porte :** Should, extension

### Story 9.2 : Écran de déclaration d'un Lot et « Mes Lots »

En tant que Collecteur vérifié,
Je veux déclarer un Lot depuis mon téléphone et suivre l'état de mes Lots,
Afin de vendre ma matière sans démarche papier.

**Critères d'acceptation :**

**Étant donné** un Collecteur vérifié sur un écran de 390×844
**Quand** il ouvre « Déclarer un lot » [HORS MAQUETTE]
**Alors** il choisit le Type de déchet avec le sélecteur commun (pictogramme + libellé + couleur), saisit le poids en kg (> 0, virgule décimale), choisit la Zone dans la liste des quartiers et prend une photo (consigne « ni personne ni plaque », compression à 300 Ko au plus)
**Et** le bouton « Déclarer » reste désactivé tant qu'un champ manque

**Étant donné** une réponse 422
**Quand** elle arrive
**Alors** le message du champ en cause s'affiche (clé `errors.<code>`) et la saisie est conservée

**Étant donné** l'appareil hors réseau
**Quand** le Collecteur touche « Déclarer »
**Alors** l'écran affiche « Pas de réseau : le lot n'est pas encore déclaré » et rien n'est mis en File hors-ligne

**Étant donné** l'écran « Mes Lots »
**Quand** il est ouvert
**Alors** chaque Lot affiche son badge de Type de déchet, son poids, sa Zone, sa date et son Statut de Lot (`disponible` ou `réservé`, pictogramme + libellé), et la liste se rafraîchit toutes les 15 s
**Et** un état vide invite à déclarer un premier Lot, les cibles tactiles mesurent au moins 44 px et aucun texte n'est en dur

**Exigences :** FR-38, UX-DR-33, UX-DR-3, UX-DR-7, UX-DR-8, UX-DR-9, NFR-4
**Porte :** Should, extension

### Story 9.3 : Consulter les Lots `disponible`

En tant que Recycleur,
Je veux consulter les Lots `disponible`, filtrés par Type de déchet, Zone et poids minimal,
Afin d'anticiper la matière que je peux acheter.

**Critères d'acceptation :**

**Étant donné** des Lots `disponible` et `réservé` de plusieurs Types de déchet, Zones et poids
**Quand** un Recycleur appelle `GET /v1/lots?waste_type=&zone_id=&min_weight_kg=`
**Alors** il ne reçoit que des Lots `disponible` correspondant à tous les filtres fournis, plus récents d'abord, paginés (`limit` ≤ 100)
**Et** avec `min_weight_kg=10`, un Lot de 9,99 kg est exclu et un Lot de 10 kg inclus

**Étant donné** n'importe quelle réponse de cette liste
**Quand** elle est sérialisée
**Alors** chaque élément porte l'identifiant du Lot, le Type de déchet, le poids, le nom de la Zone, la date, `is_demo` et une URL signée de 5 min vers la photo
**Et** aucun champ ne contient le numéro, le nom, l'identifiant ni une Position du Collecteur (test qui cherche ces valeurs dans la réponse brute)

**Étant donné** un Collecteur, un Citoyen ou un membre du Personnel
**Quand** il appelle cette route
**Alors** il reçoit 403 (test « route × rôle »)

**Étant donné** un Recycleur sur un écran de 390×844 ou de 1280×800
**Quand** il ouvre « Lots disponibles » [HORS MAQUETTE]
**Alors** il voit les Lots avec badge de Type de déchet, poids, Zone et photo, et des filtres Type de déchet, Zone et poids minimal
**Et** l'étiquette « Données de démonstration » marque les Lots `is_demo`, et l'écran est utilisable au clavier

**Exigences :** FR-39, AD-10, UX-DR-33, UX-DR-3, UX-DR-6, UX-DR-7, NFR-9
**Porte :** Should, extension

### Story 9.4 : Demander le contact du Collecteur d'un Lot

En tant que Recycleur,
Je veux obtenir le contact du Collecteur d'un Lot après en avoir fait la demande,
Afin de négocier directement, sans que les identités soient exposées à tous.

**Critères d'acceptation :**

**Étant donné** la base au schéma courant
**Quand** la migration Alembic de cette story s'applique
**Alors** la table `lot_requests` existe (`lot_id`, `recycler_user_id`, `created_at`, `is_demo`, `UNIQUE (lot_id, recycler_user_id)`), écrite par le seul module `lots`

**Étant donné** un Recycleur et un Lot `disponible`
**Quand** il appelle `POST /v1/lots/<id>/contact-requests` avec une `Idempotency-Key`
**Alors** il reçoit 201 avec le nom affiché et le numéro du Collecteur, obtenus par `auth.service.get_contact()`
**Et** une seconde demande du même Recycleur pour le même Lot renvoie 200 avec le même contact, sans seconde ligne
**Et** `GET /v1/lots/requests/mine` liste les demandes de ce seul Recycleur avec le Lot et le contact obtenu

**Étant donné** un Lot `réservé` ou inexistant
**Quand** un Recycleur demande le contact
**Alors** il reçoit respectivement 409 et 404, sans contact

**Étant donné** un contact fourni
**Quand** les autres réponses sont examinées
**Alors** le contact n'apparaît que dans la réponse de cette demande et dans `GET /v1/lots/requests/mine` du même Recycleur, jamais dans `GET /v1/lots`
**Et** les journaux `structlog` masquent le numéro (test de lecture des journaux)

**Étant donné** le détail d'un Lot sur l'écran du Recycleur
**Quand** il touche « Demander le contact » puis confirme
**Alors** le nom affiché et le numéro s'affichent avec un bouton « Appeler » (lien `tel:`)

**Étant donné** un Collecteur, un Citoyen ou un membre du Personnel
**Quand** il appelle ces routes
**Alors** il reçoit 403

**Exigences :** FR-39 (contact après demande), AD-10, AD-2, AD-5, NFR-14, UX-DR-33
**Porte :** Should, extension

### Story 9.5 : Réserver un Lot

En tant que Recycleur,
Je veux réserver un Lot `disponible`,
Afin de m'assurer qu'aucun autre Recycleur ne le prenne pendant que j'organise l'enlèvement.

**Critères d'acceptation :**

**Étant donné** la base au schéma courant
**Quand** la migration Alembic de cette story s'applique
**Alors** `material_lots` reçoit `reserved_by_user_id` et `reserved_at`, nuls tant que le Lot est `disponible`

**Étant donné** un Recycleur et un Lot `disponible`
**Quand** il appelle `POST /v1/lots/<id>/reservation` avec une `Idempotency-Key`
**Alors** le Lot passe à `réservé` par une mise à jour conditionnelle (`WHERE status = 'available'`), avec `reserved_at` = `core.clock.now()`
**Et** `LotReserved` est émis après le commit

**Étant donné** deux Recycleurs qui réservent le même Lot en parallèle (répété 20 fois)
**Quand** les requêtes aboutissent
**Alors** une seule réussit et l'autre reçoit 409
**Et** toute réservation d'un Lot déjà `réservé` reçoit 409, sauf le rejeu d'une même requête avec la même `Idempotency-Key`

**Étant donné** un Lot réservé
**Quand** un Recycleur appelle `GET /v1/lots`
**Alors** ce Lot n'y figure plus

**Étant donné** le Collecteur du Lot avec l'application ouverte sur « Mes Lots »
**Quand** la réservation est validée
**Alors** le Lot y apparaît `réservé` au plus 15 s après (rafraîchissement de 15 s, test à minuterie simulée)
**Et** la notification du Collecteur au MVP est cette apparition dans la liste en 15 s au plus ; aucune réaction n'est abonnée à `LotReserved`

**Étant donné** le détail d'un Lot `disponible` sur l'écran du Recycleur
**Quand** il touche « Réserver ce lot » puis confirme
**Alors** le Lot s'affiche `réservé` ; une réponse 409 affiche « Ce lot vient d'être réservé » et rafraîchit la liste

**Exigences :** FR-40, AD-5, AD-21, UX-DR-33, UX-DR-8
**Porte :** Could, extension
