// Types du client API (story 1.13), générés depuis src/api/openapi.json, lui-même exporté
// par le backend (`uv run python scripts/export_openapi.py`, dans backend/). Écrit
// src/api/schema.d.ts ; lancé par `npm run api:types`. Fichier versionné : la CI le
// régénère et refuse toute différence.
//
// Transformation : un champ `format: binary` (la photo du Signalement) devient un `Blob`,
// ce qu'envoie la PWA, au lieu d'une chaîne.
import { readFileSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

import openapiTS, { astToString } from 'openapi-typescript'
import ts from 'typescript'

const INPUT = new URL('../src/api/openapi.json', import.meta.url)
const OUTPUT = new URL('../src/api/schema.d.ts', import.meta.url)

const BLOB = ts.factory.createTypeReferenceNode(ts.factory.createIdentifier('Blob'))
const NULL = ts.factory.createLiteralTypeNode(ts.factory.createNull())

const HEADER = `// Généré par scripts/gen-api-types.mjs depuis src/api/openapi.json : ne pas modifier.
// Régénérer : \`uv run python scripts/export_openapi.py\` (backend/), puis \`npm run api:types\`.
`

const ast = await openapiTS(JSON.parse(readFileSync(INPUT, 'utf8')), {
  // Un champ avec valeur par défaut (`comment`, `waste_type`, `consent` de ReportMeta)
  // reste facultatif : le client peut l'omettre, le serveur applique la valeur par défaut.
  defaultNonNullable: false,
  transform(schemaObject) {
    if (schemaObject.format !== 'binary') return undefined
    return schemaObject.nullable ? ts.factory.createUnionTypeNode([BLOB, NULL]) : BLOB
  },
})

// Fins de ligne LF, fin de ligne finale : mêmes octets sur tous les systèmes.
const source = `${HEADER}\n${astToString(ast).replace(/\r\n/g, '\n').trimEnd()}\n`
writeFileSync(OUTPUT, source)
console.log(`Types écrits : ${fileURLToPath(OUTPUT)}`)
