# Validation finale BMAD (étape 4) — passe 2

Document jugé : `_bmad-output/planning-artifacts/epics.md` (frontmatter `status: draft`, 9 epics, 100 stories : 17 + 12 + 15 + 11 + 15 + 3 + 7 + 15 + 5).
Sources consultées : PRD (§4 FR, §5 NFR), épine d'architecture (via les AR-n reprises dans epics.md), fichier d'étape `step-04-final-validation.md`.
epics.md n'a pas été modifié.

Règle de verdict : un contrôle est en **ÉCHEC** s'il porte au moins un point **bloquant**. Les points **à corriger** doivent être levés avant de passer `status: final` ; les points **mineurs** peuvent l'être au fil de l'eau.

## Synthèse

| # | Contrôle | Verdict | Bloquant | À corriger | Mineur |
|---|---|---|---|---|---|
| 1 | Couverture FR-1..FR-43 | OK | 0 | 1 (A4) | 1 (M13) |
| 2 | Architecture (squelette, tables) | OK | 0 | 0 | 3 (M1, M5, M12) |
| 3 | Qualité des stories | OK | 0 | 1 (A6) | 2 (M8, M11) |
| 4 | Structure des epics, churn | OK | 0 | 0 | 2 (M9, M10) |
| 5 | Dépendances (critique) | **ÉCHEC** | 1 (B1) | 4 (A1, A2, A3, A5) | 5 (M2, M3, M4, M6, M7) |
| | **Total** | **ÉCHEC global** | **1** | **6** | **13** |

Conclusion : epics.md doit rester `status: draft` ; 1 contrôle ouvert (n° 5), 7 points à lever avant la finalisation.

---

## 1. Couverture des FR — OK

Les 43 FR sont portées par au moins une story, et chaque conséquence testable du PRD a un critère correspondant. Preuves :

| FR | Stories | Conséquences testables vérifiées |
|---|---|---|
| FR-1 | 2.2, 2.3 | +221 seul, 5 min, usage unique, 5 essais, haché, 5/h numéro, 5/h appareil, 20/h IP, 429 + délai, plafond SMS 503 + alerte |
| FR-2 | 2.3, 2.4 | 30 j, ≤ 15 min, déconnexion/révocation 401, réutilisation → famille révoquée, aucun jeton en stockage, 5 tests de jeton invalide |
| FR-3 | 2.5 (+ 4.1, 4.7, 5.1) | route × rôle, propriété 404, jamais par Numéro de suivi, aucun auteur pour Collecteur |
| FR-4 | 1.7, 1.11, 1.16, 2.8, 4.6 | consentement avant capture, rien envoyé sans accord, horodatage compte / appareil, refus non bloquant, copie sur Signalement, retrait passé + futur évalué à l'export |
| FR-5 | 2.8, 2.9, 2.10, 5.11 | profil, langue, nom, suppression (401, purge 30 j, pending/rejeté supprimés, validés anonymisés), retrait anonyme |
| FR-6 | 1.2, 2.1, 2.2 | OTP affiché, refus en prod, bandeau partout |
| FR-7 | 1.8, 1.9, 1.11, 1.13 | champs obligatoires, Zone active écran 2 + 422, `TC-AAAA-NNNNNN` concurrent, Zone déduite, > 50 m drapeau, consigne |
| FR-8 | 1.9, 1.10, 1.14 | ≤ 300 Ko, HEIC, 415/413/422, ré-encodage sans EXIF, photo identique → Doublon probable |
| FR-9 | 1.12 | 201 puis 200, 10 → 1, 409 sans donnée |
| FR-10 | 1.15 | 10/h appareil/IP/compte, 60/min, XFF 11e → 429, AOF |
| FR-11 | 3.9, 3.12, 3.14 | < 3 s Android 2 Go hors réseau, repli sans Modèle, pas de Désaccord |
| FR-12 | 3.12 | 59 % / 60 % |
| FR-13 | 3.11, 3.12, 4.3, 4.6 | Correction en un toucher, enregistrée avec prédiction/version/auteur, export validé + consenti |
| FR-14 | 3.11, 3.13, 3.14 | tâche de fond, p95 < 2 s, deux Classifications, pré-rempli, rien de définitif, file bornée 500 |
| FR-15 | 3.14, 4.1 | drapeau, `NULL` sans Classification locale |
| FR-16 | 3.1–3.7, 3.13, 3.15, 4.11 | version enregistrée, remplaçable, porte SM-2 + Fiche, réentraînement mensuel |
| FR-17..19 | 6.1, 6.2, 6.3 | mode avion 100 % des champs, envoi auto sans doublon, 4xx définitif, compteur exact, « Réessayer » < 1 s |
| FR-20 | 1.13, 2.8, 4.7, 1.7 | liste, ≤ 15 s, motif, perte de liste anonyme + compte proposé, aucune donnée par Numéro de suivi |
| FR-21 | 4.8, 4.9, 4.10 | changements depuis la dernière visite, push ≤ 1 min, pas de push anonyme |
| FR-22 | 4.1 | ≤ 50, plus anciens d'abord, champs, drapeaux, filtre, lien vers l'original |
| FR-23 | 4.2, 4.3, 4.4, 4.5, 4.7 | validation/rejet, 409, audit, visibilité Collecteur, photo « personne ou plaque » < 24 h (réserve A4) |
| FR-24..29, FR-42 | 5.1–5.9, 5.12 | rayon 1–10 km, 3 décimales, miniature, exclusivité, annulation, itinéraire, assignation ≤ 15 s, Preuve 150 m + précision, expiration 48 h 01 |
| FR-30, FR-41 | 5.10, 5.13, 5.14, 5.15, 7.7 | historique, total kg, tirage ≥ 5 % et ≥ 1, photo identique, revue motivée, exclusion des kg, part contestée |
| FR-31..34 | 7.1–7.6, 2.5 | Cohorte, 6/10 → 60 %, carte < 2 s / 5 000, export sans donnée personnelle, carte publique ≥ 500 m masquée sous 3 |
| FR-35, FR-36 | 2.6, 2.7, 2.10, 2.11, 2.12, 4.2, 4.3, 4.6, 5.5, 5.9, 5.12, 5.14, 7.5 | les 17 actions d'audit ont chacune une story productrice, méta-test `PENDING_AUDIT_ACTIONS` |
| FR-37 | 1.11, 1.13, 1.17, 2.5, 4.4, 5.3, 5.6 | chargement/retrait en une commande, comptes de chaque rôle, étiquetage automatique |
| FR-38..40 | 9.1–9.5 | 422, contact après demande, 409 sur double réservation, ≤ 15 s |
| FR-43 | 2.12 | TOTP, 403 `second_factor_required`, audit activation/réinitialisation |

### Points

- **A4 — à corriger.** Story 4.4 : le rejet `duplicate` exige `duplicate_of_report_id` dans la requête, mais aucune story ne dit où il est enregistré, alors que 4.7 et 4.8 doivent renvoyer « le Numéro de suivi du Signalement d'origine » (FR-23 : « un rejet doublon affiche au Citoyen le Numéro de suivi d'origine »). **Correction :** dans 4.4, préciser que `reject()` passe `duplicate_of_report_id` dans `set_fields` de `transition()` (colonne `reports.duplicate_of_report_id` de la story 1.14, alors écrasée par la décision) ou l'écrit dans le détail du motif de `report_status_events` ; et dans 4.7/4.8, citer cette source.
- **M13 — mineur.** Story 3.12 : sous le Seuil de confiance (ou sans Modèle), il n'est pas dit que `citizen_type` est envoyé quand le Citoyen choisit le même type que la proposition. `prefilled_type()` (3.14) renverrait alors la Classification serveur au lieu du choix explicite du Citoyen (PRD : « le choix du Citoyen s'il en a fait un »). **Correction :** ajouter à 3.12 « tout choix explicite fait sans présélection est envoyé en `citizen_type` ».

Réserve liée : la partie « historique des Statuts visible du Personnel » de FR-36 n'est couverte que pour le Modérateur (voir B1).

---

## 2. Architecture — OK

- **Squelette.** Story 1.1 : backend écrit à la main, « sans starter full-stack ni SQLModel », arborescence AD-1, Compose à 7 services, rôles `teranga_migrator`/`teranga_app`. Story 1.3 : `create-vite` (`react-ts`) pour la PWA, conforme à AR-1. Aucune table métier créée en 1.1.
- **Tables (23 d'AR-10) : chacune créée par une seule story, la première qui en a besoin.** `zones` 1.8 ; `devices`, `reports`, `report_photos`, `tracking_counters` 1.11 ; `idempotency_records` 1.16 ; `users` 2.3 ; `refresh_tokens` 2.4 ; `collector_profiles` 2.5 ; `audit_logs`, `audit_log_ips` 2.6 ; `staff_second_factors` 2.12 ; `corrections` 3.11 ; `classifications` 3.13 ; `report_status_events` 4.2 ; `push_subscriptions`, `notifications` 4.9 ; `weight_estimates` 5.1 ; `missions` 5.3 ; `proofs` 5.6 ; `proof_reviews` 5.14 ; `material_lots` 9.1 ; `lot_requests` 9.4. Vues : 7.1 (branchement de `proof_reviews` en 7.7).
- **Colonnes ajoutées après coup, chacune une seule fois et avant usage :** `(owner_key, client_uuid)` unique 1.12 ; `duplicate_of_report_id` + index GiST 1.14 ; `reports.author_user_id`, `users.display_name` 2.3 ; `users.locale/training_consent/terms_*` 2.8 ; `client_*`, `device_type`, `flag_low_confidence` 3.11 ; `classification_status` 3.13 ; `flag_ai_disagreement` 3.14 ; `retained_type` 4.3 ; `report_photos.purged_at` 4.5 ; `proofs.sampled_at/sample_reason` 5.13 ; `material_lots.reserved_*` 9.5. Aucun doublon de création trouvé.
- **Tâches planifiées d'AR-23 :** les 7 ont un propriétaire (1.16, 2.10, 3.13, 4.5, 5.12, 5.13, 8.11).

### Points

- **M1 — mineur.** Story 4.9 crée `notifications` alors que seule 4.10 l'utilise (unicité `status_event_id`). **Correction :** déplacer la création de `notifications` dans la migration de 4.10 ; 4.9 ne crée que `push_subscriptions`.
- **M5 — mineur.** Briques sans propriétaire déclaré : `core.geo.expose()` (premier usage 4.1, test « 3 décimales » en 5.1), `core.security.principal()` et `core.demo.flag()` (créés implicitement par 1.11), `missions.service.photo_seen()` (5.13). **Correction :** écrire « créé par cette story » dans 4.1 (ou 1.8) pour `expose()`, dans 1.11 pour `principal()` et `demo.flag()`, dans 5.13 pour `photo_seen()`, et les ajouter au tableau des règles de cohérence.
- **M12 — mineur.** Story 1.17 : « lignes `is_demo = true` de `reports` et `report_photos` », mais `report_photos` n'a pas de colonne `is_demo` (AR-32). **Correction :** « les `report_photos` rattachées aux Signalements `is_demo` ».

---

## 3. Qualité des stories — OK

Chaque story a un rôle, une valeur, des critères Étant donné / Quand / Alors testables (valeurs limites, horloges simulées, tests de concurrence, tests Playwright), une ligne « Exigences » et une ligne « Porte ». Les stories ml/ (3.4–3.7) ont des critères mesurables (verrou du Jeu de test, F1 ± 0,01, 1e-3, ≤ 8 Mo). Les stories de démo (8.6–8.9) sont vérifiables par consignation.

### Points

- **A6 — à corriger.** NFR-SM-3 (création < 30 s, médiane de 10 essais par ≥ 3 nouveaux utilisateurs sur Android 2 Go) est citée par 1.13 et 3.12 mais aucun critère ne la mesure. **Correction :** ajouter à 3.12 (ou 8.9) un critère « 3 nouveaux utilisateurs × 10 essais sur Android 2 Go, écran 1 → écran 4, médiane < 30 s, résultats consignés ».
- **M8 — mineur.** Stories lourdes pour un seul agent : 1.11 (4 tables, route, compteur annuel, miniature arq, drapeaux, démo), 1.13 (client OpenAPI généré + écrans 3 et 4 + deux composants partagés), 2.5 (rôles, générateur route × rôle, propriété, `collector_profiles`, comptes de démo, routage PWA), 5.6 (Preuve, géorepérage, démo, rétention). **Correction suggérée :** sortir de 1.11 la tâche `thumb:` ; sortir de 1.13 la génération du client OpenAPI ; sortir de 2.5 les comptes de démo et le routage PWA par rôle.
- **M11 — mineur.** Story 2.1 : « dernière réponse précachée de `GET /v1/config` », alors que 1.8 garde cette réponse dans Dexie `meta`. **Correction :** « dernière réponse de `GET /v1/config` gardée dans Dexie `meta` (story 1.8) ».

---

## 4. Structure des epics — OK

- Epics 1 à 7 et 9 : titres et résumés orientés utilisateur (Citoyen, Modérateur, Collecteur, Administrateur commune, Recycleur). Les stories techniques sont regroupées en tête d'Epic 1 (1.1–1.6), ce qui est attendu pour un projet neuf, et chacune ne pose que ce qu'il faut à H24.
- Epic 8 : formulé en valeur (jury, commune), mais surtout composé d'exigences non fonctionnelles ; accepté puisqu'il ne couvre aucune FR et que le découpage démo (8.1–8.9) / pilote (8.10–8.15) est explicite.
- Churn : `reports.service.create()` / `POST /v1/reports` est modifié par 1.11, 1.12, 1.14, 1.15, 2.3, 2.8, 3.11, 3.13, 4.2 ; l'écran 1 par 1.7, 1.16, 4.7, 4.8, 6.2, 6.3 ; `GET /v1/config` par 1.2, 1.8, 3.2, 4.9 ; `GET /v1/missions/mine` par 5.3, 5.10, 5.14. Ce churn suit les portes H24 → H48 → H60 (chaque porte livre une démo et un retour) et le tableau des règles de cohérence désigne un propriétaire par brique : le découpage est justifié.

### Points

- **M9 — mineur.** La justification du churn n'est écrite nulle part. **Correction :** ajouter sous « Règles de cohérence entre epics » une phrase : « Les epics touchent les mêmes fichiers (`reports.service`, écran 1, `GET /v1/config`) parce que chaque porte H24/H48/H60 livre une démo ; la consolidation a été écartée pour cette raison. »
- **M10 — mineur.** Epic 8 reste un epic d'exploitation. **Correction facultative :** le noter comme epic transverse assumé dans sa description.

---

## 5. Dépendances (critique) — ÉCHEC

Vérifications faites :
- Ordre des portes par epic, monotone partout sauf l'Epic 7 : Epic 2 (H24 → H48 → opt. H48 → H60 → pilote), Epic 3 (H24 → H48), Epic 4 (H48 → H60 → pilote), Epic 5 (H48 → opt. H48 → H60 → pilote), Epic 6 (H48 → H60), Epic 8 (H48 → H60 → pilote).
- Prérequis inter-epics déclarés (en-têtes des Epics 2 à 9, tableau des règles) : aucun epic ne dépend d'un epic de numéro supérieur. Les mentions vers l'avant (1.13 → 4.7, 2.10 → 5.11, 2.11 → 5.11, 4.7 → Epic 6, 5.10 → 5.15) décrivent des extensions futures, pas des prérequis.
- Références croisées : les 160 mentions « story X.Y » pointent vers des stories existantes, au bon contenu (par ex. 1.6 table des routes, 1.16 `retention.sweep` et `core/events.py`, 2.6 méta-test, 3.14 `get_for_staff()`, 4.2 `ReportStatusChanged`, 5.2 tuiles, 8.14 procédure de restauration). Aucune référence mal renumérotée.
- Tableau des propriétaires : chaque brique est créée par la story annoncée, avant ses utilisatrices.

### Points

- **B1 — bloquant.** Aucune route ne donne à l'Administrateur commune l'accès aux Signalements. 4.1 réserve `/v1/moderation/*` au Modérateur (« un Administrateur commune … 403 »), et aucune autre story ne crée de liste ni de détail de Signalement pour l'Administrateur. Pourtant 5.5 (« le détail d'un Signalement `assigné` dans l'espace du Personnel … un Administrateur commune l'ouvre … bouton « Annuler la Mission » ») et 5.9 (« le détail d'un Signalement `validé` … l'Administrateur commune choisit « Assigner à un collecteur » ») en dépendent. L'Administrateur ne peut donc ni trouver un Signalement `validé` à assigner (FR-28), ni la Mission `active` à annuler (FR-26 côté Administrateur), ni voir l'historique des Statuts que FR-36 réserve au « Personnel ». Ces deux stories utilisent une brique qui n'a pas de propriétaire. **Correction :** dans 4.1, ouvrir `GET /v1/moderation/reports/{id}` en lecture à `municipal_admin` (et l'historique de 4.2) ; dans 5.9 (ou une nouvelle story à opt. H48 placée avant 5.9), créer `GET /v1/staff/reports?status=validated|assigned&cursor=` (Modérateur et Administrateur commune, au test route × rôle) avec la Mission `active` de chaque Signalement `assigné` ; puis citer cette route dans 5.5 et 5.9 et l'ajouter au tableau des règles de cohérence.
- **A1 — à corriger.** Story 7.6 (porte « opt. H48 ») a pour prérequis 7.1, dont la porte est H60 : elle dépend donc d'une porte plus tardive. La parade « 7.1 est tirée avec elle » n'est écrite que dans 7.6. **Correction :** mettre la porte de 7.1 à « opt. H48 si 7.6 est tirée, sinon H60 » et le dire dans « Porte de l'Epic 7 », ou supprimer la dépendance en faisant lire à 7.6 `report_status_events` par `reports.service` sans passer par les vues.
- **A2 — à corriger.** `/metrics` n'a pas de story propriétaire : 1.3 se contente de ne pas le relayer, 8.4 (H60) teste qu'il « reste joignable depuis le réseau interne » et 8.11 lit ses compteurs de 5xx. **Correction :** ajouter à 1.2 (ou à 8.4) un critère qui crée `/metrics` (compteurs de requêtes par route et code HTTP, exposés seulement sur le réseau interne), et l'inscrire au tableau des règles de cohérence.
- **A3 — à corriger.** 8.4 teste « le Modèle indisponible → `/readyz` non prêt » (NFR-7, AR-33 `onnx_sha256`), mais 1.2 ne vérifie que la base, Valkey, le stockage et le worker, et 3.3 ne complète pas `/readyz`. **Correction :** ajouter à 3.3 un critère : « `/readyz` n'est prêt que si la session du Modèle courant est chargée avec un `onnx_sha256` conforme (test : Modèle retiré → 503) ».
- **A5 — à corriger.** Story 5.3 charge « 2 Missions `completed` » de démonstration « par ses propres règles », alors qu'aucune règle de 5.3 ne peut terminer une Mission (`active → completed` passe par la Preuve de 5.6). La question ouverte n° 9 reconnaît ces Missions `completed` sans Preuve. 5.3 dépend donc de 5.6 pour un jeu de données cohérent. **Correction :** 5.3 ne charge que des Missions `active` ; 5.6 charge les Missions `completed` en passant par `submit_proof()` ; supprimer la question ouverte n° 9.
- **M2 — mineur.** 2.5 (H24) cite dans sa liste close de routes appareil des routes créées plus tard : `GET /v1/reports/mine` (2.8), `DELETE /v1/reports/{id}` (2.9), `GET /v1/reports/mine/changes` (4.8). De même, 1.6 met dans la liste blanche `GET /v1/public/map`, qui n'existe qu'en 7.6. **Correction :** 2.5 déclare la liste avec `PUT /v1/device/consent` seul, et chaque story qui crée une route appareil l'y ajoute ; 1.6 précise que l'entrée `GET /v1/public/map` est réservée à 7.6.
- **M3 — mineur.** 3.5 contient un critère déclenché par le résultat d'une story future du même epic (« Quand la mesure de latence de la story 3.6 dépasse 3 s »). **Correction :** « l'option `--arch small` entraîne MobileNetV3-Small sans autre changement de code (test) ; elle sert si la mesure de 3.6 dépasse 3 s ».
- **M4 — mineur.** Erreurs dans le tableau des propriétaires. `core.idempotency` est dit « utilisé par … 6.2 », or `POST /v1/reports` est exempté d'`Idempotency-Key` ; le tableau omet aussi 2.8, 2.9, 4.3, 4.4, 4.9, 5.3, 5.5, 5.9 et 9.x. `retention.sweep` est dit « utilisé par 2.10 », or 2.10 utilise `auth.purge_deleted_accounts`. **Correction :** corriger ces deux lignes.
- **M6 — mineur.** 2.9 (H60, Epic 2) teste le refus de retrait d'un Signalement `validé`, `assigné`, `collecté` ou `rejeté`, des Statuts produits par les Epics 4 et 5. **Correction :** ajouter, comme en 2.10, « Signalements de test insérés directement aux Statuts voulus (valeurs de `core/enums.py`) ».
- **M7 — mineur.** La question ouverte n° 2 (sauvegarde : service Compose ou tâche arq) reste ouverte alors que 8.12 tranche (« service planifié du profil `prod` »). **Correction :** clore la question n° 2 en renvoyant à 8.12, ou marquer ce critère de 8.12 comme provisoire.

---

## Ordre de correction conseillé

1. B1 (accès de l'Administrateur aux Signalements), puis A1, A2, A3, A5 (dépendances).
2. A4, A6 (traçabilité FR-23 et mesure de NFR-SM-3).
3. Mineurs M1 à M13.
4. Relancer le contrôle 5, puis passer `status: final` si aucun point bloquant ni à corriger ne reste.
