import { format, parseISO } from 'date-fns'

const numberFormatter = new Intl.NumberFormat('pt-BR')

const brlFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

export function formatBrl(value: number): string {
  return brlFormatter.format(value)
}

export function formatNumberPtBr(n: number): string {
  return numberFormatter.format(n)
}

export function formatTopLabel(name: string, pages: number): string {
  return `${name} — ${formatNumberPtBr(pages)} páginas`
}

/** Timestamp da API já está em America/Sao_Paulo — sem shift extra (Pitfall 4). */
export function formatDateTime(iso: string): string {
  return format(parseISO(iso), 'dd/MM/yyyy HH:mm')
}
