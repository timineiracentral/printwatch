import { TZDate } from '@date-fns/tz'
import { format, subDays } from 'date-fns'

export const TZ = 'America/Sao_Paulo'

export function presetToday(): { date_from: string; date_to: string } {
  const today = TZDate.tz(TZ)
  const s = format(today, 'yyyy-MM-dd')
  return { date_from: s, date_to: s }
}

export function presetLast7Days(): { date_from: string; date_to: string } {
  const end = TZDate.tz(TZ)
  const start = subDays(end, 6)
  return {
    date_from: format(start, 'yyyy-MM-dd'),
    date_to: format(end, 'yyyy-MM-dd'),
  }
}

export function presetMonthToDate(): { date_from: string; date_to: string } {
  const now = TZDate.tz(TZ)
  const first = new TZDate(now.getFullYear(), now.getMonth(), 1, TZ)
  return {
    date_from: format(first, 'yyyy-MM-dd'),
    date_to: format(now, 'yyyy-MM-dd'),
  }
}

export function presetLast30Days(): { date_from: string; date_to: string } {
  const end = TZDate.tz(TZ)
  const start = subDays(end, 29)
  return {
    date_from: format(start, 'yyyy-MM-dd'),
    date_to: format(end, 'yyyy-MM-dd'),
  }
}

export function presetLast90Days(): { date_from: string; date_to: string } {
  const end = TZDate.tz(TZ)
  const start = subDays(end, 89)
  return {
    date_from: format(start, 'yyyy-MM-dd'),
    date_to: format(end, 'yyyy-MM-dd'),
  }
}
