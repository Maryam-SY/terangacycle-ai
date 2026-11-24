# Validation finale BMAD (étape 4) — epics.md

Date : 2026-11-23. Document validé : `_bmad-output/planning-artifacts/epics.md` (9 epics, 92 stories, frontmatter `status: draft`).
Sources de contrôle : `steps/step-04-final-validation.md`, PRD (`prd.md` §4), épine (`ARCHITECTURE-SPINE.md`), addendum. La section « Règles de cohérence entre epics » a été appliquée comme prioritaire sur les mentions « créé s'il n'existe pas » des stories.

Ordre des portes appliqué : **H24 < H48 (opt. H48) < H60 < pilote < extension**. Une story ne peut dépendre que d'une story de numéro inférieur **et** de porte inférieure ou égale.

Sévérités : **bloquant** = un critère d'une story ne peut pas être satisfait quand on l'implémente à sa place et à sa porte, ou une migration échoue ; **à corriger** = incohérence ou manque qui produira une erreur d'implémentation ou de CI sans empêcher l'ordre ; **mineur** = précision, doublon ou formulation.

## Synthèse

| Contrôle | Verdict | Bloquant | À corriger | Mineur |
|---|---|---|---|---|
| 1. Couverture FR | ÉCHEC | 1 | 6 | 3 |
| 2. Architecture | ÉCHEC | 1 | 4 | 0 |
| 3. Qualité des stories | ÉCHEC | 0 | 2 | 4 |
| 4. Structure des epics | ÉCHEC | 0 | 2 | 2 |
| 5. Dépendances | ÉCHEC | 9 | 3 | 2 |
| **Total** | | **11** | **17** | **11** |

`epics.md` doit rester `status: draft` : 5 contrôles ouverts.

---

## 1. Couverture FR — ÉCHEC

### 1.1 Tableau des 43 FR

Légende : ✅ toutes les conséquences testables du PRD sont portées par des critères ; ⚠️ conséquence manquante ou portée trop tard (voir point).

| FR | Stories porteuses | Couverture |
|---|---|---|
| FR-1 | 2.2, 2.3 | ✅ (expiration 5 min, usage unique, 5 essais, haché, 3 portées 429, plafond 503 + alerte, +221) |
| FR-2 | 2.3, 2.4 | ✅ (30 j, ≤ 15 min, rotation/réutilisation, déconnexion, stockage navigateur, 5 cas 401) |
| FR-3 | 2.5 (+1.7, 2.8, 2.9, 4.1, 4.6, 5.1) | ✅ |
| FR-4 | 1.3, 1.6, 1.11, 2.8, 3.15, 6.1 | ⚠️ point 1-D (acceptation horodatée pour un compte) |
| FR-5 | 2.8, 2.9, 2.10, 4.8 | ⚠️ point 1-H (compte Collecteur supprimé avec Mission `active`) |
| FR-6 | 1.1, 2.1, 2.2 | ✅ |
| FR-7 | 1.4, 1.5, 1.6, 1.8 | ✅ (la table de conversion « livrée avec FR-7 », PRD §11 Q6, est traitée en 1-A) |
| FR-8 | 1.5, 1.6, 1.9 | ✅ |
| FR-9 | 1.7, 1.8, 6.2 | ✅ |
| FR-10 | 1.10 | ✅ |
| FR-11 | 3.6, 3.8, 3.9, 3.12, 8.2 | ✅ |
| FR-12 | 3.1, 3.12 | ✅ (tests 59 % / 60 %) |
| FR-13 | 3.11, 3.12, 4.3, 3.15 | ⚠️ point 1-E (auteur de la Correction) |
| FR-14 | 3.3, 3.11, 3.13, 3.14 | ✅ |
| FR-15 | 3.14, 4.1 | ✅ |
| FR-16 | 3.1 à 3.7, 3.16, 3.17 | ✅ |
| FR-17 | 6.1 | ✅ |
| FR-18 | 6.2 | ✅ |
| FR-19 | 6.3 | ✅ |
| FR-20 | 4.6 (+1.3, 6.1) | ✅ |
| FR-21 | 4.7, 4.8 | ✅ |
| FR-22 | 4.1 | ✅ (miniature : voir 5-H) |
| FR-23 | 4.2, 4.3, 4.4, 4.5, 4.6 | ✅ |
| FR-24 | 5.1, 5.2, 5.3 | ⚠️ **point 1-A bloquant** (Poids estimé jamais défini ni calculé) |
| FR-25 | 5.3, 5.4 | ✅ |
| FR-26 | 5.5 | ✅ |
| FR-27 | 5.8 | ✅ |
| FR-28 | 5.9 | ⚠️ point 1-F (« qui en est notifié ») |
| FR-29 | 5.6, 5.7 | ✅ |
| FR-30 | 5.10, 5.13, 5.14 | ✅ |
| FR-31 | 7.1, 7.2, 7.3 | ✅ (mais critère « contestée » de 7.2 hors porte : 5-G) |
| FR-32 | 7.4 | ✅ (tuiles : 5-E) |
| FR-33 | 7.5 | ✅ |
| FR-34 | 7.6 | ⚠️ point 1-G (« tant que FR-34 n'est pas livrée ») |
| FR-35 | 2.11 | ✅ |
| FR-36 | 2.6, 2.7, 2.9, 2.10, 2.11, 2.12, 3.15, 4.2, 4.3, 4.4, 5.3, 5.5, 5.9, 5.11, 5.13, 7.5 | ⚠️ point 1-C (« un test par action » non soldé) |
| FR-37 | 1.6, 1.8, 1.12, 2.5, 5.3, 5.6 + étiquettes | ⚠️ point 1-B (Signalements à divers Statuts, Missions, Preuves) |
| FR-38 | 9.1, 9.2 | ✅ |
| FR-39 | 9.3, 9.4 | ✅ |
| FR-40 | 9.5 | ⚠️ point 1-F (« le Collecteur est notifié ») |
| FR-41 | 5.12, 5.13, 5.14, 7.7 | ✅ |
| FR-42 | 5.11 | ✅ |
| FR-43 | 2.12 | ✅ |

Les 43 FR apparaissent dans au moins une story ; aucune FR n'est orpheline. Les manques portent sur des conséquences.

### 1.2 Points

**1-A — bloquant — FR-24 : le Poids estimé n'est produit par aucune story.**
Preuve : le glossaire du PRD (l. 123) le définit comme « déduit de la Taille de tas et du Type de déchet par une table de conversion » ; l'épine (AD-2) donne la table `weight_estimates` au module `reports`. Aucune story ne crée cette table ni ne définit le calcul, alors que 5.1 (« le Poids estimé »), 5.2 (« ≈ 15 kg »), 5.3, 5.4, 7.1 (`v_report_facts` « le Poids estimé ») et 7.5 le renvoient.
Correction : ajouter à la **story 5.1** (première consommatrice, porte H48) le critère :
> **Étant donné** une base sans table `weight_estimates`
> **Quand** la migration de cette story s'applique
> **Alors** elle crée seulement `weight_estimates` (propriétaire `reports` ; `heap_size` ∈ {small, medium, large}, `waste_type` ∈ `WasteType`, `kg NUMERIC(6,1) > 0`, unicité `(heap_size, waste_type)`), chargée depuis un fichier versionné de valeurs provisoires `[ASSUMPTION, PRD §11 Q6]`
> **Et** `reports.service.estimated_weight(report)` renvoie le kg de `(heap_size, retained_type)` ; la table couvre les 15 couples (test).

Ajouter dans la section de cohérence la ligne : `| Table weight_estimates, estimated_weight() | 5.1 | 5.2, 5.3, 7.1, 7.5 |`.

**1-B — à corriger — FR-37 : « Signalements à divers Statuts » non porté.**
Preuve : la règle de cohérence annonce « 4.2 ajoute les Signalements `validé` et `rejeté`, 5.3 et 5.6 les Missions et les Preuves », mais aucun critère de 4.2, 5.3 ou 5.6 ne le dit ; 1.12 ne charge que des `en attente de modération`. Or 7.2, 8.3, 8.6 (« boucle SM-1 ») supposent ce jeu.
Correction : ajouter un critère identique dans **4.4** (après le rejet, pour disposer de `validé` et `rejeté`), **5.3** et **5.6** :
> **Étant donné** la commande `python -m app.cli demo load`
> **Quand** elle s'exécute après les chargements des modules précédents
> **Alors** le service de ce module ajoute ses Données de démonstration par ses propres règles (4.4 : au moins 5 Signalements `validé` avec Type retenu et 3 `rejeté` dont un `duplicate` ; 5.3 : au moins 2 Missions `active` et 2 `completed` ; 5.6 : une Preuve pour chaque Mission `completed`), toutes `is_demo = true`
> **Et** `demo purge` les retire, et un second `demo load` ne les duplique pas.

Et remplacer dans la règle de cohérence « 4.2 les Signalements `validé` et `rejeté` » par « 4.4 les Signalements `validé` et `rejeté` ».

**1-C — à corriger — FR-36 « pour chaque action, un test » : le méta-test de 2.6 cassera la CI.**
Preuve : 2.6 fait échouer la CI « si une valeur en attente a déjà son test ». Seules 2.11, 2.12, 4.2 et 4.3 retirent leur action de `PENDING_AUDIT_ACTIONS`. Les stories suivantes écrivent une action auditée sans ce critère : 2.9 (`report.withdrawn`), 2.10 (`account.delete`), 3.15 (`export.corrections`), 5.5 (`mission.transition`), 5.9 (`mission.assign`), 5.13 (`proof.review`), 7.5 (`export.aggregate`).
Correction : ajouter à chacune de ces 7 stories :
> **Étant donné** le méta-test du Journal d'audit (story 2.6)
> **Quand** la CI s'exécute
> **Alors** `<action>` a son test et n'est plus dans `PENDING_AUDIT_ACTIONS`.

**1-D — à corriger — FR-4 « l'acceptation est horodatée pour un compte ».**
Preuve : 1.3 mémorise l'acceptation dans Dexie (anonyme) ; 2.8 n'horodate que `training_consent` ; aucune story n'enregistre côté serveur l'acceptation des conditions (date, version du texte) d'un compte.
Correction : dans **2.8**, compléter la migration (« `users` gagne … `terms_accepted_at`, `terms_version` ») et ajouter :
> **Étant donné** un Citoyen connecté qui envoie `consent.terms = true` avec une version de texte
> **Quand** le serveur accepte le Signalement
> **Alors** `users.terms_accepted_at = core.clock.now()` et `terms_version` sont enregistrés s'ils sont absents ou si la version a changé, et `GET /v1/me` les renvoie.

**1-E — mineur — FR-13 « chaque Correction est enregistrée avec … son auteur ».**
Preuve : `corrections(report_id, actor_kind, …)` (3.11) n'a que la nature de l'acteur ; l'identité du Modérateur n'est que dans l'entrée `report.correction` du Journal (4.3).
Correction : dans 3.11, ajouter la colonne `actor_ref` (identifiant du Modérateur ; `NULL` pour le Citoyen, dont l'auteur est le Signalement) et, dans 4.3, l'écrire ; préciser que 3.15 ne l'exporte pas.

**1-F — mineur — FR-28 « qui en est notifié » et FR-40 « le Collecteur est notifié ».**
Preuve : 5.9 émet `MissionAssigned` et 9.5 `LotReserved` sans réaction ; la « notification » se réduit au rafraîchissement de 15 s.
Correction : écrire explicitement dans 5.9 et 9.5 « la notification au MVP est l'apparition dans la liste en ≤ 15 s (rafraîchissement) ; aucune réaction n'est abonnée à l'événement », ou ajouter une réaction push au Collecteur dans `reactions.py`.

**1-G — mineur — FR-34 « tant que FR-34 n'est pas livrée, aucune carte n'est accessible sans connexion ».**
Preuve : seule 7.6 (Should) le teste. Si 7.6 n'est pas livrée, rien ne le garantit.
Correction : ajouter à **2.5** : « **Et** le test route × rôle sans jeton vérifie qu'aucune route renvoyant des coordonnées de Signalement n'est accessible sans jeton, hors `GET /v1/public/map`. »

**1-H — à corriger — FR-5 / AD-21 : suppression d'un compte Collecteur qui a une Mission `active`.**
Preuve : l'épine (AD-21) impose `AccountDeleted` → `missions.service.on_collector_deleted()` (« Mission `active` annulée ») puis `detach_owner` ; 2.10 renvoie à « l'epic des Missions » mais aucune story de l'Epic 5 ne l'implémente.
Correction : ajouter à **5.5** :
> **Étant donné** un Collecteur qui a une Mission `active` et supprime son compte (story 2.10)
> **Quand** la réaction `AccountDeleted` s'exécute
> **Alors** `missions.service.on_collector_deleted(user_id)` annule sa Mission (`mission.transition`, acteur `system:account_deleted`), le Signalement revient à `validé`, puis `detach_owner` s'exécute, dans cet ordre dans `reactions.py`
> **Et** rejouer la réaction ne change rien.

**1-I — à corriger (hors FR, NFR-10) — analyse de vulnérabilités absente.**
Preuve : NFR-10 exige l'échec de la CI « sur toute vulnérabilité critique ou haute non justifiée dans un fichier d'exceptions daté (pip-audit, npm audit, Trivy) ». La règle de cohérence le confie à 8.5, mais aucun critère de 8.5 ne le porte (8.10 n'utilise Trivy que pour les secrets).
Correction : ajouter à **8.5** :
> **Étant donné** pip-audit, npm audit et Trivy (image API) en CI
> **Quand** une vulnérabilité critique ou haute est détectée
> **Alors** la CI échoue, sauf si elle figure dans `security/exceptions.yaml` avec justification et date d'expiration non dépassée (test négatif avec une exception échue).

**1-J — à corriger (hors FR, NFR-6.1c) — durées de conservation des photos non appliquées.**
Preuve : seules les purges d'IP (2.6), de comptes (2.10), de photos « personne ou plaque » (4.5) et des `idempotency_records` (1.11) existent. Rien ne supprime les photos de Signalement après 12 mois, les photos de `rejeté` après 30 jours ni les photos de Preuve après 12 mois, alors que NFR-6.1c exige « test à horloge simulée : photo échue supprimée et lien inopérant ».
Correction : ajouter à **4.5** (porte H48) :
> **Étant donné** `retention.sweep` et une horloge simulée
> **Quand** la tâche s'exécute
> **Alors** les photos (et miniatures) de Signalements `rejeté` depuis plus de `REJECTED_PHOTO_RETENTION_DAYS` (30) et de Signalements reçus depuis plus de `REPORT_PHOTO_RETENTION_DAYS` (365) sont purgées, l'ancienne URL signée ne fonctionne plus, et la purge est inscrite par lot (`retention.purge`).

Et ajouter le même critère pour les photos de Preuve (365 j) à **5.6**.

---

## 2. Architecture — ÉCHEC

### 2.1 Story 1.1 et squelette — OK

1.1 crée le squelette sans starter full-stack ni SQLModel (« écrits à la main sans starter full-stack ni SQLModel ») et `web/` par « `create-vite` (template `react-ts`) avec `vite-plugin-pwa` », conformément à AR-1 et à la décision de l'épine. Les versions de la Stack sont épinglées avec fichiers de verrouillage.

### 2.2 Création des tables — inventaire

| Table | Story qui la crée | Remarque |
|---|---|---|
| `zones` | 1.4 | OK |
| `devices`, `reports`, `report_photos`, `tracking_counters` | 1.6 | OK |
| `idempotency_records` | 1.11 | OK |
| `users` | 2.3 | OK (voir 5-I pour `display_name`) |
| `refresh_tokens` | 2.4 | OK |
| `collector_profiles` | 2.5 | OK |
| `audit_logs`, `audit_log_ips` | 2.6 | OK |
| `staff_second_factors` | 2.12 | OK |
| `corrections` | 3.11 **et** 4.3 (« créée par cette story … si elle n'existe pas ») | point 2-B |
| `classifications` | 3.13 | OK |
| `report_status_events` | 4.2 | utilisée avant par 3.15 : point 5-C |
| `notifications`, `push_subscriptions` | 4.8 | OK |
| `missions` | 5.3 | OK |
| `proofs` | 5.6 | OK |
| `proof_reviews` | 5.13 | utilisée avant par le critère « contestée » de 7.2 : point 5-G |
| `material_lots` | 9.1 | OK |
| `lot_requests` | 9.4 | OK |
| `weight_estimates` | **aucune** | point 1-A |
| vues `v_*_facts` | 7.1 | utilisées avant par 5.13 et 7.6 : points 5-K, 5-J |

Aucune story ne crée toutes les tables d'avance : la règle « table créée par la première story qui en a besoin » est respectée, sauf les cas ci-dessous.

### 2.3 Points

**2-A — bloquant — colonne `reports.citizen_type` créée deux fois (conflit de migration).**
Preuve : 1.6 : « `reports` porte … `citizen_type` nullable parmi les 5 Types de déchet » ; 3.11 : « `reports` gagne `client_predicted_type`, `client_confidence`, `client_model_version` …, `citizen_type`, la colonne générée `device_type` … ». La migration de 3.11 échouera (`column already exists`).
Correction : dans **3.11**, remplacer « `citizen_type`, la colonne générée » par « la colonne générée `device_type = coalesce(citizen_type, client_predicted_type)` (`citizen_type` existe depuis la story 1.6) ».

**2-B — à corriger — table `corrections` : deux créateurs possibles, et l'intro de l'Epic 4 contredit la règle de cohérence.**
Preuve : la règle de cohérence fixe « Table `corrections`, `prefilled_type()` | 3.11 / 3.14 | 4.3 (doit être fait après 3.11 et 3.14) » ; mais l'Epic 4 dit « **L'Epic 3 n'est pas requis** … sauf `corrections` si elle manque (story 4.3) » et 4.3 dit « créée par cette story avec le même schéma (AD-19) si elle n'existe pas ».
Correction :
- Intro de l'Epic 4 : remplacer « L'Epic 3 n'est pas requis : … sauf `corrections` si elle manque (story 4.3). » par « Les stories 3.11 (`corrections`) et 3.14 (`prefilled_type()`, `get_for_staff()`) sont requises par 4.1 et 4.3 ; la Classification serveur (3.13) ne l'est pas : sans elle, la File affiche « classification serveur en attente ». »
- 4.3 : supprimer « ou créée par cette story avec la même règle » et « ou créée par cette story avec le même schéma (AD-19) si elle n'existe pas ».

**2-C — à corriger — `get_for_staff()` sans propriétaire unique.**
Preuve : 3.14 l'utilise (« exposé dans le modèle de lecture du Personnel (`reports.service.get_for_staff()`) ») ; 4.1 dit « créé par cette story, ou étendu s'il existe ». La règle de cohérence ne le cite pas.
Correction : ligne de cohérence à ajouter : `| reports.service.get_for_staff() | 3.14 | 4.1 (étend les champs), 4.2, 4.3 |` ; dans 4.1 remplacer « (créé par cette story, ou étendu s'il existe) » par « (créé par la story 3.14, étendu ici) ».

**2-D — à corriger — `core/events.py` et `reactions.py` : textes contradictoires avec la règle de cohérence (propriétaire 1.11).**
Preuve : 2.8 « (`core/events.py` et `reactions.py` sont créés par cette story s'ils n'existent pas encore) » ; prérequis de l'Epic 4 « stories 2.8 (`GET /v1/reports/mine`, `core/events.py`, `reactions.py`) ».
Correction : dans 2.8, remplacer la parenthèse par « (créés par la story 1.11) » ; dans les prérequis de l'Epic 4, remplacer par « stories 2.8 (`GET /v1/reports/mine`) et 2.10 (`AccountDeleted`) ».

**2-E — à corriger — URL signée de 5 min (`MEDIA_HOST`) sans propriétaire.**
Preuve : première apparition dans 2.9 (« l'ancienne URL signée de la photo ne fonctionne plus », H60, Epic 2), puis 4.1 (« une URL signée de 5 min de la photo sur `MEDIA_HOST` », H48), 4.5, 5.x, 9.3. Aucune story ne crée la fonction de `core.storage`.
Correction : ajouter à **4.1** le critère « **Étant donné** `core.storage.signed_url(object_key, ttl=300)` (créée par cette story, client S3 public, `MEDIA_HOST`) **Quand** l'URL a plus de 5 min **Alors** Garage la refuse » ; ligne de cohérence : `| core.storage.signed_url() (5 min, MEDIA_HOST) | 4.1 | 2.9, 4.5, 5.x, 9.x |` ; et voir 5-L pour 2.9.

---

## 3. Qualité des stories — ÉCHEC

Toutes les 92 stories ont une ligne « Exigences » et une « Porte ». 80 citent au moins une FR ; les 12 autres (1.1, 1.2, 8.1, 8.3, 8.4, 8.5, 8.7, 8.9, 8.10, 8.12, 8.13, 8.14) citent des NFR, AR ou AD : acceptable, aucune story n'est sans référence d'exigence.

**3-A — à corriger — story 1.1 trop grosse pour un seul agent.**
Preuve : 9 blocs de critères couvrant arborescence backend + PWA, 7 services Compose avec empreintes et healthchecks, rôles PostgreSQL, `/healthz`, `/readyz` (4 pannes simulées), validation `ENV`×`DEMO_MODE`, inventaire des secrets, exposition de `/docs`, enveloppe d'erreur, journaux masqués, coquille PWA i18n + thème, routage Caddy.
Découpage proposé :
- **1.1a Squelette backend et Compose** : arborescence `backend/`, `ml/`, `infra/`, Compose 7 services + healthchecks, `migrate`, rôles `teranga_migrator`/`teranga_app`, PostGIS, refus du `CREATE TABLE`.
- **1.1b Configuration, sondes et conventions d'API** : `Settings`, refus `ENV`/`DEMO_MODE`, secrets manquants, `/healthz`, `/readyz`, `/docs` selon `ENV`, enveloppe d'erreur, `structlog` masqué, unité de travail + `after_commit`, worker arq + battement, `GET /v1/config` (propriété de la règle de cohérence).
- **1.1c Coquille PWA et bord Caddy** : `create-vite` + `vite-plugin-pwa`, i18n `fr.json`/`wo.json`, police Inter, bloc `@theme`, routage Caddy (`/`, `/v1/*`, sondes, `MEDIA_HOST`, refus `/metrics` et `/v1/ai/*`).
Mettre à jour la ligne de cohérence « Unité de travail, `core.db.after_commit`, worker arq, `GET /v1/config` | 1.1 » → « 1.1b ».

**3-B — à corriger — story 1.2 trop grosse.**
Preuve : 11 blocs (pipeline, import-linter, ESLint `fetch`, Gitleaks + règle Figma, épinglage, `git ls-files`, `.env.example`, `SECURITY.md`, Dependabot, script de contraste, codes d'erreur ↔ `fr.json`, table des routes, réglages GitHub, `LICENSE`).
Découpage proposé :
- **1.2a CI de qualité** : ruff, ESLint (dont `fetch`), pytest sur services réels, Vitest, couverture ≥ 60 %, import-linter (3 contrats + paquet témoin).
- **1.2b Hygiène du dépôt public** : Gitleaks + règle Figma, épinglage, `git ls-files`, `.gitignore`, `.env.example`, `SECURITY.md`, Dependabot, protection de `main`, `LICENSE` (H60).
- **1.2c Contrôles de contrat** : script de contraste (paire témoin), codes d'erreur ↔ `fr.json`, table des routes ↔ liste blanche.

**3-C — mineur — story 1.6 volumineuse.**
Preuve : 4 tables, validation, consentement, `X-Device-Id`, ingestion photo (415/413/422), ré-encodage, compteur annuel concurrent, drapeau de précision, rollback + `after_rollback`, étiquetage démo ; s'y ajoute la miniature (point 5-H).
Découpage proposé : **1.6a** création du Signalement (tables, validation, Zone, Numéro de suivi, drapeau, démo, unité de travail) ; **1.6b** `core.storage.ingest_photo()` (types, tailles, ré-encodage, bucket privé, `after_rollback`, miniature `thumb:<photo_id>`).

**3-D — mineur — story 4.8 volumineuse.**
Découpage proposé : **4.8a** abonnements (tables, VAPID dans `GET /v1/config`, `POST/DELETE /v1/me/push-subscriptions`, demande d'autorisation contextuelle, suppression sur `AccountDeleted`) ; **4.8b** envoi (réaction `notify:<status_event_id>`, unicité, ≤ 1 min, 404/410/5xx, ouverture au toucher). L'émission de `ReportStatusChanged` passe en 4.2 (point 5-D).

**3-E — mineur — critère non testable dans 8.11.**
Preuve : « **Quand** un mois s'écoule **Alors** la disponibilité mensuelle est calculée et consignée ».
Correction : « **Étant donné** une sonde externe sur `/healthz` toutes les minutes **Quand** on génère le rapport sur une période (test sur 24 h simulées avec 15 min de panne) **Alors** il affiche 98,96 % et la cible de 99 % ; le premier rapport mensuel réel est une tâche d'exploitation, hors story. »

**3-F — mineur — critère non réalisable dans le temps de la story 8.14.**
Preuve : « **Quand** la fin du pilote approche **Alors** une seconde restauration complète … a réussi sur un hôte d'un autre hébergeur ».
Correction : retirer ce bloc de 8.14 et créer **8.15 Restauration de sortie vers un autre hébergeur** (porte : fin du pilote, exigences NFR-6.4), ou le déplacer dans la liste de contrôle de fin de pilote.

---

## 4. Structure des epics — ÉCHEC

Les epics 1 à 7 et 9 sont orientés valeur (titres et descriptions du point de vue Citoyen, Modérateur, Collecteur, Administrateur commune, Recycleur). L'Epic 8 est en partie technique, mais formulé pour le jury et la commune et justifié par les portes démo/pilote : acceptable. Les stories de fondation (1.1, 1.2) ne créent que le nécessaire ; aucune table n'est créée d'avance.

Recouvrements de fichiers relevés : `theme.css` (1.1, 1.8, 3.8, 8.1), écran 3 (1.8, 3.12, 6.1 — justifié par la boucle Epic 1 sans IA → Epic 3 → Epic 6), écran 1 (1.3, 1.11, 2.2, 4.6, 4.7, 6.2, 6.3 — incident), `reactions.py` (1.11, 2.8, 2.10, 4.8, 5.5 — voulu par AD-21), porte des Statuts (4.2 puis 4.3, 4.4, 5.3, 5.5, 5.6, 5.11 — voulu par AD-3).

**4-A — à corriger — composant Type de déchet construit trois fois.**
Preuve : 1.8 crée « un sélecteur facultatif des 5 Types de déchet … chacun avec pictogramme, libellé et couleur … les couleurs par type sont ajoutées comme jetons dans `@theme` et passent le script de contraste » ; 3.8 crée « le composant unique `WasteTypeBadge` / `WasteTypePicker` … une couleur déclarée comme jeton » avec le même contrôle de contraste ; 8.1 redéclare les cinq jetons. Aucune boucle de retour ne justifie 1.8 → 3.8 (seule 8.1, validation par Mia, en est une).
Correction : faire de **1.8** la propriétaire de `WasteTypeBadge` / `WasteTypePicker` (dans `web/src/features/classify/` ou un dossier partagé) avec jetons provisoires `--color-waste-*` ; réduire **3.8** à « présélection pilotée par la proposition IA et annonce en groupe de boutons radio (`aria-checked`) », sans nouveaux jetons ; garder **8.1** pour les valeurs définitives. Ligne de cohérence : `| Composant WasteTypeBadge/WasteTypePicker et jetons --color-waste-* | 1.8 | 3.8, 3.12, 4.1, 5.2, 7.3, 8.1 (valeurs définitives), 9.2 |`.

**4-B — à corriger — contrôle d'épinglage posé deux fois et règle de cohérence erronée.**
Preuve : 1.2 « **Étant donné** le script de contrôle d'épinglage … la CI échoue en listant chaque élément non épinglé » ; 8.5 refait le même contrôle ; la règle de cohérence dit pourtant « Contrôles de CI non posés par 1.2 : … épinglage par empreinte | 8.5 ».
Correction : dans le tableau « Contrôles de CI non posés par 1.2 », remplacer la ligne par `| Trivy, pip-audit, npm audit (exceptions datées) | 8.5 |` ; dans 8.5, remplacer le bloc d'épinglage par le critère de 1-I et « le contrôle d'épinglage de la story 1.2 couvre aussi le workflow de publication ».

**4-C — mineur — doublons de critères entre stories.**
Preuve : refus `ENV`×`DEMO_MODE` (1.1 et 2.1), secret manquant bloque le démarrage (1.1 et 8.10), table des routes ↔ liste blanche (1.2 et 2.5).
Correction : garder le critère dans la première story et écrire dans la seconde « (test de la story 1.1 / 1.2, étendu à …) » : 2.1 ne garde que le bandeau et les 6 cas, 8.10 ne garde que KMS et rotation, 2.5 ne garde que le générateur route × rôle.

**4-D — mineur — porte de l'Epic 9 incohérente.**
Preuve : en-tête et Epic List : « Extension (après le pilote) » ; notes de lecture et PRD §4.12 : « extension = Lots de matière, après H48 ».
Correction : aligner sur le PRD : « **Porte :** extension (après H48, hors démo) ».

---

## 5. Dépendances — ÉCHEC (critique)

**5-A — bloquant — 1.11 (H24) dépend de `retention.sweep`, dont la propriétaire est 2.6 (H48).**
Preuve : 1.11 « la tâche planifiée `retention.sweep` (quotidienne) s'exécute … les entrées `idempotency_records` de plus de 24 h sont supprimées » ; règle de cohérence « Balayage de rétention `retention.sweep` | 2.6 » ; 2.6 « (créée par cette story si elle n'existe pas encore) ».
Correction : ligne de cohérence → `| Balayage de rétention retention.sweep | 1.11 | 2.6, 2.10, 4.5, 5.6, 8.14 |` ; dans 2.6 remplacer « (créée par cette story si elle n'existe pas encore) » par « (créée par la story 1.11) ».

**5-B — bloquant — Frise de suivi : 1.8 (H24) dépend de sa propriétaire 4.6 (H60).**
Preuve : règle de cohérence « Composant Frise de suivi | 4.6 | 1.8 (affiche seulement l'état « Signalé ») » ; or 1.8 construit déjà le composant complet (« ses 4 étapes … en liste ordonnée, l'étape courante « Signalé » étant distinguée autrement que par la couleur et annoncée »).
Correction : ligne de cohérence → `| Composant Frise de suivi (4 étapes) | 1.8 | 4.6 (ajoute l'état rejeté, le motif, l'étape courante dynamique) |` ; dans 4.6 remplacer « (créé par cette story, ou complété s'il existe déjà sur l'écran 4) » par « (créé par la story 1.8, complété ici) ».

**5-C — bloquant — 3.15 (Epic 3) dépend de 4.2 et 4.3 (Epic 4).**
Preuve : 3.15 « « ayant atteint `validé` » se lit dans `report_status_events` » (table créée par 4.2) et son jeu d'essai exige des Signalements `validé` et `rejeté` (transitions de 4.3, 4.4).
Correction : **déplacer 3.15 dans l'Epic 4**, après 4.5, sous le titre « Story 4.6 : Export des Corrections consenties comme exemples étiquetés » (porte H48), et renuméroter 4.6–4.8 en 4.7–4.9 ; mettre à jour la carte de couverture : « FR-13 : Epic 3 et Epic 4 (export) », et dans 3.17 « archive produite par la story 4.6 ».

**5-D — bloquant — 5.3 et 5.6 (H48) supposent l'émission de `ReportStatusChanged`, introduite par 4.8 (H60).**
Preuve : 5.3 « `ReportStatusChanged` n'est émis qu'après le commit » ; 5.6 « `ReportStatusChanged` émis après le commit » ; seule 4.8 (porte H60) ajoute « `ReportStatusChanged` … est émis par `core.events.emit()` en `after_commit` » à la transition.
Correction : déplacer le critère d'émission de **4.8 vers 4.2** :
> **Étant donné** une transition réussie
> **Quand** l'unité de travail est validée
> **Alors** `ReportStatusChanged` (`event_id` de `report_status_events`, Numéro de suivi, `owner_key`, `author_user_id`, nouveau Statut, motif) est émis par `core.events.emit()` en `after_commit`, sans abonné à ce stade
> **Et** aucune émission n'a lieu si la transaction est annulée (test).

et, dans 4.8, écrire « l'événement émis par la story 4.2 » ; ajouter `ReportStatusChanged` (émission) à la règle de cohérence avec propriétaire 4.2.

**5-E — bloquant — écran 5 (5.2, H48, Epic 5) dépend des tuiles de 8.7 (H60, Epic 8).**
Preuve : 5.2 « la carte (react-leaflet, tuiles de `TILES_HOST`) » ; les tuiles ne sont générées et servies qu'en 8.7 (« générées à partir d'un extrait OpenStreetMap … servies par Caddy sur `TILES_HOST` ») ; la CSP n'autorise aucune autre source d'images que `MEDIA_HOST` et `TILES_HOST`.
Correction : déplacer de 8.7 vers **5.2** le critère :
> **Étant donné** l'emprise de la Zone active définie dans `infra/` (zooms 11 à 17)
> **Quand** les tuiles sont préparées
> **Alors** elles sont générées depuis un extrait OpenStreetMap, sans téléchargement massif depuis les serveurs publics d'OSM, servies par Caddy sur `TILES_HOST`, et l'attribution « © OpenStreetMap contributors » est affichée sur chaque carte.

8.7 garde seulement « les tuiles de la story 5.2 sont copiées sur le portable et aucune requête de tuile n'échoue Internet coupé ». Ligne de cohérence : `| Tuiles TILES_HOST de la zone de démo | 5.2 | 7.4, 7.6, 8.7 |`.

**5-F — bloquant — 8.1 (H48) dépend de l'écran 7 (7.3, H60), et le prérequis de l'Epic 8 contredit la porte de 8.1.**
Preuve : 8.1 « affiché sur les écrans 3 et 5 (390×844), l'écran 7 et la File de modération … des captures de ces quatre écrans » ; prérequis de l'Epic 8 « Epics 1 à 7 livrés » alors que 8.1 est H48 et l'Epic 7 H60.
Correction : dans 8.1, remplacer « l'écran 7 et la File de modération » par « la File de modération » et « ces quatre écrans » par « ces trois écrans » ; ajouter à **7.3** « la répartition utilise les jetons `--color-waste-*` de la story 8.1 ». Remplacer le prérequis de l'Epic 8 par : « 8.1 : stories 1.8, 3.12, 4.1, 5.2 ; 8.2 à 8.9 : Epics 1 à 7 ; 8.10 à 8.14 : 8.1 à 8.9. »

**5-G — bloquant — 7.2 (H60) teste l'exclusion des Preuves `contestée`, qui n'existent qu'avec 5.13 (pilote).**
Preuve : 7.2 « **Étant donné** des Preuves de collecte acceptées pendant la période, dont une `contestée` » ; `proof_reviews` est créée par 5.13 (pilote) ; la règle de cohérence prévoit « 7.1 : `review_status = unreviewed` tant qu'elle n'existe pas ».
Correction : dans 7.2, remplacer « dont une `contestée` » par « (Kg collectés = Preuves dont `review_status` ≠ `contested` dans `v_mission_facts`) » et déplacer vers **7.7** (pilote) le critère :
> **Étant donné** des Preuves acceptées dans la période dont une `contestée` (story 5.13)
> **Quand** les Indicateurs sont calculés
> **Alors** les Kg collectés l'excluent, au total et par Type de déchet.

**5-H — bloquant — miniature : la propriétaire déclarée (1.6) n'a aucun critère, et 4.1 (Epic 4) dépend de fait de 5.1 (Epic 5).**
Preuve : règle de cohérence « Tâche de miniature `thumb:<photo_id>` | 1.6 | 5.1 » ; 1.6 ne mentionne aucune miniature ; 5.1 « la tâche arq `thumb:<photo_id>` s'exécute (créée par cette story si elle n'existe pas encore) » ; 4.1 (H48) affiche « chaque élément avec miniature » ; 2.9 et 4.5 suppriment « la miniature ».
Correction : ajouter à **1.6** :
> **Étant donné** une photo de Signalement stockée
> **Quand** la transaction est validée
> **Alors** la tâche arq `thumb:<photo_id>` est mise en file par `after_commit` et produit une miniature JPEG d'au plus 30 Ko sous `report_thumb/<yyyy>/<mm>/<uuid>.jpg`, dont la clé est gardée dans `report_photos.thumb_key` (test sur 10 photos de 1 Mo)
> **Et** rejouer la tâche ne crée pas de second objet.

et dans 5.1 remplacer « (créée par cette story si elle n'existe pas encore, clé …) » par « (story 1.6) ».

**5-I — bloquant — 5.5 (H48) affiche le nom affiché du Collecteur, colonne ajoutée par 2.8 (H60).**
Preuve : 5.5 « il voit la Mission `active` (nom affiché du Collecteur, date d'acceptation) » ; `display_name` est ajoutée à `users` par 2.8 (« une migration qui ajoute à `users` `display_name`, `locale` … »), porte H60. 2.11 (H60) en a aussi besoin à la création.
Correction : dans **2.3**, ajouter `display_name` (nullable) à la création de `users` ; dans 2.8, remplacer « ajoute à `users` `display_name`, `locale` » par « ajoute à `users` `locale` » ; dans 5.5, écrire « nom affiché du Collecteur (ou son identifiant court s'il n'en a pas) ».

**5-J — à corriger — 7.6 (opt. H48) dépend des vues de 7.1 (H60).**
Preuve : 7.6 porte « opt. H48 » et s'appuie sur AD-22 / AR-31 (vues analytiques de 7.1, porte H60).
Correction : dans 7.6, porte → « opt. H48 avec 7.1 (si la porte H48 est atteinte en avance, 7.1 est tirée avec elle), sinon après H60 » et ajouter « **Prérequis :** story 7.1 ».

**5-K — à corriger — 5.13 (Epic 5) appelle `recreate_analytics_views()`, créé par 7.1 (Epic 7).**
Preuve : 5.13 « toute vue analytique qui lit `proofs` est recréée par `recreate_analytics_views()` ». La porte (pilote > H60) est respectée, pas la numérotation.
Correction : dans 5.13, écrire « **Prérequis :** story 7.1 (porte H60, antérieure au pilote) ; la migration appelle `recreate_analytics_views()` de la story 7.1 et `v_mission_facts.review_status` lit désormais `proof_reviews` » ; ou déplacer 5.12 à 5.14 dans un epic placé après l'Epic 7.

**5-L — à corriger — 2.9 (Epic 2) et 5.9 (opt. H48) s'appuient sur des briques ultérieures.**
Preuve : 2.9 teste « l'ancienne URL signée de la photo ne fonctionne plus » alors que l'URL signée naît en 4.1 (point 2-E) ; 5.9 (opt. H48) fait choisir « un Collecteur dans la liste des Collecteurs vérifiés actifs (nom affiché, recherche par nom) », liste servie par `GET /v1/admin/collectors` de 2.11 (H60).
Correction : 2.9 → remplacer par « et l'objet photo et sa miniature n'existent plus dans le bucket (lecture interne → 404) » ; 5.9 → ajouter « **Et** la liste vient de `GET /v1/missions/assignable-collectors` (créée par cette story : Collecteurs vérifiés actifs, nom affiché, sans numéro) », ou porter 5.9 à H60 après 2.11.

**5-M — mineur — `CollectorSuspended` émis sans réaction.**
Preuve : 2.11 « `CollectorSuspended` est émis » ; aucune story n'y réagit (l'épine non plus). Une Mission `active` d'un Collecteur suspendu reste bloquée jusqu'à 48 h (5.11, pilote).
Correction : dans 5.5, ajouter une réaction « `CollectorSuspended` → `missions.service.on_collector_deleted()` (même annulation) », ou écrire dans 2.11 « aucune réaction au MVP ; l'Administrateur commune annule la Mission (story 5.5) ».

**5-N — mineur — références conditionnelles à des epics ultérieurs.**
Preuve : 4.6 « un élément `en attente d'envoi` de la File hors-ligne, s'il en existe » (Epic 6) ; 2.10 teste « un Signalement par Statut » (`rejeté`, `assigné`, `collecté` produits par les Epics 4 et 5).
Correction : 4.6 → « (la File hors-ligne de l'Epic 6 complète cet affichage ; sans elle, rien à afficher) » ; 2.10 → « les Signalements de test sont insérés directement aux Statuts voulus (valeurs de `core/enums.py`) ».

---

## Lignes à modifier dans « Règles de cohérence entre epics » (récapitulatif)

| Action | Ligne |
|---|---|
| Modifier | `Unité de travail, core.db.after_commit, worker arq, GET /v1/config` → propriétaire **1.1b** (si 3-A appliqué) |
| Modifier | `Balayage de rétention retention.sweep` → propriétaire **1.11**, utilisée par 2.6, 2.10, 4.5, 5.6, 8.14 |
| Modifier | `Composant Frise de suivi` → propriétaire **1.8**, utilisée par 4.6 |
| Modifier | `Table corrections, prefilled_type()` → **3.11 / 3.14**, utilisée par 4.1, 4.3, 4.6 (ex-3.15) |
| Modifier | `Tâche de miniature thumb:<photo_id>` → 1.6 **avec critère ajouté**, utilisée par 2.9, 4.1, 4.5, 5.1 |
| Ajouter | `reports.service.get_for_staff()` → 3.14 ; 4.1, 4.2, 4.3 |
| Ajouter | `core.storage.signed_url()` → 4.1 ; 2.9, 4.5, 5.x, 9.x |
| Ajouter | Émission de `ReportStatusChanged` → 4.2 ; 4.8, 5.3, 5.6 |
| Ajouter | Table `weight_estimates`, `estimated_weight()` → 5.1 ; 5.2, 5.3, 7.1, 7.5 |
| Ajouter | Tuiles `TILES_HOST` → 5.2 ; 7.4, 7.6, 8.7 |
| Ajouter | Composant `WasteTypeBadge/WasteTypePicker`, jetons `--color-waste-*` → 1.8 ; 3.8, 3.12, 4.1, 5.2, 7.3, 8.1, 9.2 |
| Ajouter | `users.display_name` → 2.3 ; 2.8, 2.11, 5.5, 5.9 |
| Modifier | « Extensions du jeu de démonstration » : « 4.2 les Signalements » → « 4.4 les Signalements » |
| Modifier | « Contrôles de CI non posés par 1.2 » : « Trivy, pip-audit, npm audit, épinglage par empreinte » → « Trivy, pip-audit, npm audit (exceptions datées) » |
| Modifier | « Porte de l'Epic 8 » : ajouter « 8.1 ne dépend que de 1.8, 3.12, 4.1 et 5.2 » |
