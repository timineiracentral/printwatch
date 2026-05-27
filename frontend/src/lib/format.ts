import { format, parseISO } from 'date-fns'

const numberFormatter = new Intl.NumberFormat('pt-BR')

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
