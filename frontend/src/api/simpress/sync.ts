import { getJson, postJson } from '../client'
import type { SyncStatusRead, SyncSummaryRead } from '../../types/api'

export function triggerSimpressSync(): Promise<{ status: string }> {
  return postJson<{ status: string }>('/simpress/sync', {})
}

export function fetchSimpressSyncStatus(): Promise<SyncStatusRead> {
  return getJson<SyncStatusRead>('/simpress/sync/status')
}

export function fetchLastSimpressSync(): Promise<SyncSummaryRead> {
  return getJson<SyncSummaryRead>('/simpress/sync/last')
}
