import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { fetchFleetList } from '../api/fleet'

export function useFleet() {
  return useQuery({
    queryKey: ['fleet', 'list'],
    queryFn: fetchFleetList,
    staleTime: 60_000,
    refetchInterval: 120_000,
    placeholderData: keepPreviousData,
    refetchOnWindowFocus: false,
  })
}
