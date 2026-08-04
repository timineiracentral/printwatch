import { useQuery } from '@tanstack/react-query'
import { probeSimpressHealth } from '../api/simpress/health'

const KEY = ['simpress', 'health'] as const

export function useSimpressHealth() {
  return useQuery({
    queryKey: KEY,
    queryFn: probeSimpressHealth,
    retry: false,
    staleTime: 60_000,
  })
}
