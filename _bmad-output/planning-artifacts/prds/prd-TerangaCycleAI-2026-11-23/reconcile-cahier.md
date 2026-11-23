# Réconciliation : `docs/cahier-des-charges.md` → PRD + addendum

> Source : `docs/cahier-des-charges.md` (version du 9 novembre 2026, 236 lignes).
> Cible : `prd.md` (40 FR, 14 NFR, 5 UJ, SM-1 à SM-8, SM-C1 à SM-C4) et `addendum.md`.
> Date : 2026-11-23. `prd.md` et `addendum.md` n'ont pas été modifiés.
> Les numéros de ligne `L.xx` renvoient au cahier des charges.

**Points exclus parce que déjà tranchés dans `.memlog.md` :**
- MobileNetV3-Large par défaut, Small en secours ;
- F1 macro plutôt que top-1 accuracy ;
- rayon de 5 km, réglable de 1 à 10 km ;
- pilote à 60 % sur 6 mois (au lieu de 80 % sur 4 à 6 semaines) ;
- pitch de 1 min 30 (au lieu de 5 min) ;
- Docker Compose en fin de hackathon ;
- vert `#187A50` ;
- Lots de matière après la porte H48 ;
- consentement à la porte H24 ;
- audit S1 à S12 intégré.

Sur ces sujets, seuls les **effets de bord non couverts** par la décision sont signalés.

---

## 1. Couverture US / NF

### 1.1 User stories US-01 à US-22

Légende :
- **C** : couverte ;
- **P** : partiellement couverte (un critère d'acceptation est perdu ou affaibli) ;
- **D** : couverte par une décision journalisée ;
- **NC** : non couverte.

| US | Prio source | FR / NFR / SM du PRD | État | Critère perdu ou affaibli |
|---|---|---|---|---|
| US-01 Signaler avec photo | Must | FR-7, FR-8, FR-17, UJ-1 | P | Le PRD n'exige nulle part que le Numéro de suivi soit **affiché** au Citoyen (accusé de réception). FR-7 dit seulement que le serveur l'attribue ; seul UJ-1, illustratif, le montre. Les critères « photo obligatoire », « GPS automatique » et « 280 caractères » sont couverts. |
| US-02 Type proposé | Must | FR-11, FR-12, NFR-1 | C | Les critères « 3 s » et « seuil à 60 % » sont repris. |
| US-03 Corriger | Must | FR-13 | C | Le choix en un toucher et l'enregistrement pour le réentraînement sont repris. Le refus du réentraînement (FR-4) est une `[ASSUMPTION]` du PRD, pas du memlog. |
| US-04 Hors réseau | Must | FR-17, FR-18, FR-19, FR-9, SM-4 | C | Le badge « en attente », l'envoi automatique et l'absence de doublon sont repris. |
| US-05 Suivre l'état | Must | FR-20, FR-21 | P | La notification à **chaque** changement est réservée au Citoyen **connecté** (FR-21), alors que le parcours principal est anonyme (UJ-1). Le PRD ne dit pas comment un anonyme suit son Signalement : UJ-1 montre Awa, anonyme, qui voit « Validé » puis « Collecté », mais aucun FR ne le permet. |
| US-06 Wolof | Should | NFR-13, §8, §9.2 | NC | Le Should de la source (sélecteur de langue, écran de signalement traduit) est rétrogradé en non-objectif. Seule la préparation i18n reste exigée. Aucune décision du memlog ne l'explique : la source prévoit de **couper** le wolof en plan B si la porte n'est pas atteinte, pas de l'exclure d'avance. Les pictogrammes restent couverts par FR-11. |
| US-07 Points | Could | §8 (non-objectif) | D* | Le cahier le classe en Could, c'est-à-dire après le hackathon. Le PRD l'exclut sans le renvoyer à la feuille de route du pilote. Écart mineur. |
| US-08 Missions proches | Must | FR-24 | D | Le rayon a été tranché. Les critères « type et photo visibles » et « tri par distance » sont repris. |
| US-09 Accepter | Must | FR-25 | C | Le code 409 et le collecteur unique sont repris. |
| US-10 Preuve photo | Must | FR-29 | P | La source parle d'un **poids estimé** saisi en kg. Le PRD l'appelle « Poids mesuré » (glossaire, FR-29, UJ-3 « 15 kg »), ce qui suppose une pesée. Les récupérateurs informels n'ont pas toujours de balance. Le changement de sens n'est pas journalisé. |
| US-11 Itinéraire | Should | FR-27 | C | — |
| US-12 Déclarer un lot | Should | FR-38 | D | — |
| US-13 Voir les lots | Should | FR-39 | D | — |
| US-14 Réserver un lot | Could | FR-40 | D | — |
| US-15 Carte de chaleur | Must | FR-32, NFR-3 | C | Les filtres par période, type et statut, et le seuil de 2 s pour 5 000 points sont repris. |
| US-16 Indicateurs | Must | FR-31 | P | Le « délai moyen » de la source devient un « délai médian ». La médiane est cohérente avec le §6 de la source, mais le changement n'est pas journalisé. Les « zones prioritaires » du MVP (point 5, L.60) n'ont pas d'indicateur (voir l'écart E5). |
| US-17 Export | Must | FR-33 | C | Les formats CSV et GeoJSON, sans donnée personnelle, sont repris. |
| US-18 Assigner | Should | FR-28 | P | La précision « depuis la carte » est perdue : il n'y a pas de carte en points pour l'Administrateur, seulement une carte de chaleur. |
| US-19 Modérer | Must | FR-22, FR-23 | C | Le motif obligatoire et la journalisation sont repris. |
| US-20 Comptes collecteurs | Must | FR-35 | C | La création, la suspension, la vérification et le Journal d'audit sont repris. |
| US-21 Connexion | Must | FR-1, FR-2, FR-7, FR-10 | C | L'OTP et le signalement anonyme avec limite de débit sont repris. |
| US-22 Données personnelles | Must | FR-4, FR-5 | P | La source demande la suppression « du compte **et des données associées** ». Le PRD conserve les Signalements (photo, Position précise) avec un auteur anonymisé. Rien n'est prévu pour un Citoyen **anonyme**, ni pour retirer une photo précise. Le choix n'est pas journalisé. |

**Bilan :**
- aucune US n'est perdue au sens strict, sauf **US-06**, rétrogradée en non-objectif sans décision ;
- **6 US sont partiellement couvertes** : US-01, US-05, US-10, US-16, US-18, US-22.

### 1.2 Exigences non fonctionnelles NF-01 à NF-15

| NF | Exigence source | NFR / FR du PRD | État | Écart |
|---|---|---|---|---|
| NF-01 | Classification en moins de 3 s | NFR-1, FR-11 | C | Le PRD est plus strict : Android à 2 Go au lieu d'un milieu de gamme. |
| NF-02 | p95 sous 300 ms à 50 req/s | NFR-2 | C | — |
| NF-03 | Carte en moins de 2 s pour 5 000 points, avec clustering | NFR-3, FR-32 | C | Le mot « clustering », qui concerne la carte en points, disparaît. Mineur. |
| NF-04 | Image de 300 Ko au plus | NFR-4, FR-8 | C | — |
| NF-05 | Page d'accueil de 500 Ko au plus, hors images | NFR-5 | P | Le PRD exclut **aussi le Modèle** du budget, sans décision ni budget séparé pour le Modèle. Sur un forfait épuisé (persona Awa), le premier téléchargement du Modèle n'est plus encadré. |
| NF-06 | 100 % des champs conservés hors-ligne | FR-17, SM-4 | C | — |
| NF-07 | 99 % de disponibilité, sauvegardes quotidiennes | NFR-7 | P | **Les sauvegardes quotidiennes et la cible de 99 % sont perdues.** La décision f (Docker Compose) ne justifie pas l'abandon des sauvegardes, surtout pour le pilote. |
| NF-08 | TLS 1.2 en transit **et chiffrement au repos** | NFR-8, §6.1 | P | Le chiffrement au repos est réduit au seul numéro de téléphone. Rien n'est dit pour les photos, la base et les sauvegardes. |
| NF-09 | Aucune route sensible sans jeton ni rôle | FR-3, NFR-9 | C | — |
| NF-10 | **Ni visage ni plaque conservés** ; position arrondie dans les exports | FR-4, FR-23, FR-33, addendum S9 | P | Le PRD met une consigne et une modération avant exposition, mais aucune exigence ne dit que la photo **n'est pas conservée** (ou est floutée ou rejetée) si elle montre un visage ou une plaque. Une photo rejetée reste stockée 12 mois (§6.1). |
| NF-11 | Pas d'API d'IA étrangère ; export CSV/GeoJSON | §6.4, FR-33 | C | — |
| NF-12 | Contraste AA, 44 px, **pictogrammes** | NFR-12, FR-11, §7 | P | Les pictogrammes sortent de l'exigence d'accessibilité, où ils sont remplacés par les libellés pour lecteur d'écran. Ils restent dans FR-11 pour les Types seulement, pas pour les Statuts ni les actions. |
| NF-13 | Android 8+, Chrome, 2 Go | NFR-6 | C | — |
| NF-14 | Couverture de 60 %, lint | NFR-11 | C | — |
| NF-15 | Licence ouverte et **documentation du Modèle** | §6.3, Q.2 du §11 | P | Le choix de licence est reporté « avant le pilote », alors que la source et le pitch (souveraineté : « code sous licence ouverte ») la supposent **dans le dépôt dès la démo**. La fiche du Modèle n'apparaît que pour lister les licences des données, sans livrable ni contenu minimal. |

**Bilan :**
- aucune NF n'est totalement absente ;
- **6 NF sont affaiblies** : NF-05, NF-07, NF-08, NF-10, NF-12, NF-15.

---

## 2. Écarts

Gravité : **H** (risque pour la démo, le pilote ou la conformité), **M** (moyen), **B** (bas).

| # | Gravité | Source | PRD / addendum | Écart (aucune décision du memlog ne l'explique) |
|---|---|---|---|---|
| E1 | **H** | §6, Risques et plans B (L.186-199) | Aucune section | **Le PRD n'a aucun registre des risques ni de plan B.** Seules les menaces d'abus sont traitées (§6.2). Sont perdus : les 10 photos préparées avec la correction en direct (modèle imprécis), la **vidéo de la démo complète**, les tuiles mises en cache, le mode démo avec comptes de test, la règle « couper une extension plutôt que repousser » et la règle de repos. NFR-7 ne garde que le portable de secours. |
| E2 | **H** | NF-07 (L.139) | NFR-7 | Les sauvegardes quotidiennes et la cible de 99 % sont abandonnées. Pour un pilote avec des données réelles, l'absence de sauvegarde est un risque de perte et de conformité. |
| E3 | **H** | NF-10 (L.142) | FR-4, FR-23, §6.1 | « Ni visage ni plaque conservés » devient une simple consigne. Il manque un motif de rejet dédié, une suppression ou un floutage de la photo concernée, et une durée de conservation courte pour les photos rejetées. |
| E4 | **M** | NF-08 (L.140) | NFR-8, §6.1 | Le chiffrement au repos ne couvre que le numéro, pas le stockage objet, la base ni les sauvegardes. |
| E5 | **M** | MVP point 5 « zones prioritaires » (L.60) ; indicateur « Zones identifiées » (L.208) | FR-31, UJ-4 | UJ-4 « identifie deux zones prioritaires », mais aucun FR ne calcule de zone au-dessus d'un seuil. L'Administrateur doit le déduire à l'œil sur la Carte de chaleur. |
| E6 | **M** | Indicateurs d'impact pour le jury (L.201-211) | FR-31, §10 | Sur les 7 indicateurs « à montrer au jury », 3 ne sont pas affichés dans le Tableau de bord : les zones identifiées, les **acteurs informels intégrés** (Collecteurs vérifiés actifs) et la **part corrigée par les utilisateurs**. Les deux derniers n'existent qu'en SM-7 et SM-8 pour le pilote. Or « les acteurs informels intégrés » porte l'argument « Inclusive ». |
| E7 | **M** | US-05 (L.88) | FR-20, FR-21, UJ-1 | Le suivi et la notification d'un Citoyen **anonyme** ne sont pas spécifiés. UJ-1 (Awa, anonyme) contredit FR-21 (notification réservée aux comptes connectés). |
| E8 | **M** | US-22 (L.125) | FR-5, UJ-5 | « Suppression des données associées » devient « auteur anonymisé, Signalements conservés ». Le compromis est défendable, mais il n'est ni journalisé ni expliqué. Rien n'est prévu pour un anonyme (qui peut demander la suppression d'un Signalement par son Numéro de suivi ?). |
| E9 | **M** | US-06 (L.89), thème « Inclusive » (L.29), extension « wolof, au moins l'écran de signalement » (L.69) | §8, §9.2, NFR-13 | Le wolof passe de Should ou extension à non-objectif pour le hackathon. La source le traite comme la **première** extension à couper si besoin, pas comme une exclusion de principe. Il faut une décision explicite ou une remise en extension après H48. |
| E10 | **M** | US-10 « poids estimé saisi » (L.98) | Glossaire « Poids mesuré », FR-29, UJ-3 | Glissement de sens de « estimé » à « mesuré », sans balance prévue. Effet : le KPI kg valorisés et SM-C3 reposent sur une donnée présentée comme une pesée. |
| E11 | **M** | NF-15 (L.147) ; pitch « code sous licence ouverte » (L.27, L.222) | §6.3, Q.2 du §11 | Le choix de licence est reporté au pilote. La démo ne peut pas revendiquer « code sous licence ouverte » si le dépôt n'a pas de `LICENSE`. La fiche du Modèle n'est pas un livrable. |
| E12 | **B** | NF-05 (L.137) | NFR-5 | Le Modèle est exclu du budget de 500 Ko sans budget de remplacement ni décision journalisée. |
| E13 | **B** | Feuille de route après le hackathon (L.175-182) | §10, §11 | Les phases 2 à 4 (consolidation, partenariat institutionnel, passage à l'échelle) et le **modèle économique** (abonnement des communes, commission sur la valorisation, subventions) disparaissent. Le PRD ne garde que le pilote. |
| E14 | **B** | Pilote : « 10 à 20 collecteurs » (L.179) | SM-7 « au moins 20 » | Le plancher du PRD est le plafond de la source. La décision d (60 % sur 6 mois) ne couvre pas cet effectif. |
| E15 | **B** | Acteurs : « Administrateur (commune, **UCG**) » (L.51) | Glossaire « Administrateur commune » | L'UCG, l'opérateur national, disparaît du rôle. Cela compte pour le partenariat de la phase 3. |
| E16 | **B** | US-18 « depuis la carte » ; NF-03 « clustering » | FR-28, FR-32 | Aucune carte en points pour le Personnel. L'assignation depuis la carte n'est pas possible avec la seule Carte de chaleur. |
| E17 | **B** | Pitch : « témoignage d'un acteur de terrain », « collecteur ou commune contacté » (L.172, L.223, L.235) ; « plan de sortie **testé** » (L.230) | §6.4 « plan de sortie documenté », §11 | Le témoignage de terrain n'est suivi nulle part. Le plan de sortie passe de « testé » à « documenté ». |
| E18 | **B** | US-07 Could (L.90) | §8 | Les points citoyens sont exclus sans être renvoyés à la feuille de route. |

---

## 3. Idées qualitatives perdues

| Idée de la source | Où dans la source | Ce qu'en fait le PRD | Perte |
|---|---|---|---|
| **Inclusion à quatre leviers** : wolof et français, hors-ligne, pictogrammes, canal SMS ou WhatsApp, récupérateurs **rémunérés** | L.29 | Le bullet « Inclusive » du §1 ne garde que le hors-ligne et les acteurs informels | Le wolof, les pictogrammes, le canal sans smartphone et la rémunération disparaissent de la vision. Le jury jugera sur les trois mots clés. |
| **Collecteurs comme relais** pour les personnes sans smartphone ni réseau | L.236 | §2.2 range ces personnes en non-utilisateurs | L'idée d'un signalement par procuration (le collecteur signale pour un riverain) est perdue. Elle est réalisable sans SMS dès le MVP. |
| **La correction en direct comme fonctionnalité**, pas comme aveu d'échec | L.192 | FR-13 est purement technique | Le cadrage narratif « l'IA propose, l'humain confirme » est présent dans la description du §4.3, mais le plan B de démo associé est perdu. |
| **Contrainte de données mobiles du collecteur** (« données mobiles limitées ») | L.49 | Aucune NFR pour l'écran Missions (liste avec photos) | Le budget réseau ne couvre que le Citoyen (NFR-4, NFR-5). Il n'y a ni miniature ni chargement différé des photos de mission. |
| **Pictogrammes comme exigence d'accessibilité** (NF-12) et pas seulement comme décoration | L.144, L.89 | FR-11 pour les Types ; §7 « avec pictogrammes » | Rien n'exige de pictogrammes pour les Statuts (la frise des 4 états) ni pour les actions principales. C'est pourtant le levier pour les utilisateurs peu à l'aise avec l'écrit. |
| **Honnêteté envers le jury** | L.213 | §7 « Honnêteté », FR-37 | Conservée. Aucune perte. |
| **Complémentarité plutôt que concurrence** avec les applications existantes | L.232 | Absente | Hors périmètre d'un PRD : à garder dans le dossier de pitch. |
| **Différenciation par la valorisation** (« le cœur n'est pas le signalement ») | L.35 | `[NOTE FOR PM]` du §9.2, et décision sur les Lots | Assumée et journalisée. Aucune perte. |
| **Faible littératie, retour sonore** | Absents de la source | — | Le cahier des charges **ne contient pas** ces idées. Pas d'écart à signaler depuis cette source ; à vérifier dans le Proposal ou la maquette. |
| **Ton** | La source ne fixe pas de ton explicite | §7 « consignes courtes, français simple, pictogrammes » | Le PRD est plus précis que la source. Aucune perte. |

---

## 4. Propositions de correction précises

Chaque proposition indique l'emplacement dans `prd.md` ou `addendum.md`. Si une proposition est refusée, il faut **journaliser la décision** dans `.memlog.md`.

### P1. Ajouter un §9.3 « Risques et plans B » (E1)

**Emplacement :** `prd.md`, après le §9.2.

**Texte proposé :**

> ### 9.3 Risques de démo et plans B
>
> | Risque | Plan B exigé | Exigence liée |
> |---|---|---|
> | Modèle imprécis sur photos locales | 10 photos locales préparées et testées ; la Correction est montrée comme une fonctionnalité | FR-13, SM-2 |
> | Réseau instable dans la salle | Vidéo de la démo complète enregistrée avant H60 ; portable servant de serveur ; tuiles de carte de la zone de démo mises en cache | NFR-7 |
> | Périmètre trop large | Si une porte n'est pas atteinte, couper une extension (Lots, wolof) plutôt que repousser la suite | §9.1 |
> | Service externe (SMS, tuiles) | Mode démonstration pour l'OTP ; tuiles en cache | FR-6 |
> | Abus pendant la démo publique | Comptes de test du jeu de démonstration | FR-37, FR-10 |

**Compléter aussi NFR-7, colonne Seuil :** « Service et portable de secours prêts ; **vidéo de secours de la démo complète** ; tuiles de la zone de démo disponibles sans réseau ; sondes de vie et de disponibilité ».

### P2. NFR-7 : sauvegardes et disponibilité (E2)

**Emplacement :** `prd.md` §5, NFR-7. Scinder en deux lignes :

- **NFR-7a (Démo) :** la ligne actuelle, complétée selon P1.
- **NFR-7b (Pilote) :**
  - **Exigence :** disponibilité et sauvegardes.
  - **Seuil :** 99 % de disponibilité visée ; sauvegarde quotidienne de la base et du stockage objet ; restauration testée au moins une fois avant la collecte de données réelles.
  - **Vérification :** supervision et exercice de restauration.

**Emplacement secondaire :** `addendum.md` §C, « Points d'infrastructure » : ajouter « Sauvegarde quotidienne chiffrée (`pg_dump` et stockage objet), hors du serveur hôte ».

### P3. NF-10 : visages et plaques (E3)

**Emplacement :** `prd.md` §4.6, FR-23, ajouter aux Conséquences :

> - Le motif de rejet « Personne ou plaque visible » existe. Une photo rejetée pour ce motif est supprimée du stockage sous 24 h, et seule la décision reste au Journal d'audit.
> - Les photos des Signalements `rejeté` pour un autre motif sont conservées 30 jours au plus `[ASSUMPTION]`.

**Mettre à jour aussi :**
- le tableau de conservation du §6.1 : ajouter la ligne « Photos de Signalements rejetés : 30 jours ; si visage ou plaque : 24 h » ;
- `addendum.md` §C, ligne S9 : « Consigne de capture, modération avant exposition, **purge de la photo** si visage ou plaque ».

### P4. NF-08 : chiffrement au repos (E4)

**Emplacement :** `prd.md` §5, NFR-8.

- **Nouvel intitulé :** « Transport et repos ».
- **Nouveau seuil :** « TLS 1.2 minimum, HSTS ; chiffrement au repos du volume de base, du stockage objet et des sauvegardes ».
- **Nouvelle vérification :** « Scan SSL et revue de configuration ».

### P5. Indicateurs d'impact au Tableau de bord (E5, E6)

**Emplacement :** `prd.md` §4.9, FR-31. Ajouter au tableau :

| Indicateur | Définition |
|---|---|
| Zones prioritaires | Cellules de la Carte de chaleur ou Zones au-dessus d'un seuil de Signalements `validé` non collectés sur la période `[ASSUMPTION : seuil configurable]` |
| Collecteurs vérifiés actifs | Collecteurs vérifiés ayant au moins une Preuve acceptée sur la période |
| Part corrigée | Part des classifications corrigées par un humain sur la période |

**Ajouter aussi une conséquence :** « Les zones prioritaires sont mises en évidence sur la Carte de chaleur (FR-32). » La gate reste H60. Si le temps manque, seules les zones prioritaires sont obligatoires, car elles réalisent UJ-4.

### P6. Suivi et notification d'un anonyme (E7)

**Emplacement :** `prd.md` §4.5, FR-20, ajouter aux Conséquences :

> - Un Citoyen anonyme voit les Signalements créés depuis son appareil (liste conservée sur l'appareil) et peut consulter un Signalement par son Numéro de suivi.
> - Le Numéro de suivi est affiché sur l'écran 4 dès sa réception (accusé de réception, US-01).

**FR-21 :** remplacer « Le Citoyen connecté » par « Le Citoyen, connecté ou anonyme sur l'appareil d'origine, » pour la notification dans l'application. La notification push anonyme peut rester `[ASSUMPTION : si autorisée, rattachée à l'appareil]`. Sinon, corriger UJ-1 pour qu'Awa voie les Statuts en rouvrant l'application.

### P7. Suppression des données (E8)

**Emplacement :** `prd.md` §4.1, FR-5, ajouter aux Conséquences :

> - À la suppression, les photos et les Positions précises des Signalements `en attente de modération` ou `rejeté` sont supprimées. Les Signalements `validé`, `assigné` ou `collecté` sont conservés avec un auteur anonymisé, parce qu'ils fondent les indicateurs et les Preuves des Collecteurs `[ASSUMPTION]`.
> - Un Citoyen anonyme peut demander le retrait d'un Signalement non encore `validé` depuis l'appareil d'origine.

**Journaliser** l'écart avec US-22 (« données associées ») dans `.memlog.md`.

### P8. Wolof (E9)

**Option recommandée :** `prd.md` §9.2, remplacer « Wolof, SMS, WhatsApp : feuille de route du pilote » par :

> - **Écran de signalement en wolof** (US-06) : extension, seulement après la porte H48, première coupée si le temps manque.
> - **SMS, WhatsApp, wolof complet** : feuille de route du pilote.

Puis, au §8, remplacer « Interface wolof complète (seule la préparation à la traduction est exigée) » par « Interface wolof complète au hackathon ».

**Sinon :** journaliser le non-objectif dans `.memlog.md`, en citant US-06 et L.69.

### P9. Poids estimé ou mesuré (E10)

**Emplacement :** `prd.md` §3, Glossaire. Remplacer la définition du Poids mesuré par :

> **Poids déclaré** : poids saisi par le Collecteur dans la Preuve de collecte, estimé ou pesé, avec l'indication `pesé` / `estimé`.

**Répercuter la modification dans :**
- FR-29 ;
- FR-31 (« Kg valorisés : somme des Poids déclarés… ») ;
- UJ-3 ;
- SM-C3.

**Alternative :** garder « mesuré » et ajouter au §11 une question « Les collecteurs ont-ils une balance ? ».

### P10. Licence et fiche du Modèle (E11)

**Emplacement :** `prd.md` §5, ajouter une ligne :

- **ID :** NFR-15.
- **Domaine :** Ouverture.
- **Exigence :** licence et fiche du Modèle.
- **Seuil :** un fichier `LICENSE` (MIT ou AGPL-3.0) est dans le dépôt **avant la démo** ; une fiche du Modèle est publiée, avec les données et leurs licences, F1 macro, rappel par classe, matrice de confusion, limites connues et version.
- **Vérification :** dépôt.

**Au §11, Q.2 :** remplacer « avant le pilote » par « avant H60 ».

### P11. Budget du Modèle (E12)

**Emplacement :** `prd.md` §5, NFR-5. Ajouter au seuil :

> Modèle ≤ `[ASSUMPTION : 6 Mo]`, téléchargé une seule fois puis mis en cache, avec la possibilité de signaler avant la fin du téléchargement (choix manuel du type).

### P12. Feuille de route et modèle économique (E13, E14)

**Emplacement :** `prd.md`, nouveau §10bis « Après le pilote » (ou une annexe dans `addendum.md`), en 4 lignes :

1. Consolidation : wolof complet, canal SMS ou WhatsApp, Lots, réentraînement ; critère : F1 macro stable sur les photos du pilote.
2. Partenariat institutionnel : commune ou UCG, avec un partenaire signé.
3. Passage à l'échelle : plusieurs villes, hébergement local.
4. Modèle économique : abonnement des communes, commission sur les lots valorisés, subventions.

**SM-7 :** aligner sur « 10 à 20 Collecteurs vérifiés actifs », ou journaliser le passage à au moins 20.

### P13. Rôle UCG et carte en points (E15, E16)

**Emplacements :**
- **Glossaire, Administrateur commune :** ajouter « ou opérateur public de collecte (UCG) ».
- **FR-28 :** ajouter « depuis une carte en points des Signalements `validé`, regroupés par clustering (NF-03) ». Autre solution : retirer « depuis la carte » et le journaliser.

### P14. Inclusion dans la vision et accessibilité (idées qualitatives)

**Emplacement :** `prd.md` §1, bullet « Inclusive ». Remplacer par :

> **Inclusive :** l'application fonctionne hors-ligne sur un Android d'entrée de gamme, guide par pictogrammes, et intègre les récupérateurs informels comme acteurs de premier rang. Le wolof et le canal SMS ou WhatsApp suivent au pilote ; d'ici là, un Collecteur peut signaler un dépôt pour un riverain sans smartphone.

**Emplacement :** `prd.md` §5, NFR-12. Ajouter au seuil :

> Chaque Type de déchet, chaque Statut de la frise et chaque action principale a un pictogramme accompagné d'un libellé.

**Emplacement :** `prd.md` §4.7. Ajouter une conséquence à FR-24 :

> La liste des Missions charge des miniatures de 30 Ko au plus ; la photo complète ne se charge qu'à l'ouverture de la Mission (données mobiles limitées).

### P15. Pitch et terrain (E17, E18)

**Emplacement :** `prd.md` §11. Ajouter les questions ouvertes suivantes :

> 8. **Témoignage de terrain** : quel collecteur ou quelle commune est contacté, et qui en est responsable ? Il porte SM-1 et la crédibilité du pilote.
> 9. **Plan de sortie** : documenté ou testé (restauration sur un autre hôte) avant le jury ?

**Emplacement :** §8. Remplacer « Points citoyens et classements par quartier » par « Points citoyens et classements par quartier (feuille de route, US-07 Could) ».

---

### Synthèse des décisions à journaliser si les propositions sont refusées

- US-06 : non-objectif du wolof (P8).
- US-10 : « mesuré » au lieu d'« estimé » (P9).
- US-16 : délai médian au lieu du délai moyen.
- US-22 : conservation des Signalements après suppression du compte (P7).
- NF-05 : exclusion du Modèle du budget (P11).
- NF-07 : sauvegardes et cible de 99 % (P2).
- NF-15 : licence reportée au pilote (P10).
- SM-7 : effectif de 20 Collecteurs (P12).
