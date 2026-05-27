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

async function parseError(res: Response): Promise<never> {
  const body = await res.json().catch(() => ({}))
  const detail = (body as { detail?: unknown }).detail ?? res.statusText
  throw new ApiError(res.status, detail)
}

export async function getJson<T>(
  path: string,
  params?: URLSearchParams,
): Promise<T> {
  const qs = params?.toString()
  const url = `${baseUrl}${path}${qs ? `?${qs}` : ''}`
  const res = await fetch(url, { headers: { Accept: 'application/json' } })
  if (!res.ok) await parseError(res)
  return res.json() as Promise<T>
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${baseUrl}${path}`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })
  if (!res.ok) await parseError(res)
  return res.json() as Promise<T>
}

export async function patchJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${baseUrl}${path}`, {
    method: 'PATCH',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })
  if (!res.ok) await parseError(res)
  return res.json() as Promise<T>
}

export async function deleteJson<T>(path: string): Promise<T> {
  const res = await fetch(`${baseUrl}${path}`, {
    method: 'DELETE',
    headers: { Accept: 'application/json' },
  })
  if (!res.ok) await parseError(res)
  return res.json() as Promise<T>
}

export async function postFormData<T>(path: string, formData: FormData): Promise<T> {
  const res = await fetch(`${baseUrl}${path}`, {
    method: 'POST',
    headers: { Accept: 'application/json' },
    body: formData,
  })
  if (!res.ok) await parseError(res)
  return res.json() as Promise<T>
}

export async function downloadBlob(path: string): Promise<Blob> {
  const res = await fetch(`${baseUrl}${path}`, { headers: { Accept: 'text/csv' } })
  if (!res.ok) await parseError(res)
  return res.blob()
}
