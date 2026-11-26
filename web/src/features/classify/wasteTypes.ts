// Les 5 Types de déchet (codes de l'API, ordre des classes du Modèle, AD-7). Libellés par
// i18n (`waste.<code>`), couleurs par jetons provisoires `--color-waste-<code>` (theme.css).
export const WASTE_TYPES = ['plastic', 'metal', 'glass', 'organic', 'mixed'] as const

export type WasteType = (typeof WASTE_TYPES)[number]

/** Toucher l'option déjà choisie la retire : le Type de déchet est facultatif. */
export function toggleWasteType(current: WasteType | null, touched: WasteType): WasteType | null {
  return current === touched ? null : touched
}
