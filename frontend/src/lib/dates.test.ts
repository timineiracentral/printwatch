import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { presetLast7Days, presetMonthToDate, presetToday } from './dates'

/** 2026-05-27 12:00 em America/Sao_Paulo (UTC-3) */
const FIXED_UTC = new Date('2026-05-27T15:00:00.000Z')

describe('dates presets (America/Sao_Paulo)', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(FIXED_UTC)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('presetToday uses calendar today in SP', () => {
    expect(presetToday()).toEqual({
      date_from: '2026-05-27',
      date_to: '2026-05-27',
    })
  })

  it('presetLast7Days spans 7 inclusive days ending today', () => {
    expect(presetLast7Days()).toEqual({
      date_from: '2026-05-21',
      date_to: '2026-05-27',
    })
  })

  it('presetMonthToDate from first of month through today', () => {
    expect(presetMonthToDate()).toEqual({
      date_from: '2026-05-01',
      date_to: '2026-05-27',
    })
  })
})
