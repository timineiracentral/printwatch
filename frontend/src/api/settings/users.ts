import { deleteJson, getJson, patchJson, postJson } from '../client'
import type { UserCreate, UserRead, UserUpdate } from '../../types/api'

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
