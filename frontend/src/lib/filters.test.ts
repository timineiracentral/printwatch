import { describe, expect, it } from 'vitest'
import {
  clearFiltersDefaults,
  filtersToSearchParams,
  parseFiltersFromUrl,
} from './filters'

describe('filters', () => {
  it('clearFiltersDefaults returns page=1 size=50 without filters', () => {
    expect(clearFiltersDefaults()).toEqual({ page: 1, size: 50 })
  })

  it('round-trips URLSearchParams omitting empty keys', () => {
    const original = {
      page: 2,
      size: 100,
      username: 'felipe',
      printer: 'hp-floor-1',
      search: 'relatorio',
      date_from: '2026-05-01',
      date_to: '2026-05-27',
    }
    const params = filtersToSearchParams(original)
    expect(parseFiltersFromUrl(`?${params.toString()}`)).toEqual(original)
  })

  it('omits empty string filter keys when serializing', () => {
    const params = filtersToSearchParams({
      page: 1,
      size: 50,
      username: '',
      search: '  ',
    })
    expect(params.has('username')).toBe(false)
    expect(params.has('search')).toBe(false)
    expect(params.get('page')).toBe('1')
    expect(params.get('size')).toBe('50')
  })

  it('uses defaults for missing or invalid page/size', () => {
    expect(parseFiltersFromUrl('?page=0&size=-1')).toEqual({ page: 1, size: 50 })
    expect(parseFiltersFromUrl('')).toEqual({ page: 1, size: 50 })
  })
})
