# TerangaCycle AI — Cahier des charges

> Version du 9 novembre 2026. Partie fonctionnelle du dossier : vision, périmètre, exigences, planning, risques et pitch.
> La partie technique (architecture, données, API, IA, sécurité, infrastructure, frontend, CI/CD) se trouve dans [dossier-technique.md](dossier-technique.md).

## Sommaire

1. [Vision et proposition de valeur](#1-vision-et-proposition-de-valeur)
2. [Périmètre et acteurs](#2-périmètre-et-acteurs)
3. [Exigences fonctionnelles et user stories](#3-exigences-fonctionnelles-et-user-stories)
4. [Exigences non fonctionnelles](#4-exigences-non-fonctionnelles)
5. [Planning, équipe et feuille de route](#5-planning-équipe-et-feuille-de-route)
6. [Risques, indicateurs d'impact et pitch](#6-risques-indicateurs-dimpact-et-pitch)

---

## 1. Vision et proposition de valeur

TerangaCycle AI transforme un déchet signalé par un citoyen en ressource tracée, classée par IA et confiée au bon collecteur ou recycleur local, avec des données hébergées et gouvernées au Sénégal.

**Problème.** Les dépôts sauvages sont signalés de manière informelle (appels, réseaux sociaux), sans géolocalisation fiable ni suivi. Les récupérateurs informels et les petits recycleurs n'ont aucun outil pour savoir où se trouve la matière valorisable. Les communes manquent de données pour planifier les tournées.

**Thème du hackathon.** « Afrique Makers : l'innovation au service d'une souveraineté technologique durable et inclusive ». Le projet répond aux trois mots clés :

| Mot clé | Réponse concrète du produit |
|---|---|
| Souveraineté | Modèle IA open source embarqué, données hébergées localement, code sous licence ouverte, exportabilité complète |
| Durable | Économie circulaire : le déchet devient une matière valorisée, avec traçabilité et indicateurs d'impact (kg valorisés) |
| Inclusive | Wolof et français, mode hors-ligne, pictogrammes, canal SMS/WhatsApp, intégration des récupérateurs informels comme acteurs rémunérés |

**Chaîne de valeur.** Signaler → Classifier (IA) → Dispatcher → Collecter → Valoriser → Mesurer l'impact.

**Différenciation face aux apps de signalement existantes.**

- Le cœur n'est pas le signalement mais la valorisation : matching entre déchet, collecteur et recycleur.
- L'IA tourne sur l'appareil ou sur un petit serveur local, sans API cloud étrangère obligatoire.
- Les acteurs informels sont des utilisateurs de premier rang, pas des bénéficiaires passifs.
- Les données sont ouvertes aux communes sous forme agrégée et anonymisée (tableau de bord, export).

## 2. Périmètre et acteurs

Le MVP de 72 h couvre la boucle complète signaler → classer → collecter → mesurer ; la place de marché, le wolof complet et les paiements sont des extensions.

### Acteurs

| Acteur | Objectif | Appareil principal | Besoin clé |
|---|---|---|---|
| Citoyen | Signaler un dépôt en moins de 30 s | Smartphone Android d'entrée de gamme | Pas de saisie longue, fonctionne sans réseau |
| Collecteur / récupérateur | Trouver des missions proches et valorisables | Smartphone, données mobiles limitées | Liste simple, itinéraire, preuve de collecte par photo |
| Recycleur | Voir l'offre de matière par type et zone | Navigateur sur ordinateur ou mobile | Volumes estimés, contact collecteur |
| Administrateur (commune, UCG) | Piloter, prioriser, rendre compte | Navigateur sur ordinateur | Carte de chaleur, délais, export |
| Modérateur | Valider les signalements douteux | Navigateur | File de modération, anti-spam |

### MVP (obligatoire pour la démo)

1. Signalement avec photo, GPS automatique et commentaire.
2. Classification IA avec score de confiance, corrigeable par l'utilisateur.
3. Carte des signalements et carte de chaleur.
4. Vue collecteur : missions proches, acceptation, changement de statut, preuve photo.
5. Tableau de bord administrateur : volumes, répartition par type, délai moyen, zones prioritaires.
6. Mode hors-ligne du signalement (file d'attente et synchronisation).

Socle transverse du MVP : connexion par code à usage unique, file de modération, gestion des comptes collecteurs et suppression des données personnelles (US-19 à US-22).

### Extensions si le temps le permet

- Place de marché simplifiée : le collecteur déclare un poids, le recycleur voit une offre.
- Points citoyens et classement par quartier.
- Interface en wolof (au moins l'écran de signalement).
- Canal WhatsApp ou SMS pour déclarer un dépôt.

### Hors périmètre de 72 h

Paiement mobile réel, applications natives iOS et Android, entraînement d'un modèle de zéro, authentification fédérée complexe, optimisation de tournées multi-véhicules.

## 3. Exigences fonctionnelles et user stories

22 user stories couvrent les 5 acteurs ; les 15 marquées **Must** forment le MVP de 72 h. Priorités : Must (démo), Should (si le temps le permet), Could (après le hackathon).

### Citoyen

| ID | Story | Critères d'acceptation | Prio |
|---|---|---|---|
| US-01 | En tant que citoyen, je veux signaler un dépôt avec une photo, afin qu'il soit pris en charge | Photo obligatoire, GPS capturé automatiquement, commentaire optionnel (280 car. max), accusé de réception avec numéro de suivi | Must |
| US-02 | En tant que citoyen, je veux que l'app propose le type de déchet, afin de gagner du temps | Classification affichée sous 3 s avec score de confiance ; si confiance sous 60 %, l'app demande de choisir le type | Must |
| US-03 | En tant que citoyen, je veux corriger la classification, afin d'améliorer la précision | Choix parmi 5 classes en un tap ; la correction est enregistrée pour le réentraînement | Must |
| US-04 | En tant que citoyen, je veux signaler sans réseau, afin de ne pas perdre mon signalement | Signalement mis en file locale, badge « en attente », envoi automatique au retour du réseau, sans doublon | Must |
| US-05 | En tant que citoyen, je veux suivre l'état de mon signalement, afin de savoir s'il a été traité | Statuts visibles : signalé, validé, assigné, collecté, rejeté ; notification à chaque changement | Must |
| US-06 | En tant que citoyen, je veux utiliser l'app en wolof, afin de la comprendre | Sélecteur de langue ; écran de signalement traduit ; pictogrammes pour les types de déchets | Should |
| US-07 | En tant que citoyen, je veux gagner des points, afin d'être encouragé | Points attribués à la collecte confirmée ; classement par quartier | Could |

### Collecteur / récupérateur

| ID | Story | Critères d'acceptation | Prio |
|---|---|---|---|
| US-08 | En tant que collecteur, je veux voir les missions proches, afin d'optimiser mes déplacements | Liste triée par distance dans un rayon réglable (1 à 10 km), type et photo visibles | Must |
| US-09 | En tant que collecteur, je veux accepter une mission, afin de la réserver | Une mission ne peut être acceptée que par un seul collecteur ; conflit géré (réponse 409) | Must |
| US-10 | En tant que collecteur, je veux prouver la collecte par une photo, afin de la valider | Photo avant/après, poids estimé saisi (kg), statut passe à « collecté » | Must |
| US-11 | En tant que collecteur, je veux voir l'itinéraire, afin de m'y rendre | Lien vers l'application de cartes du téléphone avec les coordonnées | Should |
| US-12 | En tant que collecteur, je veux déclarer un lot de matière, afin de le proposer aux recycleurs | Lot avec type, poids, zone, photo ; visible par les recycleurs | Should |

### Recycleur

| ID | Story | Critères d'acceptation | Prio |
|---|---|---|---|
| US-13 | En tant que recycleur, je veux voir les lots disponibles par type et zone, afin de planifier mes achats | Filtres type, zone, poids minimal ; contact du collecteur après demande | Should |
| US-14 | En tant que recycleur, je veux réserver un lot, afin de le sécuriser | Statut du lot « réservé », collecteur notifié | Could |

### Administrateur et modérateur

| ID | Story | Critères d'acceptation | Prio |
|---|---|---|---|
| US-15 | En tant qu'administrateur, je veux une carte de chaleur des dépôts, afin d'identifier les zones prioritaires | Heatmap filtrable par période, type et statut ; affichage sous 2 s pour 5 000 points | Must |
| US-16 | En tant qu'administrateur, je veux des indicateurs clés, afin de rendre compte | Nombre de signalements, répartition par type, délai moyen de traitement, kg collectés | Must |
| US-17 | En tant qu'administrateur, je veux exporter les données, afin de les réutiliser | Export CSV et GeoJSON, données agrégées sans information personnelle | Must |
| US-18 | En tant qu'administrateur, je veux assigner une mission à un collecteur, afin de traiter les cas urgents | Assignation manuelle depuis la carte ; collecteur notifié | Should |
| US-19 | En tant que modérateur, je veux valider ou rejeter un signalement, afin de limiter le spam | File de modération ; motif de rejet obligatoire ; action journalisée | Must |
| US-20 | En tant qu'administrateur, je veux gérer les comptes collecteurs, afin de les vérifier | Création, suspension, vérification d'un compte ; journal d'audit | Must |

### Transverses

| ID | Story | Critères d'acceptation | Prio |
|---|---|---|---|
| US-21 | En tant qu'utilisateur, je veux me connecter simplement, afin d'accéder à mon espace | Connexion par numéro de téléphone et code à usage unique ; signalement anonyme possible avec limite de débit | Must |
| US-22 | En tant qu'utilisateur, je veux gérer mes données personnelles, afin de garder le contrôle | Suppression du compte et des données associées sur demande ; consentement à la géolocalisation affiché | Must |

## 4. Exigences non fonctionnelles

Chaque exigence a une cible mesurable, vérifiable pendant la démo ou par un test automatisé. Les valeurs sont des objectifs de conception pour le MVP, à valider par mesure.

| ID | Catégorie | Exigence | Cible | Vérification |
|---|---|---|---|---|
| NF-01 | Performance | Classification d'une photo | Moins de 3 s sur smartphone milieu de gamme | Chronométrage sur 20 photos |
| NF-02 | Performance | Temps de réponse API en lecture | p95 sous 300 ms à 50 requêtes/s | Test de charge (k6) |
| NF-03 | Performance | Affichage de la carte | Moins de 2 s pour 5 000 points (clustering) | Test manuel et Lighthouse |
| NF-04 | Réseau faible | Poids d'un signalement | Image compressée à 300 Ko ou moins | Contrôle automatique |
| NF-05 | Réseau faible | Poids de la page d'accueil | 500 Ko ou moins hors images | Lighthouse |
| NF-06 | Hors-ligne | Création d'un signalement sans réseau | 100 % des champs saisis conservés, envoi au retour du réseau | Test en mode avion |
| NF-07 | Disponibilité | Disponibilité du service | 99 % visé pour la démo, sauvegardes quotidiennes | Supervision |
| NF-08 | Sécurité | Chiffrement | TLS 1.2 minimum en transit, chiffrement au repos | Scan SSL, configuration |
| NF-09 | Sécurité | Contrôle d'accès | Aucune route sensible sans jeton valide et rôle adéquat | Tests d'autorisation |
| NF-10 | Vie privée | Données personnelles | Pas de visage ni de plaque conservés ; position arrondie dans les exports | Revue et test |
| NF-11 | Souveraineté | Dépendances | Aucune API d'IA étrangère obligatoire ; données exportables en CSV/GeoJSON | Revue d'architecture |
| NF-12 | Accessibilité | Lisibilité | Contraste AA, cibles tactiles de 44 px, pictogrammes | Audit Lighthouse |
| NF-13 | Compatibilité | Appareils | Android 8+ avec Chrome, 2 Go de RAM | Test sur appareil réel |
| NF-14 | Maintenabilité | Qualité du code | Couverture de tests de 60 % sur le backend, lint sans erreur | CI |
| NF-15 | Ouverture | Licence | Code sous licence ouverte (MIT ou AGPL-3.0), documentation du modèle | Dépôt |

## 5. Planning, équipe et feuille de route

Le plan de 72 h gèle le code à H60 pour garder 12 h de répétition et de marge ; trois personnes se répartissent le socle, l'IA et le pitch, avec un critère de passage à H24, H48 et H60.

Chaque étape se termine par un critère de passage ; s'il n'est pas atteint, on coupe une extension (place de marché, wolof) plutôt que de repousser la suite.

### Répartition des rôles (3 personnes maximum, dont un développeur et un spécialiste de la thématique)

| Rôle | Profil | Responsabilités | Livrables |
|---|---|---|---|
| Fullstack | Développeur(se) | API, base de données, PWA, déploiement, intégration du modèle | Application déployée, dépôt, tests de bout en bout |
| Données et IA | Spécialiste données, IA ou environnement (le profil « souveraineté » exigé par le règlement) | Jeu de photos locales, modèle, évaluation, fiche du modèle, indicateurs d'impact | Modèle ONNX, chiffres d'évaluation, model card |
| Design et pitch | Design, communication ou terrain | Maquettes, identité visuelle, données de démo, pitch, contact avec un collecteur ou une commune | Interface, pitch de 5 minutes, vidéo de secours |

### Avant le hackathon (du 9 au 22 novembre 2026)

Vérifier d'abord avec les organisateurs ce qui peut être préparé à l'avance (données, modèle, squelette de code) : si le règlement impose de tout écrire pendant les 72 h, ne préparer que les données et la maquette.

| Échéance | Action |
|---|---|
| 12 novembre | Confirmer l'inscription et la composition de l'équipe auprès de l'organisation (la date limite du formulaire était le 7 octobre) |
| 16 novembre | Premier jeu de photos locales étiqueté ; modèle de base entraîné et évalué |
| 19 novembre | Dépôt créé, CI en place, `docker compose up` fonctionnel, schéma de base appliqué |
| 21 novembre | Parcours de signalement maquetté ; un collecteur ou une commune contacté pour un témoignage |
| 22 novembre | Répétition du pitch avec une démo de secours en vidéo |

### Feuille de route après le hackathon

| Phase | Durée indicative | Contenu | Critère de réussite |
|---|---|---|---|
| 1. Pilote terrain | 4 à 6 semaines | Un quartier ou une commune, 10 à 20 collecteurs, mesure de la précision réelle | Au moins 80 % des signalements validés traités |
| 2. Consolidation | 2 à 3 mois | Wolof complet, canal WhatsApp ou SMS, place de marché, réentraînement avec les corrections | F1 macro stable sur photos du pilote |
| 3. Partenariats | 3 à 6 mois | Convention avec une commune ou un opérateur de collecte, tableau de bord officiel | Un partenaire institutionnel signé |
| 4. Passage à l'échelle | 6 mois et plus | Plusieurs villes, hébergement local, modèle économique (abonnement des communes, commission sur la valorisation) | Équilibre financier du pilote étendu |

## 6. Risques, indicateurs d'impact et pitch

Les trois risques qui peuvent faire perdre la démo sont un modèle trop imprécis sur des photos locales, un réseau instable dans la salle et un périmètre trop large ; chacun a un plan B décidé à l'avance.

### Risques et plans B

| Risque | Probabilité | Impact | Prévention | Plan B |
|---|---|---|---|---|
| Modèle imprécis sur photos de Dakar | Moyenne | Élevé | Photos locales dans l'entraînement, seuil de confiance, correction manuelle | Démo avec 10 photos préparées et la correction en direct comme fonctionnalité |
| Réseau instable pendant la démo | Élevée | Élevé | Modèle dans le navigateur, hors-ligne, serveur local sur place | Vidéo de la démo complète, ordinateur portable servant de serveur |
| Périmètre trop large | Élevée | Moyen | MVP figé à H0, extensions seulement après le gate H48 | Couper la place de marché et le wolof, garder la boucle complète |
| Inscription non confirmée | À vérifier | Élevé | Écrire à contact@makeafrica.tech dès maintenant | Présenter le projet dans un autre concours, le dossier reste valable |
| Équipe incomplète (3 personnes dont développeur et spécialiste) | Moyenne | Élevé | Confirmer les deux autres membres cette semaine | Demander à l'organisation l'appui d'un profil manquant |
| Fraude ou abus pendant la démo publique | Faible | Moyen | Limites de débit, modération | Passer en mode démo avec comptes de test |
| Dépendance à un service externe (SMS, tuiles) | Moyenne | Moyen | Simuler l'OTP en démo, tuiles mises en cache | Code OTP affiché en mode démonstration uniquement |
| Épuisement de l'équipe | Moyenne | Moyen | Sommeil par relais, gel du code à H60 | Réduire le périmètre plutôt que les heures de repos |

### Indicateurs d'impact à montrer au jury

| Indicateur | Définition | Source |
|---|---|---|
| Kilogrammes valorisés | Somme des poids collectés confirmés par preuve photo | `missions.collected_weight_kg` |
| Délai de traitement | Médiane du temps entre signalement et collecte | `reports`, `missions` |
| Taux de traitement | Part des signalements validés qui sont collectés | `reports.status` |
| Zones identifiées | Nombre de cellules de la carte de chaleur au-dessus d'un seuil | PostGIS |
| Acteurs informels intégrés | Collecteurs vérifiés actifs | `collector_profiles` |
| Précision du modèle | F1 macro sur le jeu de test local | Évaluation (dossier technique §4) |
| Part corrigée par les utilisateurs | Classifications corrigées sur le total | `classifications` |

> Dans la démo, ne montrer que des chiffres réels ou clairement étiquetés « données de démonstration » ; un chiffre inventé présenté comme réel est le moyen le plus sûr de perdre la confiance du jury.

### Structure d'un pitch de 5 minutes

| Temps | Contenu | Preuve à montrer |
|---|---|---|
| 0:00 à 0:40 | Le problème : un dépôt sauvage, aucune donnée, aucune valorisation | Une photo prise à Dakar |
| 0:40 à 1:20 | La solution et le lien avec la souveraineté technologique durable et inclusive | Chaîne de valeur en une phrase |
| 1:20 à 3:20 | Démo en direct : signalement en mode avion, classification, carte, mission, collecte, tableau de bord | Parcours réel de bout en bout |
| 3:20 à 4:00 | Pourquoi c'est souverain : modèle ouvert, données portables, plan de sortie | Schéma d'architecture |
| 4:00 à 4:40 | Impact et modèle de pérennité : communes, valorisation, partenaires | Indicateurs, témoignage d'un acteur de terrain |
| 4:40 à 5:00 | La demande : pilote dans un quartier | Un appel à l'action précis |

### Questions probables du jury

| Question | Réponse à préparer |
|---|---|
| En quoi est-ce souverain si c'est sur AWS ? | Reconnaître la limite, montrer la portabilité : PostgreSQL, S3-compatible, conteneurs, modèle ONNX possédé, clés contrôlées, plan de sortie testé |
| Quelle est la précision de l'IA ? | Donner le F1 mesuré sur photos locales et la matrice de confusion, expliquer le seuil de 60 % et la correction manuelle |
| Existe-t-il déjà des applications de ce type ? | Citer celles que vous avez réellement testées, présenter TerangaCycle comme complémentaire (valorisation et acteurs informels) plutôt que concurrente |
| Comment financer le projet ? | Abonnement des communes pour le tableau de bord, commission sur les lots valorisés, subventions et programmes d'innovation |
| Et la vie privée ? | Consentement, minimisation, position arrondie en export, suppression sur demande, référence à la loi sénégalaise et à la CDP |
| Qui utilisera réellement l'application ? | Citer le collecteur ou la commune contacté, le plan de pilote dans un quartier |
| Que se passe-t-il sans smartphone ni réseau ? | PWA hors-ligne, canal SMS ou WhatsApp en extension, collecteurs comme relais |
