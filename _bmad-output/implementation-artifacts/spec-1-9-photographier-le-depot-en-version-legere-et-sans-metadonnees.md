---
title: 'Story 1.9 — Photographier le dépôt en version légère et sans métadonnées'
type: 'feature'
created: '2026-11-25'
status: 'done'
baseline_commit: 'b9c589bf643e6efed5c241af3a2fd9eadd2c9d6d'
route: 'dispatch'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-1-8-verifier-la-position-et-la-zone-active-avant-la-photo.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Sur l'écran 2 · Capture, le déclencheur « Prendre la photo » ne fait encore rien. Le Citoyen ne peut donc pas joindre de photo à son signalement. Or une photo brute de téléphone (environ 4 Mo, avec EXIF et GPS) coûterait cher en données mobiles et exposerait des métadonnées cachées.

**Approach:**
- **Prise de vue :** le déclencheur ouvre l'appareil photo arrière par une prise de vue directe, `<input type="file" accept="image/*" capture="environment">`.
- **Traitement sur l'appareil :**
  - décodage par le navigateur, ce qui convertit le HEIC là où il est lu ;
  - application de l'orientation ;
  - réduction et ré-encodage en JPEG d'au plus 307 200 octets par un canevas, qui n'écrit aucune métadonnée.
- **Aperçu :** il propose « Reprendre la photo » ou « Continuer ».
- **Brouillon :** « Continuer » enregistre dans Dexie la photo avec la Position, la précision et l'horodatage de l'appareil, puis ouvre l'écran 3, qui reste provisoire.

## Boundaries & Constraints

**Always:**
- **Consigne :** « Ni personne ni plaque » est visible avec son pictogramme à chaque capture, reprise comprise. Le déclencheur a une cible d'au moins 44 px, un pictogramme et un libellé. Il reste soumis au verdict de la story 1.8.
- **JPEG produit :**
  - au plus 307 200 octets ;
  - orientation appliquée ;
  - aucun segment APP1 (Exif ni XMP).
  - Ce sont ces octets exacts qui sont gardés en brouillon, puis envoyés : aucun ré-encodage plus tard.
- **Format visé :** côté le plus long de 1 600 px au plus. La qualité baisse par paliers, puis les dimensions, jusqu'à tenir sous la limite.
- **Décodage :** `createImageBitmap(file, { imageOrientation: 'from-image' })`. Une image `<img>` sert de repli. Tout échec de lecture, HEIC compris, affiche « Cette photo n'a pas pu être lue. Reprenez-la. », et rien n'est gardé.
- **Prise de vue directe :** une photo dont `lastModified` date de plus de 10 minutes avant le choix est refusée, comme une photo venue de la galerie, avec un message qui invite à photographier maintenant. Le fichier original n'est jamais stocké.
- **Brouillon :**
  - clé Dexie `meta.draft` : `{ photo: Blob, lat, lng, accuracy, capturedAt }`, où `capturedAt` est l'horodatage ISO de l'appareil au moment de la prise ;
  - la Position est la dernière mesure au moment où le fichier arrive ;
  - l'écran 3 (`/signaler/details`) lit ce brouillon ; sans brouillon, il renvoie vers la capture.
- **Aperçu :** il porte un texte alternatif. « Reprendre la photo » efface l'aperçu et fait réapparaître la consigne.
- **Confidentialité :** aucune coordonnée ni aucun octet de photo dans la console. Rien n'est envoyé au réseau dans cette story.
- **Textes et couleurs :** tout texte passe par i18next, en `fr` et `wo` ; couleurs par jetons ; aucune nouvelle dépendance.

**Never:**
- pas de viseur en direct (`getUserMedia`) ;
- pas d'import depuis la galerie ;
- pas de bibliothèque HEIC en WebAssembly ;
- pas d'envoi, de Taille de tas ni de commentaire : c'est l'écran 3, story 1.13 ;
- pas de file hors-ligne ;
- pas de stockage serveur : c'est la story 1.10.

## I/O & Edge-Case Matrix

| Scénario | Entrée / état | Comportement attendu |
|---|---|---|
| Photo normale | JPEG de 12 Mpx, environ 4 Mo, EXIF avec GPS, orientation 6 | Aperçu en portrait ; JPEG d'au plus 307 200 octets, sans APP1 |
| HEIC lisible | HEIC décodé par le navigateur | Converti en JPEG, puis même traitement |
| Fichier illisible | HEIC non pris en charge, ou octets corrompus | « Cette photo n'a pas pu être lue. Reprenez-la. » ; aucun brouillon |
| Photo ancienne | `lastModified` de plus de 10 minutes | Refusée avec un message ; aucun brouillon |
| Reprise | « Reprendre la photo » | Aperçu effacé, consigne visible, déclencheur actif |
| Continuer | Aperçu affiché | `meta.draft` complet ; navigation vers `/signaler/details` |
| Lien direct | `/signaler/details` sans brouillon | Redirection vers la capture |
| Déclencheur inactif | Position hors Zone ou imprécise sans « Continuer quand même » | Aucune prise de vue possible (story 1.8 inchangée) |

</frozen-after-approval>

## Code Map

- **`web/src/features/report/CapturePage.tsx` (`CaptureScreen`) :**
  - le déclencheur est déjà là (`ready`, `photoRequested`, `capture.photoSoon`, devenu caduc) ;
  - la région annoncée `role="status"` est à garder ;
  - `usePosition()` fournit la dernière mesure.
- **`web/src/features/report/capture.ts` :** `assessCapture` et `canTakePhoto`, à réutiliser sans les changer.
- **`web/src/offline/db.ts` :** `MetaKey`, `getMeta` et `setMeta`. Ajouter `'draft'`. Un `Blob` se stocke tel quel dans IndexedDB.
- **`web/src/ui/icons.tsx` :** `NoPersonIcon` sert déjà à la consigne du consentement. Ajouter une icône d'appareil photo si elle manque, en réutilisant celle de l'accueil s'il y en a une.
- **`web/src/paths.ts` et `web/src/routes.tsx` :** ajouter `details: '/signaler/details'` et sa page provisoire.
- **`web/src/i18n/{fr,wo}.json` :** les clés `capture.*` ; retirer `capture.photoSoon`.
- **`web/src/theme/contrast-pairs.json` :** toute nouvelle paire texte/fond.
- **`web/e2e/capture.spec.ts` :**
  - modèle des tests : géolocalisation simulée, `/v1/config` intercepté, axe, aucune requête sortante ;
  - `setInputFiles` accepte un `Buffer`. Un JPEG de 4000 × 3000 avec un APP1 Exif (orientation 6 et GPS) peut être fabriqué dans le navigateur (canevas bruité, `toBlob`, insertion d'un segment APP1 construit à la main), puis renvoyé au test.
- **`web/scripts/check-size.mjs` :** budget de 500 Ko à respecter.

## Tasks & Acceptance

**Execution:**
- [x] `web/src/features/report/photo.ts` :
  - `processPhoto(file, now)` : décodage avec orientation, réduction, boucle qualité puis dimensions, résultat `{ blob, width, height }` ;
  - `readJpegSegments(bytes)` / `hasApp1(bytes)` : parcours des marqueurs JPEG ;
  - erreurs typées `UnreadablePhotoError` et `StalePhotoError`.
- [x] `web/src/offline/draft.ts` : `saveDraft`, `getDraft`, `clearDraft` dans `meta.draft`, avec validation de forme à la lecture.
- [x] `web/src/features/report/CapturePage.tsx` :
  - consigne et pictogramme ;
  - déclencheur relié à l'`<input capture="environment">` caché ;
  - états traitement, aperçu et erreur ;
  - « Reprendre la photo » et « Continuer » (brouillon, puis navigation).
- [x] `web/src/features/report/DetailsPage.tsx`, avec `paths.ts` et `routes.tsx` : écran 3 provisoire, aperçu du brouillon et retour ; redirection vers la capture sans brouillon.
- [x] i18n `fr`/`wo`, icônes et paires de contraste.
- [x] **Tests :**
  - Vitest : `readJpegSegments` et `hasApp1` sur des octets synthétiques (avec et sans APP1, JPEG tronqué), `StalePhotoError`, validation du brouillon ;
  - Playwright, dans un vrai Chromium : chaque ligne de la matrice, en particulier le JPEG de 12 Mpx (au plus 307 200 octets, sans APP1, portrait après l'orientation 6, octets du brouillon identiques à ceux de l'aperçu), axe dans chaque état, et aucune requête ni coordonnée qui sort.

**Acceptance Criteria:**
- Étant donné un brouillon enregistré, quand on relit `meta.draft`, alors ses octets sont exactement le JPEG produit par `processPhoto`, avec la Position, la précision et `capturedAt` de la prise.
- Étant donné l'écran 2 prêt, quand on inspecte le déclencheur, alors l'`<input>` porte `accept="image/*"` et `capture="environment"`, et la cible fait au moins 44 px.

## Implementation Notes

- **Traitement.** `processPhoto` : refus d'ancienneté avant tout décodage ; `createImageBitmap(…, { imageOrientation: 'from-image' })`, repli `<img>` ; fond blanc (PNG transparent) ; qualités 0,85 → 0,55 par paliers de 0,1, puis côtés ×0,8, abandon sous 320 px (`UnreadablePhotoError`). Chaque JPEG du canevas est relu (`readJpegSegments`, EOI final exigé) et tout segment de métadonnées retiré (`withoutMetadata` : tout APPn sauf APP0 et l'APP2 « ICC_PROFILE », et tout COM) avant la mesure du poids : les octets mesurés sont ceux gardés. Le canevas de Chromium écrit APP0 (JFIF) et APP2 (profil ICC sRVB, sans donnée personnelle), gardés. Prise refusée si `lastModified` s'écarte de plus de 10 min de l'arrivée, dans un sens ou l'autre ; `capturedAt` = `min(lastModified, arrivée)`.
- **Vérifié dans Chromium (volet navigateur, page jetable hors dépôt).** JPEG de 4000 × 3000 bruité, 4,4 Mo, APP1 Exif (orientation 6, GPS) → 1200 × 1600, 190 Ko, marqueurs `e0 e2 db db c0 c4… da`, sans APP1, en 0,3 s ; PNG 1200 × 900 → JPEG ; octets corrompus et faux HEIC → `UnreadablePhotoError`.
- **Position à l'arrivée du fichier.** Revérifiée : hors Zone, erreur, configuration absente ou mesure de plus de 2 min (`MAX_PHOTO_FIX_AGE_MS`, le suivi s'arrête souvent pendant que l'appareil photo est ouvert) → refus (`capture.photo.position`) ; devenue imprécise pendant la prise de vue → acceptée avec cette précision (le serveur posera le drapeau, story 1.11). L'`<input>` caché n'est désactivé que pendant le traitement et l'aperçu, pas selon la Position : une mesure qui change pendant la prise de vue ne fait pas perdre la photo. Le déclencheur reste soumis au verdict de la story 1.8.
- **Brouillon.** Une nouvelle photo efface l'ancien brouillon dès son arrivée (« aucun brouillon » après un refus). `saveDraft` valide aussi avant d'écrire. `getDraft` efface un brouillon pris il y a plus de 24 h ou daté de plus de 10 min dans le futur. L'écran 3 a la même garde de consentement que la capture. L'écran 3 n'affiche que la précision, jamais les coordonnées.
- **Accessibilité.** Une seule région `role="status"` : annonce de la photo (traitement, aperçu, refus) sinon celle du verdict. Focus sur le message de traitement, puis sur l'aperçu (rendu seulement une fois son URL créée), sur le message d'erreur (refus ou enregistrement impossible), et sur le déclencheur après « Reprendre la photo » (le titre s'il est désactivé).
- **Vérification locale.** Conteneur Node 26 : Vitest (photo, draft, App, i18n : 67 tests) vert, `tsc -b` vert, oxlint sans erreur (un avertissement `set-state-in-effect` sur `useObjectUrl`, voulu : URL créée et révoquée dans l'effet, sûr en StrictMode), `playwright test --list` : 43 tests. Le volume `tc-ci-web-node-modules` n'a plus les liaisons natives `@rolldown/binding-linux-x64-gnu` ni `@oxlint/binding-linux-x64-gnu` (modifié vers 18 h 08 UTC le 25/11, hors de cette story) : Vitest et oxlint ont tourné sur une copie jetable du volume complétée par les liaisons de mêmes versions de `web/node_modules`. Playwright complet en CI seulement (pas de Chromium local).

## Spec Change Log

## Review Triage Log

Passe 1 (25/11/2026). Couches : Blind Hunter (B), Edge Case Hunter (E), Verification Gap (V).

| # | Constat | Verdict | Preuve | Route |
|---|---|---|---|---|
| B2 / E1 | `/signaler/details` montre le brouillon sans consentement à jour | medium | `DetailsPage` ne passe pas par `useCurrentConsent`, contrairement à `CapturePage` | patch (P1) |
| B3 / E2 | Brouillon (photo, Position exacte) gardé sans limite | medium | Seule une nouvelle photo l'efface ; aucune expiration sur `capturedAt` | patch (P1) |
| B6 | Position de la photo potentiellement ancienne | medium | `receivePhoto` ignore `fixedAt` ; `watchPosition` est souvent suspendu pendant la prise de vue | patch (P2) |
| B7 | `capturedAt` = arrivée du fichier, pas la prise de vue | low | `now` dans `receivePhoto` ; `lastModified` disponible ; correction directe | patch (P2) |
| B8 | `lastModified` dans le futur accepté sans borne | low | `assertFreshPhoto` ne borne que le passé ; correction directe | patch (P2) |
| B5 / B12 / E3 | Focus perdu pendant le traitement et sur les erreurs ; déclencheur désactivé visé | medium | Le bouton focalisé devient `disabled` ; les erreurs ne posent pas `pendingFocus` | patch (P3) |
| B4 | « Retour à la photo » ne réaffiche pas la photo | low | `CaptureScreen` démarre toujours à `idle` ; libellé trompeur, correction directe | patch (P3) |
| B11 | `<img>` sans `src` au premier rendu | low | `useObjectUrl` renvoie `undefined` d'abord ; correction directe | patch (P3) |
| B14 | Seul APP1 est retiré ; la promesse est « aucune métadonnée » | low | `withoutApp1` ignore APP13 et COM ; même fonction, correction directe | patch (P4) |
| V1 | Effacement de l'ancien brouillon par une nouvelle photo non testé | medium | Aucun test n'a de brouillon avant un refus | patch (P5) |
| V2 / B13 | Échec d'enregistrement de « Continuer » non testé | medium | Aucun test ne fait échouer `saveDraft` depuis l'écran | patch (P5) |
| E7 | Android peut décharger la page pendant que l'appareil photo est ouvert | medium (non vérifié) | Photo et Position perdues sans explication ; demande un état persistant avant l'ouverture de l'appareil | defer |
| B1 | `wo.json` copie de `fr.json` | false | Interface wolof hors objectifs du hackathon (NFR-P3) ; seules les clés comptent (UX-DR-8) | rejeté |
| B9 / E5 | Décodage complet en mémoire ; image géante | low | Entrée = appareil photo du téléphone (≈ 48 Mo) ; un fichier piégé ne ferait planter que l'onglet de son auteur | rejeté |
| B9b | Échelle de qualité recommencée à chaque réduction | low | Coût en temps seulement (0,3 s mesuré pour 12 Mpx) | rejeté |
| B10 | Message « illisible » si la photo ne peut pas descendre sous 300 Ko | low | Inatteignable pour une photo d'appareil (190 Ko à 1 600 px) | rejeté |
| B13b | Tests `useObjectUrl`, PNG transparent, sortie pendant le traitement | low | Entrée appareil photo (JPEG) ; nettoyage d'URL sans effet visible | rejeté |
| E4 | Brouillon écrit si l'on quitte pendant l'enregistrement | low | Couvert par l'expiration du brouillon (P1) | rejeté |
| E6 | Image de moins de 320 px acceptée | low | Impossible depuis l'appareil photo | rejeté |

## Design Notes

**Pas de viseur en direct :** l'appareil photo natif, avec `capture="environment"`, donne la meilleure image, l'autofocus et le flash, sans demande de permission caméra en plus ni code fragile. Le viseur décrit par la maquette est celui du téléphone.

**HEIC :** iOS remet déjà du JPEG à un `<input>`. Safari décode le HEIC nativement. Ailleurs, l'échec de lecture est géré proprement. Une bibliothèque WebAssembly (environ 1 Mo) dépasserait le budget pour un cas rare.

**Refus après 10 minutes :** l'attribut `capture` n'est pas respecté sur ordinateur et sur quelques navigateurs. L'ancienneté du fichier est alors le garde-fou contre une photo prise avant ou ailleurs.

## Verification

**Commands:**
- `npm run lint && npm test && npm run build && npm run size && npx tsc -b && npx playwright test --list` (web, conteneur Node 26) — expected: vert ; Playwright complet en CI.
- `python -I scripts/ci/check_pinning.py && python -I scripts/ci/check_repo_hygiene.py` — expected: OK.
