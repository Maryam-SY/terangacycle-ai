// Identifiant d'appareil : format, persistance, discrétion (IndexedDB simulée).
import 'fake-indexeddb/auto'

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { db } from './db.ts'
import { DEVICE_ID_PATTERN, ensureDeviceId, generateDeviceId } from './device.ts'

const CONSOLE_METHODS = ['log', 'info', 'warn', 'error', 'debug', 'trace'] as const

beforeEach(async () => {
  await db.meta.clear()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('generateDeviceId', () => {
  it('43 caractères base64url, sans remplissage', () => {
    for (let i = 0; i < 200; i += 1) {
      const id = generateDeviceId()
      expect(id).toMatch(DEVICE_ID_PATTERN)
      expect(id).not.toMatch(/[+/=]/)
    }
  })

  it('encode exactement 32 octets', () => {
    const id = generateDeviceId()
    const base64 = id.replaceAll('-', '+').replaceAll('_', '/') + '='
    expect(Buffer.from(base64, 'base64')).toHaveLength(32)
  })

  it('tire ses octets de crypto.getRandomValues', () => {
    const spy = vi.spyOn(crypto, 'getRandomValues').mockImplementation((array) => {
      const bytes = array as Uint8Array
      bytes.fill(0xff)
      return array
    })
    expect(generateDeviceId()).toBe('_'.repeat(42) + '8')
    expect(spy).toHaveBeenCalledOnce()
    expect((spy.mock.calls[0][0] as Uint8Array).length).toBe(32)
  })
})

describe('ensureDeviceId', () => {
  it('premier lancement : crée l’identifiant et le mémorise dans meta', async () => {
    const id = await ensureDeviceId()
    expect(id).toMatch(DEVICE_ID_PATTERN)
    expect(await db.meta.get('deviceId')).toEqual({ key: 'deviceId', value: id })
  })

  it('relance : garde le même identifiant, y compris après réouverture de la base', async () => {
    const first = await ensureDeviceId()
    expect(await ensureDeviceId()).toBe(first)
    db.close()
    await db.open()
    expect(await ensureDeviceId()).toBe(first)
  })

  it('appels simultanés : un seul identifiant', async () => {
    const ids = await Promise.all([ensureDeviceId(), ensureDeviceId(), ensureDeviceId()])
    expect(new Set(ids).size).toBe(1)
    expect((await db.meta.get('deviceId'))?.value).toBe(ids[0])
  })

  it('remplace une valeur mémorisée invalide', async () => {
    await db.meta.put({ key: 'deviceId', value: 'trop-court' })
    const id = await ensureDeviceId()
    expect(id).toMatch(DEVICE_ID_PATTERN)
    expect((await db.meta.get('deviceId'))?.value).toBe(id)
  })

  it('n’écrit rien dans la console', async () => {
    const spies = CONSOLE_METHODS.map((method) =>
      vi.spyOn(console, method).mockImplementation(() => undefined),
    )
    await ensureDeviceId()
    await ensureDeviceId()
    for (const spy of spies) expect(spy).not.toHaveBeenCalled()
  })
})
