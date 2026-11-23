---
title: "Triage des relectures — PRD TerangaCycle AI"
created: 2026-11-23
status: à appliquer par le rédacteur ; prd.md et addendum.md non modifiés
---

# Triage des relectures du PRD TerangaCycle AI

## 0. Mode d'emploi

**Rapports sources (abréviations) :**
- **RUB** : `review-rubric.md` (revue qualité) ;
- **CAH** : `reconcile-cahier.md` (cahier des charges) ;
- **DT** : `reconcile-dossier-technique.md` (dossier technique) ;
- **PB** : `reconcile-proposal-brief.md` (Project Proposal et handoff brief) ;
- **AUD** : `reconcile-audit.md` (audit du 23/11).

**Décisions déjà validées par Mia, non rouvertes :** MobileNetV3-Large par défaut (Small si > 3 s), F1 macro principal avec top-1 publiée, rayon de 5 km réglable de 1 à 10, pilote à 60 % sur 6 mois, pitch de 1 min 30, Docker Compose en fin de hackathon, vert `#187A50`, Lots de matière après H48, FR-4 à H24, clé Figma retirée du dépôt. Seuls leurs effets de bord sont traités.

**Règle de tri :** ce qui sert la démo ou le pilote entre dans le PRD ; le reste devient un non-objectif ou une question ouverte. Le « comment » va dans l'addendum.

**Décisions possibles :**
- `AUTOFIX` : correction évidente ;
- `DÉCISION-PAR-DÉFAUT` : choix raisonnable que le rédacteur prend puis journalise dans `.memlog.md` ;
- `QUESTION-MIA` : arbitrage que seule Mia peut trancher ;
- `DIFFÉRER` : question ouverte, avec un responsable ;
- `IGNORER` : avec sa raison.

**Numérotation :** FR-1 à FR-40 et NFR-1 à NFR-14 sont conservés. Les nouveautés sont FR-41 à FR-43, NFR-15 à NFR-17, SM-9, UJ-6 et §9.3. Aucune renumérotation n'est nécessaire.

**Ordre d'application conseillé :**
1. Obtenir les réponses aux 3 QUESTION-MIA. T-03, T-13 et T-14 changent le Glossaire, FR-7, FR-14 et §9.
2. Appliquer le Glossaire (T-33 et les ajouts cités dans chaque constat).
3. Appliquer les FR et NFR.
4. Appliquer les mises à jour mécaniques (§3).
5. Appliquer l'addendum.
6. Journaliser dans `.memlog.md`.

### Récapitulatif

| ID | Sév. | Constat | Décision | Sources |
|---|---|---|---|---|
| T-01 | high | Suivi du Citoyen anonyme non spécifié | DÉCISION-PAR-DÉFAUT | RUB, CAH E7/US-01/US-05, DT E-D1, PB A8 |
| T-02 | high | Indicateurs du Tableau de bord incompatibles avec le Statut ; « Kg valorisés » ; kg par matière | DÉCISION-PAR-DÉFAUT | RUB, CAH US-16/E5/E6, PB A7/A15/§4, DT E-D7 |
| T-03 | high | Autorité sur le Type de déchet : Citoyen, serveur ou Modérateur | **QUESTION-MIA** | PB B1/A6, RUB, PB §6 |
| T-04 | high | Aucun contrôle humain des Preuves de collecte ; SM-C3 non mesurable | DÉCISION-PAR-DÉFAUT | RUB, DT E-S7, AUD §7 |
| T-05 | high | Pas de Statut de Mission ; transitions et renvois de Mission non spécifiés ; pas d'expiration | DÉCISION-PAR-DÉFAUT | RUB, DT E-I1/E-I2 |
| T-06 | high | Journal d'audit : actions non listées, pas de trace de chaque changement de Statut, « non modifiable » non testé | DÉCISION-PAR-DÉFAUT | PB A3, RUB, DT E-S5, AUD S10 |
| T-07 | high | Détection des doublons par distance et par délai promise au jury, absente | DÉCISION-PAR-DÉFAUT | PB A2 |
| T-08 | high | Preuve de collecte hors-ligne : sujet passé sous silence | DÉCISION-PAR-DÉFAUT | RUB |
| T-09 | high | Pilote sans sauvegarde, sans supervision, avec un plan de sortie invérifiable | DÉCISION-PAR-DÉFAUT | CAH E2/E17, DT E-S3/E-O1/E-O2/E-X1, RUB, PB A11 |
| T-10 | high | Consentement au réentraînement : export non filtré, pas de retrait, anonymes non couverts | DÉCISION-PAR-DÉFAUT | DT E-C1/E-C3, AUD §4, PB A10 |
| T-11 | high | Visages et plaques : la photo reste conservée | DÉCISION-PAR-DÉFAUT | CAH E3, AUD S9, DT E-C4 |
| T-12 | high | Aucun plan B de démo ; sondes non définies | DÉCISION-PAR-DÉFAUT | CAH E1, DT E-H1, AUD S11 |
| T-13 | high | Ordre des portes : hors-ligne à H60, historique hors MVP, Modèle factice à H24 | **QUESTION-MIA** | RUB, PB A5/§3.3/§3.5 |
| T-14 | high | Périmètre géographique du pilote et configuration par commune promise au jury | **QUESTION-MIA** | PB A1, RUB, DT E-D8/§2.2-33 |
| T-15 | high | SM-2 et SM-3 non reproductibles ; calibration, fiche du Modèle et réentraînement absents | DÉCISION-PAR-DÉFAUT | DT E-A1/E-A2/E-A4/E-L1, RUB, CAH NF-15, PB §3.3 |
| T-16 | medium | Décisions validées encore marquées comme hypothèses (§6.3, SM-2, §11 Q1, §12) | AUTOFIX | RUB, AUD, PB §6 |
| T-17 | medium | Positions précises : contradiction entre §6.1 et FR-24 ; FR-34 sans seuil | DÉCISION-PAR-DÉFAUT | RUB, DT E-D5, AUD S8 |
| T-18 | medium | Géorepérage de 150 m sans règle de précision GPS ; message d'erreur flou | DÉCISION-PAR-DÉFAUT | RUB, AUD §7, PB §4 |
| T-19 | medium | « Poids mesuré » alors que les Collecteurs n'ont pas de balance | DÉCISION-PAR-DÉFAUT | CAH E10/US-10 |
| T-20 | medium | Questions ouvertes sans responsable ni échéance | AUTOFIX | RUB, AUD #4/§4, PB |
| T-21 | medium | Dépôt public sans licence | DIFFÉRER | CAH E11, AUD §4/§6, PB A12 |
| T-22 | medium | Collecteurs informels au pilote : incitation, enrôlement, critères de vérification | DIFFÉRER | RUB, PB §4, CAH E14 |
| T-23 | medium | Taille du Modèle non bornée ; premier usage sans Modèle en cache | DÉCISION-PAR-DÉFAUT | RUB, CAH E12, DT E-D9 |
| T-24 | medium | Signalements créés en direct pendant la démo non étiquetés | DÉCISION-PAR-DÉFAUT | RUB |
| T-25 | medium | FR-14 : traitement asynchrone encore en hypothèse, file non bornée | AUTOFIX | AUD S12, DT E-A3/§2.1 |
| T-26 | medium | File de modération : drapeaux non testables, Classification serveur en attente | AUTOFIX | AUD #7, RUB, PB A6 |
| T-27 | medium | Sessions, jetons, suspension « immédiate », second facteur du Personnel | DÉCISION-PAR-DÉFAUT | AUD S4/S5/§7, DT E-S1/E-S8 |
| T-28 | medium | Limites de débit sans valeur et contournables | DÉCISION-PAR-DÉFAUT | AUD S6/S7/§7, DT E-R1/E-R2 |
| T-29 | medium | Sécurité : NFR-8, NFR-9 et NFR-10 incomplètes ; rien sur les données au repos ni sur la base | AUTOFIX | CAH E4, DT E-S2/E-S4/E-S6, AUD S10/§3/§7 |
| T-30 | medium | Suppression des données et purge : écart avec US-22, purge non testable | DÉCISION-PAR-DÉFAUT | CAH E8/US-22, DT E-C1/E-C2, AUD §4, PB A9 |
| T-31 | medium | Accessibilité : Rouge et Jaune en échec ; pictogrammes ; clavier ; contrôle en CI | DÉCISION-PAR-DÉFAUT | PB §3.4, AUD §5, CAH NF-12, DT E-D4 |
| T-32 | medium | Écrans exigés par le PRD mais absents de la maquette figée | AUTOFIX | PB §3.4/§6 |
| T-33 | medium | Termes et états employés hors Glossaire | AUTOFIX | RUB |
| T-34 | medium | Addendum : schéma, contrat d'API, prétraitement IA, code hors-ligne | AUTOFIX | DT §2, AUD S1/§4 |
| T-35 | medium | Addendum : sécurité, exploitation, hygiène du dépôt | AUTOFIX | DT §2.2, AUD §3/§6 |
| T-36 | low | Conséquences testables manquantes dans FR-7, FR-8, FR-9, FR-19, FR-24 et FR-30 | AUTOFIX | AUD #3/#8/#9/§3, DT E-I3/E-D3, CAH P14, PB A4, RUB |
| T-37 | low | Feuille de route et non-objectifs : wolof, SMS, points, tuiles | DÉCISION-PAR-DÉFAUT | CAH E9/E18, DT E-D6/E-C5, PB A16/A17 |
| T-38 | low | UJ inégales, Awa incohérente, Vision et ton | AUTOFIX | RUB, CAH P14, PB §4 |
| T-39 | low | Ajouts produit ou outillage sans usage pour la démo ni le pilote | IGNORER | CAH E5/E6/E16, DT E-D2/E-D7/E-O1/E-O3/§2.2-21 |
| T-40 | low | Points hors du champ d'un PRD | IGNORER | CAH E13/E14/E15, RUB, PB §4 |

---

## 1. Constats et décisions

### Sévérité high

#### T-01 · Suivi du Citoyen anonyme non spécifié

- **Sources :** RUB (high), CAH E7, US-01 et US-05, DT E-D1 (H), PB A8.
- **Constat :** dans UJ-1, Awa est anonyme et voit « Validé » puis « Collecté ». Pourtant :
  - FR-20 ne vise que « ses Signalements » ;
  - FR-21 ne notifie que le Citoyen connecté ;
  - FR-3 ne dit pas ce que possède un anonyme ;
  - l'affichage du Numéro de suivi n'est exigé nulle part.

  Une consultation par le seul Numéro de suivi (séquentiel) permettrait d'énumérer tous les Signalements.
- **Décision :** DÉCISION-PAR-DÉFAUT. Le suivi anonyme est lié à l'appareil par un Identifiant d'appareil secret. Il n'y a jamais de consultation par le seul Numéro de suivi, ni de push pour un anonyme. Une réinstallation fait perdre la liste, et cette perte est assumée.
  *Raison : c'est le mécanisme le moins coûteux qui tient UJ-1 sans ouvrir de faille d'énumération.* Le « Code de suivi anonyme » n'est pas retenu : ce serait un secret de plus à gérer, et la création de compte couvre le suivi durable.
- **Emplacements et textes :**

§3 Glossaire, après « Identifiant client » :
```markdown
- **Identifiant d'appareil** : secret aléatoire généré à l'installation de la PWA ; il rattache à l'appareil les Signalements d'un Citoyen anonyme. Il n'est jamais affiché ni renvoyé par le serveur.
```

FR-3, ajouter aux Conséquences :
```markdown
- Un Citoyen anonyme ne possède que les Signalements créés avec son Identifiant d'appareil. Un Signalement n'est jamais consultable à partir de son seul Numéro de suivi.
```

FR-20, remplacer toute l'exigence :
```markdown
#### FR-20 : Suivi de ses Signalements

Un Citoyen voit la liste de ses Signalements, avec le Numéro de suivi, le Statut et la Frise de suivi (écrans 1 et 4). Un Citoyen connecté voit les Signalements de son compte ; un Citoyen anonyme voit ceux créés depuis son appareil. Réalise UJ-1.

**Conséquences :**
- Le Numéro de suivi s'affiche sur l'écran 4 dès la réception par le serveur ; avant, l'écran 4 affiche « en attente d'envoi ».
- Le Statut affiché se met à jour au plus 15 s après le changement, quand l'application est ouverte.
- Un Signalement `rejeté` affiche son motif.
- Un Citoyen anonyme qui réinstalle l'application ou efface les données du navigateur perd sa liste ; l'écran de consentement (FR-4) l'en informe et propose de créer un compte.
- Une requête venant d'un autre appareil, ou qui ne présente que le Numéro de suivi, ne reçoit aucune donnée du Signalement.
```

FR-21, remplacer toute l'exigence :
```markdown
#### FR-21 : Notification de changement

À l'ouverture de l'application, le Citoyen, connecté ou anonyme, voit chaque changement de Statut de ses Signalements survenu depuis sa dernière visite. Le Citoyen connecté reçoit aussi une notification push s'il l'a autorisée.

**Conséquences :**
- La notification indique le Numéro de suivi, le nouveau Statut et, pour `rejeté`, le motif.
- La notification push est émise au plus 1 min après le changement de Statut.
- Un Citoyen anonyme ne reçoit pas de notification push `[NON-GOAL pour le MVP]`.

**Hors périmètre :** notifications par SMS ou WhatsApp `[NON-GOAL pour le MVP]`.
```

UJ-1, ligne « Résolution », remplacer la dernière phrase par :
```markdown
Awa voit plus tard « Validé », puis « Collecté », en rouvrant l'application sur son téléphone.
```

---

#### T-02 · Indicateurs du Tableau de bord incompatibles avec le Statut ; « Kg valorisés » ; kg par matière

- **Sources :** RUB (high, et medium sur « Kg valorisés »), CAH US-16, E5 et E6, PB A7, A15 et §4 (honnêteté), DT E-D7.
- **Constat :** quatre défauts.
  - Avec « un et un seul Statut », le « Taux de traitement » (part des `validé` qui sont `collecté`) vaut toujours 0. Il en va de même pour SM-6.
  - L'origine du délai et la cohorte de la période ne sont pas fixées.
  - « Kg valorisés » additionne en réalité des kilos **collectés**.
  - Les kg par matière et les acteurs informels intégrés, promis au jury, ne sont pas affichés.
- **Décision :** DÉCISION-PAR-DÉFAUT, en cinq points :
  - lire les indicateurs dans l'historique des Statuts (« ayant atteint ») ;
  - définir la cohorte comme les Signalements **reçus par le serveur** pendant la période ;
  - faire partir le délai de la réception par le serveur ;
  - renommer l'indicateur « Kg collectés » ;
  - ajouter les kg par Type de déchet et les Collecteurs vérifiés actifs.

  *Raison : l'horloge de l'appareil n'est pas fiable hors-ligne ; les deux ajouts sont de simples requêtes et portent les piliers « Durable » et « Inclusive » devant le jury.* Journaliser : délai **médian** plutôt que moyen (écart avec le cahier).
- **Emplacements et textes :**

FR-31, remplacer toute l'exigence. Elle dépend de T-04 (contestée) et de T-19 (Poids déclaré).
```markdown
#### FR-31 : Indicateurs

L'Administrateur commune voit les indicateurs suivants sur une période choisie. La **cohorte** d'une période est l'ensemble des Signalements reçus par le serveur pendant cette période (horodatage serveur de réception). Réalise UJ-4.

| Indicateur | Définition |
|---|---|
| Nombre de Signalements | Signalements de la cohorte ; dont ayant atteint `validé`, dont `rejeté` |
| Délai médian | Médiane, sur les Signalements de la cohorte ayant atteint `collecté`, du délai entre la réception par le serveur et l'acceptation de la Preuve de collecte ; affiché avec le nombre de Signalements de la cohorte encore ouverts |
| Taux de traitement | Signalements de la cohorte ayant atteint `collecté` ÷ Signalements de la cohorte ayant atteint `validé`, à la date du calcul |
| Kg collectés | Somme des Poids déclarés des Preuves de collecte acceptées pendant la période et non `contestée` (FR-41), au total et par Type de déchet, avec la part `pesé` |
| Collecteurs vérifiés actifs | Collecteurs vérifiés ayant au moins une Preuve de collecte acceptée pendant la période |

Il voit aussi la répartition des Signalements de la cohorte par Type de déchet retenu.

**Conséquences :**
- « Ayant atteint » se lit dans l'historique des Statuts : un Signalement `collecté` compte parmi ceux ayant atteint `validé`.
- Sur un jeu d'essai de 10 Signalements ayant atteint `validé`, dont 6 `collecté`, le Taux de traitement affiché est 60 %.
- Un Signalement créé hors-ligne entre dans la cohorte de sa date de réception par le serveur.
```

§10, remplacer SM-5 et SM-6, puis ajouter SM-9 :
```markdown
- **SM-5** : Délai médian (FR-31) de moins de 24 h. Valide FR-24 à FR-29 et FR-31.
- **SM-6** : Taux de traitement (FR-31) d'au moins 60 %, calculé sur l'ensemble des Signalements reçus pendant les 6 mois du pilote. Valide FR-25, FR-29 et FR-31.
- **SM-9** : Kg collectés avec Preuve de collecte, par Type de déchet : suivi mensuel, sans cible. Valide FR-29 et FR-31.
```

UJ-4, « Déroulé », remplacer « écran 7 avec 4 indicateurs (Signalements du mois, délai médian, taux de traitement, kg valorisés) » par :
```markdown
écran 7 avec les indicateurs de FR-31 (Signalements du mois, Délai médian, Taux de traitement, Kg collectés par Type de déchet, Collecteurs vérifiés actifs)
```

Les autres occurrences de « valorisés » sont traitées au §3.

---

#### T-03 · Autorité sur le Type de déchet : Citoyen, serveur ou Modérateur — QUESTION-MIA

- **Sources :** PB B1 et A6 (M), RUB (medium, « Type retenu ambigu »), PB §6 (FR-13 « plus tard »).
- **Constat :** le brief dit « le résultat serveur fait foi, non falsifiable ». FR-14 fait pourtant passer la Correction du Citoyen avant le serveur, sans drapeau. Un client modifié peut donc imposer un type. Le Modérateur, de son côté, ne peut corriger que « plus tard », sans porte : il ne peut pas trancher un Désaccord IA.
- **Décision :** QUESTION-MIA. Cette règle du brief est notée « ne pas rouvrir sans Mia ».
- **Options :**
  - **A (recommandée).** Le Type de déchet retenu est fixé par le Modérateur à la validation. Il est pré-rempli avec le choix du Citoyen s'il en a fait un, sinon avec la Classification serveur. Le drapeau Désaccord IA est levé dès que le type venu de l'appareil diffère du serveur. Le Modérateur corrige à H48.
  - **B.** Statu quo : le choix du Citoyen fait foi, et l'on ajoute seulement le drapeau.
  - **C.** Le serveur fait toujours foi ; le choix du Citoyen n'est qu'une suggestion.
- **Texte prêt pour l'option A :**

§3 Glossaire, remplacer « Désaccord IA » et ajouter « Type de déchet retenu » :
```markdown
- **Désaccord IA** : le Type de déchet envoyé par l'appareil (Classification locale, ou choix du Citoyen) diffère de la Classification serveur.
- **Type de déchet retenu** : Type de déchet fixé par le Modérateur à la validation du Signalement ; c'est celui que voient les Collecteurs et que comptent les indicateurs.
```

§3 Glossaire, « Correction », remplacer par :
```markdown
- **Correction** : Type de déchet choisi par un humain (Citoyen à la création, Modérateur à la validation) qui diffère de la prédiction ; c'est un exemple étiqueté pour le réentraînement.
```

FR-13, remplacer la phrase d'énoncé par :
```markdown
Le Citoyen, à la création, et le Modérateur, à la validation (FR-23), peuvent corriger le Type de déchet en un toucher.
```

FR-14, remplacer la première conséquence par :
```markdown
- Le Type proposé au Modérateur est le choix du Citoyen s'il en a fait un, sinon la Classification serveur. Le Type de déchet retenu n'est fixé qu'à la validation (FR-23) : aucun Type envoyé par l'appareil ne devient définitif sans décision du Personnel.
```

FR-23, ajouter aux Conséquences :
```markdown
- En validant, le Modérateur confirme ou corrige le Type de déchet ; une correction est une Correction (FR-13) et est inscrite au Journal d'audit.
```

---

#### T-04 · Aucun contrôle humain des Preuves de collecte ; SM-C3 non mesurable

- **Sources :** RUB (high), DT E-S7 (H), AUD §7 (« échantillon » sans taux).
- **Constat :** §6.2 cite une « vérification par échantillon », et SM-C3 mesure « la part de Preuves contestées ». Pourtant aucune FR ne permet d'échantillonner ni de contester une Preuve. De plus, la même photo peut resservir d'une Mission à l'autre.
- **Décision :** DÉCISION-PAR-DÉFAUT. Créer FR-41, en *Should* avant le pilote et hors des portes du hackathon. L'échantillon porte sur 5 % des Preuves `[ASSUMPTION]`. Une Preuve contestée sort des Kg collectés, et la détection de photos identiques s'étend aux Preuves.
  *Raison : c'est le maillon « preuve » de la thèse, et il conditionne la crédibilité des kg au pilote ; il n'est pas utile pour la démo.*
- **Emplacements et textes :**

§3 Glossaire, après « Preuve de collecte » :
```markdown
- **Revue de Preuve** : état d'une Preuve de collecte acceptée au regard du contrôle par échantillon : `non revue`, `confirmée` ou `contestée`.
```

§4.8, nouvelle FR après FR-30 :
```markdown
#### FR-41 : Contrôler une Preuve de collecte par échantillon *(Should, avant le pilote)*

Chaque semaine, le système tire au hasard au moins 5 % des Preuves de collecte acceptées `[ASSUMPTION]`, et au moins une. Un membre du Personnel revoit chacune et la marque `confirmée` ou `contestée` ; le motif est obligatoire pour `contestée`.

**Conséquences :**
- Une Preuve `contestée` est exclue des Kg collectés (FR-31) et apparaît comme telle dans l'historique du Collecteur (FR-30) ; le Signalement reste `collecté`.
- Chaque revue est inscrite au Journal d'audit.
- Le Tableau de bord affiche la part de Preuves `contestée` parmi les Preuves revues ; elle mesure SM-C3.
- Une Preuve dont une photo est strictement identique à une photo déjà reçue (Signalement ou Preuve) est ajoutée d'office à l'échantillon.
```

§6.2, ligne « Fausses preuves », colonne Contrôle :
```markdown
FR-29 (150 m, horodatage serveur, photos), FR-41 (échantillon d'au moins 5 %, photos réutilisées)
```

SM-C3, remplacer par :
```markdown
- **SM-C3** : kg collectés par Mission. Des poids gonflés feraient monter l'indicateur ; on suit plutôt la part de Preuves `contestée` (FR-41). Il équilibre SM-5 et SM-6.
```

---

#### T-05 · Pas de Statut de Mission ; transitions et renvois de Mission non spécifiés ; pas d'expiration

- **Sources :** RUB (medium, « cycle de vie »), DT E-I1 (H), E-I2 (H) et E-I3.
- **Constat :** cinq lacunes.
  - Le refus 409 d'une transition interdite n'existe que pour la modération.
  - « terminée » n'est pas défini.
  - Aucune expiration n'est prévue : un Collecteur qui ne vient jamais bloque le Signalement en `assigné`, ce qui dégrade SM-5 et SM-6.
  - Une Preuve renvoyée après une coupure n'a pas de comportement défini.
  - FR-26 n'a aucune conséquence.
- **Décision :** DÉCISION-PAR-DÉFAUT. Le Statut de Mission prend quatre valeurs : `active`, `terminée`, `annulée`, `expirée`. Les transitions interdites sont refusées (409). Un renvoi idempotent rend le résultat existant. L'Administrateur commune peut annuler. L'expiration intervient à 48 h `[ASSUMPTION]` (FR-42, avant le pilote).
  *Raison : la base décide déjà « une Mission active » ; 48 h laisse une marge au-delà de la cible médiane de 24 h (SM-5).*
- **Emplacements et textes :**

§3 Glossaire, remplacer « Statut » et « Mission », puis ajouter « Statut de Mission » :
```markdown
- **Statut** : état d'un Signalement : `en attente de modération` → `validé` ou `rejeté` ; `validé` → `assigné` ; `assigné` → `collecté`, ou retour à `validé` si la Mission est `annulée` ou `expirée`. `rejeté` et `collecté` sont terminaux. Toute transition non prévue, de Statut ou de Statut de Mission, est refusée et ne modifie rien.
- **Mission** : prise en charge d'un Signalement `validé` par un Collecteur vérifié. Au plus une Mission `active` par Signalement.
- **Statut de Mission** : `active` → `terminée` (Preuve de collecte acceptée), `annulée` (par le Collecteur ou l'Administrateur commune) ou `expirée` (sans Preuve dans le délai de FR-42). `terminée`, `annulée` et `expirée` sont terminaux.
```

FR-25, ajouter aux Conséquences :
```markdown
- Accepter une Mission sur un Signalement qui n'est pas `validé` est refusé (409).
- Un renvoi de la même acceptation par le même Collecteur renvoie la Mission existante, sans erreur.
```

FR-26, remplacer toute l'exigence :
```markdown
#### FR-26 : Annuler une Mission

Le Collecteur annule sa Mission `active`, ou un Administrateur commune annule une Mission `active` ; la Mission passe à `annulée` et le Signalement revient à `validé`.

**Conséquences :**
- Annuler une Mission `terminée`, `annulée` ou `expirée` est refusé (409).
- L'annulation est inscrite au Journal d'audit, avec son auteur.
```

FR-29, remplacer « Une Preuve acceptée passe la Mission à « terminée » et le Signalement à `collecté`. » par :
```markdown
- Une Preuve acceptée passe la Mission à `terminée` et le Signalement à `collecté`.
- Une Preuve sur une Mission qui n'est pas `active` est refusée (409) ; une Preuve soumise par un autre Collecteur que celui de la Mission est refusée (403).
- Le renvoi d'une même Preuve après une coupure réseau renvoie la Preuve déjà acceptée : une seule Preuve et un seul Poids déclaré sont enregistrés.
```

§4.7, nouvelle FR après FR-28 :
```markdown
#### FR-42 : Expiration d'une Mission *(Should, avant le pilote)*

Une Mission `active` sans Preuve de collecte 48 h après son acceptation `[ASSUMPTION : délai configurable]` passe à `expirée`, et le Signalement revient à `validé`.

**Conséquences :**
- Le Signalement redevient visible des Collecteurs vérifiés dans le rayon (FR-24).
- L'expiration est inscrite au Journal d'audit.
- Test avec une horloge simulée : à 48 h et 1 min, la Mission est `expirée` et le Signalement `validé`.
```

---

#### T-06 · Journal d'audit : actions non listées, pas de trace de chaque changement de Statut, « non modifiable » non testé

- **Sources :** PB A3 (B, promesse « audit trail of every status change »), RUB (high, FR-36), DT E-S5, AUD S10.
- **Constat :** quatre lacunes.
  - Seules la modération et la gestion des comptes sont tracées.
  - L'acceptation, l'annulation, la Preuve et l'assignation ne le sont pas.
  - La liste des « actions sensibles » n'existe pas.
  - Le caractère « non modifiable » n'a aucun test.
- **Décision :** DÉCISION-PAR-DÉFAUT. Fixer une liste fermée. L'**inscription** est obligatoire dès H48 ; la **consultation** (FR-36) reste en Should. L'historique des Statuts est visible dans le détail d'un Signalement côté Personnel.
  *Raison : l'inscription coûte peu si elle est posée dès le début, et tient la promesse faite au jury.*
- **Emplacements et textes :**

§3 Glossaire, remplacer « Journal d'audit » :
```markdown
- **Journal d'audit** : trace horodatée par le serveur, en ajout seul, des actions listées en FR-36 ; aucune entrée ne peut être modifiée ni supprimée.
```

FR-36, remplacer toute l'exigence :
```markdown
#### FR-36 : Journal d'audit

Le système inscrit au Journal d'audit, avec l'acteur, l'objet, l'état avant et après et l'horodatage serveur :
- toute transition de Statut et de Statut de Mission, y compris l'expiration automatique ;
- toute décision de modération, toute Correction par un Modérateur et toute Revue de Preuve (FR-41) ;
- toute assignation manuelle (FR-28) ;
- toute création, vérification, suspension, suppression de compte et tout changement de rôle ;
- tout Export agrégé (FR-33) et tout export des Corrections (FR-13) ;
- toute connexion du Personnel.

Un Administrateur commune consulte le Journal d'audit, filtrable par action et par période *(Should)*. Le Personnel voit l'historique des Statuts dans le détail d'un Signalement.

**Conséquences :**
- Pour chaque action de la liste, un test vérifie qu'une entrée est créée.
- Aucune route ne permet de modifier ni de supprimer une entrée, et le rôle applicatif de la base n'en a pas le droit (NFR-17).
```

FR-28, ajouter :
```markdown
**Conséquences :**
- Le Collecteur est notifié dans l'application.
- Chaque assignation est inscrite au Journal d'audit.
```

---

#### T-07 · Détection des doublons par distance et par délai promise au jury, absente

- **Sources :** PB A2 (B : le Proposal §10 promet la « duplicate detection by distance and time »).
- **Constat :** FR-8 ne détecte que les photos strictement identiques.
- **Décision :** DÉCISION-PAR-DÉFAUT. Créer un drapeau « Doublon probable » : à moins de 50 m d'un autre Signalement, depuis moins de 72 h, sur un Signalement non terminal `[ASSUMPTION]`. Le drapeau est affiché en modération à H48.
  *Raison : c'est une requête PostGIS, et c'est la parade anti-spam annoncée au jury.*
- **Emplacements et textes :**

§3 Glossaire :
```markdown
- **Doublon probable** : Signalement dont la Position est à moins de 50 m d'un Signalement non terminal reçu dans les 72 h précédentes `[ASSUMPTION : 50 m et 72 h, configurables]`, ou dont la photo est strictement identique à une photo déjà reçue.
```

FR-8, remplacer la troisième conséquence :
```markdown
- Une photo strictement identique à une photo déjà reçue fait du Signalement un Doublon probable.
```

FR-22 : le drapeau est intégré au texte de T-26. FR-23, ajouter :
```markdown
- Un rejet pour le motif « doublon » affiche au Citoyen le Numéro de suivi du Signalement d'origine.
```

§6.2, ligne « Spam », colonne Contrôle :
```markdown
FR-10, File de modération, Doublon probable (distance, délai, photo identique)
```

---

#### T-08 · Preuve de collecte hors-ligne : sujet passé sous silence

- **Sources :** RUB (high).
- **Constat :** le Collecteur travaille dans des zones à réseau instable. Le PRD ne dit pas si une Preuve peut attendre le réseau, ni comment l'horodatage serveur et le contrôle à 150 m se combinent avec un envoi différé.
- **Décision :** DÉCISION-PAR-DÉFAUT. La Preuve hors-ligne devient un `[NON-GOAL pour le MVP]` : le Collecteur doit avoir du réseau sur place. La question est rouverte pour le pilote après mesure de la couverture (§11, T-20).
  *Raison : une Preuve différée affaiblit le géorepérage et l'horodatage serveur, et la démo n'en a pas besoin.*
- **Emplacements et textes :**

FR-29, ajouter aux Conséquences :
```markdown
- Sans réseau, la Preuve ne peut pas être envoyée : l'écran 6 l'indique et garde la saisie tant que l'application reste ouverte ; la Position est capturée au moment de l'envoi `[NON-GOAL pour le MVP : Preuve en File hors-ligne]`.
```

§8 Non-objectifs, ajouter :
```markdown
- Preuve de collecte hors-ligne : au MVP, le Collecteur doit avoir du réseau sur place (question rouverte pour le pilote, §11).
```

---

#### T-09 · Pilote sans sauvegarde, sans supervision, avec un plan de sortie invérifiable

- **Sources :** CAH E2 (H) et E17, DT E-S3 (H), E-O1 (H), E-O2 et E-X1, RUB (medium, « pilote sans exigence d'exploitation » ; low, « plan de sortie »), PB A11.
- **Constat :** NFR-7 ne vise que la démo. Les sauvegardes quotidiennes et la cible de 99 % du cahier sont perdues, aucune alerte n'est exigée, et le plan de sortie est seulement « documenté ».
- **Décision :** DÉCISION-PAR-DÉFAUT, en trois volets :
  - NFR-15 pour la continuité au pilote ;
  - NFR-16 pour la supervision, réduite à **4 alertes utiles** (les 8 alertes du dossier technique sont écartées en T-39) ;
  - un plan de sortie vérifiable, testé pendant le pilote.

  *Raison : six mois de données réelles et des Preuves qui fondent la reconnaissance des Collecteurs ; sans sur-outillage.*
- **Emplacements et textes :**

§5, ajouter deux lignes au tableau :
```markdown
| NFR-15 | Continuité (pilote) | Sauvegarde et restauration | Sauvegarde quotidienne chiffrée de la base et des photos, hors du serveur hôte ; perte maximale de 24 h ; une restauration complète réussie avant la collecte de données réelles ; disponibilité visée de 99 % par mois | Exercice de restauration ; supervision |
| NFR-16 | Supervision (pilote) | Alertes | Une alerte part sur le canal de l'équipe si : le taux de réponses 5xx dépasse 2 % sur 5 min ; une sauvegarde échoue ou le disque est rempli à plus de 85 % `[ASSUMPTION]` ; le plafond SMS est atteint (FR-1) ; la file de Classification serveur est pleine (FR-14) | Déclenchement simulé de chaque alerte |
```

NFR-14, colonne Exigence :
```markdown
Journaux structurés avec identifiant de requête, rôle, route et durée ; jamais de jeton ni de numéro complet
```

§6.4, remplacer « Plan de sortie documenté vers un hébergement au Sénégal. » par :
```markdown
- Plan de sortie vérifiable vers un hébergement au Sénégal : export complet de la base et des photos en formats standard ; déploiement décrit par conteneurs ; clés de chiffrement contrôlées par l'organisation ; une restauration complète sur un autre hôte est réalisée avant la fin du pilote (§11, région d'hébergement).
```

---

#### T-10 · Consentement au réentraînement : export non filtré, pas de retrait, anonymes non couverts

- **Sources :** DT E-C3 (H) et E-C1, AUD §4 (finalité distincte), PB A10, CAH US-03.
- **Constat :** FR-13 rend toutes les Corrections exportables, sans filtre. Le retrait du consentement après coup n'existe pas. Le consentement d'un anonyme n'est stocké nulle part côté serveur.
- **Décision :** DÉCISION-PAR-DÉFAUT. On conserve le refus sans perte d'accès : le `[ASSUMPTION]` de FR-4 devient une décision. Le choix est copié sur chaque Signalement, le retrait est possible à tout moment, et l'export est filtré.
  *Raison : c'est conforme à la loi 2008-12 et au dossier CDP ; à l'oral, on dira « chaque correction consentie ».*
- **Emplacements et textes :**

FR-4, remplacer la troisième conséquence et en ajouter deux :
```markdown
- Le Citoyen peut refuser l'usage pour le réentraînement sans perdre l'accès au signalement.
- Le choix est enregistré sur chaque Signalement au moment de sa création.
- Le Citoyen peut changer d'avis à tout moment, depuis son profil (connecté) ou les réglages de l'application (anonyme) ; un retrait exclut ses Signalements, passés et futurs, des exports suivants.
```

FR-13, remplacer « Les Corrections sont exportables comme jeu d'exemples étiquetés. » par :
```markdown
- Seules les Corrections de Signalements ayant atteint `validé`, dont l'auteur a accepté l'usage pour le réentraînement, sont exportées comme exemples étiquetés. Test : un Signalement avec refus n'apparaît pas dans l'export.
```

---

#### T-11 · Visages et plaques : la photo reste conservée

- **Sources :** CAH E3 (H, NF-10 « ni visage ni plaque conservés »), AUD S9, DT E-C4.
- **Constat :** trois lacunes.
  - La consigne n'est donnée qu'à la première utilisation.
  - Une photo rejetée reste stockée 12 mois.
  - Les photos de Preuve ne passent par aucune modération, et le report du floutage n'est inscrit nulle part.
- **Décision :** DÉCISION-PAR-DÉFAUT, en quatre mesures :
  - un motif de rejet dédié, avec purge de la photo sous 24 h ;
  - une conservation de 30 jours pour les autres rejets `[ASSUMPTION]` ;
  - un rappel de la consigne à chaque capture ;
  - le floutage automatique placé en non-objectif.

  *Raison : cela respecte NF-10 sans IA de floutage.*
- **Emplacements et textes :**

FR-7, ajouter aux Conséquences :
```markdown
- L'écran de capture (écran 2) rappelle à chaque fois la consigne « ni personne ni plaque ».
```

FR-23, ajouter aux Conséquences :
```markdown
- Le motif de rejet « Personne ou plaque visible » existe ; la photo d'un Signalement rejeté pour ce motif est supprimée du stockage sous 24 h, seule la décision restant au Journal d'audit.
```

FR-29, ajouter aux Conséquences :
```markdown
- Les photos de Preuve ne sont visibles que du Collecteur de la Mission et du Personnel ; l'écran 6 rappelle la consigne « ni personne ni plaque ».
```

§6.1, tableau de conservation : voir T-30, qui regroupe toutes les lignes. §8, ajouter :
```markdown
- Floutage automatique des visages et des plaques : après le MVP ; la consigne de capture et la modération le compensent.
```

---

#### T-12 · Aucun plan B de démo ; sondes non définies

- **Sources :** CAH E1 (H), DT E-H1, AUD S11.
- **Constat :** deux manques.
  - Les plans B du cahier ont disparu : photos préparées, vidéo de la démo, tuiles en cache, règle « couper une extension ».
  - NFR-7 parle de « sondes » sans contenu, et `/docs` reste exposé.
- **Décision :** DÉCISION-PAR-DÉFAUT. Ajouter un §9.3 court et réécrire NFR-7.
  *Raison : c'est la démo du jury, avec une seule chance.*
- **Emplacements et textes :**

§5, remplacer NFR-7 :
```markdown
| NFR-7 | Disponibilité | Démo | Service et portable de secours prêts ; vidéo de la démo complète enregistrée avant H60 ; tuiles de la zone de démo disponibles sans réseau ; `/healthz` répond tant que le processus vit ; `/readyz` n'est prêt que si la base, le stockage et le Modèle sont disponibles et ne renvoie qu'un statut global ; hors Mode démonstration, `/docs` et `/openapi.json` ne sont pas exposés | Répétition ; test automatisé des sondes et de l'exposition |
```

Nouveau §9.3, après le §9.2 :
```markdown
### 9.3 Risques de démo et plans B

| Risque | Plan B exigé | Exigence liée |
|---|---|---|
| Modèle imprécis sur des photos locales | 10 photos locales préparées et testées ; la Correction est montrée comme une fonctionnalité | FR-13, SM-2 |
| Réseau instable dans la salle | Vidéo de la démo complète ; portable de secours servant de serveur ; tuiles en cache | NFR-7 |
| File hors-ligne pas prête | SM-1 commence par la séquence « mode avion » de la vidéo | FR-17, FR-18, SM-1 |
| Porte non atteinte | Couper une extension (Lots de matière, wolof) plutôt que repousser la suite | §9.1 |
| Passerelle SMS indisponible | Mode démonstration pour l'OTP | FR-6 |
```

---

#### T-13 · Ordre des portes : hors-ligne à H60, historique hors MVP, Modèle factice à H24 — QUESTION-MIA

- **Sources :** RUB (medium : hors-ligne au gel, historique hors MVP ; low : FR-37 et Collecteur vérifié), PB A5 (M), §3.3 (M) et §3.5 (M).
- **Constat :** trois décalages entre le plan et la promesse.
  - Le hors-ligne ouvre la démo (SM-1, UJ-1, pilier « Inclusive ») mais n'arrive qu'à H60.
  - L'historique du Collecteur (FR-30) porte la thèse et SM-7, mais il est « si H48 en avance ».
  - Le Proposal et le brief fixent à H24 un « premier Modèle entraîné exporté en ONNX » ; le PRD le remplace par le Modèle factice.
- **Décision :** QUESTION-MIA. C'est la capacité de l'équipe sur 72 h ; le plan des portes vient du brief.
- **Options :**
  - **A (recommandée).**
    - H24 : la cible est un premier Modèle entraîné, le Modèle factice servant de repli.
    - H48 : FR-17 et FR-18, plus l'inscription au Journal d'audit (T-06).
    - H60 : FR-30.
  - **B.** Portes inchangées. On journalise le report de FR-30 avec une phrase pour l'oral, et l'on s'appuie sur le plan B vidéo de T-12 pour le hors-ligne.
- **Texte prêt pour l'option A** (remplace le tableau du §9.1 et la première puce du §9.2) :
```markdown
| Porte | Exigences livrées | État visé |
|---|---|---|
| **H24** | FR-1 à FR-4, FR-6, FR-7 à FR-10, FR-16 (premier Modèle entraîné exporté en ONNX ; Modèle factice en repli), FR-37 | Signalement relié à la PWA |
| **H48** | FR-11 à FR-15, FR-17, FR-18, FR-22 à FR-26, FR-29, FR-36 (inscription au Journal d'audit) | Boucle signaler → modérer → collecter de bout en bout, hors-ligne compris |
| **H60** | FR-5, FR-19 à FR-21, FR-30, FR-31 à FR-33, FR-35 | Gel des fonctionnalités |
```
```markdown
- **FR-27, FR-28, FR-34, FR-36 (consultation) :** seulement si la porte H48 est atteinte en avance.
- **FR-41 à FR-43 :** avant le pilote, hors des portes du hackathon.
```

FR-37, ajouter aux Conséquences, quelle que soit l'option (AUTOFIX, dépendance relevée par RUB) :
```markdown
- Les comptes de test comprennent au moins un Collecteur vérifié, un Modérateur et un Administrateur commune.
```

---

#### T-14 · Périmètre géographique du pilote et configuration par commune promise au jury — QUESTION-MIA

- **Sources :** PB A1 (B : « Configuration per commune », « built to be replicated »), RUB (medium, « périmètre géographique du pilote »), DT E-D8 et §2.2 n° 33 (isolation par commune).
- **Constat :** trois incohérences.
  - FR-7 accepte toute Position au Sénégal, alors que le pilote porte sur une seule commune.
  - Rien ne dit ce que deviennent les Signalements hors de la commune, ni ceux hors des Zones chargées.
  - La promesse « configuration par commune » n'est ni livrée ni écartée.
- **Décision :** QUESTION-MIA. Le choix touche le modèle de données (cloisonnement) et une promesse faite au jury.
- **Options :**
  - **A (recommandée).** Mono-commune assumée : une « Zone active » (Dakar pour la démo, la commune partenaire au pilote) ; un refus avant la photo en dehors de cette Zone ; le multi-commune en non-objectif ; à l'oral, « mono-commune au pilote, conçu pour être répliqué ».
  - **B.** Une FR « Commune » minimale avant le pilote : entité commune, Zones rattachées, Personnel limité à sa commune, Tableau de bord cloisonné.
- **Texte prêt pour l'option A :**

§3 Glossaire :
```markdown
- **Zone active** : Zone où le service est ouvert ; Dakar pour la démo, la commune partenaire pour le pilote.
```

FR-7, remplacer « Une Position hors du Sénégal est refusée. » et « La Zone est déterminée automatiquement à partir de la Position. » par :
```markdown
- Une Position hors de la Zone active est refusée dès l'écran 2, avant la photo, avec le message « TerangaCycle n'est pas encore actif ici ».
- La Zone (quartier) est déterminée automatiquement à partir de la Position.
```

§8, ajouter :
```markdown
- Multi-commune : cloisonnement du Personnel et des données par commune, et configuration des Types de déchet par commune. Le MVP et le pilote servent une seule commune ; le modèle reste réplicable.
```

§11 : ajouter la question 10 de T-20.

---

#### T-15 · SM-2 et SM-3 non reproductibles ; calibration, fiche du Modèle et réentraînement absents

- **Sources :** DT E-A1 (H, ECE), E-A2 (150 photos par classe), E-A4 et E-L1 (H, réentraînement), RUB (medium, SM-2 et SM-3), CAH NF-15 et E11 (fiche du Modèle), PB §3.3 (livrables IA).
- **Constat :** quatre lacunes.
  - Le « jeu de test local conservé » n'a ni taille ni origine.
  - La calibration, dont dépend le Seuil de confiance, n'apparaît que dans l'addendum.
  - SM-3 n'a ni point de départ ni point d'arrivée.
  - La fiche du Modèle n'est pas un livrable, et rien ne gouverne la publication d'une nouvelle version au pilote.
- **Décision :** DÉCISION-PAR-DÉFAUT, en quatre points :
  - viser 150 photos par classe, en publiant honnêtement la taille réelle si la cible n'est pas atteinte ;
  - exiger ECE ≤ 0,10 ;
  - faire de la fiche du Modèle un livrable ;
  - prévoir un réentraînement **manuel** mensuel au pilote, le déclenchement automatique devenant un non-objectif.

  *Raison : un chiffre annoncé au jury doit être reproductible ; l'automatisation du réentraînement ne sert pas le pilote.*
- **Emplacements et textes :**

§10, remplacer SM-2 et SM-3 :
```markdown
- **SM-2** : qualité du Modèle sur un jeu de test figé de photos prises au Sénégal, d'au moins 150 photos par classe, découpé par lieu et par jour, jamais utilisé pour l'entraînement.
  - Seuils : F1 macro ≥ 0,80 et rappel ≥ 0,70 par classe ; calibration ECE ≤ 0,10, condition de validité du Seuil de confiance. La top-1 accuracy est publiée en complément, face à la cible de 80 % du Proposal, avec la matrice de confusion.
  - Si le jeu n'atteint pas 150 photos par classe à H48, les chiffres sont publiés avec la taille réelle du jeu.
  - Une fiche du Modèle est publiée avec chaque version : données et licence de chaque source, métriques, matrice de confusion, limites connues (photos sombres, tas mélangés, déchets mouillés).
  - Valide FR-11, FR-12 et FR-14.
- **SM-3** : création d'un Signalement en moins de 30 s, de l'appui sur « Signaler un dépôt » (écran 1) à l'accusé de réception (écran 4) ; médiane de 10 essais réalisés par au moins 3 personnes qui découvrent l'application, sur un Android à 2 Go de RAM. Valide FR-7, FR-11 et FR-12.
```

FR-16, ajouter :
```markdown
**Conséquences :**
- Une nouvelle version du Modèle n'est publiée que si elle atteint les seuils de SM-2 sur le jeu de test figé, et avec sa fiche.
- Pendant le pilote, le Modèle est réentraîné au plus une fois par mois sur les Corrections exportables (FR-13).
```

SM-8, remplacer « Valide FR-13 et FR-16. » par « Valide FR-13 et FR-16 (réentraînement mensuel). ». §8, ajouter :
```markdown
- Déclenchement automatique du réentraînement sur un seuil de Corrections : le réentraînement du pilote est manuel et mensuel.
```

### Sévérité medium

#### T-16 · Décisions validées encore marquées comme hypothèses

- **Sources :** RUB (notes mécaniques), AUD (synthèse, #1, #2, §5), PB §6.
- **Constat :** quatre endroits n'ont pas suivi le `.memlog.md` :
  - le §11 Q1 (Large ou Small) est toujours ouvert ;
  - SM-2 garde son `[ASSUMPTION]` ;
  - le §6.3 garde `[ASSUMPTION : validation de Mia]` ;
  - le §12 liste encore les décisions a à f comme des hypothèses.
- **Décision :** AUTOFIX. Textes au §3 de ce document (réécriture du §12 et retrait des balises).

---

#### T-17 · Positions précises : contradiction entre §6.1 et FR-24 ; FR-34 sans seuil

- **Sources :** RUB (medium), DT E-D5, AUD S8 (écart principal n° 1).
- **Constat :** le §6.1 réserve les positions précises au Personnel et au Collecteur de la Mission. Or FR-24 les montre à tout Collecteur vérifié, avant toute acceptation. FR-34 ne fixe ni taille de cellule ni seuil d'affichage.
- **Décision :** DÉCISION-PAR-DÉFAUT. Avant l'acceptation, la Position est arrondie à 3 décimales (environ 110 m) et la distance à 100 m près ; la Position précise n'est donnée qu'après l'acceptation. Pour FR-34 : cellules d'au moins 500 m, et masquage sous 3 Signalements `[ASSUMPTION]`.
  *Raison : on garde le §6.1 et l'audit, et l'arrondi suffit pour choisir une Mission.*
- **Emplacements et textes :**

FR-24, ajouter aux Conséquences :
```markdown
- Avant l'acceptation, la Position d'un Signalement est donnée arrondie à 3 décimales (environ 110 m) et la distance à 100 m près. Test : un Collecteur vérifié qui n'est pas celui de la Mission ne reçoit jamais plus de 3 décimales.
- Après l'acceptation, le Collecteur de la Mission reçoit la Position précise (FR-27).
```

FR-34, remplacer toute l'exigence :
```markdown
#### FR-34 : Carte publique agrégée

Tout Visiteur voit une carte des Signalements agrégée par cellule ou par Zone, jamais de point précis. *(Should)*

**Conséquences :**
- Les cellules mesurent au moins 500 m de côté ; une cellule de moins de 3 Signalements n'est pas affichée `[ASSUMPTION]`.
- Aucune réponse publique de l'API ne contient de coordonnées de Signalement.
- Tant que FR-34 n'est pas livrée, aucune carte n'est accessible sans connexion.
```

---

#### T-18 · Géorepérage de 150 m sans règle de précision GPS ; message d'erreur flou

- **Sources :** RUB (medium), AUD §7 (« message clair »), PB §4 (ton : ne pas accuser le Collecteur).
- **Constat :** la précision GPS est enregistrée mais jamais utilisée. Une Position de Signalement à ± 200 m fait échouer un Collecteur honnête.
- **Décision :** DÉCISION-PAR-DÉFAUT.
  - À la création : au-delà de 50 m de précision, une invite à patienter, puis un drapeau « position imprécise ».
  - À la Preuve : la précision du Collecteur doit être ≤ 50 m, avec une tolérance de 150 m plus la précision du Signalement, plafonnée à 50 m `[ASSUMPTION : 50 m]`.

  *Raison : cela protège le Collecteur honnête sans ouvrir de fenêtre de fraude.*
- **Emplacements et textes :**

FR-7, ajouter aux Conséquences :
```markdown
- Si la précision de la Position dépasse 50 m `[ASSUMPTION]`, l'écran 2 invite à patienter quelques secondes ; le Citoyen peut envoyer quand même, et le Signalement porte le drapeau « position imprécise » dans la File de modération.
```

FR-29, remplacer « Une Position du Collecteur à plus de 150 m de la Position du Signalement est refusée, avec un message clair. » par :
```markdown
- La Preuve est refusée si la précision de la Position du Collecteur dépasse 50 m (l'écran 6 invite à réessayer), ou si sa distance à la Position du Signalement dépasse 150 m plus la précision du Signalement, plafonnée à 50 m.
- Le message de refus indique la distance mesurée et le rayon accepté, sans accuser le Collecteur, par exemple : « Vous êtes à 230 m du dépôt ; rapprochez-vous à moins de 150 m. »
```

---

#### T-19 · « Poids mesuré » alors que les Collecteurs n'ont pas de balance

- **Sources :** CAH E10 et US-10 (« poids estimé saisi »).
- **Constat :** « mesuré » suppose une pesée, que les récupérateurs informels n'ont pas toujours. Les Kg collectés reposeraient alors sur une donnée présentée à tort comme pesée, ce qui contredit le §7 « Honnêteté ».
- **Décision :** DÉCISION-PAR-DÉFAUT. Le terme devient « Poids déclaré », avec la mention `pesé` ou `estimé`.
  *Raison : c'est honnête et c'est mesurable ; la part `pesé` devient un indicateur de qualité.*
- **Emplacements et textes :**

§3 Glossaire, remplacer « Poids mesuré » :
```markdown
- **Poids déclaré** : poids saisi par le Collecteur dans la Preuve de collecte, avec la mention `pesé` ou `estimé`.
```

§3 Glossaire, « Preuve de collecte », remplacer par :
```markdown
- **Preuve de collecte** : photo avant, photo après, Poids déclaré et Position du Collecteur, horodatés par le serveur. « Preuve » en est l'abréviation admise.
```

FR-29, remplacer « Sans photo avant, photo après et Poids mesuré supérieur à 0, la Preuve est refusée. » par :
```markdown
- Sans photo avant, photo après, Poids déclaré supérieur à 0 et mention `pesé` ou `estimé`, la Preuve est refusée.
```

UJ-3, « Arrivée » : remplacer « Poids mesuré de 15 kg » par « Poids déclaré de 15 kg (estimé) ». Les autres occurrences sont traitées au §3.

---

#### T-20 · Questions ouvertes sans responsable ni échéance

- **Sources :** RUB (medium : Q3 à Q7 sans responsable ; Q6 bloque H48), AUD #4, §4 (mineurs, cadre légal) et §8 (jeu de photos), PB §3.5 (Q1 ouverte à tort).
- **Décision :** AUTOFIX. Réécrire le §11. Les responsables Ahmadou et Aissatou sont proposés d'après les rôles du Proposal, et Mia peut les réaffecter. Q1 (Large ou Small) est fermée et passe au §12. Q7 (inscription au hackathon, partage Figma) sort du PRD (voir §4).
- **Emplacement :** §11, remplacer toute la section :
```markdown
## 11. Questions ouvertes

| # | Question | Responsable | Échéance |
|---|---|---|---|
| 1 | **Licence du code :** MIT (adoption) ou AGPL-3.0 (commun numérique) ? Un fichier `LICENSE` doit être à la racine avant la démo. | Mia | H60 |
| 2 | **Passerelle SMS au Sénégal :** couverture, coût, valeur du plafond quotidien de FR-1. Le Mode démonstration couvre le hackathon. | Ahmadou | Avant le pilote |
| 3 | **Région d'hébergement du pilote :** Le Cap, Paris ou hébergeur sénégalais ; latence depuis Dakar, dossier CDP, test du plan de sortie (§6.4). | Ahmadou | Avant le pilote |
| 4 | **Âge minimum** pour créer un compte, et relecture juridique du texte de consentement (FR-4). La démo n'utilise que des comptes de test. | Mia | Avant le pilote |
| 5 | **Cadre légal :** la loi n° 2008-12 a-t-elle été remplacée ou complétée ? Durées de conservation du §6.1 à valider avec la commune. | Mia | Avant le dépôt du dossier CDP |
| 6 | **Table de conversion Taille de tas → Poids estimé :** table provisoire `[ASSUMPTION]` livrée avec FR-7 ; valeurs réelles à obtenir d'un collecteur. | Ahmadou (table provisoire), Mia (valeurs terrain) | H24, puis avant le pilote |
| 7 | **Collecteurs au pilote :** incitation (rémunération par la commune, GIE, reconnaissance), enrôlement des récupérateurs informels, critères de « Collecteur vérifié » (pièce d'identité obligatoire ou non). Risque direct sur SM-7. | Mia, avec la commune | Avant le pilote |
| 8 | **Preuve de collecte hors-ligne au pilote** (§8) : à décider après mesure de la couverture réseau des premiers sites. | Ahmadou | Fin du 1er mois du pilote |
| 9 | **Jeu de photos locales et Modèle :** dans le dépôt à quelle date ? (SM-2) | Aissatou | H24 |
| 10 | **Multi-commune** (si T-14 option A) : quand et comment cloisonner le Personnel et les données par commune ? | Mia | Avant une deuxième commune |
```

---

#### T-21 · Dépôt public sans licence

- **Sources :** CAH E11 (NF-15, pitch « code sous licence ouverte »), AUD §4 et §6, PB A12.
- **Constat :** le dépôt est déjà public. Sans `LICENSE`, il est « tous droits réservés », ce qui contredit la souveraineté et le « commun numérique ».
- **Décision :** DIFFÉRER. **Responsable : Mia, échéance H60** (§11 Q1 de T-20). Le choix entre MIT et AGPL reste à Mia. Seule l'échéance change.
- **Emplacements et textes :** §6.3, remplacer la puce « Licence ouverte du code » :
```markdown
- **Licence ouverte du code** : MIT ou AGPL-3.0 ; fichier `LICENSE` à la racine du dépôt avant la démo (§11, Q1).
```

---

#### T-22 · Collecteurs informels au pilote : incitation, enrôlement, critères de vérification

- **Sources :** RUB (medium : « être reconnu et payé » face aux non-objectifs ; low : pas d'UJ d'enrôlement), PB §4 (critères, auto-inscription), CAH E14 (10 à 20 collecteurs).
- **Constat :** SM-7 vise au moins 20 Collecteurs vérifiés actifs, mais le PRD ne dit ni qui les rémunère, ni comment un informel obtient un compte, ni sur quels critères il est « vérifié ».
- **Décision :** DIFFÉRER. **Responsable : Mia, avec la commune ; avant le pilote** (§11 Q7 de T-20). Pour le MVP, le compte reste créé par l'Administrateur commune (FR-35 inchangé ; UJ-6 en T-38). SM-7 reste à « au moins 20 », chiffre remis au jury (CAH E14 ignoré, voir T-40).
- **Emplacements et textes :** §9.2, ajouter après le `[NOTE FOR PM]` existant :
```markdown
  `[NOTE FOR PM]` L'incitation des Collecteurs pendant le pilote n'est pas définie : le paiement réel et les points sont des non-objectifs (§8). Le modèle de rémunération ou de reconnaissance est à négocier avec la commune (§11, Q7). Sans lui, SM-7 est à risque.
```

---

#### T-23 · Taille du Modèle non bornée ; premier usage sans Modèle en cache

- **Sources :** RUB (medium), CAH E12 (NF-05), DT E-D9.
- **Constat :** NFR-5 exclut le Modèle de son budget sans lui en fixer un, alors qu'Awa a un « forfait souvent épuisé ». Le comportement sans Modèle en cache n'est pas défini.
- **Décision :** DÉCISION-PAR-DÉFAUT. Le Modèle doit peser 8 Mo au plus (environ 6 Mo attendus). Sans Modèle en cache, le choix du type est manuel et aucun Désaccord IA n'est calculé.
  *Raison : c'est la marge sur MobileNetV3-Large INT8, et cela évite de bloquer le premier Signalement.*
- **Emplacements et textes :**

NFR-5, colonne Seuil :
```markdown
≤ 500 Ko hors images et Modèle ; Modèle ≤ 8 Mo, téléchargé une seule fois puis mis en cache
```

FR-11, ajouter aux Conséquences :
```markdown
- Tant que le Modèle n'est pas en cache, le Citoyen peut signaler : il choisit le Type de déchet lui-même, et aucun Désaccord IA n'est calculé pour ce Signalement.
```

---

#### T-24 · Signalements créés en direct pendant la démo non étiquetés

- **Sources :** RUB (medium).
- **Constat :** SM-1 prévoit des photos réelles prises en direct, alors que le §6.3 affirme que la démo n'utilise que des Données de démonstration. FR-37 n'étiquette que le jeu chargé.
- **Décision :** DÉCISION-PAR-DÉFAUT. Tout ce qui est créé en Mode démonstration est étiqueté automatiquement.
  *Raison : la prémisse « aucune obligation CDP » redevient vraie.*
- **Emplacements et textes :**

FR-37, ajouter aux Conséquences :
```markdown
- Tant que le Mode démonstration est actif, tout Signalement, toute Mission et toute Preuve de collecte créés sont automatiquement étiquetés Données de démonstration.
```

§6.3, remplacer la première sous-puce de la loi 2008-12 :
```markdown
  - aucune obligation pour la démo : elle n'utilise que des comptes de test et des Données de démonstration, y compris les Signalements créés en direct (FR-37), dont les photos ne montrent ni personne ni plaque ;
```

---

#### T-25 · FR-14 : traitement asynchrone encore en hypothèse, file non bornée

- **Sources :** AUD S12, DT E-A3 (p95 < 2 s) et §2.1 (contrat du 201).
- **Constat :** le traitement asynchrone est une correction de sécurité (S12) déjà décidée. Il porte pourtant encore `[ASSUMPTION]`, et la « file bornée » n'a pas de valeur.
- **Décision :** AUTOFIX.
- **Emplacement :** FR-14, remplacer la deuxième conséquence :
```markdown
- La création répond sans attendre la Classification serveur, qui est calculée en tâche de fond ; le traitement d'une photo par le Modèle serveur prend moins de 2 s (p95).
- La file de classification est bornée `[ASSUMPTION : 500 tâches]` ; quand elle est pleine, les nouveaux Signalements sont acceptés et restent « classification serveur en attente » jusqu'à leur reclassement.
```

---

#### T-26 · File de modération : drapeaux non testables, Classification serveur en attente

- **Sources :** AUD #7 (FR-15 sans conséquence ; Classification serveur pas encore arrivée), RUB (high : FR-15 et FR-22 sans conséquence), PB A6 (drapeau « faible confiance »).
- **Décision :** AUTOFIX. Ce texte intègre T-07 et T-18, et il est compatible avec toutes les options de T-03.
- **Emplacements et textes :**

FR-15, ajouter :
```markdown
**Conséquences :**
- Un Signalement dont le Type envoyé par l'appareil diffère de la Classification serveur porte le drapeau Désaccord IA. Test : prédiction locale forcée différente → drapeau présent.
- Un Signalement envoyé sans Classification locale (FR-11, Modèle absent du cache) ne porte pas ce drapeau.
```

FR-22, remplacer toute l'exigence :
```markdown
#### FR-22 : File de modération

Un Modérateur voit les Signalements `en attente de modération`, les plus anciens d'abord, avec :
- la photo ;
- la Position et sa précision ;
- le Type proposé et son Score de confiance ;
- la Classification serveur ;
- les drapeaux Désaccord IA, Doublon probable, « faible confiance » (Score de confiance local sous le Seuil de confiance) et « position imprécise ».

Réalise UJ-2.

**Conséquences :**
- Tant que la Classification serveur n'est pas disponible, la File affiche « classification serveur en attente » et le Modérateur peut quand même décider.
- La File peut être filtrée par drapeau ; un Doublon probable renvoie vers le Signalement d'origine.
- La File affiche au plus 50 Signalements par page.
```

---

#### T-27 · Sessions, jetons, suspension « immédiate », second facteur du Personnel

- **Sources :** AUD S4, S5 et §7 (FR-2, FR-5, FR-35), DT E-S8 et E-S1 (H, second facteur).
- **Constat :** trois lacunes.
  - La durée du jeton d'accès n'est pas fixée.
  - « immédiatement » est faux avec des jetons sans état.
  - S4 et S5 n'existent que dans l'addendum, et le Personnel, qui exporte des données, n'a que l'OTP par SMS.
- **Décision :** DÉCISION-PAR-DÉFAUT. Jeton d'accès ≤ 15 min ; refus dès la requête suivante. Le second facteur du Personnel devient FR-43, **obligatoire avant le pilote** et non exigé au hackathon.
  *Raison : le hackathon n'utilise que des comptes de test, alors que le pilote expose des données réelles.*
- **Emplacements et textes :**

FR-2, ajouter aux Conséquences :
```markdown
- Le jeton d'accès expire au plus 15 min après son émission ; après une déconnexion ou une révocation, le renouvellement est refusé (401).
- Aucun jeton n'est stocké dans `localStorage`, `sessionStorage` ni IndexedDB (test de bout en bout qui inspecte le stockage du navigateur).
- Un jeton signé avec un algorithme hors liste blanche, d'émetteur ou d'audience incorrects, expiré ou de clé inconnue, est refusé (401) ; un test par cas.
```

FR-5, première conséquence : remplacer « désactive le compte immédiatement » par « refuse la requête suivante de l'utilisateur (401) ». FR-35, remplacer « Un compte suspendu perd l'accès immédiatement. » par :
```markdown
- La requête suivante d'un compte suspendu est refusée (401).
```

§4.1, nouvelle FR après FR-6 :
```markdown
#### FR-43 : Second facteur du Personnel *(Must avant le pilote ; hors des portes du hackathon)*

Un Modérateur ou un Administrateur commune se connecte avec l'OTP par SMS et un second facteur (application d'authentification).

**Conséquences :**
- Sans second facteur valide, les fonctions du Personnel sont refusées (403).
- L'activation et la réinitialisation du second facteur sont inscrites au Journal d'audit.
```

---

#### T-28 · Limites de débit sans valeur et contournables

- **Sources :** AUD S6, S7 et §7 (FR-1), DT E-R1 (60 req/min) et E-R2 (limite par compte).
- **Décision :** DÉCISION-PAR-DÉFAUT. Valeurs : 20 OTP par heure et par IP, 5 par appareil ; plafond SMS configurable ; 10 Signalements par heure et par compte ; 60 req/min par utilisateur connecté `[ASSUMPTION]`.
  *Raison : on passe du flou au testable, avec des seuils larges pour un usage normal.*
- **Emplacements et textes :**

FR-1, remplacer les deuxième et troisième conséquences :
```markdown
- 5 demandes au plus par heure et par numéro, 5 par Identifiant d'appareil et 20 par IP `[ASSUMPTION]` ; au-delà, la demande est refusée (429) avec le délai d'attente.
- Un plafond quotidien de SMS, configurable `[ASSUMPTION : valeur fixée avec la passerelle, §11 Q2]`, coupe l'envoi : la demande est refusée (503) avec un message, et une alerte part sur le canal de l'équipe (NFR-16).
- Le code OTP n'est jamais stocké en clair.
```

FR-10, remplacer toute l'exigence :
```markdown
#### FR-10 : Limite anti-abus

Un Citoyen anonyme peut créer au plus 10 Signalements par heure et par Identifiant d'appareil ou par IP ; un Citoyen connecté, au plus 10 par heure et par compte `[ASSUMPTION]`. Tout utilisateur connecté est limité à 60 requêtes par minute. Au-delà, la réponse est 429.

**Conséquences :**
- L'IP retenue est celle que transmet le proxy de confiance : 11 requêtes portant 11 en-têtes `X-Forwarded-For` différents obtiennent un 429 à la 11e.
- Les compteurs survivent à un redémarrage du service.
```

---

#### T-29 · Sécurité : NFR-8, NFR-9 et NFR-10 incomplètes ; rien sur les données au repos ni sur la base

- **Sources :** CAH E4 (NF-08, chiffrement au repos), DT E-S2, E-S4 et E-S6, AUD S10, §3 (CSP) et §7 (« routes sensibles », NFR-10).
- **Décision :** AUTOFIX. Ce sont des exigences déjà portées par l'audit (S1 à S12, décidé) et par le cahier ; il s'agit de les rendre testables.
- **Emplacements et textes :**

§5, remplacer NFR-8, NFR-9 et NFR-10, puis ajouter NFR-17 :
```markdown
| NFR-8 | Sécurité | Transport et en-têtes | TLS 1.2 minimum, HSTS, redirection HTTP → HTTPS ; CSP dont `script-src` n'autorise que `'self'` et `'wasm-unsafe-eval'` ; `X-Content-Type-Options: nosniff` ; `Referrer-Policy: no-referrer` ; CORS limité aux origines de la PWA ; photos servies depuis un domaine distinct de l'API | Scan SSL et test des en-têtes |
| NFR-9 | Sécurité | Contrôle d'accès | Toutes les routes `/v1` testées × chaque rôle et sans jeton, sauf une liste blanche publique explicite (`/healthz`, `/readyz`, création anonyme d'un Signalement, carte publique agrégée) | CI : échec si une route n'est ni testée ni dans la liste blanche |
| NFR-10 | Sécurité | Chaîne logicielle | Aucun secret dans Git ; la CI échoue sur toute vulnérabilité critique ou haute non justifiée dans un fichier d'exceptions daté ; images épinglées par empreinte et actions par SHA de commit | Gitleaks, pip-audit, npm audit, Trivy en CI |
| NFR-17 | Sécurité | Données au repos et base | Base, photos et sauvegardes chiffrées au repos (pilote) ; l'API se connecte avec un rôle qui ne peut ni modifier le schéma, ni modifier ou supprimer une entrée du Journal d'audit ; aucune colonne ne contient le numéro de téléphone en clair | Test CI (création de table et mise à jour du Journal refusées) ; recherche du numéro en clair dans une copie de la base |
```

FR-3, première conséquence, remplacer « chaque route sensible » par « chaque route de NFR-9 ». §6.1 « Protection », ajouter :
```markdown
- au pilote, la base, les photos et les sauvegardes sont chiffrées au repos, avec des clés contrôlées par l'organisation (NFR-17).
```

---

#### T-30 · Suppression des données et purge : écart avec US-22, purge non testable

- **Sources :** CAH E8 et US-22, DT E-C1 (accès, rectification) et E-C2 (purge, photos de Preuve), AUD §4 (conservation), PB A9 (Position du Collecteur non listée).
- **Constat :** quatre lacunes.
  - US-22 demande de supprimer « les données associées », alors que le PRD garde tout avec un auteur anonymisé, sans le dire ni le justifier.
  - Rien n'est prévu pour un anonyme.
  - Aucune purge n'est testable.
  - Les photos de Preuve et la Position du Collecteur sont absentes du §6.1.
- **Décision :** DÉCISION-PAR-DÉFAUT. On supprime ce qui n'a pas été validé et l'on conserve, anonymisé, ce qui fonde les indicateurs et les Preuves. Un anonyme peut retirer un Signalement en attente. La purge est automatique et testée.
  *Raison : on respecte au mieux US-22 sans casser l'historique des Collecteurs.* Journaliser l'écart avec US-22.
- **Emplacements et textes :**

FR-5, remplacer les Conséquences :
```markdown
**Conséquences :**
- La suppression efface le numéro et refuse la requête suivante de l'utilisateur (401) ; la purge complète a lieu sous 30 jours.
- Les photos et Positions de ses Signalements `en attente de modération` ou `rejeté` sont supprimées ; ses Signalements ayant atteint `validé` sont conservés avec un auteur anonymisé, parce qu'ils fondent les indicateurs et les Preuves des Collecteurs.
- L'utilisateur consulte les données de son profil et ses Signalements (droit d'accès) et corrige son nom affiché (rectification).
- Un Citoyen anonyme peut retirer, depuis l'appareil d'origine, un Signalement encore `en attente de modération`.
```

§6.1, « Données collectées », ajouter :
```markdown
- la Position du Collecteur dans la Preuve de collecte ;
- l'empreinte de l'Identifiant d'appareil.
```

§6.1, remplacer le tableau de conservation et ajouter une phrase dessous :
```markdown
| Donnée | Durée de conservation `[ASSUMPTION : à valider avec la commune]` |
|---|---|
| Photos de Signalement | 12 mois |
| Photos de Signalements `rejeté` | 30 jours ; 24 h si personne ou plaque visible (FR-23) |
| Photos de Preuve de collecte | 12 mois |
| IP du Journal d'audit | 6 mois |
| Compte supprimé | Purgé sous 30 jours |
| Statistiques agrégées | Sans limite |

Une tâche planifiée applique ces durées. Test avec une horloge simulée : une photo plus ancienne que sa durée est supprimée et son lien ne fonctionne plus ; une IP de plus de 6 mois est effacée du Journal d'audit.
```

---

#### T-31 · Accessibilité : Rouge et Jaune en échec ; pictogrammes ; clavier ; contrôle en CI

- **Sources :** PB §3.4 (contrastes), AUD §5 (Rouge 4,28:1, Jaune 1,73:1, vert sur Menthe 3,82:1), CAH NF-12 (pictogrammes pour les Statuts et les actions), DT E-D4 (clavier).
- **Décision :** DÉCISION-PAR-DÉFAUT. Le vert corrigé s'applique à **tous** ses usages. Le Rouge est réservé aux aplats, aux icônes et au grand texte. Le Jaune n'est jamais un texte. Aucun nouveau jeton n'est créé.
  *Raison : on règle les échecs AA sans couleur à faire valider ; la variante foncée `#B93A1E` reste possible si Mia la veut.*
- **Emplacements et textes :**

§6.3, remplacer la puce WCAG :
```markdown
- **WCAG 2.1 AA :** NFR-12.
  - Le jeton Vert `#1F8A5B` de la maquette est remplacé par `#187A50` dans toutes ses utilisations : fond sous texte blanc (5,33:1), texte sur Fond (5,06:1), pastilles sur Menthe (4,70:1).
  - Le Rouge `#D9482B` (4,28:1 sur blanc) n'est utilisé que pour des aplats, icônes et bordures, ou pour un texte d'au moins 18,66 px en gras ; un message d'erreur s'écrit en Encre avec une icône rouge.
  - Le Jaune `#F2B705` n'est jamais une couleur de texte : il sert de fond sous un texte Encre. Un avertissement textuel utilise Ambre `#7A5C00` sur `#FFF4CC`.
```

NFR-12, colonnes Seuil et Vérification :
```markdown
| NFR-12 | Accessibilité | WCAG 2.1 AA | Contraste ≥ 4,5:1 pour le texte (3:1 pour le texte ≥ 18,66 px gras et les éléments non textuels) ; cibles tactiles ≥ 44 px ; libellés pour lecteurs d'écran ; chaque Type de déchet, chaque étape de la Frise de suivi et chaque action principale a un pictogramme accompagné d'un libellé ; navigation complète au clavier sur les écrans du Personnel | Script CI qui calcule chaque paire texte/fond des jetons ; audit Lighthouse |
```

§7, « Référence visuelle », remplacer « jetons de couleur du brief, sauf le vert corrigé (§6.3) » par « jetons de couleur du brief, avec les règles d'usage du §6.3 ».

---

#### T-32 · Écrans exigés par le PRD mais absents de la maquette figée

- **Sources :** PB §3.4 (M : Taille de tas absente de l'écran 3, aucun écran de modération ; maquette non modifiable, quota Figma) et §6 (UJ-2, UJ-5 et OTP sans écran).
- **Décision :** AUTOFIX.
- **Emplacements et textes :**

§7, ajouter après « Référence visuelle » :
```markdown
- **Écrans hors maquette :** la maquette Figma est figée. Les éléments suivants sont décrits dans la spécification UX, avec les mêmes jetons (corrigés) et la même police : Taille de tas (écran 3) ; variante « en attente d'envoi » de l'écran 4 ; consentement (FR-4) ; connexion OTP ; File de modération et détail d'un Signalement (UJ-2) ; administration des comptes et Journal d'audit ; bandeau Mode démonstration ; photo et filtre par Type de déchet dans la liste de l'écran 5.
- **Libellés de la Frise de suivi** (écran 4) : « Signalé », « Validé par la modération », « Assigné à un collecteur », « Collecté, preuve photo ».
- **Entrées de rôle :** les boutons « Je suis collecteur » et « Espace commune » de l'écran 1 mènent à la connexion OTP.
```

§2.3, note d'en-tête, remplacer par :
```markdown
> Les personnages sont illustratifs. Les numéros d'écran renvoient à la maquette Figma (1 · Accueil … 7 · Tableau de bord) ; les écrans absents de la maquette sont listés au §7.
```

---

#### T-33 · Termes et états employés hors Glossaire

- **Sources :** RUB (medium, « états hors glossaire » ; notes mécaniques).
- **Constat :** cinq termes ou états sont employés sans définition :
  - « en attente d'envoi » ;
  - la « frise des 4 états » (alors que le Statut a 5 valeurs) ;
  - « terminée » et « réservé » ;
  - « score de confiance » et « confiance » ;
  - « Modèle factice », « visiteur », « utilisateur ».
- **Décision :** AUTOFIX. On ajoute les termes ci-dessous ; les autres ajouts sont donnés dans leur constat : Identifiant d'appareil (T-01), Type de déchet retenu (T-03), Revue de Preuve (T-04), Statut de Mission (T-05), Doublon probable (T-07), Zone active (T-14), Poids déclaré (T-19). La dérive des termes est traitée au §3.
- **Emplacement :** §3 Glossaire, insérer à la place logique :
```markdown
- **Utilisateur connecté** : toute personne authentifiée, quel que soit son rôle.
- **Visiteur** : personne non connectée qui consulte la carte publique agrégée (FR-34).
- **Score de confiance** : probabilité calibrée que le Modèle associe au Type de déchet proposé, affichée en pourcentage.
- **Modèle factice** : remplaçant du Modèle qui respecte la même interface et renvoie des prédictions fixes ; il sert de repli à la porte H24.
- **En attente d'envoi** : état, sur l'appareil, d'un Signalement enregistré dans la File hors-ligne et pas encore reçu par le serveur. Ce n'est pas un Statut, et il n'a pas encore de Numéro de suivi.
- **Frise de suivi** : affichage du Statut en 4 étapes du chemin nominal : Signalé (`en attente de modération`), Validé (`validé`), Assigné (`assigné`), Collecté (`collecté`). `rejeté` remplace les étapes suivantes, avec son motif. Un Signalement en attente d'envoi n'a pas encore de frise.
- **Statut de Lot** (extension) : `disponible` → `réservé` (FR-40).
```

---

#### T-34 · Addendum : schéma, contrat d'API, prétraitement IA, code hors-ligne

- **Sources :** DT §2.1 (contrat du 201 en mode asynchrone, prétraitement différent entre l'évaluation et l'inférence, clé d'unicité après anonymisation) et §2.2 n° 1 à 14 et 22 à 26 et 35 à 38 ; AUD S1 (secret d'appareil), #7 (nom de drapeau unique), #9 (séquence annuelle) et §4 (`reports.consent_training`).
- **Décision :** AUTOFIX. Prétraitement retenu : celui de l'évaluation (Resize 256 puis CenterCrop 224), appliqué partout et vérifié par un test.
- **Emplacements et textes :**

Addendum §A, ligne « IA », remplacer :
```markdown
| IA | MobileNetV3-Large par défaut, Small si NFR-1 dépasse 3 s à la mesure H24 (décidé) ; 5 classes ; ONNX INT8 ≤ 8 Mo ; même fichier sur l'appareil et sur le serveur |
```

Addendum §A, ligne « API », remplacer :
```markdown
| API | REST JSON `/v1`, OpenAPI, format d'erreur unique `{error:{code,message,request_id}}` ; pagination par curseur (`limit` 50 par défaut, 100 au plus, réponse `{items, next_cursor}`) ; en-tête `Idempotency-Key` sur les POST sensibles (Preuve, acceptation, modération, assignation), portée par utilisateur, durée de vie 24 h ; dates ISO 8601 en UTC ; coordonnées `{lat, lng}` en WGS84 |
```

Addendum §B, ajouter les points 8 à 16 :
```markdown
8. **Preuve de collecte** : table `collection_proofs` reliée à la Mission, avec `location GEOGRAPHY(Point)`, `accuracy_m`, `weight_kg`, `weight_kind` (`weighed` | `estimated`), `review_status` (`unreviewed` | `confirmed` | `contested`), `review_reason` ; les photos `before` et `after` sont reliées à la Mission, pas seulement au Signalement (FR-29, FR-41).
9. **`missions`** : `status` (`active` | `completed` | `cancelled` | `expired`), `accepted_at`, `expires_at` ; index unique partiel « une Mission `active` par Signalement » conservé (FR-25, FR-42).
10. **`reports`** : `received_at` (horodatage serveur, origine des délais de FR-31), `accuracy_m`, `consent_training` (copié à la création, FR-4), `client_prediction` (type, confiance, `model_version`), `duplicate_of` (photo identique ou proximité, FR-7 et FR-22), `flags`.
11. **Identifiant d'appareil** : secret aléatoire d'au moins 128 bits généré à l'installation, envoyé dans un en-tête, stocké haché (`device_id_hash`), jamais renvoyé ni journalisé. L'unicité porte sur `(owner_key, client_uuid)`, où `owner_key` est l'empreinte de l'auteur ou de l'appareil calculée à la création ; elle reste valable après anonymisation de l'auteur.
12. **`audit_logs`** en ajout seul : `teranga_app` n'a que INSERT et SELECT (NFR-17).
13. **Retirer `users.points`** (non-objectif, minimisation).
14. **Numéro de suivi** : la séquence repart à 1 au 1er janvier ; l'année est celle de la réception par le serveur.
15. **Drapeau de désaccord** : un seul nom, `disagreement` (point 1).
16. **`users.totp_secret`** chiffré pour le second facteur du Personnel (FR-43).
```

Addendum §C, après la ligne S12 :
```markdown
| Contrat async (S12) | FR-14 | `POST /v1/reports` reçoit `pile_size`, `accuracy_m`, `waste_type` choisi, `client_prediction`, en-têtes d'appareil et d'idempotence ; il répond 201 (création) ou 200 (renvoi) avec `tracking_number`, `status` et `classification.status = pending` |
```

Addendum §D, remplacer le point « Prétraitement identique » et ajouter quatre points :
```markdown
- **Prétraitement unique** pour l'évaluation, le serveur et le navigateur : redimensionnement du petit côté à 256, recadrage central 224×224, normalisation ImageNet. Un test compare les sorties des trois chaînes sur 20 images (écart de score ≤ 0,01).
- **Entraînement** en deux phases ; quantification statique INT8 avec environ 200 images de calibration ; fichier ≤ 8 Mo (NFR-5).
- **Annotation** : double vérification de 20 % des photos ; cas ambigus classés `mixte`.
- **Réentraînement au pilote** : manuel, au plus une fois par mois ; export filtré par modération et consentement (FR-13) ; évaluation sur le jeu de test figé avant toute publication (FR-16).
```

Addendum, nouveau §G :
```markdown
## G. PWA hors-ligne : corrections du code du dossier technique

- Le schéma Dexie stocke 100 % des champs (FR-17) : photo, Position et précision, Taille de tas, Type choisi, Classification locale (type, score, version), commentaire, Identifiant client, état d'envoi.
- `flushQueue` est toujours appelé avec le jeton courant (si l'utilisateur est connecté) et l'Identifiant d'appareil ; un Signalement créé connecté n'est jamais renvoyé en anonyme.
- 201 et 200 vident l'entrée de la file ; un 4xx définitif (hors 408 et 429) la sort de la file et affiche le motif (FR-18) ; 429, 5xx et erreur réseau déclenchent un nouvel essai avec un délai croissant.
- Background Sync sur Chrome Android, avec replis sur l'événement `online` et sur l'ouverture de l'application.
```

---

#### T-35 · Addendum : sécurité, exploitation, hygiène du dépôt

- **Sources :** DT §2.2 n° 7, 8, 15 à 20, 27 à 34 ; AUD §3 (Gitleaks payant) et §6 (hygiène du dépôt).
- **Décision :** AUTOFIX.
- **Emplacements et textes :**

Addendum §C, ajouter au tableau, puis corriger S10 et S11 :
```markdown
| Second facteur | FR-43 | TOTP (RFC 6238) ; secret chiffré |
| Suspension | FR-5, FR-35 | Jeton d'accès de 15 min ; `is_active` vérifié à chaque requête (ou liste de révocation dans Redis) |
| Exposition | NFR-7, NFR-8 | `/v1/ai/classify` non exposé par le proxy ; `/metrics` sur le réseau interne ; délai d'expiration et taille maximale du corps au proxy ; photos sur un domaine distinct |
```
Ligne S10, colonne FR/NFR : `NFR-10` → `NFR-17`. Ligne S11 : garder `NFR-7`.

Addendum, nouveau §F :
```markdown
## F. Exploitation

- **Déploiement :** `docker compose pull && docker compose up -d` ; migrations Alembic avant le démarrage de la nouvelle version ; retour arrière en relançant le tag précédent. Python 3.12 exécuté via Docker ou `uv`, quel que soit le Python du poste.
- **Sauvegardes (NFR-15) :** `pg_dump` quotidien chiffré hors site ; versionnement du stockage objet ; exercice de restauration avant les données réelles.
- **Supervision (NFR-16) :** journaux Docker au hackathon, CloudWatch au pilote ; les 4 alertes de NFR-16.
- **Clés :** fichier d'environnement au hackathon ; KMS au pilote ; chiffrement du disque et de la base au pilote (NFR-17).
- **Fonds de carte :** tuiles publiques d'OpenStreetMap pour la démo seulement ; fournisseur ou serveur propre au pilote.
- **Modularité :** un module n'accède jamais aux tables d'un autre, il passe par son service.
- **Stockage objet :** choisir entre MinIO, Garage et SeaweedFS avant H24.
```

Addendum, nouveau §H :
```markdown
## H. Hygiène du dépôt public (epic E0, porte H24)

- `TerangaCycle AI/` n'est jamais suivi ; test CI : `git ls-files` ne contient aucun chemin `TerangaCycle AI/`.
- `.env.example` liste toutes les variables (`ENV`, `DEMO_MODE`, clés JWT, pepper, clé AES) avec des valeurs factices ; démarrer avec `ENV=production` sans les secrets requis échoue.
- `SECURITY.md` indique un canal privé de signalement et un délai de réponse.
- `main` protégée : PR obligatoire, CI verte requise, pas de *force push* ; *secret scanning*, *push protection* et Dependabot (pip, npm, Docker, GitHub Actions) activés.
- Gitleaks lancé en binaire (licence MIT) plutôt que par `gitleaks-action` si le dépôt passe dans une organisation GitHub.
```

### Sévérité low

#### T-36 · Conséquences testables manquantes dans FR-7, FR-8, FR-9, FR-19, FR-24 et FR-30

- **Sources :** AUD #3 (rayon hors bornes), #8 (Taille de tas obligatoire), #9 (Numéro de suivi) et §3 (HEIC) ; DT E-I3 (201/200) et E-D3 (filtre par type) ; CAH P14 (miniatures) ; PB A4 (quelle confiance afficher) et §3.4 (filtre de l'écran 5) ; RUB (FR-19 et FR-30 sans conséquence).
- **Décision :** AUTOFIX.
- **Emplacements et textes :**

FR-7, ajouter aux Conséquences :
```markdown
- Sans Taille de tas, l'envoi est impossible.
- Le Numéro de suivi est unique, au format `TC-AAAA-NNNNNN`, l'année étant celle de la réception par le serveur ; deux créations simultanées obtiennent deux numéros distincts.
```

FR-8, ajouter :
```markdown
- Le serveur n'accepte que JPEG, PNG et WebP (415 sinon) ; une photo HEIC est convertie en JPEG sur l'appareil avant l'envoi.
```

FR-9, ajouter :
```markdown
- La première réception renvoie 201 ; un renvoi par le même auteur ou le même appareil renvoie 200 avec le même Numéro de suivi.
- La réponse 409 ne contient ni Numéro de suivi, ni Statut, ni Position.
```

FR-19, ajouter :
```markdown
**Conséquences :**
- Le compteur affiche le nombre exact de Signalements en attente d'envoi et revient à 0 après une synchronisation réussie.
- Le bouton « Réessayer » lance l'envoi immédiatement ; sans réseau, il affiche « Toujours hors ligne ».
```

FR-24, ajouter aux Conséquences :
```markdown
- Sans réglage, le rayon est de 5 km ; une valeur hors de 1 à 10 km est refusée (422).
- La liste est filtrable par Type de déchet.
- Le Score de confiance affiché est celui de la Classification serveur ; si le Type de déchet retenu a été corrigé par un humain, l'élément affiche « Type confirmé par un humain ».
- La liste charge des miniatures de 30 Ko au plus ; la photo complète ne se charge qu'à l'ouverture d'un Signalement.
```

FR-30, ajouter :
```markdown
**Conséquences :**
- Chaque Mission figure avec sa date, son Type de déchet retenu, son Poids déclaré et son Statut de Mission ; le total des kg collectés est affiché.
- Une Preuve `contestée` (FR-41) y apparaît comme telle.
```

---

#### T-37 · Feuille de route et non-objectifs : wolof, SMS, points, tuiles

- **Sources :** CAH E9 (wolof rétrogradé sans décision) et E18 (points), DT E-D6 (wolof non journalisé) et E-C5 (tuiles OSM), PB A16 (SMS et WhatsApp en mois 6 à 12) et A17.
- **Décision :** DÉCISION-PAR-DÉFAUT. Au hackathon, le wolof se limite à la préparation (NFR-13). L'écran de signalement en wolof arrive pendant le pilote, puis SMS et WhatsApp en mois 6 à 12, comme dans le Proposal.
  *Raison : une équipe de trois en 72 h, et un alignement sur le calendrier déjà remis au jury.* Journaliser le non-objectif wolof (US-06, L.69 du cahier).
- **Emplacements et textes :**

§9.2, remplacer « **Wolof, SMS, WhatsApp :** feuille de route du pilote. » par :
```markdown
- **Wolof :** préparation à la traduction au MVP (NFR-13) ; écran de signalement en wolof pendant le pilote (mois 3 à 6), relu par des locuteurs natifs.
- **SMS et WhatsApp :** après le pilote (mois 6 à 12, comme annoncé dans le Proposal).
- **Points citoyens** (US-07), suivi des paiements des Collecteurs, intégration aux systèmes municipaux : feuille de route, sans échéance.
- **Fonds de carte :** les tuiles publiques d'OpenStreetMap sont réservées à la démo ; le pilote utilise un fournisseur ou un serveur de tuiles propre.
```

§8, remplacer « Interface wolof complète (seule la préparation à la traduction est exigée). » par :
```markdown
- Interface en wolof pendant le hackathon (seule la préparation à la traduction est exigée ; voir §9.2).
```

---

#### T-38 · UJ inégales, Awa incohérente, Vision et ton

- **Sources :** RUB (low : gabarit inégal, Awa anonyme dans UJ-1 puis titulaire d'un compte dans UJ-5, aucune UJ de vérification d'un Collecteur), CAH P14 (pilier « Inclusive »), PB §4 (Teranga, ton).
- **Décision :** AUTOFIX.
- **Emplacements et textes :**

UJ-5, remplacer toute l'entrée :
```markdown
- **UJ-5. Moussa supprime son compte.**
  - **Persona et contexte :** Moussa, 52 ans, a créé un compte pour suivre ses Signalements sur deux téléphones.
  - **Déroulé :** depuis son profil, il demande la suppression de son compte.
  - **Résolution :** son numéro est effacé ; ses Signalements validés restent dans les statistiques avec un auteur anonymisé ; ceux encore en attente sont supprimés (FR-5).
```

Nouvelle UJ-6, après UJ-5 :
```markdown
- **UJ-6. M. Ndiaye vérifie Ibrahima, récupérateur informel.**
  - **Point de départ :** Ibrahima se présente au service propreté avec son téléphone.
  - **Déroulé :** M. Ndiaye crée le compte Collecteur et le marque vérifié selon les critères retenus (§11, Q7).
  - **Résolution :** Ibrahima peut se connecter et voir les Signalements `validé` proches (UJ-3) ; l'action est inscrite au Journal d'audit. Réalise FR-35.
```

UJ-2, UJ-3 et UJ-4, ajouter une ligne « Persona et contexte » en tête :
```markdown
  - **Persona et contexte :** Fatou, 29 ans, agente du service propreté, sur ordinateur de bureau avec un réseau stable.
```
```markdown
  - **Persona et contexte :** Ibrahima, 41 ans, membre d'un GIE de pré-collecte, Android à 2 Go de RAM, données mobiles limitées.
```
```markdown
  - **Persona et contexte :** M. Ndiaye, 55 ans, chef du service propreté, rend compte au maire chaque mois.
```

§1, remplacer la puce « Inclusive » :
```markdown
- **Inclusive :** l'application fonctionne hors-ligne sur un Android d'entrée de gamme, guide par pictogrammes, et intègre les récupérateurs informels comme acteurs de premier rang ; le wolof suit pendant le pilote.
```

§7, puce « Ton », compléter :
```markdown
- **Ton :** consignes courtes, en français simple, avec pictogrammes ; des messages d'erreur qui disent quoi faire. Fidèle à la *teranga* : remercier le Citoyen, ne jamais le culpabiliser ; nommer le Collecteur comme un acteur reconnu ; un refus de Preuve donne la distance mesurée, sans accuser.
```

---

#### T-39 · Ajouts produit ou outillage sans usage pour la démo ni le pilote — IGNORER

| Proposition | Source | Raison |
|---|---|---|
| Indicateur calculé « zones prioritaires » | CAH E5, P5 | La Carte de chaleur filtrée suffit à UJ-4. Retouche : dans UJ-4, écrire « il repère deux zones prioritaires sur la Carte de chaleur ». |
| « Part corrigée » au Tableau de bord | CAH E6 | Elle est suivie par SM-8 au pilote, par une requête ; elle n'est pas utile à l'Administrateur commune. |
| Série temporelle `/analytics/timeseries` | DT E-D7 | Aucune UJ ne la demande. |
| Carte en points pour assigner depuis la carte | CAH E16, P13 | FR-28 est en Should ; on assigne depuis la liste. |
| Notification des Modérateurs à chaque nouveau Signalement | DT E-D2 | Le rafraîchissement toutes les 15 s suffit. |
| Les 8 alertes du dossier technique (dérive des scores, files hors-ligne, etc.) ; remontée de la taille de la File hors-ligne | DT E-O1, E-O3 | NFR-16 garde les 4 alertes utiles au pilote. |
| Bandit et Semgrep en CI | DT §2.2 n° 21 | Gitleaks, pip-audit, npm audit et Trivy suffisent pour 72 h ; à reconsidérer au pilote. |
| Pagination dans le PRD | DT E-P1, P-6 | C'est du « comment » : elle va dans l'addendum §A (T-34). Seule FR-22 fixe 50 éléments par page. |

---

#### T-40 · Points hors du champ d'un PRD — IGNORER

| Proposition | Source | Raison |
|---|---|---|
| Phases 2 à 4 de la feuille de route, modèle économique | CAH E13, P12 | Ils relèvent du pitch et du dossier de financement (voir §4). |
| SM-7 « 10 à 20 Collecteurs » | CAH E14 | On garde « au moins 20 », le chiffre remis au jury dans le Proposal. |
| Rôle UCG dans le Glossaire | CAH E15 | Un agent UCG délégué est un Administrateur commune ; aucun impact sur le MVP. |
| Doubler chaque code HTTP d'un comportement visible | RUB (low) | C'est traité au cas par cas là où cela compte (FR-1, FR-7, FR-25, FR-29) ; le reste relève de la spécification UX. |
| « Complémentarité avec les applications existantes » | CAH §3 | C'est un message de pitch (voir §4). |

---

## 2. Questions pour Mia

| # | Question | Option recommandée |
|---|---|---|
| T-03 | Qui fixe le Type de déchet retenu ? | **A** : le Modérateur, à la validation, pré-rempli par le choix du Citoyen ou par la Classification serveur ; drapeau Désaccord IA si l'appareil diffère du serveur. |
| T-13 | Faut-il réordonner les portes ? | **A** : H24 vise un premier Modèle entraîné (le Modèle factice en repli) ; FR-17 et FR-18 à H48 ; FR-30 à H60. |
| T-14 | Mono-commune ou configuration par commune ? | **A** : une Zone active (Dakar pour la démo, la commune partenaire au pilote), refus en dehors avant la photo, multi-commune en non-objectif, phrase pour l'oral. |

---

## 3. Mises à jour mécaniques

### 3.1 Références au cahier des charges dans le corps du PRD

| Emplacement | Actuel | Remplacer par |
|---|---|---|
| FR-11 | `(NF-01)` | `(NFR-1)` |
| FR-17 | `(NF-06)` | `(SM-4)`. NF-06 du cahier n'a pas d'équivalent en NFR ; SM-4 le vérifie. |
| FR-32 | `(NF-03)` | `(NFR-3)` |
| §0 | « exigences NF-01 à NF-15 » | Inchangé : c'est une référence au cahier. |

### 3.2 `[ASSUMPTION]` à retirer, car ce sont des décisions

- §6.3 : `[ASSUMPTION : validation de Mia]` sur le vert (décision de Mia) ; le texte est remplacé par celui de T-31.
- §10 SM-2 : la ligne `[ASSUMPTION : le Proposal annonce…]` disparaît avec le nouveau SM-2 (T-15).
- FR-14 : `[ASSUMPTION]` sur l'asynchronisme (décision S12) ; remplacé par T-25.
- FR-4 : `[ASSUMPTION]` sur le refus du réentraînement ; c'est une décision par défaut (T-10).
- **À conserver :** FR-1 (+221), FR-33 (3 décimales), §6.1 (durées), plus les nouvelles balises posées dans ce triage.

### 3.3 §11 et §12

§11 : appliquer T-20. Q1 (Large ou Small) est fermée et Q7 (inscription, partage Figma) sort du PRD.

§12, remplacer toute la section :
```markdown
## 12. Décisions et hypothèses

### 12.1 Décisions validées par Mia (ne pas rouvrir)

- Modèle : MobileNetV3-Large par défaut ; bascule vers Small si NFR-1 dépasse 3 s à la mesure H24 (responsable : Aissatou).
- Métrique du Modèle : F1 macro ≥ 0,80 et rappel ≥ 0,70 par classe ; top-1 accuracy publiée en complément (SM-2).
- Rayon des Signalements proches : 5 km par défaut, réglable de 1 à 10 km (FR-24).
- Pilote : Taux de traitement ≥ 60 % sur 6 mois (SM-6).
- Pitch : 1 min 30, plus 2 à 3 min de questions.
- Déploiement de fin de hackathon : Docker Compose sur un serveur unique et un portable de secours ; AWS au pilote.
- Jeton Vert : `#187A50` à la place de `#1F8A5B`, dans toutes ses utilisations (§6.3).
- Lots de matière : extension, après la porte H48 (§4.12).
- Consentement (FR-4) : porte H24.
- Exigences de sécurité S1 à S12 de l'audit du 23/11 intégrées, dont la Classification serveur asynchrone (FR-14).

### 12.2 Décisions par défaut (journalisées dans `.memlog.md`, révisables par Mia)

- Suivi anonyme lié à l'appareil ; jamais de consultation par le seul Numéro de suivi (FR-3, FR-20, FR-21).
- Indicateurs : cohorte = Signalements reçus par le serveur dans la période ; délai médian depuis la réception ; « Kg collectés » (FR-31).
- Poids déclaré, avec la mention `pesé` ou `estimé`.
- Statut de Mission ; expiration à 48 h (FR-42) ; contrôle des Preuves par échantillon (FR-41) ; second facteur du Personnel avant le pilote (FR-43).
- Doublon probable : 50 m et 72 h.
- Positions arrondies avant l'acceptation d'une Mission (FR-24).
- Preuve de collecte hors-ligne : non-objectif du MVP.
- Refus du réentraînement possible, avec retrait à tout moment (FR-4, FR-13).
- Purge des photos « personne ou plaque visible » sous 24 h (FR-23).
- Rouge et Jaune : règles d'usage, sans nouveau jeton (§6.3).
- Wolof : préparation seule au hackathon ; écran de signalement pendant le pilote (§9.2).
- Réentraînement manuel et mensuel au pilote (FR-16).
- [Réponses de Mia à T-03, T-13 et T-14]

### 12.3 Hypothèses à confirmer

- FR-1 : seuls les numéros sénégalais (+221) sont acceptés au MVP ; 20 demandes d'OTP par heure et par IP ; plafond SMS à fixer avec la passerelle.
- FR-7 : précision maximale de 50 m. FR-29 : tolérance de 150 m plus la précision du Signalement, plafonnée à 50 m.
- FR-10 : 10 Signalements par heure et par compte connecté.
- FR-14 : file de classification bornée à 500 tâches.
- FR-24 et FR-33 : arrondi des positions à 3 décimales. FR-34 : cellules de 500 m, masquées sous 3 Signalements.
- FR-41 : échantillon de 5 % des Preuves. FR-42 : expiration à 48 h.
- §6.1 : durées de conservation, à valider avec la commune.
- NFR-16 : seuil d'alerte disque à 85 %.
- §11 Q6 : table provisoire Taille de tas → Poids estimé.
```

### 3.4 Cohérence du vocabulaire

**Frise de suivi et Statut :** remplacer « la frise des 4 états » par « la Frise de suivi » dans UJ-1 (moment clé) et FR-20. La définition (T-33) règle l'écart entre les 4 étapes et les 5 Statuts.

**« Kg valorisés » devient « Kg collectés » :** « valorisé » reste réservé aux Lots de matière.

| Emplacement | Actuel | Remplacer par |
|---|---|---|
| §1 Vision | « combien de kilos sont valorisés » | « combien de kilos sont collectés, par matière » |
| UJ-4 | « kg valorisés » | Voir T-02. |
| FR-31 | « Kg valorisés » | Voir T-02. |
| SM-C3 | « kg valorisés par Mission » | Voir T-04. |

**« Poids mesuré » devient « Poids déclaré » :** Glossaire, UJ-3, FR-29, FR-31 et SM-C3 (voir T-19).

**Taux de traitement :** formule de cohorte en T-02 ; SM-6 y renvoie.

**Dérive des termes du Glossaire :**

| Emplacement | Actuel | Remplacer par |
|---|---|---|
| UJ-3 | « missions dans un rayon de 5 km » | « Signalements `validé` dans un rayon de 5 km » |
| UJ-3 | « la mission » (minuscule, hors libellé d'interface) | « la Mission » ; le libellé « Accepter la mission » reste tel quel, entre guillemets |
| Titre de FR-24 | « Missions proches » | « Signalements `validé` proches » |
| UJ-2 | « visible des collecteurs » | « visible des Collecteurs » |
| UJ-2 | « désaccord IA » | « Désaccord IA » |
| FR-17, FR-24, FR-38, FR-39, UJ-3 | « type » seul | « Type de déchet » |
| FR-11 | « un score de confiance » | « un Score de confiance » |
| FR-24, UJ-3 | « confiance » | « Score de confiance » |
| FR-16, §9.1 | « modèle factice » | « Modèle factice » |
| FR-34 | « visiteur » | « Visiteur » |
| FR-1, FR-2, FR-5 | « utilisateur » | Toléré, défini par « Utilisateur connecté » (T-33). |
| FR-33, §6.1 | « positions » | « Positions » |

### 3.5 Renvois et traçabilité

- **§0 Sources :** ajouter `TerangaCycle AI – Handoff brief` (PDF, hors dépôt), décisions de l'équipe (cité dans `.memlog.md`).
- **§12** ne renvoie plus à « §6.3 et §7 » : réglé par sa réécriture.
- **§9.2, premier `[NOTE FOR PM]`** : remplacer « mais elle est hors démo. Il faut assumer clairement ce décalage devant le jury » par « et le Proposal la place déjà après le hackathon ; à l'oral, on assume ». Le Proposal ne promet pas de Lots pendant la démo (PB §5).
- **SM-7 :** « Valide FR-30 et FR-35 » devient « Valide FR-30, FR-31 (Collecteurs vérifiés actifs) et FR-35 ».
- **SM-C3 :** renvoie à FR-41 (T-04).
- **§6.2 :** lignes « Spam » et « Fausses preuves » (T-07, T-04) ; ajouter la ligne « Accès indus au Personnel » → FR-43.
- **Addendum §C :** S10 rattaché à NFR-17 ; S11 rattaché à NFR-7 (réécrit).
- **Addendum §E, dernière puce :** retirer « le cahier des charges (80 % sur 4 à 6 semaines) est à aligner », qui devient une action hors PRD (§4).
- **Identifiants :** vérifier la continuité. FR-1 à FR-43, NFR-1 à NFR-17, SM-1 à SM-9, SM-C1 à SM-C4, UJ-1 à UJ-6.

### 3.6 Journalisation dans `.memlog.md`

Ajouter une entrée `(decision)` par décision par défaut du §12.2. Ajouter aussi les écarts assumés avec les sources :
- US-06 (wolof) ;
- US-10 (« estimé » devenu « déclaré ») ;
- US-16 (délai médian au lieu du délai moyen) ;
- US-22 (conservation anonymisée) ;
- NF-05 (Modèle ≤ 8 Mo hors budget de la page) ;
- NF-07 (sauvegardes reportées au pilote, NFR-15).

Ajouter enfin une entrée `(event)` « triage des 5 relectures appliqué ».

---

## 4. Hors PRD : actions pour l'équipe

**Project Proposal (PDF remis au jury)**
- Si le PDF peut être redéposé : MobileNetV3-Small devient Large, et « deployment on AWS » devient « Docker Compose, AWS au pilote ».
- Sinon, préparer 4 phrases pour l'oral :
  1. « Large par défaut, Small si la latence dépasse 3 s ; mesure à H24. »
  2. « F1 macro, plus honnête avec des classes déséquilibrées ; la top-1 promise est aussi publiée. »
  3. « Portable d'abord, AWS au pilote, par souveraineté. »
  4. « Vert foncé pour l'accessibilité AA. »
- Ajouter une phrase « mono-commune au pilote, conçue pour être répliquée », si T-14 est retenue en option A.

**Pitch**
- Obtenir un témoignage de terrain : collecteur ou commune contactés (CAH E17). Responsable à désigner.
- Garder les messages de pitch : sens de *teranga*, complémentarité avec les applications existantes, modèle économique (abonnement des communes, commission sur les Lots, subventions), « chaque correction consentie devient un exemple ».

**Maquette Figma**
- Elle est figée (quota Figma) : ne pas la modifier.
- Reporter dans la spécification UX la liste des nodes (1:2 Accueil, 1:39 Capture, 1:57 Résultat IA, 1:97 Confirmation, 2:2 Missions, 2:35 Preuve, 2:65 Tableau de bord), **sans la clé du fichier**.
- Les captures du Proposal gardent `#1F8A5B` : l'annoncer à l'oral comme correction d'accessibilité.
- Vérifier le partage « Anyone with the link can view ».

**Documents sources**
- **`docs/cahier-des-charges.md` (responsable : Mia) :**
  - critère du pilote (80 % sur 4 à 6 semaines → 60 % sur 6 mois) ;
  - pitch (5 min → 1 min 30) ;
  - délai moyen → délai médian ;
  - poids estimé → Poids déclaré.
- **`docs/dossier-technique.md` :**
  - marquer comme remplacés le prétraitement (Resize 224 sans recadrage), `PendingReport`, `flushQueue` sans jeton, les 4xx renvoyés sans fin, le reclassement synchrone et le hachage salé du téléphone ;
  - renvoyer vers l'addendum.

**Dépôt (epic E0, avant H24, responsable proposé : Ahmadou)**
- Committer le `.gitignore` modifié.
- Ajouter `.env.example` et `SECURITY.md`.
- Protéger `main`, activer *secret scanning*, *push protection* et Dependabot.
- Ajouter `LICENSE` dès que Mia a tranché (H60).
- Avant de committer `_bmad-output/`, chercher la clé du fichier Figma dans tous les fichiers. Les rapports de relecture et ce triage n'en contiennent pas, mais il faut le vérifier.
- Exécuter Python 3.12 via Docker ou `uv` (le poste a la 3.15).

**Organisation**
- Confirmer l'inscription au hackathon et l'équipe de trois auprès des organisateurs (ancienne Q7).
- Démo : préparer les 10 photos locales, enregistrer la vidéo avant H60, mettre en cache les tuiles de la zone de démo (exigé par T-12, réalisé par l'équipe).
- Commune partenaire : préparer le dossier CDP (déclaration avant les données réelles, transfert hors Sénégal si AWS) ; valider les durées de conservation ; négocier l'incitation des Collecteurs (§11 Q5 et Q7).
