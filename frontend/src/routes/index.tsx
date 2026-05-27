import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { JobsPage } from '../pages/JobsPage'
import { CostCentersPage } from '../pages/settings/CostCentersPage'
import { DepartmentsPage } from '../pages/settings/DepartmentsPage'
import { ImportPage } from '../pages/settings/ImportPage'
import { PrintersPage } from '../pages/settings/PrintersPage'
import { SettingsLayout } from '../pages/settings/SettingsLayout'
import { TiExportPage } from '../pages/settings/TiExportPage'
import { UsersPage } from '../pages/settings/UsersPage'

export function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<JobsPage />} />
        <Route path="/settings/users/:userId/ti-export" element={<TiExportPage />} />
        <Route path="/settings" element={<SettingsLayout />}>
          <Route index element={<Navigate to="printers" replace />} />
          <Route path="printers" element={<PrintersPage />} />
          <Route path="departments" element={<DepartmentsPage />} />
          <Route path="cost-centers" element={<CostCentersPage />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="import" element={<ImportPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
