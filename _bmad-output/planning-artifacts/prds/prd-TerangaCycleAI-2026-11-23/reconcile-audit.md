---
title: "Réconciliation — audit du 23/11/2026 ↔ PRD TerangaCycle AI"
source: docs/audit-2026-11-23.md
cible: prd.md, addendum.md (+ .memlog.md)
created: 2026-11-23
---

# Réconciliation : audit du 23 novembre 2026 ↔ PRD

**Source :** `docs/audit-2026-11-23.md` (audit de conception : incohérences, sécurité, confidentialité, conformité, hygiène du dépôt).
**Cibles lues en entier :** `prd.md`, `addendum.md`, `.memlog.md`. Aucune modification n'a été faite dans `prd.md` ni dans `addendum.md`.

**Légende des statuts**

- **Couvert** : traduit en exigence testable dans le PRD, ou placé dans l'addendum avec une décision claire, ou explicitement mis de côté (question ouverte, non-objectif).
- **Partiel** : présent, mais incomplet, non testable, mal rattaché ou contredit ailleurs.
- **Absent** : on ne le trouve ni dans le PRD, ni dans l'addendum, ni dans les questions ouvertes ou non-objectifs.

## Synthèse

| Bloc | Constats | Couverts | Partiels | Absents |
|---|---|---|---|---|
| Incohérences #1–#10 | 10 | 7 | 3 | 0 |
| Sécurité S1–S12 | 12 | 4 (dont S2 et S6 couverts par l'addendum, mais partiels dans le PRD) | 8 | 0 |
| Sécurité, points mineurs | 7 | 4 | 2 | 1 |
| Confidentialité et conformité | 8 | 3 | 5 | 0 |
| Contrastes WCAG (combinaisons en échec) | 5 | 1 | 2 | 2 |
| Hygiène du dépôt | 7 | 0 | 3 | 4 |

**Écarts principaux**

1. **Contradiction sur les positions précises (S8).** Le §6.1 réserve les positions précises « au Personnel et au Collecteur de la Mission ». Or FR-24 montre à **tout** Collecteur vérifié, sur une carte, les Signalements `validé` avec leur distance, donc leur position précise, avant toute acceptation. De plus FR-34 (carte publique agrégée) est en *Should* hors MVP, sans règle pour l'écran « Tous » de la maquette.
2. **Contrastes WCAG : rouge et jaune absents.** Seul le vert est corrigé (§6.3). Le rouge `#D9482B` (4,28:1 sur blanc, 4,06:1 sur le Fond) et le jaune `#F2B705` en texte (1,73:1) ne font l'objet d'aucune règle. Le vert sur Menthe (3,82:1) n'est corrigé qu'implicitement, par le remplacement du jeton (à expliciter).
3. **Hygiène du dépôt quasi absente du PRD et de l'addendum.** `SECURITY.md`, `.env.example`, la protection de `main`, le *secret scanning*, la *push protection* et Dependabot n'apparaissent nulle part. Le fichier `LICENSE` est repoussé « avant le pilote », alors que le dépôt est déjà public.
4. **Exigences de sécurité S4, S5, S7, S10, S11 et S12 présentes uniquement dans l'addendum.** Elles n'ont aucune conséquence testable dans le PRD. Plusieurs exigences du PRD restent sans seuil : limites « par IP et par appareil » de FR-1, plafond SMS, « routes sensibles », « immédiatement », « file bornée », « échantillon ».
5. **Consentement au réentraînement incomplet pour les anonymes.** `users.consent_training` (addendum B6) n'existe que pour les comptes, alors que FR-4 prévoit un choix mémorisé sur l'appareil pour un anonyme. Il manque un champ par Signalement, l'exclusion testable des données refusées dans l'export des Corrections (FR-13) et le retrait du consentement après coup.

Autre point à corriger : le PRD n'a pas suivi le `.memlog.md`. Mia a validé les hypothèses a–f et le vert `#187A50`, qui sont donc des **décisions**. Pourtant, le §11 Q1 (Large ou Small) est toujours ouvert, le §12 les liste encore comme hypothèses et le §6.3 porte encore `[ASSUMPTION : validation de Mia]`.

---

## 1. Incohérences entre documents (#1–#10)

| # | Constat de l'audit | Statut | Où dans le PRD ou l'addendum | Écart et correction proposée |
|---|---|---|---|---|
| 1 | Modèle Large ou Small | **Couvert** (question ouverte et décision par défaut) | PRD §11 Q1 ; §12 ; addendum A (« Large par défaut ») ; memlog (a) | Écart d'état : le memlog indique que Mia a validé (a). **Correction :** au §11 Q1, écrire « Large par défaut (décidé) ; bascule vers Small si la latence de NFR-1 dépasse 3 s à la mesure H24 (responsable : Aissatou) ». Retirer (a) des hypothèses du §12 et le déplacer dans une liste « Décisions ». |
| 2 | F1 macro ou top-1 accuracy | **Couvert** | PRD §10 SM-2 ; addendum E | Même écart d'état : le `[ASSUMPTION]` de SM-2 est devenu une décision (memlog). **Correction :** retirer la balise dans SM-2 et au §12. Ajouter à SM-2 : « le pitch annonce le F1 macro ; si le Proposal est cité, la top-1 accuracy est donnée en complément ». |
| 3 | Rayon des missions | **Couvert** | FR-24 (1 à 10 km, 5 km par défaut) ; UJ-3 | Ajouter une conséquence testable à FR-24 : « sans réglage, la requête utilise 5 km ; une valeur hors de [1 ; 10] km renvoie 422 ». |
| 4 | Critère de réussite du pilote | **Couvert** (pour le PRD) | §10 SM-6 (60 % sur 6 mois) ; addendum E | L'alignement du cahier des charges (80 % sur 4 à 6 semaines) n'est suivi par aucune action. **Correction :** ajouter au §11 « Mettre à jour `docs/cahier-des-charges.md` (critère du pilote, durée du pitch) ; responsable : Mia ». |
| 5 | Durée du pitch | **Partiel** | §12 seulement (« pitch de 1 min 30 ») | Ce n'est pas une exigence produit, mais l'audit demande de mettre à jour le cahier. **Correction :** ajouter cette action au §11 (voir #4). Le §12 peut aussi préciser « 1 min 30 + 2 à 3 min de questions ». |
| 6 | Déploiement de fin de hackathon | **Couvert** | §12 ; addendum A et E ; NFR-7 (portable de secours) | RAS. Le §11 Q4 couvre la région d'hébergement du pilote. |
| 7 | Prédiction locale conservée ; désaccord envoyé en modération | **Partiel** | FR-14 (les deux classifications sont conservées), FR-15, FR-22 ; addendum B1 (`source`/`client_predicted_type`, drapeau `disagreement`) | FR-15 n'a **aucune conséquence testable**. Rien ne dit non plus quoi afficher quand la Classification serveur, asynchrone (FR-14), n'est pas encore arrivée au moment de la modération. **Correction (PRD, FR-15) :** « Conséquences : (a) un Signalement dont la Classification locale et la Classification serveur diffèrent porte le drapeau Désaccord IA dans la File de modération ; test avec une prédiction client forcée différente → drapeau présent ; (b) tant que la Classification serveur n'est pas disponible, la File l'indique « classification serveur en attente » et le Modérateur peut quand même décider ; (c) un Signalement envoyé sans Classification locale (ancienne version, échec du Modèle) n'est pas marqué en désaccord ». L'audit nomme le drapeau `needs_review` et l'addendum `disagreement` : garder un seul nom dans l'addendum B1. |
| 8 | Colonne `pile_size` | **Couvert** | FR-7 ; Glossaire (Taille de tas) ; addendum B2 et B7 ; §11 Q6 (table de conversion) | Ajouter à FR-7 : « sans Taille de tas, l'envoi est impossible », pour la rendre obligatoire et testable comme la photo et la Position. |
| 9 | Séquence du Numéro de suivi | **Partiel** | Glossaire (format `TC-AAAA-NNNNNN`) ; FR-7 (« le serveur attribue ») ; addendum B3 | Aucune conséquence testable. **Correction (FR-7) :** « le Numéro de suivi est unique, au format `TC-AAAA-NNNNNN`, l'année étant celle de la réception par le serveur ; deux créations simultanées obtiennent deux numéros distincts ; un renvoi idempotent (FR-9) renvoie le même numéro ». Préciser dans l'addendum B3 si la séquence repart à 1 chaque 1er janvier. |
| 10 | Poids estimé (signalement) ou mesuré (preuve) | **Couvert** | Glossaire (Poids estimé, Poids mesuré) ; FR-24 ; FR-29 (> 0) ; FR-31 (kg valorisés = Poids mesurés) | RAS. |

## 2. Sécurité S1–S12

| # | Constat | Statut | Où | Testabilité, écart et correction proposée |
|---|---|---|---|---|
| S1 | IDOR par idempotence de `POST /v1/reports` | **Couvert** | FR-9 (10 renvois → 1 seul Signalement ; autre utilisateur → 409 sans donnée) ; §6.2 ; addendum B2 et C | Bien testable. **Risque résiduel :** pour un anonyme, « même appareil » repose sur un identifiant fourni par le client. Si cet identifiant fuit comme le `client_uuid`, la protection tombe. **Correction (addendum B2) :** l'identifiant d'appareil est un secret aléatoire d'au moins 128 bits, généré à l'installation, envoyé dans un en-tête, stocké haché (`device_id_hash`), jamais renvoyé par l'API ni journalisé. Ajouter à FR-9 : « la réponse 409 ne contient ni Numéro de suivi, ni Statut, ni Position ». |
| S2 | Hachage du téléphone cassable | **Couvert** (addendum) / **Partiel** (PRD) | §6.1 (« empreinte calculée avec une clé secrète ») ; addendum B4 et C (HMAC-SHA256 + pepper, AES-GCM) | Le §6.1 décrit sans conséquence vérifiable. **Correction (PRD §6.1, sous « Protection ») :** « Conséquences : aucune colonne ne contient le numéro en clair (test : recherche du numéro en clair dans un dump de la base → 0 résultat) ; la clé d'empreinte et la clé de chiffrement ne sont ni dans le dépôt ni dans la base (Gitleaks, revue du `.env.example`) ; une même saisie normalisée en E.164 (`+221 77…`, `77…`) donne la même empreinte ». |
| S3 | OTP affiché en mode démo, actif en production | **Couvert** | FR-6 (refus de démarrer, bandeau) ; Glossaire ; §6.2 ; addendum C | Testable. Ajouter seulement « test automatisé en CI : démarrage avec `ENV=production` et `DEMO_MODE=true` → code de sortie non nul ». |
| S4 | Stockage des jetons dans la PWA (risque XSS) | **Partiel** | FR-2 (révocation, réutilisation → révocation de la famille, déconnexion) ; addendum B5 (refresh haché) et C (mémoire + cookie) | Les points vérifiables de S4 ne sont que dans l'addendum, et la durée de vie du jeton d'accès n'est fixée nulle part. **Correction (FR-2, conséquences) :** « aucun jeton n'est présent dans `localStorage`, `sessionStorage` ni IndexedDB (test e2e qui inspecte le stockage) ; le cookie de renouvellement porte `HttpOnly`, `Secure`, `SameSite=Strict` et `Path=/v1/auth` (test sur l'en-tête `Set-Cookie`) ; le jeton d'accès expire au plus tard 15 min après son émission `[ASSUMPTION]` ; la base ne stocke que l'empreinte du jeton de renouvellement ». |
| S5 | JWT : algorithme, `iss`/`aud`, clés | **Partiel** | Addendum C uniquement | Aucune conséquence dans le PRD. **Correction (FR-2, ou ligne NFR « Sécurité – Jetons ») :** « un jeton `alg=none`, signé avec un algorithme hors liste blanche, à `iss` ou `aud` incorrect, expiré, ou avec un `kid` inconnu, est rejeté (401) ; un test par cas ». Le choix EdDSA ou RS256 reste dans l'addendum. |
| S6 | Stockage et comparaison des OTP | **Couvert** (addendum) / **Partiel** (seuils) | FR-1 (5 min, usage unique, 5 essais, plafond SMS) ; addendum C (haché, temps constant) | « Un plafond quotidien de coût SMS » et « une limite par IP et par appareil » n'ont **aucune valeur** : ce n'est pas testable. **Correction (FR-1) :** « plafond quotidien configurable, par défaut N SMS par jour `[ASSUMPTION : N à fixer selon la passerelle, §11 Q3]` ; au-delà, l'envoi renvoie 503 `SMS_QUOTA_EXCEEDED` et une alerte part sur le canal de l'équipe ; au plus 20 demandes d'OTP par heure et par IP `[ASSUMPTION]` ; l'OTP n'est jamais stocké en clair (test : lecture de la clé Redis → empreinte) ». |
| S7 | Limitation de débit absente de `caddy:2` ; `X-Forwarded-For` falsifiable | **Partiel** | Addendum C (limitation dans l'API, proxys de confiance) ; limites dans FR-1 et FR-10 | Aucune conséquence dans le PRD sur l'origine de l'IP. **Correction (FR-10, conséquences) :** « l'IP prise en compte est celle que le proxy de confiance transmet ; un en-tête `X-Forwarded-For` forgé par le client ne permet pas de contourner la limite (test : 11 requêtes avec 11 `X-Forwarded-For` différents → la 11e reçoit 429) ; la limite tient après un redémarrage de l'API (compteur dans Redis) ». |
| S8 | Positions précises sur la carte publique (écran « Tous ») | **Partiel** (contradiction) | §2.2 ; §6.1 (« positions précises réservées au Personnel et au Collecteur de la Mission ») ; FR-34 (*Should*, hors MVP §9.2) ; FR-33 (arrondi) ; addendum C | (1) **Contradiction** : FR-24 montre à tout Collecteur vérifié, sur une carte, les Signalements `validé` avec leur distance, donc leur position précise **avant** acceptation, ce qui contredit le §6.1 et l'audit (« collecteur assigné »). (2) FR-34 dit « jamais de point précis », sans taille de cellule ni seuil minimal. (3) Rien n'est prévu pour l'écran « Tous » de la maquette si FR-34 n'est pas livré. **Corrections :** (a) FR-24 : « avant acceptation, la Position est affichée arrondie `[ASSUMPTION : 3 décimales, environ 110 m]` avec une distance en tranches ; la Position précise n'est renvoyée par l'API qu'au Collecteur de la Mission (FR-25) et au Personnel ; test : un Collecteur non assigné ne reçoit jamais plus de 3 décimales ». À défaut, assumer l'écart explicitement au §6.1. (b) FR-34 : « cellules d'au moins 500 m de côté `[ASSUMPTION]` ; une cellule de moins de 3 Signalements n'est pas affichée ; aucune réponse publique de l'API ne contient de coordonnées de Signalement ». (c) §9.2 : « tant que FR-34 n'est pas livré, l'écran « Tous » n'est pas exposé sans connexion ». |
| S9 | Visages et plaques sur les photos ; floutage repoussé | **Partiel** | FR-4 (consigne « avant la première capture ») ; FR-23 (validé avant exposition aux Collecteurs) ; addendum C | L'audit demande la consigne **sur l'écran de capture**, pas seulement à la première utilisation. Le report du floutage n'est inscrit nulle part comme non-objectif. Les photos de Preuve de collecte (FR-29) ne passent pas par la modération. **Corrections :** (a) FR-7 : « l'écran de capture (écran 2) rappelle à chaque fois la consigne « ni personne ni plaque » » ; (b) §8 : ajouter « floutage automatique des visages et des plaques (après le MVP) » ; (c) FR-29 : préciser qui voit les photos de preuve (Personnel et Collecteur auteur seulement) et appliquer la même consigne. |
| S10 | Moindre privilège en base (super-utilisateur) | **Partiel** (mal rattaché) | Addendum C, rattaché à NFR-10, qui porte en fait sur la chaîne logicielle | Aucune conséquence testable dans le PRD ; le rattachement à NFR-10 n'est pas pertinent. **Correction :** nouvelle NFR « Sécurité – Base de données » : « l'API se connecte avec un rôle sans DDL ni super-utilisateur (test CI : `CREATE TABLE` et `ALTER TABLE` avec le rôle applicatif → refus) ; le rôle applicatif n'a ni `UPDATE` ni `DELETE` sur la table du Journal d'audit (rend testable « non modifiable » du Glossaire) ; les migrations utilisent un rôle distinct ». |
| S11 | `/docs` et `/readyz` publics en production | **Partiel** | Addendum C (rattaché à NFR-7) | NFR-7 parle de sondes, pas d'exposition. **Correction (NFR-7, ou nouvelle NFR) :** « en production, `GET /docs`, `/redoc` et `/openapi.json` renvoient 404, ou 401 sans authentification Personnel ; `/readyz` ne renvoie qu'un statut global (pas de version, d'hôte ni de message d'erreur interne) ; test automatisé ». |
| S12 | Reclassement serveur synchrone : déni de service par le CPU | **Partiel** | FR-14 (`[ASSUMPTION]` asynchrone) ; addendum C (tâche arq, file bornée) | L'asynchronisme est encore une hypothèse alors que c'est une correction de sécurité, et « file bornée » n'a pas de valeur. **Correction (FR-14) :** retirer `[ASSUMPTION]` et ajouter « la création répond sans attendre la Classification serveur (p95 conforme à NFR-2) ; la file de classification est limitée à N tâches `[ASSUMPTION : 500]` ; une fois la file pleine, les nouveaux Signalements sont acceptés et marqués « classification serveur en attente », puis reclassés plus tard ; aucune requête HTTP n'exécute le Modèle ». |

## 3. Sécurité : points mineurs ou à surveiller

| Constat | Statut | Où | Correction proposée |
|---|---|---|---|
| CSP : `'wasm-unsafe-eval'` pour onnxruntime-web | **Partiel** | Addendum C (points d'infrastructure) | Le PRD n'a **aucune exigence de CSP** (NFR-8 ne couvre que TLS et HSTS). **Correction (NFR-8 ou nouvelle ligne) :** « la PWA est servie avec une CSP dont `script-src` n'autorise ni `'unsafe-inline'` ni `'unsafe-eval'`, seulement `'self'` et `'wasm-unsafe-eval'` ; vérifiée par test sur l'en-tête ». |
| Images Docker et actions GitHub non épinglées | **Couvert** | NFR-10 (« versions épinglées ») ; addendum C | Préciser dans NFR-10 « images épinglées par digest `@sha256:` et actions par SHA de commit ; vérifié en CI (aucun `uses:` avec tag mobile) ». |
| Distribution communautaire de MinIO | **Couvert** | Addendum C | RAS (décision à prendre dans `bmad-architecture`). |
| Healthcheck avec `curl` dans une image Python minimale | **Couvert** | Addendum C | RAS. |
| Pillow : `MAX_IMAGE_PIXELS` ; HEIC refusé | **Partiel** | FR-8 (12 MP, 1 Mo, 413/422) ; addendum C (`MAX_IMAGE_PIXELS`) | Le cas HEIC n'est pas traité et les formats acceptés ne sont pas listés. **Correction (FR-8) :** « le serveur n'accepte que JPEG, PNG et WebP (415 sinon) ; une photo HEIC prise sur iPhone est convertie en JPEG sur l'appareil avant envoi (test sur un fichier HEIC) ». |
| Gitleaks Action payante pour une organisation GitHub | **Absent** | NFR-10 cite Gitleaks sans réserve | **Correction (addendum C, points d'infrastructure) :** « utiliser le binaire `gitleaks` (licence MIT) dans un job CI plutôt que `gitleaks-action` si le dépôt passe dans une organisation GitHub ; sinon, confirmer qu'il reste sur un compte personnel ». |
| `audit_logs.ip` est une donnée personnelle : durée de conservation | **Couvert** (hypothèse) | §6.1 (IP du Journal d'audit : 6 mois) | Voir « Conservation » au §4 : manque la purge testable. |

## 4. Confidentialité et conformité

| Cadre | Statut | Où | Écart et correction proposée |
|---|---|---|---|
| Loi n° 2008-12 et CDP : déclaration avant traitement réel | **Partiel** | §6.3 (rien pour la démo ; déclaration avant le pilote) | L'audit demande de **vérifier si un nouveau texte a remplacé la loi de 2008** : ce n'est repris nulle part. **Correction (§11) :** « Q8. Cadre légal en vigueur : la loi 2008-12 a-t-elle été remplacée ou complétée ? Responsable : Mia, avant le dépôt du dossier CDP ». |
| Transferts hors du Sénégal (pilote AWS) | **Couvert** | §6.3 (transfert à couvrir dans le dossier CDP) ; §6.4 (plan de sortie) ; §11 Q4 ; addendum A | RAS. On peut ajouter l'argument « cible : hébergement au Sénégal (Diamniadio ou hébergeur local) » au §6.4, qui le dit déjà en substance. |
| Finalité « réentraînement de l'IA » distincte, avec retrait possible | **Partiel** | FR-4 (information, refus possible `[ASSUMPTION]`) ; addendum B6 (`users.consent_training`) ; FR-13 (export des Corrections) | (1) Le **retrait après coup** n'est pas prévu. (2) Le consentement des **anonymes** n'a pas de stockage côté serveur (B6 ne couvre que `users`). (3) Aucune conséquence ne garantit que les données refusées sont exclues de l'export d'entraînement. **Corrections :** FR-4 : « le Citoyen peut retirer son accord au réentraînement depuis son profil, ou dans les réglages de l'appareil pour un anonyme ; ses photos et Corrections suivantes sont alors exclues » ; FR-13 : « l'export des Corrections exclut tout Signalement sans accord au réentraînement (test : Signalement avec refus → absent de l'export) » ; addendum B : « `reports.consent_training` (booléen), copié au moment de la création ». |
| Conservation : durées fixées dans le code | **Partiel** | §6.1 (tableau des durées, `[ASSUMPTION]`) | Les valeurs existent, mais aucune purge n'est exigée ni testable. Les photos de Preuve de collecte, les jetons et les compteurs Redis ne sont pas listés. **Correction (§6.1) :** « une tâche planifiée applique ces durées (test avec horloge simulée : photo de plus de 12 mois → supprimée du stockage et lien invalide ; IP de plus de 6 mois → effacée du Journal d'audit) ». Ajouter une ligne « Photos de Preuve de collecte » au tableau. |
| Mineurs (moins de 18 ans) | **Couvert** (question ouverte) | §11 Q5 | Sans responsable ni échéance. **Correction :** « Responsable : Mia ; décision avant le pilote ; par défaut pour la démo : mention « 15 ans et plus » sur l'écran de consentement, le parcours anonyme restant ouvert `[ASSUMPTION]` ». |
| Licences des jeux de données (TrashNet, TACO / Flickr) | **Couvert** | §6.3 ; addendum D (fiche du Modèle) | Ajouter la condition « avant toute publication du Modèle » (formulation de l'audit) pour que ce soit vérifiable : « le Modèle n'est pas publié tant que la fiche ne liste pas la licence de chaque source ». |
| WCAG 2.1 AA (NF-12) : jetons en échec | **Partiel** | NFR-12 ; §6.3 ; §7 | Seul le vert est traité ; voir le détail au §5. |
| Licence du code (NF-15) | **Partiel** | §6.3 et §11 Q2 (« avant le pilote ») | L'audit constate un **dépôt public sans `LICENSE`**. Sans licence, le code est « tous droits réservés », ce qui contredit le §6.4 (souveraineté, commun numérique). **Correction :** au §11 Q2, avancer l'échéance à « avant la fin du hackathon (porte H60) » ; ajouter au §9.1 H24 ou H60 : « fichier `LICENSE` présent à la racine ». |

## 5. Contrastes WCAG 2.1 (mesures de l'audit)

J'ai recalculé les ratios avec la formule WCAG ; ils concordent avec l'audit.

| Combinaison | Ratio | Statut dans le PRD | Correction proposée |
|---|---|---|---|
| Blanc sur Vert `#1F8A5B` (boutons) | 4,33:1 | **Couvert** : §6.3 et §7, remplacement par `#187A50` (5,33:1), validé par Mia (memlog) | Retirer `[ASSUMPTION : validation de Mia]` au §6.3 et au §12 : c'est une décision. |
| Vert `#1F8A5B` en texte sur Fond `#F6FAF7` | 4,11:1 | **Partiel** : corrigé implicitement si le jeton est remplacé partout | Avec `#187A50`, j'obtiens **5,06:1** ✅. **Correction (§6.3) :** écrire que le jeton Vert est remplacé **dans toutes ses utilisations** (fond de bouton, texte, pastilles), pas seulement « en texte blanc ». |
| Vert sur Menthe `#EAF3EC` (pastilles) | **3,82:1** | **Partiel** : même cas | Avec `#187A50` sur Menthe, j'obtiens **4,70:1** ✅. Même correction que ci-dessus, en citant explicitement la combinaison des pastilles. |
| Rouge `#D9482B` sur blanc | **4,28:1** (4,06:1 sur le Fond) | **Absent** | **Correction (§6.3 et §7) :** « le Rouge n'est utilisé en texte, ou en fond sous un texte blanc, que dans sa variante foncée ». Candidats calculés : `#C13B1F` (5,37:1 sur blanc, 5,09:1 sur le Fond), `#B93A1E` (5,70:1, 5,41:1) ; à valider par Mia. Sinon : « Rouge réservé aux icônes et bordures (≥ 3:1, WCAG 1.4.11) ». |
| Jaune `#F2B705` en texte sur fond clair | **1,73:1** (1,82:1 sur blanc) | **Absent** | **Correction (§7, règle d'usage des jetons) :** « le Jaune n'est jamais utilisé comme couleur de texte ni d'icône porteuse de sens ; il sert uniquement de fond, sous un texte Encre (8,98:1 selon l'audit). Pour un texte d'avertissement, utiliser Ambre `#7A5C00` sur `#FFF4CC` (5,68:1) ». |

**Testabilité :** NFR-12 dit « calcul des contrastes ». Il faut préciser comment : « chaque paire texte/fond déclarée dans les jetons est calculée par un script en CI (seuil 4,5:1, ou 3:1 pour le texte ≥ 18,66 px gras et les éléments non textuels) ; une paire sous le seuil fait échouer la CI ». Ajouter aussi la spécification UX (jetons corrigés) comme sortie attendue, conformément au §6 de l'audit.

## 6. Hygiène du dépôt public

État constaté dans le dépôt le 23/11 (`git status`, `git ls-files`) : le `.gitignore` est **modifié mais pas commité**. Il contient déjà `TerangaCycle AI/`, `*.pem`, `*.key`, `*.p12`, `models/`, `*.sqlite` et `.env*.local`. Aucun fichier `LICENSE`, `SECURITY.md` ou `.env.example` n'est suivi. Je n'ai pas pu vérifier les réglages GitHub depuis le poste.

| Constat | Statut | Où | Correction proposée |
|---|---|---|---|
| Dossier `TerangaCycle AI/` (handoff : noms, clé Figma) à ne pas committer | **Partiel** (fait dans le dépôt, absent des documents) | Absent du PRD et de l'addendum ; présent dans le `.gitignore` non commité | Committer le `.gitignore`. **Addendum, nouvelle section F « Hygiène du dépôt (E0) » :** « `TerangaCycle AI/` ne doit jamais être suivi ; test CI : `git ls-files` ne contient aucun chemin `TerangaCycle AI/` ». Au passage : le PRD (§0) cite la clé Figma (retirée depuis), que l'audit range parmi les éléments sensibles. Vérifier que le PRD peut être publié avec cette clé, ou la retirer avant de committer `_bmad-output/`. |
| Ajouts au `.gitignore` (`*.pem`, `*.key`, `*.p12`, `models/`, `*.sqlite`, `.env*.local`) | **Partiel** (fait, non commité, non tracé) | Absent des documents | Même section F de l'addendum ; NFR-10 « Aucun secret dans Git » le couvre déjà par Gitleaks. |
| `LICENSE` | **Partiel** | §6.3, §11 Q2 (avant le pilote) | Voir §4 : fichier présent avant H60. |
| `SECURITY.md` (signalement des failles) | **Absent** | — | **NFR-10 (ou section F de l'addendum) :** « `SECURITY.md` à la racine indique un canal privé de signalement (adresse ou *GitHub private vulnerability reporting*) et un délai de réponse ; vérifié par la CI (fichier présent) ». |
| `.env.example` | **Absent** | — (le `.gitignore` l'exclut déjà de l'ignore) | **Addendum F :** « `.env.example` liste toutes les variables (dont `ENV`, `DEMO_MODE`, clés JWT, pepper, clé AES) avec des valeurs factices ; Gitleaks ne doit y trouver aucun secret ; démarrer avec `ENV=production` sans les secrets requis échoue (même logique que FR-6) ». |
| Protection de `main` | **Absent** | — | **Addendum F :** « `main` protégée : PR obligatoire, CI verte requise (tests, Gitleaks, pip-audit, npm audit, Trivy), pas de *force push* ». Vérifiable par capture des réglages ou `gh api repos/:owner/:repo/branches/main/protection`. |
| *Secret scanning*, *push protection*, Dependabot | **Absent** | NFR-10 couvre la CI, pas les réglages GitHub | **Addendum F :** « *secret scanning* et *push protection* activés ; Dependabot (alertes et mises à jour) activé pour pip, npm, Docker et GitHub Actions » ; à placer dans l'epic E0 Socle (porte H24). |

## 7. Testabilité des exigences de sécurité du PRD (formulations sans seuil)

| Exigence | Formulation actuelle | Problème | Reformulation testable proposée |
|---|---|---|---|
| FR-1 | « avec une limite par IP et par appareil » | Pas de valeur | « 20 demandes par heure et par IP, 5 par appareil `[ASSUMPTION]` ; au-delà, 429 » |
| FR-1 | « Un plafond quotidien de coût SMS coupe l'envoi et alerte l'équipe » | Pas de valeur, canal d'alerte non défini | « N SMS par jour (configurable) ; au-delà, 503 `SMS_QUOTA_EXCEEDED` et message sur le canal d'alerte de l'équipe » |
| FR-2 | Durée du jeton d'accès non fixée | « Révoquée ne peut plus servir » n'est vrai qu'à l'expiration du jeton d'accès | « jeton d'accès ≤ 15 min ; après révocation ou déconnexion, le renouvellement renvoie 401 » |
| FR-5 / FR-35 | « désactive le compte immédiatement », « perd l'accès immédiatement » | Avec des JWT sans état, l'accès dure jusqu'à l'expiration du jeton | « la requête suivante après suspension ou suppression renvoie 401 » (cela impose une vérification d'état en base ou une liste de révocation : à noter dans l'addendum), **ou** « au plus tard 15 min après » |
| FR-3 / NFR-9 | « chaque route sensible », « 100 % des routes sensibles » | « Sensible » n'est pas défini | « toutes les routes `/v1` sauf une liste blanche publique explicite (`/healthz`, `/readyz`, `POST /v1/reports` anonyme, carte agrégée) ; la CI échoue si une nouvelle route n'est ni testée ni dans la liste blanche » |
| FR-29 | « refusée, avec un message clair » | Adjectif | « refusée (422 `OUT_OF_GEOFENCE`) ; le message indique la distance mesurée et le rayon de 150 m » |
| FR-34 | « jamais de point précis » | Pas de taille de cellule, ni de seuil | Voir S8 : cellule ≥ 500 m, masquage des cellules de moins de 3 Signalements |
| §6.1 | « le numéro est chiffré au repos » | Vérifiable seulement par une inspection | Voir S2 : test sur un dump de la base |
| §6.1 | « positions précises réservées au Personnel et au Collecteur de la Mission » | Contredit par FR-24 | Voir S8 |
| §6.2 | « vérification par échantillon du Personnel » | Pas de taux | « au moins 5 % des Preuves acceptées, tirées au hasard chaque semaine, sont revues `[ASSUMPTION]` ; le résultat est inscrit au Journal d'audit » |
| Glossaire | Journal d'audit « non modifiable » | Pas de test | Voir S10 : le rôle applicatif n'a ni `UPDATE` ni `DELETE` sur la table du journal |
| NFR-10 | « dépendances et image auditées ; versions épinglées » | Pas de seuil de blocage ; « épinglées » est flou | « la CI échoue sur toute vulnérabilité critique ou haute non justifiée dans un fichier d'exceptions daté ; images épinglées par digest et actions par SHA » |
| NFR-8 | TLS 1.2 et HSTS seulement | Aucun en-tête de sécurité applicatif | Ajouter CSP (voir §3), `X-Content-Type-Options: nosniff` et `Referrer-Policy`, vérifiés par test |

Points déjà testables (à conserver) : FR-1 (5 min, usage unique, 5 essais, 5 demandes par heure et par numéro), FR-6, FR-8, FR-9, FR-10, FR-23 (409, journal), FR-25 (409), FR-29 (150 m, horodatage serveur), FR-33 (aucun identifiant ; 3 décimales), NFR-14 (jamais de jeton ni de numéro complet dans les journaux).

## 8. Constats de l'audit hors du périmètre demandé (pour mémoire)

- **§1 État d'avancement.** Le squelette du dépôt, la CI et `docker compose up` sont absents, tout comme le modèle ONNX et le jeu de photos locales. Le PRD ne contient pas de section « risques ». Le risque « modèle ou jeu de données indisponible à H48 » est atténué par FR-16 (Modèle factice), mais SM-2 dépend d'un jeu de test local qui n'est pas dans le dépôt. Suggestion : ajouter au §11 « Q9. Jeu de photos locales et modèle : où sont-ils, et à quelle date sont-ils dans le dépôt ? Responsable : Aissatou ».
- **Python 3.15 sur le poste, 3.12 visé.** L'addendum A fixe Python 3.12, mais ne dit pas d'exécuter via Docker ou `uv`. Ajout possible dans l'addendum A.
- **§6 Démarche BMAD et epics E0–E6.** Les portes H24, H48 et H60 du §9.1 sont cohérentes avec les epics proposés : la carte de chaleur et l'export (E5) sont à H60 dans les deux documents, et le consentement (FR-4) est à H24 (memlog). Les points d'hygiène (§6 de ce rapport) relèvent de l'E0 Socle à H24.
