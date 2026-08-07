import { getJson } from '../client'
import type { MessageAuditRead } from '../../types/api'

export function fetchSimpressAudit(limit = 100): Promise<MessageAuditRead[]> {
  const params = new URLSearchParams()
  params.set('limit', String(limit))
  return getJson<MessageAuditRead[]>('/simpress/audit', params)
}
