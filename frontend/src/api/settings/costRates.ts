import { getJson, postJson } from '../client'
import type { CostRateCreate, CostRateRead } from '../../types/api'

export function fetchCostRates(): Promise<CostRateRead[]> {
  return getJson<CostRateRead[]>('/cost-rates')
}

export function fetchCurrentCostRate(): Promise<CostRateRead> {
  return getJson<CostRateRead>('/cost-rates/current')
}

export function createCostRate(body: CostRateCreate): Promise<CostRateRead> {
  return postJson<CostRateRead>('/cost-rates', body)
}
