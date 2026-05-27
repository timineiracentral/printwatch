# Phase 5: Master Data & Organization — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `05-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-05-27  
**Phase:** 05-master-data-organization  
**Gate:** ✅ Architecture approved  
**Areas discussed:** AD-01–06 (matcher, linking, UI, printers API, migrations, import), open questions 1–6, transversal guidelines

---

## AD-01 — Printer ID assignment (matcher)

| Opção | Descrição | Selecionado |
|-------|-----------|-------------|
| Background task FastAPI lifespan | Simples; watcher intocado | ✓ |
| SQL trigger on INSERT | Imediato | |
| Worker container separado | Isolamento | (overengineering v1.5) |

**User's choice (com ajustes):**
- Matcher automático a cada **60s** — **somente** jobs com `printer_id IS NULL` (reconciliação incremental)
- **Ao salvar impressora** → match imediato para fila correspondente
- Endpoint/manual **`POST /admin/backfill-printer-ids`** obrigatório para reprocessamento histórico completo
- Evitar scans pesados no banco a cada ciclo (batch limitado + índice)

**Notes:** Queries incrementais; backfill idempotente; nunca bloquear watcher.

---

## AD-02 — User ↔ Job relationship

| Opção | Descrição | Selecionado |
|-------|-----------|-------------|
| Soft link por `username` | AS-IS do CUPS; sem migration de jobs | ✓ |
| FK `user_id` em `print_jobs` | Integridade forte | (adiado — aliases AD reais) |

**User's choice:**
- Soft link por `username`
- Preservar `username` **raw** do log em `print_jobs`
- Sem FK rígida nesta fase

---

## AD-03 — Settings UI structure

| Opção | Descrição | Selecionado |
|-------|-----------|-------------|
| `/settings/*` + AppShell | Separação clara | ✓ |
| Modal drawer sobre audit | Menos rotas | |

**User's choice:**
- `/settings/*` reutilizando AppShell
- Separar UX **operacional** (audit `/`) vs **gerencial** (`/manager` futuro)
- Menu lateral simples, PaperCut-like
- Workflows rápidos de TI — não CRUD enterprise complexo

---

## AD-04 — Printer registry vs log DISTINCT

| Opção | Descrição | Selecionado |
|-------|-----------|-------------|
| Registry primário + `unmapped-queues` | Onboarding/reconciliação | ✓ |
| Substituir `/printers` de uma vez | Menos endpoints | |

**User's choice:**
- Registry = fonte principal
- Manter `GET /printers/unmapped-queues` temporariamente
- Frontend destaca impressoras descobertas mas não cadastradas

---

## AD-05 — Schema migrations

| Opção | Descrição | Selecionado |
|-------|-----------|-------------|
| Alembic desde Fase 5 | Versionado, rollback | ✓ (forte) |
| Scripts SQL manuais | Sem dependência | (rejeitado) |

**User's choice:** Alembic obrigatório; disciplina de schema antes das entidades crescerem.

---

## AD-06 — CSV import transaction model

| Opção | Descrição | Selecionado |
|-------|-----------|-------------|
| Partial commit default | IMPORT-04 | ✓ |
| All-or-nothing only | Simples | |
| `?strict=true` opcional | Modo rigoroso | ✓ |

**User's choice:** Partial por padrão; relatório detalhado linhas válidas/inválidas; `strict=true` opcional.

---

## Open Questions — Resolutions

### Q1 — Matcher frequency

| Opção | Selecionado |
|-------|-------------|
| Só 60s | |
| Só on-save | |
| **Ambos** — on-save imediato + 60s órfãos | ✓ |

### Q2 — `cups_queue_name` uniqueness

| Opção | Selecionado |
|-------|-------------|
| Globalmente único (identidade operacional CUPS) | ✓ |
| Duplicatas permitidas | |

### Q3 — Department / Cost Center codes

| Opção | Selecionado |
|-------|-------------|
| Opcionais | |
| **Obrigatórios**; case-insensitive no backend; persistir **UPPERCASE**; unicidade por código | ✓ |

### Q4 — Delete semantics

| Opção | Selecionado |
|-------|-------------|
| Soft-delete (`is_active`) na UI | ✓ |
| Hard delete na UI | (rejeitado) |
| Hard delete só manual/DB admin | ✓ |

### Q5 — Auth v1.5

| Opção | Selecionado |
|-------|-------------|
| Sem auth; rede local | ✓ |
| Auth na app | (v3.0) |
| Arquitetura pronta para **nginx basic auth** sem refactor grande | ✓ |

### Q6 — `normalize_printer_name` shared module

| Opção | Selecionado |
|-------|-------------|
| Módulo compartilhado (watcher, API, matcher, import) | ✓ |
| Duplicar lógica | (rejeitado — divergência de identidade) |

**Target path:** `backend/app/core/normalize.py` (discretion em plan)

---

## Diretrizes transversais (aprovadas)

- Evitar acoplamento forte entre capture pipeline e master data
- Falha em import, matcher, inventory ou analytics **nunca** bloqueia impressão
- Settings UI: workflows rápidos de TI
- Backfills **idempotentes** e **incrementais**
- Estrutura preparada para crescimento sem complexidade distribuída
- Monólito + SQLite + Docker Compose preservados

---

## Claude's Discretion (para plan-phase)

- Tamanho do batch do matcher (ex.: 500–2000 rows/ciclo)
- Layout exato `backend/app/api/v1/settings/` vs agrupamento por entidade
- Schema Pydantic do relatório de import
- Ordem dos plans (schema → API → matcher → UI sugerida em CONTEXT)
- Nome exato das rotas Settings no React Router

---

## Deferred Ideas

- FK `user_id` em `print_jobs` — quando LDAP sync existir
- Auth/RBAC na aplicação — v3.0
- Hard delete na UI — nunca para v1.5
- Worker container dedicado para matcher
- Full table scan backfill sem LIMIT em produção

---

*Gate closed: 2026-05-27 — Ready for `/gsd-plan-phase 5`*
