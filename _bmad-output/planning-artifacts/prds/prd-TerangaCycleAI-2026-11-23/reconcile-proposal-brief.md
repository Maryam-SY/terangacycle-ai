---
title: "Réconciliation — Project Proposal + Handoff brief ↔ PRD TerangaCycle AI"
created: 2026-11-23
status: à arbitrer par Mia
scope: lecture seule ; prd.md et addendum.md non modifiés
---

# Réconciliation : Project Proposal et Handoff brief ↔ PRD

## 0. Sources et méthode

| Source | Statut | Lecture |
|---|---|---|
| `TerangaCycle_AI_Project_Proposal.pdf` (11 p., anglais) | **Déjà remis au jury** : chaque écart est une promesse publique | Texte intégral + contrôle visuel des p. 8-9 (écrans Figma 1-7) |
| `TerangaCycle AI – Handoff brief for Claude Code.pdf` (9 p.) | Décisions arrêtées de l'équipe (§3 « ne pas rouvrir sans Mia ») | Texte intégral + contrôle visuel des tableaux §3 et §6 |
| `prd.md`, `addendum.md`, `.memlog.md` | Brouillon PRD + décisions journalisées | Intégral |

Décisions journalisées prises comme acquises (`.memlog.md`, validées par Mia) : MobileNetV3-Large par défaut, F1 macro principal, rayon 5 km réglable 1-10, pilote 60 % sur 6 mois, pitch 1 min 30, Docker Compose en fin de hackathon, vert `#187A50`, Lots après H48. Elles ne sont signalées ici que si elles **contredisent le Proposal** (§5).

Gravité : **B** = bloquant (promesse jury non tenue ou règle du brief inversée) ; **M** = majeur (perte partielle, ambiguïté qui changera le code) ; **m** = mineur (formulation, traçabilité).

## 1. Synthèse — écarts principaux

1. **[B] « Configuration per commune (zones, waste types, moderators) »** (Proposal §3, argument « Built to be replicated ») : aucune FR, aucun non-objectif, aucune entité « commune » dans le modèle. Promesse de réplicabilité muette dans le PRD.
2. **[B] « Duplicate detection by distance and time »** (Proposal §10, risques) : le PRD ne détecte que les photos *strictement identiques* (FR-8). La mitigation annoncée au jury contre les faux signalements n'existe pas.
3. **[B] « Audit trail of every status change »** (Proposal §5, §6) : le Journal d'audit du PRD couvre les « actions sensibles » (modération FR-23, comptes FR-35) mais pas les transitions `validé→assigné`, `assigné→validé`, `assigné→collecté` ; et sa consultation (FR-36) est hors MVP.
4. **[M] Historique du Collecteur (FR-30) sorti du MVP** sans décision journalisée, alors que c'est une fonctionnalité principale du Proposal (§5) et le cœur du pilier « Inclusive » (« verifiable record of their work » pour les informels).
5. **[M] Règle du brief « le résultat serveur fait foi » modifiée** : FR-14 place la Correction humaine (saisie côté client) au-dessus de la Classification serveur, sans drapeau quand le choix du Citoyen diffère du serveur. La garantie « résultat non falsifiable » du brief §5 est perdue.
6. **[M] Porte H24 : « premier modèle entraîné exporté en ONNX »** (Proposal §10, brief §7) remplacé par un Modèle factice dans le PRD (§9.1), sans décision journalisée.
7. **[M] Taille de tas absente de la maquette Figma** (écran 3) alors que le PRD l'exige au même écran (UJ-1, FR-7) et que le Poids estimé « par mission » promis au jury en dépend ; la maquette est figée (quota Figma, brief §9).

Décisions journalisées à **expliquer à l'oral ou corriger dans le PDF** : MobileNetV3-Large (le PDF dit Small), F1 macro (le PDF promet top-1 ≥ 80 %), Docker Compose (le PDF dit « deployment on AWS » en fin de hackathon), vert `#187A50` (la maquette montrée au jury garde `#1F8A5B`). Détail au §5.

## 2. (a) Promesses du Proposal au jury

| # | Promesse (réf. Proposal) | Ce que fait le PRD / addendum | Écart | Grav. | Action proposée |
|---|---|---|---|---|---|
| A1 | Configuration par commune : zones, types de déchets, modérateurs (§3 « Built to be replicated ») ; « one commune… designed for replication » (§1) | Zone = découpage admin (glossaire). 5 types figés (Modèle). Aucun rattachement Personnel ↔ commune ; aucune table `communes` (brief §4 : 11 tables, pas de commune). Rien en §8 Non-objectifs | Promesse ni livrée ni écartée | **B** | Ajouter une FR minimale « Commune » : entité commune, Zones rattachées, Personnel limité à sa commune (cloisonnement des données et du Tableau de bord), libellés/couleurs des types configurables (pas les classes du Modèle). Sinon, non-objectif explicite + phrase orale « mono-commune au MVP, multi-commune au pilote » |
| A2 | « Duplicate detection by distance and time » (§10, risques) | FR-8 : doublon = photo strictement identique ; §6.2 « détection de doublons » sans définition ; `photo_duplicate_of` seulement (addendum B2) | Doublon spatio-temporel absent | **B** | FR : drapeau « doublon probable » si un Signalement non terminal existe à moins de X m (ex. 50 m) et depuis moins de Y h (ex. 72 h), affiché dans la File de modération (FR-22) ; requête PostGIS. Paramètres `[ASSUMPTION]` |
| A3 | « Audit trail of status changes » (§5) / « of every status change » (§6) | Journal d'audit = « actions sensibles » ; tracé : modération (FR-23), comptes (FR-35). FR-36 (consultation) hors MVP (§9.2) | Acceptation, annulation, Preuve, assignation manuelle non tracées ; journal invisible en démo | **B** | Conséquence transverse : **toute transition de Statut** (et de Mission) écrit au Journal d'audit (acteur, avant/après, horodatage serveur). Remonter FR-36 au MVP ou au moins une vue lecture seule de l'historique d'un Signalement |
| A4 | « Estimated weight and AI confidence per mission » (§5, §8 écran 5 : « ≈ 15 kg estimés », « Confiance IA 87 % ») | FR-24 affiche Poids estimé et « la confiance » | (i) la table Taille de tas → poids est une question ouverte (Q6) sans responsable ni porte ; (ii) « quelle confiance ? » (locale, serveur, ou aucune si Correction) non défini ; (iii) Taille de tas absente de l'écran 3 Figma | **M** | Table par défaut `[ASSUMPTION]` livrée à H24 avec FR-7 ; préciser « confiance = Classification serveur ; si Correction, afficher “type confirmé par un humain” » ; ajouter la Taille de tas à l'écran 3 dans la spec UX (Figma non modifiable) |
| A5 | « Personal history of completed missions » (§5) ; « verifiable record of their work » (§1, §8) ; pilote « active collectors with a verified history » (§9) | FR-30 hors MVP (« seulement si H48 en avance ») | Fonctionnalité principale annoncée, non livrée, sans décision journalisée | **M** | Remonter FR-30 en H60 (c'est une simple requête sur les Missions terminées) ou journaliser la décision et préparer la phrase orale |
| A6 | Modération des « low-confidence and flagged reports » (§3 schéma) ; « moderators confirm flagged cases » (§6) | Tous les Signalements passent en modération (conforme au brief §4) ; FR-22 drapeaux = Désaccord IA + doublon ; FR-13 « plus tard le Modérateur » peut corriger | (i) pas de drapeau « confiance < 60 % / type choisi par le Citoyen » ; (ii) la correction par le Modérateur est renvoyée à « plus tard » : un Désaccord IA ne peut donc pas être tranché | **M** | Drapeau « faible confiance » dans FR-22 ; Correction par le Modérateur **dans** FR-23 (H48). À l'oral : « tout est modéré, les cas douteux sont signalés en tête » |
| A7 | « Kilograms by material » (§1 Sustainable, §3 scénario étape 6) ; indicateur pilote « Kilograms collected with photo proof — tracked by material » (§9) | FR-31 : kg valorisés **totaux** ; répartition par type = en nombre de Signalements. SM-5…SM-8 n'incluent pas cet indicateur | Indicateur pilote du Proposal perdu ; kg par matière non livrés | **M** | FR-31 : kg mesurés par Type de déchet ; ajouter un SM pilote « kg collectés avec Preuve, par matière (suivi, pas de cible) » |
| A8 | « Visible follow-up on every report » (§4) ; numéro de suivi + frise (§3) | Signalement anonyme autorisé (FR-7) ; FR-20 « liste de ses Signalements » ; FR-21 notifications pour connectés seulement ; FR-3 « un Citoyen ne voit que ses propres Signalements » | Mécanisme de suivi pour un **anonyme** non spécifié (liste locale sur l'appareil ? recherche par Numéro de suivi ?). Une recherche publique par `TC-AAAA-NNNNNN` séquentiel exposerait tous les Signalements (énumération) | **M** | Préciser : suivi anonyme = Signalements mémorisés sur l'appareil + lecture par Identifiant client lié à l'appareil ; jamais de consultation par Numéro de suivi seul |
| A9 | Minimisation : « phone number for login, position of the report » (§6) | §6.1 ajoute IP, nom affiché, empreinte d'appareil (addendum B2), et omet la **Position du Collecteur** et les photos de Preuve | Données personnelles au-delà de la promesse, dont une (géolocalisation d'un travailleur) non listée | **m** | Compléter §6.1 (Position du Collecteur, durée de conservation) ; justifier les ajouts par la sécurité dans le dossier CDP |
| A10 | « Every correction becomes a training example » (§3, §6) | FR-4 `[ASSUMPTION]` : refus possible de l'usage pour le réentraînement | Nuance légitime mais contraire à la formulation | **m** | Garder la règle (meilleure pour la conformité) ; dire à l'oral « chaque correction consentie » |
| A11 | « Data belongs to the commune and can leave AWS… documented exit plan » (§1, §6) | §6.4 : données exportables, plan de sortie documenté ; aucune FR, aucune porte. FR-33 = export **agrégé** anonymisé seulement | Pas d'export complet pour la commune (réversibilité) ni de livrable « plan de sortie » | **m** | Livrable pilote : procédure de sauvegarde/restauration complète (PostgreSQL + objets) + plan de sortie ; le mentionner en §9 ou §11 |
| A12 | « Open-source stack », « reusable open platform » (§1, §9) | Licence MIT/AGPL ouverte « avant le pilote » (Q2) | Dépôt public pendant le hackathon sans licence = pas open source juridiquement | **m** | Trancher la licence avant la démo (ou poser un `LICENSE` provisoire) |
| A13 | Rôles : citizen, collector, moderator, commune admin (§5) | + Recycleur | Extension, sans conflit | — | RAS |
| A14 | Statuts « reported, validated, assigned, collected » (§3) | `en attente de modération`, `validé`, `assigné`, `collecté`, `rejeté` | Libellé seulement ; l'écran 4 Figma affiche « Signalé / Validé par la modération / Assigné à un collecteur / Collecté, preuve photo » | **m** | Fixer les libellés UI sur la maquette, garder le glossaire pour le code |
| A15 | Pilote « share of reports validated **and** collected ≥ 60 % » (§9) | SM-6 : 60 % des Signalements `validé` passent à `collecté` | Dénominateur différent (tous les Signalements vs validés) | **m** | Garder SM-6 (cohérent avec « Taux de traitement » de l'écran 7) mais l'énoncer ainsi à l'oral |
| A16 | Feuille de route : SMS/WhatsApp et marketplace en **mois 6-12** ; Wolof en mois 3-6 (§10) | §9.2 : « Wolof, SMS, WhatsApp : feuille de route du pilote » | SMS/WhatsApp avancés au pilote par rapport au PDF | **m** | Aligner §9.2 sur le Proposal (SMS/WhatsApp = mois 6-12) |
| A17 | « Collector payment tracking », « API integration with municipal systems » (§5, après hackathon) | Paiement réel en non-objectif ; intégration SI municipal absente | Roadmap seulement | **m** | Citer en §9.2 pour traçabilité |

Promesses **tenues** (contrôlées) : photo + GPS < 30 s, IA locale + confiance + correction, seuil 60 %, reclassement serveur, File hors-ligne IndexedDB, Numéro de suivi, carte + liste des missions (5 km), Preuve (photos, poids, 150 m), 4 indicateurs, carte de chaleur, export CSV, OTP + rôles, URL signées, JWT courts, limitation de débit, pas d'API d'IA étrangère, indicateurs annoncés comme objectifs.

## 3. (b) Décisions du Handoff brief

### 3.1 Tableau §3 « Décisions déjà prises »

| Décision du brief | PRD / addendum | Écart | Grav. |
|---|---|---|---|
| Stade présenté : Figma + conception, sans logiciel ; lien de démo = Figma | Q7 (partage Figma) | Conforme | — |
| Monolithe modulaire (7 modules) | Addendum A | Conforme | — |
| IA 5 classes, ONNX navigateur puis serveur **qui fait foi**, pas d'API hébergée | FR-11, FR-14, §6.4 | FR-14 fait passer la Correction humaine (côté client) avant le serveur ; aucun drapeau si le choix du Citoyen ≠ serveur | **M** — voir B1 |
| Poids estimé : table petit/moyen/grand, sans IA | Glossaire, §8, addendum B7 | Conforme ; valeurs non fixées (Q6) | m |
| Temps réel : 15 s + Web Push, pas de WebSocket | FR-20, FR-21, §8 | Conforme | — |
| Hébergement : Compose hackathon, AWS pilote, plan de sortie | Addendum A | Conforme | — |
| Maquettes faites avec Figma (pas le type Design) | §7 | Conforme ; mais voir 3.4 (maquette figée) | — |
| Données de démo toujours étiquetées « Données de démonstration » | FR-37, §7 | Conforme | — |

**B1 [M] — Autorité du résultat serveur.** Le brief (§4, §5) dit « le résultat serveur fait foi » et « résultat enregistré non falsifiable ». Le PRD retient « Correction humaine, sinon Classification serveur » (FR-14) et ne définit le Désaccord IA que local ↔ serveur. Un Citoyen (ou un client modifié) peut donc imposer un type sans que la modération le voie. Proposition : le Type retenu avant modération = Classification serveur ; le choix du Citoyen est conservé comme Correction **proposée** et déclenche un drapeau s'il diffère ; seul le Modérateur fixe le type final (ce qui reste cohérent avec « l'IA propose, l'humain confirme »). Décision à journaliser.

### 3.2 §4 Règles métier et données

| Règle / élément du brief | PRD | Écart | Grav. |
|---|---|---|---|
| Seuil 60 %, Preuve 150 m, rayon 5 km, idempotence, reclassement serveur | FR-12, FR-29, FR-24, FR-9, FR-14 | Conformes (rayon réglable : décision journalisée) | — |
| Machine à états (pending_review… terminaux) | Glossaire « Statut » | Conforme ; libellés FR | — |
| 11 tables dont `collector_profiles`, `lot_requests`, `notifications` | Addendum B (écarts) | Pas de table `communes` (voir A1) ; `weight_estimates`, `refresh_tokens` ajoutées (justifiées) | m |
| Module `notifications` : Web Push, **SMS**, messages internes | FR-21 : SMS en non-objectif | Cohérent avec le Proposal (SMS après hackathon) ; le module SMS ne sert qu'à l'OTP | — |
| Module `auth` porte le journal d'audit | FR-23, FR-35 | Couverture partielle (A3) | B |
| OpenAPI sur `/docs` | Addendum S11 : désactivé hors démo | Décision d'audit journalisée (S1-S12) | — |
| MinIO en local | Addendum C : « vérifier MinIO, ou Garage/SeaweedFS » | Possible changement de brique non journalisé ; à trancher avant H24 | m |

### 3.3 §5 Plan IA

| Élément du brief | PRD | Écart | Grav. |
|---|---|---|---|
| Porte H24 : « premier modèle exporté en ONNX » (aussi Proposal §10) | §9.1 H24 : FR-16 « avec un Modèle factice » | Objectif du volet IA d'Aissatou à H24 disparu ; le factice est un filet (brief §10 étape 5), pas la cible | **M** |
| Livrables IA : modèle ONNX, chiffres d'évaluation, **fiche du modèle**, indicateurs d'impact | Fiche citée pour les licences (§6.3), addendum D | Pas de livrable explicite ni de porte | m |
| Transfert d'apprentissage en deux phases ; augmentation lumière/encombrement (Proposal §6) | Absent (normal, c'est du « comment ») | À reporter dans l'addendum D | m |
| Chaque correction stockée dans `classifications` | FR-13 | Conforme | — |

### 3.4 §6 Interface, écrans Figma, nodes et jetons

| Élément du brief | PRD | Écart | Grav. |
|---|---|---|---|
| « Le frontend doit reproduire la maquette, pas la réinventer » | §7 « Référence visuelle » | Le PRD ajoute des éléments absents des 7 écrans : Taille de tas (écran 3), variante hors-ligne de l'écran 4 sans Numéro de suivi (UJ-1), consentement (FR-4), connexion OTP, File de modération (UJ-2), comptes et Journal d'audit, bandeau Mode démonstration, photo dans la liste des missions (FR-24). **Aucun écran de modération n'existe dans Figma** alors que UJ-2 est une étape clé de SM-1 | **M** |
| Maquette **non modifiable** (quota Figma Starter atteint, brief §9) | Non mentionné | Les écrans ajoutés et le vert corrigé devront être spécifiés hors Figma (spec UX en code, mêmes jetons) | **M** |
| Nodes : 1:2 Accueil, 1:39 Capture, 1:57 Résultat IA, 1:97 Confirmation, 2:2 Missions, 2:35 Preuve, 2:65 Tableau de bord | Clé de fichier seule | Nodes perdus pour l'aval (UX, stories) | m |
| Parcours reliés : Citoyen 1→2→3→4→1 ; Collecteur 1 ou 4→5→6→1 ; Commune 1→7→1 ; boutons « Je suis collecteur », « Espace commune », « Passer à l'espace collecteur » | Non repris | Entrées de rôle depuis l'Accueil à préserver (avec OTP en interstitiel) | m |
| Écran 5 : en-tête « Rayon 5 km · plastique et verre » (filtre par type) | FR-24 : pas de filtre par type | Filtre visible dans la maquette, absent des FR | m |
| Mobile 390×844, desktop 1280×800, Inter, français d'abord | NFR-6, NFR-13, §7 | Conforme | — |
| Jetons : Vert foncé `#0B3D2E`, Vert `#1F8A5B`, Jaune `#F2B705`, Menthe `#EAF3EC`, Encre `#14231C`, Gris `#5E7168`, Ligne `#D5E3D9`, Fond `#F6FAF7`, Ambre `#FFF4CC`/`#7A5C00`, Rouge `#D9482B` | §7 renvoie aux « jetons du brief » sans les lister ; seul le vert est corrigé | Autres contrastes non vérifiés (voir ci-dessous) | m |

Contrôle des contrastes (calcul WCAG) à reporter en NFR-12 :
- Blanc sur `#D9482B` (Rouge) = **4,28:1** : échoue pour du texte normal. Rouge réservé aux aplats (carte de chaleur, pastille métal) ou texte ≥ 18,66 px gras.
- Blanc sur `#F2B705` (Jaune) = 1,82:1 : texte du statut « en attente » obligatoirement en Encre (8,98:1).
- `#1F8A5B` en texte sur Menthe = 3,82:1 et sur Fond = 4,11:1 (liens « Espace commune », « Retour à l'accueil ») : la correction `#187A50` (4,70:1 et 5,06:1) doit aussi s'appliquer au texte vert, pas seulement aux boutons.
- Gris, Ambre, Encre, Vert foncé : conformes.

### 3.5 §7 Portes et §9 Précautions

| Élément du brief | PRD | Écart | Grav. |
|---|---|---|---|
| H24 : flux de signalement relié à la PWA (brief §10 étape 4 : PWA **avec la file Dexie**) | File hors-ligne (FR-17…19) à H60 | Le hors-ligne, démontré en direct (SM-1, SM-4) et pilier « Inclusive », est placé à la porte de gel : risque de démo. Le Proposal dit seulement « offline sync **tested** » à H60 | **M** |
| H60 : « tableau de bord branché sur de vraies données » | FR-31…33 à H60 + FR-37 | Conforme ; préciser que les données de la démo en direct et le jeu de démonstration sont tous deux étiquetés | m |
| §9.1 Modèle Large ou Small : « corriger le PDF si Mia garde Large » | Décision journalisée Large ; mais §11 Q1 le laisse **ouvert** | Incohérence interne ; correctif PDF non planifié | m (voir §5) |
| §9.2 Chiffres du PDF à aligner (60 %, 150 m, 5 km, 80 %) | Traités (SM-2, FR-24) | Conforme | — |
| §9.3 Partage Figma « Anyone with the link can view » | Q7 | Conforme ; ajouter le quota Figma | m |
| §9.4 Inscription et équipe de trois à confirmer | Q7 | Conforme | — |
| Contraintes : souveraineté, hors-ligne, l'IA propose / l'humain confirme, données minimales, URL signées, honnêteté | §1, §6, §7 | Conforme sauf B1 (autorité serveur) et A9 (minimisation) | — |

## 4. (c) Éléments qualitatifs

| Thème | Sources | PRD | Écart / proposition | Grav. |
|---|---|---|---|---|
| **Teranga** | Proposal §1 : nom = teranga (hospitalité, soin mutuel) + cycle (du signal à la valorisation, au lieu de déplacer le tas d'un coin de rue à l'autre) | Jamais mentionné | Ajouter une ligne en §1 et traduire la valeur dans le ton (§7) : remercier le Citoyen, ne jamais culpabiliser, nommer le Collecteur comme acteur reconnu | m |
| **Ton** | Brief : français d'abord, documents jury EN/FR | §7 : consignes courtes, pictogrammes, erreurs actionnables | Conforme ; ajouter la sobriété des messages d'échec de Preuve (« vous êtes à X m ») pour ne pas accuser un collecteur | m |
| **Honnêteté démo** | Proposal p. 8-9 : écrans et chiffres = données de démonstration ; §9 : objectifs, pas résultats. Brief §3, §9 | FR-37, §7, §10 | Conforme. Deux points : (i) libellé « **Kg valorisés** » = somme des poids **collectés**, pas valorisés (recyclés) : risque de surpromesse, préférer « kg collectés (preuve photo) » ou définir le terme à l'oral ; (ii) publier la top-1 accuracy face à la cible annoncée même si elle est sous 80 % | M |
| **Inclusion des informels** | Proposal §1, §4, §8 : missions géolocalisées et « verifiable record » pour les informels ; 20 collecteurs avec historique | Glossaire inclut les informels ; mais FR-30 (historique) hors MVP ; « Collecteur vérifié » validé par l'admin sans critère ni parcours de demande (FR-35 : l'admin crée le compte) | Préciser comment un informel **demande** un compte (auto-inscription en attente de vérification) et sur quels critères il est vérifié (pas de pièce d'identité obligatoire `[ASSUMPTION]`), sinon la vérification exclut ceux que le Proposal met en avant | M |
| **Validation terrain** | Proposal §2 : l'analyse « will be validated with communes and collectors during the pilot » ; acteurs cités = exemples | Q6 (table de poids auprès d'un collecteur) | Ajouter une hypothèse explicite : besoins collecteurs et commune non encore validés sur le terrain | m |

## 5. Décisions journalisées qui contredisent le Proposal remis au jury

| Décision (`.memlog.md`) | Ce que dit le Proposal | Traitement recommandé |
|---|---|---|
| **MobileNetV3-Large par défaut** | §6 : « MobileNetV3-Small fine-tuned on 5 classes » | Le brief §9 demande de **corriger le PDF**. Si le PDF ne peut plus être redéposé : phrase orale « Large par défaut, Small si la latence dépasse 3 s sur un Android 2 Go ; mesure à H24 ». Fermer aussi la Q1 du PRD (§11), restée ouverte |
| **F1 macro ≥ 0,80 comme métrique principale** | §9 : « Top-1 accuracy of at least 80 % on 5 classes » | Explication orale obligatoire (classes déséquilibrées) ; publier **les deux** chiffres et dire honnêtement si la top-1 promise est atteinte ou non. Pas de correctif PDF nécessaire si le chiffre promis est aussi publié |
| **Docker Compose en fin de hackathon** | §10 : « Final hours: deployment on AWS » ; §7 : Ahmadou « deployment on AWS » ; §6 « AWS for the pilot » | Explication orale : « portable d'abord, AWS au pilote » (cohérent avec la souveraineté). Correctif PDF facultatif |
| **Vert `#187A50`** | Captures Figma (p. 8-9) en `#1F8A5B` ; maquette non modifiable | Écart visuel entre la démo et la maquette montrée au jury : l'annoncer comme correction d'accessibilité (WCAG AA) |
| Rayon 5 km réglable 1-10 | §5 : « radius 5 km » | Compatible (5 km par défaut) ; rien à corriger |
| Pilote 60 % sur 6 mois | §9 : 60 %, 6 mois | Conforme ; seul le dénominateur est à préciser (A15) |
| Pitch 1 min 30 | Non mentionné | Pas de conflit |
| Lots après H48 | §5 et §10 : marketplace **après** le hackathon | Pas de conflit avec le jury ; la `[NOTE FOR PM]` du §9.2 surestime le décalage : le Proposal ne promet pas de Lots pendant la démo |

Écarts **non journalisés** qui contredisent aussi le Proposal et exigent soit une décision, soit une explication orale : A1 (configuration par commune), A2 (doublons distance/temps), A3 (audit de chaque changement), A5 (historique collecteur), modèle factice à H24 (§3.3).

## 6. Incohérences internes du PRD (relevées en passant)

- §11 Q1 (Large ou Small) encore ouverte alors que la décision est prise (`.memlog.md`, dernière ligne).
- §12 classe en « hypothèses » les six choix a-f et le vert, validés par Mia : à déplacer en « décisions » ; §6.3 garde `[ASSUMPTION : validation de Mia]` sur le vert.
- §2.3 annonce que les numéros d'écran renvoient à la maquette, mais UJ-2, UJ-5 et la connexion OTP n'ont pas d'écran.
- FR-13 « plus tard le Modérateur » : « plus tard » n'est rattaché à aucune porte.

## 7. Actions proposées (à arbitrer ; aucune appliquée)

| Priorité | Action | Fichier cible |
|---|---|---|
| 1 | Décider A1 (FR « Commune » minimale ou non-objectif assumé) et le journaliser | prd.md §4, §8 ; .memlog.md |
| 2 | FR doublon spatio-temporel (A2) dans la File de modération | prd.md FR-22, §6.2 ; addendum B |
| 3 | Journal d'audit = toute transition de Statut et de Mission ; vue d'historique d'un Signalement au MVP (A3) | prd.md glossaire, FR-23…29, §9.1 |
| 4 | Trancher B1 (autorité serveur vs Correction citoyenne) | prd.md FR-14, FR-15, FR-22 |
| 5 | Remonter FR-30 en H60 ou journaliser son report (A5) | prd.md §9 |
| 6 | Porte H24 : « premier modèle entraîné exporté », factice en repli ; File hors-ligne amorcée dès H24 | prd.md §9.1 |
| 7 | Spec UX des écrans hors Figma (Taille de tas, modération, OTP, consentement, variante hors-ligne écran 4) + nodes + contrastes Rouge/Jaune/texte vert | prd.md §7 ; spec UX |
| 8 | Kg par matière (A7), suivi anonyme (A8), libellé « kg valorisés », parcours d'inscription des informels (§4) | prd.md FR-20, FR-31, FR-35, §10 |
| 9 | Préparer les 4 phrases orales du §5 et, si possible, redéposer un PDF corrigé (Small → Large) | pitch ; Proposal |
