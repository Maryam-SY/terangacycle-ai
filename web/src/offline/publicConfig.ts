// Configuration publique sur l'appareil, gardée dans Dexie (`meta.publicConfig`).
// Avec une configuration gardée valide : elle sert tout de suite (aucune attente réseau,
// même sur une connexion lente), et une lecture réseau en arrière-plan la met à jour.
// Sans configuration gardée : lecture réseau ; hors ligne la toute première fois, une
// connexion est nécessaire.
import { fetchPublicConfig, parsePublicConfig, type PublicConfig } from '../api/config.ts'
import { getMeta, setMeta } from './db.ts'

export type ConfigSource = 'network' | 'cache'

export interface LoadedConfig {
  config: PublicConfig
  source: ConfigSource
  /** Mise à jour en arrière-plan (source `cache` seulement) : la configuration reçue et
   *  gardée, ou `undefined` si le réseau a échoué. Ne rejette jamais. */
  refreshed?: Promise<PublicConfig | undefined>
}

/** Ni réseau ni configuration gardée : une première connexion est nécessaire. */
export class ConfigUnavailableError extends Error {
  constructor() {
    super('configuration publique indisponible : connexion nécessaire une première fois')
    this.name = 'ConfigUnavailableError'
  }
}

/** Dernière configuration gardée, validée ; `undefined` si absente, illisible ou invalide. */
export async function getCachedPublicConfig(): Promise<PublicConfig | undefined> {
  try {
    return parsePublicConfig(await getMeta('publicConfig'))
  } catch {
    return undefined
  }
}

/** Lecture réseau, gardée dans Dexie si elle réussit ; `undefined` si elle échoue. */
async function fetchAndStore(
  fetchConfig: () => Promise<PublicConfig>,
): Promise<PublicConfig | undefined> {
  let config: PublicConfig
  try {
    config = await fetchConfig()
  } catch {
    return undefined
  }
  // Un échec d'écriture ne bloque pas : la configuration reçue sert tout de suite.
  await setMeta('publicConfig', config).catch(() => undefined)
  return config
}

export async function loadPublicConfig(
  fetchConfig: () => Promise<PublicConfig> = fetchPublicConfig,
): Promise<LoadedConfig> {
  const cached = await getCachedPublicConfig()
  if (cached) return { config: cached, source: 'cache', refreshed: fetchAndStore(fetchConfig) }
  const config = await fetchAndStore(fetchConfig)
  if (config) return { config, source: 'network' }
  throw new ConfigUnavailableError()
}
