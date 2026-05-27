import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createCostRate,
  fetchCostRates,
  fetchCurrentCostRate,
} from '../api/settings/costRates'
import type { CostRateCreate } from '../types/api'

const KEY = ['cost-rates'] as const

export function useCostRates() {
  const queryClient = useQueryClient()

  const list = useQuery({
    queryKey: KEY,
    queryFn: fetchCostRates,
  })

  const current = useQuery({
    queryKey: [...KEY, 'current'],
    queryFn: fetchCurrentCostRate,
    retry: false,
  })

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: KEY })
  }

  const create = useMutation({
    mutationFn: (body: CostRateCreate) => createCostRate(body),
    onSuccess: invalidate,
  })

  return { list, current, create }
}
