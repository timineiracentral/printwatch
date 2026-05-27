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

export interface PrinterRead {
  id: number
  display_name: string
  cups_queue_name: string
  ip_address?: string | null
  manufacturer_model?: string | null
  location?: string | null
  department_id?: number | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface PrinterCreate {
  display_name: string
  cups_queue_name: string
  ip_address?: string | null
  manufacturer_model?: string | null
  location?: string | null
  department_id?: number | null
}

export interface PrinterUpdate {
  display_name?: string
  cups_queue_name?: string
  ip_address?: string | null
  manufacturer_model?: string | null
  location?: string | null
  department_id?: number | null
}

export interface DepartmentRead {
  id: number
  code: string
  name: string
  cost_center_id?: number | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface DepartmentCreate {
  code: string
  name: string
  cost_center_id?: number | null
}

export interface DepartmentUpdate {
  code?: string
  name?: string
  cost_center_id?: number | null
}

export interface CostCenterRead {
  id: number
  code: string
  name: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CostCenterCreate {
  code: string
  name: string
}

export interface CostCenterUpdate {
  code?: string
  name?: string
}

export interface UserRead {
  id: number
  cups_username: string
  display_name: string
  department_id: number
  cost_center_id?: number | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserCreate {
  cups_username: string
  display_name: string
  department_id: number
  cost_center_id?: number | null
}

export interface UserUpdate {
  display_name?: string
  department_id?: number
  cost_center_id?: number | null
  is_active?: boolean
}

export interface ImportLineError {
  line: number
  message: string
}

export interface ImportResult {
  total: number
  created: number
  updated: number
  skipped: number
  errors: ImportLineError[]
}

export type ImportEntity =
  | 'departments'
  | 'cost-centers'
  | 'users'
  | 'printers'
