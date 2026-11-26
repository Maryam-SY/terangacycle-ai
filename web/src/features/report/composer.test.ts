import { describe, expect, it } from 'vitest'

import { toggleWasteType } from '../classify/wasteTypes.ts'
import {
  COMMENT_MAX,
  clampCodePoints,
  codePointLength,
  formatDuration,
  pickVoiceMimeType,
} from './composer.ts'

describe('commentaire', () => {
  it('compte en points de code, comme le serveur', () => {
    expect(codePointLength('é')).toBe(1)
    expect(codePointLength('🗑')).toBe(1) // 2 unités UTF-16, 1 point de code
  })

  it('s’arrête à 280 points de code sans couper un emoji', () => {
    const long = '🗑'.repeat(COMMENT_MAX + 5)
    const clamped = clampCodePoints(long)
    expect(codePointLength(clamped)).toBe(COMMENT_MAX)
    expect(clamped).toBe('🗑'.repeat(COMMENT_MAX))
    expect(clampCodePoints('court')).toBe('court')
  })
})

describe('note vocale', () => {
  it('choisit le premier format pris en charge, sinon le choix du navigateur', () => {
    expect(pickVoiceMimeType((type) => type.startsWith('audio/webm'))).toBe(
      'audio/webm;codecs=opus',
    )
    expect(pickVoiceMimeType((type) => type === 'audio/mp4')).toBe('audio/mp4')
    expect(pickVoiceMimeType(() => false)).toBeUndefined()
  })

  it('affiche la durée en m:ss', () => {
    expect(formatDuration(0)).toBe('0:00')
    expect(formatDuration(7.9)).toBe('0:07')
    expect(formatDuration(30)).toBe('0:30')
  })
})

describe('type de déchet', () => {
  it('se choisit en un toucher et se retire en touchant le même', () => {
    expect(toggleWasteType(null, 'plastic')).toBe('plastic')
    expect(toggleWasteType('plastic', 'metal')).toBe('metal')
    expect(toggleWasteType('plastic', 'plastic')).toBeNull()
  })
})
