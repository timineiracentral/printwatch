import { fetchPrintersRegistry } from './settings/printers'
import type { PrinterRead } from '../types/api'

/** Registry canônico — substitui DISTINCT legado (Fase 5). */
export function fetchPrinters(): Promise<PrinterRead[]> {
  return fetchPrintersRegistry(true)
}
