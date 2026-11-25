// Point dans un MultiPolygon, limite incluse (story 1.8).
import { describe, expect, it } from 'vitest'

import type { MultiPolygon, Position } from '../../api/config.ts'
import { multiPolygonCovers } from './geo.ts'

function square(lng: number, lat: number, size: number): Position[] {
  return [
    [lng, lat],
    [lng + size, lat],
    [lng + size, lat + size],
    [lng, lat + size],
    [lng, lat],
  ]
}

// Carré de Dakar avec un trou, et une île à part (comme Gorée).
const ZONE: MultiPolygon = {
  type: 'MultiPolygon',
  coordinates: [
    [square(-17.5, 14.6, 0.2), square(-17.45, 14.65, 0.05)],
    [square(-17.25, 14.66, 0.01)],
  ],
}

describe('multiPolygonCovers', () => {
  it('dedans : vrai', () => {
    expect(multiPolygonCovers(ZONE, 14.7, -17.48)).toBe(true)
  })

  it('dehors (Thiès) : faux', () => {
    expect(multiPolygonCovers(ZONE, 14.791, -16.9359)).toBe(false)
  })

  it('sur un sommet ou sur un côté : vrai (limite incluse)', () => {
    expect(multiPolygonCovers(ZONE, 14.6, -17.5)).toBe(true)
    expect(multiPolygonCovers(ZONE, 14.6, -17.4)).toBe(true)
    expect(multiPolygonCovers(ZONE, 14.7, -17.5)).toBe(true)
    expect(multiPolygonCovers(ZONE, 14.8, -17.35)).toBe(true)
  })

  it('juste au-delà d’un côté : faux', () => {
    expect(multiPolygonCovers(ZONE, 14.7, -17.5001)).toBe(false)
    expect(multiPolygonCovers(ZONE, 14.5999, -17.45)).toBe(false)
  })

  it('dans un trou : faux ; sur la limite du trou : vrai', () => {
    expect(multiPolygonCovers(ZONE, 14.675, -17.425)).toBe(false)
    expect(multiPolygonCovers(ZONE, 14.65, -17.425)).toBe(true)
  })

  it('dans le second polygone (île) : vrai', () => {
    expect(multiPolygonCovers(ZONE, 14.665, -17.245)).toBe(true)
  })

  it('sens de parcours indifférent', () => {
    const reversed: MultiPolygon = {
      type: 'MultiPolygon',
      coordinates: [[square(-17.5, 14.6, 0.2).reverse()]],
    }
    expect(multiPolygonCovers(reversed, 14.7, -17.48)).toBe(true)
    expect(multiPolygonCovers(reversed, 14.9, -17.48)).toBe(false)
  })

  it('coordonnées non finies : faux', () => {
    expect(multiPolygonCovers(ZONE, Number.NaN, -17.48)).toBe(false)
    expect(multiPolygonCovers(ZONE, 14.7, Number.POSITIVE_INFINITY)).toBe(false)
  })
})
