---
title: 'Story 1.13 — Compléter, envoyer et voir la confirmation (avec note vocale)'
type: 'feature'
created: '2026-11-26'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Après la photo, le Citoyen ne peut ni décrire le dépôt ni l'envoyer, et ne reçoit pas son Numéro de suivi.

**Approach (mode allégé, décidé le 26/11/2026 pour la démo de 14 h) :**
- Écran 3 :
  - miniature de la photo ;
  - Taille de tas, obligatoire, sans présélection ;
  - `WasteTypePicker` facultatif, sans présélection, un choix pouvant être retiré ;
  - barre de description « comme WhatsApp », demandée par l'équipe : on écrit (compteur n/280, en points de code) ou, champ vide, on touche le micro pour parler en wolof ou en français, 30 s au plus ;
  - « Envoyer », désactivé avec sa raison annoncée tant que la Taille de tas manque.
- Envoi : `POST /v1/reports` avec la partie `voice` facultative.
- Écran 4 : remerciement, Numéro de suivi, Frise des 4 étapes (« Signalé » courant), étiquette « Données de démonstration », « Retour à l'accueil ».
- Serveur : note vocale contrôlée (WebM, Ogg ou MP4 d'après les octets, 600 Ko au plus), rangée dans le bucket privé sous `voice/<yyyy>/<mm>/<uuid>.<ext>`, clé gardée dans `reports.voice_key` (migration `0004_report_voice`).

**Reporté (deferred-work.md) :** client généré depuis l'OpenAPI et sa vérification en CI ; 200 sur un second envoi (story 1.12). Le double appui est déjà empêché : le bouton est désactivé pendant l'envoi.

</frozen-after-approval>

## Implementation Notes

- **Serveur** :
  - `core.storage.ingest_voice()` contrôle avant toute écriture : 413 `voice_too_large`, 415 `unsupported_voice_type`. L'audio n'est pas ré-encodé (les conteneurs ne portent ni position ni identité) ;
  - suppression par `after_rollback`, hors de la boucle asyncio ;
  - la note n'est rangée qu'après la photo, donc seulement si tout le reste est accepté ;
  - partie `voice` facultative dans la route, lue avec un plafond de 600 Ko + 1.
- **PWA** :
  - `api/reports.ts` : client écrit à la main, avec `X-Device-Id`, un délai de 30 s, et réseau ou 5xx → `network` ;
  - `features/classify/` : `WasteTypePicker` et `WasteTypeBadge` (coche + `aria-pressed`, 44 px), jetons provisoires `--color-waste-*` vérifiés à 3:1 sur `surface` et `mint` ;
  - `Composer.tsx` : textarea, ou micro quand le champ est vide (MediaRecorder, format choisi parmi webm/opus, webm, ogg, mp4 ; arrêt automatique à 30 s ; écoute et suppression de la note). Le micro n'est demandé qu'au toucher ; s'il est refusé, un message propose d'écrire ;
  - `DetailsPage.tsx` : envoi avec le consentement lu dans Dexie. `consent_required` ramène au consentement ; une erreur de photo ou `outside_active_zone` propose de revenir à la photo ; en cas d'erreur réseau, la saisie est gardée et le bouton devient « Réessayer » ;
  - `ConfirmationPage.tsx` : `TrackingTimeline` en liste ordonnée, étape courante marquée par `aria-current="step"`, une coche et un libellé ;
  - `draft.ts` : `clientUuid` (UUID v4) attribué à la création du brouillon (écran 2), et dernier Signalement accepté pour l'écran 4.
- **Confidentialité** : la consigne sous la barre dit de ne citer ni nom ni numéro de téléphone.
- **Tests** :
  - pytest : `sniff_voice`, contrôles avant stockage, rollback, note stockée et liée, refus sans écriture ;
  - Vitest : `composer.test.ts`, `reports.test.ts` ;
  - Playwright : parcours écran 3 → 4 (Taille exigée, micro remplacé par la saisie, envoi, numéro, frise, étiquette démo), hors Zone et panne réseau avec saisie gardée.
