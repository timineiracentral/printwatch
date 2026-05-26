# Phase 3: Backend API — Technical Research

**Pesquisado:** 2026-05-26  
**Fontes:** context7 MCP (FastAPI 0.136.3, SQLAlchemy 2.0, Pydantic 2.13), CONTEXT.md (D-01–D-34), código existente Fase 2  
**Objetivo:** O que é preciso saber para **planejar bem** os endpoints REST + CSV + GAPs herdados.

---

## 1. Padrões FastAPI 0.136 a aplicar

### 1.1 Estrutura modular (APIRouter + prefix versionado) — D-24, D-33

FastAPI suporta agregar múltiplos `APIRouter` em um único `include_router` com prefixo global. Padrão validado pelo Tutorial oficial (`bigger-applications.md`):

```python
# backend/app/api/v1/__init__.py
from fastapi import APIRouter
from app.api.v1 import jobs, stats, printers, export, health

api_v1_router = APIRouter()
api_v1_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_v1_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_v1_router.include_router(printers.router, prefix="/printers", tags=["printers"])
api_v1_router.include_router(export.router, prefix="/export", tags=["export"])
api_v1_router.include_router(health.router, prefix="/health", tags=["health"])

# backend/app/main.py
app.include_router(api_v1_router, prefix="/api/v1")
```

Cada módulo define `router = APIRouter()` e endpoints relativos (`@router.get("")`, `@router.get("/{id}")`). **Não** acumular todos os endpoints em `main.py` (D-33).

### 1.2 Swagger reabilitado — D-26

`FastAPI(docs_url="/api/v1/docs", redoc_url=None, openapi_url="/api/v1/openapi.json")`. Atual main.py tem `docs_url=None` (D-12 Fase 2) — **alterar para reabilitar**.

### 1.3 Dependency injection `get_db()` com yield — D-31

O `app/db/session.py` já tem `get_db()` como **contextmanager** (`@contextmanager`). Para `Depends()` do FastAPI o padrão correto é uma função **generator simples** (não decorada com contextmanager):

```python
# backend/app/db/session.py — adicionar AO LADO do contextmanager existente
from typing import Generator
from sqlalchemy.orm import Session

def get_db_dep() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Uso: `db: Session = Depends(get_db_dep)`. **Importante (FastAPI ≥ 0.118.0):** o exit code (`finally: db.close()`) executa **APÓS** o `StreamingResponse` terminar de enviar, garantindo que o yield_per do CSV não morra pela sessão fechada prematuramente. PR #14099 confirmou esse comportamento. Versão atual do projeto: 0.136.3 → comportamento correto por padrão.

### 1.4 CORSMiddleware sem wildcard — D-27

```python
from fastapi.middleware.cors import CORSMiddleware

origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,         # lista explícita, NUNCA ["*"] (D-27)
    allow_credentials=False,        # MVP sem auth, sem cookies
    allow_methods=["GET"],          # única operação na Fase 3 (D-27)
    allow_headers=["*"],
)
```

`settings.allowed_origins` lido de env `ALLOWED_ORIGINS` (string CSV). Default `.env.example`: `http://localhost:5173,http://VM_HOST`.

### 1.5 Pydantic v2 generic para paginação — D-32 (option, Claude's Discretion)

Pydantic 2 suporta `Generic[T]` nativamente:

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
```

Decisão recomendada para o planner: usar `Page[JobOut]` em vez de schema concreto para reuso futuro (CSV e listagens compartilham o mesmo `JobOut`). Trade-off: classes genéricas em Pydantic v2 são instantâneas (sem custo de runtime relevante a 50k registros).

### 1.6 Validação de query params via `Query`/Pydantic

Para `GET /api/v1/jobs?page=1&size=50&username=...&printer=...&date_from=...&date_to=...` o padrão recomendado em FastAPI ≥ 0.115 é modelar os filtros como `BaseModel` + `Annotated[Filters, Query()]`:

```python
from typing import Annotated, Optional
from datetime import date
from fastapi import Query
from pydantic import BaseModel, Field, model_validator

class JobFilters(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(50, ge=1, le=500)            # D-08
    username: Optional[str] = None
    printer: Optional[str] = None                  # exact match, D-09
    search: Optional[str] = None                   # LIKE em job_name, D-09
    date_from: Optional[date] = None               # interpretado em America/Sao_Paulo
    date_to: Optional[date] = None                 # idem; ambas inclusive

    @model_validator(mode="after")
    def _date_range(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be <= date_to")
        return self
```

`422 Unprocessable Entity` é retornado automaticamente pela Pydantic para inputs inválidos.

### 1.7 StreamingResponse para CSV — D-15, D-16

Padrão FastAPI oficial (`stream-data.md`):

```python
from fastapi.responses import StreamingResponse

def _generate_csv(rows_iter):
    yield "\ufeff"                                          # BOM (D-12)
    yield "Data/Hora;Usuário;Impressora;Documento;Páginas;Papel;Frente/Verso;Modo de Cor;Origem\n"
    for r in rows_iter:
        yield ";".join(_csv_safe(c) for c in r) + "\n"

@router.get("/csv")
def export_csv(filters: Annotated[JobFilters, Query()], db: Session = Depends(get_db_dep)):
    cnt = service.count_jobs(db, filters)
    if cnt > 100_000:
        raise HTTPException(400, "Resultado excede 100k linhas — refine os filtros")
    rows = service.iter_jobs_for_csv(db, filters)           # generator
    ts = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y%m%d_%H%M")
    return StreamingResponse(
        _generate_csv(rows),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="print_jobs_{ts}.csv"'},
    )
```

`_csv_safe` escapa `;`, `"`, `\n` conforme RFC 4180 (`"value"` se contém separador, dobra aspas internas).

### 1.8 yield_per para streaming SQLAlchemy — D-15

Para evitar OOM no CSV de 100k linhas, usar `execution_options(yield_per=1000)` na query:

```python
stmt = select(...).group_by(...).order_by(...).execution_options(yield_per=1000)
for row in db.execute(stmt):
    yield row
```

`yield_per` em SQLAlchemy 2.0 ativa `stream_results` + `Result.yield_per()` automaticamente. **Não usar `Result.all()`** — anula o benefício. Para SQLite, `yield_per` ainda é útil para reduzir alocações intermediárias (não há server-side cursor real no SQLite, mas o batching evita materializar Result inteiro).

---

## 2. Padrões SQLAlchemy 2.0 para agregação por job — D-01 a D-06

### 2.1 GROUP BY com strftime SQLite — D-05

A chave de agregação `(printer_normalized, job_id, username, job_name, timestamp_window)` se traduz em:

```python
from sqlalchemy import func, select

ts_minute = func.strftime("%Y-%m-%d %H:%M", PrintJob.timestamp).label("ts_minute")

stmt = (
    select(
        PrintJob.printer.label("printer"),
        PrintJob.username.label("username"),
        PrintJob.job_id.label("job_id"),
        PrintJob.job_name.label("job_name"),
        func.min(PrintJob.timestamp).label("timestamp"),       # D-06
        func.count().label("pages"),                            # D-03
        func.max(PrintJob.color_mode).label("color_mode"),
        func.max(PrintJob.host_origin).label("host_origin"),
        func.max(PrintJob.media).label("media"),
        func.max(PrintJob.sides).label("sides"),
        ts_minute,
    )
    .group_by(
        PrintJob.printer,
        PrintJob.username,
        PrintJob.job_id,
        PrintJob.job_name,
        ts_minute,                                              # mesma expressão, repetir não label
    )
)
```

Notas:
- `func.max(color_mode)` etc. resolvem valores que **deveriam ser iguais** dentro do grupo, mas o agregador aceita pequenas variações sem erro (mais robusto que `min`).
- SQLite **aceita** `GROUP BY` por label, mas a forma portável é repetir a expressão.
- `func.count()` (sem argumento) = `COUNT(*)`.

### 2.2 Contagem total para paginação

`SELECT COUNT(*) FROM (subquery agregada)`:

```python
def count_jobs(db, filters) -> int:
    agg = _build_aggregated_query(filters).subquery()
    return db.execute(select(func.count()).select_from(agg)).scalar_one()
```

Sem `LIMIT/OFFSET` na subquery — só depois `paginated = stmt.limit(size).offset((page-1)*size)`.

### 2.3 Filtros LIKE case-insensitive + intervalo de data — D-09, D-10

```python
from sqlalchemy import func, or_, and_

def _apply_filters(stmt, filters):
    if filters.username:
        stmt = stmt.where(func.lower(PrintJob.username).contains(filters.username.lower()))
    if filters.printer:
        stmt = stmt.where(PrintJob.printer == filters.printer)        # exact, D-09
    if filters.search:
        stmt = stmt.where(func.lower(PrintJob.job_name).contains(filters.search.lower()))
    if filters.date_from:
        # date_from local → 00:00 America/Sao_Paulo → UTC
        utc_start = datetime.combine(filters.date_from, time.min, tzinfo=ZoneInfo("America/Sao_Paulo")).astimezone(timezone.utc)
        stmt = stmt.where(PrintJob.timestamp >= utc_start)
    if filters.date_to:
        # date_to local INCLUSIVE → 23:59:59.999999 America/Sao_Paulo → UTC
        utc_end = datetime.combine(filters.date_to, time.max, tzinfo=ZoneInfo("America/Sao_Paulo")).astimezone(timezone.utc)
        stmt = stmt.where(PrintJob.timestamp <= utc_end)
    return stmt
```

Importante: filtro de data é aplicado **na tabela base** (`print_jobs.timestamp`), **antes** do `GROUP BY` — usa os índices `idx_print_jobs_timestamp` e compostos eficientemente. Não filtrar pelo `MIN(timestamp)` derivado.

### 2.4 Índices via DDL idempotente — D-29

SQLAlchemy 2.0 + SQLite: `CREATE INDEX IF NOT EXISTS` via `text()` no startup do lifespan:

```python
from sqlalchemy import text

def ensure_indexes(engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_print_jobs_timestamp ON print_jobs(timestamp DESC)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_print_jobs_username_timestamp ON print_jobs(username, timestamp DESC)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_print_jobs_printer_timestamp ON print_jobs(printer, timestamp DESC)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_print_jobs_job_id ON print_jobs(job_id)"))
```

Chamado no `lifespan` **antes** de `purge_old_jobs` (já existente em `main.py`). Idempotente — seguro em restarts.

### 2.5 Performance esperada (DASH-06: < 500ms para 50k)

- `idx_print_jobs_timestamp DESC` → `ORDER BY timestamp DESC LIMIT 50` é O(50) — index range scan.
- `idx_print_jobs_username_timestamp` → filtro por username + ordem é O(matches).
- `GROUP BY` com 50k linhas + chave composta de baixa cardinalidade (job_id é incremental, ~ 50k jobs distintos): full scan + hash group. SQLite resolve a < 200ms em hardware típico. Sem índice funcional sobre `strftime` (D-29) porque o GROUP BY já está atrás de filtros que reduzem o universo.
- Critério mensurável: rodar `EXPLAIN QUERY PLAN` no `validate-phase3.sh` para confirmar uso dos índices criados.

---

## 3. GAP-02-01: bug parser printer quote — D-22

### 3.1 Investigação observacional ANTES do código (D-22 mandatório)

```bash
# Na VM VM_HOST (ou local):
docker compose exec cups tail -n 50 /var/log/cups/page_log
# Capturar UMA linha bruta cujo printer começa com aspa no banco (job_id 4, por ex.)
```

Hipótese a confirmar:
- (a) Linha inteira tem aspas externas — improvável, CUPS PageLogFormat não faz isso.
- (b) Aspa interna do `%{job-name}` (campo com espaço) "vaza" para o printer no regex — **provável**.
- (c) `%p` (printer) tem aspas no próprio nome no `printers.conf` — verificar.

### 3.2 Normalizador idempotente

```python
# backend/app/services/normalization.py (módulo dedicado — D-22 Discretion)
def normalize_printer_name(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = raw.strip()
    # Remove aspas duplas/simples nas extremidades, repetidamente (idempotente).
    while len(s) >= 2 and s[0] in ('"', "'") and s[0] == s[-1]:
        s = s[1:-1].strip()
    # Caso degenerado: só aspa inicial (sem fechamento) — strip lateral.
    s = s.lstrip('"').lstrip("'").strip()
    return s
```

Características:
- **Idempotente:** `normalize(normalize(x)) == normalize(x)`.
- Aplica `.strip()` → cobre `"test_printer ` e ` test_printer`.
- Trata o caso real observado (aspa só no início) sem quebrar nomes válidos.

### 3.3 Aplicação no parser

```python
# backend/app/services/parser.py
from app.services.normalization import normalize_printer_name

def parse_page_log_line(line: str) -> Optional[dict[str, Any]]:
    m = PAGE_LOG_REGEX.match(line.strip())
    if m is None:
        return None
    return {
        "printer": normalize_printer_name(m.group(1)),   # ← aqui
        "username": m.group(2),
        ...
    }
```

### 3.4 Backfill idempotente do SQLite existente

Script Python em `backend/scripts/backfill_printer_quotes.py` que:
1. Conta linhas afetadas (`SELECT COUNT(*) FROM print_jobs WHERE printer LIKE '"%' OR printer LIKE "'%" OR printer LIKE '%"' OR printer LIKE "%'"`).
2. Faz `UPDATE print_jobs SET printer = TRIM(...)` aplicando a mesma lógica do normalizador (em SQL puro ou via Python via SQLAlchemy + commit em batch).
3. Conta de novo e loga `before / after / fixed`.
4. Guard: se `before == 0`, sai 0 sem alterar nada.
5. Rodável manualmente (`docker compose exec backend python -m scripts.backfill_printer_quotes`). **Não** entra no lifespan automático — operação de manutenção registrada.

Trade-off justificado: backfill no lifespan parece atraente mas (1) atrasa startup, (2) reroda toda vez (mesmo sendo idempotente é desperdiço), (3) operação de migração de dado deve ser explícita e auditável. Script standalone é o padrão.

### 3.5 Teste de regressão

`backend/tests/test_parser.py` (estendido) + `backend/tests/test_normalization.py`:

```python
def test_normalize_printer_name_strips_leading_quote():
    assert normalize_printer_name('"test_printer') == "test_printer"

def test_normalize_printer_name_idempotent():
    n1 = normalize_printer_name('"test_printer')
    n2 = normalize_printer_name(n1)
    assert n1 == n2 == "test_printer"

def test_parse_page_log_line_with_quote_in_raw_log():
    # Linha bruta capturada do page_log real (substituir após coleta D-22)
    raw = '"test_printer user.example 4 [...] total 1 - CLIENT_HOST "Página de teste" A4 one-sided'
    parsed = parse_page_log_line(raw)
    assert parsed["printer"] == "test_printer"
```

A linha bruta exata vem da investigação observacional (D-22 passo 1).

---

## 4. GAP-02-02: username sem domínio AD — D-23

### 4.1 Investigação observacional (NÃO codificar antes)

Comandos a executar:
1. `docker compose exec cups tail -n 100 /var/log/cups/access_log` — formato do username recebido pelo CUPS.
2. `docker compose exec cups tail -n 100 /var/log/cups/page_log` — formato gravado.
3. Em um PC Windows AD: durante envio de job, capturar `Get-PrintJob -PrinterName test_printer | Format-List *` — inspecionar `requesting-user-name` IPP.
4. (Opcional) `nc -l 6310` na VM + roteamento temporário para capturar IPP raw e olhar o header `requesting-user-name`.

### 4.2 Conclusão e registro

Resultado deve ser anotado em `.planning/phases/03-backend-api/03-INVESTIGATION-username-ad.md` com:
- Comandos exatos rodados (timestamps).
- Output bruto (com PII redatada se necessário).
- Conclusão classificada como (a)/(b)/(c)/(d) conforme `GAP-02-02-username-domain-ad.md`.
- Recomendação: ajustar D-14 no STATE.md OU adicionar D-XX nova fechando o GAP.

### 4.3 Critério de "Done" para o gap nesta fase

**O gap é fechado** quando:
- O documento de investigação existir com evidência.
- Decisão registrada (D-XX nova ou D-14 atualizada) no STATE.md.
- `GAP-02-02-username-domain-ad.md` movido para `.planning/todos/resolved/`.

**Sem mudança de código nesta fase** salvo se a evidência for (b)/(c)/(d) inequívoca **e** a correção for trivial (<10 LoC). Caso contrário, criar tarefa explícita em Fase 4 ou v2.

---

## 5. Health check expandido — D-25

### 5.1 `/healthz` (mantido) + `/api/v1/health` (novo)

`/healthz` atual:
```python
return {"status": "ok", "watcher": alive}
```

`/api/v1/health` novo:
```python
@router.get("")
def health(db: Session = Depends(get_db_dep)):
    from app.main import _observer
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    watcher_alive = _observer is not None and _observer.is_alive()

    status_str = "ok" if (db_ok and watcher_alive) else "degraded"
    body = {
        "status": status_str,
        "db_reachable": db_ok,
        "watcher_alive": watcher_alive,
    }
    if not db_ok:
        return JSONResponse(body, status_code=503)
    return body  # HTTP 200 mesmo degraded (apenas watcher down) — D-25
```

Notas:
- HTTP 503 **só** se DB inacessível (operação crítica).
- Watcher down → 200 `"degraded"` — UI pode alertar mas não treme.
- Acessar `_observer` direto do `main.py` quebra encapsulamento — alternativa: expor função `app.watcher.status.is_alive()` que encapsula a global. **Recomendação ao planner:** criar `app/watcher/status.py` com `def is_alive() -> bool` que lê de um state singleton. Trade-off justificado: testabilidade > simplicidade. Custo: ~10 LoC adicionais.

### 5.2 Exposição da porta 8000 no docker-compose.yml

Hoje o serviço `backend` em `docker-compose.yml` **não tem `ports:`** (D-12 Fase 2 dizia "sem rotas REST públicas"). Fase 3 inverte essa decisão. Mudança mínima:

```yaml
backend:
  build: ./backend
  env_file: .env
  environment:
    ...
    ALLOWED_ORIGINS: ${ALLOWED_ORIGINS:-http://localhost:5173,http://VM_HOST}
  ports:
    - "8000:8000"          # Fase 3 — expõe API REST para curl + Fase 4 dashboard
  volumes:
    - cups_logs:/var/log/cups:ro
    - db_data:/app/data
  restart: unless-stopped
  depends_on:
    - cups
```

`ALLOWED_ORIGINS` adicionado em `environment:` e em `.env.example`.

---

## 6. `/stats/summary` — janelas temporais — D-20

### 6.1 Bounds em America/Sao_Paulo

```python
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Sao_Paulo")
UTC = timezone.utc

def _today_bounds_utc() -> tuple[datetime, datetime]:
    today_local = datetime.now(TZ).date()
    start = datetime.combine(today_local, time.min, tzinfo=TZ).astimezone(UTC)
    end = datetime.combine(today_local, time.max, tzinfo=TZ).astimezone(UTC)
    return start, end

def _month_bounds_utc() -> tuple[datetime, datetime]:
    now_local = datetime.now(TZ)
    first = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if first.month == 12:
        next_first = first.replace(year=first.year+1, month=1)
    else:
        next_first = first.replace(month=first.month+1)
    last = next_first - timedelta(microseconds=1)
    return first.astimezone(UTC), last.astimezone(UTC)
```

### 6.2 Top-N por SUM(pages)

```python
def top_by_field(db, field, start_utc, end_utc, n=5):
    # field é PrintJob.username ou PrintJob.printer
    # Usa o dataset AGREGADO POR JOB (D-20): primeiro agrega pages COUNT(*) por job,
    # depois soma esses "pages do job" agrupados pelo field-alvo.
    job_agg = _build_aggregated_query(
        JobFilters(date_from=..., date_to=...)  # ou bounds diretos
    ).subquery()
    stmt = (
        select(getattr(job_agg.c, field), func.sum(job_agg.c.pages).label("pages"))
        .group_by(getattr(job_agg.c, field))
        .order_by(func.sum(job_agg.c.pages).desc())
        .limit(n)
    )
    return [{"name": r[0], "pages": r[1]} for r in db.execute(stmt)]
```

Schema da resposta (definitivo, derivado de D-20):
```json
{
  "hoje":  { "jobs": N, "pages": N, "top_users": [{"name":"...","pages":N}], "top_printers": [...] },
  "mes":   { "jobs": N, "pages": N, "top_users": [...], "top_printers": [...] },
  "total": { "jobs": N, "pages": N, "top_users": [...], "top_printers": [...] }
}
```

---

## 7. `/printers` — fonte de dados — D-21

Implementação trivial:
```python
@router.get("", response_model=list[str])
def list_printers(db: Session = Depends(get_db_dep)):
    stmt = (
        select(PrintJob.printer)
        .distinct()
        .order_by(PrintJob.printer.asc())
    )
    return [row[0] for row in db.execute(stmt)]
```

**Nada de CUPS**. **Nada de online/offline** (Fase 5 SERVER-04). Pode haver printers órfãos (impressoras removidas do CUPS mas com histórico) — comportamento esperado (D-21 informacional/histórico).

---

## 8. Estrutura de diretórios proposta

```
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py          # api_v1_router agregador
│   │       ├── jobs.py              # GET /jobs, GET /jobs/{id}
│   │       ├── stats.py             # GET /stats/summary
│   │       ├── printers.py          # GET /printers
│   │       ├── export.py            # GET /export/csv
│   │       └── health.py            # GET /health
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── jobs.py                  # JobOut, JobFilters, Page[T]
│   │   ├── stats.py                 # StatsBucket, StatsSummaryResponse
│   │   └── health.py                # HealthResponse
│   ├── services/
│   │   ├── jobs_service.py          # build/aggregate/count/list/get_by_id
│   │   ├── stats_service.py         # today/month/total + top_users + top_printers
│   │   ├── normalization.py         # normalize_printer_name (D-22)
│   │   ├── csv_export.py            # generate_csv_stream
│   │   ├── parser.py                # (já existe — adicionar normalize)
│   │   ├── retention.py             # (já existe — sem mudança)
│   │   └── tail_reader.py           # (já existe — sem mudança)
│   ├── db/
│   │   ├── migrations.py            # ensure_indexes (D-29)
│   │   ├── models.py                # (já existe — sem mudança)
│   │   ├── repository.py            # (já existe — REUTILIZAR, D-31)
│   │   ├── session.py               # (já existe — adicionar get_db_dep)
│   │   └── base.py                  # (já existe)
│   ├── watcher/
│   │   ├── handler.py               # (já existe)
│   │   ├── checkpoint.py            # (já existe)
│   │   └── status.py                # NOVO — encapsula _observer global (5.1)
│   ├── core/
│   │   └── config.py                # ESTENDER: allowed_origins, api_timezone
│   └── main.py                      # ESTENDER: include_router, CORS, docs_url, ensure_indexes
├── tests/
│   ├── test_api_jobs.py             # TestClient + GET /api/v1/jobs (filtros, paginação)
│   ├── test_api_stats.py            # GET /api/v1/stats/summary
│   ├── test_api_export.py           # GET /api/v1/export/csv (BOM, headers, encoding)
│   ├── test_api_printers.py         # GET /api/v1/printers
│   ├── test_api_health.py           # GET /healthz + GET /api/v1/health (degraded)
│   ├── test_normalization.py        # normalize_printer_name idempotente
│   ├── test_parser.py               # (existente — adicionar regressão com aspa)
│   └── conftest.py                  # (existente — adicionar TestClient fixture + DB em memória)
└── scripts/
    └── backfill_printer_quotes.py   # backfill idempotente (D-22)

scripts/
└── validate-phase3.sh                # Nyquist Fase 3 (modelo validate-phase2.sh)
```

---

## 9. Testes — padrão TestClient + DB isolado

`conftest.py` adiciona fixture FastAPI:

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db.base import Base
from app.db.session import get_db_dep

@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    yield session
    session.close()

@pytest.fixture
def client(db_session):
    def _get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db_dep] = _get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

Padrão usado: `client.get("/api/v1/jobs?page=1&size=10")` retorna `Response` que assertamos JSON/headers/status. Cobertura mínima:
- Paginação: `size > 500` → 422; `total/page/size/items` no payload.
- Filtros: `username`, `printer`, `search`, `date_from`/`date_to`.
- Agregação: inserir 3 page-rows de mesmo job → `pages == 3` na resposta.
- CSV: BOM `\ufeff` no início, separador `;`, `Content-Disposition` com `attachment; filename=...`.
- Health: DB OK + watcher fake-down → 200 + `"degraded"`.

---

## 10. Validação Nyquist (Dimensão 8) — `validate-phase3.sh`

Modelo: `scripts/validate-phase2.sh`. Suite a implementar:

| # | Check | Critério |
|---|-------|----------|
| 1 | `docker compose up -d backend` sobe sem erro | exit 0, watcher healthy em 10s |
| 2 | `curl -s :8000/api/v1/openapi.json | jq .info.title` retorna `"PrintWatch"` | string match |
| 3 | `curl -s :8000/healthz` retorna `{"status":"ok",...}` | jq filter `.status == "ok"` |
| 4 | `curl -s :8000/api/v1/health` retorna 200 + `db_reachable: true` | jq filter |
| 5 | `curl -s ':8000/api/v1/jobs?page=1&size=10'` retorna `{ items, total, page, size }` | jq filter shape |
| 6 | Indices existem: `docker exec backend sqlite3 /app/data/printwatch.db ".indices print_jobs"` | grep `idx_print_jobs_timestamp` |
| 7 | EXPLAIN QUERY PLAN usa índice em filtro timestamp | grep `USING INDEX idx_print_jobs_timestamp` |
| 8 | `curl -s -I ':8000/api/v1/export/csv'` retorna `Content-Type: text/csv` + `Content-Disposition: attachment` | grep headers |
| 9 | CSV baixado: primeira linha começa com BOM `\xef\xbb\xbf` | `xxd | head -1` |
| 10 | CSV baixado: separador `;` na linha de header | grep `;` |
| 11 | `curl ':8000/api/v1/jobs?date_from=2025-01-01&date_to=2024-12-31'` retorna 422 | status code |
| 12 | `curl ':8000/api/v1/jobs?size=999'` retorna 422 | status code |
| 13 | `curl :8000/api/v1/printers` retorna lista JSON ordenada alfabeticamente | jq sort check |
| 14 | CORS preflight `curl -X OPTIONS -H 'Origin: http://localhost:5173'` retorna `Access-Control-Allow-Origin` | header presente |
| 15 | CORS de origem não permitida (`-H 'Origin: http://evil.com'`) NÃO retorna `Access-Control-Allow-Origin` | header ausente |
| 16 | pytest passes: `docker exec backend pytest -q` exit 0 | exit code |
| 17 | Checkpoint humano: job real Windows → aparece em `/api/v1/jobs?username=...` em ≤ 30s + CSV abre no Excel | manual |

Modo `--quick` roda 1–10 + 16 (sem checkpoint humano). Modo completo inclui 17.

---

## 11. Validation Architecture (para gsd-plan-checker — Dimensão 8 Nyquist)

| Dimensão | Tipo | Implementação | Falha = |
|----------|------|---------------|---------|
| 1 — Schema/Endpoint | OpenAPI shape | `validate-phase3.sh` check #2, #5 | API inválida |
| 2 — Functional happy path | pytest + curl | test_api_jobs/stats/printers/export/health | Endpoint não retorna o esperado |
| 3 — Error paths | pytest 422/400/503 | test_api_jobs (size > 500, date inválida); test_api_health (DB down) | Erro silencioso |
| 4 — Idempotência | pytest backfill + indexes | test_normalize idempotente; ensure_indexes rodar 2x | Migration corrompe |
| 5 — Performance (DASH-06) | EXPLAIN QUERY PLAN | validate-phase3.sh #7 | Full table scan em filtros indexados |
| 6 — Encoding/Locale (EXPORT-02) | BOM + ; em CSV | validate-phase3.sh #9, #10 | Excel não abre |
| 7 — Compatibilidade com Fase 2 | watcher continua | validate-phase3.sh #3 (`/healthz` ok), insert job → aparece em `/api/v1/jobs` | Quebra pipeline existente |
| 8 — Checkpoint humano | Job AD real → aparece + CSV | validate-phase3.sh #17 (manual) | Falha de UAT |

---

## 12. Riscos identificados + mitigações

| # | Risco | Probabilidade | Mitigação |
|---|-------|---------------|-----------|
| R-1 | `GROUP BY` por minuto agrupa **dois jobs distintos** quando dois jobs do mesmo usuário/impressora batem no mesmo minuto e têm o mesmo `job_id` (improvável — `job_id` é incremental do CUPS) | Baixa | `job_id` está na chave de grupo (D-04); ainda assim, observar contador `jobs_distintos_no_DB / jobs_agregados_na_API` no validate. |
| R-2 | `func.lower(...).contains(...)` no SQLite é case-insensitive **só para ASCII** | Média | Acentos não normalizados (ex: `josé` vs `jose`). Para MVP, aceitar (D-09 diz "case-insensitive", não "accent-insensitive"). Documentar como limitação. |
| R-3 | `StreamingResponse` + DB session: se uvicorn workers > 1 + thread-pool pequeno, sessões empilham | Baixa | Default uvicorn = 1 worker; thread pool padrão 40. Para 20-100 users + CSV ocasional, sem problema. Documentar. |
| R-4 | `_observer` global acoplado a `main.py` quebra teste unitário de `/health` | Alta (sem mitigação) | Criar `app/watcher/status.py` com singleton — 5.1 recomendação. |
| R-5 | `Base.metadata.create_all(engine)` em `session.py` roda no import → conflita com índices criados via DDL | Baixa | `create_all` não recria tabelas existentes; índices via `CREATE INDEX IF NOT EXISTS` em `ensure_indexes()` chamado no lifespan **antes** de `purge_old_jobs`. Ordem: create_all (no import) → lifespan startup → ensure_indexes → purge → start watcher. |
| R-6 | CORS preflight bate em CORSMiddleware antes do routing — origem inválida não chega ao endpoint | Conceito | É exatamente o comportamento desejado. Validado em validate-phase3 #14/#15. |
| R-7 | Cliente Windows envia date sem timezone → JSON com naive datetime vira UTC errado | Média | Filtros `date_from`/`date_to` são `date` (não datetime) — sem hora. Conversão local→UTC é determinística (start/end of day em America/Sao_Paulo). |
| R-8 | Volume `db_data` existente tem dados Fase 2 com aspa em printer — `printer` em filtros não acha | Alta | Backfill explícito (D-22). Sem o backfill, GAP-02-01 não é resolvido. Plano dedicado garante execução. |

---

## 13. Package Legitimacy Audit (novas deps)

| Pacote | Versão | Necessário para | Fonte | Veredito |
|--------|--------|-----------------|-------|----------|
| (nenhum novo) | — | CORS, CSV, pagination — tudo coberto pela stack atual (FastAPI 0.136 + pydantic 2.13 + sqlalchemy 2.0) | — | ✓ Nenhuma dependência nova exigida |

Notas:
- `CORSMiddleware` vem com FastAPI (`fastapi.middleware.cors`).
- `StreamingResponse` vem com FastAPI (`fastapi.responses`).
- `zoneinfo` é stdlib Python 3.9+ (imagem `python:3.11-slim` já tem).
- CSV escrito manualmente (não precisa `pandas`) — economiza ~50MB de dependência.

---

## 14. Bottom-Up Validation (o que provar antes do "Done")

Ordem recomendada de execução (planner deve refletir em waves):

1. **Wave 1 (paralela):**
   - Plano A: normalização + parser fix + backfill + teste regressão (D-22). Não bloqueia outras rotas.
   - Plano B: infra de rotas (CORS, docs_url, get_db_dep, includer_router vazio, expor porta 8000 no compose, ALLOWED_ORIGINS no .env). Habilita o resto.
2. **Wave 2 (paralela, depois de Wave 1):**
   - Plano C: `/api/v1/jobs` + `/jobs/{id}` (service jobs_service + schemas + tests).
   - Plano D: `/api/v1/stats/summary` (stats_service + tests).
   - Plano E: `/api/v1/printers` + `/api/v1/health` (curto).
   - Plano F: `/api/v1/export/csv` (depende de jobs_service quando agregação for compartilhada — mas pode rodar em paralelo se service for criado em C).
3. **Wave 3:**
   - Plano G: índices SQLite no lifespan (D-29) — independente, pode ir em Wave 1 também.
   - Plano H (sequencial pós-tudo): `validate-phase3.sh` + investigação GAP-02-02 + checkpoint humano.

Cobertura de requisitos por plano:
- A → resolve GAP-02-01 (sem REQ direto; melhora qualidade de DASH-04/05/EXPORT-01).
- B → infraestrutura (sem REQ direto, habilita todos).
- C → DASH-06 (parcial), suporte DASH-03/DASH-04 (Fase 4 consumirá).
- D → suporte DASH-02 (Fase 4 consumirá).
- E → suporte DASH-04 (lista printers) + health.
- F → **EXPORT-01, EXPORT-02**.
- G → **DASH-06** (índices).
- H → Nyquist + GAP-02-02 + UAT.

REQ-IDs explícitos da Fase 3 (`phase_req_ids` = `EXPORT-01, EXPORT-02, DASH-06`):
- `EXPORT-01`: Plano F.
- `EXPORT-02`: Plano F.
- `DASH-06`: Plano C (query eficiente) + Plano G (índices) — ambos compartilham `must_haves`.

---

## 15. Sumário executivo (TL;DR para planner)

1. **Versões pinadas estão OK** — FastAPI 0.136.3, SQLAlchemy 2.0.50, Pydantic 2.13.4 cobrem **tudo** sem deps novas.
2. **Estrutura de pastas confirmada:** `backend/app/api/v1/{jobs,stats,printers,export,health}.py` + `app/schemas/` + `app/services/{jobs_service,stats_service,csv_export,normalization}.py`.
3. **GAP-02-01 vira plano dedicado** — investigação observacional primeiro, depois normalizer + parser fix + backfill + teste regressão. Idempotente.
4. **GAP-02-02 = investigação documental** sem mudança de código nesta fase (a menos que evidência mostre fix trivial).
5. **Agregação por job** via `GROUP BY (printer, username, job_id, job_name, strftime('%Y-%m-%d %H:%M', timestamp))` — D-04/D-05.
6. **Timezone:** banco UTC, API ↔ user em America/Sao_Paulo (conversão na borda).
7. **CSV:** UTF-8 + BOM + `;` + `StreamingResponse` + `yield_per=1000` + cap 100k linhas. Sem novas deps.
8. **Índices SQLite via `CREATE INDEX IF NOT EXISTS`** no lifespan (idempotente).
9. **CORS sem wildcard** — lista CSV em env var `ALLOWED_ORIGINS`.
10. **Swagger reabilitado** em `/api/v1/docs` (supersede D-12 Fase 2).
11. **Expor porta 8000** no `docker-compose.yml`.
12. **`/health` 200 sempre que DB OK** (degraded só pelo watcher); **503 só se DB inacessível**.
13. **8 dimensões Nyquist** no `validate-phase3.sh` + checkpoint humano (#17).
14. **Sem deps novas** — auditoria de cadeia de suprimento OK.

---

## RESEARCH COMPLETE

Status: Pronto para planejamento. Todas as decisões D-01–D-34 traduzidas em padrões de código verificados (FastAPI 0.136, SQLAlchemy 2.0, Pydantic 2.13 via context7). Nenhum bloqueador identificado. Riscos R-1 a R-8 com mitigações claras. Estrutura de 7–8 planos em 3 waves recomendada.
