import { deleteJson, getJson, patchJson, postJson } from '../client'
import type {
  CostCenterCreate,
  CostCenterRead,
  CostCenterUpdate,
} from '../../types/api'

export function fetchCostCenters(includeInactive = false): Promise<CostCenterRead[]> {
  const params = new URLSearchParams()
  if (includeInactive) params.set('include_inactive', 'true')
  return getJson<CostCenterRead[]>('/cost-centers', params)
}

export function createCostCenter(body: CostCenterCreate): Promise<CostCenterRead> {
  return postJson<CostCenterRead>('/cost-centers', body)
}

export function updateCostCenter(
  id: number,
  body: CostCenterUpdate,
): Promise<CostCenterRead> {
  return patchJson<CostCenterRead>(`/cost-centers/${id}`, body)
}

export function deactivateCostCenter(id: number): Promise<CostCenterRead> {
  return deleteJson<CostCenterRead>(`/cost-centers/${id}`)
}
