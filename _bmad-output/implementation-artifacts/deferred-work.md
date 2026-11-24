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
