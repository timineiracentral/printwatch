/** Mapa D-32 — fallback para valor bruto (D-33). */
const MEDIA_LABELS: Record<string, string> = {
  iso_a4_210x297mm: 'A4',
  'na_letter_8.5x11in': 'Carta',
}

export function formatMediaLabel(raw: string | null | undefined): string {
  if (raw == null || raw === '') return ''
  return MEDIA_LABELS[raw] ?? raw
}
