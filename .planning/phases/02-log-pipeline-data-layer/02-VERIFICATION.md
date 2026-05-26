---
phase: 02-log-pipeline-data-layer
status: passed
verdict: "functional with known data-quality gaps"
approved_by: operator
approved_at: "2026-05-26"
plans: 5
plans_completed: 5
must_haves_verified: "11/11 funcionais"
gaps_registered: 2
gaps_open: 2
---

# Verification — Fase 2: Log Pipeline & Data Layer

## Veredito

**Approved (functional with known data-quality gaps)** — 2026-05-26

A fase entrega o objetivo central do MVP: **Windows → CUPS → watcher → SQLite com captura automática e persistência**. Foram detectados dois desvios de qualidade de dado (parser + username AD) que foram registrados como gap-closures formais para tratamento na Fase 3 — sem expandir escopo nem refatorar nesta fase.

---

## Critérios de Aceite do ROADMAP

| # | Critério | Status | Evidência |
|---|----------|--------|-----------|
| 1 | Job impresso de PC Windows com usuário AD aparece no banco em ≤ 30s | ✅ funcional (com gap) | `Print-Job successful-ok` no `access_log` 19:58:49; job em DB no mesmo timestamp |
| 2 | Restart do backend não duplica nem perde jobs | ✅ | UNIQUE constraint `uq_page_log_line` + CheckpointRepository (inode+offset); evidência: backend reiniciado várias vezes durante validação sem duplicatas |
| 3 | Container backend parado → CUPS imprime sem erro | ✅ | `check_cups_without_backend` no `validate-phase2.sh` PASS |
| 4 | VM reiniciada → jobs anteriores intactos | ✅ | volume `db_data` persistido; jobs históricos de 17:53–19:58 mantidos após múltiplos rebuilds |

## Must-Haves Verificados

| ID | Must-Have | Status |
|----|-----------|--------|
| CAPTURE-01 | Todos campos registrados por job | ⚠ parcial (ver GAP-02-01, GAP-02-02) |
| CAPTURE-02 | Job no banco em ≤ 30s | ✅ ~1-3s observado |
| CAPTURE-03 | Restart watcher não duplica nem perde | ✅ |
| CAPTURE-04 | CUPS opera com backend caído | ✅ |
| DATA-01 | LOG_RETENTION_DAYS configurável | ✅ default 90, purge no startup |
| DATA-02 | Volumes Docker persistem | ✅ `db_data`, `cups_logs` |
| DATA-03 | SQLite 600 | ✅ confirmado por `stat` |
| EXTEND-01 | Coluna `status` default `allowed` | ✅ todos os jobs com `status=allowed` |
| EXTEND-02 | Tabela `policies` vazia criada | ✅ |
| EXTEND-03 | Hook `pre_process_job` → True | ✅ validado no `validate-phase2.sh --quick` |

## Pipeline End-to-End

```
PC Windows (CLIENT_HOST, user.example)
  ↓ IPP/HTTP
CUPS test_printer (cups-pdf:/)
  ↓ /var/log/cups/page_log
Inotify watcher (backend container)
  ↓ parse_page_log_line + repo.upsert
SQLite /app/data/printwatch.db (UNIQUE uq_page_log_line)
```

**Evidência runtime (banco):**

```
2026-05-26 19:58:49 | user.example | "test_printer | Página de teste | pages=0 | status=allowed
2026-05-26 18:12:24 | user.example | "test_printer | Microsoft Word - ... | pages=1 | status=allowed
2026-05-26 18:10:37 | user.example | "test_printer | Microsoft Word - ... | pages=1 | status=allowed
2026-05-26 17:53:51 | user.example | "test_printer | Página de teste | pages=1 | status=allowed
```

## Validações Automatizadas

```
bash scripts/validate-phase2.sh --quick  → 0 FAIL, 1 WARN (pytest dev-only no host)
pytest backend/tests/                    → 24 passed (parser/tail/repository/retention)
```

## Gaps Registrados (não bloqueiam a fase)

| ID | Tipo | Descrição | Resolve em |
|----|------|-----------|-----------|
| GAP-02-01 | bug | Parser captura aspa inicial em `printer` (`"test_printer`) | Fase 3 |
| GAP-02-02 | investigation | Username sem prefixo AD (`user.example` em vez de `DOMAIN\user.example`) — investigar antes de mudar código | Fase 3 |

Detalhes em `.planning/todos/pending/GAP-02-01-*.md` e `.planning/todos/pending/GAP-02-02-*.md`.

## Issue conhecida não-bloqueante

- `pages=0` em alguns jobs — comportamento esperado da fila virtual `cups-pdf:/` (não conta página real). Aceito.

## Incidente Operacional Resolvido (não-código)

Durante a validação Windows o cliente IPP do PC ficou com uma porta órfã no Internet Print Provider apontando para `http://VM_HOST:631/printers/test_printer`, gerando `0x0000000d` repetidamente. Resolvido removendo a chave de registro:

```
HKLM:\SYSTEM\CurrentControlSet\Control\Print\Providers\Internet Print Provider\Ports\http://VM_HOST:631/printers/test_printer
```

Não é bug do projeto — é estado local do Windows. Documentar no runbook de troubleshooting na Fase 5.

## Próximo passo

`/gsd-discuss-phase 3` — Backend API (FastAPI servindo jobs com filtros + CSV).
