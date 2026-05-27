import { getJson, patchJson } from './client'
import type {
  JobFilters,
  JobLineFilters,
  JobLineOut,
  JobOut,
  Page,
} from '../types/api'
import { filtersToSearchParams } from '../lib/filters'

export function fetchJobs(filters: JobFilters): Promise<Page<JobOut>> {
  return getJson<Page<JobOut>>('/jobs', filtersToSearchParams(filters))
}

function jobLineFiltersToParams(filters: JobLineFilters): URLSearchParams {
  const params = new URLSearchParams()
  params.set('printer', filters.printer)
  params.set('username', filters.username)
  params.set('job_id', String(filters.job_id))
  params.set('minute_bucket', filters.minute_bucket)
  if (filters.job_name != null && filters.job_name !== '') {
    params.set('job_name', filters.job_name)
  }
  return params
}

export function fetchJobLines(filters: JobLineFilters): Promise<JobLineOut[]> {
  return getJson<JobLineOut[]>('/jobs/lines', jobLineFiltersToParams(filters))
}

export function patchLineColorMode(
  lineId: number,
  color_mode: 'mono' | 'color',
): Promise<JobLineOut> {
  return patchJson<JobLineOut>(`/jobs/lines/${lineId}/color-mode`, { color_mode })
}
