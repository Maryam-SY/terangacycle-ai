---
title: "Proposition de changement de sprint — TerangaCycle 2.0"
date: 2026-11-25
status: approuvé le 25/11/2026, avec trois amendements ; appliqué aux artefacts le 25/11/2026
approved: 2026-11-25
workflow: bmad-correct-course
mode: Batch
scope: Majeur
trigger: "Cadrage « TerangaCycle 2.0 » validé le 25/11/2026"
inputs:
  - _bmad-output/planning-artifacts/prds/prd-TerangaCycleAI-2026-11-23/prd.md
  - _bmad-output/planning-artifacts/prds/prd-TerangaCycleAI-2026-11-23/addendum.md
  - _bmad-output/planning-artifacts/architecture/architecture-TerangaCycleAI-2026-11-23/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/implementation-artifacts/sprint-status.yaml
  - _bmad-output/implementation-artifacts/epic-1-context.md
---

# Proposition de changement de sprint — TerangaCycle 2.0

> **Règle de confidentialité appliquée à ce document et à toutes les modifications proposées.** Le dépôt est public. Aucun prix d'offre, taux de commission, forfait de frais, récit investisseurs, détail de négociation, nom de personne, téléphone, e-mail ni lien de maquette n'est écrit ici ni ne doit l'être dans les artefacts modifiés. Les prix, frais et commissions sont des **paramètres configurables par contrat**, sans valeur chiffrée : « valeurs commerciales hors dépôt ». Les responsables sont désignés par leur rôle (responsable produit, responsable technique, responsable IA).
>
> **Statut.** Approuvée le 25/11/2026 par la responsable produit (étape 5), avec les trois amendements ci-dessous. Les modifications ont été appliquées le même jour au PRD, à l'addendum, à l'épine, à `epics.md`, à `sprint-status.yaml` et à `epic-1-context.md` (étape 6). En cas d'écart entre le corps de ce document et la section « Décision d'approbation », la décision fait foi.

## Décision d'approbation (25/11/2026)

**Réponse :** oui. Les choix par défaut de l'annexe B s'appliquent, sauf pour les trois points amendés.

### Amendements choisis par la responsable produit

1. **Hors-ligne (point [!] n° 2) : maintenu dans la piste hackathon.** Les trois stories de l'Epic 6 (6.1, 6.2 et 6.3) rejoignent la piste hackathon, avec les quatre stories de l'Epic 3 (3.1, 3.9, 3.11 et 3.12). SM-1 et SM-4 restent inchangés, et la séquence « mode avion » de la vidéo de démo (8.8) est conservée. Ce point remplace « Epic 6 → P4 » dans §2.1, §2.2, P-11 et E-7, ainsi que les lignes du lot P4 qui concernent le hors-ligne.
2. **Vendeur d'un Lot (point [!] n° 4) : le Collecteur.** Le vendeur est le Collecteur, ou son groupement de collecteurs. Il vend des kg qu'il a lui-même prouvés, non contestés et non encore vendus. Une Organisation n'est vendeuse que si son Contrat le prévoit. L'ayant droit des kg d'une Preuve est fixé quand la Preuve est acceptée, dans cet ordre :
   - l'Organisation de la Mission, si son Contrat la désigne comme vendeuse ;
   - sinon, le groupement du Collecteur, si le Collecteur en est membre et si le Contrat du groupement l'autorise à vendre ;
   - sinon, le Collecteur.

   Un groupement est une Organisation de type `collector_group`. La Commission est un paramètre du Contrat du Recycleur. FR-38, FR-70, AD-35, AD-10 et les stories 9.2, 9.3, 9.5 et 9.6 sont ajustés en conséquence.
3. **Epic 13 (point [!] n° 8) : validé.** Il est planifié **après le pilote** (priorité « post-pilote », après P4) et inscrit dans `epics.md` et `sprint-status.yaml` avec l'état `backlog`.

### Tableau final des décisions

| # | Point | Décision finale |
|---|---|---|
| 1 | IA de la démo et Modèle entraîné | Défaut : le Modèle prototype, entraîné hors story, est publié par le contrat de la story 3.1 (manifeste `kind: trained`, étiqueté « prototype ») ; les seuils de SM-2, la Fiche du Modèle et la publication conditionnelle restent en P4 |
| 2 | Hors-ligne | **Amendé** : les stories 6.1 à 6.3 sont dans la piste hackathon ; SM-1, SM-4 et la séquence 8.8 sont inchangés |
| 3 | Missions d'entreprise | Défaut : vivier de Collecteurs vérifiés par la plateforme, plus les opérateurs prestataires désignés au Contrat de l'entreprise |
| 4 | Vendeur d'un Lot | **Amendé** : le Collecteur ou son groupement ; une Organisation seulement si son Contrat le prévoit |
| 5 | Preuve contestée | Défaut : Montant dû `contesté` et Litige automatique ; Lot non vendu retiré ; Lot vendu → Litige |
| 6 | Story 1.18 (miniature) | Défaut : oui |
| 7 | Nettoyage de confidentialité | Défaut : prénoms remplacés par des rôles, section « Pitch » de l'addendum retirée, historique Git non réécrit |
| 8 | Epic 13 | **Amendé** : validé, priorité post-pilote, inscrit en `backlog` |
| 9 | Spécification UX de la console | Défaut : spécification UX légère avant P2 ; P1 se contente du gabarit de la story 2.15 |
| 10 | « SMS » en P4 | Défaut : il s'agit du canal citoyen ; la passerelle SMS de l'OTP reste requise pour les comptes réels |

---

## 1. Résumé du problème

### 1.1 Déclencheur

Le 25/11/2026, la responsable produit a validé le cadrage « TerangaCycle 2.0 », avec la consigne de l'appliquer au code existant. TerangaCycle ne se présente plus comme une application de signalement pour une seule commune. Il devient une **infrastructure de traçabilité de l'économie circulaire au Sénégal**. Le signalement citoyen et la mise en relation pour la collecte deviennent des fonctions de cette infrastructure.

Le MVP reste ciblé : un territoire et une boucle prouvée, de bout en bout : **signalement citoyen ou demande d'entreprise → Mission → Preuve de collecte → kg vérifiés**.

Aucune story n'a révélé ce changement : il s'agit d'un **pivot stratégique**, qui apporte aussi de **nouvelles exigences des parties prenantes**. Il arrive entre la story 1.9 (terminée et fusionnée sur `main`) et la story 1.10 (prochaine).

### 1.2 Énoncé du problème

Les artefacts de planification décrivent un produit mono-commune, sans organisation cliente, sans espace entreprise, sans suivi financier et avec des Lots de matière déclarés librement. Le cadrage validé exige au contraire :

1. **Organisations clientes et cloisonnement des données dès maintenant.** Chaque table métier porte son organisation, et chaque requête est filtrée par l'organisation de la personne connectée, sauf pour le Super Admin. Le non-objectif « multi-commune » du PRD (§8) est levé.
2. **Une seule application React avec deux espaces chargés séparément** : l'espace mobile `/` (citoyen, collecteur) et la console web `/console` (commune ou opérateur, entreprise, recycleur, Super Admin). Le budget mobile reste de 500 Ko.
3. **Une IA minimale pour la démo du hackathon** : quatre stories de l'Epic 3 (Modèle sur le téléphone, Seuil de confiance, Correction). Le reste de l'IA passe en priorité 4.
4. **Aucune détention de fonds par TerangaCycle.** Le système enregistre des états (dû, payé, contesté, référence mobile money, confirmé par qui) ; le client paie lui-même le collecteur. Il n'y a pas de passerelle de paiement.
5. **Des Lots issus seulement de kg prouvés, non contestés et non encore vendus**, règle vérifiée par la base de données.

### 1.3 Preuves et contexte

| Constat | Source |
|---|---|
| Le multi-commune est un non-objectif, et aucune colonne `commune_id` n'existe au MVP | PRD §8 ; addendum B.1 point 16 ; épine, section « Différé » |
| Il n'y a que cinq rôles globaux, portés par `users.role` | PRD FR-3 ; story 2.3 (`role` = Citoyen) ; story 2.5 |
| Le paiement réel des Collecteurs est un non-objectif, et le suivi des paiements est « feuille de route » | PRD §8 et §9.2 |
| Le Lot de matière est déclaré par le Collecteur, sans lien avec une Preuve | PRD FR-38 ; épine AD-2 (`material_lots`) ; Epic 9 |
| Le code ne contient que la table métier `zones`. Les modules `auth`, `reports`, `missions`, `lots`, `analytics`, `ai` et `notifications` sont vides | `backend/migrations/versions/0001_baseline.py`, `0002_zones.py` ; `backend/app/modules/*` |
| La story 1.11 crée la table `reports` : c'est le dernier moment sans coût pour lui faire porter l'organisation | `epics.md`, story 1.11 |
| `sprint-status.yaml` indique la story 1.9 `in-progress`, alors qu'elle est fusionnée (PR n° 13) | `git log` de `main` |

**Conséquence.** Le changement a peu d'effet sur le code livré (stories 1.1 à 1.9, rien à défaire) mais beaucoup sur la planification : vision, rôles, modèle de données, quatre epics nouveaux ou réécrits, et l'ordre de priorité.

---

## 2. Analyse d'impact

### 2.1 Impact sur les epics

| Epic | Impact | Résumé |
|---|---|---|
| 1 · Signaler un dépôt | **Modifié** (P0) | 1.11 crée `organizations` et `reports.organization_id`. 1.14 et 1.17 sont ajustées. Nouvelle 1.18 (miniature sortie de 1.11). Les stories 1.1 à 1.10 ne changent pas. |
| 2 · Comptes, accès, audit | **Enrichi** (P1) | Organisations, appartenances, rôles par organisation, Super Admin minimal, console `/console`, test d'isolement entre organisations. Trois stories ajoutées (2.13 à 2.15). Les stories 2.3, 2.5, 2.6, 2.7, 2.11 et 2.12 sont modifiées. |
| 3 · IA | **Scindé** | Piste hackathon : 3.1, 3.9, 3.11 et 3.12 (3.8 est absorbée par 3.12). Les autres stories passent en P4. |
| 4 · Modérer et suivre | **Modifié** (P1) | File filtrée par organisation. `get_for_staff()` et `prefilled_type()` passent de 3.14 à 4.1. Les stories 4.6 et 4.11 (IA) passent en P4. |
| 5 · Missions et preuve | **Modifié** (P1) | La Mission porte une organisation et une origine. Les Collecteurs sont vérifiés par une organisation. Les stories 5.12 à 5.15 passent de « pilote » à P1. Nouvelle 5.16 : alertes de fraude. |
| 6 · Hors-ligne | **Reporté** (P4) | Contenu inchangé. Effet sur SM-1 et SM-4 (voir [!] n° 2). |
| 7 · Tableau de bord | **Modifié** (P1) | Les vues et les indicateurs sont cloisonnés par organisation ; statistiques par quartier, matière et période. |
| 8 · Démo et exploitation | **Ajusté** | 8.1 à 8.9 forment la piste démo ; 8.10 à 8.15 doivent être faites avant les premières données réelles (sortie de P1). Le budget de 8.2 porte sur l'espace mobile. |
| 9 · Lots de matière | **Réécrit** (P3) | La place de marché : vérification des recycleurs, Lots issus de kg prouvés, réservation, vente confirmée, commission. 8 stories remplacent les 5 actuelles. |
| 10 · Organisations et contrats | **Nouveau** (P2) | 6 stories. |
| 11 · Espace entreprise | **Nouveau** (P2) | 8 stories. |
| 12 · Finance terrain | **Nouveau** (P2) | 6 stories. |
| 13 · Données ouvertes | **Proposé, à valider** | 3 stories, après le pilote. |

### 2.2 Impact sur les stories

- **Terminées (1.1 à 1.9) : aucune réouverture.** Le schéma `zones` (1.8) sert tel quel : une organisation de type commune pointe vers sa Zone.
- **Prochaine (1.10) : inchangée.** `ingest_photo()` ne connaît pas l'organisation.
- **À modifier avant développement :** 1.11, 1.14, 1.17 ; 2.3, 2.5, 2.6, 2.7, 2.11, 2.12 ; 4.1, 4.3 ; 5.1, 5.3, 5.6, 5.9, 5.11, 5.13, 5.14 ; 7.1 à 7.5 ; 8.2.
- **À créer :** 1.18 ; 2.13 à 2.15 ; 5.16 ; 9.1 à 9.8 (réécrites) ; 10.1 à 10.6 ; 11.1 à 11.8 ; 12.1 à 12.6 ; 13.1 à 13.3 (proposées).
- **Fusionnée :** 3.8 dans 3.12.
- **Repriorisées en P4 :** 3.2 (pour l'essentiel), 3.3 à 3.7, 3.10, 3.13 à 3.15, 4.6, 4.11 et tout l'Epic 6.

### 2.3 Conflits avec les artefacts

| Artefact | Sections en conflit |
|---|---|
| PRD | §0, §1, §2, §3 ; FR-3, FR-14, FR-24, FR-25, FR-28, FR-31 à FR-33, FR-35 à FR-38, FR-39, FR-40, FR-41, FR-43 ; NFR-5, NFR-6, NFR-9, NFR-14 ; §6, §7, §8 (non-objectifs), §9 (périmètre), §10, §11 |
| Addendum | A (liste des modules) ; B.1 point 16 (« aucune colonne `commune_id` ») ; G (noms et messages de pitch, voir [!] n° 7) |
| Épine d'architecture | Diagramme du paradigme ; AD-1, AD-2, AD-3, AD-4, AD-9, AD-10, AD-14, AD-18, AD-21, AD-22, AD-25, AD-30 ; Conventions (« pas d'argent au MVP ») ; Différé (multi-commune) ; carte des capacités ; arborescence |
| UX | Aucun document `bmad-ux` (décision antérieure). La console, l'espace entreprise, l'espace recycleur, les écrans Super Admin et les montants du Collecteur sont **hors maquette** (voir [!] n° 9). |
| `epics.md` | Inventaire des exigences, carte de couverture, liste des epics, règles de cohérence, questions ouvertes, Epics 1 à 5, 7, 9 ; nouveaux Epics 10 à 13 |
| `sprint-status.yaml` | 1.9 à passer en `done` ; nouvelles entrées ; ordre par priorité |
| `epic-1-context.md` | À régénérer après la mise à jour d'`epics.md` (module `orgs`, propriété de `organizations`) |

### 2.4 Impact technique

- **Backend.** Trois nouveaux modules : `orgs`, `enterprise` et `finance`. Ils sont ajoutés aux conteneurs import-linter avec de nouvelles flèches autorisées. Le principal unique porte les appartenances. Le cloisonnement est appliqué dans chaque repository et vérifié par un test généré.
- **Base.** Nouvelles tables : `organizations`, `memberships`, `contracts`, `sites`, `site_waste_declarations`, `collection_requests`, `collection_schedules`, `invoices`, `payouts`, `disputes`, `lot_items`, `lot_proof_balances`, `lot_reservations` et `sales`. Une colonne `organization_id` s'ajoute aux tables métier. Les montants sont des entiers en FCFA.
- **PWA.** La console `/console` est chargée séparément. Un contrôle CI vérifie que le paquet de l'espace mobile ne contient pas la console. Caddy doit renvoyer `/console/*` vers l'application (retour à `index.html`).
- **CI.** Le test route × rôle couvre tous les rôles. S'y ajoutent un test d'isolement entre organisations, le budget du paquet mobile, et import-linter étendu.
- **Infrastructure, déploiement.** Aucun changement de topologie. `.env.example` reçoit de nouveaux réglages, sans aucune valeur commerciale.

---

## 3. Approche recommandée

### 3.1 Options évaluées

| Option | Viable ? | Effort | Risque | Commentaire |
|---|---|---|---|---|
| 1 · Ajustement direct (modifier ou ajouter des stories dans la structure actuelle) | Partiellement | Moyen | Moyen | Suffit pour l'Epic 1 et les compléments de 2, 4, 5 et 7, mais pas pour la vision, les non-objectifs ni les nouveaux domaines (entreprise, finance, place de marché). |
| 2 · Retour arrière | **Non** | Faible | Faible | Rien n'est à défaire : les stories 1.1 à 1.9 ne créent aucune table métier hormis `zones`, qui reste valable. |
| 3 · Revue du MVP du PRD | **Oui, nécessaire** | Élevé | Moyen | Le MVP est redéfini en lots P0 à P4, avec une piste hackathon. Les non-objectifs, la vision et les rôles changent. |

### 3.2 Recommandation : approche hybride (option 3 + option 1)

1. **Revoir le MVP et les fondations (option 3)** : PRD v2.0, épine (nouvelles AD 31 à 36 et AD amendées), réécriture d'`epics.md` pour les Epics 9 à 13.
2. **Ajuster directement l'Epic 1 et les epics P1 (option 1)** : la story 1.11 porte l'organisation dès sa création ; Epic 2 enrichi ; Epics 4, 5 et 7 cloisonnés.
3. **Ne rien défaire (option 2 écartée)** : 1.10 reste la prochaine story, puis 1.11 modifiée.

**Pourquoi cette approche.**

- **Coût minimal maintenant, coût maximal plus tard.** Ajouter `organization_id` à `reports` avant sa création ne coûte que quelques colonnes. Le faire après les Epics 4 et 5 imposerait une migration de données, une reprise des vues analytiques (AD-22) et une reprise des tests d'accès.
- **Élan de l'équipe préservé.** Le travail livré reste valable, et la prochaine story est inchangée.
- **Durabilité.** Le cloisonnement, la règle « aucune détention de fonds » et la traçabilité des kg sont posés par des contraintes de base et des tests CI, pas par une discipline à tenir à la main.
- **Valeur.** Le MVP opérationnel (P1) prouve la boucle. Le MVP commercial (P2) rend le produit vendable aux communes et aux entreprises. La place de marché (P3) arrive quand les kg vérifiés existent.

### 3.3 Effort, risques et calendrier

| Élément | Estimation |
|---|---|
| Mise à jour des artefacts (PRD, épine, `epics.md`, `sprint-status.yaml`, contexte de l'Epic 1) | 1 à 2 jours (PM et architecte) |
| Stories ajoutées (net) | Environ 28 : 1.18, 2.13 à 2.15, 5.16, 9.x (+3), 10.x (6), 11.x (8), 12.x (6) ; 13.x (3) si elles sont validées |
| Effet sur la piste hackathon | La story 1.11 s'alourdit un peu (compensé par 1.18). Les stories 2.13 et 2.15 rejoignent la porte H24 de l'Epic 2 ; 2.14 peut attendre H60. L'IA de démo passe de 15 à 4 stories. L'hors-ligne sort de la démo (voir [!] n° 2). |

| Risque | Niveau | Atténuation |
|---|---|---|
| Une fuite entre organisations passe inaperçue | Élevé | AD-31 : portée d'organisation obligatoire dans chaque repository, test d'isolement généré depuis la table des routes et bloquant en CI |
| Les stories 1.11 et 2.5 deviennent trop lourdes pour un agent | Moyen | 1.18 sort la miniature de 1.11 ; 2.13 sort les appartenances de 2.5 ; 2.15 sort le routage de la PWA de 2.5 |
| TerangaCycle se trouve à encaisser pour compte de tiers sans cadre légal | Élevé | AD-34 : aucune table de solde, aucune route qui déplace de l'argent, avis juridique demandé avant tout encaissement (question ouverte) |
| Des valeurs commerciales fuitent dans le dépôt | Moyen | Paramètres en base par contrat ; seed de démonstration avec des valeurs manifestement fictives et étiquetées ; revue avant chaque PR |
| La console alourdit l'espace mobile | Moyen | AD-33 : console chargée à part ; contrôle CI du paquet mobile (≤ 500 Ko) |

---

## 4. Propositions de modification détaillées

Le format est **AVANT → APRÈS**, avec une justification. Les identifiants P-n (PRD), A-n (architecture), E-n (epics) et S-n (`sprint-status.yaml`) servent à l'approbation proposition par proposition.

### 4.1 PRD (`prd.md`)

#### P-1 · En-tête et §0 Objet

**AVANT (§0, extrait)** : « Ce PRD fixe **ce que** TerangaCycle AI doit faire pour la démo du hackathon […] et pour le pilote qui suit. Il s'adresse à l'équipe ([prénoms]) et aux workflows BMAD en aval […] »

**APRÈS :**

```markdown
---
title: "PRD — TerangaCycle"
version: 2.0
status: final
created: 2026-11-23
updated: 2026-11-25
---

## 0. Objet du document

Ce PRD fixe **ce que** TerangaCycle doit faire : d'abord la démo du hackathon, ensuite un MVP
opérationnel puis commercial sur un premier territoire, enfin la place de marché de la matière
(lots P0 à P4, §9). Il s'adresse à l'équipe et aux workflows BMAD en aval.

**Version 2.0 (25/11/2026).** Le produit devient une infrastructure de traçabilité de l'économie
circulaire (§1). Voir `sprint-change-proposal-2026-11-25.md`.

**Confidentialité.** Ce dépôt est public. Les prix des offres, les frais de coordination, la
rémunération et la commission sont des **paramètres configurables par contrat**, sans valeur
chiffrée ici : « valeurs commerciales hors dépôt ». Aucun nom de personne ni coordonnée.
```

**Justification :** cadrage 2.0 et règle de confidentialité du dépôt public.

#### P-2 · §1 Vision (réécrite)

**AVANT :** un citoyen signale, un collecteur prouve, et la commune voit (vision mono-commune centrée sur le signalement).

**APRÈS :**

```markdown
## 1. Vision

TerangaCycle est une **infrastructure de traçabilité de l'économie circulaire au Sénégal**. Elle
relie ceux qui voient ou produisent des déchets (citoyens, entreprises), ceux qui les collectent
(collecteurs et récupérateurs vérifiés), ceux qui en ont la charge (communes, opérateurs) et ceux
qui les valorisent (recycleurs). Chaque kilo collecté est prouvé, contrôlé et traçable jusqu'à sa
vente.

**Boucle prouvée du MVP :** un Signalement citoyen ou une Demande de collecte d'entreprise devient
une Mission ; la Mission produit une Preuve de collecte ; la Preuve contrôlée produit des kg
vérifiés. Le signalement et la mise en relation pour la collecte sont des fonctions de cette
infrastructure. On commence par un territoire et cette seule boucle.

**Thèse.** Le problème n'est pas l'absence de signalement : c'est la **chaîne de confiance** entre
ceux qui produisent, collectent, financent et valorisent. Chaque étape produit une donnée
vérifiable (photo, position, classification revue par un humain, preuve géorepérée, contrôle par
échantillon). Cette chaîne transforme un appel informel en travail traçable, donne aux collecteurs
un historique crédible et des rémunérations enregistrées, et donne aux recycleurs une matière
d'origine prouvée.

- **Souveraine :** le Modèle d'IA appartient au projet et tourne sur l'appareil ; les données sont
  exportables ; l'hébergement est réversible.
- **Durable :** chaque collecte est comptée en kilos par Type de déchet, et chaque kg vendu
  remonte à une Preuve.
- **Inclusive :** Android d'entrée de gamme, pictogrammes, récupérateurs informels acteurs de
  premier rang et rémunérés pour les collectes validées ; wolof pendant le pilote.
- **Neutre financièrement :** TerangaCycle ne détient aucun fonds ; il enregistre ce qui est dû,
  payé ou contesté, et le client paie lui-même le collecteur.
- **Cloisonnée :** chaque organisation cliente ne voit que ses données, dès le premier jour.
```

**Justification :** décision n° 1 et principes du cadrage. La vision précédente reste un sous-cas : la boucle « Signalement ».

#### P-3 · §2 Utilisateurs cibles

**AVANT (§2.1)** : Citoyen, Collecteur, Modérateur, Administrateur commune et Recycleur (« extension »).

**APRÈS :** les cinq tâches à accomplir existantes restent, avec les renommages ci-dessous, et quatre s'ajoutent :

```markdown
- **Administrateur d'organisation** (commune ou opérateur ; remplace « Administrateur commune »).
  « Je veux savoir où agir en priorité, gérer mes collecteurs et rendre compte avec des chiffres
  vérifiables. »
- **Gestionnaire d'entreprise** (hôtel, restaurant, marché, supermarché). « Je veux faire
  collecter mes déchets quand il faut, et prouver chaque mois ce qui a été collecté et où c'est
  allé. »
- **Recycleur** (n'est plus une extension). « Je veux acheter une matière dont l'origine est
  prouvée, par type, quantité et zone. »
- **Super Admin** (équipe TerangaCycle). « Je veux ouvrir et suivre les organisations clientes,
  leurs contrats, la vérification des acteurs, les litiges et la santé de la plateforme. »
```

Nouveau **§2.4 Rôles et espaces** :

```markdown
### 2.4 Rôles et espaces

Les rôles sont portés par une **Appartenance** à une Organisation (FR-45). Une personne peut avoir
plusieurs Appartenances. Le Citoyen n'en a aucune.

| Acteur | Espace | Organisation (type) | Vérifié par | Accès |
|---|---|---|---|---|
| Citoyen | mobile `/` | aucune | — | gratuit, avec ou sans compte |
| Collecteur | mobile `/` | commune, opérateur ou plateforme | l'organisation | gratuit ; rémunéré pour les collectes validées |
| Modérateur | console `/console` | commune ou opérateur | — | contrat de l'organisation |
| Administrateur d'organisation | console | commune ou opérateur | plateforme | contrat de l'organisation |
| Gestionnaire d'entreprise | console | entreprise | plateforme | contrat de l'organisation |
| Recycleur | console | recycleur | plateforme | contrat de l'organisation |
| Super Admin | console | plateforme | — | équipe TerangaCycle |
```

Nouveaux parcours, chacun en 3 à 5 lignes, sur le format de UJ-1 à UJ-6 :

- **UJ-7.** Un gestionnaire d'hôtel demande une collecte ponctuelle depuis la console. Une Mission d'origine `collection_request` part chez les Collecteurs éligibles. Il voit ensuite la Preuve et les kg sur son site.
- **UJ-8.** Le Super Admin ouvre une commune cliente : il crée l'organisation, lui rattache sa Zone, nomme son premier Administrateur et enregistre son contrat.
- **UJ-9.** Un Collecteur voit le montant dû pour sa Mission terminée, puis « payé » quand le payeur confirme la référence mobile money. Il peut contester.
- **UJ-10.** Un Recycleur vérifié filtre les Lots de plastique d'une zone, réserve un Lot, obtient le contact du vendeur, puis confirme la réception.

Dans UJ-2, UJ-4 et UJ-6, « Administrateur commune » devient « Administrateur d'organisation ».

**Justification :** acteurs, rôles et espaces du cadrage.

#### P-4 · §3 Glossaire

**Termes modifiés :**

| Terme | AVANT | APRÈS |
|---|---|---|
| Collecteur vérifié | « validé par un Administrateur commune » | validé par une Organisation (commune, opérateur ou plateforme) dont il est membre ; il n'accepte que les Missions des organisations qui l'ont vérifié (FR-48) |
| Administrateur commune | Personnel qui pilote le Tableau de bord… | **Administrateur d'organisation** : membre d'une commune ou d'un opérateur qui pilote le Tableau de bord, gère les membres et exporte les données de son Organisation |
| Personnel | Modérateur ou Administrateur commune | Modérateur ou Administrateur d'organisation, **pour son Organisation** |
| Recycleur | consulte et réserve des Lots (extension) | membre d'une Organisation de type recycleur, vérifiée par la plateforme, qui achète des Lots |
| Lot de matière | quantité déclarée par un Collecteur | quantité de matière **constituée à partir de kg vérifiés** (Éléments de lot), mise en vente par son vendeur (FR-38) |
| Statut de Lot | `disponible` → `réservé` | `disponible` → `réservé` → `vendu` ; `réservé` → `disponible` (réservation annulée) ; `retiré` (terminal) |
| Mission | prise en charge d'un Signalement `validé` | prise en charge d'une **Origine** : Signalement `validé` ou Demande de collecte (FR-58) |

**Termes ajoutés** (une ligne chacun dans le PRD) : **Organisation** (types commune, opérateur, entreprise, recycleur, plateforme) ; **Appartenance** ; **Organisation responsable** (d'un Signalement) ; **Portée d'organisation** ; **Super Admin** ; **Console web** et **Espace mobile** ; **Gestionnaire d'entreprise** ; **Site** ; **Demande de collecte** ; **Programme de collecte** ; **Origine de Mission** ; **Contrat** ; **Facture** (états `émise`, `payée`, `en retard`) ; **Frais de coordination** ; **Rémunération prévue** ; **Montant dû** (états `dû`, `payé`, `contesté`) ; **Référence de paiement** (référence de transaction mobile money, saisie, jamais vérifiée auprès d'un opérateur) ; **kg vérifiés** (Poids déclaré d'une Preuve acceptée et non `contestée`) ; **Élément de lot** ; **Réservation** ; **Vente** ; **Commission** ; **Litige** ; **Alerte de fraude**.

**Justification :** vocabulaire obligatoire pour les stories (le glossaire du PRD fait foi).

#### P-5 · §4 Fonctionnalités existantes modifiées

| FR | AVANT (résumé) | APRÈS (résumé ; conséquences testables à rédiger dans le PRD) |
|---|---|---|
| FR-3 | Rôles Citoyen, Collecteur, Recycleur, Modérateur, Administrateur commune, et contrôle de propriété | Rôles **par Appartenance** (§2.4) **et** cloisonnement par Organisation (FR-46). Le test route × rôle couvre tous les rôles, et un test d'isolement entre organisations s'y ajoute (NFR-9, NFR-18). |
| FR-14 | Type pré-rempli : choix du Citoyen, sinon Classification serveur | Ajout : tant que la Classification serveur n'est pas livrée (P4), le Type pré-rempli est le choix du Citoyen, sinon la Classification locale, sinon aucun. Il ne devient définitif que par la décision du Personnel. |
| FR-24 | Le Collecteur vérifié voit les Signalements `validé` à moins de 5 km | Il voit les Missions ouvertes (Signalements `validé` **et** Demandes de collecte) des seules Organisations qui l'ont vérifié. Les autres règles sont inchangées (arrondi, rayon). |
| FR-25 | Accepter une Mission (Signalement) | Accepter une Mission, quelle que soit son Origine. L'exclusivité vaut par Origine. |
| FR-28 | Assignation par l'Administrateur commune | Assignation par l'Administrateur de l'Organisation de la Mission, à un Collecteur vérifié par cette Organisation. |
| FR-31 à FR-33 | Indicateurs, Carte de chaleur et Export de la commune | Mêmes définitions, calculées **dans la Portée d'organisation** de la personne. Ajout : répartition par quartier, Type de déchet et période. Le Super Admin voit le total (FR-53). |
| FR-35 | L'Administrateur commune gère les comptes Collecteurs et les rôles | L'Administrateur d'organisation gère les **Appartenances** de son Organisation : créer, vérifier, suspendre, changer le rôle. La suspension d'un **compte** est réservée au Super Admin. |
| FR-36 | Liste des actions auditées | Ajout : actions sur les organisations, appartenances, contrats, factures, montants dus, litiges, lots, réservations et ventes, et tout accès du Super Admin à une autre organisation. Chaque entrée porte son Organisation. |
| FR-37 | Jeu de démonstration (zones, comptes, Signalements) | Ajout : au moins deux Organisations communes de démonstration, une entreprise, un recycleur, et des comptes de chaque rôle. Tout montant de démonstration est manifestement fictif et étiqueté. |
| FR-41 | Une Preuve `contestée` est exclue des Kg collectés | Ajout : une Preuve `contestée` ne produit **aucun kg valorisable**. Elle ne peut entrer dans aucun Lot, et l'Élément de lot qui la contient est gelé (FR-71). |
| FR-43 | Second facteur du Modérateur et de l'Administrateur commune | Ajout : obligatoire pour l'Administrateur d'organisation, le Modérateur et le **Super Admin** dès qu'il y a des données réelles. Facultatif en P2 pour le Gestionnaire d'entreprise et le Recycleur. |

**Justification :** décisions n° 1, 4 et 5 du cadrage. L'IA serveur passe en P4 (décision n° 3).

#### P-6 · §4 Nouveaux groupes de FR

À insérer après §4.12. Chaque FR reçoit ses « Conséquences (testables) » complètes à la rédaction du PRD. Le contenu ci-dessous est le minimum à garder.

```markdown
### 4.13 Organisations et appartenances

#### FR-44 : Organisation
Une Organisation a un type (commune, opérateur, entreprise, recycleur, plateforme), un nom et un
statut (`active`, `suspendue`). Une commune ou un opérateur est rattaché à une Zone. Une seule
Organisation plateforme existe.
- Une commune sans Zone est refusée (422).
- Une Organisation `suspendue` ne reçoit plus de nouveau Signalement, de Demande ni de Mission ;
  ses membres gardent la lecture de son historique.

#### FR-45 : Appartenance et rôle par organisation
Un rôle est donné par une Appartenance (personne, Organisation, rôle, statut, date de
vérification). Une personne peut avoir plusieurs Appartenances.
- Un rôle incompatible avec le type de l'Organisation est refusé (par exemple Recycleur dans une
  commune).
- Le rôle est lu en base à chaque requête (AD-30), jamais dans le jeton.

#### FR-46 : Cloisonnement des données
Chaque objet métier appartient à une Organisation. Toute lecture, liste ou modification est limitée
à la Portée d'organisation de la personne connectée. Le Super Admin fait exception, et chacun de
ses accès est audité.
- Un objet d'une autre Organisation répond 404, sans aucune donnée.
- Un test d'isolement, généré depuis la table des routes, prouve qu'un membre de A ne lit, ne liste
  ni ne modifie rien de B (NFR-18).

#### FR-47 : Organisation responsable d'un Signalement
L'Organisation responsable est déduite de la Position à la réception : la commune ou l'opérateur
`active` dont la Zone couvre la Position, en prenant la Zone la plus précise. À défaut, c'est
l'Organisation plateforme. Elle est fixée à la création et ne change plus.
- Elle n'est jamais renvoyée au Citoyen.

#### FR-48 : Vérification par une organisation
Un Collecteur est vérifié par l'Organisation (commune, opérateur ou plateforme) dont il est
membre. Un Recycleur, un Gestionnaire d'entreprise et l'Administrateur initial d'une Organisation
sont vérifiés par la plateforme.

### 4.14 Super Admin et plateforme

#### FR-49 : Super Admin
Le Super Admin est membre de l'Organisation plateforme. Il est distinct de l'Administrateur
d'organisation. Le premier Super Admin est créé par une commande d'exploitation.
- Second facteur obligatoire avec des données réelles (FR-43).
- Chaque accès aux données d'une autre Organisation est inscrit au Journal d'audit.

#### FR-50 : Organisations clientes
Le Super Admin crée, modifie et suspend une Organisation, et nomme son premier Administrateur.

#### FR-51 : Contrats et abonnements
Un Contrat lie une Organisation à une offre : prix mensuel, dates et statut. Il porte aussi les
paramètres commerciaux (frais de coordination, rémunération, commission).
- Les valeurs sont saisies en base par le Super Admin. Aucune valeur n'est dans le code, la
  configuration versionnée ni ce document.
- Montants en entiers FCFA.

#### FR-52 : Factures et échéances (états)
Le système émet une Facture par Contrat et par période (montant, statut `émise`, `payée` ou
`en retard`, référence). Le Super Admin marque une Facture `payée` avec sa référence.
- Aucun encaissement, aucune passerelle de paiement.
- Une Facture `émise` dont l'échéance est dépassée passe `en retard` (tâche planifiée), et une
  alerte part.

#### FR-53 : Tableau de bord plateforme
Le Super Admin voit les indicateurs SM-B1 à SM-B8 (§10) par période et par Organisation.

#### FR-54 : Paramètres et Journal d'audit global
Le Super Admin règle les paramètres de la plateforme et consulte le Journal d'audit de toutes les
Organisations, filtrable par Organisation, action et période.

### 4.15 Espaces

#### FR-55 : Espace mobile et console web
Une seule application propose deux espaces chargés séparément : l'espace mobile `/` (Citoyen,
Collecteur) et la console web `/console` (Personnel, Gestionnaire d'entreprise, Recycleur, Super
Admin). Après la connexion, chacun arrive dans son espace. Une personne qui a plusieurs
Appartenances de console choisit l'Organisation active.
- Le budget de NFR-5 s'applique à l'espace mobile seul, et la console n'y est pas chargée.

### 4.16 Espace entreprise

#### FR-56 : Sites
Le Gestionnaire d'entreprise gère les Sites de son entreprise : nom, Position dans la Zone active,
contact du site.

#### FR-57 : Déchets déclarés
Pour chaque Site, il déclare les Types de déchet produits et un volume estimé par période.

#### FR-58 : Demande de collecte ponctuelle
Il demande une collecte pour un Site (Types de déchet, volume estimé, créneau souhaité). La
Demande crée une Mission d'Origine `collection_request`, ouverte aux Collecteurs éligibles
(AD-36).
- Une Demande n'a pas de modération citoyenne. Son statut suit celui de la Mission.

#### FR-59 : Programme de collecte
Il programme des collectes régulières (fréquence, Site, Types de déchet). Une tâche planifiée crée
les Demandes à échéance.

#### FR-60 : Suivi des demandes, des prestataires et des preuves
Il suit ses Demandes et leurs Missions : Collecteur (nom affiché et état de vérification), Preuves
(photos, Poids déclaré, méthode), kg vérifiés par Site.

#### FR-61 : Rapports mensuels
L'entreprise, et la commune ou l'opérateur, téléchargent un rapport mensuel (kg vérifiés par Type
de déchet et par Site ou quartier, Missions terminées, Preuves contestées), sans donnée
personnelle.

### 4.17 Finance terrain (aucune détention de fonds)

#### FR-62 : Frais et rémunération prévus
À sa création, une Mission reçoit ses Frais de coordination et sa Rémunération prévue, calculés
depuis les paramètres du Contrat de son Organisation.
- Les valeurs sont figées sur la Mission. Un changement de Contrat ne modifie pas les Missions
  existantes.

#### FR-63 : Montant dû
Une Preuve acceptée crée un Montant dû au Collecteur (Mission, Collecteur, montant, payeur, statut
`dû`).

#### FR-64 : Paiement confirmé
Le payeur (l'Organisation cliente) enregistre le paiement : référence mobile money, date,
personne qui confirme. Le Montant passe `payé`.
- TerangaCycle ne reçoit, ne détient et ne transfère aucun fonds. Aucune route ne déplace
  d'argent.
- Toute transition est inscrite au Journal d'audit.

#### FR-65 : Montants du Collecteur
Le Collecteur voit ses Montants dus et payés, et conteste un Montant (motif obligatoire), ce qui
ouvre un Litige.

#### FR-66 : Litiges
Un Litige porte sur un objet (Preuve, Montant dû, Vente) avec un motif, un statut (`ouvert`,
`en instruction`, `tranché`) et une décision motivée du Super Admin.
- Un Montant `contesté` n'est ni `dû` ni `payé` tant que le Litige est ouvert.

#### FR-67 : Suivi des montants
L'Organisation voit ses Montants dus, payés et contestés. Le Super Admin les voit tous. Les deux
peuvent exporter.

### 4.8 (complément) Fraude

#### FR-68 : Alertes de fraude
Une photo réutilisée, un Doublon probable dans une Preuve, une Preuve contestée ou un Poids déclaré
hors des bornes `[ASSUMPTION : bornes configurables]` crée une Alerte de fraude. L'Alerte est
visible du Personnel de l'Organisation et du Super Admin, et elle ajoute la Preuve à l'échantillon
de FR-41.
```

**§4.12 réécrit** : « Lots de matière (place de marché, P3) ».

```markdown
#### FR-38 (réécrit) : Constituer un Lot à partir de kg vérifiés
Le vendeur constitue un Lot (Type de déchet, Zone) à partir d'Éléments de lot. Chaque Élément
reprend une Preuve d'origine et les kg prélevés.
- Seuls des kg vérifiés, non contestés et non encore vendus peuvent entrer dans un Lot. La règle
  est vérifiée par la base (AD-35).
- La somme des kg prélevés sur une Preuve ne dépasse jamais son Poids déclaré.

#### FR-39 (réécrit) : Consulter les Lots
Un Recycleur vérifié consulte les Lots `disponible`, filtrés par Type de déchet, quantité et Zone.
Aucune identité ni aucun contact du vendeur n'apparaît dans la liste.

#### FR-40 (réécrit) : Réserver un Lot
Un Recycleur vérifié réserve un Lot `disponible`. Le contact du vendeur ne lui est donné qu'après
la réservation.
- Une réservation concurrente est refusée (409).

#### FR-69 : Vérifier un Recycleur
Le Super Admin vérifie une Organisation recycleur. Sans cette vérification, aucune consultation
ni réservation n'est possible.

#### FR-70 : Vente confirmée et commission
Le Recycleur confirme la réception, puis le vendeur confirme la vente (prix, date). La Commission
est calculée depuis le paramètre du Contrat et enregistrée sur la Vente, en état seulement.

#### FR-71 : Traçabilité des kg
Chaque kg vendu remonte à une Preuve. Si une Preuve est contestée après son entrée dans un Lot non
vendu, l'Élément est gelé et le Lot n'est plus vendable. Si le Lot est déjà vendu, un Litige
s'ouvre.
```

**Justification :** cadrage, sections « Espaces et fonctions », « Modèle de données » et « Règles de la chaîne de confiance ».

#### P-7 · §5 Exigences non fonctionnelles

| NFR | AVANT | APRÈS |
|---|---|---|
| NFR-5 | Page d'accueil ≤ 500 Ko hors images et Modèle | **Espace mobile** ≤ 500 Ko hors images et Modèle. La console n'est ni chargée ni précachée par l'espace mobile (contrôle CI sur le manifeste de construction). |
| NFR-6 | Mobile 390×844 ; tableau de bord 1280×800 | Mobile 390×844 ; **console** 1280×800, navigation complète au clavier |
| NFR-9 | Toutes les routes × chaque rôle | Toutes les routes × **chaque rôle de §2.4** (Collecteur vérifié ou non, Recycleur vérifié ou non) et sans jeton |
| NFR-14 | Jamais de jeton ni de numéro complet dans les journaux | Ajout : jamais de Référence de paiement complète ni de montant associé à une personne |
| **NFR-18** (nouvelle) | — | **Isolement entre organisations** : pour chaque route qui manipule un objet d'Organisation, un test à deux Organisations prouve l'absence de lecture, de liste et d'écriture croisées. La CI échoue si une route n'est pas couverte. |

#### P-8 · §6 Confidentialité, sécurité et conformité

Ajouts :

- **§6.1 Données collectées :** les Sites d'entreprise (Position et contact du site), les Montants et Références de paiement, les contacts des vendeurs et recycleurs. Durées de conservation `[ASSUMPTION]` : les pièces financières suivent la durée légale comptable, à confirmer. Les Références de paiement ne sont visibles que du payeur, du Collecteur concerné et du Super Admin.
- **§6.2 Abus et fraude**, nouvelles lignes : « faux paiement confirmé » → double vue payeur et Collecteur, contestation, Litige (FR-64 à FR-66) ; « kg gonflés ou réutilisés dans un Lot » → AD-35 et FR-71 ; « accès entre organisations » → FR-46 et NFR-18.
- **§6.3 Conformité :** « TerangaCycle n'encaisse aucun fonds pour compte de tiers. Un avis juridique sur la réglementation de la BCEAO est requis avant toute évolution vers un encaissement (§11). La facturation (forme juridique, TVA) est une question ouverte. »

#### P-9 · §7 Plateforme

**AVANT** : « PWA installable […] mobile d'abord ; tableau de bord sur ordinateur. » ; « les boutons "Je suis collecteur" et "Espace commune" de l'écran 1 mènent à la connexion OTP. »

**APRÈS** : « Une seule PWA React, deux espaces chargés séparément (FR-55) : mobile `/` et console `/console`. Sur l'écran 1, "Je suis collecteur" mène à la connexion OTP de l'espace mobile, et "Espace professionnel" (qui remplace "Espace commune") à la connexion de la console. » Les écrans hors maquette de la console sont ajoutés à la liste du §7.

#### P-10 · §8 Non-objectifs

| AVANT | APRÈS |
|---|---|
| « Paiement mobile réel des Collecteurs. » | « **Détention ou transfert de fonds par TerangaCycle**, et passerelle de paiement : le système enregistre des états (FR-62 à FR-67) ; le client paie le collecteur. » |
| « Multi-commune : cloisonnement du Personnel et des données par commune […]. Le MVP et le pilote servent une seule commune […] » | **Levé.** Remplacé par : « Ouverture **à grande échelle** de nombreux territoires, configuration des Types de déchet par Organisation, libre-service d'inscription des organisations : P4. Le cloisonnement par Organisation est, lui, dans le MVP (FR-46). » |
| (autres non-objectifs) | Inchangés |

**§9.2, ligne « Points citoyens, suivi des paiements des Collecteurs, intégration aux systèmes municipaux »** : retirer « suivi des paiements des Collecteurs », qui est désormais dans P2.

#### P-11 · §9 Périmètre (réécrit en lots)

```markdown
## 9. Périmètre et lots

| Lot | Contenu | Exigences |
|---|---|---|
| **P0 · en cours** | Finir l'Epic 1, avec l'Organisation dès la création d'un Signalement | FR-4, FR-7 à FR-10, FR-37, FR-44 (table), FR-47 |
| **P1 · MVP opérationnel** | Comptes OTP, Organisations, Appartenances, Super Admin minimal, console, audit ; modération, Statuts, notifications ; vérification des Collecteurs, Missions, Preuves, contrôle par échantillon, alertes de fraude ; Tableau de bord et exports | FR-1 à FR-3, FR-5, FR-6, FR-20 à FR-33, FR-35, FR-36, FR-41 à FR-43, FR-45, FR-46, FR-48, FR-49, FR-55, FR-68 |
| **Piste hackathon** | IA minimale : Modèle sur le téléphone, Seuil de confiance, Correction (4 stories de l'Epic 3) | FR-11, FR-12, FR-13 (partie création) |
| **P2 · MVP commercial** | Organisations et contrats ; espace entreprise ; finance terrain ; rapports mensuels | FR-50 à FR-54, FR-56 à FR-67 |
| **P3 · Place de marché** | Recycleurs vérifiés, Lots issus de kg vérifiés, réservation, vente, commission | FR-38 à FR-40, FR-69 à FR-71 |
| **P4 · Automatisation** | Reste de l'IA (Classification serveur, pipeline d'entraînement, réentraînement) ; hors-ligne ; canal SMS citoyen ; analyses ; ouverture de nombreux territoires | FR-13 (export), FR-14 à FR-19, FR-34 si non tirée avant |

La démo du hackathon montre P0, le chemin nominal de P1 et la piste hackathon. Les portes H24,
H48 et H60 ne servent plus qu'à cette démo.
```

§9.3 (risques de démo) : retirer la ligne « File hors-ligne pas prête » si le [!] n° 2 est confirmé.

#### P-12 · §10 Indicateurs de réussite

Ajouter un bloc **« Indicateurs d'activité (MVP commercial) — suivis, sans cible publiée dans le dépôt »** :

- **SM-B1** Clients payants ;
- **SM-B2** Revenu mensuel récurrent ;
- **SM-B3** Coût moyen par collecte ;
- **SM-B4** Missions terminées ;
- **SM-B5** Preuves valides (acceptées et non contestées) ;
- **SM-B6** Kg vérifiés ;
- **SM-B7** Lots vendus ;
- **SM-B8** Rémunérations versées (Montants `payé`).

Contre-indicateur ajouté : **SM-C5** « montants confirmés sans contestation possible ». Une part de contestations nulle doit inquiéter autant qu'une part élevée. Il équilibre SM-B8.

SM-1 et SM-4 : voir le [!] n° 2.

#### P-13 · §11 Questions ouvertes

- Q10 (multi-commune) : **fermée**, tranchée par FR-46. Elle est remplacée par la Q20.
- Les responsables nommés sont remplacés par des rôles (voir [!] n° 7).
- Nouvelles questions, **sans aucun chiffre** :

| # | Question | Responsable |
|---|---|---|
| 11 | Qui paie les collecteurs, et selon quelle grille (paramètres du Contrat) ? | Responsable produit |
| 12 | Prix des abonnements par type d'organisation (valeurs hors dépôt) | Responsable produit |
| 13 | Frais de coordination : forfait ou pourcentage ? | Responsable produit |
| 14 | Commission sur les ventes de Lots : assiette et payeur (valeur hors dépôt) | Responsable produit |
| 15 | Rôle de l'opérateur public national de gestion des déchets (organisation opérateur, partenaire de données ou autre) | Responsable produit |
| 16 | Commune et entreprises du pilote | Responsable produit |
| 17 | Forme juridique et facturation (TVA) | Responsable produit |
| 18 | Dossier CDP et région d'hébergement (reprend la Q3) | Responsable technique |
| 19 | Passerelle SMS : OTP du pilote et canal citoyen (reprend la Q2) | Responsable technique |
| 20 | Avis juridique BCEAO avant tout encaissement pour compte de tiers | Responsable produit |

#### P-14 · Addendum

- **A, ligne « Style »** : « Monolithe modulaire FastAPI : `auth`, `orgs`, `reports`, `missions`, `enterprise`, `finance`, `lots`, `analytics`, `ai`, `notifications`. »
- **B.1 point 16**, AVANT : « Aucune colonne `commune_id` de cloisonnement au MVP (multi-commune : non-objectif). » APRÈS : « Cloisonnement par `organization_id` sur chaque table métier (épine AD-31). La Zone active reste unique au MVP. »
- **G** : voir le [!] n° 7 (prénoms et messages de pitch).

---

### 4.2 Épine d'architecture (`ARCHITECTURE-SPINE.md`)

#### A-1 · En-tête

`binds: [FR-1..FR-71, NFR-1..NFR-18]`, `updated: '2026-11-25'`, `version: 2.0`. Ajouter `sprint-change-proposal-2026-11-25.md` aux `sources`.

#### A-2 · Paradigme et AD-1 : nouveaux modules et flèches

**AVANT** : 7 modules ; flèches `missions → reports, auth` ; `reports → ai, auth` ; `lots → missions, auth` ; `notifications → auth`.

**APRÈS** : 10 modules. Flèches ajoutées, toujours vers `service` seulement :

| De | Vers | Raison |
|---|---|---|
| `reports` | `orgs` | Organisation responsable (FR-47) |
| `missions` | `orgs` | Éligibilité des Collecteurs, Portée d'organisation |
| `enterprise` | `missions`, `orgs` | Une Demande crée une Mission (AD-36) |
| `finance` | `orgs` | Paramètres du Contrat |
| `lots` | `orgs` | Vérification des recycleurs, vendeur |
| `auth` | — | `auth` n'importe pas `orgs`. Le chargement des Appartenances passe par un port (A-6). |

Les réactions entre modules (Preuve acceptée → Montant dû, Preuve contestée → Lot gelé) restent dans `reactions.py` (AD-21) : `finance` et `lots` n'importent pas `missions` pour réagir. `pyproject.toml` ajoute `orgs`, `enterprise` et `finance` aux conteneurs `layers`, ainsi que les `ignore_imports` correspondants. Le diagramme mermaid est mis à jour.

#### A-3 · AD-2 Propriété des données (lignes ajoutées ou modifiées)

| Propriétaire | Tables |
|---|---|
| `auth` | `users` (**sans** `role`), `refresh_tokens`, `devices`, `staff_second_factors`. `collector_profiles` est **supprimée du plan** : la vérification passe dans `memberships`. |
| **`orgs`** | `organizations`, `memberships`, `contracts` |
| `reports` | Inchangé ; `reports.organization_id` |
| `missions` | `missions` (+ `organization_id`, `origin`, `collection_request_id`, `planned_fee`, `planned_payout`), `proofs`, `proof_reviews`, **`fraud_alerts`** |
| **`enterprise`** | `sites`, `site_waste_declarations`, `collection_requests`, `collection_schedules` |
| **`finance`** | `invoices`, `payouts`, `disputes` |
| `lots` | `lots` (remplace `material_lots`), `lot_items`, `lot_proof_balances`, `lot_reservations`, `sales` (remplace `lot_requests`) |

#### A-4 · Nouvelle AD-31 : Organisations et cloisonnement

```markdown
### AD-31 — Organisations et cloisonnement des données

- **Binds:** FR-3, FR-44 à FR-47, FR-49, NFR-9, NFR-18, AD-2, AD-9, AD-22.
- **Prevents:** une fuite entre organisations, un filtre oublié dans une requête, et un cloisonnement
  ajouté après coup par migration de données.
- **Rule:**
  - Chaque table métier porte `organization_id NOT NULL`, indexé, avec une clé étrangère vers
    `organizations` sans `ON DELETE`. Exceptions closes, sans organisation : `users`, `devices`,
    `refresh_tokens`, `staff_second_factors`, `zones`, `idempotency_records`, `push_subscriptions`.
    `audit_logs.organization_id` est nullable (actions de plateforme).
  - `core.security.OrgScope(org_ids: frozenset[UUID] | ALL)` est calculée par `principal()` :
    Organisation active pour le Personnel, le Gestionnaire et le Recycleur ; Organisations qui
    l'ont vérifié pour le Collecteur ; `ALL` pour le Super Admin ; aucune pour le Citoyen (seule
    la propriété s'applique).
  - Toute fonction de repository qui lit ou écrit une table cloisonnée exige un paramètre `scope`,
    sans valeur par défaut. Un test d'architecture parcourt les repositories et échoue sinon.
  - Un objet hors portée renvoie 404 (pas 403), comme le contrôle de propriété (AD-9).
  - Une lecture `ALL` est inscrite `superadmin.access` (une entrée par requête, sans données
    personnelles).
  - Organisation responsable d'un Signalement : `orgs.service.responsible_org(geog)` renvoie
    l'Organisation `active` de type commune ou opérateur dont la Zone couvre la Position (la Zone
    la plus précise : quartier, puis commune, puis ville), sinon l'Organisation plateforme. Elle
    est fixée à la création et immuable.
  - L'Organisation plateforme est une ligne système à UUID fixe, insérée par migration, jamais
    supprimée ni étiquetée `is_demo`.
  - Test d'isolement (NFR-18) : généré depuis la table des routes ; deux Organisations seedées avec
    les mêmes objets ; chaque route est appelée par un membre de A sur un objet de B.
  - Différé : RLS PostgreSQL en défense en profondeur (P4).
```

#### A-5 · Nouvelle AD-32 : rôles par appartenance (amende AD-9 et AD-30)

**AVANT (AD-9)** : `Principal(kind, user_id, role, device_hash, owner_key)`. **AVANT (AD-30)** : le cache `authz:<user_id>` contient `(status, role, token_version)`.

**APRÈS :**

```markdown
### AD-32 — Rôles par appartenance

- **Binds:** FR-3, FR-35, FR-45, FR-48, FR-49, FR-55, AD-9, AD-30.
- **Prevents:** un rôle global qui ignore l'organisation, un `core` qui importe un module, une
  appartenance lue dans le jeton.
- **Rule:**
  - `memberships(user_id, organization_id, role, status, verified_at, verified_by, is_demo)`,
    unique `(user_id, organization_id, role)`. `CHECK` de compatibilité rôle × type :
    `collector` ↔ commune, opérateur, plateforme ; `moderator` et `org_admin` ↔ commune, opérateur ;
    `enterprise_manager` ↔ entreprise ; `recycler` ↔ recycleur ; `super_admin` ↔ plateforme.
  - `Principal(kind, user_id, memberships, active_org_id, scope, device_hash, owner_key)`.
    `principal()` lit `(status, token_version, memberships)` dans `authz:<user_id>` (Valkey,
    TTL 60 s). Le repli en base passe par un **port** `core.security.MembershipLoader`, implémenté
    par `orgs.service` et branché dans `main.py` et `worker.py`, si bien que `core` n'importe aucun
    module.
  - Organisation active : en-tête `X-Org-Id`, exigé seulement si la personne a plusieurs
    Appartenances de console ; hors Appartenance : 403 `org_not_member`. Le Super Admin peut viser
    toute Organisation (audité, AD-31).
  - `require_role(...)` devient `require_membership(*roles)`. Le contrôle de propriété dans le
    service est inchangé.
  - Créer, suspendre ou changer le rôle d'une Appartenance incrémente `token_version` et invalide le
    cache par `after_commit` (comme AD-30).
  - Second facteur (AD-30) : `STAFF_MFA_REQUIRED` couvre `moderator`, `org_admin` et `super_admin`.
```

#### A-6 · Nouvelle AD-33 : console web

```markdown
### AD-33 — Deux espaces dans une seule PWA

- **Binds:** FR-55, NFR-5, NFR-6, NFR-12, AD-16, AD-23.
- **Prevents:** une console qui alourdit le téléphone d'un collecteur, et deux applications à
  maintenir.
- **Rule:**
  - `web/src/mobile/` (route `/`) et `web/src/console/` (route `/console/*`), chargée par
    `React.lazy` dans un morceau de construction distinct ; aucune importation de `console/` depuis
    `mobile/` (règle ESLint `no-restricted-imports`).
  - Le précache du service worker exclut les morceaux `console`.
  - CI : le manifeste de construction prouve que l'entrée mobile (JS et CSS, hors images et Modèle)
    tient en 500 Ko et ne référence aucun morceau `console`.
  - Même origine, même CSP et même client API (AD-11, AD-23) ; Caddy renvoie `/console/*` vers
    `index.html`.
  - Après la connexion, la redirection suit les Appartenances : aucune ou `collector` → `/` ;
    autres rôles → `/console`. La barrière reste l'API.
```

#### A-7 · Nouvelle AD-34 : aucune détention de fonds

```markdown
### AD-34 — États financiers sans détention de fonds

- **Binds:** FR-51, FR-52, FR-62 à FR-67, FR-70, PRD §6.3.
- **Prevents:** un TerangaCycle qui encaisse pour compte de tiers, des montants en flottants, des
  valeurs commerciales dans le dépôt.
- **Rule:**
  - Montants : `BIGINT` en francs CFA entiers (`amount_xof`), jamais de flottant ni de décimale.
    Taux en points de base entiers (`*_bps`).
  - `finance` enregistre des états (`invoices`, `payouts`, `disputes`). Il n'existe ni table de
    solde, ni portefeuille, ni passerelle de paiement, ni route qui déclenche un transfert. Un test
    d'architecture interdit toute dépendance de paiement dans `pyproject.toml`.
  - `payouts.status ∈ {due, paid, contested}` ; `paid` exige `payment_reference`, `paid_at` et
    `confirmed_by`. Les transitions passent par une table constante, testée, et sont auditées.
  - La Référence de paiement est masquée dans les journaux (AD-10), visible seulement du payeur, du
    Collecteur et du Super Admin.
  - Valeurs commerciales : seulement dans `contracts` (en base), saisies par le Super Admin.
    `Settings` et `.env.example` n'en contiennent aucune. Les données de démonstration utilisent des
    valeurs fictives étiquetées `is_demo`.
  - Frais et rémunération sont figés sur la Mission à sa création (`planned_fee`,
    `planned_payout`).
```

#### A-8 · Nouvelle AD-35 : traçabilité des kg

```markdown
### AD-35 — Lots issus de kg vérifiés, garantis par la base

- **Binds:** FR-38, FR-41, FR-70, FR-71, AD-2, AD-21.
- **Prevents:** un kg vendu deux fois, un Lot bâti sur une Preuve contestée, un module qui lit les
  tables d'un autre.
- **Rule:**
  - `lots` tient sa projection `lot_proof_balances(proof_id PK, organization_id, waste_type,
    kg_total, kg_taken, eligible, sold_kg)`, alimentée par les réactions à `ProofAccepted`,
    `ProofContested` et `ProofConfirmed` (AD-21). `CHECK (0 <= kg_taken AND kg_taken <= kg_total)`.
  - Prélever des kg : `UPDATE lot_proof_balances SET kg_taken = kg_taken + :kg WHERE proof_id = :p
    AND eligible AND kg_taken + :kg <= kg_total`. 0 ligne → 409 `kg_not_available`. Puis insertion
    de `lot_items(lot_id, proof_id, kg)` dans la même unité de travail.
  - `ProofContested` → `eligible = false`. Un Élément d'un Lot non vendu est gelé et le Lot passe
    `retiré` ; un Lot vendu ouvre un Litige (FR-71).
  - Une Vente confirmée fixe `sold_kg`. Un Lot `vendu` est immuable.
  - Test : 20 prélèvements concurrents sur une même Preuve ne dépassent jamais `kg_total`.
```

#### A-9 · Nouvelle AD-36 : origine des Missions (amende AD-3 et AD-4)

**AVANT (AD-4)** : index unique partiel `missions(report_id) WHERE status = 'active'`.

**APRÈS :**

```markdown
### AD-36 — Origine des Missions

- **Binds:** FR-24, FR-25, FR-28, FR-58, FR-59, AD-3, AD-4.
- **Rule:**
  - `missions.origin ∈ {report, collection_request}`, avec
    `CHECK ((origin = 'report') = (report_id IS NOT NULL))` et
    `CHECK ((origin = 'collection_request') = (collection_request_id IS NOT NULL))`.
  - Exclusivité (AD-4) : deux index uniques partiels, `(report_id) WHERE status = 'active'` et
    `(collection_request_id) WHERE status = 'active'`.
  - `missions.organization_id` : l'Organisation responsable du Signalement, ou l'entreprise de la
    Demande.
  - Éligibilité : `orgs.service.eligible_collector_orgs(mission_org)` (pour un Signalement,
    l'Organisation elle-même ; pour une Demande, voir le [!] n° 3).
  - Machine à états de la Demande (`requested → assigned → completed | cancelled`), propre à
    `enterprise` et mise à jour par réaction à `MissionAssigned`, `MissionCompleted` et
    `MissionReleased`. La porte des Statuts de Signalement (AD-3) ne concerne que `origin = report`.
  - Mise en place par expansion : la story 5.3 ajoute `organization_id` et `origin` (`report`
    seulement) ; la story 11.3 ajoute `collection_request_id`, rend `report_id` nullable et pose les
    `CHECK`.
```

#### A-10 · AD existantes amendées (une ligne chacune)

- **AD-10** : niveaux d'exposition étendus. Le Gestionnaire d'entreprise voit la Position exacte de ses Sites et les photos de Preuve de ses Demandes. Le Recycleur voit la Zone d'un Lot, jamais une Position de Preuve. Le contact du vendeur est donné après la réservation, via `orgs.service.get_contact()`. Les Références de paiement sont masquées.
- **AD-14** : `is_demo` s'ajoute à toutes les nouvelles tables, sauf l'Organisation plateforme. La commande `demo load` crée les Organisations de démonstration.
- **AD-18** : nouvelles tâches planifiées `enterprise.generate_scheduled_requests` (quotidienne), `finance.issue_invoices` (mensuelle), `finance.mark_overdue_invoices` (quotidienne) et `missions.fraud_sweep` (horaire).
- **AD-21** : nouveaux événements `ProofAccepted`, `ProofContested`, `ProofConfirmed`, `MissionCompleted`, `MissionReleased`, `CollectionRequestCreated`, `MembershipSuspended(user_id, organization_id)` (remplace `CollectorSuspended` pour la libération des Missions d'une seule organisation), `OrganizationSuspended` et `SaleConfirmed`. Nouvelles réactions : `ProofAccepted` → `finance.service.create_payout()` et `lots.service.on_proof_accepted()` ; `ProofContested` → `lots`, `finance` (le Montant passe `contested`, un Litige s'ouvre).
- **AD-22** : chaque vue porte `organization_id`, et les lectures passent par `scope`. Nouvelles vues `v_finance_facts` et `v_lot_facts` pour FR-53.
- **AD-25** : `AuditAction` s'étend à `org.create`, `org.update`, `org.suspend`, `membership.create`, `membership.verify`, `membership.suspend`, `membership.role_change`, `contract.create`, `contract.update`, `invoice.issue`, `invoice.status`, `payout.create`, `payout.status`, `dispute.open`, `dispute.decide`, `lot.create`, `lot.reserve`, `lot.withdraw`, `sale.confirm`, `fraud_alert.create` et `superadmin.access`. `audit_logs.organization_id` est nullable.
- **Conventions** : la ligne « Poids… pas d'argent au MVP » devient « Montants : `BIGINT` FCFA entiers (AD-34) ». Les énumérations s'étendent à `OrganizationType`, `MembershipRole`, `MissionOrigin`, `CollectionRequestStatus`, `InvoiceStatus`, `PayoutStatus`, `DisputeStatus` et `LotStatus` (`available`, `reserved`, `sold`, `withdrawn`).
- **Différé** : retirer « Multi-commune ; la Zone active suffit ». Ajouter « RLS PostgreSQL (P4) », « Ouverture de nombreux territoires : Zone active = union des Zones des Organisations actives (P4) » et « Passerelle de paiement : exclue tant que l'avis juridique n'est pas rendu ».
- **Carte des capacités et arborescence** : ajouter les lignes 4.13 à 4.17, `modules/orgs`, `modules/enterprise`, `modules/finance`, ainsi que `web/src/mobile` et `web/src/console`.
- **Diagramme des entités** : ajouter `ORGANIZATIONS`, `MEMBERSHIPS`, `CONTRACTS`, `SITES`, `COLLECTION_REQUESTS`, `INVOICES`, `PAYOUTS`, `DISPUTES`, `LOT_ITEMS`, `LOT_PROOF_BALANCES` et `SALES`.

---

### 4.3 Epics et stories (`epics.md`)

#### E-1 · Notes de lecture et liste des epics

- **Notes de lecture, AVANT** : « Portes du plan de 72 h […] H24, H48, H60 = démo du hackathon […] extension = Lots de matière ». **APRÈS** : « Chaque epic et chaque story portent une **Priorité** (P0 à P4, PRD §9), qui est l'axe de planification. Les portes H24, H48 et H60 ne servent plus qu'à la démo du hackathon. »
- **Inventaire des exigences et carte de couverture** : ajouter FR-44 à FR-71 et NFR-18, avec la correspondance suivante :

| Exigences | Epic |
|---|---|
| FR-44 (table), FR-47 | Epic 1 (1.11) |
| FR-44, FR-45, FR-46, FR-48, FR-49, FR-55, NFR-18 | Epic 2 |
| FR-68 | Epic 5 |
| FR-50 à FR-54 | Epic 10 |
| FR-56 à FR-61 | Epic 11 |
| FR-62 à FR-67 | Epic 12 |
| FR-38 à FR-40, FR-69 à FR-71 | Epic 9 |

- **Liste des epics** : ajouter la ligne « **Priorité :** » à chaque epic (1 : P0 ; 2, 4, 5, 7 : P1 ; 3 : piste hackathon et P4 ; 8 : démo et sortie de P1 ; 9 : P3 ; 10, 11, 12 : P2 ; 6 : P4 ; 13 : proposé). Ajouter les Epics 10 à 13. Renommer l'Epic 7 « Tableau de bord des organisations » et l'Epic 9 « Place de marché de la matière ».
- **Règles de cohérence** (nouvelles lignes ou lignes modifiées) :

| Brique partagée | Story propriétaire | Utilisée par |
|---|---|---|
| Table `organizations`, ligne plateforme, `orgs.service.responsible_org()` | **1.11** | 1.14, 1.17, 2.13, 2.14, 4.x, 5.x, 7.x, 10.x, 11.x |
| Tâche de miniature `thumb:<photo_id>` | **1.18** (au lieu de 1.11) | 2.9, 4.1, 4.5, 5.1 |
| `memberships`, `OrgScope`, `MembershipLoader`, `X-Org-Id`, `require_membership()` | **2.13** | 2.5, 2.11, 2.14, et toutes les stories P1 et suivantes |
| Générateur du test d'isolement entre organisations | **2.5** | toutes les stories qui ajoutent une route |
| Coque de la console `/console`, sélecteur d'Organisation | **2.15** | 2.7, 2.11, 2.14, 4.1, 5.9, 7.3, 9.x, 10.x, 11.x, 12.x |
| `reports.service.get_for_staff()`, `prefilled_type()` | **4.1** (au lieu de 3.14) | 4.2, 4.3 ; 3.14 (P4) l'étend |
| Événements `ProofAccepted`, `MissionCompleted` | 5.6 | 9.2, 11.6, 12.2 |
| Événement `ProofContested` | 5.14 | 9.2, 12.5 |
| `contracts` (paramètres commerciaux) | 10.2 | 10.3, 12.1, 9.7 |
| `collection_requests`, `missions.collection_request_id` | 11.3 | 11.4 à 11.6 |
| `payouts` | 12.2 | 12.3, 12.4, 12.6, 10.5 |
| `disputes` | 12.5 | 9.6, 11.6, 12.4 |
| `lot_proof_balances` | 9.2 | 9.3, 9.6 |
| Ligne `collector_profiles` (2.5) | **supprimée** | remplacée par `memberships.verified_at` |

- **Questions ouvertes d'`epics.md`** : la n° 7 (premier Administrateur) est tranchée par 2.14 ; la n° 9 (stories lourdes) est en partie traitée par 1.18, 2.13 et 2.15 ; les responsables nommés deviennent des rôles ([!] n° 7).

#### E-2 · Epic 1 : Signaler un dépôt (P0)

**Story 1.11 : Recevoir un Signalement anonyme et attribuer son Numéro de suivi** (titre et clé inchangés)

Section : critères d'acceptation, migration.

```
AVANT :
**Alors** elle crée seulement `devices` (propriétaire `auth` ; …), `reports`, `report_photos`
(dont `thumb_key` nullable) et `tracking_counters` (propriétaire `reports`)

APRÈS :
**Alors** elle crée seulement `organizations` (propriétaire `orgs`, nouveau module : `id`, `type`
parmi `commune`, `operator`, `enterprise`, `recycler`, `platform` (`core/enums.py`), `name`,
`zone_id` nullable vers `zones` et obligatoire pour `commune` (`CHECK`), `status` parmi `active`,
`suspended`, `is_demo`, horodatages), avec la ligne système de l'Organisation plateforme (UUID
fixe, `is_demo = false`) ; `devices` (propriétaire `auth`) ; `reports`, `report_photos` (dont
`thumb_key` nullable) et `tracking_counters` (propriétaire `reports`)
**Et** `reports` porte `organization_id NOT NULL`, indexé, avec une clé étrangère vers
`organizations` sans `ON DELETE` (AD-31).
```

Critères ajoutés :

```
**Étant donné** deux Organisations `active` de type commune rattachées à deux communes
d'arrondissement de la Zone active, et aucune sur une troisième
**Quand** trois Signalements arrivent, un dans chaque commune
**Alors** les deux premiers prennent l'`organization_id` de leur commune
(`orgs.service.responsible_org()`, Zone la plus précise) et le troisième celui de l'Organisation
plateforme
**Et** `organization_id` est absent de la réponse au Citoyen, et aucune route ne permet de le
modifier.

**Étant donné** le nouveau module `orgs` (router, service, repository)
**Quand** import-linter s'exécute
**Alors** `app.modules.orgs` est un conteneur `layers`, et la seule flèche ajoutée est
`reports → orgs.service`.
```

Critère retiré (déplacé en 1.18) : « une photo de Signalement stockée […] tâche arq `thumb:<photo_id>` […] rejouer la tâche ne crée pas de second objet ». La colonne `thumb_key` reste créée par 1.11.

Exigences : ajouter FR-44, FR-47, AD-31.
**Justification :** la table `reports` naît ici. Y mettre l'organisation coûte quelques colonnes, alors que l'ajouter plus tard imposerait une migration de données. La miniature sort de la story pour compenser l'ajout (question n° 9 d'`epics.md`).

**Story 1.14 : Repérer les Doublons probables à la réception**

```
AVANT : … quand un nouveau Signalement arrive à 49 m de lui (`ST_DWithin` …)
APRÈS : … (`ST_DWithin` …), la recherche étant limitée aux Signalements de la même
`organization_id` (AD-31)
```

Pour une photo identique, la recherche reste globale à la plateforme : une photo réutilisée est un signal de fraude, quelle que soit l'organisation. Le Citoyen ne voit aucun champ supplémentaire.

**Story 1.17 : Charger et retirer les Données de démonstration en une commande**

```
AJOUT : **Alors** `demo load` crée d'abord au moins deux Organisations de type commune
`is_demo = true`, rattachées à deux communes d'arrondissement de Dakar, et les Signalements
fictifs se répartissent entre elles par `responsible_org()`
**Et** `demo purge` retire ces Organisations et jamais l'Organisation plateforme.
```

**Nouvelle story 1.18 : Produire la miniature d'une photo de Signalement** (P0, porte H24)

Elle reprend tel quel le critère retiré de 1.11 : tâche `thumb:<photo_id>` par `after_commit`, JPEG d'au plus 30 Ko sous `report_thumb/…`, `report_photos.thumb_key`, rejouable sans doublon, et aucune tâche si la transaction est annulée. Elle dépend de 1.11. Voir le [!] n° 6.

**Inchangées :** 1.10, 1.12, 1.13, 1.15, 1.16 (le `devices` du Citoyen n'est pas cloisonné : c'est une table d'identité).

#### E-3 · Epic 2 : Comptes, organisations, accès et audit (P1, enrichi)

**Intro, AVANT** : « Chacun se connecte par OTP avec son rôle […] l'Administrateur commune vérifie les Collecteurs […] ». **APRÈS** : « Chacun se connecte par OTP. Ses rôles viennent de ses Appartenances à des Organisations, et chaque requête est cloisonnée à sa Portée d'organisation, ce que prouve un test d'isolement. Le Super Admin ouvre les Organisations. L'espace mobile et la console sont chargés séparément. Chaque action sensible est tracée. Avant les données réelles, le Personnel et le Super Admin ajoutent un Second facteur. »

**Ordre d'exécution** : 2.1 → 2.2 → 2.3 → 2.4 → **2.13** → **2.15** → 2.5 → 2.6 → 2.7 → 2.8 → 2.9 → 2.10 → 2.11 → **2.14** → 2.12.

| Story | Modification (AVANT → APRÈS) |
|---|---|
| 2.3 | « `role` = Citoyen » → la table `users` n'a **pas** de colonne `role`. La réponse renvoie `user {id, memberships: []}`. Un utilisateur sans Appartenance est Citoyen. |
| 2.5 | Rôles `citizen, collector, recycler, moderator, municipal_admin` → `MembershipRole` (`collector`, `moderator`, `org_admin`, `enterprise_manager`, `recycler`, `super_admin`). `require_role` devient `require_membership`. Principaux testés : sans jeton, appareil, Citoyen, Collecteur non vérifié, Collecteur vérifié, Modérateur, Administrateur d'organisation, Gestionnaire d'entreprise, Recycleur non vérifié, Recycleur vérifié, Super Admin. **Ajout : générateur du test d'isolement entre organisations** (deux Organisations ; la CI échoue si une route n'est pas couverte). **Retrait** : `collector_profiles` (remplacée par 2.13) et le routage de la PWA par rôle (déplacé en 2.15). Comptes de démonstration : un par rôle, répartis dans les Organisations de démonstration. |
| 2.6 | `audit_logs` gagne `organization_id` (nullable). Liste `AuditAction` étendue (A-10). |
| 2.7 | Journal filtré par la Portée de l'Administrateur d'organisation ; le Super Admin voit tout, avec un filtre par Organisation. |
| 2.11 | (Titre inchangé.) Routes `/v1/orgs/{id}/members` : l'Administrateur d'organisation crée l'Appartenance d'un Collecteur (et le compte s'il n'existe pas), la vérifie, la **suspend dans son Organisation** et change le rôle dans son Organisation. La suspension d'un **compte** relève du Super Admin. `CollectorSuspended` devient `MembershipSuspended(user_id, organization_id)`. |
| 2.12 | Priorité P1. Le Second facteur couvre aussi `super_admin` (obligatoire en `prod`). La réinitialisation est faite par l'Administrateur de la même Organisation, ou par le Super Admin. |

**Nouvelle story 2.13 : Organisations et appartenances par rôle** (P1, porte H24)

- **Étant donné** la migration du module `orgs`, **alors** `memberships` est créée selon AD-32 : clé unique sur `(user_id, organization_id, role)` et `CHECK` de compatibilité entre rôle et type d'Organisation, testé couple par couple.
- **Étant donné** un utilisateur connecté, **quand** il appelle `GET /v1/me/memberships`, **alors** il reçoit ses Appartenances (Organisation, type, rôle, état vérifié), et rien d'autre.
- **Étant donné** `principal()`, **alors** il charge les Appartenances par le port `MembershipLoader` et le cache `authz:<user_id>`, et calcule `OrgScope`. `X-Org-Id` hors Appartenance renvoie 403 `org_not_member`. Avec plusieurs Appartenances de console et sans `X-Org-Id`, la réponse est 400 `org_required`.
- **Étant donné** un changement d'Appartenance, **alors** `token_version` est incrémenté et la requête suivante reçoit 401 `session_revoked`.
- **Étant donné** les repositories, **alors** un test d'architecture échoue si une fonction qui touche une table cloisonnée n'exige pas `scope`.

**Nouvelle story 2.14 : Super Admin minimal de la plateforme** (P1, porte H60)

- **Étant donné** `python -m app.cli superadmin create --phone …`, **alors** elle crée l'utilisateur et son Appartenance `super_admin` dans l'Organisation plateforme. Elle est auditée et utilisable en `prod` (rôle `teranga_app`).
- **Étant donné** le Super Admin, **quand** il appelle `POST /v1/admin/organizations` (type, nom, Zone pour une commune) puis `POST /v1/admin/organizations/{id}/admins`, **alors** l'Organisation et son premier Administrateur sont créés, et `org.create` et `membership.create` sont inscrits.
- **Étant donné** `GET /v1/admin/organizations`, **alors** la liste est paginée. Une lecture d'objet d'une autre Organisation inscrit `superadmin.access`.
- **Étant donné** un autre rôle, **alors** il reçoit 403 sur `/v1/admin/*`, ce que vérifie le test route × rôle.
- Écran « Organisations » de la console [HORS MAQUETTE], en 1280×800, entièrement au clavier.

**Nouvelle story 2.15 : Console web chargée à part de l'espace mobile** (P1, porte H24)

- **Étant donné** la construction Vite, **alors** `/console/*` est un morceau chargé par `React.lazy`. Le test CI du manifeste prouve que l'entrée mobile tient en 500 Ko et ne référence aucun morceau `console`, et le précache exclut la console.
- **Étant donné** une connexion OTP réussie, **alors** l'utilisateur est redirigé selon ses Appartenances : Citoyen et Collecteur vers `/`, autres rôles vers `/console`. Une URL de console sans Appartenance affiche « Accès refusé ».
- **Étant donné** plusieurs Appartenances de console, **alors** un sélecteur d'Organisation fixe `X-Org-Id` pour le client API.
- **Étant donné** Caddy, **alors** `/console/*` renvoie vers l'application.
- **Étant donné** l'écran 1, **alors** « Espace commune » devient « Espace professionnel ».
- La console est en 1280×800, navigable au clavier, avec un focus visible et le bandeau du Mode démonstration.

#### E-4 · Epic 3 : L'IA propose le type de déchet (scindé)

**Piste hackathon (4 stories)** :

| Story | Contenu gardé |
|---|---|
| 3.1 Contrat du Modèle et Modèle factice | Inchangée. **Absorbe** de 3.2 la distribution minimale : le `.onnx` et le manifeste courants (`ml/release/current.json`) sont récupérés à la construction de la PWA, empreinte vérifiée. |
| 3.9 Classification locale dans la PWA | Inchangée (« Modèle sur le téléphone »). |
| 3.11 Enregistrer la Classification locale et la Correction du Citoyen | Inchangée (« Correction »). |
| 3.12 Écran 3 · Résultat IA avec Seuil de confiance et Correction | **Absorbe 3.8** (sélecteur piloté par la proposition IA) (« Seuil de confiance »). |

**P4** : 3.2 (le reste : release GitHub, récupération par l'API), 3.3, 3.4, 3.5, 3.6, 3.7, 3.10, 3.13, 3.14, 3.15.
**Fusionnée** : 3.8 dans 3.12, entrée retirée de `sprint-status.yaml`.
**Prérequis de l'Epic 4, AVANT** : « Les stories 3.11 (`corrections`) et 3.14 (`prefilled_type()`, `get_for_staff()`) sont requises par 4.1 et 4.3 ». **APRÈS** : « La story 3.11 est requise par 4.1 et 4.3. `prefilled_type()` et `get_for_staff()` sont créées par 4.1. »
Voir le [!] n° 1 (Modèle entraîné « prototype » décidé le 24/11).

#### E-5 · Epic 4 : Modérer et suivre un signalement (P1)

- **4.1** : la File est limitée à la Portée d'organisation du Modérateur ; un Signalement d'une autre Organisation renvoie 404. La story **crée** `reports.service.get_for_staff()` et `prefilled_type()` (choix du Citoyen, sinon Classification serveur si elle existe, sinon Classification locale, sinon aucun : PRD FR-14 modifié).
- **4.3** : le prérequis 3.14 est retiré. Le reste est inchangé.
- **4.6** (export des Corrections) et **4.11** (réentraînement) : priorité **P4**.
- **4.2, 4.4, 4.5, 4.7 à 4.10** : seulement le cloisonnement des lectures du Personnel (`scope`). Le Citoyen garde le contrôle de propriété.

#### E-6 · Epic 5 : Missions et preuve de collecte (P1)

| Story | Modification |
|---|---|
| 5.1 | La liste couvre les Missions ouvertes des seules Organisations qui ont vérifié le Collecteur (`OrgScope`). Test : un Collecteur vérifié par A ne voit aucun Signalement de B. |
| 5.3 | La migration de `missions` ajoute `organization_id NOT NULL` (copié du Signalement) et `origin` (`report` seulement, AD-36). L'acceptation exige une vérification par l'Organisation de la Mission (sinon 403 `collector_not_verified_here`). |
| 5.6 | Une Preuve acceptée émet `ProofAccepted` et `MissionCompleted` (AD-21) sous `after_commit`. Aucune réaction n'y est abonnée dans cette story. |
| 5.9 | L'assignation est faite par l'Administrateur de l'Organisation de la Mission, à un Collecteur vérifié par elle. |
| 5.11 | La réaction s'abonne à `MembershipSuspended` et ne libère que les Missions de l'Organisation concernée. `AccountDeleted` libère toutes les Missions. |
| 5.12 à 5.15 | Priorité **P1** (au lieu de « pilote »). 5.13 : au moins une Preuve tirée par Organisation ayant des Preuves. 5.14 : `contestée` émet `ProofContested`. |

**Nouvelle story 5.16 : Alertes de fraude pour le Personnel et le Super Admin** (P1)

- **Étant donné** une Preuve dont une photo a le `sha256` d'une photo déjà reçue (Signalement ou Preuve, toutes Organisations), ou un Poids déclaré hors des bornes configurables `[ASSUMPTION]`, ou une Preuve `contestée`, **alors** une ligne `fraud_alerts(organization_id, kind, proof_id, created_at, status)` est créée et la Preuve est ajoutée à l'échantillon (5.13). `fraud_alert.create` est inscrit au Journal d'audit.
- **Étant donné** le Personnel, **alors** `GET /v1/fraud-alerts` liste les Alertes de sa Portée. Le Super Admin voit toutes les Organisations.
- **Étant donné** une Alerte, **quand** le Personnel la classe (`examinée`, motif), **alors** l'action est auditée.
- La tâche planifiée `missions.fraud_sweep` (horaire, AD-18) est idempotente.

#### E-7 · Epic 6 : Signaler sans réseau → **P4**

Le contenu est inchangé. Le prérequis de l'Epic 8 (8.8, séquence « mode avion » de la vidéo) est à revoir selon le [!] n° 2.

#### E-8 · Epic 7 : Tableau de bord des organisations (P1)

- **7.1** : `v_report_facts`, `v_mission_facts` et `v_collector_facts` exposent `organization_id`, et leur lecture exige `scope`.
- **7.2 à 7.5** : indicateurs, Carte de chaleur et Export dans la Portée. Ajout de la répartition par quartier, Type de déchet et période (cadrage « stats par quartier/matière/période »).
- **7.6** (carte publique) : agrégation sur toutes les Organisations, sans aucun identifiant d'Organisation.
- **7.7** : priorité P1.

#### E-9 · Epic 8 : Démo fiable et service exploitable

- **8.2** : le budget est mesuré sur l'entrée mobile seule (AD-33).
- **8.6 et 8.9** : la démo montre deux Organisations de démonstration et le cloisonnement (une phrase ajoutée au script de démo).
- **8.10 à 8.15** : priorité « avant données réelles », condition de sortie de P1.

#### E-10 · Epic 9 réécrit : Place de marché de la matière (P3)

Intro : « Un Recycleur vérifié par la plateforme achète des Lots constitués exclusivement de kg vérifiés, non contestés et non encore vendus. Chaque kg vendu remonte à une Preuve. La réservation, la vente et la commission sont enregistrées en états, sans aucun flux d'argent. » FR couvertes : FR-38 à FR-40, FR-69 à FR-71. Prérequis : Epics 2, 5 (5.6, 5.14) et 10 (10.2).

| Story | Critères d'acceptation (esquisse) |
|---|---|
| **9.1 Vérifier un Recycleur** | Le Super Admin vérifie une Organisation recycleur (`membership.verify`). Une Organisation non vérifiée reçoit 403 sur toute route de Lot. Test route × rôle avec un Recycleur non vérifié et un vérifié. |
| **9.2 Suivre les kg vérifiés disponibles à la vente** | Création de `lot_proof_balances` (AD-35), alimentée par les réactions `ProofAccepted`, `ProofContested` et `ProofConfirmed`, idempotentes. `CHECK 0 ≤ kg_taken ≤ kg_total`. Le vendeur voit ses kg disponibles par Type de déchet et Zone. |
| **9.3 Constituer un Lot à partir de kg vérifiés** | `POST /v1/lots` à partir de Preuves (`proof_id`, kg) : prélèvement conditionnel (AD-35), 409 `kg_not_available`. Test de 20 prélèvements concurrents. Une Preuve contestée est refusée. Le Lot est `available`. `lot.create` est audité. |
| **9.4 Consulter les Lots disponibles** | Recycleur vérifié seulement. Filtres Type de déchet, quantité minimale et Zone. Aucune identité ni aucun contact du vendeur. Pagination par curseur. |
| **9.5 Réserver un Lot et obtenir le contact du vendeur** | `POST /v1/lots/{id}/reservations` (`Idempotency-Key`) : `available → reserved`, une réservation concurrente reçoit 409. Le contact du vendeur n'est donné qu'après la réservation (`orgs.service.get_contact()`). Le vendeur est notifié. L'annulation remet le Lot `available`. |
| **9.6 Confirmer la réception et la vente d'un Lot** | Le Recycleur confirme la réception, puis le vendeur confirme la vente (`POST /v1/sales/{id}/confirm` : prix en entier FCFA, date). Le Lot passe `sold` et devient immuable, et `sold_kg` est fixé. Une contestation ouvre un Litige (12.5). |
| **9.7 Enregistrer la commission d'une vente** | La Commission est calculée depuis le paramètre `*_bps` du Contrat (10.2) et figée sur `sales`. Aucune valeur dans le code ni dans le seed hors `is_demo`. Rien n'est encaissé (AD-34). |
| **9.8 Suivre les Lots, réservations et ventes** | Console du vendeur (ses Lots) et du Super Admin (tous). Export CSV. Un Lot dont un Élément est gelé (Preuve contestée) apparaît `withdrawn` avec son motif. |

#### E-11 · Nouvel Epic 10 : Organisations et contrats (P2)

Intro : « Le Super Admin gère les Organisations clientes, leurs Contrats et leurs Factures en états, et pilote la plateforme. » FR-50 à FR-54. Prérequis : 2.13, 2.14, 2.15.

| Story | Critères d'acceptation (esquisse) |
|---|---|
| **10.1 Gérer le cycle de vie d'une organisation cliente** | Modifier une Organisation, la suspendre ou la réactiver (`OrganizationSuspended` : plus de nouveau Signalement, de Demande ni de Mission ; lecture de l'historique gardée). Audit `org.update` et `org.suspend`. |
| **10.2 Enregistrer les contrats et abonnements** | Table `contracts` (`orgs`) : offre, `monthly_price_xof`, dates, statut, et paramètres `coordination_fee_*`, `collector_payout_*`, `commission_bps`. Saisie par le Super Admin seul. Aucune valeur dans le dépôt (test : `.env.example` et le seed hors démo n'en contiennent aucune). |
| **10.3 Émettre les factures et suivre leurs échéances** | La tâche `finance.issue_invoices` (mensuelle, idempotente par contrat et période) crée des Factures `émise`. Le Super Admin les marque `payée` avec une référence. Audit. Aucune passerelle. |
| **10.4 Signaler les factures en retard** | `finance.mark_overdue_invoices` (quotidienne, horloge simulée) : `émise → en retard` après l'échéance, et une alerte part. La console du Super Admin liste les retards. |
| **10.5 Tableau de bord plateforme du Super Admin** | Indicateurs SM-B1 à SM-B8 par période et par Organisation (`v_finance_facts`, `v_lot_facts`). Données de démonstration étiquetées. |
| **10.6 Paramètres de la plateforme et journal d'audit global** | Paramètres non commerciaux (bornes de fraude, délais), en base et audités. Journal d'audit global filtrable par Organisation, action et période. |

#### E-12 · Nouvel Epic 11 : Espace entreprise (P2)

Intro : « Le Gestionnaire d'entreprise gère ses Sites, déclare ses déchets, demande des collectes ponctuelles ou régulières, et suit preuves et quantités jusqu'au rapport mensuel. » FR-56 à FR-61. Prérequis : Epics 2 et 5, 10.2, 12.1 (pour les montants prévus).

| Story | Critères d'acceptation (esquisse) |
|---|---|
| **11.1 Gérer les sites de l'entreprise** | `sites` (`enterprise`) : nom, Position dans la Zone active, contact du site chiffré. CRUD dans la Portée. Test d'isolement entre deux entreprises. |
| **11.2 Déclarer les déchets d'un site** | `site_waste_declarations` : Types de déchet et volume estimé par période. Historique conservé. |
| **11.3 Demander une collecte ponctuelle** | `POST /v1/collection-requests` (`Idempotency-Key`) : la Demande passe `requested` et une Mission d'Origine `collection_request` est créée par `missions.service`. Migration d'expansion AD-36 (`collection_request_id`, `CHECK`, index d'exclusivité). |
| **11.4 Programmer des collectes régulières** | `collection_schedules` (fréquence, Site, Types de déchet). La tâche `enterprise.generate_scheduled_requests` est idempotente par échéance (horloge simulée). |
| **11.5 Voir les Missions d'entreprise dans l'espace Collecteur** | Sur l'écran 5, les Demandes éligibles apparaissent avec un pictogramme « Entreprise ». La Position est arrondie avant l'acceptation (AD-10). L'acceptation, la Preuve et l'historique sont identiques. |
| **11.6 Suivre les demandes, les prestataires et les preuves** | La console de l'entreprise montre l'état de chaque Demande, le Collecteur (nom affiché et état vérifié, jamais le numéro), les photos de Preuve (URL signées) et les kg vérifiés par Site. Une contestation ouvre un Litige (12.5). |
| **11.7 Rapport mensuel de l'entreprise** | CSV et PDF : kg vérifiés par Type de déchet et Site, Missions terminées, Preuves contestées. Aucune donnée personnelle. Audit `export.aggregate`. |
| **11.8 Rapport mensuel de la commune ou de l'opérateur** | Même format, par quartier, à partir des vues de l'Epic 7. |

#### E-13 · Nouvel Epic 12 : Finance terrain (P2)

Intro : « Chaque Mission porte ses frais et sa rémunération prévus ; chaque Preuve acceptée crée un Montant dû ; le payeur confirme le paiement mobile money ; le Collecteur voit et conteste ; les Litiges sont tranchés. TerangaCycle ne détient aucun fonds (AD-34). » FR-62 à FR-67. Prérequis : 5.6, 5.14, 10.2.

| Story | Critères d'acceptation (esquisse) |
|---|---|
| **12.1 Fixer les frais et la rémunération prévus d'une Mission** | Migration d'expansion `missions.planned_fee_xof` et `planned_payout_xof` (nullable pour l'historique). À la création, les valeurs viennent du Contrat de l'Organisation et sont figées. Un changement de Contrat ne les modifie pas (test). |
| **12.2 Créer le montant dû au Collecteur à la Preuve acceptée** | Réaction `ProofAccepted` → `payouts(mission, collector, amount_xof, payer_org, status = due)`, idempotente (unique par Mission). Audit `payout.create`. |
| **12.3 Confirmer un paiement mobile money** | Le payeur (Administrateur d'organisation ou Gestionnaire d'entreprise) passe `due → paid` avec `payment_reference`, `paid_at` et `confirmed_by`. La référence est masquée dans les journaux. Aucune route de transfert. Transitions testées couple par couple. |
| **12.4 Voir ses montants dus et ses paiements confirmés** | Écran mobile du Collecteur [HORS MAQUETTE] : liste et totaux dû et payé. « Contester » (motif obligatoire) passe le Montant `contested` et ouvre un Litige. |
| **12.5 Ouvrir et trancher un litige** | `disputes(object_type ∈ {proof, payout, sale}, object_id, reason, status, decision, decided_by)`. Décision motivée par le Super Admin. Les effets passent par événements : Montant `due` ou `paid`, Preuve `contestée` ou confirmée. Audit `dispute.open` et `dispute.decide`. |
| **12.6 Suivre les montants dus, payés et contestés** | Console de l'Organisation (sa Portée) et du Super Admin (toutes). Filtres et export CSV, sans Référence de paiement complète. |

#### E-14 · Nouvel Epic 13 : Données ouvertes et interopérabilité — **proposé, à valider**

Statut : proposé par le cadrage, non validé. À ne pas planifier avant validation ([!] n° 8). Il viendrait après le pilote.

| Story | Esquisse |
|---|---|
| 13.1 Exports en formats standards documentés | Schéma publié (CSV, GeoJSON), licence ouverte des données agrégées, données déjà anonymisées (FR-33). |
| 13.2 API en lecture pour partenaires | Jetons de partenaire en lecture seule, limités à des agrégats par Zone et période. Débit limité. Audités. |
| 13.3 Documentation publique des jeux de données | Dictionnaire des champs, fréquence de mise à jour, limites connues. |

---

### 4.4 UX

Aucun document `bmad-ux` n'existe, et la maquette est figée. Les écrans suivants s'ajoutent à la liste « hors maquette » du PRD §7, avec les jetons et la police existants : sélecteur d'Organisation ; console (gabarit, navigation) ; Organisations (Super Admin) ; Membres d'une Organisation ; Alertes de fraude ; Sites, Demandes, Programmes et Rapports (entreprise) ; Contrats, Factures et Tableau de bord plateforme ; Montants du Collecteur (mobile) ; Lots, Réservations et Ventes ; Litiges. Voir le [!] n° 9.

### 4.5 `sprint-status.yaml`

**S-1 · Correction d'état (hors décision)** : `1-9-photographier-le-dépôt-en-version-légère-et-sans-métadonnées: in-progress` → `done`. La PR n° 13 est fusionnée sur `main`. `last_updated` passe au 25/11/2026.

**S-2 · Epic 1** : ajouter après `1-17-…` (sous réserve du [!] n° 6) :

```yaml
  1-18-produire-la-miniature-d-une-photo-de-signalement: backlog
```

**S-3 · Epic 2** : insérer dans l'ordre d'exécution (après `2-4-…`, avant `2-5-…`) :

```yaml
  2-13-organisations-et-appartenances-par-rôle: backlog
  2-15-console-web-chargée-à-part-de-l-espace-mobile: backlog
```

Puis, après `2-11-…` :

```yaml
  2-14-super-admin-minimal-de-la-plateforme: backlog
```

**S-4 · Epic 3** : retirer `3-8-sélecteur-des-types-de-déchet-piloté-par-la-proposition-ia` (fusionnée dans 3.12). Placer en tête de l'Epic 3, sous le commentaire `# Piste hackathon`, les entrées 3-1, 3-9, 3-11 et 3-12, puis les autres sous `# P4`.

**S-5 · Epic 4** : commentaire `# P4` sur `4-6-…` et `4-11-…`.

**S-6 · Epic 5** : ajouter `5-16-alertes-de-fraude-pour-le-personnel-et-le-super-admin: backlog`.

**S-7 · Epic 9** : remplacer les clés 9-1 à 9-5 par :

```yaml
  epic-9: backlog   # P3 · Place de marché (réécrit le 25/11/2026)
  9-1-vérifier-un-recycleur: backlog
  9-2-suivre-les-kg-vérifiés-disponibles-à-la-vente: backlog
  9-3-constituer-un-lot-à-partir-de-kg-vérifiés: backlog
  9-4-consulter-les-lots-disponibles: backlog
  9-5-réserver-un-lot-et-obtenir-le-contact-du-vendeur: backlog
  9-6-confirmer-la-réception-et-la-vente-d-un-lot: backlog
  9-7-enregistrer-la-commission-d-une-vente: backlog
  9-8-suivre-les-lots-réservations-et-ventes: backlog
  epic-9-retrospective: optional
```

**S-8 · Nouveaux Epics 10 à 12** :

```yaml
  epic-10: backlog   # P2 · Organisations et contrats
  10-1-gérer-le-cycle-de-vie-d-une-organisation-cliente: backlog
  10-2-enregistrer-les-contrats-et-abonnements: backlog
  10-3-émettre-les-factures-et-suivre-leurs-échéances: backlog
  10-4-signaler-les-factures-en-retard: backlog
  10-5-tableau-de-bord-plateforme-du-super-admin: backlog
  10-6-paramètres-de-la-plateforme-et-journal-d-audit-global: backlog
  epic-10-retrospective: optional

  epic-11: backlog   # P2 · Espace entreprise
  11-1-gérer-les-sites-de-l-entreprise: backlog
  11-2-déclarer-les-déchets-d-un-site: backlog
  11-3-demander-une-collecte-ponctuelle: backlog
  11-4-programmer-des-collectes-régulières: backlog
  11-5-voir-les-missions-d-entreprise-dans-l-espace-collecteur: backlog
  11-6-suivre-les-demandes-les-prestataires-et-les-preuves: backlog
  11-7-rapport-mensuel-de-l-entreprise: backlog
  11-8-rapport-mensuel-de-la-commune-ou-de-l-opérateur: backlog
  epic-11-retrospective: optional

  epic-12: backlog   # P2 · Finance terrain (aucune détention de fonds)
  12-1-fixer-les-frais-et-la-rémunération-prévus-d-une-mission: backlog
  12-2-créer-le-montant-dû-au-collecteur-à-la-preuve-acceptée: backlog
  12-3-confirmer-un-paiement-mobile-money: backlog
  12-4-voir-ses-montants-dus-et-ses-paiements-confirmés: backlog
  12-5-ouvrir-et-trancher-un-litige: backlog
  12-6-suivre-les-montants-dus-payés-et-contestés: backlog
  epic-12-retrospective: optional
```

**S-9 · Ordre des blocs et priorités** : ordonner les blocs par priorité, avec un commentaire `# Pn` sur chaque ligne `epic-N` : 1 (P0) ; 2, 3 (piste hackathon), 4, 5, 7 (P1) ; 8 (démo, puis sortie de P1) ; 10, 11, 12 (P2) ; 9 (P3) ; 6 (P4). L'Epic 13 n'est **pas** ajouté avant sa validation.

**S-10 · `action_items`** : ajouter, avec des rôles comme responsables et sans nom de personne :

- « Appliquer la Sprint Change Proposal du 25/11/2026 au PRD, à l'épine, à `epics.md` et à `epic-1-context.md` » (responsable : PM et architecte ; ouvert).
- « Trancher les points [!] n° 1 à 10 de la proposition » (responsable : responsable produit ; ouvert).
- L'action existante sur le Modèle « prototype » (Epic 3) reste ouverte et liée au [!] n° 1.

### 4.6 Autres artefacts

| Artefact | Modification |
|---|---|
| `epic-1-context.md` | À régénérer : module `orgs`, propriété d'`organizations`, critères de 1.11, 1.14 et 1.17, story 1.18. |
| `backend/pyproject.toml` (import-linter) | Les conteneurs `orgs`, `enterprise` et `finance` et les flèches A-2 sont ajoutés **par les stories** (1.11, puis 11.x et 12.x), pas maintenant. |
| `.env.example` | Réglages non commerciaux (bornes de fraude, délais) ajoutés par les stories. **Aucune** valeur commerciale. |
| `infra/Caddyfile` | Retour vers l'application pour `/console/*` (story 2.15). |
| `README.md` | Description du produit à aligner sur la vision 2.0 (sans prix ni récit investisseurs). |
| `docs/cahier-des-charges.md`, `docs/dossier-technique.md` | Ajouter une mention « remplacé par le PRD v2.0 pour la vision, les rôles et les non-objectifs ». |

---

## 5. Passation et mise en œuvre

### 5.1 Classification du périmètre : **Majeur**

Le changement redéfinit la vision, lève un non-objectif structurant, ajoute trois modules, six AD (31 à 36) et trois epics, réécrit un epic et rebat les priorités. Une replanification par le PM et l'architecte est nécessaire avant la reprise du développement au-delà de la story 1.10.

### 5.2 Destinataires et responsabilités

| Rôle (agent BMAD) | Responsabilités |
|---|---|
| **PM** (`bmad-agent-pm`) | Appliquer P-1 à P-14 (PRD v2.0, addendum). Faire trancher les [!] produit (n° 1 à 5, 7, 8, 10). Valider l'Epic 13 ou le retirer. |
| **Architecte** | Appliquer A-1 à A-10 (AD-31 à AD-36, AD amendées). Valider les choix techniques par défaut : repli vers l'Organisation plateforme, `X-Org-Id`, port `MembershipLoader`, projection `lot_proof_balances`. |
| **PO et Scrum Master** | Appliquer E-1 à E-14 dans `epics.md`, S-1 à S-10 dans `sprint-status.yaml`, régénérer `epic-1-context.md`, redécouper si besoin. |
| **Développeur** | Poursuivre avec la story **1.10 (inchangée)** pendant la mise à jour. Ne commencer la 1.11 qu'une fois E-2 appliqué. |
| **UX** (si le [!] n° 9 est retenu) | Spécification légère de la console avant P2. |

### 5.3 Séquencement

1. Approbation de cette proposition (étape 5), avec les [!] tranchés ou leurs choix par défaut acceptés.
2. PRD v2.0 et épine v2.0 (en parallèle).
3. `epics.md`, puis `sprint-status.yaml`, puis `epic-1-context.md`.
4. Développement : 1.10 → 1.11 (modifiée) → 1.12 à 1.18 → Epic 2 dans l'ordre E-3 → P1.

### 5.4 Critères de réussite de la mise en œuvre

- Le PRD v2.0 ne contient plus le non-objectif multi-commune. Il contient FR-44 à FR-71, NFR-18 et les lots P0 à P4.
- L'épine contient AD-31 à AD-36, et les AD amendées sont cohérentes (aucune mention de `users.role` ni de `collector_profiles`).
- `epics.md` contient les Epics 9 (réécrit), 10, 11 et 12, et la carte de couverture de FR-44 à FR-71 est complète.
- `sprint-status.yaml` est valide en YAML : 1.9 `done`, nouvelles clés, ordre par priorité.
- **Contrôle de confidentialité** : une recherche dans `_bmad-output/` ne trouve aucun montant commercial, aucun taux, aucun nom de personne, aucun lien de maquette ni aucune coordonnée personnelle.
- Story 1.11 livrée : test « organisation responsable » vert, import-linter vert avec `orgs`.
- Fin de P1 : test d'isolement entre organisations bloquant en CI et vert sur toutes les routes.

---

## Annexe A — Checklist de navigation du changement (mode Batch)

| # | Point | Statut | Constat |
|---|---|---|---|
| 1.1 | Story déclencheuse | [x] | Aucune : pivot validé le 25/11, entre 1.9 (terminée) et 1.10 (prochaine). |
| 1.2 | Nature du problème | [x] | Pivot stratégique et nouvelles exigences des parties prenantes (§1.2). |
| 1.3 | Preuves | [x] | Cadrage validé ; état du code (`zones` seule) ; PRD §8 ; addendum B.1.16 ; AD-2 (§1.3). |
| 2.1 | Epic en cours (1) | [x] | Réalisable avec 1.11, 1.14 et 1.17 modifiées et 1.18 ajoutée. Rien à défaire. |
| 2.2 | Changements au niveau des epics | [x] | 2 enrichi ; 3 scindé ; 4, 5 et 7 cloisonnés ; 9 réécrit ; 10 à 12 nouveaux ; 13 proposé. |
| 2.3 | Epics futurs | [x] | Tous revus (§2.1). Dépendance 4.1 → 3.14 cassée par le passage de 3.14 en P4 : corrigée (E-5). |
| 2.4 | Epics obsolètes ou nouveaux | [x] | Aucun obsolète. L'Epic 9 change de nature. Trois epics nouveaux, un proposé. |
| 2.5 | Ordre et priorités | [x] | Lots P0 à P4 et piste hackathon ; Epic 6 en P4 ; 5.12 à 5.15 et 2.12 avancées en P1. |
| 3.1 | PRD | [x] | Vision, rôles, non-objectifs, FR, NFR, périmètre, indicateurs et questions (P-1 à P-14). |
| 3.2 | Architecture | [x] | Six AD nouvelles, onze amendées, conventions et différé (A-1 à A-10). |
| 3.3 | UX | [!] | Pas de spécification UX ; nombreux écrans de console hors maquette ([!] n° 9). |
| 3.4 | Autres artefacts | [x] | CI (import-linter, budget mobile, isolement), Caddy, `.env.example`, README, docs sources (§4.6). |
| 4.1 | Option 1 · Ajustement direct | Viable en partie | Effort moyen, risque moyen ; insuffisant seul. |
| 4.2 | Option 2 · Retour arrière | Non viable | Rien à défaire. |
| 4.3 | Option 3 · Revue du MVP | Viable | Effort élevé, risque moyen ; nécessaire. |
| 4.4 | Voie retenue | [x] | Hybride 3 + 1 (§3.2). |
| 5.1 à 5.5 | Composantes de la proposition | [x] | Sections 1 à 5 de ce document. |
| 6.1 | Revue de la checklist | [x] | Tous les points traités ; les [!] sont listés en annexe B. |
| 6.2 | Exactitude de la proposition | [x] | Relue pour la cohérence des numéros (FR-44 à FR-71, AD-31 à AD-36, clés de `sprint-status.yaml`) et pour la confidentialité. |
| 6.3 | Approbation explicite | [x] | Approuvée le 25/11/2026, avec trois amendements (section « Décision d'approbation »). |
| 6.4 | Mise à jour de `sprint-status.yaml` | [x] | Appliquée le 25/11/2026 (S-1 à S-10, plus les amendements : Epic 6 dans la piste hackathon, Epic 13 en post-pilote). |
| 6.5 | Passation confirmée | [x] | Artefacts mis à jour ; prochaine story : 1.10. |

## Annexe B — Points [!] à trancher

Chaque point indique un choix par défaut, proposé si la responsable produit ne tranche pas autrement.

1. **IA de la démo et Modèle entraîné.** Le cadrage limite l'IA de démo à quatre stories (3.1, 3.9, 3.11, 3.12) et place le pipeline `ml/` (3.4 à 3.7) en P4. Or la décision du 24/11 (action ouverte) prévoit de montrer le vrai Modèle entraîné, étiqueté « prototype ». *Par défaut :* le Modèle prototype entraîné hors story est publié par le contrat de 3.1 (manifeste `kind: trained`, étiqueté « prototype » à l'écran). Les seuils de SM-2, la Fiche du Modèle et la publication conditionnelle restent en P4.
2. **Hors-ligne en P4.** L'Epic 6 passe en P4. SM-1 (« signalement hors-ligne → … ») et SM-4 ne sont donc plus des indicateurs de la démo, et la séquence « mode avion » de la vidéo (8.8) disparaît. *Par défaut :* SM-1 devient « signalement → modération → Mission → Preuve → Tableau de bord, avec deux organisations cloisonnées », et SM-4 passe en P4.
3. **Éligibilité aux Missions d'entreprise.** Qui peut prendre une Demande d'entreprise ? *Par défaut :* les Collecteurs vérifiés par l'Organisation plateforme (vivier TerangaCycle) et par tout opérateur désigné comme prestataire dans le Contrat de l'entreprise.
4. **Vendeur d'un Lot.** Le Collecteur, ou l'Organisation (commune ou opérateur) qui a contrôlé les Preuves ? *Par défaut :* l'Organisation de la Mission. Les Lots déclarés librement par un Collecteur disparaissent.
5. **Effet d'une Preuve contestée sur la rémunération.** *Par défaut :* le Montant dû passe `contesté` (ni dû ni payé) et un Litige s'ouvre automatiquement. Un Lot non vendu qui la contient est retiré ; un Lot vendu ouvre un Litige.
6. **Story 1.18 (miniature sortie de 1.11).** Elle compense l'alourdissement de 1.11 sans renuméroter. *Par défaut :* oui.
7. **Nettoyage de confidentialité de l'existant.** Le PRD (§0, §11), l'addendum (§G : prénoms, messages de pitch et modèle économique), `epics.md` (responsables) et `sprint-status.yaml` (responsables des actions) contiennent des prénoms et des éléments de pitch. La règle s'applique à tous les fichiers du dépôt. *Par défaut :* remplacer les prénoms par des rôles et retirer la section « Pitch » de l'addendum à l'application de cette proposition. L'historique Git n'est pas réécrit.
8. **Epic 13 (données ouvertes).** Proposé par le cadrage, non validé. *Par défaut :* ne pas l'inscrire dans `sprint-status.yaml` avant sa validation.
9. **Spécification UX de la console.** Sans document UX, une vingtaine d'écrans de console sont hors maquette. *Par défaut :* une spécification UX légère (gabarit de console, tableaux, formulaires, états vides), avant le début de P2. P1 se contente du gabarit de 2.15.
10. **« SMS » en P4.** *Par défaut :* il s'agit du canal citoyen (signalement et notifications par SMS). La passerelle SMS de l'OTP reste nécessaire pour les comptes réels dès la sortie de P1 (Q19).
