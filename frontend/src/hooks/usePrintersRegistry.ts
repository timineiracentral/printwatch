import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createPrinter,
  deactivatePrinter,
  fetchPrintersRegistry,
  fetchUnmappedQueues,
  updatePrinter,
} from '../api/settings/printers'
import type { PrinterCreate, PrinterUpdate } from '../types/api'

const LIST_KEY = ['printers', 'registry'] as const
const UNMAPPED_KEY = ['printers', 'unmapped'] as const

export function usePrintersRegistry(activeOnly = true) {
  const queryClient = useQueryClient()

  const list = useQuery({
    queryKey: [...LIST_KEY, { activeOnly }],
    queryFn: () => fetchPrintersRegistry(activeOnly),
  })

  const unmapped = useQuery({
    queryKey: UNMAPPED_KEY,
    queryFn: fetchUnmappedQueues,
  })

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: LIST_KEY })
    void queryClient.invalidateQueries({ queryKey: UNMAPPED_KEY })
    void queryClient.invalidateQueries({ queryKey: ['printers'] })
  }

  const create = useMutation({
    mutationFn: (body: PrinterCreate) => createPrinter(body),
    onSuccess: invalidate,
  })

  const update = useMutation({
    mutationFn: ({ id, body }: { id: number; body: PrinterUpdate }) =>
      updatePrinter(id, body),
    onSuccess: invalidate,
  })

  const deactivate = useMutation({
    mutationFn: (id: number) => deactivatePrinter(id),
    onSuccess: invalidate,
  })

  return { list, unmapped, create, update, deactivate }
}
