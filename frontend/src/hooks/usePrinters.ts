import { useQuery } from '@tanstack/react-query'
import { fetchPrinters } from '../api/printers'

const STALE_TIME_MS = 5 * 60 * 1000

export function usePrinters() {
  return useQuery({
    queryKey: ['printers'],
    queryFn: () => fetchPrinters(),
    staleTime: STALE_TIME_MS,
  })
}
