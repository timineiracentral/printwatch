import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createCostCenter,
  deactivateCostCenter,
  fetchCostCenters,
  updateCostCenter,
} from '../api/settings/costCenters'
import type { CostCenterCreate, CostCenterUpdate } from '../types/api'

const KEY = ['cost-centers'] as const

export function useCostCenters(includeInactive = false) {
  const queryClient = useQueryClient()

  const list = useQuery({
    queryKey: [...KEY, { includeInactive }],
    queryFn: () => fetchCostCenters(includeInactive),
  })

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: KEY })
  }

  const create = useMutation({
    mutationFn: (body: CostCenterCreate) => createCostCenter(body),
    onSuccess: invalidate,
  })

  const update = useMutation({
    mutationFn: ({ id, body }: { id: number; body: CostCenterUpdate }) =>
      updateCostCenter(id, body),
    onSuccess: invalidate,
  })

  const deactivate = useMutation({
    mutationFn: (id: number) => deactivateCostCenter(id),
    onSuccess: invalidate,
  })

  return { list, create, update, deactivate }
}
