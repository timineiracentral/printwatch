import type { JobFilters } from '../types/api'

export type { JobFilters } from '../types/api'

const DEFAULT_PAGE = 1
const DEFAULT_SIZE = 50

export function clearFiltersDefaults(): JobFilters {
  return { page: DEFAULT_PAGE, size: DEFAULT_SIZE }
}

export function hasActiveFilters(filters: JobFilters): boolean {
  return !!(
    filters.username?.trim() ||
    filters.printer?.trim() ||
    filters.search?.trim() ||
    filters.date_from ||
    filters.date_to ||
    filters.outside_policy != null
  )
}

export function parseFiltersFromUrl(search: string): JobFilters {
  const params = new URLSearchParams(
    search.startsWith('?') ? search.slice(1) : search,
  )
  const filters: JobFilters = {
    page: parsePositiveInt(params.get('page'), DEFAULT_PAGE),
    size: parsePositiveInt(params.get('size'), DEFAULT_SIZE),
  }

  const username = params.get('username')?.trim()
  if (username) filters.username = username

  const printer = params.get('printer')?.trim()
  if (printer) filters.printer = printer

  const searchTerm = params.get('search')?.trim()
  if (searchTerm) filters.search = searchTerm

  const dateFrom = params.get('date_from')?.trim()
  if (dateFrom) filters.date_from = dateFrom

  const dateTo = params.get('date_to')?.trim()
  if (dateTo) filters.date_to = dateTo

  const outsidePolicy = params.get('outside_policy')?.trim()
  if (outsidePolicy === 'true') filters.outside_policy = true
  if (outsidePolicy === 'false') filters.outside_policy = false

  return filters
}

export function filtersToSearchParams(filters: JobFilters): URLSearchParams {
  const params = new URLSearchParams()
  params.set('page', String(filters.page ?? DEFAULT_PAGE))
  params.set('size', String(filters.size ?? DEFAULT_SIZE))

  if (filters.date_from) params.set('date_from', filters.date_from)
  if (filters.date_to) params.set('date_to', filters.date_to)
  const username = filters.username?.trim()
  if (username) params.set('username', username)

  const printer = filters.printer?.trim()
  if (printer) params.set('printer', printer)

  const search = filters.search?.trim()
  if (search) params.set('search', search)

  if (filters.outside_policy === true) params.set('outside_policy', 'true')
  if (filters.outside_policy === false) params.set('outside_policy', 'false')

  return params
}

function parsePositiveInt(value: string | null, fallback: number): number {
  if (!value) return fallback
  const parsed = Number.parseInt(value, 10)
  return Number.isFinite(parsed) && parsed >= 1 ? parsed : fallback
}
