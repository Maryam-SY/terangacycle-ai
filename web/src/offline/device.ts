// Identifiant d'appareil du Citoyen anonyme (AD-9) : 32 octets aléatoires en base64url
// sans remplissage (43 caractères), créé au premier lancement et gardé dans `meta`.
// Donnée personnelle : jamais affichée, jamais écrite dans la console. Elle partira dans
// l'en-tête X-Device-Id avec la story 1.11, pas avant.
import { db } from './db.ts'

const KEY = 'deviceId'
const BYTES = 32
export const DEVICE_ID_PATTERN = /^[A-Za-z0-9_-]{43}$/

function base64url(bytes: Uint8Array): string {
  let binary = ''
  for (const byte of bytes) binary += String.fromCharCode(byte)
  return btoa(binary).replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/, '')
}

export function generateDeviceId(): string {
  return base64url(crypto.getRandomValues(new Uint8Array(BYTES)))
}

/** Identifiant de l'appareil : celui de `meta` s'il est valide, sinon un nouveau, mémorisé.
 *  Lecture et écriture dans une même transaction : deux onglets ouverts au premier
 *  lancement ne créent pas deux identifiants. */
export async function ensureDeviceId(): Promise<string> {
  return db.transaction('rw', db.meta, async () => {
    const existing = (await db.meta.get(KEY))?.value
    if (typeof existing === 'string' && DEVICE_ID_PATTERN.test(existing)) return existing
    const created = generateDeviceId()
    await db.meta.put({ key: KEY, value: created })
    return created
  })
}
