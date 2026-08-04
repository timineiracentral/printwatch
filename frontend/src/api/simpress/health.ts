import { baseUrl } from '../client'

export interface SimpressHealthResponse {
  status: string
  db_reachable: boolean
}

/** D-07: true only when module is mounted and DB reachable; never throws. */
export async function probeSimpressHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${baseUrl}/simpress/health`, {
      headers: { Accept: 'application/json' },
    })
    if (!res.ok) return false
    const body = (await res.json()) as SimpressHealthResponse
    return body.status === 'ok' && body.db_reachable
  } catch {
    return false
  }
}
