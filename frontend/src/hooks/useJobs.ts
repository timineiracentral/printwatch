import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { fetchJobs } from '../api/jobs'
import type { JobFilters } from '../types/api'

export function useJobs(filters: JobFilters) {
  return useQuery({
    queryKey: ['jobs', filters],
    queryFn: () => fetchJobs(filters),
    placeholderData: keepPreviousData,
  })
}
