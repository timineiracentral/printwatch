---
phase: 05-master-data-organization
reviewed: 2026-05-27T12:00:00Z
depth: standard
files_reviewed: 58
files_reviewed_list:
  - backend/alembic/versions/085a2d5c5767_master_data_tables.py
  - backend/alembic/env.py
  - backend/app/api/v1/__init__.py
  - backend/app/api/v1/admin.py
  - backend/app/api/v1/cost_centers.py
  - backend/app/api/v1/departments.py
  - backend/app/api/v1/import_routes.py
  - backend/app/api/v1/printers.py
  - backend/app/api/v1/users.py
  - backend/app/core/normalize.py
  - backend/app/db/migrations.py
  - backend/app/db/models.py
  - backend/app/main.py
  - backend/app/schemas/cost_center.py
  - backend/app/schemas/department.py
  - backend/app/schemas/printer.py
  - backend/app/schemas/user.py
  - backend/app/services/cost_centers_service.py
  - backend/app/services/departments_service.py
  - backend/app/services/import_service.py
  - backend/app/services/matcher_hooks.py
  - backend/app/services/normalization.py
  - backend/app/services/parser.py
  - backend/app/services/printer_matcher.py
  - backend/app/services/printers_service.py
  - backend/app/services/users_service.py
  - backend/app/watcher/handler.py
  - backend/tests/test_admin_backfill.py
  - backend/tests/test_import_csv.py
  - backend/tests/test_matcher.py
  - backend/tests/test_migrations.py
  - backend/tests/test_normalization.py
  - backend/tests/test_org_api.py
  - backend/tests/test_printers_api.py
  - frontend/src/App.tsx
  - frontend/src/api/client.ts
  - frontend/src/api/printers.ts
  - frontend/src/api/settings/costCenters.ts
  - frontend/src/api/settings/departments.ts
  - frontend/src/api/settings/import.ts
  - frontend/src/api/settings/printers.ts
  - frontend/src/api/settings/users.ts
  - frontend/src/components/filters/PrinterCombobox.tsx
  - frontend/src/components/layout/Sidebar.tsx
  - frontend/src/components/settings/ConfirmDialog.tsx
  - frontend/src/components/settings/SettingsSearch.tsx
  - frontend/src/components/settings/UnmappedQueuesBanner.tsx
  - frontend/src/components/ui/Badge.tsx
  - frontend/src/components/ui/Button.tsx
  - frontend/src/components/ui/Dialog.tsx
  - frontend/src/components/ui/Select.tsx
  - frontend/src/hooks/useCostCenters.ts
  - frontend/src/hooks/useDepartments.ts
  - frontend/src/hooks/useImport.ts
  - frontend/src/hooks/usePrintersRegistry.ts
  - frontend/src/hooks/useUsers.ts
  - frontend/src/lib/normalize.ts
  - frontend/src/pages/JobsPage.tsx
  - frontend/src/pages/settings/CostCentersPage.tsx
  - frontend/src/pages/settings/DepartmentsPage.tsx
  - frontend/src/pages/settings/ImportPage.tsx
  - frontend/src/pages/settings/PrintersPage.tsx
  - frontend/src/pages/settings/SettingsLayout.tsx
  - frontend/src/pages/settings/UsersPage.tsx
  - frontend/src/routes/index.tsx
  - frontend/src/types/api.ts
findings:
  critical: 1
  warning: 5
  info: 2
  total: 8
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-05-27T12:00:00Z  
**Depth:** standard  
**Files Reviewed:** 58  
**Status:** issues_found

## Summary

Revisão adversarial da Fase 5 (master-data-organization), com foco em migrations Alembic, isolamento matcher/watcher, import CSV, validação CRUD e rotas `/settings/*` no frontend.

**Pontos positivos verificados:**
- Watcher (`app/watcher/handler.py`) não importa `printer_matcher` — isolamento D-01 respeitado.
- Migration `085a2d5c5767` trata upgrade em DB v1.0 existente (só adiciona `printer_id`) e em DB vazio; testes `test_migrations.py` passam (upgrade/downgrade/re-upgrade).
- Import CSV: limite 5MB, cabeçalho estrito, sanitização de fórmulas (`_sanitize_csv_field`), modos partial/strict testados.
- `cups_username` imutável no schema `UserUpdate`; duplicatas e FKs de usuário validados no service layer.
- Rotas FastAPI `/printers/unmapped-queues` declaradas antes de `/{printer_id}` — sem shadowing.
- Suite focal da fase: **30 testes passando** (`test_migrations`, `test_matcher`, `test_import_csv`, `test_printers_api`, `test_org_api`).

**Preocupação principal:** validação incompleta de `department_id` em impressoras pode gerar HTTP 500 em vez de 422.

---

## Critical Issues

### CR-01: `department_id` inválido em impressoras causa HTTP 500

**File:** `backend/app/services/printers_service.py:51-71`, `74-96`  
**Issue:** `create_printer` e `update_printer` aceitam qualquer `department_id` sem verificar existência ou `is_active`. Usuários e departamentos já usam `_validate_department_id` / `_validate_cost_center_id`; impressoras não. Um ID inexistente dispara `IntegrityError` do SQLite sem handler global → resposta 500 opaca ao cliente.

**Fix:**
```python
# Em printers_service.py — espelhar users_service
def _validate_department_id(db: Session, department_id: Optional[int]) -> None:
    if department_id is None:
        return
    dept = departments_service.get_department_by_id(db, department_id)
    if dept is None:
        raise HTTPException(status_code=422, detail="department_id não encontrado")
    if not dept.is_active:
        raise HTTPException(status_code=422, detail="department_id inativo")

# Chamar em create_printer (antes do db.add) e em update_printer quando department_id em data
```

---

## Warnings

### WR-01: CSV com encoding inválido gera HTTP 500

**File:** `backend/app/services/import_service.py:70`  
**Issue:** `_parse_csv` usa `content.decode("utf-8-sig")` sem capturar `UnicodeDecodeError`. Upload Latin-1/Windows-1252 ou binário corrompido estoura exceção não tratada em `import_csv_endpoint`.

**Fix:**
```python
def _parse_csv(content: bytes, expected_headers: tuple[str, ...]) -> list[tuple[int, dict[str, str]]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("arquivo não é UTF-8 válido") from exc
    ...
```

### WR-02: `match_jobs_for_queue` varre todos os jobs órfãos sem limite

**File:** `backend/app/services/printer_matcher.py:58-61`  
**Issue:** On-save após CRUD de impressora, `select(PrintJob).where(PrintJob.printer_id.is_(None))` carrega **toda** a fila órfã em memória. `match_batch` limita a 500; on-save não. Em volume alto, risco de pico de memória e sessão DB longa (correção de robustez, não só performance).

**Fix:** Filtrar no SQL por `printer` normalizado quando possível, ou reutilizar lógica batch com `LIMIT` em loop até esvaziar a fila da queue alvo.

### WR-03: Renomear `cups_queue_name` não revincula jobs históricos

**File:** `backend/app/api/v1/printers.py:50-59`, `backend/app/services/printer_matcher.py:48-64`  
**Issue:** Após PATCH que altera `cups_queue_name`, `schedule_match_for_queue` só processa o **novo** nome. Jobs em `print_jobs.printer` ainda contêm o texto do log CUPS (nome antigo); permanecem com `printer_id IS NULL` até coincidência acidental ou backfill manual.

**Fix:** No update, se `cups_queue_name` mudou, agendar match também para o nome anterior normalizado, ou executar `UPDATE print_jobs SET printer_id=... WHERE normalize(printer)=old_norm`.

### WR-04: Import CSV sem teto de linhas (DoS lógico dentro do limite de 5MB)

**File:** `backend/app/services/import_service.py:374-426`  
**Issue:** Um arquivo de 5MB com linhas de 1–2 bytes pode gerar centenas de milhares de linhas. Modo partial faz `commit` por linha → pressão extrema no SQLite e API bloqueada por muito tempo.

**Fix:** Introduzir `MAX_IMPORT_ROWS` (ex.: 10_000) após `_parse_csv` e retornar erro 413/422 com mensagem clara.

### WR-05: Rotas `/settings/*` inválidas renderizam layout vazio

**File:** `frontend/src/routes/index.tsx:15-22`  
**Issue:** Não há rota catch-all dentro de `SettingsLayout`. URL como `/settings/foo` monta shell sem conteúdo no `<Outlet />` — UX quebrada e difícil de diagnosticar.

**Fix:**
```tsx
<Route path="*" element={<Navigate to="printers" replace />} />
```
como último filho de `/settings`.

---

## Info

### IN-01: Endpoints mutáveis sem autenticação (escopo documentado)

**File:** `backend/app/api/v1/import_routes.py`, `backend/app/api/v1/admin.py`, CRUD em `printers`/`users`/etc.  
**Issue:** Qualquer cliente na rede pode importar CSV, executar backfill e alterar cadastros.  
**Contexto:** Alinhado a D-27 (sem auth nesta fase). Registrar como débito técnico até nginx basic auth (D-28).

### IN-02: Import CSV em massa não dispara matcher on-save

**File:** `backend/app/services/import_service.py` (ausência de hook)  
**Issue:** Impressoras criadas via CSV só ganham `printer_id` nos jobs após o loop periódico de 60s ou POST `/admin/backfill-printer-ids`. Comportamento aceitável se documentado; UI poderia mencionar atraso de até 1 minuto.

---

_Reviewed: 2026-05-27T12:00:00Z_  
_Reviewer: Claude (gsd-code-reviewer)_  
_Depth: standard_
