import { useMemo } from 'react'
import { useFleet } from './useFleet'
import type { FleetConnectivityStatus } from '../types/api'

export function useFleetStatusMap(): Map<number, FleetConnectivityStatus> {
  const { data } = useFleet()

  return useMemo(() => {
    const map = new Map<number, FleetConnectivityStatus>()
    for (const row of data?.items ?? []) {
      map.set(row.printer_id, row.fleet_status)
    }
    return map
  }, [data])
}
