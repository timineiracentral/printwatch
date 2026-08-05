import { useQuery } from '@tanstack/react-query'
import { fetchSimpressInvoices } from '../api/simpress/invoices'

const KEY = ['simpress', 'invoices'] as const

export function useSimpressInvoices(q?: string) {
  return useQuery({
    queryKey: [...KEY, { q }],
    queryFn: () => fetchSimpressInvoices(q),
  })
}
