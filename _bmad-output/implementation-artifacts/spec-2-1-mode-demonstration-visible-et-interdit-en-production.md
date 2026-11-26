---
title: 'Story 2.1 — Mode démonstration visible et interdit en production'
type: 'feature'
created: '2026-11-26'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Rien n'indique à l'écran que l'instance tourne en Mode démonstration. Le jury pourrait prendre des Données de démonstration pour des données réelles.

**Approach (mode allégé, 26/11/2026) :**
- Un bandeau « Mode démonstration » s'affiche en haut de tous les écrans quand `GET /v1/config` renvoie `demo_mode = true`.
- Il n'a pas de bouton de fermeture et forme une région nommée pour les lecteurs d'écran.
- Hors ligne, il suit la configuration gardée dans Dexie.
- Le refus de démarrage `ENV` × `DEMO_MODE` existe déjà.

</frozen-after-approval>

## Implementation Notes

- **Bandeau** :
  - `web/src/ui/AppLayout.tsx` : `DemoBanner`, en Encre sur Jaune (paire `ink/accent` déjà vérifiée à 4,5:1 par `contrast.test`) ;
  - route parente de la table des routes : tous les écrans l'ont ;
  - il lit `usePublicConfig` (configuration gardée d'abord, puis réseau).
- **Serveur** : les 6 combinaisons `ENV` × `DEMO_MODE` sont déjà couvertes par `tests/unit/test_config.py` (4 acceptées, 2 refusées). L'API et le worker passent par la même `load_settings_or_exit()`.
- **Tests e2e** : bandeau sur la capture et l'accueil, sans bouton, sans violation axe ; aucun bandeau quand `demo_mode = false`.
- **Vérifié** : `tsc` et oxlint propres, Vitest 132/132, Playwright 34/34, budget 303,8 Ko sur 500.
