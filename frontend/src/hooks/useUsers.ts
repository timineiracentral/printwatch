import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createUser,
  deactivateUser,
  fetchUsers,
  updateUser,
} from '../api/settings/users'
import type { UserCreate, UserUpdate } from '../types/api'

const KEY = ['users'] as const

export function useUsers(includeInactive = false) {
  const queryClient = useQueryClient()

  const list = useQuery({
    queryKey: [...KEY, { includeInactive }],
    queryFn: () => fetchUsers(includeInactive),
  })

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: KEY })
  }

  const create = useMutation({
    mutationFn: (body: UserCreate) => createUser(body),
    onSuccess: invalidate,
  })

  const update = useMutation({
    mutationFn: ({ id, body }: { id: number; body: UserUpdate }) =>
      updateUser(id, body),
    onSuccess: invalidate,
  })

  const deactivate = useMutation({
    mutationFn: (id: number) => deactivateUser(id),
    onSuccess: invalidate,
  })

  return { list, create, update, deactivate }
}
