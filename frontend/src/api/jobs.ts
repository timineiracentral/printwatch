import { getJson } from './client'
import type { JobFilters, JobOut, Page } from '../types/api'
import { filtersToSearchParams } from '../lib/filters'

export function fetchJobs(filters: JobFilters): Promise<Page<JobOut>> {
  return getJson<Page<JobOut>>('/jobs', filtersToSearchParams(filters))
}
