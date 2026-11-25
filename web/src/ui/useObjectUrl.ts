import { useEffect, useState } from 'react'

/** URL `blob:` d'un Blob à afficher (aperçu d'une photo), révoquée quand le Blob change
 *  ou que le composant disparaît ; `undefined` avant sa création ou sans Blob. */
export function useObjectUrl(blob: Blob | undefined): string | undefined {
  const [url, setUrl] = useState<{ blob: Blob; url: string }>()

  useEffect(() => {
    if (!blob) return undefined
    const created = URL.createObjectURL(blob)
    setUrl({ blob, url: created })
    return () => URL.revokeObjectURL(created)
  }, [blob])

  // Une URL d'un Blob précédent (déjà révoquée) n'est jamais rendue.
  return url && url.blob === blob ? url.url : undefined
}
