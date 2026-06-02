import { getJson, postJson } from './client'
import type {
  FleetListResponse,
  FleetPrinterDetail,
  SnmpTestResponse,
} from '../types/api'

export function fetchFleetList(): Promise<FleetListResponse> {
  return getJson<FleetListResponse>('/fleet')
}

export function fetchFleetPrinter(id: number): Promise<FleetPrinterDetail> {
  return getJson<FleetPrinterDetail>(`/fleet/${id}`)
}

export function postSnmpTest(printerId: number): Promise<SnmpTestResponse> {
  return postJson<SnmpTestResponse>(`/printers/${printerId}/snmp-test`, {})
}
