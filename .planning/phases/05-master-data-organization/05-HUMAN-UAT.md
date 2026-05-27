---
status: partial
phase: 05-master-data-organization
source: [05-VERIFICATION.md]
started: 2026-05-27T18:30:00Z
updated: 2026-05-27T18:30:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Audit dashboard após navegação Settings
expected: Dashboard de jobs carrega, filtra por impressora do registry e exporta CSV sem regressão
result: [pending]

### 2. CRUD Settings (4 entidades)
expected: Dialogs modais persistem via API; soft-delete reflete is_active=false; busca local funciona; erros 409/422 visíveis
result: [pending]

### 3. Import CSV (strict on/off)
expected: Download attachment; painel mostra total/created/updated/skipped/errors; strict=true não persiste linhas com erro
result: [pending]

### 4. Matcher e backfill printer_id
expected: Jobs órfãos recebem printer_id após cadastro de impressora ou backfill; banner unmapped diminui
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps
