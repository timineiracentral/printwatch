import { deleteJson, getJson, patchJson, postJson } from '../client'
import type { PrinterCreate, PrinterRead, PrinterUpdate } from '../../types/api'

export function fetchPrintersRegistry(activeOnly = true): Promise<PrinterRead[]> {
  const params = new URLSearchParams()
  if (!activeOnly) params.set('active_only', 'false')
  return getJson<PrinterRead[]>('/printers', params)
}

export function fetchUnmappedQueues(): Promise<string[]> {
  return getJson<string[]>('/printers/unmapped-queues')
}

export function createPrinter(body: PrinterCreate): Promise<PrinterRead> {
  return postJson<PrinterRead>('/printers', body)
}

export function updatePrinter(id: number, body: PrinterUpdate): Promise<PrinterRead> {
  return patchJson<PrinterRead>(`/printers/${id}`, body)
}

export function deactivatePrinter(id: number): Promise<PrinterRead> {
  return deleteJson<PrinterRead>(`/printers/${id}`)
}
