import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchCnpjContacts, putCnpjContacts } from '../api/simpress/cnpjs'
import { fetchContactCnpjs, putContactCnpjs } from '../api/simpress/contacts'
import type { CnpjIdsReplace, ContactIdsReplace } from '../types/api'

const CNPJS_KEY = ['simpress', 'cnpjs'] as const
const CONTACTS_KEY = ['simpress', 'contacts'] as const

export function useCnpjContacts(cnpjId: number | null) {
  const qc = useQueryClient()
  const query = useQuery({
    queryKey: [...CNPJS_KEY, cnpjId, 'contacts'],
    queryFn: () => fetchCnpjContacts(cnpjId!),
    enabled: cnpjId != null,
  })
  const save = useMutation({
    mutationFn: (body: ContactIdsReplace) => putCnpjContacts(cnpjId!, body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: [...CNPJS_KEY, cnpjId, 'contacts'] })
      void qc.invalidateQueries({ queryKey: CNPJS_KEY })
      void qc.invalidateQueries({ queryKey: CONTACTS_KEY })
    },
  })
  return { ...query, save }
}

export function useContactCnpjs(contactId: number | null) {
  const qc = useQueryClient()
  const query = useQuery({
    queryKey: [...CONTACTS_KEY, contactId, 'cnpjs'],
    queryFn: () => fetchContactCnpjs(contactId!),
    enabled: contactId != null,
  })
  const save = useMutation({
    mutationFn: (body: CnpjIdsReplace) => putContactCnpjs(contactId!, body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: [...CONTACTS_KEY, contactId, 'cnpjs'] })
      void qc.invalidateQueries({ queryKey: CONTACTS_KEY })
      void qc.invalidateQueries({ queryKey: CNPJS_KEY })
    },
  })
  return { ...query, save }
}
