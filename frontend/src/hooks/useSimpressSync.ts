import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'
import { ApiError } from '../api/client'
import {
  fetchLastSimpressSync,
  fetchSimpressSyncStatus,
  triggerSimpressSync,
} from '../api/simpress/sync'

const STATUS_KEY = ['simpress', 'sync', 'status'] as const
const LAST_KEY = ['simpress', 'sync', 'last'] as const
const INVOICES_KEY = ['simpress', 'invoices'] as const
const CNPJS_KEY = ['simpress', 'cnpjs'] as const

export function useSimpressSync() {
  const queryClient = useQueryClient()
  const prevInProgress = useRef<boolean | undefined>(undefined)

  const status = useQuery({
    queryKey: STATUS_KEY,
    queryFn: fetchSimpressSyncStatus,
    refetchInterval: (query) =>
      query.state.data?.in_progress ? 3_000 : false,
  })

  const last = useQuery({
    queryKey: LAST_KEY,
    queryFn: fetchLastSimpressSync,
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status === 404) return false
      return failureCount < 2
    },
  })

  useEffect(() => {
    const inProgress = status.data?.in_progress
    if (prevInProgress.current === true && inProgress === false) {
      void queryClient.invalidateQueries({ queryKey: STATUS_KEY })
      void queryClient.invalidateQueries({ queryKey: LAST_KEY })
      void queryClient.invalidateQueries({ queryKey: INVOICES_KEY })
      void queryClient.invalidateQueries({ queryKey: CNPJS_KEY })
    }
    prevInProgress.current = inProgress
  }, [status.data?.in_progress, queryClient])

  const trigger = useMutation({
    mutationFn: triggerSimpressSync,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: STATUS_KEY })
    },
  })

  return { status, last, trigger }
}
