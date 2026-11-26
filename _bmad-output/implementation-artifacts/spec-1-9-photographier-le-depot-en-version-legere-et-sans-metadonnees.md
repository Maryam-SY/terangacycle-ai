---
title: 'Story 1.9 — Photographier le dépôt en version légère et sans métadonnées'
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

**Problem:** L'écran 2 vérifie la Position, mais le Citoyen ne peut pas encore photographier le dépôt.

**Approach:** Mode allégé, décidé le 26/11/2026 pour tenir le parcours citoyen à 14 h : spec courte, tests essentiels, revue par l'agent seul. Sur l'écran 2 :
- la consigne « Ni personne ni plaque » est rappelée ;
- le déclencheur ouvre l'appareil photo arrière (`capture="environment"`) ;
- la photo est redressée, réduite et ré-encodée en JPEG ≤ 300 Ko sans métadonnées (canevas) ;
- un aperçu propose « Reprendre la photo » ou « Continuer ». « Continuer » garde le brouillon (photo, Position, précision, horodatage de l'appareil) pour l'écran 3.

</frozen-after-approval>

## Implementation Notes

- **`web/src/features/report/photo.ts`** :
  - `preparePhoto(file, codec)` essaie 1600, 1280, 1024, 800 puis 640 px de grand côté, à des qualités de 0,82 à 0,5, jusqu'à ≤ 307 200 octets ;
  - `createImageBitmap(..., { imageOrientation: 'from-image' })` applique l'orientation, et le canevas n'écrit aucune métadonnée ;
  - une photo non décodable (HEIC sur Chrome Android, fichier corrompu) lève `PhotoUnreadableError` : message « Cette photo n'a pas pu être lue. Reprenez-la. », rien n'est gardé ;
  - le codec est injectable (Vitest n'a pas de canevas).
- **`draft.ts`** : brouillon en mémoire seulement. Un rechargement le perd et l'écran 3 renvoie alors à la capture.
- **`CapturePage.tsx`** : consigne à bordure rouge (icône en `stroke-danger` : le rouge n'est jamais du texte), entrée fichier cachée ouverte par le bouton « Prendre la photo », états « préparation », « illisible » et « aperçu ». L'URL de l'aperçu est libérée à la reprise et en quittant l'écran.
- **`DetailsPage.tsx`** (`/signaler/details`) : écran 3 minimal (titre), complété par la story 1.13.
- **Textes** : `capture.rule`, `capture.photo`, `capture.preview` et `details.title`, en `fr` et `wo` ; `capture.photoSoon` est retiré.
- **Tests** :
  - Vitest `photo.test.ts` (8) : plafond, réduction progressive, pas d'agrandissement, refus HEIC, détection de l'APP1 ;
  - e2e `capture.spec.ts` : consigne, `capture="environment"`, aperçu, reprise, « Continuer » vers l'écran 3, photo illisible.
- **Vérifié** : oxlint et `tsc -b` sans avertissement, Vitest 123/123. Les tests e2e n'ont pas tourné localement au moment du commit (Chromium en cours d'installation) : ils tournent en CI.
- **Limite connue** : la conversion HEIC n'est pas faite sur Chrome Android, faute de décodeur natif. La photo est refusée avec le message prévu. Les appareils photo Android produisent du JPEG par défaut.
