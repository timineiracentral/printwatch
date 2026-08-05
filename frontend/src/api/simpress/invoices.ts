import { getJson } from '../client'
import type { InvoiceRead } from '../../types/api'

export function fetchSimpressInvoices(q?: string): Promise<InvoiceRead[]> {
  const params = new URLSearchParams()
  if (q) params.set('q', q)
  return getJson<InvoiceRead[]>('/simpress/invoices', params)
}
