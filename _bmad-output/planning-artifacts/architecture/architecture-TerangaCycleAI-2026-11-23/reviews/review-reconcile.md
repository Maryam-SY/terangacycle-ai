---
type: review-reconcile
target: ARCHITECTURE-SPINE.md (+ .memlog.md)
sources:
  - _bmad-output/planning-artifacts/prds/prd-TerangaCycleAI-2026-11-23/prd.md (final, 43 FR, 17 NFR)
  - _bmad-output/planning-artifacts/prds/prd-TerangaCycleAI-2026-11-23/addendum.md
  - docs/audit-2026-11-23.md (S1-S12)
date: 2026-11-23
---

# Réconciliation de l'épine d'architecture avec ses sources

## Verdict

L'épine tient bien le cœur transactionnel (Statuts, acceptation exclusive, idempotence des Signalements, contrat du Modèle). En revanche, elle a **perdu presque toute la couche de bord et d'exploitation** : en-têtes et CSP, limitation de débit, purges, sauvegardes, alertes. Elle laisse aussi ouverts plusieurs invariants entre équipes : révocation de session, Second facteur, consentement, catalogue d'audit, codes d'énumération entre `ml` et l'API. Enfin, elle **contredit** le PRD sur trois points : l'effacement des IP du Journal d'audit, les codes 408 et le réenvoi d'une acceptation par le même Collecteur. Elle ne peut pas servir de substrat aux stories avant les correctifs R-01 à R-08.

## Synthèse

| # | Sévérité | Écart | Emplacement dans l'épine | Type |
|---|---|---|---|---|
| R-01 | critical | Révocation non garantie : JWT de 15 min sans contrôle d'état ; suspension, suppression et changement de rôle restent effectifs jusqu'à 15 min | AD-9 | contredit FR-5, FR-35 |
| R-02 | high | IP du Journal d'audit à effacer après 6 mois, alors que `teranga_app` n'a pas `UPDATE` sur `audit_logs` | AD-15, AD-2 | contradiction entre deux exigences |
| R-03 | high | Purges de conservation (§6.1, FR-23 24 h, FR-5) absentes ; bucket versionné qui garde les photos « supprimées » | AD-8, AD-13, déploiement | perdu (confidentialité) |
| R-04 | high | Bord HTTP perdu : CSP `'wasm-unsafe-eval'`, HSTS, nosniff, Referrer-Policy, CORS, domaine photo distinct, `/docs` masqué, `/v1/ai/classify` non exposé, journaux Caddy | Squelette (Caddy), aucun AD | perdu (NFR-7, NFR-8, S11) |
| R-05 | high | Limitation de débit et proxys de confiance (S7) : aucune règle ; persistance des compteurs non garantie | AD-14 (« limites de débit » seulement) | perdu (FR-1, FR-10, S6, S7) |
| R-06 | high | AD-10 incomplet : la Position précise reste visible après la fin de la Mission ; distance non arrondie à 100 m ; Position du Collecteur et photos de Preuve non couvertes ; position de recherche du Collecteur journalisée | AD-10 | laissé ouvert, en partie contredit (FR-24, FR-27, FR-29, §6.1) |
| R-07 | high | Second facteur (FR-43) sans mécanisme : aucun claim, aucune règle de `require_role` | AD-9, AD-2 | laissé ouvert |
| R-08 | high | Consentement (FR-4, FR-13) absent : stockage, retrait rétroactif, anonymes, filtre d'export | AD-2, aucun AD | perdu |
| R-09 | high | Contrat `ml` ↔ `ai` ↔ PWA : la chaîne d'évaluation sort du test doré ; octets classés, version du Modèle et source du seuil non fixés | AD-7 | contredit l'addendum D, laissé ouvert |
| R-10 | medium | Codes d'énumération : Type de déchet, Revue de Preuve, Poids déclaré, Taille de tas, Statut de Lot, motifs de rejet ; diagramme AD-3 hors convention | Conventions, AD-3 | laissé ouvert |
| R-11 | medium | Idempotence : la liste des POST à `Idempotency-Key` obligatoire n'est pas fixée ; mise en cache des 4xx ; réenvoi de l'acceptation par le même Collecteur contredit par AD-4 | AD-4, AD-5 | contredit FR-25, laissé ouvert |
| R-12 | medium | Outbox : le code 408 n'est pas réessayé ; un Signalement créé connecté peut être renvoyé en anonyme | AD-12 | contredit FR-18 et l'addendum B.2 |
| R-13 | medium | Tâches planifiées absentes : tirage FR-41, balayage FR-42, reprise de la file pleine FR-14 ; pas d'horloge injectable ; acteur « système » non défini | AD-8 | laissé ouvert |
| R-14 | medium | Catalogue d'audit (FR-36) non fixé : noms d'action et forme d'entrée | AD-3, AD-15 | laissé ouvert |
| R-15 | medium | Indicateurs : historique des Statuts, exclusion des Preuves `contestée` et des Données de démonstration, Collecteurs vérifiés hors des vues | AD-2 (analytics) | laissé ouvert |
| R-16 | medium | Photos : table des photos de Preuve sans propriétaire ; empreinte « photo identique » partagée entre `reports` et `missions` ; miniatures sans clé | AD-2, AD-13 | laissé ouvert |
| R-17 | medium | Suppression de compte et retrait anonyme (FR-5) : aucun chemin entre `auth` et `reports` | AD-1, AD-3 | laissé ouvert |
| R-18 | medium | Identifiant d'appareil : rôle de `devices`, clé HMAC, entropie minimale, journaux | AD-2, AD-9 | laissé ouvert |
| R-19 | medium | Exploitation (NFR-15, NFR-16, NFR-17) : sauvegardes hors hôte, 4 alertes, `/metrics`, gestion des clés | Déploiement, aucun AD | perdu |
| R-20 | medium | Mode et Données de démonstration : `is_demo` côté API, retrait en une commande face à l'audit en ajout seul, seed refusé en prod, champ OTP de démo | AD-14 | laissé ouvert |
| R-21 | medium | Seuils : « 50 m » ambigu (4 seuils distincts) ; nombreux seuils absents de la liste | AD-14 | laissé ouvert |
| R-22 | medium | Topologie des origines : cookie `SameSite=Strict` et CORS dépendent d'un choix de domaines non fixé | AD-9, AD-11 | laissé ouvert |
| R-23 | low | Écarts de nom ou de forme avec l'addendum : `proofs` / `collection_proofs`, `proof_reviews` / colonnes de revue, `staff_second_factors` / `users.totp_secret`, `classification_status` / `classification.status`, `ENV=prod` / `production` | AD-2, AD-8, AD-14 | contradiction de forme |
| R-24 | low | Points secondaires : liste blanche de NFR-9, `/readyz` et Modèle chargé dans le worker, Garage (versionnement, chiffrement), « changements depuis la dernière visite » pour un anonyme, Lots (Recycleur), source `dossier-technique.md` | divers | laissé ouvert |

---

## Détail des écarts et corrections prêtes à coller

### R-01 — critical — La révocation n'est pas garantie par AD-9

- **Emplacement :** AD-9 (« Jeton d'accès : JWT EdDSA de 15 min, avec … `role` »).
- **Sources :**
  - FR-35 : « La requête suivante d'un compte suspendu est refusée (401) ».
  - FR-5 : la suppression « refuse la requête suivante de l'utilisateur (401) ».
  - FR-2 : session révoquée inutilisable.
  - Addendum C, « Suspension » : `is_active` vérifié à chaque requête, ou liste de révocation.
  - FR-35 : changement de rôle.
- **Constat :** avec un JWT sans état qui porte `role`, un compte suspendu, supprimé ou rétrogradé garde jusqu'à 15 min l'accès et le rôle précédent. C'est le comportement par défaut de toute implémentation qui suit l'épine à la lettre. L'équipe `auth` et les équipes des routes en tireraient des conclusions différentes.
- **Correction (nouvel AD) :**

```markdown
### AD-17 — Principal revérifié à chaque requête

- **Binds:** FR-2, FR-3, FR-5, FR-35, FR-43, S4, S5.
- **Prevents:** qu'un compte suspendu, supprimé ou rétrogradé agisse encore pendant la durée de vie du jeton d'accès, et que chaque module contrôle l'état du compte à sa façon.
- **Rule:**
  - Une seule dépendance `core.security.current_principal()` produit le principal. Toutes les routes, y compris `require_role(...)`, passent par elle.
  - Pour un JWT, elle vérifie la signature (liste blanche `algorithms=["EdDSA"]`, `iss`, `aud`, `exp`, `kid` connu), puis lit en base (ou dans un cache Valkey de 30 s au plus, invalidé à l'écriture) `users.is_active`, `users.role`, `users.token_version` et le statut Collecteur vérifié.
  - Le rôle en base fait foi. Le claim `role` sert seulement à l'affichage. Un `token_version` différent de celui du jeton renvoie 401.
  - Suspension, suppression, changement de rôle et réinitialisation du Second facteur incrémentent `token_version` et révoquent toutes les familles de jetons de renouvellement de l'utilisateur, dans la même transaction que l'entrée d'audit.
  - Le jeton de renouvellement a une durée glissante de 30 jours d'activité (FR-2). La déconnexion révoque sa famille.
```

---

### R-02 — high — L'effacement des IP du Journal d'audit est impossible avec AD-15

- **Emplacement :** AD-15 (« `teranga_app` … **sans** `UPDATE` ni `DELETE` sur `audit_logs` ») et AD-2 (`core/audit`, ajout seul).
- **Sources :**
  - PRD §6.1 : « IP du Journal d'audit : 6 mois ». Test : « une IP de plus de 6 mois est effacée du Journal d'audit ».
  - NFR-17 et addendum B.1, point 12.
  - Audit, « `audit_logs.ip` ».
- **Constat :** les deux exigences sont incompatibles si l'IP est une colonne de `audit_logs`. Une équipe accordera `UPDATE (ip)`, ce qui viole NFR-17 et FR-36. Une autre n'effacera jamais les IP, ce qui viole §6.1.
- **Correction (ajout à AD-15 et à la table d'AD-2) :**

```markdown
  - L'IP d'une entrée d'audit n'est **pas** une colonne de `audit_logs` : elle est dans `audit_log_ips(audit_log_id, ip, created_at)`, propriété de `core/audit`. `teranga_app` a INSERT, SELECT et DELETE sur cette table seulement. La purge des IP de plus de 6 mois supprime des lignes de `audit_log_ips` et ne touche jamais `audit_logs`.
```

Ligne à ajouter dans la table d'AD-2 : `| core/audit | audit_logs (ajout seul), audit_log_ips (purge à 6 mois) |`

---

### R-03 — high — Les purges de conservation sont perdues, et le versionnement les contredit

- **Emplacement :** AD-8 (aucune tâche de purge) ; AD-13 ; diagramme de déploiement (« Stockage S3 privé, chiffré, versionné ») ; aucune règle de conservation.
- **Sources :**
  - PRD §6.1 (tableau des durées ; « Une tâche planifiée applique ces durées », test à horloge simulée).
  - FR-23 : photo « Personne ou plaque visible » supprimée sous 24 h.
  - FR-5 : purge sous 30 jours ; photos et Positions des Signalements `en attente`/`rejeté` supprimées.
  - Addendum F.1 : purge nocturne en arq ; versionnement du stockage objet.
  - Audit S9.
- **Constat :**
  - Aucune règle ne fixe qui purge quoi.
  - Un bucket versionné garde la version « supprimée » : FR-23 (24 h) et FR-5 ne sont donc pas tenus, et le test « son lien ne fonctionne plus » passe à tort.
  - Les sauvegardes de photos (NFR-15) prolongent aussi la conservation sans limite fixée.
- **Correction (nouvel AD) :**

```markdown
### AD-18 — Cycle de vie des données personnelles

- **Binds:** PRD §6.1, FR-5, FR-23, NFR-15, NFR-17, S9.
- **Prevents:** des photos ou Positions « supprimées » qui survivent dans une version d'objet ou une sauvegarde, et des purges implémentées différemment par chaque module.
- **Rule:**
  - Les durées du §6.1 sont des réglages nommés (`RETENTION_REPORT_PHOTO_DAYS=365`, `RETENTION_REJECTED_PHOTO_DAYS=30`, `RETENTION_PERSON_VISIBLE_HOURS=24`, `RETENTION_PROOF_PHOTO_DAYS=365`, `RETENTION_AUDIT_IP_DAYS=182`, `ACCOUNT_PURGE_DAYS=30`).
  - Chaque module propriétaire expose `service.purge_expired(now)`. Une seule tâche arq planifiée (`purge:<date>`) les appelle chaque nuit. FR-23 a sa propre tâche horaire.
  - Supprimer une photo passe par `core.storage.purge(object_key)`, qui supprime **toutes les versions** de l'objet. Si le bucket est versionné, une règle de cycle de vie expire les versions non courantes sous 24 h.
  - Les sauvegardes ont une rétention bornée (`BACKUP_RETENTION_DAYS`, 30 par défaut). Une donnée purgée disparaît donc de toutes les copies dans ce délai. Après une restauration, la tâche de purge est rejouée avant la réouverture du service.
  - La suppression d'une photo vide aussi `object_key` en base. La purge est inscrite au Journal d'audit par lot (nombre d'objets, catégorie), sans donnée personnelle.
```

---

### R-04 — high — Le bord HTTP est perdu : en-têtes, CSP, exposition, journaux du proxy

- **Emplacement :** squelette (« Caddy : TLS · en-têtes · statiques »), sans aucun AD ; AD-11 (OpenAPI) ; AD-10 (journaux de l'application seulement).
- **Sources :**
  - NFR-8 : TLS 1.2+, HSTS, HTTP vers HTTPS, CSP `script-src 'self' 'wasm-unsafe-eval'`, nosniff, `Referrer-Policy: no-referrer`, CORS limité, photos sur un domaine distinct.
  - NFR-7 et S11 : `/docs` et `/openapi.json` non exposés hors Mode démonstration.
  - Addendum C, « Exposition » : `/v1/ai/classify` non exposé, `/metrics` interne, délai et taille maximale du corps au proxy.
  - Audit, « CSP ».
  - Addendum B.1, point 11 : l'Identifiant d'appareil n'est jamais journalisé.
- **Constat :**
  - Les en-têtes peuvent être posés à deux endroits (Caddy et un middleware FastAPI), avec des valeurs divergentes.
  - Sans règle, onnxruntime-web risque de charger ses `.wasm` hors de l'origine (bloqué par `script-src 'self'`, contraire à la souveraineté) ou d'exiger l'isolation cross-origin pour le multithread (COOP/COEP), ce qui casserait les tuiles et les photos signées.
  - Le filtre `structlog` d'AD-10 ne couvre pas les journaux d'accès de Caddy. Ceux-ci incluent les en-têtes de requête (dont `X-Device-Id`) et les query strings (positions).
- **Correction (nouvel AD) :**

```markdown
### AD-19 — Bord HTTP : en-têtes, exposition et journaux du proxy

- **Binds:** NFR-7, NFR-8, NFR-14, S7, S11, FR-11.
- **Prevents:** des en-têtes posés deux fois avec des valeurs différentes, une CSP affaiblie « pour que ça marche », une surface interne exposée, et des données personnelles dans les journaux du proxy.
- **Rule:**
  - **Caddy est le seul endroit** où sont posés HSTS, CSP, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer` et la redirection HTTP vers HTTPS (TLS 1.2 minimum). FastAPI n'en pose aucun.
  - La CSP est fixée dans `infra/Caddyfile` et testée en CI :
    `default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; img-src 'self' blob: data: https://<MEDIA_HOST> https://<TILES_HOST>; connect-src 'self' https://<MEDIA_HOST>; worker-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'`.
  - onnxruntime-web charge ses fichiers `.wasm` depuis l'origine de la PWA (`ort.env.wasm.wasmPaths` vers des fichiers précachés), jamais d'un CDN. Il tourne en **un seul thread** (`numThreads = 1`) : pas de COOP/COEP au MVP.
  - Les photos sont servies depuis `MEDIA_HOST`, un domaine distinct de l'API et de la PWA.
  - Caddy ne publie que `/v1/*` (hors `/v1/ai/*`) et les fichiers statiques. `/metrics` et `/v1/ai/*` ne sont joignables que sur le réseau interne. Caddy fixe une taille maximale de corps (`MAX_BODY_BYTES`, 2 Mo) et un délai d'expiration.
  - Hors `ENV ∈ {dev, demo}`, FastAPI est construite avec `docs_url=None, redoc_url=None, openapi_url=None`. Le client TypeScript est généré en CI depuis l'application, pas depuis l'URL publique.
  - Les journaux d'accès de Caddy suppriment `X-Device-Id`, `Authorization`, `Cookie` et `Idempotency-Key`, ainsi que les paramètres `lat` et `lng` des URL.
  - Un test automatisé vérifie la présence et la valeur de chaque en-tête, l'absence de `/docs` en prod et le refus externe de `/metrics` et `/v1/ai/*`.
```

---

### R-05 — high — Limitation de débit et proxys de confiance (S7) : aucune règle

- **Emplacement :** AD-14 (« limites de débit » parmi les réglages) ; diagramme (Valkey « OTP · limites »).
- **Sources :**
  - FR-1 : 5 demandes par heure par numéro, 5 par appareil, 20 par IP ; plafond quotidien de SMS, puis 503 et alerte.
  - FR-10 : 10 Signalements par heure par appareil ou IP, ou par compte ; 60 requêtes par minute par Utilisateur connecté ; test avec 11 `X-Forwarded-For` différents ; « Les compteurs survivent à un redémarrage ».
  - Addendum C, S6 et S7.
  - Audit S6, S7 : `caddy:2` n'a pas de limitation de débit.
- **Constat :**
  - Rien ne fixe où l'on limite (Caddy ou API), comment l'IP est lue, ni la persistance de Valkey.
  - Un middleware qui lit le premier élément de `X-Forwarded-For`, ou un `forwarded_allow_ips="*"`, rend la limite par IP contournable.
  - Sans persistance (AOF) dans Valkey, les compteurs, les OTP et la file arq sont perdus au redémarrage.
- **Correction (nouvel AD) :**

```markdown
### AD-20 — Limitation de débit et IP du client

- **Binds:** FR-1, FR-10, FR-14, S6, S7, NFR-16.
- **Prevents:** une IP falsifiable par `X-Forwarded-For`, des compteurs perdus au redémarrage, et des limites implémentées route par route.
- **Rule:**
  - La limitation se fait **dans l'API**, par `core.security.rate_limit(scope, key, limit, window)` sur Valkey (fenêtre glissante, opérations atomiques). Jamais dans Caddy.
  - L'IP du client est celle que pose Caddy. uvicorn tourne avec `--proxy-headers --forwarded-allow-ips=<IP du conteneur Caddy>`, jamais `*`. Caddy ignore tout `X-Forwarded-For` venu du client. Le code lit seulement `request.client.host`.
  - Portées fixées (clés hachées, jamais en clair) :
    - `otp:phone` 5/h ; `otp:device` 5/h ; `otp:ip` 20/h ; `sms:daily` (plafond `SMS_DAILY_CAP`, au-delà 503 `sms_cap_reached` et alerte AD-24) ;
    - `report:device` 10/h ; `report:ip` 10/h ; `report:user` 10/h ;
    - `user:any` 60/min.
  - Tout 429 porte l'en-tête `Retry-After`, en secondes, et le code `rate_limited`. L'outbox (AD-12) le respecte.
  - L'OTP est stocké haché (HMAC) dans Valkey, avec un TTL de 5 min et un compteur d'essais. La comparaison se fait à temps constant ; il est invalidé au 5ᵉ échec.
  - Valkey tourne avec persistance AOF (`appendonly yes`) dans tous les environnements.
```

---

### R-06 — high — AD-10 incomplet face à FR-24, FR-27, FR-29 et §6.1

- **Emplacement :** AD-10, table des niveaux.
- **Sources :**
  - FR-24 : avant l'acceptation, Position arrondie à 3 décimales **et distance à 100 m près** ; test « ne reçoit jamais plus de 3 décimales ».
  - FR-27 : itinéraire seulement pour le Collecteur de la Mission `active`.
  - FR-29 : photos de Preuve visibles du seul Collecteur de la Mission et du Personnel.
  - §6.1 : la Position du Collecteur est une donnée personnelle ; « Positions précises réservées au Personnel et au Collecteur de la Mission ».
  - FR-34 : aucune coordonnée dans une réponse publique.
  - FR-39 : ni nom ni numéro du Collecteur dans la liste des Lots.
- **Constat :**
  1. `precise` pour « Collecteur de la Mission » ne dit pas « tant que la Mission est `active` » : après une annulation ou une expiration, l'ancien Collecteur garde la Position précise.
  2. La distance n'est pas arrondie, ce qui permet de trianguler la Position exacte à partir de distances précises et d'annuler l'arrondi.
  3. La Position du Collecteur dans la Preuve et les photos `before`/`after` n'ont pas de niveau.
  4. La Position courante du Collecteur, envoyée pour la recherche FR-24, n'a pas de règle : faut-il la stocker ou la journaliser ?
  5. L'« auteur » en `precise` est plus large que la formulation du §6.1 (acceptable pour sa propre Position, à expliciter).
- **Correction (remplacer la table et ajouter des puces à AD-10) :**

```markdown
    | Niveau | Destinataires | Précision |
    |---|---|---|
    | `precise` | Personnel ; Collecteur d'une Mission **`active`** sur ce Signalement ; auteur (sa propre Position seulement) | Position exacte |
    | `approx` | Collecteur vérifié sans Mission `active` sur ce Signalement | Arrondie à 3 décimales ; distance renvoyée arrondie à 100 m, calculée côté serveur sur la Position exacte |
    | `rounded` | Exports agrégés (FR-33) | Arrondie à 3 décimales |
    | `aggregated` | Visiteurs (FR-34) | Cellules d'au moins 500 m, 3 Signalements minimum ; aucune coordonnée de Signalement |
    | `none` | Collecteur non vérifié, Recycleur, tout autre rôle | Aucune Position de Signalement |

  - Le niveau se calcule dans le service, à partir du principal **et** du Statut de Mission courant, jamais du rôle seul.
  - La Position du Collecteur dans une Preuve, et les photos `before`/`after`, ne sont servies qu'au Personnel et au Collecteur de la Mission (FR-29), quel que soit le Statut de Mission.
  - La Position courante envoyée par un Collecteur pour la recherche FR-24 n'est ni stockée ni journalisée. Elle voyage dans le corps ou dans des paramètres que AD-19 retire des journaux.
  - Aucune réponse de la liste des Lots ne contient de nom, de numéro ni d'identifiant de Collecteur (FR-39).
  - Le test « jamais plus de 3 décimales » couvre toutes les réponses lues par un Collecteur vérifié qui n'est pas celui de la Mission `active`, champs de distance compris.
```

---

### R-07 — high — Second facteur (FR-43) : aucun mécanisme

- **Emplacement :** AD-9 (binds FR-43, sans règle) ; AD-2 (`staff_second_factors`).
- **Sources :**
  - FR-43 : sans Second facteur valide, fonctions du Personnel refusées (403) ; activation et réinitialisation auditées.
  - Addendum C : TOTP RFC 6238, secret chiffré.
  - Addendum B.1, point 15.
- **Constat :** rien ne dit comment une route du Personnel sait que le second facteur a été franchi. L'équipe `auth` peut l'encoder dans le jeton, une autre équipe le revérifier par route. Rien non plus sur le chiffrement du secret ni sur son activation au pilote seulement.
- **Correction (ajout à AD-17, ou nouvel AD) :**

```markdown
  - **Second facteur (FR-43) :** TOTP RFC 6238 (pas de 30 s, fenêtre ±1), secret chiffré en AES-GCM avec une clé dédiée (`TOTP_ENC_KEY`) dans `staff_second_factors`. Un code déjà utilisé dans sa fenêtre est refusé.
  - Le jeton d'accès porte `amr` (`["otp"]` ou `["otp","totp"]`). La famille de renouvellement mémorise le niveau atteint. `require_role(MODERATOR | ADMIN)` exige `"totp" ∈ amr` quand `STAFF_MFA_REQUIRED` est vrai, sinon 403 `second_factor_required`.
  - `STAFF_MFA_REQUIRED` vaut faux par défaut en `dev`/`demo` et **vrai, sans dérogation, en `prod`** : le démarrage échoue sinon.
  - L'activation, la réinitialisation (par un Administrateur commune) et chaque connexion du Personnel sont inscrites au Journal d'audit (AD-22).
```

---

### R-08 — high — Consentement : perdu

- **Emplacement :** aucun AD ; AD-2 (aucune colonne ni table de consentement ; `devices` sans contenu défini).
- **Sources :**
  - FR-4 : rien n'est envoyé sans acceptation ; acceptation horodatée pour un compte, mémorisée sur l'appareil pour un anonyme ; choix enregistré sur chaque Signalement ; retrait à tout moment qui « exclut ses Signalements, passés et futurs, des exports suivants ».
  - FR-13 : export des Corrections filtré par consentement.
  - FR-36 : l'export des Corrections est audité.
  - Addendum B.1, points 6 et 10.
  - Audit §4 (finalité « réentraînement »).
- **Constat :**
  - Le retrait rétroactif est incompatible avec une simple copie figée sur le Signalement.
  - Le retrait par un anonyme suppose un appel API avec `X-Device-Id`.
  - Le propriétaire de l'export des Corrections n'est pas désigné : `ai`, `ml` ou `analytics` ?
  - La PWA et l'API peuvent nommer différemment les champs de consentement.
- **Correction (nouvel AD) :**

```markdown
### AD-21 — Consentement au réentraînement

- **Binds:** FR-4, FR-13, FR-36, PRD §6.3.
- **Prevents:** qu'un Signalement dont l'auteur a retiré son consentement apparaisse dans un export, et que la PWA, `auth` et `reports` stockent le consentement chacun à sa façon.
- **Rule:**
  - `POST /v1/reports` exige `consent: {terms: true, training: bool}`. Sans `terms: true`, le serveur répond 422 `consent_required`.
  - La valeur courante vit chez `auth` : `users.consent_training` + `consent_training_at` pour un compte ; `devices.consent_training` + horodatage pour un anonyme (ligne créée au premier contact).
  - `reports.consent_training` est la copie prise à la création. Un retrait (`PUT /v1/me/consent` ou `PUT /v1/device/consent`) appelle `reports.service.revoke_training_consent(owner_key)`, qui met cette colonne à faux sur **tous** les Signalements de l'`owner_key`, dans la même transaction.
  - L'export des Corrections appartient à `reports` (`reports.service.export_corrections()`). Il ne retient que les Signalements ayant atteint `validated` avec `consent_training = true` au moment de l'export, et inscrit l'export au Journal d'audit. `ml/` ne lit que ce fichier.
```

(Numérotation proposée pour les nouveaux AD : AD-17 session, AD-18 cycle de vie, AD-19 bord HTTP, AD-20 débit, AD-21 consentement, AD-22 audit, AD-23 suppression, AD-24 exploitation.)

---

### R-09 — high — Contrat `ml` ↔ `ai` ↔ PWA incomplet (AD-7)

- **Emplacement :** AD-7.
- **Sources :**
  - Addendum D : prétraitement unique « pour l'évaluation, le serveur et le navigateur » ; test sur **20** images, **trois chaînes**, écart de score ≤ 0,01.
  - FR-14 : le serveur reclasse « la même photo avec la même version du Modèle ».
  - FR-12 et FR-15 ; SM-2 (ECE ≤ 0,10, condition de validité du seuil).
- **Constat :**
  1. Le test doré d'AD-7 ne compare que Python serveur et TypeScript. La chaîne d'évaluation de `ml/` (PyTorch/torchvision) en sort, alors que les seuils SM-2 se mesurent sur cette chaîne. `ml` et `ai` peuvent diverger sans qu'aucun test ne le voie.
  2. Rien ne dit **quels octets** sont classés. Si le navigateur classe la capture brute et le serveur le JPEG de 300 Ko ré-encodé sans EXIF, sans application de l'orientation, on obtient des Désaccords IA artificiels.
  3. La version du Modèle peut différer entre le cache de la PWA et le serveur. FR-14 exige la même version, et AD-7 ne dit pas quoi faire.
  4. Le Seuil de confiance est à la fois un réglage serveur (AD-14) et un `needs_user_choice` calculé côté client : deux sources possibles.
- **Correction (remplacer les puces 3 et 4 d'AD-7, puis ajouter) :**

```markdown
  - Un test doré, joué en CI sur 20 images de référence, compare **trois chaînes** : évaluation `ml/` (celle qui produit les métriques SM-2), serveur (onnxruntime) et navigateur (onnxruntime-web, en Node/Playwright). L'écart de score doit être ≤ 0,01 par classe.
  - Les deux côtés classent **les mêmes octets** : le JPEG compressé envoyé au serveur. Le navigateur classe le blob produit par la compression d'AD-12, et non la capture brute. Le serveur applique l'orientation EXIF (`ImageOps.exif_transpose`) avant de la supprimer, puis classe l'image ré-encodée stockée.
  - Le JSON du Modèle porte `classes` (codes de la convention « Type de déchet »), `confidence_threshold` (0,60), `temperature` et `sha256` du `.onnx`. Le navigateur et le serveur lisent le seuil **dans ce JSON**. Le réglage `CONFIDENCE_THRESHOLD` d'AD-14 ne sert qu'à vérifier, au démarrage, qu'il est égal à celui du JSON.
  - Le Désaccord IA n'est calculé que si `client_model_version == model_version` côté serveur. Sinon, le Signalement porte `disagreement = null`. Le serveur garde la version N-1 chargeable pendant 30 jours après une publication.
```

---

### R-10 — medium — Codes d'énumération incomplets

- **Emplacement :** Conventions de cohérence (ligne « Nommage ») ; diagramme d'AD-3.
- **Sources :**
  - Glossaire : Type de déchet (5 classes), Taille de tas, Poids déclaré (`pesé`/`estimé`), Revue de Preuve (`non revue`/`confirmée`/`contestée`), Statut de Lot (`disponible`/`réservé`).
  - FR-23 : motifs de rejet, dont « doublon » et « Personne ou plaque visible ».
  - Addendum B.1, points 2, 8 et 9.
- **Constat :**
  - Seuls les Statuts et Statuts de Mission sont mappés. Le Type de déchet est le plus risqué : `ml` produit l'ordre des classes, l'API valide `waste_type`, la PWA associe pictogramme et couleur. Trois équipes, aucun code commun.
  - Le diagramme d'AD-3 utilise `en_attente_de_moderation`, `valide`, etc., au lieu des codes de la convention (`pending_review`…).
  - Le mapping des Statuts et Statuts de Mission est, lui, conforme au Glossaire et à B.1.
- **Correction (lignes de convention à ajouter) :**

```markdown
| Énumérations (suite) | Type de déchet : `plastique`=`plastic`, `métal`=`metal`, `verre`=`glass`, `organique`=`organic`, `mixte`=`mixed` ; ces codes sont exactement les `classes` du JSON du Modèle (AD-7). Taille de tas : `small`, `medium`, `large`. Poids déclaré : `pesé`=`weighed`, `estimé`=`estimated`. Revue de Preuve : `non revue`=`unreviewed`, `confirmée`=`confirmed`, `contestée`=`contested`. Statut de Lot : `disponible`=`available`, `réservé`=`reserved`. Motifs de rejet : `spam`, `not_waste`, `outside_zone`, `duplicate` (exige `duplicate_of`), `person_or_plate_visible` (déclenche la purge de 24 h d'AD-18), `other` (texte obligatoire). |
| Énumérations : source unique | Chaque énumération est définie une fois dans `backend/app/core/enums.py`, exportée dans l'OpenAPI, et le client TypeScript la reçoit par génération (AD-11). Aucune liste recopiée à la main dans `web/` ni dans `ml/` ; un test vérifie que `classes` du JSON du Modèle = `WasteType`. |
```

Et dans AD-3 : renommer les états du diagramme en `pending_review`, `validated`, `rejected`, `assigned`, `collected`.

---

### R-11 — medium — Idempotence : liste des routes, mise en cache des refus, réenvoi d'une acceptation

- **Emplacement :** AD-5 (« Preuves de collecte et autres POST sensibles ») ; AD-4 (« Une violation d'unicité est traduite en 409 »).
- **Sources :**
  - Addendum A : `Idempotency-Key` sur « Preuve, acceptation, modération, assignation ».
  - FR-25 : « Un renvoi de la même acceptation par le même Collecteur renvoie la Mission existante, sans erreur ».
  - FR-29 : renvoi d'une même Preuve, une seule Preuve enregistrée ; une Preuve refusée pour la distance doit pouvoir être resoumise.
- **Constat :**
  1. « Autres POST sensibles » n'est pas une liste. Comme l'absence d'en-tête renvoie 400, la PWA et l'API doivent avoir **exactement** la même liste.
  2. AD-4 renvoie 409 même au Collecteur qui détient déjà la Mission `active`, ce qui contredit FR-25 si le renvoi arrive sans la même clé ou après expiration du cache.
  3. Si un 422 (distance) est mis en cache 24 h sous la même clé, toute nouvelle tentative rejoue le refus.
  4. L'unicité d'une Preuve par Mission ne repose que sur le cache d'idempotence.
- **Correction (ajouts à AD-5 et AD-4) :**

```markdown
  - **Routes à `Idempotency-Key` obligatoire** (liste close, testée) : `POST /v1/missions` (acceptation), `POST /v1/missions/{id}/proof`, `POST /v1/reports/{id}/decision` (modération), `POST /v1/admin/assignments`, `POST /v1/missions/{id}/cancel`, `POST /v1/lots/{id}/reservations`. Toute nouvelle route qui crée ou fait transiter une ressource s'ajoute à cette liste dans la même PR.
  - Seules les réponses **2xx** sont conservées (Valkey avec persistance, TTL 24 h). Un 4xx n'est pas mis en cache : le client peut resoumettre avec la même clé après avoir corrigé (par exemple, une nouvelle Position).
  - La base garantit l'unicité indépendamment du cache : `UNIQUE (proofs.mission_id)`, plus l'index partiel d'AD-4.
```

Ajout à AD-4 :

```markdown
  - Sur violation d'unicité, si la Mission `active` existante appartient au **même** Collecteur, la réponse est 200 avec cette Mission (FR-25). Sinon, 409 `mission_already_taken`.
```

---

### R-12 — medium — Outbox : le code 408 et le principal d'envoi

- **Emplacement :** AD-12.
- **Sources :**
  - FR-18 : refus définitif = « 4xx autre que 408 et 429 ».
  - Addendum B.2 : « un Signalement créé connecté n'est jamais renvoyé en anonyme » ; `flushQueue` toujours avec le jeton courant et l'Identifiant d'appareil.
- **Constat :**
  - AD-12 ne réessaie pas le code 408, qui passe donc en échec définitif (contradiction).
  - « Jeton d'accès, ou `X-Device-Id` » permet de renvoyer en anonyme un Signalement créé connecté, après une déconnexion ou un jeton expiré. Il prendrait alors un autre `owner_key` : soit un doublon, soit un 409 `client_uuid_conflict` pour son propre auteur.
- **Correction (remplacer les puces concernées d'AD-12) :**

```markdown
  - Chaque élément mémorise, à sa création, son principal (`user:<id>` ou `device`). Un élément `user` n'est envoyé qu'avec un jeton valide de ce même utilisateur ; sinon il attend (jamais de repli anonyme). `X-Device-Id` est joint à tous les envois.
  - Réessai avec backoff exponentiel plafonné **uniquement** sur erreur réseau, 408, 429 (en respectant `Retry-After`) ou 5xx.
  - Tout autre 4xx sort l'élément de la file d'envoi (il ne compte plus dans le compteur de FR-19) et le garde, dans un état `failed`, pour afficher le motif.
```

---

### R-13 — medium — Tâches planifiées et horloge

- **Emplacement :** AD-8 (liste : Classification, miniatures, notifications, expiration).
- **Sources :**
  - FR-41 : tirage hebdomadaire d'au moins 5 %, au moins une Preuve, et ajout d'office des photos identiques.
  - FR-42 : test à horloge simulée, 48 h + 1 min.
  - FR-14 : une file pleine laisse des Signalements « en attente » « jusqu'à leur reclassement ».
  - §6.1 : test à horloge simulée.
  - FR-36 : expiration automatique auditée, avec un acteur.
- **Constat :**
  - Le mécanisme d'expiration n'est pas fixé (tâche différée par Mission, ou balayage périodique).
  - Aucune tâche ne reprend les Classifications restées `pending` quand la file était pleine : ces Signalements restent bloqués.
  - Le tirage FR-41 n'a ni planification ni source d'aléa.
  - Il n'y a pas d'horloge injectable pour les tests, ni d'acteur d'audit pour le système.
- **Correction (ajout à AD-8) :**

```markdown
  - **Tâches planifiées (cron arq), liste close :**
    - `missions.expire_due` chaque minute : `UPDATE … WHERE status='active' AND expires_at <= now()`, via `missions.service.transition` (pas de tâche différée par Mission) ;
    - `reports.requeue_pending_classifications` toutes les 5 min, dans la limite de la place libre de la file ;
    - `missions.sample_proofs` chaque lundi, identifiant `proof_sample:<année-semaine ISO>`, tirage par `secrets.SystemRandom` (≥ `PROOF_SAMPLE_RATE`, au moins 1) ;
    - purges d'AD-18.
  - Toute lecture de l'heure passe par `core.clock.now()`, que les tests remplacent ; aucun `datetime.now()` hors de `core.clock`.
  - Une action faite par une tâche est auditée avec `actor = "system:<nom_de_tâche>"`.
```

---

### R-14 — medium — Catalogue d'audit (FR-36) non fixé

- **Emplacement :** AD-3 (transitions seulement) ; AD-15 (binds FR-36).
- **Sources :** FR-36 (liste de 7 familles d'actions, acteur, objet, avant/après, horodatage serveur ; « pour chaque action de la liste, un test vérifie qu'une entrée est créée » ; consultation filtrable par action et période) ; FR-26 ; FR-35 ; FR-43.
- **Constat :** sans liste de codes, `auth`, `reports`, `missions` et `analytics` nommeront leurs actions différemment, et le filtre « par action » comme le test « pour chaque action » n'ont pas de référence.
- **Correction (ajout à AD-15, ou nouvel AD) :**

```markdown
### AD-22 — Catalogue du Journal d'audit

- **Binds:** FR-36, FR-23, FR-26, FR-28, FR-35, FR-41, FR-42, FR-43, FR-13, FR-33.
- **Prevents:** des noms d'action divergents entre modules, et une action exigée par FR-36 qui n'est jamais journalisée.
- **Rule:**
  - `core.audit.AuditAction` est une énumération close : `report.transition`, `report.correction`, `mission.transition`, `mission.assign`, `proof.review`, `account.create`, `account.verify`, `account.suspend`, `account.delete`, `account.role_change`, `mfa.enable`, `mfa.reset`, `staff.login`, `export.aggregate`, `export.corrections`, `retention.purge`.
  - Une entrée contient `actor` (`user:<id>` ou `system:<tâche>`), `actor_role`, `action`, `object_type`, `object_id`, `before`, `after` (JSON, sans donnée personnelle), `request_id` et `created_at` (serveur). L'IP est dans `audit_log_ips` (R-02).
  - Un test paramétré sur `AuditAction` vérifie qu'au moins un chemin de code produit chaque action.
```

---

### R-15 — medium — Faits d'indicateurs

- **Emplacement :** AD-2 (`analytics` lit `v_report_facts`, `v_mission_facts`) ; graphe des modules (pas de lien `analytics` → `auth`).
- **Sources :**
  - FR-31 : « Ayant atteint » se lit dans l'historique des Statuts ; Délai médian = réception → acceptation de la Preuve ; Kg collectés hors Preuves `contestée`, avec la part `pesé` ; Collecteurs vérifiés actifs.
  - FR-41 : part de Preuves `contestée` au Tableau de bord.
  - FR-37 et §7 : honnêteté, « aucun chiffre de démonstration présenté comme réel ».
- **Constat :**
  - L'historique des Statuts n'a pas de source définie. `analytics` risque de lire `audit_logs` (forme libre, purge des IP) ou de déduire l'historique du seul Statut courant.
  - « Collecteurs vérifiés » est une donnée de `auth`, que les deux vues ne couvrent pas.
  - L'exclusion des Preuves `contestée` et le traitement de `is_demo` ne sont pas fixés.
- **Correction (ajout à AD-2) :**

```markdown
  - `reports` tient les jalons `received_at`, `validated_at`, `rejected_at`, `assigned_at`, `collected_at`, posés par `transition()` (le premier passage fait foi ; un retour `assigned → validated` ne les efface pas). `v_report_facts` les expose. `analytics` ne lit jamais `audit_logs`.
  - `v_mission_facts` expose, par Preuve acceptée, `accepted_at`, `weight_kg`, `weight_kind`, `review_status`, `retained_type` et `collector_verified` (jointure faite dans la vue, créée par migration). Les Kg collectés excluent `review_status = 'contested'`.
  - Les deux vues portent `is_demo`. Chaque réponse d'`analytics` contient `contains_demo_data: bool`, que la PWA affiche comme étiquette (FR-37).
```

---

### R-16 — medium — Photos : propriété, empreinte partagée, miniatures

- **Emplacement :** AD-2 (`report_photos` chez `reports` ; aucune table de photos de Preuve chez `missions`) ; AD-13 (`<kind>` ∈ `report`, `before`, `after`) ; AD-8 (miniatures).
- **Sources :**
  - FR-8 et Glossaire, « Doublon probable » : photo strictement identique.
  - FR-41 : une Preuve dont une photo est identique à une photo déjà reçue (Signalement **ou** Preuve) rejoint l'échantillon.
  - Addendum B.1, point 8 : photos `before`/`after` reliées à la Mission.
  - FR-24 : miniatures de 30 Ko au plus.
  - FR-22 : un Doublon probable renvoie vers l'original ; B.1, point 10 : `duplicate_of`, `flags`.
- **Constat :**
  - Les lignes de photos de Preuve n'ont pas de propriétaire : `missions` pourrait écrire dans `report_photos`.
  - « Strictement identique » n'est pas défini : empreinte des octets reçus ou de l'image ré-encodée ?
  - La recherche croisée entre Signalements et Preuves franchit la frontière des modules.
  - Les miniatures n'ont pas de format de clé.
  - La détection de proximité (50 m, 72 h, non terminal) n'a ni moment ni lieu fixés.
- **Correction :**

Table d'AD-2 : `| missions | missions, proofs, proof_photos, proof_reviews |`

Ajout à AD-13 :

```markdown
  - Chaque photo stockée porte `sha256` = SHA-256 des **octets reçus**, avant ré-encodage. La colonne est indexée dans `report_photos` et `proof_photos`.
  - `reports.service.find_photo_by_sha256()` et `missions.service.find_photo_by_sha256()` sont les seules façons de chercher une photo identique. `missions` appelle celle de `reports` (sens autorisé par le graphe).
  - `<kind>` ∈ `report`, `before`, `after`, `thumb` ; la miniature (≤ 30 Ko) a la clé `thumb/<yyyy>/<mm>/<uuid de la photo source>.jpg`.
  - Le Doublon probable se calcule de façon synchrone dans `reports.service.create()` (photo identique, ou `ST_DWithin` de 50 m sur les Signalements non terminaux reçus depuis 72 h). Il remplit `duplicate_of` et `flags` et ne bloque jamais la création.
```

---

### R-17 — medium — Suppression de compte et retrait anonyme (FR-5)

- **Emplacement :** AD-1 et AD-3 (pas de chemin) ; AD-5 (`owner_key = user:<id>`).
- **Sources :**
  - FR-5 et UJ-5 : numéro effacé, 401, purge sous 30 jours ; photos et Positions des Signalements `en attente`/`rejeté` supprimées ; Signalements `validé` conservés avec un auteur anonymisé ; un anonyme retire un Signalement `en attente`.
  - Addendum B.1, point 11 : l'unicité reste valable après anonymisation.
- **Constat :**
  - Cette opération traverse `auth` et `reports` (et `missions` pour un Collecteur), mais aucune règle ne fixe l'orchestrateur ni l'effet sur la machine à états.
  - Un Signalement retiré n'a pas de Statut dans le Glossaire : faut-il le supprimer ou créer un nouvel état ?
  - L'`owner_key` `user:<id>` garde un lien vers l'identifiant purgé.
- **Correction (nouvel AD) :**

```markdown
### AD-23 — Suppression de compte et retrait

- **Binds:** FR-5, FR-35, FR-36, AD-5, AD-18.
- **Prevents:** une suppression partielle faite module par module, et l'invention d'un Statut hors du Glossaire.
- **Rule:**
  - `auth.service.delete_account(user_id)` est l'unique point d'entrée. Dans une transaction : effacement de `phone_hash` et `phone_enc`, `token_version` incrémenté, familles révoquées, puis appel de `reports.service.detach_owner(owner_key)`, qui :
    - supprime définitivement (ligne et photos, via `core.storage.purge`) les Signalements `pending_review` et `rejected` ;
    - met `author_id = NULL` sur les autres, en gardant `owner_key` (unicité d'AD-5).
  - Le retrait par un anonyme (`DELETE /v1/reports/{id}` avec `X-Device-Id`) n'est permis qu'en `pending_review`. C'est une suppression, pas un Statut. Il est audité sans donnée personnelle.
  - La ligne `users` est purgée par AD-18 après `ACCOUNT_PURGE_DAYS`.
  - `owner_key` d'un compte vaut `user:<HMAC(user_id)>` : il ne révèle pas l'identifiant après purge.
  - Suppression d'un Collecteur ayant une Mission `active` : la Mission est d'abord `cancelled` par `missions.service.transition`.
```

---

### R-18 — medium — Identifiant d'appareil

- **Emplacement :** AD-2 (`devices` chez `auth`, contenu non défini) ; AD-5 et AD-9 (`HMAC(Identifiant d'appareil)`, clé non nommée).
- **Sources :**
  - Glossaire : jamais affiché ni renvoyé.
  - Addendum B.1, point 11 : ≥ 128 bits, stocké haché (`device_id_hash`), jamais journalisé.
  - §6.1 : empreinte de l'Identifiant d'appareil.
  - FR-1 : limite de 5 OTP par appareil.
- **Constat :**
  - Le calcul du HMAC (fonction et clé) n'est pas attribué : `reports` peut le calculer lui-même avec la clé du téléphone.
  - Rien n'oblige à rejeter un identifiant faible, comme `1234`, qui rendrait l'`owner_key` devinable et rouvrirait S1.
  - Rien ne dit qui crée la ligne `devices`.
- **Correction (ajout à AD-9) :**

```markdown
  - `X-Device-Id` doit être 32 caractères base64url ou plus (≥ 128 bits, généré par `crypto.getRandomValues`) ; sinon 400 `invalid_device_id`.
  - Une seule fonction, `core.security.device_hash(raw)` = HMAC-SHA256 avec la clé `DEVICE_ID_PEPPER`, distincte de `PHONE_PEPPER`.
  - La ligne `devices(device_hash, consent_training, consent_at, first_seen_at)` est créée par `auth.service.resolve_device()` au premier contact. `reports` n'écrit jamais dans `devices`.
```

---

### R-19 — medium — Exploitation (NFR-15, NFR-16, NFR-17)

- **Emplacement :** diagramme de déploiement (« sauvegardes quotidiennes chiffrées ») ; aucun AD.
- **Sources :**
  - NFR-15 : sauvegarde quotidienne chiffrée de la base **et des photos**, hors de l'hôte ; perte maximale de 24 h ; une restauration réussie avant les données réelles ; 99 % de disponibilité par mois.
  - NFR-16 : 4 alertes (5xx > 2 % sur 5 min ; sauvegarde échouée ou disque > 85 % ; plafond SMS ; file de classification pleine).
  - NFR-17 : chiffrement au repos, clés contrôlées par l'organisation.
  - Addendum F.1 (CloudWatch, KMS) et C (`/metrics` interne).
  - §6.4 : restauration sur un autre hôte avant la fin du pilote.
- **Constat :**
  - Deux alertes viennent de modules métier (`auth` pour le plafond SMS, `reports` pour la file pleine) sans mécanisme commun.
  - Les photos ne sont pas sauvegardées hors de l'hôte : le versionnement n'est pas une sauvegarde.
  - La cible souveraine auto-hébergée n'a aucune règle de sauvegarde.
  - Les clés (pepper du téléphone, pepper de l'appareil, AES, JWT, TOTP, VAPID) n'ont ni inventaire ni rotation.
- **Correction (nouvel AD) :**

```markdown
### AD-24 — Exploitation : sauvegardes, alertes et clés

- **Binds:** NFR-15, NFR-16, NFR-17, FR-1, FR-14, PRD §6.4.
- **Prevents:** des alertes émises différemment par chaque module, des photos sans sauvegarde, et des clés sans propriétaire ni rotation.
- **Rule:**
  - **Alertes :** les modules n'appellent que `core.alerts.raise_alert(code, context)` (codes : `sms_cap_reached`, `classification_queue_full`, `backup_failed`, `disk_high`, `http_5xx_rate`). Le canal de l'équipe est configuré par `ALERT_WEBHOOK_URL`. Une alerte est dédupliquée 15 min par code.
  - Le taux de 5xx vient de `/metrics` (interne, AD-19).
  - Chaque alerte a un test de déclenchement simulé.
  - **Sauvegardes (pilote, et toute cible `prod`) :** `pg_dump` quotidien et copie quotidienne du bucket vers un stockage **hors de l'hôte** et d'un autre compte, chiffrés avec une clé de l'organisation. Rétention `BACKUP_RETENTION_DAYS` (AD-18). Une restauration complète, sur un autre hôte, est réussie et consignée avant la première donnée réelle.
  - **Clés :** inventaire fixe dans `Settings` : `JWT_SIGNING_KEYS` (avec `kid`, rotation par ajout), `PHONE_PEPPER`, `DEVICE_ID_PEPPER`, `PHONE_ENC_KEY`, `TOTP_ENC_KEY`, `VAPID_PRIVATE_KEY`. Fichier d'environnement au hackathon, KMS ou gestionnaire de secrets au pilote. En `prod`, l'absence d'une clé fait échouer le démarrage.
  - Un pepper n'est jamais renouvelé sans migration de recalcul.
```

---

### R-20 — medium — Mode et Données de démonstration

- **Emplacement :** AD-14 (`is_demo` sur les lignes ; démarrage refusé en `prod` avec `DEMO_MODE`).
- **Sources :**
  - FR-6 : OTP affiché ; bandeau sur tous les écrans.
  - FR-37 : étiquette sur tout écran qui affiche des Données de démonstration ; « se retire en une commande » ; comptes de test ; étiquetage auto des Signalements, Missions et Preuves.
  - S3.
- **Constat :**
  - Le moyen par lequel la PWA sait qu'un objet ou un agrégat est de démonstration n'est pas fixé.
  - Le retrait en une commande se heurte à l'audit en ajout seul (AD-15) et au rôle `teranga_app`.
  - Le chargement du seed en `prod` n'est pas interdit.
  - Le canal de l'OTP de démo (champ de réponse) n'est pas fixé, alors que la PWA et `auth` doivent s'accorder dessus.
- **Correction (ajout à AD-14) :**

```markdown
  - Toute ressource sérialisée qui a `is_demo` l'expose dans l'API. Les agrégats exposent `contains_demo_data` (R-15). `GET /v1/meta` renvoie `{demo_mode, env}` pour le bandeau de FR-6.
  - En Mode démonstration seulement, `POST /v1/auth/otp` renvoie `demo_otp`. Ce champ n'existe pas dans le schéma hors démo (test).
  - `python -m app.cli demo load|purge` : refusé si `ENV=prod`. `purge` tourne avec `teranga_migrator`, supprime les lignes `is_demo` (et leurs objets via `core.storage.purge`) et laisse les entrées d'audit, qui portent `is_demo` pour être filtrées.
```

---

### R-21 — medium — Seuils nommés ambigus ou absents

- **Emplacement :** AD-14 (« 60 %, 150 m, 50 m, 5 km, 48 h, 5 %, limites de débit »).
- **Sources :** FR-7 (50 m de précision), FR-29 (précision du Collecteur ≤ 50 m ; plafond de 50 m sur la précision du Signalement), Glossaire (Doublon : 50 m et 72 h), FR-14 (500), FR-24 (1–10 km, 3 décimales, 100 m, 30 Ko), FR-34 (500 m, 3), FR-8 (300 Ko, 1 Mo, 12 MP), FR-1 (5 min, 5 essais), FR-2 (30 jours), NFR-16 (2 %, 85 %), §6.1.
- **Constat :** « 50 m » désigne quatre seuils distincts. Une équipe les fusionnera en un seul réglage, une autre en créera quatre avec d'autres noms.
- **Correction (remplacer la puce d'AD-14) :**

```markdown
  - Les seuils du PRD sont des réglages nommés, avec une valeur par défaut : `CONFIDENCE_THRESHOLD=0.60` (vérifié contre le JSON du Modèle), `REPORT_ACCURACY_FLAG_M=50`, `PROOF_RADIUS_M=150`, `PROOF_REPORT_ACCURACY_CAP_M=50`, `PROOF_COLLECTOR_ACCURACY_MAX_M=50`, `DUPLICATE_RADIUS_M=50`, `DUPLICATE_WINDOW_H=72`, `MISSION_RADIUS_DEFAULT_KM=5`, `MISSION_RADIUS_MIN_KM=1`, `MISSION_RADIUS_MAX_KM=10`, `MISSION_EXPIRY_H=48`, `PROOF_SAMPLE_RATE=0.05`, `CLASSIFICATION_QUEUE_MAX=500`, `PUBLIC_CELL_M=500`, `PUBLIC_CELL_MIN_COUNT=3`, `COORD_ROUND_DECIMALS=3`, `DISTANCE_ROUND_M=100`, `PHOTO_MAX_BYTES=1_000_000`, `PHOTO_MAX_PIXELS=12_000_000`, `THUMB_MAX_BYTES=30_000`, `OTP_TTL_S=300`, `OTP_MAX_ATTEMPTS=5`, `SESSION_IDLE_DAYS=30`, `ALERT_5XX_RATE=0.02`, `ALERT_DISK_RATIO=0.85`, `SMS_DAILY_CAP`, ainsi que les limites d'AD-20 et les durées d'AD-18.
```

---

### R-22 — medium — Topologie des origines non fixée

- **Emplacement :** AD-9 (cookie `SameSite=Strict; Path=/v1/auth`) ; AD-11 ; squelette.
- **Sources :** NFR-8 (CORS limité aux origines de la PWA ; photos sur un domaine distinct) ; S4.
- **Constat :** un cookie `SameSite=Strict` n'est envoyé que si la PWA et l'API sont sur le même site. Une équipe qui met l'API sur un autre domaine casse le renouvellement de session. Une autre ouvrira un CORS large avec `credentials`.
- **Correction (ligne de convention) :**

```markdown
| Origines | La PWA et l'API partagent **une seule origine** (`https://<APP_HOST>`, Caddy sert `/` et `/v1`) : pas de CORS en production. Les photos sont servies depuis `https://<MEDIA_HOST>`, sur un domaine enregistrable distinct, sans cookie. Les tuiles viennent de `<TILES_HOST>`. Ces trois hôtes sont les seuls dans la CSP (AD-19). |
```

---

### R-23 — low — Écarts de nom ou de forme avec l'addendum

- **Emplacement :** AD-2, AD-8, AD-14.
- **Constat et correction :** l'épine peut trancher, mais doit dire qu'elle **remplace** l'addendum, sinon les stories qui citent l'addendum divergeront.
  - `proofs` (épine) / `collection_proofs` (B.1, point 8) ; `proof_reviews` (table) / `review_status` + `review_reason` (colonnes).
  - `staff_second_factors` / `users.totp_secret` (B.1, point 15).
  - `classification_status: "pending"` (AD-8, champ plat) / `classification.status = pending` (addendum C, objet imbriqué).
  - `ENV ∈ {dev, demo, prod}` (AD-14) / `ENV=production` (addendum C S3 et F.2, `.env.example`).
- **Ligne à ajouter sous la table d'AD-2 :**

```markdown
> Noms faisant foi (remplacent l'addendum B.1 et C) : `proofs` (et non `collection_proofs`), `proof_reviews` (une ligne par revue ; `proofs` n'a pas de colonne de revue), `staff_second_factors` (et non `users.totp_secret`), champ de réponse `classification_status` au premier niveau, `ENV=prod` (et non `production`). Les stories citent l'épine, pas l'addendum, pour ces noms.
```

---

### R-24 — low — Points secondaires

- **NFR-9, liste blanche publique :** fixer la liste close dans AD-9 : `/healthz`, `/readyz`, `POST /v1/reports` (anonyme), `GET /v1/public/map`. Ajouter une catégorie « principal appareil » pour `GET /v1/reports/mine`, `DELETE /v1/reports/{id}` et `PUT /v1/device/consent`, testée comme un rôle à part entière.
- **`/readyz` et Modèle chargé :** la Classification serveur tourne dans le worker (AD-8). Écrire : « `/readyz` de l'API vérifie la présence et le `sha256` des artefacts du Modèle ; le worker publie un battement dans Valkey (`worker:heartbeat`, 60 s), vérifié par `/readyz` ». Cela évite de charger le Modèle dans chaque processus API.
- **Garage `[ASSUMPTION]` :** vérifier qu'il prend en charge le versionnement, le cycle de vie et le chiffrement côté serveur. S'il ne le fait pas, AD-18 (purge de toutes les versions) et AD-24 (copie hors de l'hôte) restent valables, mais le chiffrement au repos de la cible souveraine passe par le disque. Entrée Différé :
  `- **Garage en cible souveraine** : versionnement, cycle de vie et chiffrement côté serveur à vérifier avant la sortie du pilote ; sinon chiffrement du disque et copie hors de l'hôte (AD-24).`
- **FR-21, anonyme :** ligne de convention : « Les changements de Statut depuis la dernière visite d'un anonyme se calculent dans la PWA (derniers Statuts vus, mémorisés dans Dexie) ; le module `notifications` ne gère que les comptes ».
- **Rattachement appareil → compte :** à figer pour éviter qu'`auth` réécrive les `owner_key`. Entrée Différé :
  `- **Rattachement des Signalements anonymes à un compte** : non prévu au MVP ; `owner_key` est immuable (AD-5).`
- **Sources de l'épine :** `docs/dossier-technique.md` est cité en source alors que l'addendum en déclare plusieurs parties remplacées (G, « Documents sources »). Ajouter dans l'en-tête : « En cas de conflit, ordre de priorité : PRD > addendum > dossier technique ».
- **Lots (FR-39, FR-40) :** le contact du Collecteur n'est donné qu'après une demande, par `lots.service`, qui appelle `auth.service.get_contact(collector_id)` (sens autorisé). Le contact n'apparaît jamais dans une liste.

---

## Vérifications demandées : ce qui est conforme

- **Statuts et Statuts de Mission ↔ Glossaire :** transitions et terminaux conformes, y compris le retour `assigné → validé` sur `annulée`/`expirée`. Les codes de Mission `active/completed/cancelled/expired` sont conformes à B.1, point 9. Seuls manquent les autres énumérations (R-10).
- **`retained_type`, `duplicate_of`, `flags`, `pile_size`, `received_at` :** ces colonnes vivent dans `reports`, ce qui est cohérent avec la propriété d'AD-2. Elles ne sont pas nommées dans l'épine, ce qui est acceptable pour des colonnes internes à un seul module, sauf `received_at` (R-15) et `duplicate_of` (R-16).
- **S1, S2, S3, S4, S5, S10, S12 :** couverts (AD-5, AD-10, AD-14, AD-9, AD-15, AD-8), sous réserve de R-01 pour S4/S5. **S6, S7, S8, S9, S11 :** partiels ou perdus (R-05, R-06, R-03, R-04).
- **Concurrence de l'acceptation (FR-25) :** AD-4 est solide, sauf le réenvoi par le même Collecteur (R-11).
