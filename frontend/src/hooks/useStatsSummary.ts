import { useQuery } from '@tanstack/react-query'
import { fetchStatsSummary } from '../api/stats'

export function useStatsSummary() {
  return useQuery({
    queryKey: ['stats', 'summary'],
    queryFn: () => fetchStatsSummary(),
    staleTime: 60_000,
  })
}
