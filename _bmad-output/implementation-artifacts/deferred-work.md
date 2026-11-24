# Travail différé

- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-squelette-backend-et-docker-compose.md`
  summary: Les tests d'intégration (rôles PostgreSQL, PostGIS) sont ignorés en silence sans `TEST_APP_DATABASE_URL` et `TEST_MIGRATOR_DATABASE_URL`, et aucune CI ne démarre la pile pour les exécuter.
  evidence: `backend/tests/integration/test_db_roles.py` appelle `pytest.skip` quand les variables manquent ; `.github/workflows/` ne contient qu'un `.gitkeep`. À traiter par la story 1.4 (CI de qualité) : démarrer la pile en CI et faire échouer, au lieu d'ignorer, quand `-m integration` est demandé sans base.
