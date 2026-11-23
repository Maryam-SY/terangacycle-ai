---
type: review-rubric
target: ../ARCHITECTURE-SPINE.md
memlog: ../.memlog.md
prd: ../../../prds/prd-TerangaCycleAI-2026-11-23/prd.md
date: 2026-11-23
reviewer: rubric walker (BMAD)
---

# Revue par grille — Épine d'architecture TerangaCycle AI

## Verdict global

**À réviser avant le découpage en epics (pas un rejet).**

Le cœur métier est solide. Les machines à états (AD-3), l'acceptation exclusive (AD-4), l'autorité serveur (AD-6), le contrat du Modèle (AD-7), l'exposition des Positions (AD-10) et les conventions d'API (AD-11) fixent les bons points de divergence, avec des règles testables. Les 43 FR sont toutes rattachées à la carte des capacités.

L'épine laisse en revanche **muette une bonne partie de l'enveloppe opérationnelle** : supervision et alertes, gestion des secrets, publication et retour arrière, tâches planifiées et rétention. Elle **contredit NFR-10** sur l'épinglage. Plusieurs **mécanismes transverses** que trois personnes vont écrire en parallèle ne sont pas décidés : frontière transactionnelle entre services, limitation de débit, révocation, horloge, version du Modèle. Une règle est **fausse en l'état** : l'identifiant de tâche d'AD-8 fait perdre des notifications.

| Sévérité | Nombre |
|---|---|
| Critique | 0 |
| Haute | 10 |
| Moyenne | 11 |
| Basse | 11 |

## Jugement par point de la grille

| # | Point de la grille | Jugement | Justification (citations) |
|---|---|---|---|
| 1 | Fixe les vrais points de divergence pour le niveau inférieur (epics en parallèle à 3, puis pilote), sans en oublier | **adequate** | Forts : Statut (AD-3 l.99-122), Mission (AD-4 l.124-132), idempotence (AD-5), contrat IA (AD-7), API (AD-11), outbox (AD-12). Oubliés : frontière transactionnelle quand `missions.service` appelle `reports.service` (AD-4 l.130 contre la convention « Transactions » l.297) ; limitation de débit (FR-1, FR-10) ; révocation et suspension (FR-5, FR-35) ; version du Modèle entre client et serveur (FR-14) ; horloge simulée (FR-42, §6.1) ; port SMS (FR-1, FR-6) ; tâches planifiées (§6.1, FR-41). Voir F4 à F10, F15 à F17. |
| 2 | Chaque Rule est applicable et empêche réellement la divergence annoncée | **adequate** | La plupart des règles ont un garde-fou automatique : import-linter (AD-1 l.79), test exhaustif des transitions (AD-3 l.110), index partiel (AD-4), test doré (AD-7 l.171), test rôle × route (AD-9 l.196), démarrage refusé (AD-14 l.260), rôles PostgreSQL (AD-15). Défauts : AD-8 l.180 est **contre-productive** (F5) ; AD-5 l.144 vise des « POST sensibles » non énumérés, donc inapplicable (F13) ; AD-4 l.131 contredit FR-25 sur le rejeu (F13) ; AD-2 n'a pas de garde-fou automatique (seul AD-1 l'outille indirectement) ; AD-16 n'est vérifiable qu'en revue (pas de lint i18n ni de règle ESLint `no-restricted-globals: fetch`). |
| 3 | Rien dans « Différé » ne laisse deux unités diverger | **thin** | La l.453 affirme que le fournisseur SMS est « sans effet sur les invariants grâce à AD-13 et AD-14 ». C'est faux : AD-13 porte sur le stockage, et aucun port SMS n'est fixé (F17). « PostgreSQL managé ou auto-hébergé » est différé l.453, mais le schéma de déploiement l.366 le tranche déjà (« PostgreSQL managé »), d'où F12. Le choix des tuiles, différé l.457, conditionne la CSP (NFR-8) et le cache hors-ligne de la démo (NFR-7) : F18. Les autres reports (services, multi-commune, temps réel, orchestrateur, réentraînement) sont sans risque. |
| 4 | La technologie nommée est vérifiée et à jour | **adequate** | Contrôles du 23/11/2026 : FastAPI 0.165.0 (PyPI, dernière), arq 0.28.0 (PyPI, 16/04/2026), leaflet.heat 1.0.1 (npm, publiée le 13/11/2026, donc très récente), onnxruntime-web 1.31.1 (npm). Écarts : Node 24 n'est plus l'Active LTS, Node 26 « Lithium » l'est depuis octobre 2026 (F-L1) ; onnxruntime serveur 1.32 contre web 1.31 (F-L2) ; outils cités dans les AD mais absents du Stack : import-linter, openapi-typescript et son runtime, Gitleaks, Trivy, pip-audit (F-L3). Le marquage `[ASSUMPTION]` de Valkey et Garage est correct et repris au memlog (l.29-30). |
| 5 | Couvre les capacités du PRD (FR-1 à FR-43, NFR-1 à NFR-17) | **thin** | **FR : complet.** La carte l.432-446 couvre bien FR-1 à FR-43 (4.1 à 4.12, avec FR-41, FR-42 et FR-43 rangées à part). **NFR : insuffisant.** Le front matter déclare `binds: [..., NFR-1..NFR-17]` (l.11), mais la carte n'a qu'une ligne fourre-tout, « NFR sécurité et chaîne logicielle » (l.446). Sans réponse architecturale : NFR-3 (rendu de 5 000 points), NFR-5 (budget), NFR-7 (`/docs` masqué, tuiles hors-ligne), NFR-8 (domaine distinct pour les photos, CSP et WASM), NFR-11, NFR-15 (sauvegarde des photos hors hôte, exercice de restauration) et NFR-16 (alertes, rien du tout). Le §6.1 (rétention et tâche planifiée) et le §6.4 (plan de sortie, partiellement couvert par le schéma l.372) n'apparaissent pas dans la carte. Voir F1, F4, F12, F18, F21. |
| 6 | Chaque dimension de l'altitude est décidée, différée ou en question ouverte, enveloppe opérationnelle comprise | **thin** | Dimension par dimension, dans le tableau suivant. |
| 7 | Sobriété : des décisions, pas de justification ; pas de détail qui relève du code | **adequate** | L'épine est globalement sobre, et les justifications des AD sont bien au memlog. Il reste de la justification dans le Stack (« pas 7.0 : typescript-eslint exige… », l.327) et dans le Différé (« attendre une saturation CPU mesurée », « inutile pour un serveur unique », « encore en bêta », l.450-457). Détail de graine : la liste des fichiers par module (l.407) et la liste des `features/` (l.421) relèvent du code. L'ERD fixe une relation que le PRD n'exige pas (`MISSIONS ||--o{ MATERIAL_LOTS`, l.393). Voir F-L4, F-L8. |
| 8 | Les diagrammes Mermaid sont valides | **strong** | Les 5 blocs (flowchart des modules, stateDiagram-v2, flowchart des conteneurs, flowchart de déploiement, erDiagram) sont syntaxiquement valides : libellés entre guillemets, `<br/>`, cylindres `[(…)]`, arêtes étiquetées entre sous-graphes, cardinalités ER correctes. Remarques de fond, sans effet sur la validité : il manque des arêtes au graphe des modules (F20) ; le schéma d'états emploie un troisième nommage, `valide` ou `assigne`, au lieu de `validated` (F-L5) ; il n'y a pas de schéma pour la machine à états des Missions (acceptable, la table de transitions suffit) ; le sous-graphe « Pilote » omet Caddy et Valkey (F12). |

### Enveloppe opérationnelle (point 6)

| Dimension | État | Citation |
|---|---|---|
| Déploiement et environnements | **adequate** | Schéma l.358-373 et profils Compose (l.375). `ENV ∈ {dev, demo, prod}` (AD-14). Mais le pilote omet Caddy et Valkey (F12). |
| Stratégie d'infrastructure et de fournisseur | **adequate** | Portabilité par images et S3 (AD-13) ; région en question ouverte (PRD Q3, l.453) ; cible souveraine (l.369-372). Le pilote AWS de l'addendum (A, « Hébergement ») n'est pas nommé, ce qui est acceptable puisque c'est une question ouverte. |
| Sauvegardes | **thin** | Seulement « sauvegardes quotidiennes chiffrées » pour PostgreSQL (l.366). Les photos sont « versionnées », mais le versionnement n'est pas une copie hors hôte (NFR-15). Rien sur l'exercice de restauration, ni sur la persistance de Valkey. |
| Supervision et alertes | **broken (absent)** | Aucune mention. NFR-16 exige 4 alertes, dont 2 émises par le code (FR-1 : plafond SMS ; FR-14 : file pleine). |
| Gestion des secrets | **broken (absent)** | AD-14 ne dit que « variables d'environnement ». Rien sur les clés EdDSA et la rotation par `kid`, le pepper HMAC, la clé AES-GCM, les clés VAPID, les identifiants S3, ni sur le KMS du pilote (addendum, « Clés ») ou les « clés contrôlées par l'organisation » (NFR-17, §6.4). |
| CI/CD, publication et retour arrière | **thin** | La CI est citée (l.427), avec un épinglage **contraire à NFR-10** (l.376). Pas de registre d'images, de déclencheur de déploiement, de stratégie de retour arrière ni de règle de compatibilité des migrations (l'addendum prévoit pourtant « relancer le tag précédent »). |
| Observabilité | **thin** | Journaux `structlog` (conventions l.296, AD-10) et sondes (l.377). Aucune métrique (le taux de 5xx de NFR-16 n'est pas calculable) ni destination des journaux. |

### Applicabilité AD par AD (point 2)

| AD | Jugement | Note |
|---|---|---|
| AD-1 | strong | import-linter en CI. |
| AD-2 | adequate | Tableau clair, sans contrôle automatique ; il manque le magasin d'idempotence et l'historique des Statuts (F13, F14). |
| AD-3 | strong | Transition conditionnelle, audit dans la même transaction, test exhaustif. L'enfilement après commit n'est pas fiabilisé (F15). |
| AD-4 | adequate | Index partiel correct ; le rejeu par le même Collecteur n'est pas traité (F13). |
| AD-5 | thin | « POST sensibles » non énumérés ; stockage non désigné (F13). |
| AD-6 | strong | Colonnes `client_` et liste fermée. |
| AD-7 | adequate | Le test doré est excellent. Rien sur la coexistence des versions ni sur la distribution (F10). |
| AD-8 | broken (partiel) | La clé `<type>:<entity_id>` déduplique à tort (F5). Planification non couverte (F4). |
| AD-9 | adequate | Révocation, suspension et Second facteur absents (F8). |
| AD-10 | strong | Fonction unique `expose()` et tableau des niveaux. |
| AD-11 | strong | Client généré. Ajouter `/docs` désactivé hors démo (F18). |
| AD-12 | strong | Le statut 408 n'est pas traité (F-L6). |
| AD-13 | adequate | Domaine distinct pour les photos manquant (F18). |
| AD-14 | strong | Secrets hors périmètre (F2). |
| AD-15 | strong | Compatibilité des migrations avec le retour arrière manquante (F11). |
| AD-16 | adequate | Applicable seulement en revue ; WASM hébergé chez soi manquant (F18). |

## Constats

Format : **ID — sévérité — titre**, puis citation, problème et correctif prêt à coller (en Markdown, au style de l'épine).

### Haute

#### F1 — Haute — Supervision, alertes et métriques absentes (NFR-16, NFR-14)

- **Citation :** aucune occurrence de « alerte », « supervision » ou « métrique » dans l'épine. NFR-16 (PRD l.649) et FR-1 (« une alerte part sur le canal de l'équipe »), FR-14.
- **Problème :** deux modules émettent des alertes (`auth` pour le plafond SMS, `reports`/`ai` pour la file pleine). Sans canal ni API commune, chacun l'implémentera à sa façon. Le taux de 5xx n'est pas mesurable sans métriques.
- **Correctif à coller (nouvel AD) :**

```markdown
### AD-17 — Supervision et alertes

- **Binds:** NFR-14, NFR-16, FR-1, FR-14, NFR-15.
- **Prevents:** des alertes émises différemment par chaque module, et des seuils de NFR-16 non mesurables.
- **Rule:**
  - Seul `core.alerts.raise_alert(code, context)` envoie une alerte ; codes fermés : `sms_daily_cap_reached`, `classification_queue_full`, `http_5xx_rate`, `backup_failed`, `disk_usage_high`.
  - Canal unique : webhook de l'équipe (`ALERT_WEBHOOK_URL` dans `Settings`) ; anti-rafale d'une alerte par code et par 15 min (clé Valkey).
  - L'API expose `/metrics` (Prometheus, réseau interne seulement, jamais via Caddy) : compteurs de requêtes par statut, latence, profondeur de file arq.
  - Le taux de 5xx, le disque et les sauvegardes sont surveillés hors application : tâche arq `ops:health_sweep` toutes les minutes au hackathon ; supervision de l'hébergeur au pilote (question ouverte Q3).
  - Chaque alerte a un test de déclenchement simulé (NFR-16).
```

#### F2 — Haute — Gestion des secrets et des clés absente (NFR-17, §6.4)

- **Citation :** AD-14 l.259 : « Toute configuration passe par `core.config.Settings` (pydantic-settings, variables d'environnement). » AD-9 cite un `kid` (l.190) sans dire comment les clés tournent.
- **Problème :** les clés EdDSA, le pepper HMAC (téléphone, Identifiant d'appareil), la clé AES-GCM, les clés VAPID et les identifiants S3 n'ont ni source, ni format, ni rotation. Un changement de pepper ou de clé AES sans versionnement rend les données illisibles. Le PRD exige des clés contrôlées par l'organisation au pilote.
- **Correctif à coller :**

```markdown
### AD-18 — Secrets et clés

- **Binds:** NFR-10, NFR-17, §6.4 du PRD, AD-9, AD-10.
- **Prevents:** des secrets dans Git ou dans les images, et des données chiffrées devenues illisibles après une rotation.
- **Rule:**
  - Les secrets ne sont lus que par `core.config.Settings`, depuis des fichiers montés (`/run/secrets/*`, secrets Docker Compose), jamais depuis des variables commitées ou des couches d'image.
  - Hackathon : fichier `.env.secrets` hors Git. Pilote : secrets générés et chiffrés par le KMS de l'hébergeur, clés détenues par l'organisation.
  - Toute valeur chiffrée ou HMAC porte l'identifiant de sa clé (`key_id`) : `phone_enc = (key_id, nonce, ct)`, `phone_hmac_kid`. Une rotation ajoute une clé ; l'ancienne reste en lecture jusqu'à la ré-écriture des données.
  - JWT : clés EdDSA listées par `kid`, la plus récente signe, toutes vérifient ; rotation documentée dans `infra/`.
  - Le démarrage échoue si un secret requis manque, quel que soit `ENV` (sauf `dev`, qui génère des valeurs éphémères).
```

#### F3 — Haute — L'épinglage contredit NFR-10

- **Citation :** l.376 : « Les images et les actions GitHub sont épinglées par version. » NFR-10 (PRD l.643) : « images épinglées par empreinte et actions par SHA de commit ».
- **Problème :** la règle de l'épine produit une non-conformité directe à une NFR testée en CI.
- **Correctif à coller (remplace la l.376) :**

```markdown
- Images Docker épinglées par empreinte (`image@sha256:…`), actions GitHub par SHA de commit complet (avec la version en commentaire) ; Dependabot met à jour les deux. La CI échoue sur une image ou une action non épinglée.
```

#### F4 — Haute — Tâches planifiées et rétention (§6.1, FR-5, FR-23, FR-41, FR-42) non décidées

- **Citation :** AD-8 l.179 ne liste que « Classification serveur, miniatures, notifications et expiration des Missions ». Le §6.1 du PRD (l.679 : « Une tâche planifiée applique ces durées ») est absent de la carte des capacités.
- **Problème :** cinq traitements périodiques (purge à 24 h des photos « Personne ou plaque », purge à 30 jours des comptes supprimés, rétention à 12 mois et 6 mois, tirage hebdomadaire de FR-41, expiration à 48 h) n'ont ni mécanisme (cron de l'hôte ? arq cron ? report différé ?) ni propriétaire. Trois personnes, trois mécanismes.
- **Correctif à coller (ajout à AD-8) :**

```markdown
  - Les traitements périodiques sont des `cron_jobs` arq déclarés dans `worker.py`, idempotents et rejouables. Pas de cron d'hôte ni de report différé (`_defer_by`) pour une échéance métier.
    | Tâche | Fréquence | Propriétaire |
    |---|---|---|
    | `missions:expire_sweep` (FR-42) | 5 min | `missions` |
    | `reports:purge_rejected_photos` (FR-23, §6.1) | 1 h | `reports` |
    | `retention:sweep` (§6.1 : photos, IP d'audit) | 1 jour | `reports`, `missions`, `core/audit` |
    | `auth:purge_deleted_accounts` (FR-5) | 1 jour | `auth` |
    | `missions:weekly_proof_sample` (FR-41) | hebdomadaire | `missions` |
  - Les durées de §6.1 sont des réglages nommés (AD-14).
```

Ajouter aussi la ligne `§6.1 Rétention | tâches arq planifiées | AD-8, AD-14` à la carte des capacités.

#### F5 — Haute — L'identifiant de tâche d'AD-8 perd des notifications

- **Citation :** AD-8 l.180 : « Une tâche est identifiée par `<type>:<entity_id>` (identifiant de tâche arq), ce qui la rend idempotente. »
- **Problème :** arq refuse d'enfiler une tâche dont le `job_id` existe déjà, y compris tant que son résultat est conservé (`keep_result`, 1 h par défaut). Deux changements de Statut rapprochés (par exemple `validé` puis `assigné`) donnent le même `notify:<report_id>` : la seconde notification est silencieusement abandonnée, ce qui casse FR-21. Le même risque touche une re-classification légitime.
- **Correctif à coller (remplace la l.180) :**

```markdown
  - Le `job_id` arq identifie l'**événement**, pas l'entité : `<type>:<entity_id>:<event_id>`, où `event_id` est l'identifiant de l'entrée d'audit de la transition (notifications) ou la `model_version` (classification). L'effet de la tâche est lui-même idempotent (contrainte unique en base sur `(entity_id, event_id)` pour `notifications`).
```

#### F6 — Haute — Frontière transactionnelle entre services non décidée

- **Citation :** AD-4 l.130 : « La Mission est insérée, puis `reports.service.transition(validé → assigné)` est appelé, dans **une** transaction. » Conventions l.297 : « Une transaction par requête, ouverte par le service. »
- **Problème :** si chaque service ouvre sa transaction, l'appel de `missions` vers `reports` en ouvre deux, et l'atomicité d'AD-3 et AD-4 (Mission, Statut, audit) est perdue. Le porteur de `missions` et celui de `reports` trancheront différemment (session passée en paramètre, session de contexte, transaction imbriquée).
- **Correctif à coller (remplace la ligne « Transactions » des conventions) :**

```markdown
| Transactions | Une unité de travail par requête ou par tâche : la dépendance FastAPI `get_uow()` (ou l'entrée de la tâche arq) ouvre la session et valide une seule fois à la fin. Les services reçoivent `uow` en premier paramètre et le transmettent aux services appelés ; aucun service ni repository n'appelle `commit()` ou `begin()`. Les effets externes (tâches arq, S3) sont enregistrés via `uow.after_commit(...)`. |
```

#### F7 — Haute — Le graphe des modules interdit FR-5 (cycle `auth` ↔ `reports`)

- **Citation :** graphe l.51 : `reports -->|service| auth`. l.68 : « Toute autre dépendance entre modules est interdite, en particulier les cycles. » FR-5 : la suppression d'un compte supprime les Signalements en attente et anonymise les autres.
- **Problème :** `auth` doit agir sur les tables de `reports` (AD-2), mais `auth → reports` crée un cycle interdit. import-linter le refusera, et chacun contournera le problème (SQL direct, import tardif).
- **Correctif à coller (ajout à AD-1) :**

```markdown
  - La suppression de compte (FR-5) est orchestrée par une tâche arq `account:delete:<user_id>`, déclarée dans `worker.py`. Elle appelle dans l'ordre `reports.service.purge_author(user_id)`, `missions.service.purge_collector(user_id)` et `auth.service.erase_user(user_id)`. `worker.py` est le seul composant autorisé à composer plusieurs modules sans arête dans le graphe ; `auth` n'importe jamais `reports`.
```

#### F8 — Haute — Révocation, suspension et Second facteur absents d'AD-9

- **Citation :** AD-9 l.190 : JWT d'accès de 15 min. FR-35 : « La requête suivante d'un compte suspendu est refusée (401) » ; FR-5 de même ; FR-43 exige le Second facteur.
- **Problème :** un JWT sans état reste valable jusqu'à 15 min après une suspension ou une suppression, ce qui fait échouer le test de FR-35. L'addendum hésite entre « `is_active` vérifié à chaque requête » et « liste de révocation Redis ». La preuve du Second facteur (claim ou base) n'est pas fixée : `require_role` sera écrit de deux façons.
- **Correctif à coller (ajout à AD-9) :**

```markdown
  - **Révocation immédiate :** `require_role` lit `auth:user_state:<sub>` dans Valkey (TTL 15 min, repli en base) et refuse (401) un compte suspendu ou supprimé ; `auth.service` met cette clé à jour à chaque suspension, suppression ou changement de rôle.
  - **Second facteur :** le JWT du Personnel porte `amr: ["otp","totp"]` ; `require_role("moderator"|"admin")` exige `totp` dans `amr`, sinon 403 (FR-43). Avant le pilote, `require_staff_mfa` est désactivé par réglage (`STAFF_MFA_REQUIRED`).
```

#### F9 — Haute — Limitation de débit et proxy de confiance non décidés (FR-1, FR-10, S7)

- **Citation :** seule la mention « Valkey : OTP · limites » du schéma (l.346) en parle. FR-10 : « 11 requêtes portant 11 en-têtes `X-Forwarded-For` différents obtiennent un 429 à la 11e ».
- **Problème :** sans règle, les limites seront codées route par route, avec des algorithmes et des clés différents, et l'IP sera lue naïvement dans `X-Forwarded-For`, ce qui fait échouer le test de sécurité de FR-10.
- **Correctif à coller (nouvel AD) :**

```markdown
### AD-19 — Limitation de débit

- **Binds:** FR-1, FR-10, S7.
- **Prevents:** des limites codées différemment par route, et une IP falsifiable.
- **Rule:**
  - Seule la dépendance `core.ratelimit.limit(name)` limite ; fenêtre fixe dans Valkey, clé `rl:<name>:<dimension>:<valeur>:<fenêtre>` ; les plafonds sont des réglages nommés (AD-14).
  - L'IP client est `request.client.host` après le middleware proxy d'Uvicorn, avec `--forwarded-allow-ips` limité à l'adresse de Caddy ; Caddy **remplace** `X-Forwarded-For` (pas d'ajout). Aucun module ne lit `X-Forwarded-For` lui-même.
  - Le dépassement renvoie 429 `rate_limited` avec `Retry-After`.
```

#### F10 — Haute — Version du Modèle entre client et serveur, et distribution des artefacts

- **Citation :** AD-7 l.167-172. FR-14 : « Le serveur reclasse la même photo avec la même version du Modèle. » FR-16 : réentraînement mensuel au pilote.
- **Problème :** après un changement de Modèle, des PWA gardent l'ancienne version en cache. Le serveur reclasse alors avec une autre version, ce qui produit exactement les Désaccords IA artificiels qu'AD-7 veut empêcher, et viole FR-14. Rien ne dit non plus comment l'artefact produit dans `ml/` arrive dans l'image de l'API et dans le précache de la PWA. C'est le point de contact entre la personne ML et les deux autres.
- **Correctif à coller (ajout à AD-7) :**

```markdown
  - Les artefacts sont publiés comme assets d'une release GitHub `model-v<semver>` (empreinte SHA-256 dans le JSON) ; le build de l'API et celui de la PWA les téléchargent par version épinglée (`MODEL_VERSION` dans `Settings` et dans `web/.env`). Rien n'est commité dans Git.
  - Le serveur charge la version active **et** la précédente. La tâche de Classification serveur utilise la `client_model_version` du Signalement si elle est chargée ; sinon, elle classe avec la version active et **ne calcule pas** de Désaccord IA.
  - `GET /v1/model/manifest` donne la version active ; la PWA rafraîchit son précache quand elle diffère.
  - Le Modèle factice a la version `0.0.0-stub`, sélectionnée par `MODEL_VERSION`.
```

### Moyenne

#### F11 — Moyenne — Publication et retour arrière non décidés

- **Citation :** l.372 « mêmes images Docker » ; AD-15 l.274 « Les migrations tournent avant le démarrage ». L'addendum prévoit « retour arrière en relançant le tag précédent ».
- **Problème :** aucun registre, aucun déclencheur, aucune étiquette d'image. Surtout, un retour arrière par tag précédent n'est sûr que si les migrations restent compatibles avec la version N-1.
- **Correctif à coller (sous « Déploiement et environnements ») :**

```markdown
- La CI construit une seule image `ghcr.io/<org>/terangacycle-api:<sha>` (API et worker) et la PWA statique, sur `main` seulement ; le déploiement est `docker compose pull && docker compose up -d` avec `IMAGE_TAG=<sha>`, après un service `migrate` à usage unique (rôle `teranga_migrator`).
- Retour arrière : relancer avec le `IMAGE_TAG` précédent. Les migrations sont donc **expand/contract** : une migration ne supprime ni ne renomme une colonne encore lue par la version N-1 ; la suppression vient dans une version ultérieure.
```

#### F12 — Moyenne — Topologie du pilote incomplète, sauvegardes partielles, contradiction avec le Différé

- **Citation :** l.365-368 (pilote : « Conteneurs api + worker », « PostgreSQL managé », « Stockage S3 … versionné ») contre l.453 (« PostgreSQL managé ou auto-hébergé : questions ouvertes »). NFR-15 : sauvegarde hors hôte, photos comprises, et restauration testée.
- **Problème :** le pilote n'a ni Caddy (TLS, en-têtes NFR-8) ni Valkey (OTP, limites, file arq). Le choix « managé » est à la fois tranché et différé. Le versionnement S3 n'est pas une copie hors hôte, et la persistance de Valkey (OTP en cours, file arq) n'est pas fixée.
- **Correctif à coller :** remplacer `P1["Conteneurs api + worker"]` par `P1["Conteneurs caddy, api, worker, valkey (AOF)"]`, et `PostgreSQL managé + PostGIS` par `PostgreSQL + PostGIS (managé ou auto-hébergé, Q3)`. Puis ajouter :

```markdown
- Sauvegardes (pilote, NFR-15) : `pg_dump -Fc` quotidien chiffré (clé de l'organisation) et réplication quotidienne du bucket photos vers un second fournisseur ou une seconde région ; rétention de 30 jours ; échec signalé par `backup_failed` (AD-17) ; exercice de restauration complet sur un hôte vierge avant les données réelles, puis avant la fin du pilote (§6.4).
- Valkey : persistance AOF `everysec` ; sa perte n'entraîne aucune perte de données métier (seuls OTP et compteurs).
```

#### F13 — Moyenne — AD-5 et AD-4 : périmètre et stockage de l'Idempotency-Key indéfinis, conflit avec FR-25

- **Citation :** AD-5 l.144 « Preuves de collecte et autres POST sensibles … réponse conservée 24 h ». AD-4 l.131 « Une violation d'unicité est traduite en 409 `mission_already_taken` ». FR-25 : « Un renvoi de la même acceptation par le même Collecteur renvoie la Mission existante, sans erreur. »
- **Problème :** « POST sensibles » n'est pas une liste, donc la règle est inapplicable. Le lieu de stockage (Valkey volatil ou table) n'a pas de propriétaire au sens d'AD-2. Enfin, le rejeu de l'acceptation par le même Collecteur sans la même clé, par exemple après la fermeture de l'application, renvoie 409, contrairement à FR-25.
- **Correctif à coller :**

```markdown
  - `Idempotency-Key` est obligatoire sur : `POST /v1/missions` (acceptation), `POST /v1/missions/{id}/proof`, `POST /v1/missions/{id}/cancel`, `POST /v1/lots`, `POST /v1/lots/{id}/requests`. La liste vit dans `core/idempotency` et un test vérifie chaque route.
  - Stockage : table `idempotency_records` (propriétaire `core/idempotency`, purge par tâche planifiée après 24 h).
  - AD-4 : sur violation d'unicité, si la Mission `active` existante appartient au même Collecteur, réponse 200 avec cette Mission ; sinon 409 `mission_already_taken`.
```

#### F14 — Moyenne — La source de l'historique des Statuts n'est pas désignée (FR-31, FR-36)

- **Citation :** FR-31 « "Ayant atteint" se lit dans l'historique des Statuts » ; FR-36 « Le Personnel voit l'historique des Statuts » ; AD-2 l.97 (`v_report_facts`).
- **Problème :** `analytics` peut lire l'historique dans `audit_logs` (JSON avant/après) ou dans le Statut courant. Le Taux de traitement en dépend, et les deux lectures donnent des résultats différents.
- **Correctif à coller (AD-2) :** ajouter `report_status_history` et `mission_status_history` aux tables de `reports` et `missions`, écrites par `transition()` dans la même transaction. Puis : « `v_report_facts` expose `reached_validated_at`, `reached_collected_at`, calculés depuis `report_status_history` ; `audit_logs` n'est jamais une source d'indicateur. »

#### F15 — Moyenne — L'enfilement « après commit » n'est pas fiable

- **Citation :** AD-3 l.109 « la mise en file des notifications **après** le commit » ; AD-8.
- **Problème :** un crash ou une indisponibilité de Valkey entre le commit et l'enfilement perd la notification (FR-21 : au plus 1 min) ou la Classification serveur (FR-14), sans reprise.
- **Correctif à coller (AD-8) :** « Toute tâche déclenchée par une écriture est d'abord une ligne `outbox_events` dans la même transaction. La tâche planifiée `events:dispatch` (toutes les 10 s) enfile les lignes non envoyées ; le `job_id` est l'`id` de la ligne. Le classement de FR-14 lit `classification_status = pending` pour reprendre après une file pleine. »

#### F16 — Moyenne — Pas d'horloge injectable

- **Citation :** FR-42 (« Test avec une horloge simulée ») et §6.1 (même exigence) ; aucune mention dans l'épine.
- **Problème :** sans convention, chacun appellera `datetime.now()` ou `now()` en SQL, et les tests d'expiration et de rétention seront impossibles ou divergents.
- **Correctif à coller (conventions) :** `| Temps | Tout « maintenant » vient de core.clock.now() (UTC) ; les requêtes SQL reçoivent :now en paramètre, jamais NOW() pour une règle métier ; les tests figent l'horloge avec une fixture. |`

#### F17 — Moyenne — Pas de port SMS ; le Différé l.453 se justifie à tort

- **Citation :** l.453 « Fournisseur SMS … sans effet sur les invariants grâce à AD-13 et AD-14 ». FR-6 : le Mode démonstration affiche le code OTP.
- **Problème :** AD-13 ne concerne que le stockage. Sans adaptateur, la personne qui porte `auth` codera l'affichage démo directement dans le service, et le branchement de la passerelle au pilote touchera la logique métier.
- **Correctif à coller :** ajouter à AD-14 « Seul `core/sms.SmsSender` envoie un SMS ; implémentations `DemoSmsSender` (code renvoyé dans la réponse si `DEMO_MODE`) et `GatewaySmsSender` (pilote), sélectionnées par `SMS_BACKEND`. Le plafond quotidien (FR-1) est vérifié dans le port. » Corriger la l.453 en « … sans effet sur les invariants grâce au port `core/sms` (AD-14), à AD-13 et à AD-15 ».

#### F18 — Moyenne — NFR-8 et NFR-7 sans traduction architecturale

- **Citation :** Caddy « TLS · en-têtes · statiques » (l.343) ; AD-13 ; AD-16 l.284. NFR-8 : « photos servies depuis un domaine distinct de l'API », CSP `script-src 'self' 'wasm-unsafe-eval'`. NFR-7 : `/docs` et `/openapi.json` non exposés hors démo.
- **Problème :** onnxruntime-web charge par défaut ses fichiers WASM depuis un CDN, ce qui est bloqué par la CSP ou viole la règle si la CSP est assouplie. Le domaine des URL signées n'est pas fixé. L'exposition de `/docs` n'est pas réglée.
- **Correctif à coller :**

```markdown
- AD-13 : les URL signées pointent vers `media.<domaine>` (Caddy en proxy inverse vers le stockage), jamais vers le domaine de l'API.
- AD-16 : les fichiers `.wasm` d'onnxruntime-web sont servis par la PWA (`ort.env.wasm.wasmPaths = "/ort/"`) et précachés ; aucun CDN.
- Caddy : un seul bloc d'en-têtes (HSTS, CSP `script-src 'self' 'wasm-unsafe-eval'`, `nosniff`, `Referrer-Policy: no-referrer`) ; CORS limité à `PWA_ORIGIN`.
- AD-11 : `docs_url` et `openapi_url` valent `None` sauf si `ENV ∈ {dev, demo}` ; le client TypeScript est généré depuis `app.openapi()` à la construction, pas depuis une URL.
```

#### F19 — Moyenne — Le calcul de l'empreinte de photo n'est pas fixé (FR-8, FR-41)

- **Citation :** FR-8 « photo strictement identique » (Doublon probable) ; FR-41 « photo strictement identique … (Signalement ou Preuve) ».
- **Problème :** `reports` et `missions` comparent les photos entre modules. Si l'un hache les octets reçus et l'autre le JPEG ré-encodé, la détection croisée échoue.
- **Correctif à coller (AD-13) :** « `core/storage.put_photo()` renvoie `(object_key, sha256)`, où `sha256` est calculé sur les octets **reçus**, avant le ré-encodage ; il est stocké dans `report_photos.sha256` et `proofs.*_sha256` (index), et la recherche croisée passe par `reports.service.find_photo_by_hash()`. »

#### F20 — Moyenne — Le graphe des modules est incomplet, alors qu'import-linter le fait respecter

- **Citation :** graphe l.36-66 et AD-1 l.79.
- **Problème :** FR-40 (le Collecteur est notifié de la réservation d'un Lot) n'a pas d'arête `lots ⇢ notifications`. FR-31 (Collecteurs vérifiés actifs) exige les profils de `auth`, sans arête `analytics ⇢ auth`. `missions` doit lire les Signalements proches (FR-24) : l'arête existe. Les flèches pleines vers `core` sont décrites comme des « appels de service », ce qui est ambigu. La CI bloquera des stories légitimes, ou poussera à des contournements.
- **Correctif à coller :** ajouter `lots -.->|tâche arq| notifications` et `analytics -.->|vues SQL en lecture| auth` ; écrire `auth -.-> core` (et de même pour tous les modules) en pointillé, avec la légende « pointillés vers `core` : dépendance technique ».

#### F21 — Moyenne — La carte des capacités ne couvre pas les NFR ni le §6

- **Citation :** front matter `binds: [FR-1..FR-43, NFR-1..NFR-17]` (l.11) ; carte l.446 (une seule ligne générique).
- **Problème :** les epics ne savent pas quelle AD porte quelle NFR, et plusieurs NFR (3, 5, 7, 8, 11, 15, 16) n'ont aucun porteur.
- **Correctif à coller (lignes à ajouter à la carte) :**

```markdown
| NFR-1, NFR-5 (Modèle et budget) | `web/features/classify`, `ml/` | AD-7, AD-16 |
| NFR-2 (lecture API) | `core/db`, index | AD-8, AD-11 |
| NFR-3 (carte 5 000 points) | `analytics` (agrégation serveur), `web/features/dashboard` | AD-10 |
| NFR-4 (photo ≤ 300 Ko) | `web/offline` | AD-12 |
| NFR-7, NFR-8 (sondes, en-têtes) | Caddy, `main.py` | AD-11, AD-13, AD-16 |
| NFR-9 (contrôle d'accès) | `tests/authz` | AD-9 |
| NFR-10, NFR-11 (chaîne logicielle, qualité) | CI | AD-18, Stack |
| NFR-12, NFR-13 (accessibilité, langue) | `web/theme`, `web/i18n` | AD-16 |
| NFR-14, NFR-16 (journaux, alertes) | `core/logging`, `core/alerts` | AD-17 |
| NFR-15, §6.4 (sauvegarde, sortie) | `infra/` | Déploiement |
| NFR-17 (données au repos) | `core/security`, base | AD-15, AD-18 |
| §6.1 (rétention) | tâches planifiées | AD-8 |
```

### Basse

| ID | Constat | Correctif prêt à coller |
|---|---|---|
| F-L1 | Stack l.324 : « Node.js 24 LTS ». Au 23/11/2026, Node 26 (« Lithium ») est l'Active LTS (v26.13.1 du 10/11/2026) ; Node 24 est en maintenance. | `\| Node.js (outillage) \| 26 LTS \|`, ou garder 24 avec la mention « LTS de maintenance, choix délibéré » au memlog. |
| F-L2 | onnxruntime 1.32 (serveur) contre onnxruntime-web 1.31 (navigateur). Le test doré d'AD-7 couvre le risque, mais l'écart n'est pas assumé. | Ajouter au memlog : « écart 1.32 / 1.31 accepté, verrouillé par le test doré AD-7 » ; ou aligner sur la même mineure dès qu'onnxruntime-web 1.32 sort. |
| F-L3 | Outils cités dans les AD mais absents du Stack : import-linter (AD-1), openapi-typescript et son runtime `openapi-fetch` (AD-11), Gitleaks, Trivy, pip-audit (NFR-10), ruff, ESLint, typescript-eslint, uv. | Ajouter ces lignes au tableau Stack avec leur version vérifiée. |
| F-L4 | Justification dans l'épine : l.327 « (pas 7.0 : typescript-eslint exige… ) » ; Différé l.450-457 (« attendre une saturation CPU mesurée », « inutile pour un serveur unique », « encore en bêta »). | Ne garder que la décision (« TypeScript 6.0.3 », « Orchestrateur : différé », « Carte : Leaflet 1.9.4 au MVP ; revue au pilote ») et déplacer les raisons au `.memlog.md`. |
| F-L5 | Trois nommages des Statuts : le schéma d'états (`valide`, `assigne`, `collecte`), AD-3 l.130 (`validé → assigné`) et les conventions l.290 (`validated`, `assigned`). | Renommer les états du `stateDiagram-v2` avec les valeurs de base (`pending_review`, `validated`, `rejected`, `assigned`, `collected`) et écrire `transition(validated → assigned)` dans AD-4. |
| F-L6 | AD-12 l.237 réessaie sur « erreur réseau, 429 ou 5xx », alors que FR-18 traite aussi 408 comme temporaire. | « … uniquement sur erreur réseau, 408, 429 ou 5xx. » |
| F-L7 | Le tag `[ADOPTED]` ne figure que sur AD-1, AD-4 et AD-11 : le statut des 13 autres AD est ambigu. | Marquer chaque AD (`[ADOPTED]` ou `[PROPOSED]`), ou retirer le tag et s'appuyer sur `status: draft`. |
| F-L8 | L'ERD l.393 `MISSIONS \|\|--o{ MATERIAL_LOTS : produit` fixe un lien que FR-38 n'exige pas (un Lot a une Zone, un Collecteur et une photo). Les listes de fichiers par module (l.407) et de `features/` (l.421) relèvent du code. | `USERS \|\|--o{ MATERIAL_LOTS : declare` et `ZONES \|\|--o{ MATERIAL_LOTS : situe` ; réduire l'arborescence aux dossiers de premier niveau. |
| F-L9 | Le front matter dit `altitude: feature`, mais `scope: 'Système complet …'`, ce qui est incohérent pour une épine de niveau système. | `altitude: system` (et de même dans le memlog), ou justifier « feature » au memlog. |
| F-L10 | AD-14 `ENV ∈ {dev, demo, prod}` contre l'addendum (`ENV=production` dans `.env.example`). | Fixer `prod` et ajouter au memlog : « l'addendum (`production`) est remplacé par `prod` ». |
| F-L11 | AD-13 et AD-15 lient NFR-10 (chaîne logicielle) sans rapport ; NFR-17 est le bon lien pour AD-13. | AD-13 **Binds:** FR-8, FR-29, NFR-8, NFR-17. AD-15 **Binds:** NFR-17, FR-36. |

## Remarques sur le memlog

- Le memlog trace bien les 16 AD, les versions et les deux `[ASSUMPTION]` (Garage, Valkey).
- Il manque une trace pour les décisions de l'épine qui n'y figurent pas : topologie de déploiement (PostgreSQL « managé »), sondes `/healthz` et `/readyz`, compteur `tracking_counters`, alors que l'addendum (point 3) demandait une séquence PostgreSQL par année. Il faut une ligne `(decision)` pour chacune, l'écart à l'addendum inclus.
- La justification déplacée par F-L4 doit y être ajoutée.
