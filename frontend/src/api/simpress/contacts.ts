import { deleteJson, getJson, patchJson, postJson, putJson } from '../client'
import type {
  CnpjIdsReplace,
  CnpjRead,
  ContactCreate,
  ContactRead,
  ContactUpdate,
} from '../../types/api'

export function fetchContacts(
  includeInactive = false,
  q?: string,
): Promise<ContactRead[]> {
  const params = new URLSearchParams()
  if (includeInactive) params.set('include_inactive', 'true')
  if (q) params.set('q', q)
  return getJson<ContactRead[]>('/simpress/contacts', params)
}

export function createContact(body: ContactCreate): Promise<ContactRead> {
  return postJson<ContactRead>('/simpress/contacts', body)
}

export function updateContact(
  id: number,
  body: ContactUpdate,
): Promise<ContactRead> {
  return patchJson<ContactRead>(`/simpress/contacts/${id}`, body)
}

export function deactivateContact(id: number): Promise<ContactRead> {
  return deleteJson<ContactRead>(`/simpress/contacts/${id}`)
}

export function fetchContactCnpjs(
  contactId: number,
  includeInactive = false,
): Promise<CnpjRead[]> {
  const params = new URLSearchParams()
  if (includeInactive) params.set('include_inactive', 'true')
  return getJson<CnpjRead[]>(`/simpress/contacts/${contactId}/cnpjs`, params)
}

export function putContactCnpjs(
  contactId: number,
  body: CnpjIdsReplace,
): Promise<CnpjRead[]> {
  return putJson<CnpjRead[]>(`/simpress/contacts/${contactId}/cnpjs`, body)
}
