import { describe, expect, it } from 'vitest'
import { formatMediaLabel } from './media'

describe('formatMediaLabel', () => {
  it('maps iso_a4 to A4', () => {
    expect(formatMediaLabel('iso_a4_210x297mm')).toBe('A4')
  })

  it('maps na_letter to Carta', () => {
    expect(formatMediaLabel('na_letter_8.5x11in')).toBe('Carta')
  })

  it('returns raw value for unknown media', () => {
    expect(formatMediaLabel('custom_legal')).toBe('custom_legal')
  })

  it('handles null and empty', () => {
    expect(formatMediaLabel(null)).toBe('')
    expect(formatMediaLabel('')).toBe('')
  })
})
