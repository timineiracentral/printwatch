import { useCallback, useSyncExternalStore } from 'react'
import {
  clearFiltersDefaults,
  filtersToSearchParams,
  parseFiltersFromUrl,
} from '../lib/filters'
import {
  presetLast7Days,
  presetMonthToDate,
  presetToday,
} from '../lib/dates'
import type { JobFilters } from '../types/api'

const SEARCH_CHANGE = 'printwatch:search-change'

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

function replaceSearch(filters: JobFilters): void {
  const qs = filtersToSearchParams(filters).toString()
  const next = qs ? `?${qs}` : ''
  if (window.location.search !== next) {
    const path = `${window.location.pathname}${next}${window.location.hash}`
    window.history.replaceState(null, '', path)
    window.dispatchEvent(new Event(SEARCH_CHANGE))
  }
}

export type DatePresetName = 'today' | 'last7' | 'month'

function presetDates(name: DatePresetName): { date_from: string; date_to: string } {
  switch (name) {
    case 'today':
      return presetToday()
    case 'last7':
      return presetLast7Days()
    case 'month':
      return presetMonthToDate()
  }
}

export function useUrlFilters() {
  const search = useSyncExternalStore(
    subscribeToSearch,
    getSearchSnapshot,
    () => '',
  )

  const filters = parseFiltersFromUrl(search)

  const setFilters = useCallback(
    (partial: Partial<JobFilters>) => {
      const next: JobFilters = { ...filters, ...partial }
      const filterKeys = [
        'username',
        'printer',
        'search',
        'date_from',
        'date_to',
        'size',
      ] as const
      const filterChanged = filterKeys.some(
        (key) => key in partial && partial[key] !== filters[key],
      )
      if (filterChanged && !('page' in partial)) {
        next.page = 1
      }
      replaceSearch(next)
    },
    [filters],
  )

  const setPage = useCallback(
    (page: number) => {
      setFilters({ page })
    },
    [setFilters],
  )

  const clearFilters = useCallback(() => {
    replaceSearch(clearFiltersDefaults())
  }, [])

  const applyDatePreset = useCallback(
    (name: DatePresetName) => {
      const dates = presetDates(name)
      setFilters({ ...dates, page: 1 })
    },
    [setFilters],
  )

  return { filters, setFilters, setPage, clearFilters, applyDatePreset }
}
