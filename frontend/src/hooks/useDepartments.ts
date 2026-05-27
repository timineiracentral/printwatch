import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createDepartment,
  deactivateDepartment,
  fetchDepartments,
  updateDepartment,
} from '../api/settings/departments'
import type { DepartmentCreate, DepartmentUpdate } from '../types/api'

const KEY = ['departments'] as const

export function useDepartments(includeInactive = false) {
  const queryClient = useQueryClient()

  const list = useQuery({
    queryKey: [...KEY, { includeInactive }],
    queryFn: () => fetchDepartments(includeInactive),
  })

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: KEY })
  }

  const create = useMutation({
    mutationFn: (body: DepartmentCreate) => createDepartment(body),
    onSuccess: invalidate,
  })

  const update = useMutation({
    mutationFn: ({ id, body }: { id: number; body: DepartmentUpdate }) =>
      updateDepartment(id, body),
    onSuccess: invalidate,
  })

  const deactivate = useMutation({
    mutationFn: (id: number) => deactivateDepartment(id),
    onSuccess: invalidate,
  })

  return { list, create, update, deactivate }
}
