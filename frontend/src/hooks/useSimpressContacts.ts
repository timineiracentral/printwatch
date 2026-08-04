import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createContact,
  deactivateContact,
  fetchContacts,
  updateContact,
} from '../api/simpress/contacts'
import type { ContactCreate, ContactUpdate } from '../types/api'

const KEY = ['simpress', 'contacts'] as const

export function useSimpressContacts(includeInactive = false, q?: string) {
  const queryClient = useQueryClient()

  const list = useQuery({
    queryKey: [...KEY, { includeInactive, q }],
    queryFn: () => fetchContacts(includeInactive, q),
  })

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: KEY })
  }

  const create = useMutation({
    mutationFn: (body: ContactCreate) => createContact(body),
    onSuccess: invalidate,
  })

  const update = useMutation({
    mutationFn: ({ id, body }: { id: number; body: ContactUpdate }) =>
      updateContact(id, body),
    onSuccess: invalidate,
  })

  const deactivate = useMutation({
    mutationFn: (id: number) => deactivateContact(id),
    onSuccess: invalidate,
  })

  return { list, create, update, deactivate }
}
