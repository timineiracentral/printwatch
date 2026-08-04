import { deleteJson, getJson, patchJson, postJson, putJson } from '../client'
import type {
  CnpjCreate,
  CnpjRead,
  CnpjUpdate,
  ContactIdsReplace,
  ContactRead,
} from '../../types/api'

export function fetchCnpjs(
  includeInactive = false,
  q?: string,
): Promise<CnpjRead[]> {
  const params = new URLSearchParams()
  if (includeInactive) params.set('include_inactive', 'true')
  if (q) params.set('q', q)
  return getJson<CnpjRead[]>('/simpress/cnpjs', params)
}

export function createCnpj(body: CnpjCreate): Promise<CnpjRead> {
  return postJson<CnpjRead>('/simpress/cnpjs', body)
}

export function updateCnpj(id: number, body: CnpjUpdate): Promise<CnpjRead> {
  return patchJson<CnpjRead>(`/simpress/cnpjs/${id}`, body)
}

export function deactivateCnpj(id: number): Promise<CnpjRead> {
  return deleteJson<CnpjRead>(`/simpress/cnpjs/${id}`)
}

export function fetchCnpjContacts(
  cnpjId: number,
  includeInactive = false,
): Promise<ContactRead[]> {
  const params = new URLSearchParams()
  if (includeInactive) params.set('include_inactive', 'true')
  return getJson<ContactRead[]>(`/simpress/cnpjs/${cnpjId}/contacts`, params)
}

export function putCnpjContacts(
  cnpjId: number,
  body: ContactIdsReplace,
): Promise<ContactRead[]> {
  return putJson<ContactRead[]>(`/simpress/cnpjs/${cnpjId}/contacts`, body)
}
