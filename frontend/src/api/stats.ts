import { getJson } from './client'
import type { StatsSummaryResponse } from '../types/api'

export function fetchStatsSummary(top?: number): Promise<StatsSummaryResponse> {
  const params =
    top !== undefined ? new URLSearchParams({ top: String(top) }) : undefined
  return getJson<StatsSummaryResponse>('/stats/summary', params)
}
