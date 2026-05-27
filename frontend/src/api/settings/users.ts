import { baseUrl, deleteJson, getJson, patchJson, postJson, putJson } from '../client'
import type {
  PrinterAccessRead,
  PrinterAccessReplace,
  PrinterUserAccessRead,
  TiExportRow,
  UserCreate,
  UserRead,
  UserUpdate,
} from '../../types/api'

export function fetchUsers(includeInactive = false): Promise<UserRead[]> {
  const params = new URLSearchParams()
  if (includeInactive) params.set('include_inactive', 'true')
  return getJson<UserRead[]>('/users', params)
}

export function createUser(body: UserCreate): Promise<UserRead> {
  return postJson<UserRead>('/users', body)
}

export function updateUser(id: number, body: UserUpdate): Promise<UserRead> {
  return patchJson<UserRead>(`/users/${id}`, body)
}

export function deactivateUser(id: number): Promise<UserRead> {
  return deleteJson<UserRead>(`/users/${id}`)
}

export function fetchUserPrinterAccess(userId: number): Promise<PrinterAccessRead[]> {
  return getJson<PrinterAccessRead[]>(`/users/${userId}/printer-access`)
}

export function putUserPrinterAccess(
  userId: number,
  body: PrinterAccessReplace,
): Promise<PrinterAccessRead[]> {
  return putJson<PrinterAccessRead[]>(`/users/${userId}/printer-access`, body)
}

export function fetchPrinterUsers(printerId: number): Promise<PrinterUserAccessRead[]> {
  return getJson<PrinterUserAccessRead[]>(`/printers/${printerId}/users`)
}

export function fetchTiExport(userId: number): Promise<TiExportRow[]> {
  return getJson<TiExportRow[]>(`/users/${userId}/ti-export`)
}

export function tiExportCsvUrl(userId: number): string {
  return `${baseUrl}/users/${userId}/ti-export?format=csv`
}
