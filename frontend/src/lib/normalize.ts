/** Espelha app.core.normalize — valor de filtro jobs compatível com o backend. */
export function normalizePrinterName(raw: string | null | undefined): string {
  if (raw == null) return ''
  let s = raw.trim()
  while (s.length >= 2 && (s[0] === '"' || s[0] === "'") && s[0] === s.at(-1)) {
    s = s.slice(1, -1).trim()
  }
  return s.replace(/^["']+|["']+$/g, '').trim()
}

export function normalizeOrgCode(raw: string): string {
  return raw.trim().toUpperCase()
}
