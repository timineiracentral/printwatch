import { useCallback, useEffect, useSyncExternalStore } from 'react'
import {
  presetLast30Days,
  presetLast7Days,
  presetLast90Days,
  presetMonthToDate,
  presetToday,
} from '../lib/dates'
import type { ManagerFilters } from '../types/api'

const SEARCH_CHANGE = 'printwatch:manager-search-change'

export type ManagerDatePreset =
  | 'today'
  | 'last7'
  | 'last30'
  | 'last90'
  | 'month'
  | 'custom'

function getSearchSnapshot(): string {
  return window.location.search
}

function subscribeToSearch(onStoreChange: () => void): () => void {
  const handler = () => onStoreChange()
  window.addEventListener('popstate', handler)
  window.addEventListener(SEARCH_CHANGE, handler)
  return () => {
    window.removeEventListener('popstate', handler)
    window.removeEventListener(SEARCH_CHANGE, handler)
  }
}

function parseManagerFilters(search: string): ManagerFilters {
  const params = new URLSearchParams(search)
  const date_from = params.get('date_from') ?? ''
  const date_to = params.get('date_to') ?? ''
  const preset = params.get('preset') ?? undefined
  return { date_from, date_to, preset }
}

function filtersToSearchParams(filters: ManagerFilters): URLSearchParams {
  const sp = new URLSearchParams()
  sp.set('date_from', filters.date_from)
  sp.set('date_to', filters.date_to)
  if (filters.preset) {
    sp.set('preset', filters.preset)
  }
  return sp
}

function replaceSearch(filters: ManagerFilters): void {
  const qs = filtersToSearchParams(filters).toString()
  const next = qs ? `?${qs}` : ''
  if (window.location.search !== next) {
    const path = `${window.location.pathname}${next}${window.location.hash}`
    window.history.replaceState(null, '', path)
    window.dispatchEvent(new Event(SEARCH_CHANGE))
  }
}

function presetDates(name: ManagerDatePreset): ManagerFilters {
  switch (name) {
    case 'today': {
      const d = presetToday()
      return { ...d, preset: 'today' }
    }
    case 'last7': {
      const d = presetLast7Days()
      return { ...d, preset: 'last7' }
    }
    case 'last30': {
      const d = presetLast30Days()
      return { ...d, preset: 'last30' }
    }
    case 'last90': {
      const d = presetLast90Days()
      return { ...d, preset: 'last90' }
    }
    case 'month': {
      const d = presetMonthToDate()
      return { ...d, preset: 'month' }
    }
    case 'custom':
      return presetLast30Days()
  }
}

export function useUrlManagerFilters() {
  const search = useSyncExternalStore(
    subscribeToSearch,
    getSearchSnapshot,
    () => '',
  )

  const filters = parseManagerFilters(search)

  useEffect(() => {
    if (!filters.date_from || !filters.date_to) {
      replaceSearch(presetDates('last30'))
    }
  }, [filters.date_from, filters.date_to])

  const setFilters = useCallback((partial: Partial<ManagerFilters>) => {
    const current = parseManagerFilters(getSearchSnapshot())
    const next: ManagerFilters = {
      date_from: partial.date_from ?? current.date_from,
      date_to: partial.date_to ?? current.date_to,
      preset: partial.preset ?? current.preset,
    }
    replaceSearch(next)
  }, [])

  const applyDatePreset = useCallback((name: ManagerDatePreset) => {
    replaceSearch(presetDates(name))
  }, [])

  const effective =
    filters.date_from && filters.date_to
      ? filters
      : { ...presetLast30Days(), preset: 'last30' as const }

  return { filters: effective, setFilters, applyDatePreset }
}
