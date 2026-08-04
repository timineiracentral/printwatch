const CNPJ_LEN = 14
const WEIGHTS_DV1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2] as const
const WEIGHTS_DV2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2] as const

export function normalizeCnpj(raw: string): string {
  return (raw || '').replace(/\D/g, '')
}

function checkDigit(base: string, weights: readonly number[]): number {
  const total = [...base].reduce((sum, d, i) => sum + Number(d) * weights[i], 0)
  const remainder = total % 11
  return remainder < 2 ? 0 : 11 - remainder
}

export function isValidCnpj(digits: string): boolean {
  if (!/^\d+$/.test(digits)) return false
  if (digits.length !== CNPJ_LEN) return false
  if (digits === digits[0].repeat(CNPJ_LEN)) return false
  const dv1 = checkDigit(digits.slice(0, 12), WEIGHTS_DV1)
  const dv2 = checkDigit(digits.slice(0, 12) + String(dv1), WEIGHTS_DV2)
  return digits.slice(-2) === `${dv1}${dv2}`
}

if (import.meta.env.DEV) {
  console.assert(isValidCnpj('11222333000181'), 'simpressCnpj self-check valid')
  console.assert(!isValidCnpj('11222333000100'), 'simpressCnpj self-check invalid DV')
}
