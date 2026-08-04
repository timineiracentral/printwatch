const E164_MAX = 15
const MIN_DIGITS = 10

export function normalizePhone(raw: string): string {
  return (raw || '').replace(/\D/g, '')
}

export function isValidPhone(digits: string): boolean {
  if (!/^\d+$/.test(digits)) return false
  if (digits.length < MIN_DIGITS || digits.length > E164_MAX) return false
  if (digits.startsWith('0')) return false
  return true
}

if (import.meta.env.DEV) {
  const ok = normalizePhone('+55 (31) 99999-9999')
  console.assert(ok === '5531999999999' && isValidPhone(ok), 'simpressPhone self-check')
  console.assert(!isValidPhone('031999999999'), 'simpressPhone rejects leading 0')
}
