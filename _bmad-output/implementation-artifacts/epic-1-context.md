# Epic 1 Context: Signaler un dépôt

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->
<!-- Régénéré le 25/11/2026 après la Sprint Change Proposal « TerangaCycle 2.0 » (organisations dès 1.11, story 1.18). -->

## Goal

Permettre à un Citoyen anonyme de donner son consentement, de photographier un dépôt sauvage avec sa Position dans la Zone active (Dakar) et de recevoir un Numéro de suivi, sur une instance de démonstration clairement étiquetée. Depuis la v2.0, chaque Signalement est rattaché dès sa création à son **Organisation responsable** (commune ou opérateur dont la Zone couvre la Position, sinon l'Organisation plateforme), parce que la table `reports` naît dans cet epic et que le cloisonnement par Organisation est exigé dès le MVP. L'epic pose aussi tout le socle du projet : squelette backend et Docker Compose, configuration et conventions d'API, coquille PWA derrière Caddy, et une CI bloquante dès la porte H24. Dans cet epic, la Classification IA n'existe pas encore : le Type de déchet est choisi par le Citoyen ou laissé vide. Aucune story ne dépend d'un epic ultérieur. **Priorité :** P0 (toutes les stories).

## Stories

- Story 1.1 : Squelette backend et Docker Compose
- Story 1.2 : Configuration, sondes et conventions d'API
- Story 1.3 : Coquille PWA et bord Caddy
- Story 1.4 : CI de qualité
- Story 1.5 : Hygiène du dépôt public
- Story 1.6 : Contrôles de contrat en CI
- Story 1.7 : Accueil et consentement avant la première capture
- Story 1.8 : Vérifier la Position et la Zone active avant la photo
- Story 1.9 : Photographier le dépôt en version légère et sans métadonnées
- Story 1.10 : Stocker une photo sans métadonnées dans le bucket privé
- Story 1.11 : Recevoir un Signalement anonyme et attribuer son Numéro de suivi
- Story 1.12 : Renvoyer un Signalement sans doublon ni fuite
- Story 1.13 : Compléter, envoyer et voir la confirmation
- Story 1.14 : Repérer les Doublons probables à la réception
- Story 1.15 : Limiter les abus de signalement
- Story 1.16 : Retirer son consentement au réentraînement
- Story 1.17 : Charger et retirer les Données de démonstration en une commande
- Story 1.18 : Produire la miniature d'une photo de Signalement (sortie de 1.11 le 25/11/2026)

État au 25/11/2026 : 1.1 à 1.9 terminées ; prochaine story : 1.10 (inchangée), puis 1.11 (modifiée).

## Requirements & Constraints

- **Consentement d'abord** : avant la première capture, écran de consentement (géolocalisation, envoi de la photo, usage pour le Modèle en case séparée non cochée, consigne « ni personne ni plaque », avertissement que l'anonyme perd sa liste en réinstallant). Rien n'est demandé (géolocalisation, caméra) ni envoyé avant acceptation. Le refus du réentraînement ne bloque jamais le signalement ; le choix est copié sur chaque Signalement et révocable à tout moment (le retrait s'applique aux Signalements passés et futurs ; un nouvel accord ne vaut que pour le futur).
- **Signalement** : photo, Position (avec précision) et Taille de tas obligatoires ; commentaire ≤ 280 points de code ; Type de déchet facultatif. Position hors Zone active refusée dès l'écran de capture, avant la photo, et par le serveur (422). Précision > 50 m : invitation à patienter, envoi possible avec drapeau « position imprécise » (50 m exactement : pas de drapeau). Statut initial `pending_review` ; Zone (quartier, sinon commune) déduite par le serveur.
- **Organisation responsable (v2.0, FR-44, FR-47)** : `reports.organization_id NOT NULL`, fixé à la création par `orgs.service.responsible_org()` (Organisation `active` de type commune ou opérateur dont la Zone couvre la Position, la plus précise d'abord ; sinon l'Organisation plateforme), jamais renvoyé au Citoyen ni modifiable. La recherche de Doublon probable par proximité se limite à la même Organisation ; la recherche par photo identique reste globale.
- **Numéro de suivi** `TC-AAAA-NNNNNN` attribué par le serveur, unique même en création simultanée, année = année de réception UTC.
- **Photo** : compressée sur l'appareil en JPEG ≤ 300 Ko sans EXIF/GPS (HEIC converti ; prise de vue directe, pas d'import galerie). Serveur : JPEG/PNG/WebP seulement (415), > 1 Mo → 413, > 12 Mpx ou corrompue → 422 ; ré-encodage sans métadonnées ; aucun objet orphelin en cas d'échec.
- **Idempotence** : un renvoi par le même auteur avec le même Identifiant client renvoie l'existant (201 puis 200, même Numéro, aucune modification) ; un autre auteur avec le même Identifiant client reçoit 409 sans aucune donnée du Signalement.
- **Doublon probable** : photo strictement identique, ou Signalement non terminal à ≤ 50 m reçu depuis < 72 h ; marque calculée une fois à la création ; la réponse au Citoyen ne révèle jamais l'existence d'un autre Signalement.
- **Anti-abus** : 10 Signalements/h par appareil, par IP et par compte ; 60 req/min par Utilisateur connecté ; 429 `rate_limited` + `Retry-After` ; compteurs persistants au redémarrage ; un renvoi idempotent ne consomme pas de quota ; IP lue uniquement via le proxy de confiance.
- **Données de démonstration** : chargement et retrait en une commande, refusés en production ; `demo load` crée d'abord au moins deux Organisations communes de démonstration et y répartit les Signalements ; `demo purge` ne retire jamais l'Organisation plateforme ; tout ce qui est créé en Mode démonstration est étiqueté `is_demo` ; aucun chiffre de démonstration présenté comme réel.
- **Minimisation et confidentialité** : aucune coordonnée, Identifiant d'appareil, jeton ou numéro dans les journaux ni la console ; `owner_key` et empreintes jamais renvoyés.
- **Non-fonctionnel** : accueil ≤ 500 Ko hors images et Modèle ; PWA installable ; Android 8+ Chrome 2 Go, 390×844 ; WCAG 2.1 AA (4,5:1 / 3:1, cibles ≥ 44 px) ; aucune chaîne en dur (fr d'abord, wo prêt) ; couverture backend ≥ 60 % ; parcours écran 1 → 4 visé en < 30 s.

## Technical Decisions

- **Monolithe modulaire écrit à la main** (pas de starter full-stack, pas de SQLModel) : `backend/app/core` + modules `auth, orgs, reports, missions, enterprise, finance, lots, analytics, ai, notifications` (v2.0 : `orgs` est créé par la story 1.11 ; `enterprise` et `finance` viendront avec les Epics 11 et 12), trois couches `router → service → repository`. Un module n'importe d'un autre que son `service`, selon les flèches autorisées (ex. `reports → auth`, et en v2.0 `reports → orgs`, seule flèche ajoutée par 1.11) ; `core` sans règle métier ni import de module ; contrôlé par import-linter (1.11 ajoute `app.modules.orgs` aux conteneurs `layers`).
- **Propriété des tables** : `orgs` possède `organizations` (v2.0 ; types `commune`, `operator`, `collector_group`, `enterprise`, `recycler`, `platform` ; `zone_id` obligatoire pour une commune ; ligne système de l'Organisation plateforme à UUID fixe, insérée par la migration de 1.11, jamais `is_demo`) ; `auth` possède `devices` ; `reports` possède `reports`, `report_photos`, `tracking_counters` ; `core/geo` possède `zones` (lecture seule pour l'API) ; `core/idempotency` possède `idempotency_records`.
- **Base** : PostgreSQL 16 + PostGIS, `GEOGRAPHY(Point|MultiPolygon, 4326)`, `ST_Covers` (limite incluse) et `ST_DWithin` sur `geography`. Alembic seul chemin de schéma. Rôles `teranga_migrator` (propriétaire) et `teranga_app` (DML seul) **créés par un script `docker-entrypoint-initdb.d`, hors Alembic**.
- **Unité de travail** : une transaction par requête ou tâche, services `@transactional`, jamais de `commit/rollback/begin` dans service ou repository ; effets externes par `after_commit`, nettoyages par `after_rollback`.
- **Le serveur fait autorité** : horodatages via `core.clock` (simulable), Numéro de suivi par compteur annuel `INSERT … ON CONFLICT`, appartenance à la Zone, drapeaux ; valeurs client gardées à part.
- **Identité anonyme** : `X-Device-Id` = 32 octets aléatoires base64url (43 car., sinon 400) stocké dans Dexie `meta` ; `owner_key = device:<HMAC-SHA256(DEVICE_ID_PEPPER, id)>` via le principal unique `core.security.principal()`. `Authorization` invalide → 401.
- **API** : préfixe `/v1`, enveloppe d'erreur unique, codes en énumération (`core/errors/codes.py`), chacun avec un message `errors.<code>` en `fr.json` ; énumérations uniques dans `core/enums.py` (code en anglais). Création de Signalement en `multipart/form-data` (`meta` + `photo`), exemptée d'`Idempotency-Key` ; toute autre mutation l'exige. Liste blanche publique close : `/healthz`, `/readyz`, `GET /v1/config`, `POST /v1/reports`, `GET /v1/public/map` (réservée à plus tard).
- **Configuration** : tout via `core.config.Settings`, `ENV ∈ {dev, demo, prod}`, `DEMO_MODE` interdit en prod, un réglage nommé par seuil (`REPORT_ACCURACY_FLAG_M`, `DUPLICATE_RADIUS_M`, `DUPLICATE_WINDOW_H`, plafonds de débit, `ACTIVE_ZONE_ID`) ; secrets lus dans `/run/secrets/`, absents → refus de démarrer hors `dev`. `GET /v1/config` public expose `demo_mode`, `env`, `model_version`, la Zone active (polygone simplifié) et le seuil de précision.
- **Stockage** : seul `core/storage` parle S3 (Garage, bucket privé) ; `ingest_photo()` et `purge()` ; clés `<kind>/<yyyy>/<mm>/<uuid>.jpg` ; miniature ≤ 30 Ko en tâche arq `thumb:<photo_id>` (story 1.18 ; la colonne `report_photos.thumb_key` est créée par 1.11).
- **Asynchrone** : worker arq (même image) ; événements entre modules via `core/events.py`, réactions idempotentes dans `reactions.py` ; tâche planifiée `retention.sweep`.
- **Débit** : `core.ratelimit.limit(scope)` sur Valkey AOF, clés hachées ; uvicorn `--proxy-headers` restreint à l'IP de Caddy, qui remplace `X-Forwarded-For`.
- **Infra** : un seul `docker-compose.yml` (profils `demo`/`prod`), images épinglées par `@sha256:`, healthchecks sans `curl`. Caddy sert `APP_HOST` (PWA + `/v1`) et `MEDIA_HOST` (photos) ; `/metrics` et `/v1/ai/*` jamais exposés ; `/docs` et `/openapi.json` absents en prod.
- **PWA** : `create-vite` (react-ts) + `vite-plugin-pwa`, Tailwind 4 via un seul bloc `@theme` (`web/src/theme/theme.css`, ni `tailwind.config.js` ni `@config`), i18next, Dexie, TanStack Query ; **routage par `react-router` 8** (décidé le 2026-11-24). Client API généré depuis l'OpenAPI (`openapi-typescript` + une instance `openapi-fetch` enveloppée), versionné et vérifié en CI ; `fetch` interdit hors `web/src/api/` et `web/src/offline/`.
- **Versions et tests** : versions exactes de la Stack d'architecture, épinglées avec fichiers de verrouillage ; pytest sur PostGIS, Valkey et Garage réels, sans mock de base pour les règles métier.

## UX & Interaction Patterns

- Écrans de la maquette : 1 · Accueil (bouton « Signaler un dépôt », accès Réglages), 2 · Capture (Position ± N m, consigne « ni personne ni plaque » à chaque capture, message « TerangaCycle n'est pas encore actif ici » avant la photo, invitation en Ambre si > 50 m avec « Continuer quand même »), 3 · Résultat IA **adapté sans IA** (miniature, Taille de tas, `WasteTypePicker` facultatif, commentaire « n/280 », « Envoyer » désactivé avec raison annoncée), 4 · Confirmation (remerciement, Numéro de suivi, Frise de suivi à l'étape « Signalé »).
- Hors maquette, à concevoir avec les mêmes jetons et la police Inter : consentement, sélecteur de Taille de tas, Réglages (interrupteur du réentraînement), étiquette « Données de démonstration ».
- Jetons : Vert marque `#187A50` (jamais `#1F8A5B`), Rouge `#D9482B` seulement en aplat/icône/bordure/grand texte gras, Jaune `#F2B705` jamais en texte, avertissement en Ambre `#7A5C00` sur `#FFF4CC` ; message d'erreur en Encre avec icône rouge. Couleurs des Types de déchet provisoires (`--color-waste-*`).
- Ton : français simple, remercier, ne jamais culpabiliser, chaque erreur dit quoi faire (ex. 429 : « Réessayez dans N min. » ; erreur réseau : saisie gardée + « Réessayer »). État sélectionné signalé autrement que par la couleur ; Frise en liste ordonnée lisible par lecteur d'écran.

## Cross-Story Dependencies

- Ordre du socle : 1.1 → 1.2 → 1.3, puis CI 1.4 à 1.6 ; les stories fonctionnelles 1.7 à 1.17 s'appuient dessus.
- Briques partagées dont cet epic est propriétaire (les epics suivants les réutilisent sans les recréer) : unité de travail, `after_commit`, worker et `GET /v1/config` (1.2) ; `/metrics` (1.2) ; `ingest_photo()`/`purge()` (1.10) ; `principal()`, `core.demo.flag()`, table `organizations` et `orgs.service.responsible_org()` (1.11) ; tâche de miniature (1.18) ; Frise de suivi et `WasteTypeBadge`/`WasteTypePicker` (1.13) ; `core.idempotency`, `core/events.py` + `reactions.py`, `retention.sweep` (1.16) ; commande `demo load|purge` extensible par module (1.17).
- Chaîne fonctionnelle : 1.8 (table `zones`, `core.geo`) → 1.11 (création, Organisation responsable) → 1.18 (miniature) ;
- 1.11 → 1.12 (unicité `(owner_key, client_uuid)`) → 1.14 (doublons) / 1.15 (débit) ; 1.9 et 1.10 alimentent 1.11 ; 1.13 consomme l'API de 1.11 et le client généré.
- Vers d'autres epics : Appartenances, rôles par Organisation, Super Admin et console (Epic 2, stories 2.13 à 2.15) ; comptes de test (Epic 2), IA sur l'écran 3 (Epic 3), état `rejeté` de la Frise (Epic 4), File hors-ligne (Epic 6), couleurs définitives des déchets (Epic 8).
- **Point tranché** : les polygones des Zones de Dakar viennent d'OpenStreetMap (licence ODbL), chargés par la migration `0002_zones` de la story 1.8 (source et commande de reconstruction dans `backend/migrations/data/README.md`).
