import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { fetchManagerSummary } from '../api/manager'

export function useManagerSummary(
  dateFrom: string,
  dateTo: string,
  preset?: string,
) {
  return useQuery({
    queryKey: ['manager', 'summary', dateFrom, dateTo, preset ?? ''],
    queryFn: () =>
      fetchManagerSummary({
        date_from: dateFrom,
        date_to: dateTo,
        preset,
      }),
    staleTime: 60_000,
    placeholderData: keepPreviousData,
    refetchOnWindowFocus: false,
    enabled: Boolean(dateFrom && dateTo),
  })
}
