import { deleteJson, getJson, patchJson, postJson } from '../client'
import type {
  DepartmentCreate,
  DepartmentRead,
  DepartmentUpdate,
} from '../../types/api'

export function fetchDepartments(includeInactive = false): Promise<DepartmentRead[]> {
  const params = new URLSearchParams()
  if (includeInactive) params.set('include_inactive', 'true')
  return getJson<DepartmentRead[]>('/departments', params)
}

export function createDepartment(body: DepartmentCreate): Promise<DepartmentRead> {
  return postJson<DepartmentRead>('/departments', body)
}

export function updateDepartment(
  id: number,
  body: DepartmentUpdate,
): Promise<DepartmentRead> {
  return patchJson<DepartmentRead>(`/departments/${id}`, body)
}

export function deactivateDepartment(id: number): Promise<DepartmentRead> {
  return deleteJson<DepartmentRead>(`/departments/${id}`)
}
