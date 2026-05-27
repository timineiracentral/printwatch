import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  fetchUserPrinterAccess,
  putUserPrinterAccess,
} from '../api/settings/users'
import type { PrinterAccessReplace } from '../types/api'

export function useUserPrinterAccess(userId: number | null) {
  const qc = useQueryClient()
  const query = useQuery({
    queryKey: ['users', userId, 'printer-access'],
    queryFn: () => fetchUserPrinterAccess(userId!),
    enabled: userId != null,
  })
  const save = useMutation({
    mutationFn: (body: PrinterAccessReplace) =>
      putUserPrinterAccess(userId!, body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['users', userId, 'printer-access'] })
      void qc.invalidateQueries({ queryKey: ['printers'] })
    },
  })
  return { ...query, save }
}
