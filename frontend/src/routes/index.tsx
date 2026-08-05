import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { JobsPage } from '../pages/JobsPage'
import { FleetPage } from '../pages/FleetPage'
import { ManagerPage } from '../pages/ManagerPage'
import { CnpjsPage } from '../pages/simpress/CnpjsPage'
import { ContatosPage } from '../pages/simpress/ContatosPage'
import { FaturasPage } from '../pages/simpress/FaturasPage'
import { SimpressLayout } from '../pages/simpress/SimpressLayout'
import { SyncPage } from '../pages/simpress/SyncPage'
import { CostCentersPage } from '../pages/settings/CostCentersPage'
import { CostRatesPage } from '../pages/settings/CostRatesPage'
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
        <Route path="/manager" element={<ManagerPage />} />
        <Route path="/fleet" element={<FleetPage />} />
        <Route path="/simpress" element={<SimpressLayout />}>
          <Route index element={<Navigate to="cnpjs" replace />} />
          <Route path="cnpjs" element={<CnpjsPage />} />
          <Route path="contatos" element={<ContatosPage />} />
          <Route path="sync" element={<SyncPage />} />
          <Route path="faturas" element={<FaturasPage />} />
        </Route>
        <Route path="/settings/users/:userId/ti-export" element={<TiExportPage />} />
        <Route path="/settings" element={<SettingsLayout />}>
          <Route index element={<Navigate to="printers" replace />} />
          <Route path="printers" element={<PrintersPage />} />
          <Route path="departments" element={<DepartmentsPage />} />
          <Route path="cost-centers" element={<CostCentersPage />} />
          <Route path="cost-rates" element={<CostRatesPage />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="import" element={<ImportPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
