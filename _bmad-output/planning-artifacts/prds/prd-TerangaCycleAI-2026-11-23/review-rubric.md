# Revue qualité du PRD — TerangaCycle AI

> Grille : `.claude/skills/bmad-prd/assets/prd-validation-checklist.md`. Documents relus : `prd.md`, `addendum.md`, `.memlog.md` (état au 2026-11-23T14:39). Enjeu retenu : démo de 72 h devant le jury MakeAfrica, puis pilote réel de 6 mois avec une commune ; le PRD alimente l'UX, l'architecture et les stories.

## Verdict global

Le PRD tient bien sur l'essentiel : une thèse nette (la « chaîne de confiance »), un glossaire riche, des portes H24/H48/H60 qui couvrent toutes les FR, des contre-indicateurs réfléchis et des NFR chiffrées. En revanche, la clarté du « fini » est mince exactement là où la thèse se joue. Le suivi du Citoyen anonyme (le parcours phare UJ-1) n'est pas spécifié, les indicateurs du Tableau de bord contredisent le modèle « un et un seul Statut », et le maillon « preuve » ne repose que sur un géorepérage de 150 m, sans échantillonnage, sans mode hors-ligne et sans règle de précision GPS. Rien ne bloque le travail H24, mais ces points sont à corriger avant de découper les stories H48/H60 et avant le dossier pilote.

## Décisions — adequate

Les décisions sont présentées comme des décisions, pas comme des « considérations ». Le choix F1 macro contre top-1 accuracy est assumé avec ce qu'il coûte (écart avec le Proposal, §10 SM-2, addendum §E). Docker Compose contre AWS est justifié (addendum §E). Le report des Lots de matière porte un `[NOTE FOR PM]` placé à une vraie tension (§9.2 : « le cœur n'est pas le signalement », alors que la valorisation est hors démo). Les non-objectifs (§8) disent aussi ce qu'on abandonne, par exemple « Estimation du poids par IA : la table de Taille de tas suffit ».

Deux faiblesses toutefois. Plusieurs questions ouvertes n'ont ni responsable ni échéance, et l'une d'elles conditionne une porte. Une tension structurante pour le pilote, la motivation des Collecteurs, n'est pas nommée.

### Constats
- **[medium]** Questions ouvertes sans responsable, dont une qui bloque H48 (§11 Q3 à Q7). Seules Q1 et Q2 ont un responsable. Q6 (« Table de conversion Taille de tas → Poids estimé : valeurs par type à obtenir d'un collecteur ») conditionne le « Poids estimé » affiché par FR-24, livré à H48, et le Poids estimé de UJ-3. Q5 (âge minimum, relecture juridique du consentement) conditionne FR-4 en pilote. *Correctif :* donner à chaque question un responsable et une échéance exprimée en porte (H24, H48, H60, avant pilote). Pour Q6, prévoir une table provisoire explicitement marquée `[ASSUMPTION]` pour la démo.
- **[medium]** Tension non signalée sur l'incitation des Collecteurs pendant le pilote (§2.1, §8, SM-7). Le JTBD du Collecteur est « être reconnu et payé ». Or le paiement réel et les points sont des non-objectifs (§8), et SM-7 vise pourtant « au moins 20 Collecteurs vérifiés actifs ». Le PRD ne dit pas qui rémunère la collecte pendant le pilote (commune, GIE existant, bénévolat) ni pourquoi un récupérateur informel utiliserait l'application. *Correctif :* ajouter un `[NOTE FOR PM]` en §9.2 ou §11 : modèle de rémunération ou de reconnaissance pendant le pilote, à négocier avec la commune, et risque associé pour SM-7.

## Substance contre façade — strong

Les personas sont utiles. Chaque rôle du §2.1 pilote au moins une FR, et le Recycleur est explicitement marqué « extension ». Les UJ portent des cas limites réels : seuil à 60 %, Mission déjà prise. La Vision est spécifique au projet : la photo hors-ligne en 30 s, la preuve géorepérée et l'historique des informels ne se transposent pas à un autre PRD de la catégorie. Les NFR ont des seuils et des méthodes de vérification (§5) ; on n'y trouve pas de « scalable / sécurisé » générique.

### Constats
- **[medium]** « Kg valorisés » mesure de la collecte, pas de la valorisation (§1 Vision « combien de kilos sont valorisés » ; FR-31 « Kg valorisés : Somme des Poids mesurés des Preuves acceptées » ; SM-C3). Rien dans le MVP ne trace ce qui est recyclé : les Lots de matière sont hors démo. Présenter des kilos collectés comme « valorisés » contredit l'engagement du §7 (« aucun objectif comme un résultat ») devant un jury, puis devant une commune. *Correctif :* renommer l'indicateur « Kg collectés », ce qui l'aligne aussi sur FR-30. Réserver « valorisés » aux Lots de matière réservés (FR-40).
- **[low]** Le pilier « Souveraine » promet un « Plan de sortie documenté vers un hébergement au Sénégal » (§6.4), sans FR, sans responsable et sans échéance. *Correctif :* rattacher ce plan à Q4 (§11) avec la même échéance « avant pilote ».

## Cohérence stratégique — adequate

La thèse est explicite (§1 : « le problème n'est pas l'absence de signalement : c'est la chaîne de confiance ») et l'ordre des portes la suit. H48 livre la boucle signaler → modérer → collecter, et SM-1 valide précisément cette boucle. Les contre-indicateurs SM-C1 à SM-C4 sont pertinents et reliés aux SM qu'ils équilibrent. Le type de MVP (résoudre un problème, prouver une boucle) est cohérent avec le périmètre.

La chaîne de confiance a cependant un maillon faible, la preuve. Et deux éléments que la thèse met en avant (l'historique du Collecteur, le hors-ligne) sont relégués en fin de plan ou hors du MVP.

### Constats
- **[high]** Le maillon « preuve » n'a aucune vérification humaine spécifiée (§6.2 « vérification par échantillon du Personnel » ; SM-C3 « part de Preuves contestées lors de l'échantillonnage »). Aucune FR ne permet au Personnel d'échantillonner, de contester ou d'invalider une Preuve de collecte. Aucun statut « contestée » n'existe, et le contre-indicateur SM-C3 n'est donc pas mesurable. FR-29 ne contrôle que la distance, la présence des photos et un poids > 0 : rien n'empêche de réutiliser les mêmes photos d'une Mission à l'autre ou de gonfler le poids. *Correctif :* ajouter une FR (par exemple après FR-29) : échantillonnage d'au moins X % des Preuves par le Personnel, statut de Preuve contestée, effet sur les kg et sur l'historique, inscription au Journal d'audit. Étendre la détection de doublon de FR-8 aux photos de Preuve.
- **[medium]** L'historique du Collecteur est hors MVP alors que la thèse, UJ-3 et SM-7 s'appuient dessus. §1 : « donne aussi aux collecteurs informels un historique crédible » ; UJ-3, Résolution : « la Mission entre dans son historique » ; SM-7 « Valide FR-30 ». Pourtant FR-30 figure au §9.2 parmi les FR livrées « seulement si la porte H48 est atteinte en avance ». *Correctif :* passer FR-30 à H60 (c'est une simple liste filtrée), ou retirer la phrase de UJ-3 et l'assumer dans le `[NOTE FOR PM]`.
- **[medium]** Le hors-ligne, moment d'ouverture de la démo, n'arrive qu'à la porte du gel (§9.1 : FR-17 à FR-21 à H60 ; SM-1 commence par « signalement hors-ligne » ; UJ-1 est titré « sans réseau »). Si H60 glisse, la démonstration perd son premier temps fort. *Correctif :* avancer FR-17 et FR-18 à H48, ou écrire le repli prévu pour SM-1 si le hors-ligne n'est pas prêt.
- **[medium]** Le périmètre géographique du pilote n'est pas défini. FR-7 accepte toute Position au Sénégal (« Une Position hors du Sénégal est refusée »), alors que le pilote concerne « une commune ». Le PRD ne dit pas ce que deviennent les Signalements hors de la commune pilote (refus, file à part, exclusion des indicateurs), ni comment ils pèsent sur SM-5 et SM-6. *Correctif :* ajouter une conséquence à FR-7 ou une règle de Zone active pour le pilote.
- **[low]** Une dépendance entre portes n'est pas écrite. FR-25 (H48) exige un Collecteur vérifié, mais la vérification par l'Administrateur commune (FR-35) n'arrive qu'à H60. La boucle H48 repose donc implicitement sur les comptes de test de FR-37. *Correctif :* l'écrire dans la conséquence de FR-37 (« comptes de test pour chaque rôle, dont un Collecteur vérifié »).

## Clarté du « fini » — thin

C'est la dimension la plus faible, et celle dont la création des stories dépend le plus. Les bonnes FR sont excellentes : FR-1, FR-8, FR-9 (« 10 renvois identiques produisent un seul Signalement ») et FR-25 ont des conséquences vérifiables. Mais une quinzaine de FR n'ont aucun bloc « Conséquences » ou reposent sur des adjectifs. Surtout, plusieurs FR du cœur de la boucle laissent des règles métier indécidables.

### Constats
- **[high]** Le suivi du Citoyen anonyme n'est pas spécifié. UJ-1 : Awa est « sans compte ; signalement anonyme » et « voit plus tard « Validé », puis « Collecté » ». Or FR-20 ne parle que de « ses Signalements », FR-3 exige un contrôle de « propriété » sans dire comment un anonyme possède un Signalement, et FR-21 ne notifie que le « Citoyen connecté ». L'addendum (B.2, `device_id_hash`) laisse deviner un rattachement à l'appareil, mais le PRD ne dit pas ce que voit un anonyme, sur quel appareil, ni ce qu'il perd s'il réinstalle l'application ou vide le cache. *Correctif :* ajouter à FR-20 des conséquences propres aux anonymes : liste liée à l'appareil, perte assumée en cas de réinstallation, consultation par Numéro de suivi ou non, aucune notification push. Préciser dans FR-3 la règle de propriété des anonymes.
- **[high]** Les définitions des indicateurs sont incompatibles avec le modèle de Statut. Le glossaire pose qu'un Signalement « a un et un seul Statut », et `collecté` n'est atteint qu'après `validé` puis `assigné`. Lue au pied de la lettre, la définition du « Taux de traitement » (FR-31 : « Part des Signalements `validé` qui sont `collecté` ») vaut donc toujours 0. Il en va de même pour « dont `validé` » et pour SM-6 (« 60 % des Signalements `validé` passent à `collecté` »). Plusieurs points restent aussi à trancher :
  - le « Délai médian » part-il de la création sur l'appareil ou de la réception par le serveur ? Les Signalements hors-ligne faussent l'une ou l'autre mesure ;
  - quelle cohorte entre dans une « période choisie » ?
  - comment sont traités les Signalements encore ouverts ?

  Ces chiffres sont montrés au jury et servent à juger le pilote. *Correctif :* les redéfinir en termes d'historique (« Signalements ayant atteint `validé` »), fixer l'origine du délai (horodatage serveur de réception, par exemple) et la règle de cohorte (créés dans la période).
- **[high]** Beaucoup de FR n'ont pas de conséquence testable, ou reposent sur des adjectifs :
  - FR-4 « une information claire » ;
  - FR-15 « mis en évidence », sans bloc Conséquences ;
  - FR-29 « avec un message clair » ;
  - FR-19 : aucune conséquence ;
  - FR-21 : ni délai ni contenu de la notification ;
  - FR-22 : aucune conséquence (pagination, comportement si la Classification serveur n'est pas encore arrivée) ;
  - FR-26 : aucune conséquence (annulation possible après Preuve ? limite contre les annulations abusives ?) ;
  - FR-28 « qui en est notifié » : canal non précisé ;
  - FR-30 : aucune conséquence ;
  - FR-34 : taille de cellule non fixée ;
  - FR-36 : la propriété « non modifiable » du Journal d'audit (glossaire) n'est vérifiée nulle part, et la liste des « actions sensibles » n'existe pas (connexion ? export ? suppression de compte ? changement de rôle ?) ;
  - FR-38 à FR-40 : aucune conséquence (acceptable pour une extension).

  *Correctif :* ajouter au moins une conséquence vérifiable à chaque FR. Dresser la liste fermée des actions inscrites au Journal d'audit et ajouter à FR-36 une conséquence du type « aucune route ne permet de modifier ou de supprimer une entrée ».
- **[medium]** Le géorepérage de 150 m n'a pas de règle de précision GPS (FR-7 et FR-29 ; glossaire « Position : coordonnées GPS et précision en mètres »). La précision est enregistrée mais jamais utilisée. Une Position de Signalement à ± 200 m fait échouer un Collecteur honnête, et une précision médiocre peut aussi couvrir une fraude. *Correctif :* fixer une précision maximale acceptée à la création (par exemple ≤ 50 m, sinon un avertissement) et une règle pour la Preuve (distance moins les précisions, ou seuil combiné), avec le message à afficher.
- **[medium]** Le cycle de vie de la Mission n'est pas défini. Le glossaire ne connaît qu'une « Mission active ». FR-29 introduit « terminée », FR-26 une annulation implicite. Aucune expiration n'est prévue : un Collecteur qui accepte et ne vient jamais laisse le Signalement en `assigné` indéfiniment, ce qui dégrade directement SM-5 et SM-6. *Correctif :* ajouter au glossaire les états de la Mission (active, annulée, terminée, expirée), un délai d'expiration avec retour automatique à `validé`, et l'annulation par l'Administrateur commune.
- **[medium]** La règle du « Type de déchet retenu » est ambiguë (FR-12, FR-13, FR-14). Sous le Seuil de confiance, le choix du Citoyen n'est une « Correction » que s'il diffère de la prédiction (glossaire). S'il coïncide avec le premier choix local, le type retenu devient la Classification serveur, qui peut différer de ce que le Citoyen a choisi. Par ailleurs, « et plus tard le Modérateur » (FR-13) ne dit pas si « plus tard » renvoie à la feuille de route ou au moment du parcours, et FR-22 ne prévoit pas d'action de correction pour le Modérateur. *Correctif :* le Type de déchet retenu = choix humain explicite (Citoyen sous le seuil, ou Correction), sinon la Classification serveur. Inscrire la correction par le Modérateur dans FR-22 et FR-23 avec sa porte.
- **[medium]** La taille du Modèle et le premier usage sans réseau ne sont pas bornés. FR-11 vaut « une fois le Modèle en cache », et NFR-5 exclut explicitement le Modèle (« ≤ 500 Ko hors images et Modèle »). Or la persona d'UJ-1 a un « forfait de données souvent épuisé ». Le PRD ne fixe ni de taille maximale du Modèle, ni le comportement quand le Modèle n'est pas en cache : choix manuel ? Classification locale absente, et donc Désaccord IA indéfini ? *Correctif :* ajouter un seuil NFR sur la taille du Modèle et une conséquence à FR-11 (« sans Modèle en cache, le Citoyen choisit le Type de déchet ; aucun Désaccord IA n'est calculé »).
- **[medium]** SM-2 et SM-3 ne sont pas reproductibles en l'état. SM-2 : un « jeu de test local conservé » peut désigner un jeu conservé localement ou des photos prises au Sénégal ; ni sa taille ni sa composition ne sont fixées, alors que le choix de cette métrique remplace la promesse du Proposal. SM-3 : « moins de 30 s » sans point de départ ni d'arrivée (appui sur « Signaler un dépôt » → accusé de l'écran 4 ?), sans nombre d'essais ni profil de testeur. *Correctif :* définir l'origine et la taille minimale du jeu de test (par exemple ≥ N photos prises à Dakar, découpées par lieu et par jour comme dans l'addendum §D), puis le protocole de chronométrage.

## Honnêteté sur le périmètre — adequate

Le §8 Non-objectifs travaille réellement, le §9.2 assume ce qui sort de la démo, les `[ASSUMPTION]` en ligne sont tous indexés au §12, et le seul `[NOTE FOR PM]` est bien placé. Densité des points ouverts : 7 `[ASSUMPTION]` en ligne, 7 questions ouvertes et 1 `[NOTE FOR PM]`. C'est proportionné pour une porte de 72 h, à condition de rafraîchir l'index (voir Notes mécaniques). Trois omissions restent pourtant silencieuses.

### Constats
- **[high]** La Preuve de collecte ne fonctionne pas hors-ligne, et rien ne le dit (§1 « l'application fonctionne hors-ligne » ; §4.4 ne couvre que les Signalements ; FR-29 « L'horodatage est celui du serveur »). Le Collecteur travaille sur le terrain, dans les mêmes zones à réseau instable que le Citoyen. Le PRD ne dit ni si la Preuve peut être mise en file, ni comment l'horodatage serveur et le contrôle à 150 m se combinent avec un envoi différé. *Correctif :* soit une FR « Preuve en file hors-ligne » (Position et heure de capture enregistrées sur l'appareil, horodatage serveur à la réception, écart toléré), soit un `[NON-GOAL pour le MVP]` explicite avec son impact sur le pilote.
- **[medium]** Le pilote n'a aucune exigence d'exploitation. NFR-7 ne vise que la « Démo » (« Service et portable de secours prêts »). Pour 6 mois de données réelles, et des Preuves qui fondent la reconnaissance des Collecteurs, le PRD ne fixe ni disponibilité, ni sauvegarde, ni restauration testée, ni perte de données maximale. *Correctif :* ajouter des NFR pilote : disponibilité cible, sauvegarde quotidienne avec restauration testée, RPO et RTO.
- **[medium]** La démo en direct contredit l'affirmation « Données de démonstration uniquement ». SM-1 exige une boucle « en direct, sur des photos réelles », donc des Signalements créés pendant la démo avec des Positions réelles. Or §6.3 écrit « la démo, qui n'utilise que des Données de démonstration », et FR-37 n'étiquette que le jeu chargé. Les Signalements créés en direct ne sont pas étiquetés, et l'argument « aucune obligation CDP » repose sur une prémisse fausse. *Correctif :* préciser que tout ce qui est créé en Mode démonstration est automatiquement étiqueté comme Données de démonstration, et que les photos de la démo ne montrent ni personne ni plaque.

## Utilisabilité en aval — adequate

Le glossaire (§3) est le point fort du document : 30 termes, majuscules systématiques, machine à états du Statut explicite. Les identifiants FR-1 à FR-40, NFR-1 à NFR-14, SM-1 à SM-8, SM-C1 à SM-C4 et UJ-1 à UJ-5 sont contigus et uniques. Chaque section du §4 cite ses UJ. Trois défauts gêneront toutefois l'extraction par l'architecture et les stories.

### Constats
- **[medium]** Contradiction entre §6.1 et FR-24 sur les positions précises. §6.1 : « les positions précises sont réservées au Personnel et au Collecteur de la Mission ». FR-24 : tout Collecteur vérifié voit les Signalements `validé` « sur une carte et en liste », triés par distance, donc avant toute Mission. L'architecture et les tests d'accès (NFR-9) implémenteront l'une ou l'autre règle. *Correctif :* trancher. Soit les Collecteurs vérifiés voient les positions précises dans leur rayon (et §6.1 est amendé), soit les positions sont floutées jusqu'à l'acceptation (et FR-24 le dit).
- **[medium]** Des références croisées pointent vers les identifiants du cahier des charges et non vers ceux du PRD : FR-11 « (NF-01) », FR-17 « (NF-06) », FR-32 « (NF-03) ». NF-01 et NF-03 correspondent par hasard au contenu de NFR-1 et NFR-3. En revanche, « NF-06 » renvoie dans le PRD à NFR-6 Compatibilité, alors que FR-17 parle de conservation hors-ligne, qui n'a aucune NFR dans le §5. *Correctif :* remplacer par NFR-1 et NFR-3, et ajouter une NFR hors-ligne (ou retirer la référence de FR-17).
- **[medium]** Des états et notions sont employés hors du glossaire :
  - « en attente d'envoi » (UJ-1, FR-17), état côté appareil absent du Statut ;
  - « terminée » (FR-29) pour la Mission ;
  - « réservé » (FR-40) pour le Lot de matière ;
  - « la frise des 4 états » (UJ-1, FR-20), alors que le Statut en compte 5 (`en attente de modération`, `validé`, `rejeté`, `assigné`, `collecté`). L'UX ne peut pas savoir lesquels afficher.

  *Correctif :* ajouter au glossaire les états de la File hors-ligne, de la Mission et du Lot de matière, et définir la frise (par exemple 4 étapes sur le chemin nominal, avec `rejeté` en branche).
- **[low]** Les UJ sont inégales. Seule UJ-1 a une ligne « Persona et contexte ». UJ-5 n'a aucune structure et fait supprimer un compte à Awa, alors que dans UJ-1 elle est « sans compte ». Aucune UJ ne couvre l'enrôlement et la vérification d'un Collecteur (FR-35), étape pourtant critique pour SM-7, et les critères de « vérifié » ne sont pas énoncés. *Correctif :* harmoniser le gabarit, donner à UJ-5 un autre protagoniste ou un contexte de compte, et ajouter une UJ courte « M. Ndiaye vérifie un récupérateur informel », avec les critères de vérification.

## Adéquation de la forme — strong

Le produit a plusieurs parties prenantes (Citoyen, Collecteur, Personnel) et une UX forte : les UJ avec protagoniste nommé sont donc indispensables, et elles sont présentes. Le PRD est en tête de chaîne (UX → architecture → stories) : l'addendum sépare proprement le « comment », et la traçabilité FR ↔ UJ ↔ SM est assurée. Le niveau de formalisme est juste pour l'enjeu.

### Constats
- **[low]** Un peu de solution déborde dans les FR : codes HTTP (401, 403, 409, 413, 422, 429), « jeton de renouvellement » (FR-2), outils de vérification (k6, Gitleaks, Trivy au §5). C'est acceptable, puisque cela rend les conséquences testables, mais l'UX lira des codes HTTP à la place des comportements visibles. *Correctif :* pour chaque code, ajouter le comportement côté utilisateur, comme FR-25 le fait déjà (« Mission déjà prise »).

## Notes mécaniques

**Dérive du glossaire** (le PRD est en français ; termes à employer à l'identique) :
- « missions » au sens de Signalements `validé` disponibles : UJ-3 « missions dans un rayon de 5 km », titre de FR-24 « Missions proches ». Selon le glossaire, une Mission n'existe qu'après acceptation. Écrire « Signalements disponibles » ou « Signalements `validé` proches ».
- « Accepter la mission », « la mission » (minuscule, UJ-3) ; « collecteurs » (minuscule, UJ-2 « visible des collecteurs ») : écrire « Mission » et « Collecteurs ».
- « type » seul (FR-17, FR-24, FR-38, FR-39, UJ-3) au lieu de « Type de déchet ».
- « confiance » (FR-24, UJ-3) et « score de confiance » (FR-11) ne sont pas définis ; seul « Seuil de confiance » l'est. Ajouter « Score de confiance » au glossaire.
- « Kg valorisés » (FR-31) contre « kg collectés » (FR-30) contre « kg valorisés par Mission » (SM-C3) : choisir un seul terme (voir le constat Substance).
- « Modèle factice » (FR-16, §9.1 en minuscule, addendum §D en gras) : absent du glossaire.
- « visiteur » (FR-34), « utilisateur » (FR-1, FR-2, FR-5) : rôles non définis. Ajouter « Visiteur » ou écrire « toute personne non connectée ».
- « désaccord IA » entre guillemets et en minuscule (UJ-2) contre « Désaccord IA » (glossaire, FR-15).
- « positions » en minuscule (FR-33, §6.1) au lieu de « Position ».
- « Preuve » abrégé (FR-29, FR-31) pour « Preuve de collecte » : tolérable, mais à déclarer dans le glossaire.

**Continuité des identifiants :** FR-1 à FR-40, NFR-1 à NFR-14, SM-1 à SM-8, SM-C1 à SM-C4 et UJ-1 à UJ-5 sont sans trou ni doublon. Les références NF-01, NF-03 et NF-06 (FR-11, FR-17, FR-32) ne se résolvent pas dans le PRD (voir le constat Utilisabilité en aval). §12 renvoie à « §6.3 et §7 » pour le jeton Vert, mais le §7 ne porte aucune balise `[ASSUMPTION]`.

**Aller-retour de l'index des hypothèses :**
- Les 7 `[ASSUMPTION]` en ligne (FR-1, FR-4, FR-14, FR-33, §6.1, §6.3, SM-2) figurent tous au §12.
- L'index est périmé. D'après `.memlog.md`, Mia a validé les hypothèses a à f, le vert `#187A50` et le report des Lots de matière : « ils deviennent des décisions ». Pourtant §6.3 garde `[ASSUMPTION : validation de Mia]`, SM-2 garde son `[ASSUMPTION]`, et le §12 liste encore les cinq « décisions par défaut » comme hypothèses. Il faut les déplacer dans une rubrique « Décisions validées », sinon l'aval les traitera comme révisables.
- Deux entrées de l'index n'apparaissent nulle part dans le corps du PRD : « pitch de 1 min 30 » et « déploiement final sur Docker Compose » (seulement dans l'addendum). Inversement, le rayon de 5 km (FR-24) et le seuil de 60 % (SM-6) sont dans l'index mais sans balise en ligne. C'est cohérent si ces points deviennent des décisions.

**Protagonistes des UJ :** chaque UJ en a un (Awa, Fatou, Ibrahima, M. Ndiaye, Awa). Le contexte en ligne manque pour UJ-2 à UJ-5, et Awa est incohérente entre UJ-1 (anonyme) et UJ-5 (titulaire d'un compte).

**Sections requises :** toutes sont présentes pour l'enjeu : vision, utilisateurs, glossaire, FR, NFR, conformité, non-objectifs, périmètre, SM, questions, index. Il n'y a pas de section « Critères d'acceptation » distincte ; ce choix tient seulement si chaque FR reçoit un bloc « Conséquences » (voir le constat Clarté du « fini »).

## Synthèse des constats

| Gravité | Nombre |
|---|---|
| critical | 0 |
| high | 5 |
| medium | 16 |
| low | 4 |
