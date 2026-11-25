# Zones de Dakar — `zones-dakar.geojson`

Données chargées dans la table `zones` par la migration `0002_zones` (story 1.8).

## Source et licence

- **Source :** OpenStreetMap, extraction Overpass du 25/11/2026 ;
  département de Dakar, relation [12982139](https://www.openstreetmap.org/relation/12982139).
- **Date de la base OSM :** `2026-11-25T14:30:28Z` (champ `osm3s.timestamp_osm_base` de
  l'extraction, recopié dans `osm_base` du fichier).
- **Licence :** [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
  © les contributeurs d'OpenStreetMap. Toute réutilisation de ce fichier, ou d'une base
  qui en dérive, doit citer cette attribution et rester sous ODbL.

Seul le fichier dérivé est versionné : l'extraction OSM brute ne l'est pas.

## Contenu

Une `FeatureCollection` ; chaque Feature est une Zone en `MultiPolygon` (WGS 84,
6 décimales), avec les propriétés :

| Propriété | Sens |
|---|---|
| `id` | identifiant lisible et unique (nom sans accents ; homonymes suffixés par leur référence OSM, par exemple `-w1463235703`) |
| `name` | nom OSM (préfixe « Commune de » retiré pour les communes) |
| `kind` | `commune` ou `quartier` |
| `parent_id` | Zone parente : aucune pour Dakar, `dakar` pour les communes, une commune pour les quartiers |
| `osm_ref` | élément OSM d'origine (`relation/…` ou `way/…`) |

Hiérarchie :

- **Dakar** : la relation 12982139 (`commune`, sans parent, identifiant `dakar`) ;
- **les 19 communes d'arrondissement** : relations `admin_level=8` (parent `dakar`) ;
- **les quartiers** que l'OSM dessine : voies et relations `place=suburb|quarter|neighbourhood`,
  ou limites administratives de niveau 9 et 10. Parent : la plus petite commune qui contient
  leur point intérieur (à défaut, Dakar). Ils sont partiels : hors quartier, un point est
  rattaché à sa commune.

Traitement (`backend/scripts/build_zones.py`) : chaque voie est simplifiée (Douglas-Peucker,
environ 3 m, extrémités gardées pour que deux Zones voisines partagent la même limite), les
anneaux sont assemblés, et toute Zone sans nom, ouverte, plate, qui se recoupe ou hors de
Dakar est écartée (liste affichée à la construction). Le fichier fait au plus 400 Ko.

## Reconstruction

1. Requête Overpass (sortie `out geom`, JSON), par exemple sur
   <https://overpass-api.de/api/interpreter> :

   ```
   [out:json];
   rel(12982139);map_to_area->.a;(rel(12982139);rel(area.a)["boundary"="administrative"]["admin_level"~"^(8|9|10)$"];rel(area.a)["place"~"^(suburb|quarter|neighbourhood)$"];way(area.a)["place"~"^(suburb|quarter|neighbourhood)$"];way(area.a)["boundary"="administrative"]["admin_level"~"^(9|10)$"];);out geom;
   ```

   Enregistrer la réponse hors du dépôt, par exemple `dakar-osm.json`.

2. Construction, depuis la racine du dépôt (bibliothèque standard Python seulement) :

   ```
   python backend/scripts/build_zones.py dakar-osm.json -o backend/migrations/data/zones-dakar.geojson
   ```

3. Mettre à jour la date de la base OSM ci-dessus. La migration `0002_zones` lit ce fichier
   à son exécution : une base neuve reçoit la nouvelle version, mais une base déjà migrée
   ne la reçoit que par une **nouvelle migration** qui recharge la table.
