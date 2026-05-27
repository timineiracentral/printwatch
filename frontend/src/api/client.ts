export const baseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

export class ApiError extends Error {
  readonly status: number
  readonly detail: unknown

  constructor(status: number, detail: unknown) {
    super(String(detail))
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

export async function getJson<T>(
  path: string,
  params?: URLSearchParams,
): Promise<T> {
  const qs = params?.toString()
  const url = `${baseUrl}${path}${qs ? `?${qs}` : ''}`
  const res = await fetch(url, { headers: { Accept: 'application/json' } })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const detail =
      (body as { detail?: unknown }).detail ?? res.statusText
    throw new ApiError(res.status, detail)
  }
  return res.json() as Promise<T>
}
