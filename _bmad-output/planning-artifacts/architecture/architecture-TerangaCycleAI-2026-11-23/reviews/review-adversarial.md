---
type: review
mode: adversarial
target: ../ARCHITECTURE-SPINE.md
against: ../../../prds/prd-TerangaCycleAI-2026-11-23/prd.md
date: '2026-11-23'
---

# Revue adverse de l'épine d'architecture — TerangaCycle AI

## Méthode

On joue l'adversaire. Pour chaque point de l'épine, on construit **deux unités d'un niveau en dessous**. Ce sont les epics que l'équipe de 3 personnes construira en parallèle pendant les 72 h :

- les modules backend `auth`, `reports`, `missions`, `lots`, `analytics`, `ai`, `notifications` et `core` ;
- les fonctionnalités de la PWA : `report`, `classify`, `offline`, `track`, `missions`, `proof`, `moderation`, `dashboard` et `admin` ;
- le pipeline `ml/` ;
- `infra/` et la CI.

Chaque unité respecte **à la lettre** tous les AD. Pourtant, assemblées, les deux ne fonctionnent pas ensemble. Chaque paire trouvée est un trou. On le bouche avec un nouvel AD (AD-17 et suivants) ou en resserrant la règle d'un AD existant. Les identifiants des AD existants ne changent pas.

Sévérités :

- **critique** : casse la boucle de démo (porte H24 ou H48), ou provoque une perte de données silencieuse ;
- **haute** : viole une conséquence testable du PRD, ou provoque une fuite ou une corruption ;
- **moyenne** : demande une reprise coûteuse au moment de l'intégration ;
- **basse** : friction ou dette.

## Verdict

L'épine fixe bien les **invariants locaux** : une porte pour les Statuts, un index unique, l'autorité du serveur. En revanche, elle laisse ouverts presque tous les **contrats entre unités** :

- la frontière de transaction entre services ;
- la forme des données de Classification et de Correction ;
- le transport des photos ;
- le schéma du manifeste du Modèle ;
- l'emplacement de l'idempotence ;
- la forme du principal anonyme ;
- les réactions qui remontent le graphe des modules ;
- le renouvellement de session côté PWA.

Trois paires cassent la démo telles quelles (T-1 à T-3). Dix autres violent une conséquence testable du PRD.

## Synthèse

| # | Trou | Sévérité | Correctif |
|---|---|---|---|
| T-1 | Frontière de transaction quand un service en appelle un autre ; effets « après commit » | critique | **AD-17** (nouveau), AD-3 et AD-4 resserrés |
| T-2 | Renouvellements de session concurrents (client généré, outbox, onglets) : la famille de jetons est révoquée | critique | AD-9 et AD-12 resserrés |
| T-3 | Transport des photos : multipart ou URL présignée | critique | AD-11 et AD-13 resserrés |
| T-4 | Désaccord IA : qui le calcule, quand, sur quoi, et où sont stockés les drapeaux | haute | **AD-19** (nouveau) |
| T-5 | Forme des Classifications, des Corrections et de `retained_type` ; consentement par Signalement | haute | **AD-19**, AD-2 resserré |
| T-6 | Manifeste du Modèle : clés, vocabulaire des classes, prétraitement, version, seuil | haute | AD-7 resserré, conventions |
| T-7 | Idempotence : stockage (Valkey ou base), liste des routes, requêtes concurrentes | haute | AD-5 resserré, AD-2 |
| T-8 | Outbox : l'identité change entre la mise en file et l'envoi (connexion) | haute | AD-12 et AD-5 resserrés |
| T-9 | Identifiant d'appareil : format, HMAC, table `devices` et qui l'écrit | haute | AD-9 resserré |
| T-10 | Historique des Statuts : « ayant atteint » (FR-31) et nouveautés pour l'anonyme (FR-21) | haute | AD-3 resserré, AD-2 |
| T-11 | Identifiant de tâche arq par entité : les notifications sont perdues | haute | AD-8 resserré |
| T-12 | JWT sans état contre suspension, changement de rôle et suppression (401 à la requête suivante) | haute | AD-9 resserré |
| T-13 | Réactions à contre-sens du graphe (suppression de compte, retrait du consentement) | haute | **AD-21** (nouveau) |
| T-14 | Expiration de Mission contre Preuve concurrente : ordre des verrous, mécanisme, horloge | moyenne | AD-3 resserré, **AD-18** (nouveau) |
| T-15 | `is_demo` contre `DEMO_MODE` contre `ENV=demo` | moyenne | AD-14 resserré |
| T-16 | Vues analytiques : propriétaire, cycle de vie, tables d'`auth` | moyenne | **AD-22** (nouveau), AD-2 |
| T-17 | Stockage : miniatures, photo de Lot, empreinte de photo, point d'accès public, purge | moyenne | AD-13 resserré |
| T-18 | Forme de l'entrée d'audit (acteur système ou appareil) ; effacement de l'IP malgré l'interdiction d'UPDATE | moyenne | AD-15 resserré |
| T-19 | File de classification bornée : personne ne relance les Signalements en attente | moyenne | AD-8 resserré |
| T-20 | Contenu des tâches de notification ; flèche `lots → notifications` absente | moyenne | **AD-21**, graphe |
| T-21 | Retrait d'un Signalement anonyme (FR-5) : aucun chemin d'état | moyenne | AD-3 resserré |
| T-22 | Année du Numéro de suivi, compteur, fuseau horaire | basse | **AD-18** |
| T-23 | Petits trous de plomberie : codes d'erreur et i18n, génération OpenAPI, 408, `ST_Contains`, persistance de Valkey, origine unique | basse | AD-11, AD-12, AD-6, infra |

---

## T-1 — Frontière de transaction entre services `[critique]`

**Unité A, `reports` (Statuts).** Elle applique la convention « une transaction par requête, ouverte par le service ». `reports.service.transition()` ouvre donc sa transaction, fait l'`UPDATE` conditionnel et l'audit, valide (`commit`), puis met en file la notification « après le commit » (AD-3).

**Unité B, `missions` (acceptation).** Elle applique AD-4 : elle ouvre sa transaction, insère la Mission, puis appelle `reports.service.transition(validé → assigné)`, « dans une transaction ».

**Ce qui casse à l'assemblage.** Trois issues sont possibles, toutes conformes à l'épine :

1. SQLAlchemy lève `A transaction is already begun` : l'acceptation échoue toujours, et la porte H48 n'est pas atteinte.
2. `transition()` utilise une autre session. Le Signalement passe `assigné` et cette transaction est validée. Ensuite, l'insertion de la Mission perd la course à l'index unique et revient en arrière. Résultat : un Signalement `assigné` sans Mission `active`, bloqué pour toujours.
3. `transition()` valide la transaction partagée en cours de route. La notification « Assigné » part, puis la suite échoue : la notification décrit un changement qui n'existe pas.

Le même problème touche la Preuve (`missions` vers `reports.transition(assigné → collecté)`), l'annulation, l'expiration et l'assignation manuelle.

**Correctif — nouvel AD :**

```markdown
### AD-17 — Unité de travail et effets après commit

- **Binds:** tous les services, `core/db`, `core/jobs`, `core/storage`, AD-3, AD-4, AD-8.
- **Prevents:** une transaction validée à moitié quand un service en appelle un autre, et des effets externes (tâche, push, suppression d'objet) émis pour une transaction annulée.
- **Rule:**
  - `core.db` porte **une** session et **une** transaction par requête HTTP ou par exécution de tâche arq, dans un `contextvar`.
  - Le décorateur `@core.db.transactional` sur une méthode publique de service :
    - ouvre la transaction s'il n'y en a pas ;
    - sinon, **rejoint** celle de l'appelant.
    Seul le niveau le plus externe valide (`commit`) ou annule (`rollback`). Aucun service n'appelle `commit`, `rollback` ni `begin` directement.
  - Tout effet externe passe par `core.db.after_commit(fn, *args)` : mise en file arq, envoi push, suppression d'objet S3. L'effet n'est exécuté qu'après le commit **le plus externe**, et il est abandonné en cas de rollback.
  - `core.db.after_rollback(fn, *args)` sert seulement à nettoyer les objets S3 écrits avant le commit (AD-13).
  - Un test d'intégration force une exception après `reports.service.transition()` dans `missions.service.accept()`. Il vérifie que rien n'est écrit, qu'aucune tâche n'est en file et qu'aucune entrée d'audit n'existe.
```

**AD-3, point 3 de la règle, remplacé par :** « la mise en file des notifications par `core.db.after_commit` (AD-17), jamais directement ».

**Convention « Transactions », remplacée par :** « Une transaction par requête ou par tâche, gérée par AD-17 ; les services rejoignent la transaction de leur appelant ; les repositories ne valident jamais. »

---

## T-2 — Renouvellements concurrents : la famille de jetons est révoquée `[critique]`

**Unité A, `web/src/api` (client généré).** Son intercepteur réagit à un 401 en appelant `/v1/auth/refresh`, puis rejoue la requête. C'est conforme à AD-9 et AD-11.

**Unité B, `web/src/offline` (outbox).** Elle applique AD-12 : « sur 401, un renouvellement du jeton, puis un seul réessai ». Elle appelle donc elle aussi `/v1/auth/refresh`.

**Ce qui casse.** Au retour du réseau, les deux unités reçoivent un 401 au même moment, parce que le jeton de 15 min a expiré pendant la coupure. Elles envoient chacune le même cookie de renouvellement. Le serveur applique AD-9 : la deuxième présentation est une réutilisation, et **toute la famille est révoquée**. Le Collecteur ou le Modérateur est déconnecté en pleine démo. Deux onglets ouverts produisent le même effet. Un Background Sync dans le service worker aussi : il n'a pas le jeton gardé en mémoire et renouvelle donc de son côté.

**Correctif — AD-9, puces ajoutées :**

```markdown
  - **Renouvellement côté PWA :** une seule fonction, `refreshSession()` dans `web/src/api/session.ts`, appelle `/v1/auth/refresh`.
    - Elle est à vol unique : une promesse partagée dans l'onglet.
    - Elle est sérialisée entre onglets par `navigator.locks.request('tc-refresh', …)`.
    - L'intercepteur du client généré et l'outbox l'appellent tous deux. Aucun autre code n'appelle la route.
  - **Tolérance côté serveur :** un jeton de renouvellement présenté moins de `REFRESH_REUSE_GRACE_S` (10 s) après sa rotation renvoie 401 `refresh_superseded`, **sans** révoquer la famille. Au-delà de ce délai, la réutilisation révoque la famille (FR-2).
```

**AD-12, puce ajoutée :** « L'outbox s'exécute dans la fenêtre, déclenchée par l'événement `online`, l'ouverture de l'application ou « Réessayer » ; jamais dans le service worker (pas de Background Sync au MVP). »

---

## T-3 — Transport des photos `[critique]`

**Unité A, `reports` avec `core/storage`.** AD-13 dit que « seul `core/storage` parle l'API S3 », et le schéma des conteneurs montre déjà que la PWA utilise des URL signées. L'unité expose donc `POST /v1/uploads`, qui renvoie une URL `PUT` présignée, puis `POST /v1/reports {object_key, …}`. C'est conforme : la PWA ne parle pas l'API S3, elle suit une URL.

**Unité B, `web/features/report` et `offline`.** AD-12 dit que chaque élément porte **une** clé idempotente (`client_uuid`). L'outbox stocke donc `{meta, photo: Blob}` et envoie **un** `POST /v1/reports` en multipart.

**Ce qui casse.** Les deux unités ne parlent pas le même protocole : en deux temps d'un côté, en un temps de l'autre. Avec le protocole en deux temps, l'étape 1 n'a pas de clé idempotente. Le ré-encodage serveur (FR-8) doit relire l'objet depuis S3. Une photo de 12 Mpx entre dans le bucket avant toute validation. Sur un réseau faible, la reprise de l'étape 1 crée des objets orphelins. Le même choix se pose pour la Preuve (deux photos) et pour la photo de Lot (FR-38). C'est la porte H24, « Signalement relié à la PWA ».

**Correctif — AD-11, puce ajoutée :**

```markdown
  - **Photos :** elles transitent **uniquement par l'API**, en `multipart/form-data`, dans la requête qui crée la ressource :
    - `POST /v1/reports` : parties `meta` (JSON `ReportCreate`) et `photo` ;
    - `POST /v1/missions/{id}/proof` : parties `meta`, `photo_before` et `photo_after` ;
    - `POST /v1/lots` : parties `meta` et `photo`.
    Le corps multipart est décrit dans l'OpenAPI, donc le client généré l'expose. Aucune URL présignée en écriture : les URL signées servent seulement à la lecture (AD-10).
```

**AD-13, puce ajoutée :** « Le serveur refuse une partie photo de plus de 1 Mo ou 12 Mpx (413 ou 422) avant tout appel à `core/storage`. »

---

## T-4 — Désaccord IA : qui le calcule, quand, et sur quoi `[haute]`

**Unité A, `moderation` dans la PWA et la route de file dans `reports`.** Elle calcule le Désaccord IA **à la lecture**, dans la requête de la File de modération : `client_predicted_type <> classification serveur`. Rien dans l'épine ne l'interdit.

**Unité B, la tâche `classify` (AD-8) avec `reports.service`.** Elle calcule le Désaccord **à l'écriture** de la Classification serveur, et le stocke sous forme de booléen.

**Ce qui casse :**

- **La comparaison n'est pas la même.** A compare `client_predicted_type`. B compare le « Type de déchet envoyé par l'appareil », c'est-à-dire le choix du Citoyen s'il existe (Glossaire). Pour un Signalement corrigé par le Citoyen, les deux unités donnent des drapeaux opposés.
- **Le filtre par drapeau ne tient pas.** FR-22 l'exige, paginé par curseur (AD-11). Un calcul à la lecture ne s'indexe pas.
- **Le cas sans Classification locale n'est pas couvert.** FR-15 demande qu'il n'y ait pas de drapeau. A teste `client_predicted_type IS NULL`. B teste `client_confidence IS NULL`. Les colonnes `client_*` n'ont pas de règle de nullité.
- **Les versions du Modèle peuvent différer.** Si la PWA a gardé en cache `tc-mnv3-1.0.0` et que le serveur tourne en `1.1.0`, on obtient exactement le Désaccord artificiel qu'AD-7 veut empêcher.
- **Les autres drapeaux sont dans le même flou.** « Faible confiance », « position imprécise » et Doublon probable n'ont ni propriétaire ni moment de calcul. Le rejet pour doublon (FR-23) doit afficher le Numéro de suivi d'origine : il faut une référence stockée.

**Correctif :** voir AD-19, au trou T-5.

---

## T-5 — Classifications, Corrections et `retained_type` : deux formes de données `[haute]`

**Unité A, `reports` (modération).** À la validation, elle écrit `reports.retained_type`. Elle enregistre la Correction comme une ligne `classifications(source='moderator')`, puisqu'AD-2 ne liste aucune table `corrections`.

**Unité B, l'export des Corrections (FR-13, `ml/` et `analytics`).** Elle lit une table `corrections` qu'elle suppose exister. Elle prend la Classification locale dans `classifications(source='local')`, alors qu'AD-6 la range dans `reports.client_*`.

**Ce qui casse :**

- **Deux endroits pour la Classification locale** : `client_*` et une ligne `local`. Ils finissent par diverger.
- **Aucune table pour les Corrections.** Le test de FR-13 (« un Signalement avec refus n'apparaît pas dans l'export ») ne peut pas s'écrire de la même façon des deux côtés.
- **La Correction du Citoyen à la création** n'a pas d'écrivain désigné.
- **`retained_type` n'est pas couvert par AD-3.** La signature `transition(report_id, from, to, actor, reason)` ne permet pas de fixer `retained_type`. Une unité fait un `UPDATE` séparé sans garde de Statut, et un deuxième Modérateur peut écraser le type retenu d'un Signalement que le premier a déjà validé.
- **Le consentement au réentraînement (FR-4)** doit être « enregistré sur chaque Signalement » et pouvoir être retiré rétroactivement. Il n'a pas de propriétaire. `auth` le met dans `users`. `reports` en prend un instantané. L'export lit l'un ou l'autre.

**Correctif — nouvel AD :**

```markdown
### AD-19 — Données de Classification, Corrections et drapeaux

- **Binds:** FR-12 à FR-15, FR-22, FR-23, FR-13 (export), FR-24, FR-4 (consentement par Signalement).
- **Prevents:** deux formes de la même Classification, des Désaccords IA calculés de deux façons, un Type de déchet retenu écrit hors de la porte des Statuts, et un export qui ignore le consentement.
- **Rule:**
  - **Classification locale :** elle est stockée **uniquement** dans `reports` :
    - `client_predicted_type`, `client_confidence` et `client_model_version` : les trois sont nuls ensemble, ou renseignés ensemble (contrainte `CHECK`) ;
    - `citizen_type` : le choix du Citoyen, nul s'il a gardé la proposition.
    Le « Type de déchet envoyé par l'appareil » est `device_type = coalesce(citizen_type, client_predicted_type)`, en colonne générée.
  - **Classification serveur :** une ligne `classifications(report_id, model_version, predicted_type, confidence, scores jsonb, created_at)` par version, unique sur `(report_id, model_version)`. Elle n'est écrite que par `reports.service.record_server_classification()`, appelée par la tâche `classify`.
  - **Corrections :** elles sont dans la table `corrections`, propriété de `reports` : `(report_id, actor_kind ∈ {citizen, moderator}, actor_ref, original_type, original_source ∈ {local, server, prefill}, model_version, corrected_type, created_at)`. Deux cas, et seulement deux :
    - à la création, si `citizen_type` et `client_predicted_type` sont renseignés et différents ;
    - à la validation, si `retained_type` diffère du type pré-rempli (FR-14). La Classification serveur est alors recopiée dans la ligne.
  - **Type de déchet retenu :** il n'est écrit que par `reports.service.validate(report_id, retained_type, actor)`. Le même `UPDATE … WHERE status = 'pending_review'` fixe `retained_type` et le Statut, grâce à `transition(…, set_fields={…})`. `retained_type` est `NOT NULL` dès que le Statut a atteint `validated` (contrainte `CHECK`).
  - **Drapeaux :** ce sont des colonnes de `reports`, écrites seulement par `reports.service` et indexées pour le filtre de FR-22 :
    - à la création : `flag_low_confidence` (`client_confidence` sous le seuil du manifeste, AD-7), `flag_imprecise_position` (précision supérieure à 50 m), `duplicate_of_report_id` (distance, délai, empreinte de photo, AD-13) ;
    - à l'écriture de la Classification serveur : `flag_ai_disagreement`, qui vaut `NULL` si `client_model_version` est nul **ou différent** de la version serveur (Désaccord non comparable), et `device_type <> predicted_type` sinon.
    Aucun drapeau n'est recalculé à la lecture.
  - **Consentement au réentraînement :** la colonne `reports.training_consent` reçoit l'instantané envoyé à la création (champ `training_consent` de `ReportCreate`). Le retrait rétroactif passe par AD-21. L'export des Corrections ne sélectionne que les Signalements ayant atteint `validated` avec `training_consent = true`.
```

**AD-2, tableau, ligne `reports` :** ajouter `corrections` et `report_status_events` (voir T-10).

---

## T-6 — Manifeste du Modèle : `ml/` et les deux chargeurs `[haute]`

**Unité A, `ml/export.py`.** Elle produit `tc-mnv3-1.0.0.json` :

```json
{"classes": ["plastique","metal","verre","organique","mixte"], "input_size": 224,
 "mean": [0.485,0.456,0.406], "std": [0.229,0.224,0.225], "resize": "bilinear", "T": 1.4}
```

Le graphe ONNX inclut le softmax. C'est conforme à AD-7 : tous les champs demandés sont présents.

**Unité B, `ai` (Python) et `features/classify` (TypeScript).** Elles lisent `class_order`, `image_size: [224, 224]` et `temperature`. Elles appliquent `softmax(logits / T)` sur la sortie. Elles normalisent des pixels de 0 à 255. L'énumération `waste_type` de la base vaut `plastic`, `metal`, `glass`, `organic` et `mixed`, parce que la convention de nommage dit « code et base en anglais ».

**Ce qui casse :**

- **Les clés du JSON** ne sont pas les mêmes d'un côté et de l'autre.
- **Le vocabulaire des classes diffère** : les classes en français du JSON ne correspondent pas à l'énumération anglaise. Les conventions donnent la correspondance des Statuts, mais **pas** celle des Types de déchet, de la Taille de tas, de `pesé` / `estimé`, de la Revue de Preuve ni du Statut de Lot.
- **La température est appliquée deux fois**, sur un softmax déjà calculé.
- **L'échelle des pixels diffère** (0 à 1 contre 0 à 255).
- **L'orientation EXIF :** le navigateur applique l'orientation, alors que le serveur supprime l'EXIF sans l'appliquer (FR-8). On obtient des Désaccords IA artificiels sur chaque photo prise en portrait.
- **Les octets classés :** le navigateur classe l'image avant compression, alors que le serveur classe le JPEG de 300 Ko ré-encodé.
- **Le seuil de 60 %** est dans `Settings` d'après AD-14, mais la PWA hors ligne n'a pas accès à `Settings`.
- **La version « courante »** du Modèle n'est fixée nulle part : l'image Docker et le build Vite peuvent embarquer deux versions différentes.

Le test doré d'AD-7 compare Python et TypeScript, pas `ml/` et les chargeurs. Il passe si les deux chargeurs partagent la même mauvaise lecture.

**Correctif — AD-7, règle complétée :**

```markdown
  - Le JSON suit le schéma `ml/contract/model-manifest.schema.json` (`schema_version: 1`). La CI valide contre ce schéma la sortie de `ml/export.py`, le chargeur Python et le chargeur TypeScript. Champs :
    - `model_version` ;
    - `onnx_file` et `onnx_sha256` ;
    - `classes` : exactement les codes de l'énumération API `WasteType`, dans l'ordre des sorties ;
    - `input` : `{name, layout: "NCHW", size: [h, w], color: "RGB", scale: "0-1", mean[3], std[3], resize: "shorter_side_then_center_crop", interpolation: "bilinear"}` ;
    - `output` : `{name, kind: "logits"}` ;
    - `temperature` ;
    - `confidence_threshold` (0.60) ;
    - `kind` : `"trained"` ou `"fake"`.
  - Le graphe ONNX sort des **logits** : aucun softmax dans le graphe. Les deux implémentations calculent `softmax(logits / temperature)`.
  - **Mêmes octets des deux côtés.** La PWA classe exactement le JPEG qu'elle envoie : après conversion HEIC, application de l'orientation (`createImageBitmap(…, {imageOrientation: 'from-image'})`) et compression. Le serveur classe la photo stockée, après `ImageOps.exif_transpose()` puis la suppression de l'EXIF (FR-8).
  - **Seuil de confiance :** `confidence_threshold` vient du manifeste et nulle part ailleurs. `needs_user_choice = confidence < confidence_threshold`, des deux côtés.
  - **Version courante :** le fichier `ml/release/current.json` (`{"model_version": "x.y.z"}`) est la seule source. Le Dockerfile de l'API et le build Vite copient `ml/release/tc-mnv3-<version>.{onnx,json}`. La CI échoue si les deux artefacts embarqués diffèrent. Le Modèle factice a son propre manifeste (`kind: "fake"`).
```

**Conventions, ligne « Nommage », compléter par :**
« Type de déchet : `plastique` = `plastic`, `métal` = `metal`, `verre` = `glass`, `organique` = `organic`, `mixte` = `mixed`. Taille de tas : `small`, `medium`, `large`. Poids déclaré : `weighed`, `estimated`. Revue de Preuve : `unreviewed`, `confirmed`, `disputed`. Statut de Lot : `available`, `reserved`. Les libellés français n'existent que dans `fr.json`. »

**AD-14 :** retirer « 60 % » de la liste des réglages ; il est dans le manifeste (AD-7).

---

## T-7 — Idempotence : où, pour quelles routes, et sous concurrence `[haute]`

**Unité A, `missions` (Preuve).** Elle stocke la réponse dans Valkey (`idem:<principal>:<route>:<key>`, TTL 24 h), **après** le commit, via un middleware. C'est conforme à AD-5 : la réponse est conservée 24 h avec la bonne clé.

**Unité B, `lots` (réservation, FR-40).** Elle crée sa propre table `lot_idempotency`. AD-2 ne dit rien sur ce point : l'idempotence n'a pas de propriétaire.

**Unité C, `web/features/missions`.** Elle n'envoie pas d'`Idempotency-Key` sur l'acceptation : AD-5 parle d'« autres POST sensibles », sans les lister.

**Ce qui casse :**

- **Avec Valkey,** une panne entre le commit et l'écriture de la clé fait qu'un renvoi recrée l'effet. Un double appui envoyé en parallèle passe deux fois, puisque rien n'est encore stocké.
- **Deux implémentations** de l'idempotence coexistent.
- **L'acceptation renvoie 400** au client, qui n'a pas envoyé l'en-tête. FR-25 (« un renvoi renvoie la Mission existante ») échoue.
- **Une même clé avec un corps différent** n'a pas de comportement défini.

**Correctif — AD-5, puce « Preuves de collecte… » remplacée par :**

```markdown
  - **Toute requête qui modifie l'état** (`POST`, `PUT`, `PATCH` ou `DELETE` sous `/v1`) exige l'en-tête `Idempotency-Key` (UUID) ; sans lui, la réponse est 400 `idempotency_key_required`. Seules exceptions : `/v1/auth/*` et `POST /v1/reports`, couvert par `client_uuid`.
    - L'en-tête est imposé par la dépendance partagée `core.idempotency.require_key`. Il est donc déclaré dans l'OpenAPI, et le client généré l'exige.
    - Le test de la table des routes échoue si une route qui modifie l'état n'a ni la dépendance ni une exemption listée.
  - **Stockage :** table `idempotency_records`, propriété de `core/idempotency`. Clé primaire `(principal_key, route_template, key)`, plus `request_sha256`, `response_status`, `response_body jsonb` et `created_at`. `principal_key` est l'`owner_key` d'AD-9.
  - **Même transaction que l'effet :**
    - la ligne est insérée **au début** de la transaction métier (`INSERT … ON CONFLICT DO NOTHING`). Une requête concurrente attend donc la fin de la première sur l'index unique ;
    - la réponse est écrite avant le commit.
  - **En cas de conflit :**
    - même empreinte de corps : la réponse stockée est rejouée ;
    - empreinte différente : 422 `idempotency_key_reused`.
  - Une tâche cron purge les lignes de plus de 24 h. Valkey n'est **jamais** utilisé pour l'idempotence.
  - Les clés naturelles restent en place : `unique(proofs.mission_id)` et l'index partiel d'AD-4.
```

**AD-2 :** ajouter la ligne `core/idempotency` → `idempotency_records`.

---

## T-8 — Outbox : l'identité change entre la mise en file et l'envoi `[haute]`

**Unité A, `web/offline`.** Elle applique AD-12 : « l'envoi joint toujours le jeton d'accès, ou `X-Device-Id` ». Au moment de l'envoi, elle joint le jeton si l'utilisateur est connecté, sinon l'Identifiant d'appareil.

**Unité B, `reports`.** Elle applique AD-5 : `owner_key` vaut `user:<id>` si un jeton est présent, `device:<hmac>` sinon. Pour un autre `owner_key`, elle renvoie 409 `client_uuid_conflict`.

**Ce qui casse.** Un Citoyen anonyme met un Signalement en file. Le premier envoi arrive au serveur (`device:…`), mais la réponse est perdue. Le Citoyen se connecte, puis l'outbox réessaie avec le jeton (`user:…`). Le serveur renvoie 409, et l'outbox classe l'élément en échec définitif (« tout autre 4xx »). Le Signalement existe, mais il disparaît de la liste de l'appareil et de celle du compte. Le scénario inverse (déconnexion entre deux essais) produit le même résultat.

**Correctif — AD-12, puce « L'envoi joint… » remplacée par :**

```markdown
  - **Identité figée :** chaque élément enregistre l'identité de sa mise en file, `principal: 'device' | 'user:<id>'`, et est toujours renvoyé avec **cette** identité :
    - un élément `device` part avec `X-Device-Id` seul, sans `Authorization`, même si l'utilisateur s'est connecté depuis ;
    - un élément `user:<id>` attend une session de cet utilisateur. Sans elle, il reste dans l'état « en attente de connexion » : ce n'est pas un échec.
  - Réessai aussi sur 408, conformément à FR-18.
```

**AD-5, ajout :** « `owner_key` vaut `user:<id>` si et seulement si un jeton d'accès valide est présent ; `X-Device-Id`, s'il est joint en plus, ne sert alors qu'aux limites de débit. »

---

## T-9 — Identifiant d'appareil : format, HMAC et enregistrement `[haute]`

**Unité A, `auth`.** Elle possède `devices` (AD-2). Elle expose `POST /v1/devices` pour enregistrer l'appareil, et applique la limite OTP par appareil (FR-1) avec `base64(HMAC(OTP_KEY, id))`.

**Unité B, `reports`.** Elle calcule `owner_key = "device:" + hmac_sha256(SECRET_KEY, id).hexdigest()`. Elle n'appelle jamais `auth`, puisque l'anonyme n'a pas besoin de compte.

**Unité C, `web`.** Elle génère un `crypto.randomUUID()` et ne fait aucun enregistrement.

**Ce qui casse :**

- **Trois empreintes différentes** pour le même appareil : les limites de débit, la propriété (AD-5) et le principal d'idempotence ne se recoupent pas.
- **La table `devices` reste vide.** Elle ne peut pas porter le retrait du consentement de l'anonyme (FR-4), alors que `reports` en aurait besoin.
- **Le contrôle de propriété échoue** si A impose l'enregistrement et que C ne le fait pas.
- **Un UUID v4 n'est pas un secret fort** au sens du Glossaire (122 bits, admissible), mais **aucun format** n'est validé. Un `X-Device-Id` vide ou de 2 caractères crée un propriétaire facile à deviner, donc la fuite S1.
- **Le test de FR-2** (« aucun jeton dans IndexedDB ») échoue si l'Identifiant d'appareil y est stocké sans exception déclarée.

**Correctif — AD-9, puce « Citoyen anonyme » remplacée par :**

```markdown
  - **Citoyen anonyme :**
    - **Format :** `X-Device-Id` est un secret de 32 octets aléatoires (`crypto.getRandomValues`) en base64url (43 caractères), généré au premier lancement et stocké dans la table Dexie `meta`. C'est la seule exception déclarée au test de stockage de FR-2. Un autre format renvoie 400 `invalid_device_id`.
    - **Principal unique :** la dépendance `core.security.principal()` est la seule à lire `Authorization` et `X-Device-Id`. Elle renvoie `Principal(kind, user_id, role, device_hash, owner_key)`, avec `device_hash = HMAC-SHA256(DEVICE_HMAC_KEY, id)` en hexadécimal minuscule. Les limites de débit, AD-5 et l'idempotence utilisent ce `device_hash`, sans le recalculer.
    - **Pas d'enregistrement explicite :** il n'y a pas de route `/v1/devices` pour enregistrer. `reports.service.create()` appelle `auth.service.touch_device(device_hash)` (insertion ou mise à jour, dans la même transaction). `devices` porte `first_seen_at` et `training_consent`.
    - `reports` stocke `owner_key` (texte) et `author_user_id` (nullable). Il n'y a pas de clé étrangère vers `devices`.
```

---

## T-10 — Historique des Statuts : « ayant atteint » et « depuis la dernière visite » `[haute]`

**Unité A, `notifications`.** Elle implémente FR-21 avec la table `notifications(user_id, …)`, conformément au schéma (`USERS ||--o{ NOTIFICATIONS`). La route `GET /v1/notifications?since=` sert l'écran d'accueil.

**Unité B, `web/features/track`.** Pour le Citoyen anonyme, que FR-21 inclut explicitement, elle appelle la même route avec `X-Device-Id`. Elle reçoit 401, puisqu'il n'y a pas de `user_id`.

**Unité C, `analytics`.** Elle calcule « ayant atteint `validé` » (FR-31) en parcourant `audit_logs.after->>'status'`. Le contenu de `before` et `after` n'est fixé nulle part, et `reports` y écrit `{"state": …}`.

**Ce qui casse :**

- FR-21 n'est pas servi pour l'anonyme.
- Le Taux de traitement (le test « 60 % » de FR-31) dépend d'un format d'audit que personne ne garantit.
- L'historique des Statuts visible du Personnel (FR-36) est reconstruit une troisième fois.

**Correctif — AD-3, puces ajoutées :**

```markdown
  - `reports.service.transition()` insère, dans la même transaction, une ligne `report_status_events(id bigserial, report_id, from_status, to_status, reason, actor_kind, occurred_at)`. Cette table est l'**unique** historique des Statuts. Elle sert :
    - à « ayant atteint » (FR-31), via `v_report_facts` ;
    - au détail vu par le Personnel (FR-36) ;
    - à FR-21.
    L'audit reste la trace de conformité. On ne le lit jamais pour calculer.
  - **FR-21 :** `GET /v1/reports/mine/changes?cursor=` est servi par `reports`, pour un `owner_key` utilisateur **ou** appareil. Le curseur de « dernière visite » est gardé sur l'appareil.
  - Le module `notifications` ne fait que le **push** : `push_subscriptions`, plus `notifications` comme journal d'envoi idempotent, avec la clé `status_event_id`.
```

---

## T-11 — Identifiant de tâche par entité : des notifications perdues `[haute]`

**Unité A, `reports`.** Elle applique AD-8 à la lettre : « une tâche est identifiée par `<type>:<entity_id>` ». La notification d'un changement de Statut est donc `notify:<report_id>`.

**Unité B, `missions`.** Elle accepte une Mission, ce qui fait passer le Signalement de `validé` à `assigné`, quelques secondes après la validation. Elle met en file `notify:<report_id>`.

**Ce qui casse.** arq refuse en silence un identifiant de tâche déjà présent, en file ou en résultat conservé (`keep_result`, 1 h par défaut). La notification « Assigné » n'est jamais envoyée. FR-21 (push en moins de 1 min) échoue sans aucune erreur. Le même risque touche une deuxième Classification après une montée de version du Modèle.

**Correctif — AD-8, puce « Une tâche est identifiée… » remplacée par :**

```markdown
  - **Identifiant de tâche :**
    - `<type>:<entity_id>` pour une tâche dont l'effet dépend de l'**état courant** de l'entité : `classify:<report_id>:<model_version>`, `thumb:<photo_id>`, `expire:<mission_id>` ;
    - `<type>:<event_id>` pour une tâche qui traite un **événement** : `notify:<status_event_id>`, ou une réaction d'AD-21.
  - Chaque tâche relit l'état et ne fait rien s'il est dépassé (par exemple, une Mission qui n'est plus `active`).
  - Les tâches sont mises en file par `core.db.after_commit` (AD-17).
```

---

## T-12 — JWT sans état contre « refusé à la requête suivante » `[haute]`

**Unité A, `auth` (administration, FR-35 et FR-5).** La suspension et la suppression mettent `users.status` à jour, et le changement de rôle met `users.role` à jour. C'est conforme.

**Unité B, `core/security`.** `require_role(...)` vérifie la signature, `exp`, `iss`, `aud` et `kid`, puis lit `role` dans le jeton. C'est conforme à AD-9 : le jeton est autoporteur.

**Ce qui casse.** Pendant 15 minutes au plus, un Collecteur suspendu continue d'accepter des Missions et de soumettre des Preuves. Un compte supprimé continue de lire. Un Modérateur rétrogradé continue de modérer. Cela viole FR-35 et FR-5 (« la requête suivante est refusée (401) »), et le test d'autorisation par rôle échoue juste après un changement de rôle.

**Correctif — AD-9, puce ajoutée :**

```markdown
  - **Révocation immédiate :** le jeton porte `tv`, la version de jeton de l'utilisateur.
    - À chaque requête, `require_role` lit `(status, role, token_version)` dans Valkey (`authz:<user_id>`, TTL 60 s), avec la base en repli.
    - Si `status ≠ active` ou si `tv ≠ token_version`, la réponse est 401 `session_revoked`.
    - Le rôle utilisé est celui de la base ou du cache, jamais celui du jeton.
    - `auth.service` incrémente `token_version` et invalide `authz:<user_id>` par `after_commit` (AD-17), à chaque suspension, changement de rôle, suppression ou déconnexion globale.
```

---

## T-13 — Réactions à contre-sens du graphe des modules `[haute]`

**Unité A, `auth` (FR-5, suppression de compte, et FR-4, retrait du consentement).** Le graphe interdit `auth → reports`, car `reports → auth` existe déjà et le lien créerait un cycle. L'unité se contente donc d'anonymiser `users` et de mettre `users.training_consent` à faux.

**Unité B, `reports`.** Elle garde les photos et Positions des Signalements `en attente de modération` et `rejeté` d'un compte supprimé, et `training_consent = true` sur les Signalements passés.

**Ce qui casse.** Deux conséquences testables ne sont pas tenues : la suppression des photos et Positions (FR-5), et l'exclusion rétroactive des exports (FR-4 et FR-13). Pour les satisfaire, chaque développeur aura le choix entre deux contournements, tous deux interdits : briser AD-1 avec l'import de `reports.service` dans `auth`, ou briser AD-2 avec une clé étrangère `ON DELETE` qui décide d'une règle métier dans la base. Le même cas se présente pour la suspension d'un Collecteur qui a une Mission `active`.

**Correctif — nouvel AD :**

```markdown
### AD-21 — Réactions inter-modules et événements

- **Binds:** AD-1, AD-8, FR-4, FR-5, FR-21, FR-28, FR-35, FR-40.
- **Prevents:** un cycle d'imports pour une réaction qui remonte le graphe, une règle métier cachée dans une clé étrangère, et des tâches dont le contenu diffère entre l'émetteur et le consommateur.
- **Rule:**
  - **Événements :** les événements de domaine sont des modèles Pydantic dans `core/events.py` :
    - `ReportStatusChanged{event_id, report_id, tracking_number, owner_key, author_user_id, to_status, reason}` ;
    - `MissionAssigned{…}` ;
    - `AccountDeleted{user_id}` ;
    - `TrainingConsentWithdrawn{owner_key}` ;
    - `CollectorSuspended{user_id}` ;
    - `LotReserved{…}`.
    Chaque contenu est **autosuffisant** : son consommateur n'a pas à rappeler l'émetteur.
  - **Émission :** un module émet un événement par `core.jobs.emit(event)`, sous `after_commit` (AD-17).
  - **Réactions :** les réactions sont dans `backend/app/reactions.py`. C'est la racine de composition, hors des modules, et le seul fichier autorisé (contrat import-linter) à importer plusieurs services pour une réaction. Exemples :
    - `AccountDeleted` → `reports.service.anonymize_author()`, puis `missions.service.on_collector_deleted()` ;
    - `TrainingConsentWithdrawn` → `reports.service.revoke_training_consent(owner_key)`.
    Chaque réaction est idempotente.
  - Aucune clé étrangère `ON DELETE CASCADE` ni `SET NULL` entre des tables de modules différents.
```

**Graphe :** ajouter la flèche `lots -.->|tâche arq| notifications`, pour FR-40.

---

## T-14 — Expiration de Mission contre Preuve concurrente `[moyenne]`

**Unité A, `missions` (tâche d'expiration).** Elle applique AD-3 et AD-8 : `missions.service.transition(active → expired)`, **puis** `reports.service.transition(assigned → validated)`.

**Unité B, `missions` (Preuve).** Elle vérifie d'abord le géorepérage. Elle passe le Signalement à `collecté`, en verrouillant la ligne `reports`, puis la Mission à `terminée`.

**Ce qui casse :**

- **Verrous dans l'ordre inverse.** Si les deux s'exécutent à 48 h près, PostgreSQL détecte un interblocage (`40P01`). Une des deux opérations reçoit une erreur 500 au lieu d'un 409 propre. Si c'est la Preuve, le Collecteur perd sa saisie.
- **Deux mécanismes d'expiration.** A planifie une tâche différée `expire:<mission_id>` (`_defer_until`) à l'acceptation. Une autre unité ajoute un balayage cron. Si la mise en file différée est perdue (Valkey sans persistance, voir T-23), la Mission n'expire jamais.
- **Horloge non simulable.** Le test « 48 h et 1 min avec une horloge simulée » (FR-42) ne peut pas piloter `now()` dans PostgreSQL et `datetime.now()` dans Python en même temps.

**Correctif — AD-3, puce ajoutée :**

```markdown
  - **Ordre des verrous :** toute opération qui modifie une Mission et son Signalement verrouille d'abord la ligne `missions` (`SELECT … FOR UPDATE`, ou l'`UPDATE` conditionnel), puis la ligne `reports`. Ce sont l'acceptation, la Preuve, l'annulation, l'expiration et l'assignation. Le contrôle de géorepérage de la Preuve a lieu **après** le verrou sur la Mission.
```

**Nouvel AD :**

```markdown
### AD-18 — Temps, horloge et tâches planifiées

- **Binds:** FR-7 (année du Numéro de suivi), FR-31 (Cohortes), FR-41, FR-42, §6.1 (durées de conservation), AD-6, AD-8.
- **Prevents:** des horodatages venus de deux horloges, des tests d'horloge simulée impossibles, et des tâches planifiées perdues.
- **Rule:**
  - **Horloge :** tout horodatage métier vient de `core.clock.now()`, en UTC avec fuseau. Il est passé en paramètre aux requêtes. Les valeurs par défaut de la base (`now()`) ne servent jamais aux décisions. Les tests figent `core.clock`.
  - **Tâches planifiées :** ce sont des **balayages cron arq** (expiration, purge de l'idempotence, durées de conservation, échantillon hebdomadaire de FR-41, relance de la classification). Ils sont idempotents et sélectionnent les lignes échues, par exemple `status = 'active' AND accepted_at + MISSION_TTL <= :now`. On n'utilise aucune tâche différée unitaire.
  - **Fuseau :** toutes les bornes de période (Cohorte, année, semaine) sont calculées en UTC, qui est aussi l'heure de Dakar (UTC+0, sans heure d'été). L'API reçoit et renvoie des instants ISO 8601 avec `Z`.
  - **Numéro de suivi :** l'année est celle de `received_at` (UTC). Le numéro vient de `INSERT INTO tracking_counters(year, n) VALUES (:y, 1) ON CONFLICT (year) DO UPDATE SET n = tracking_counters.n + 1 RETURNING n`, dans la transaction de création.
```

---

## T-15 — `is_demo`, `DEMO_MODE` et `ENV=demo` `[moyenne]`

**Unité A, `reports`.** Elle écrit `is_demo = settings.DEMO_MODE`.

**Unité B, `missions`.** Elle écrit `is_demo = (settings.ENV == "demo")`. Elle ne pose pas l'étiquette sur la Preuve, puisque AD-14 parle de « toute ligne » sans donner de liste.

**Unité C, `infra/seed`.** Elle crée des comptes de test et des Zones, avec `is_demo` sur `users` seulement.

**Unité D, `analytics`.** Elle ne filtre rien.

**Ce qui casse :**

- **Deux définitions** : avec `ENV=dev` et `DEMO_MODE=true`, ou avec `ENV=demo` et `DEMO_MODE=false`, les deux modules étiquettent différemment. Une Mission sans étiquette sur un Signalement étiqueté est possible.
- **Des chiffres de démo présentés comme réels** : au pilote, des Données de démonstration restées en place sont comptées dans les indicateurs, ce que §7 du PRD interdit (« Honnêteté »).
- **Un retrait du jeu de démo impossible** : la commande « en une commande » (FR-37) se heurte à `audit_logs`, qui ne se supprime pas, ou à des clés étrangères d'audit.
- **Des écrans sans étiquette** : la PWA ne sait pas quel élément porter l'étiquette « Données de démonstration », parce que `is_demo` n'est pas sérialisé.

**Correctif — AD-14, puce « Toute ligne créée en mode démo… » remplacée par :**

```markdown
  - **Source unique :** `DEMO_MODE` est la seule source. Il n'est permis que si `ENV ∈ {dev, demo}`, et `ENV=demo` l'exige. Aucun code ne teste `ENV` pour décider d'une étiquette.
  - **Tables étiquetées :** `is_demo BOOLEAN NOT NULL DEFAULT false` sur `users`, `reports`, `missions`, `proofs`, `proof_reviews`, `material_lots` et `lot_requests`. La valeur vient de `core.demo.flag(parent_is_demo=None)`, qui renvoie `DEMO_MODE or parent_is_demo` : une ligne enfant hérite de l'étiquette de son parent. Le seed écrit `true`.
  - **Exposition :** chaque schéma de réponse de ces entités expose `is_demo`. `GET /v1/config` expose `demo_mode`, pour le bandeau (FR-6).
  - **Analytique :** les vues exposent `is_demo`. Le Tableau de bord et les exports filtrent `is_demo = false` hors Mode démonstration. En Mode démonstration, ils incluent tout, avec l'étiquette.
  - **Retrait du jeu de démo :** `python -m app.cli demo purge` supprime les lignes `is_demo` dans l'ordre des clés étrangères. `audit_logs` n'a aucune clé étrangère vers les tables métier, et n'est jamais purgé.
```

---

## T-16 — Vues analytiques : propriétaire et cycle de vie `[moyenne]`

**Unité A, `reports`.** Elle renomme `reports.received_at` en `created_at` dans une migration Alembic (AD-15). La migration échoue (`cannot drop column … because other objects depend on it`). L'auteur ajoute alors `DROP VIEW … CASCADE`, et la vue disparaît.

**Unité B, `analytics`.** Elle a créé `v_report_facts` dans une **ancienne** migration. Elle ne la recrée pas. Pour « Collecteurs vérifiés actifs » (FR-31), elle joint `collector_profiles`, une table d'`auth`, alors que le graphe n'autorise les vues que sur `reports` et `missions`.

**Ce qui casse.** Le Tableau de bord renvoie une erreur 500 à la porte H60. Le contrat de colonnes des vues n'existe pas. Le graphe et la vue se contredisent sur `auth`.

**Correctif — nouvel AD :**

```markdown
### AD-22 — Vues analytiques

- **Binds:** AD-2, AD-15, FR-31 à FR-34, FR-41.
- **Prevents:** une vue cassée ou supprimée par la migration d'un autre module, et des indicateurs calculés sur des colonnes implicites.
- **Rule:**
  - **Propriété :** les vues `v_report_facts`, `v_mission_facts` et `v_collector_facts` appartiennent à `analytics`. Elles sont définies dans `backend/app/modules/analytics/views/*.sql`, avec une liste de colonnes déclarée (le contrat).
  - **Recréation :** toute migration qui modifie une table lue par une vue appelle `recreate_analytics_views()` à la fin. Ce helper fait `DROP VIEW` puis `CREATE VIEW` depuis les fichiers `.sql`. `CASCADE` est interdit.
  - **Contrôle en CI :** `alembic upgrade head`, puis une requête sur chaque vue avec son contrat de colonnes, sur le jeu de démonstration (le test des 60 % de FR-31 compris).
  - **Contenu :** les vues ne contiennent aucune donnée personnelle (ni `owner_key`, ni `author_user_id`, ni téléphone). Elles exposent `is_demo`.
```

**Graphe :** ajouter `analytics -.->|vues SQL en lecture| auth`, pour `v_collector_facts`.

---

## T-17 — Stockage : miniatures, empreintes, point d'accès et purge `[moyenne]`

**Unité A, la tâche `thumb` (AD-8).** Elle écrit `report/2026/11/<uuid>_thumb.jpg`, parce que `<kind>` n'a pas de valeur pour les miniatures. Ni la clé ni la ligne de la miniature ne sont enregistrées.

**Unité B, `reports` (FR-23, rejet « personne ou plaque »).** Elle supprime `report_photos.object_key` sous 24 h. La miniature reste, et elle est lisible par URL signée si quelqu'un a gardé la clé. C'est une fuite de données personnelles.

**Unité C, `missions` (FR-41, photo réutilisée).** Elle compare le SHA-256 du JPEG **ré-encodé**. `reports` (FR-8, doublon par photo) compare celui des octets **reçus**. Aucune correspondance n'est jamais trouvée.

**Unité D, `core/storage`.** Elle signe les URL avec `endpoint_url=http://garage:3900`, l'adresse interne de Compose. La PWA reçoit des URL injoignables, et la CSP (NFR-8) ne connaît pas l'hôte des photos.

**Unité E, `lots` (FR-38).** Aucun `<kind>` n'existe pour la photo de Lot.

**Correctif — AD-13, règle complétée :**

```markdown
  - **Clés :** `<kind> ∈ {report, report_thumb, before, after, lot}`. `<yyyy>/<mm>` est le mois UTC de réception. `<uuid>` est l'identifiant de la ligne photo. La ligne enregistre `object_key` **et** `thumb_key`.
  - **Écriture :** `core.storage.ingest_photo(bytes, kind) → {object_key, sha256, width, height}`. L'empreinte `sha256` porte sur les **octets reçus**, avant le ré-encodage. Elle est stockée dans la ligne de la photo (`report_photos.sha256`, `proofs.before_sha256` et `proofs.after_sha256`).
  - **Comparaisons :**
    - le Doublon probable par photo (FR-8) compare avec les photos de Signalement ;
    - FR-41 compare avec les photos de Signalement, via `reports.service.photo_seen(sha256)`, et avec les photos de Preuve.
  - **Suppression :** la suppression d'une photo supprime aussi sa miniature, via `core.db.after_commit` (AD-17). Un objet écrit dans une transaction annulée est supprimé par `after_rollback`. Un balayage quotidien supprime les objets sans ligne de plus de 24 h.
  - **Points d'accès :** il y en a deux. `S3_INTERNAL_ENDPOINT` sert aux écritures. `S3_PUBLIC_BASE_URL` sert à la signature des lectures, sur l'hôte des photos, qui est distinct de l'API (NFR-8) et déclaré dans la directive `img-src` de la CSP.
```

---

## T-18 — Entrée d'audit : forme, acteur et IP `[moyenne]`

**Unité A, `missions` (expiration, FR-42).** Elle appelle `core.audit.record(actor=None, …)` : il n'y a pas d'acteur humain.

**Unité B, `core/audit`.** Elle impose `actor_id UUID NOT NULL REFERENCES users`. Le retrait d'un Signalement par un appareil anonyme (FR-5) ne peut pas non plus être audité. Les actions sont des chaînes libres (`"validate"` contre `"report.validated"`), donc le test « une entrée par action de FR-36 » n'a pas de liste de référence.

**Unité C, la tâche de conservation (§6.1).** Elle efface l'IP des entrées de plus de 6 mois avec `UPDATE audit_logs SET ip = NULL`. Comme `teranga_app` n'a pas l'`UPDATE` (AD-15), la tâche échoue en production.

**Correctif — AD-15, règle complétée :**

```markdown
  - **Signature :** `core.audit.record(action: AuditAction, actor: Actor, object_type, object_id, before: dict | None, after: dict | None, ip: str | None)`.
    - `Actor(kind ∈ {user, device, system}, ref)`.
    - `AuditAction` est une énumération unique dans `core/audit/actions.py`, qui couvre la liste de FR-36. Le test de FR-36 itère sur cette énumération.
    - `before` et `after` ne contiennent que les champs modifiés, jamais de donnée personnelle.
  - **Aucune clé étrangère** de `audit_logs` vers les tables métier.
  - **IP :** elle est stockée à part, dans `audit_log_ips(audit_log_id, ip, created_at)`. `teranga_app` y a `INSERT` et `DELETE`, sans `UPDATE`. La tâche de conservation supprime les lignes de plus de 6 mois. `audit_logs` reste strictement en ajout seul.
```

---

## T-19 — File de classification bornée : personne ne relance `[moyenne]`

**Unité A, `reports` (création).** FR-14 dit que la file est bornée à 500 tâches. Quand elle est pleine, l'unité accepte le Signalement et ne met rien en file. C'est conforme : le Signalement reste « classification serveur en attente ».

**Unité B, `ai` et le worker.** Ils ne traitent que ce qui est en file.

**Ce qui casse.** Les Signalements reçus pendant la saturation ne sont **jamais** reclassés. FR-14 (« jusqu'à leur reclassement ») n'est pas tenu, et le drapeau Désaccord IA manque pour toujours. Une tâche `classify` qui échoue (Modèle en cours de chargement) ne peut pas être remise en file sous le même identifiant tant que son résultat est conservé.

**Correctif — AD-8, puces ajoutées :**

```markdown
  - `reports.classification_status ∈ {pending, done, failed}`. La création met la tâche en file seulement si la file compte moins de `CLASSIFY_QUEUE_MAX` tâches.
  - Le balayage cron `classify_sweep` (AD-18) remet en file, chaque minute, les Signalements `pending` de plus de 2 min, dans la limite de la place disponible. Il émet l'alerte de NFR-16 quand la file est pleine.
  - Les tâches `classify` sont déclarées avec `keep_result = 0`, et l'identifiant inclut la version du Modèle (voir T-11).
```

---

## T-20 — Contenu des tâches de notification `[moyenne]`

**Unité A, `reports`.** Elle met en file `notify(report_id, to_status)`.

**Unité B, `notifications`.** Pour envoyer « TC-2026-000123 rejeté : doublon » (FR-21), elle a besoin du Numéro de suivi, du motif et du destinataire. Le graphe ne l'autorise qu'à appeler `auth`, pas `reports`. Elle attend donc `notify(user_id, tracking_number, status, reason)`.

**Ce qui casse.** La tâche échoue sur ses arguments, ou `notifications` importe `reports.service`, et la CI casse (AD-1). Pour FR-40, `lots` n'a aucune flèche vers `notifications`.

**Correctif :** AD-21 (contenus autosuffisants définis dans `core/events.py`) et la flèche `lots -.-> notifications`, au trou T-13.

---

## T-21 — Retrait d'un Signalement anonyme (FR-5) `[moyenne]`

**Unité A, `reports`.** Elle implémente le retrait par une suppression de la ligne : il n'existe aucun Statut « retiré », et AD-3 interdit d'en inventer un.

**Unité B, `analytics`, avec l'audit.** La Cohorte a déjà compté le Signalement. L'entrée d'audit de création pointe vers un objet disparu. L'historique `report_status_events` (T-10) est supprimé, ou bloque la suppression par sa clé étrangère.

**Correctif — AD-3, puce ajoutée :**

```markdown
  - **Retrait (FR-5) :** `reports.service.withdraw(report_id, principal)` n'est permis qu'au propriétaire et qu'en `pending_review`. Ce n'est pas une transition. Il supprime, dans la même transaction, la ligne, ses photos (`after_commit`), ses Classifications et ses événements. Il écrit une entrée d'audit `report.withdrawn` (acteur `device` ou `user`). Un Signalement retiré n'appartient à aucune Cohorte.
```

---

## T-22 — Année du Numéro de suivi et compteur `[basse]`

**Unité A, `reports`.** Elle prend l'année de `datetime.now().year`. Le conteneur du pilote peut avoir un fuseau `Europe/Paris`, ce qui donne TC-2027 dès 23 h 00 UTC le 31 décembre. Elle incrémente le compteur par `SELECT n … FOR UPDATE` puis `UPDATE`, ce qui produit une course lors de la première création de l'année (la ligne n'existe pas encore).

**Unité B, `analytics`.** Elle borne les Cohortes en UTC, et un Signalement se retrouve compté dans l'année N-1 avec un numéro de l'année N.

**Correctif :** AD-18, au trou T-14 (année tirée de `received_at` en UTC, `INSERT … ON CONFLICT … RETURNING`). Comme Dakar est en UTC+0, le risque se limite à l'hébergement du pilote hors du Sénégal. La sévérité est basse, mais le test « deux créations simultanées » de FR-7 doit couvrir le 1er janvier.

---

## T-23 — Petits trous de plomberie `[basse]`

| Paire conforme mais incompatible | Correctif |
|---|---|
| `reports` renvoie `not_found` et `missions` renvoie `report_not_found` pour le même cas. L'outbox affiche `errors.<code>` d'après `fr.json`, et la clé manque. | **AD-11 :** les codes sont une énumération unique dans `core/errors/codes.py`, exportée dans l'OpenAPI. Un test CI exige une clé `errors.<code>` dans `fr.json` pour chaque code. |
| La PWA génère le client depuis `GET /openapi.json` sur le serveur de démo. Hors Mode démonstration, la route n'existe pas (NFR-7). Deux schémas `ReportOut`, dans `reports` et dans `missions`, entrent en collision dans `openapi-typescript`. | **AD-11 :** `backend/scripts/export_openapi.py` écrit `web/src/api/openapi.json` hors ligne. Le fichier et le client généré sont versionnés, et la CI échoue s'ils diffèrent d'une nouvelle génération. Les noms de schéma sont préfixés par le module (`ReportsReportOut`, `MissionsReportCard`). |
| AD-12 classe 408 en échec définitif, alors que FR-18 le réessaie. | **AD-12 :** « réseau, 408, 429 ou 5xx » (voir T-8). |
| AD-6 prescrit `ST_Contains` sur `geography` : la fonction n'existe pas pour ce type, et un développeur caste en `geometry` de façon incohérente. | **AD-6 :** l'appartenance se teste avec `ST_Covers(zone.geog, report.geog)` ; `zones.geog` est de type `GEOGRAPHY(MultiPolygon, 4326)`. |
| `infra` lance Valkey avec la configuration par défaut, sans persistance. Les limites de débit (FR-10, « survivent à un redémarrage ») et la file arq sont perdues au redémarrage. | **Squelette, infra :** Valkey avec `appendonly yes` et un volume persistant. `/readyz` le vérifie. |
| `infra` sert la PWA sur `app.…` et l'API sur `api.…` : le cookie `SameSite=Strict; Path=/v1/auth` fonctionne. Sur le portable de secours, servi par IP sur deux ports, il est bloqué, et le renouvellement échoue. | **AD-9 :** la PWA et l'API ont la **même origine** (Caddy sert `/v1/*` vers l'API et `/` vers les fichiers statiques). Seules les photos ont un hôte distinct (NFR-8). |
| La PWA vérifie hors ligne la Zone active « dès l'écran 2 » (FR-7). Or `core/geo` n'a pas de router, et aucune unité ne sert le polygone. | **AD-16 :** `GET /v1/config` est servi par `auth`, en route publique dans la liste blanche de NFR-9. Il renvoie `demo_mode` et le polygone simplifié de la Zone active. La PWA le met en précache. |

---

## Récapitulatif des modifications de l'épine

- **Nouveaux AD :**
  - AD-17 : unité de travail et effets après commit ;
  - AD-18 : temps, horloge et tâches planifiées ;
  - AD-19 : données de Classification, Corrections et drapeaux ;
  - AD-21 : réactions inter-modules et événements ;
  - AD-22 : vues analytiques.
  (AD-20 reste libre.)
- **AD resserrés :**
  - AD-2 : `corrections`, `report_status_events`, `idempotency_records` et `audit_log_ips` ;
  - AD-3 : point 3, ordre des verrous, historique, retrait ;
  - AD-5 : liste des routes, stockage en base, concurrence ;
  - AD-6 : `ST_Covers` ;
  - AD-7 : schéma du manifeste, logits, octets classés, version courante, seuil ;
  - AD-8 : identifiants de tâche, balayage de la classification ;
  - AD-9 : renouvellement à vol unique, révocation immédiate, format et principal de l'appareil, origine unique ;
  - AD-11 : photos en multipart, registre des codes d'erreur, export de l'OpenAPI ;
  - AD-12 : identité figée, 408, envoi dans la fenêtre seulement ;
  - AD-13 : clés, empreintes, points d'accès, purge ;
  - AD-14 : `DEMO_MODE` comme source unique, héritage de l'étiquette, exposition, retrait du jeu de démo, seuil de 60 % retiré ;
  - AD-15 : signature de l'audit, IP séparée ;
  - AD-16 : `GET /v1/config`.
- **Graphe :** flèches `lots -.-> notifications` et `analytics -.-> auth` (vue), et ajout de `reactions.py` comme racine de composition.
- **Conventions :** correspondance de toutes les énumérations (Type de déchet, Taille de tas, Poids déclaré, Revue de Preuve, Statut de Lot) ; convention « Transactions » réécrite selon AD-17.
