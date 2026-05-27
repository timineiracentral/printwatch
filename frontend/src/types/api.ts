/** Espelha schemas Pydantic do backend (D-65). */

export interface JobOut {
  id?: number | null
  printer: string
  username: string
  job_id: number
  job_name?: string | null
  timestamp: string
  pages: number
  color_mode?: string | null
  host_origin?: string | null
  media?: string | null
  sides?: string | null
}

export interface JobFilters {
  page: number
  size: number
  username?: string
  printer?: string
  search?: string
  date_from?: string
  date_to?: string
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  size: number
}

export interface TopEntry {
  name: string
  pages: number
}

export interface StatsBucket {
  jobs: number
  pages: number
  top_users: TopEntry[]
  top_printers: TopEntry[]
}

export interface StatsSummaryResponse {
  hoje: StatsBucket
  mes: StatsBucket
  total: StatsBucket
}

export type ExportFilters = Omit<JobFilters, 'page' | 'size'>
