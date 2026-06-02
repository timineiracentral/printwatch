/** Espelha schemas Pydantic do backend (D-65). */

export interface JobOut {
  id?: number | null
  printer: string
  username: string
  job_id: number
  job_name?: string | null
  minute_bucket?: string | null
  timestamp: string
  pages: number
  pages_billable?: number
  pages_pending_color?: number
  pages_mono?: number
  pages_color?: number
  estimated_cost?: number | null
  color_mode?: string | null
  host_origin?: string | null
  media?: string | null
  sides?: string | null
  outside_policy?: boolean
}

export interface JobLineOut {
  id: number
  timestamp: string
  color_mode?: string | null
  color_mode_source?: string | null
  pages: number
}

export interface JobLineFilters {
  printer: string
  username: string
  job_id: number
  job_name?: string | null
  minute_bucket: string
}

export interface CostRateRead {
  id: number
  rate_mono: string
  rate_color: string
  valid_from: string
  created_at: string
}

export interface CostRateCreate {
  rate_mono: number
  rate_color: number
  valid_from?: string | null
}

export interface JobFilters {
  page: number
  size: number
  username?: string
  printer?: string
  search?: string
  date_from?: string
  date_to?: string
  outside_policy?: boolean
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

export interface PrinterAccessItem {
  printer_id: number
  is_default: boolean
  is_active: boolean
}

export interface PrinterAccessRead {
  id: number
  user_id: number
  printer_id: number
  printer_display_name?: string | null
  is_default: boolean
  is_active: boolean
}

export interface PrinterAccessReplace {
  assignments: PrinterAccessItem[]
}

export interface PrinterUserAccessRead {
  id: number
  display_name: string
  cups_username: string
  is_default: boolean
}

export interface TiExportRow {
  display_name: string
  username: string
  printer_display_name: string
  cups_queue_name: string
  ipp_url: string | null
  is_default: boolean
  department: string | null
  location: string | null
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

export interface ManagerTopEntry {
  name: string
  pages: number
  estimated_cost?: number | null
}

export interface PeriodKpi {
  pages_mono: number
  pages_color: number
  pages_billable: number
  pages_pending: number
  estimated_cost?: number | null
  previous?: PeriodKpi | null
  delta_pct_pages?: number | null
  delta_pct_cost?: number | null
}

export interface MeterReconciliationRow {
  printer_id: number
  printer_name: string
  reading_start?: string | null
  reading_end?: string | null
  pages_meter?: number | null
  cost_meter?: number | null
  pages_jobs: number
  divergence_pct?: number | null
  partial_interval: boolean
  counter_reset: boolean
  proportional_cost_note?: string | null
}

export interface ManagerSummaryResponse {
  period: PeriodKpi
  top_users: ManagerTopEntry[]
  top_printers: ManagerTopEntry[]
  top_departments: ManagerTopEntry[]
  meter_reconciliation: MeterReconciliationRow[]
  has_rates: boolean
  pending_pct?: number | null
  pending_count: number
}

export interface ManagerFilters {
  date_from: string
  date_to: string
  preset?: string
}

export interface MeterReadingCreate {
  timestamp: string
  counter_total: number
  counter_mono?: number | null
  counter_color?: number | null
  source?: 'manual' | 'import'
}

export interface MeterReadingRead {
  id: number
  printer_id: number
  timestamp: string
  counter_total: number
  counter_mono?: number | null
  counter_color?: number | null
  source: string
  created_at: string
}
