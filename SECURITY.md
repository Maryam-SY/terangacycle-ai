# Politique de sécurité

TerangaCycle AI traite des signalements géolocalisés, des photos et des numéros de téléphone. Une faille peut exposer des personnes réelles : merci de nous la signaler en privé.

## Signaler une vulnérabilité

Utilisez le **signalement privé de GitHub** : onglet **Security** du dépôt, puis **Report a vulnerability**. Seules les personnes qui maintiennent le dépôt voient votre rapport.

Décrivez, autant que possible :
- la partie concernée (API, PWA, bord Caddy, infrastructure, modèle d'IA) et la version ou le commit ;
- les étapes pour reproduire, et ce qu'un attaquant pourrait obtenir ;
- une proposition de correctif, si vous en avez une.

## Nos engagements

- **Accusé de réception sous 72 heures.**
- **Premier diagnostic sous 7 jours** : gravité retenue, versions touchées, suite prévue.
- Nous vous tenons informé·e jusqu'au correctif, et nous vous citons dans l'avis de sécurité si vous le souhaitez.

## Ce qu'il ne faut pas faire

- **Pas d'issue publique**, de pull request ni de message public tant que la faille n'est pas corrigée.
- **Pas de test sur des données réelles** : ni sur une instance déployée, ni sur les comptes ou les signalements d'autres personnes. Testez sur votre propre pile locale (`docker compose --profile demo up`, voir le [README](README.md)), avec des données factices.
- Pas de déni de service, d'ingénierie sociale ni d'accès physique.

## Versions couvertes

Le projet est en cours de développement : seule la branche `main` reçoit des correctifs de sécurité.
