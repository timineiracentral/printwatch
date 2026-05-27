import { baseUrl } from './client'
import type { ExportFilters } from '../types/api'

export class ExportCapError extends Error {
  readonly detail: unknown

  constructor(detail: unknown) {
    super(String(detail))
    this.name = 'ExportCapError'
    this.detail = detail
  }
}

function exportFiltersToSearchParams(filters: ExportFilters): URLSearchParams {
  const params = new URLSearchParams()

  if (filters.date_from) params.set('date_from', filters.date_from)
  if (filters.date_to) params.set('date_to', filters.date_to)

  const username = filters.username?.trim()
  if (username) params.set('username', username)

  const printer = filters.printer?.trim()
  if (printer) params.set('printer', printer)

  const search = filters.search?.trim()
  if (search) params.set('search', search)

  return params
}

export async function downloadCsv(filters: ExportFilters): Promise<void> {
  const qs = exportFiltersToSearchParams(filters).toString()
  const url = `${baseUrl}/export/csv${qs ? `?${qs}` : ''}`
  const res = await fetch(url)

  if (res.status === 400) {
    const body = await res.json().catch(() => ({}))
    throw new ExportCapError(
      (body as { detail?: unknown }).detail ?? 'Export limit exceeded',
    )
  }

  if (!res.ok) {
    throw new Error('export failed')
  }

  const blob = await res.blob()
  const filename =
    res.headers.get('Content-Disposition')?.match(/filename="(.+)"/)?.[1] ??
    'print_jobs.csv'
  const objectUrl = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(objectUrl)
}
