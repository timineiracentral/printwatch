import { useQuery } from '@tanstack/react-query'
import { fetchSimpressAudit } from '../api/simpress/audit'

const KEY = ['simpress', 'audit'] as const

export function useSimpressAudit(limit = 100) {
  return useQuery({
    queryKey: [...KEY, { limit }],
    queryFn: () => fetchSimpressAudit(limit),
  })
}
