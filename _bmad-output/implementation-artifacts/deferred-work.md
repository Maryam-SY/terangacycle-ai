# Travail différé

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-squelette-backend-et-docker-compose.md`
  summary: Les tests d'intégration (rôles PostgreSQL, PostGIS) sont ignorés en silence sans `TEST_APP_DATABASE_URL` et `TEST_MIGRATOR_DATABASE_URL`, et aucune CI ne démarre la pile pour les exécuter.
  evidence: `backend/tests/integration/test_db_roles.py` appelle `pytest.skip` quand les variables manquent ; `.github/workflows/` ne contient qu'un `.gitkeep`. À traiter par la story 1.4 (CI de qualité) : démarrer la pile en CI et faire échouer, au lieu d'ignorer, quand `-m integration` est demandé sans base.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-2-configuration-sondes-et-conventions-d-api.md`
  summary: Le masquage des journaux ne couvre ni le texte des exceptions ni les arguments positionnels des journaux des bibliothèques (SQLAlchemy, uvicorn).
  evidence: `format_exc_info` s'exécute après `mask_sensitive` dans `core/logging.py`, et les `%`-args sont déjà rendus dans `event`. À traiter avant la story 1.11, qui manipule les premières Positions et Identifiants d'appareil.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-3-coquille-pwa-et-bord-caddy.md`
  summary: Les tests de la PWA (`npm test`) ne tournent ni dans la construction de l'image Caddy ni en CI.
  evidence: `infra/caddy/Dockerfile` ne lance que `npm ci` et `npm run build`, et `.github/workflows/` est vide. À brancher par la story 1.4 (CI de qualité).

- source_spec: `_bmad-output/implementation-artifacts/spec-1-5-hygiene-du-depot-public.md`
  summary: Les verrous Trivy et pip-audit du job `audit` ne sont pas testés en négatif : rien ne prouve qu'ils échoueraient sur une vulnérabilité HIGH/CRITICAL.
  evidence: Un test négatif exige une image ou un verrou volontairement vulnérable. À ajouter si une régression du câblage (`--exit-code`, `|| status=1`) devient un risque.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-10-stocker-une-photo-sans-metadonnees-dans-le-bucket-prive.md`
  summary: Description vocale du dépôt (en wolof ou en français) pour le Citoyen qui ne sait pas lire ni écrire, en alternative au commentaire écrit de l'écran 3.
  evidence: Demandé par l'équipe le 25/11/2026 pendant la story 1.10 (backend seul). Concerne l'écran 3 et la création du Signalement (stories 1.11 et 1.13). Décidé le 25/11/2026 : note audio jointe (≈ 30 s, écoutée par le modérateur ou le collecteur), sans transcription. À cadrer : sans API d'IA étrangère (souveraineté), limite de durée et de poids, consentement au micro, stockage par `core.storage`.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-10-stocker-une-photo-sans-metadonnees-dans-le-bucket-prive.md`
  summary: `sprint-status.yaml` garde la story 1.8 en `in-progress` alors que sa spec est `done` et sa PR #12 fusionnée.
  evidence: Relevé en revue de la story 1.10 (B14) ; antérieur à cette story. À passer en `done` au prochain passage de `bmad-sprint-planning`.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-11-recevoir-un-signalement-anonyme-et-attribuer-son-numero-de-suivi.md`
  summary: Miniature de la photo de Signalement (tâche arq `thumb:<photo_id>` par `after_commit`, JPEG ≤ 30 Ko sous `report_thumb/<yyyy>/<mm>/<uuid>.jpg`, `report_photos.thumb_key`, rejeu sans second objet ; test sur 10 photos de 1 Mo), extraite de la story 1.11.
  evidence: Découpage décidé le 26/11/2026 (action ouverte « redécouper 1.11 ») : la 1.11 livre l'enregistrement du Signalement ; la colonne `thumb_key` nullable est créée par sa migration. À livrer juste après la 1.11.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-11-recevoir-un-signalement-anonyme-et-attribuer-son-numero-de-suivi.md`
  summary: Aucun test automatique d'aller-retour des migrations (upgrade, downgrade, upgrade, liste des tables) ; le downgrade de 0003 n'est vérifié qu'à la main.
  evidence: Revue de la 1.11 (V, B). Aucun test de migration dans le dépôt, pour 0001 et 0002 non plus : un test commun, en intégration, avec le rôle teranga_migrator.

- source_spec: `_bmad-output/implementation-artifacts/spec-1-11-recevoir-un-signalement-anonyme-et-attribuer-son-numero-de-suivi.md`
  summary: Limite de taille du corps de `POST /v1/reports` au bord HTTP (Caddy `request_body max_size`), au-dessus de 1 Mo pour la photo plus `meta`.
  evidence: Revue de la 1.11 (B, E) : python-multipart reçoit toute la partie avant la route ; la lecture bornée ne protège que la mémoire du service. Relève de la story 8.4 (bord HTTP durci).

- source_spec: `_bmad-output/implementation-artifacts/spec-1-13-completer-envoyer-et-voir-la-confirmation.md`
  summary: Client API généré depuis l'OpenAPI (`backend/scripts/export_openapi.py`, `openapi-typescript`, instance `openapi-fetch`), versionné et vérifié en CI, à la place du client écrit à la main `web/src/api/reports.ts`.
  evidence: Reporté le 26/11/2026 (mode allégé pour la démo de 14 h). Le contrat est couvert par les tests d'intégration du serveur et par `reports.test.ts`.
