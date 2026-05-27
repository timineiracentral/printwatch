import { getJson } from './client'

export function fetchPrinters(): Promise<string[]> {
  return getJson<string[]>('/printers')
}
