# Journal des corrections — epics.md (suite à validation.md)

Date : 2026-11-23. Frontmatter inchangé (`status: draft`, `stepsCompleted: [1, 2, 3]`). Seul `epics.md` a été modifié.

## Bilan

- Bloquants : 11/11 appliqués.
- À corriger : 17/17 appliqués.
- Mineurs : 11/11 appliqués (aucun renvoyé en question ouverte).
- Stories : 92 → 100.

## Renumérotation

| Ancien | Nouveau | Motif |
|---|---|---|
| 1.1 | 1.1 Squelette backend et Docker Compose ; 1.2 Configuration, sondes et conventions d'API ; 1.3 Coquille PWA et bord Caddy | 3-A |
| 1.2 | 1.4 CI de qualité ; 1.5 Hygiène du dépôt public ; 1.6 Contrôles de contrat en CI | 3-B |
| 1.3 → 1.7, 1.4 → 1.8, 1.5 → 1.9 | décalage | |
| 1.6 | 1.10 Stocker une photo sans métadonnées ; 1.11 Recevoir un Signalement anonyme | 3-C (+ miniature 5-H dans 1.11) |
| 1.7 → 1.12, 1.8 → 1.13, 1.9 → 1.14, 1.10 → 1.15, 1.11 → 1.16, 1.12 → 1.17 | décalage | |
| 3.15 | 4.6 Export des Corrections consenties | 5-C |
| 3.16 | 3.15 | décalage |
| 3.17 | 4.11 Réentraînement mensuel (pilote) | conséquence de 5-C : sinon 3.x dépendrait de 4.6 |
| 4.6 → 4.7, 4.7 → 4.8 | décalage | |
| 4.8 | 4.9 S'abonner aux notifications push ; 4.10 Recevoir une notification push | 3-D |
| — | 5.11 Libérer la Mission `active` d'un Collecteur supprimé ou suspendu (H60, nouvelle) | 1-H, 5-M |
| 5.11 → 5.12, 5.12 → 5.13, 5.13 → 5.14, 5.14 → 5.15 | décalage | |
| 8.14 (dernier bloc) | 8.15 Restauration de sortie vers un autre hébergeur (nouvelle) | 3-F |

## Points appliqués (et écarts au rapport)

- 1-A : 5.1 crée `weight_estimates` + `estimated_weight()` ; question ouverte 8 ajoutée (valeurs provisoires).
- 1-B : critères de démo dans 4.4, 5.3, 5.6 ; règle FR-37 et carte de couverture → 4.4. Question ouverte 9 (Missions `completed` sans Preuve entre 5.3 et 5.6).
- 1-C : critère méta-test dans 2.9, 2.10, 4.6 (ex-3.15), 5.5, 5.9, 5.14 (ex-5.13), 7.5.
- 1-D : 2.8 (`terms_accepted_at`, `terms_version`).
- 1-E : `corrections.actor_ref` (3.11), écrit par 4.3, non exporté (4.6).
- 1-F : texte « notification = apparition en ≤ 15 s, aucune réaction » dans 5.9 et 9.5.
- 1-G : 2.5.
- 1-H : **écart** — placé dans la nouvelle story 5.11 (H60) et non dans 5.5 (H48), car `AccountDeleted` vient de 2.10 (H60) : 5.5 aurait dépendu d'une porte plus tardive.
- 1-I : 8.5. 1-J : 4.5 (photos de Signalement) et 5.6 (photos de Preuve).
- 2-A : 3.11. 2-B : intro de l'Epic 4 et 4.3. 2-C : 4.1 + ligne de cohérence. 2-D : 2.8 + prérequis Epic 4. 2-E : 4.1 crée `core.storage.signed_url()`.
- 3-A, 3-B, 3-C, 3-D, 3-F : découpages ci-dessus. 3-E : 8.11.
- 4-A : 1.13 propriétaire de `WasteTypeBadge`/`WasteTypePicker` et des jetons provisoires ; 3.8 réduite (présélection IA) ; 8.1 donne les valeurs définitives.
- 4-B : tableau des contrôles CI + 8.5. 4-C : 2.1, 2.5, 8.10 renvoient au test de la story 1.2 / 1.6. 4-D : porte de l'Epic 9.
- 5-A : `retention.sweep` créée par 1.16 (ex-1.11) ; 2.6 corrigée.
- 5-B : Frise propriété de 1.13 (ex-1.8), complétée par 4.7.
- 5-C : 3.15 → 4.6 (voir aussi 3.17 → 4.11).
- 5-D : émission de `ReportStatusChanged` déplacée en 4.2 ; 4.10 la consomme.
- 5-E : tuiles en 5.2 ; 8.7 copie seulement ; 7.4 cite 5.2.
- 5-F : 8.1 limitée à 3 écrans ; prérequis Epic 8 réécrit. **Écart** : 7.3 cite les jetons `--color-waste-*` de la story 1.13 (et non de 8.1), pour qu'aucune story de l'Epic 7 ne dépende de l'Epic 8.
- 5-G : 7.2 sans `contestée` ; critère déplacé en 7.7.
- 5-H : miniature dans 1.11 (`report_photos.thumb_key`) ; 5.1 y renvoie.
- 5-I : `display_name` créé par 2.3 ; 2.8 ne l'ajoute plus ; 5.5 avec repli sur l'identifiant court.
- 5-J : porte de 7.6 (prérequis 7.1 dans la ligne Porte, pour garder le format de story).
- 5-K : **écart** — au lieu d'un prérequis 5.14 → 7.1 (Epic 5 dépendant de l'Epic 7), la migration de `proof_reviews` (5.14) ne touche aucune vue ; c'est 7.7 (pilote) qui branche `v_mission_facts.review_status` sur `proof_reviews` et appelle `recreate_analytics_views()`.
- 5-L : 2.9 vérifie l'absence d'objet dans le bucket ; 5.9 crée `GET /v1/missions/assignable-collectors`.
- 5-M : réaction `CollectorSuspended` dans 5.11 ; 2.11 indique qu'aucune réaction n'est abonnée dans sa propre story.
- 5-N : 4.7 (File hors-ligne) et 2.10 (Signalements de test insérés aux Statuts voulus).

## Corrections supplémentaires (règle 4 : ordre, portes, propriétaire unique)

- `core.storage.purge()` sans propriétaire (utilisé par 2.9 H60 et 4.5 H48) : créé par 1.10, ligne de cohérence ajoutée avec `ingest_photo()`.
- Unité de travail, `after_commit`/`after_rollback`, worker arq + battement, `GET /v1/config` minimal : critères ajoutés à 1.2 (la règle de cohérence les donnait à 1.1 sans critère) ; 1.8 étend `GET /v1/config`.
- `report_photos.purged_at` (4.5) et `proofs.photos_purged_at` (5.6) : colonnes nommées et rattachées à leur story.
- Index GiST de `reports` : créé explicitement par 1.14 (plus de « s'il manque »).
- 4.7 : le lien « Créer un compte » est ajouté par 4.7, l'avertissement existe depuis 1.7.
- 4.1 : mentions « sans l'Epic 3 » supprimées (3.11 et 3.14 sont désormais prérequis).
- Prérequis des Epics 5, 7, 8 et 9 réécrits par porte (« Epics N livrés » incluait des stories pilote).
- Carte de couverture : FR-5 (5.11), FR-13 (4.6), FR-16 (4.11), FR-37 (4.4) ; Epic List : Epics 1, 4, 5, 8, 9.
- Questions ouvertes : références 1.4 → 1.8 ; ajout des questions 8 et 9.

---

# Passe 2 (validation-2.md)

Frontmatter inchangé. Aucune story ajoutée ni renumérotée : 100 stories.

- Bloquant : 1/1. À corriger : 6/6. Mineurs : 12/13 appliqués, M8 renvoyé en question ouverte n° 9.

## Bloquant
- B1 : 4.1 crée `GET /v1/staff/reports?status=` (Modérateur et Administrateur commune) et ouvre `GET /v1/moderation/reports/{id}` en lecture à l'Administrateur commune (File et décisions restent au Modérateur) ; 4.2 montre l'historique des Statuts au Modérateur et à l'Administrateur. 5.5 crée `GET /v1/missions/staff` (Missions avec nom affiché du Collecteur ; route du module `missions`, car `reports` ne peut pas importer `missions`). 5.5 et 5.9 citent ces routes. Lignes ajoutées au tableau des propriétaires.

## À corriger
- A1 : porte de 7.1 « H60 ; opt. H48 si 7.6 est tirée » ; paragraphe « Porte de l'Epic 7 » ; Epic List mise à jour ; porte de 7.6 reformulée.
- A2 : 1.2 crée `/metrics` (interne, compteurs par route et code HTTP) ; ligne au tableau (utilisée par 8.4, 8.11).
- A3 : 3.3 complète `/readyz` (Modèle courant chargé, `onnx_sha256` conforme ; test Modèle retiré → 503).
- A4 : 4.4 écrit l'identifiant d'origine dans le détail du motif de la ligne `report_status_events` du rejet (pas d'écrasement de `reports.duplicate_of_report_id`) ; 4.7 et 4.8 citent cette source.
- A5 : 5.3 ne charge que des Missions `active` ; 5.6 charge les Missions `completed` par `submit_proof()` ; question ouverte n° 9 (ancienne) supprimée ; règle FR-37 mise à jour.
- A6 : 3.12 mesure NFR-SM-3 (3 nouveaux utilisateurs × 10 essais, Android 2 Go, médiane < 30 s, consignée).

## Mineurs
- M1 : `notifications` créée par 4.10, 4.9 ne crée que `push_subscriptions`.
- M2 : 2.5 ouvre la liste des routes appareil avec `PUT /v1/device/consent` ; 2.8, 2.9, 4.8 y ajoutent leur route ; 1.6 réserve `GET /v1/public/map` à 7.6 ; paragraphe « Routes du principal appareil ».
- M3 : 3.5 reformulée (option testée, sans déclencheur futur).
- M4 : lignes `core.idempotency` (6.2 retirée, utilisatrices complètes) et `retention.sweep` (2.10 retirée) corrigées.
- M5 : propriétaires déclarés — `core.geo.expose()` 4.1, `core.security.principal()` et `core.demo.flag()` 1.11, `missions.service.photo_seen()` 5.13 ; lignes au tableau.
- M6 : 2.9 insère les Signalements de test aux Statuts voulus.
- M7 : question ouverte n° 2 close par renvoi à 8.12 (à confirmer à l'implémentation).
- M8 : **non appliqué** (redécoupage de 1.11, 1.13, 2.5 et 5.6 = nouvelle renumérotation des Epics 1 et 2) → question ouverte n° 9.
- M9 : paragraphe « Fichiers partagés entre epics » sous les règles de cohérence.
- M10 : Epic 8 noté « epic transverse d'exploitation assumé ».
- M11 : 2.1 lit `GET /v1/config` dans Dexie `meta` (story 1.8).
- M12 : 1.17 purge les `report_photos` rattachées aux Signalements `is_demo`.
- M13 : 3.12 envoie en `citizen_type` tout choix explicite fait sans présélection.
