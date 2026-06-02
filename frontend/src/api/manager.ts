import { getJson, postJson } from './client'
import type {
  ManagerSummaryResponse,
  MeterReadingCreate,
  MeterReadingRead,
} from '../types/api'

export function fetchManagerSummary(params: {
  date_from: string
  date_to: string
  preset?: string
}): Promise<ManagerSummaryResponse> {
  const sp = new URLSearchParams({
    date_from: params.date_from,
    date_to: params.date_to,
  })
  if (params.preset) {
    sp.set('preset', params.preset)
  }
  return getJson<ManagerSummaryResponse>('/manager/summary', sp)
}

export function createMeterReading(
  printerId: number,
  payload: MeterReadingCreate,
): Promise<MeterReadingRead> {
  return postJson<MeterReadingRead>(
    `/printers/${printerId}/meter-readings`,
    payload,
  )
}
