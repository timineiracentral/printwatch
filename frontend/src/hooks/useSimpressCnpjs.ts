import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createCnpj,
  deactivateCnpj,
  fetchCnpjs,
  updateCnpj,
} from '../api/simpress/cnpjs'
import type { CnpjCreate, CnpjUpdate } from '../types/api'

const KEY = ['simpress', 'cnpjs'] as const

export function useSimpressCnpjs(includeInactive = false, q?: string) {
  const queryClient = useQueryClient()

  const list = useQuery({
    queryKey: [...KEY, { includeInactive, q }],
    queryFn: () => fetchCnpjs(includeInactive, q),
  })

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: KEY })
  }

  const create = useMutation({
    mutationFn: (body: CnpjCreate) => createCnpj(body),
    onSuccess: invalidate,
  })

  const update = useMutation({
    mutationFn: ({ id, body }: { id: number; body: CnpjUpdate }) =>
      updateCnpj(id, body),
    onSuccess: invalidate,
  })

  const deactivate = useMutation({
    mutationFn: (id: number) => deactivateCnpj(id),
    onSuccess: invalidate,
  })

  return { list, create, update, deactivate }
}
