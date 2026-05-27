# Phase 4: Dashboard Web — Pattern Map

**Mapeado:** 2026-05-27  
**Arquivos analisados:** 32 novos/modificados (greenfield `frontend/` + `nginx/` + infra)  
**Análogos encontrados:** 18 / 32 (14 sem análogo React no repo — primeira UI)

---

## Contexto da Análise

Não existe pasta `frontend/` nem `nginx/` no repositório. A Fase 4 adiciona a **primeira camada React** e o **primeiro reverse proxy nginx**. Os análogos fortes são:

- **Contratos API** — `backend/app/schemas/*.py` + `backend/app/api/v1/*.py` (consumo direto)
- **Testes de integração HTTP** — `backend/tests/test_api_*.py` (query params, shapes, erros)
- **Infra Docker/Compose** — `docker-compose.yml`, `backend/Dockerfile`, `cups/Dockerfile`, `cups/entrypoint.sh`
- **Validação Nyquist** — `scripts/validate-phase3.sh` → `validate-phase4.sh`
- **Transformação de labels** — `backend/app/services/normalization.py` (padrão para `lib/media.ts`)
- **Limites de data** — `backend/app/services/stats_service.py` (alinhamento timezone com `lib/dates.ts`)

Para componentes React, primitivos UI e Headless Combobox: **sem análogo no codebase** — usar `04-RESEARCH.md` + `04-UI-SPEC.md` (planner referencia seções, não arquivos `.tsx` existentes).

---

## File Classification

| Arquivo Novo/Modificado | Role | Data Flow | Análogo Mais Próximo | Qualidade |
|-------------------------|------|-----------|----------------------|-----------|
| `frontend/package.json` | config | — | `backend/requirements.txt` (pin de deps) | partial |
| `frontend/vite.config.ts` | config | request-response (proxy) | `backend/app/main.py` (prefixo `/api/v1`) | partial |
| `frontend/index.html` | config | — | *(greenfield Vite)* | none |
| `frontend/vitest.config.ts` | config/test | — | `backend/pytest.ini` | role-match |
| `frontend/src/main.tsx` | provider | — | `backend/app/main.py` (app bootstrap) | partial |
| `frontend/src/App.tsx` | component | request-response | *(sem React no repo)* | none |
| `frontend/src/index.css` | config | — | `04-UI-SPEC.md` tokens | partial |
| `frontend/src/types/api.ts` | model | transform | `backend/app/schemas/jobs.py`, `stats.py`, `common.py` | exact |
| `frontend/src/api/client.ts` | service | request-response | `backend/tests/conftest.py` + `test_api_jobs.py` | partial |
| `frontend/src/api/jobs.ts` | service | request-response | `backend/app/api/v1/jobs.py` | exact |
| `frontend/src/api/stats.ts` | service | request-response | `backend/app/api/v1/stats.py` | exact |
| `frontend/src/api/printers.ts` | service | request-response | `backend/app/api/v1/printers.py` | exact |
| `frontend/src/api/export.ts` | service | file-I/O | `backend/app/api/v1/export.py` + `validate-phase3.sh` checks 08–10 | exact |
| `frontend/src/hooks/useJobs.ts` | hook | request-response | `backend/tests/test_api_jobs.py` | partial |
| `frontend/src/hooks/useStatsSummary.ts` | hook | request-response | `backend/tests/test_api_stats.py` | partial |
| `frontend/src/hooks/usePrinters.ts` | hook | request-response | `backend/tests/test_api_printers.py` | partial |
| `frontend/src/hooks/useUrlFilters.ts` | hook | transform | `backend/app/schemas/jobs.py` (`JobFilters`) | role-match |
| `frontend/src/lib/filters.ts` | utility | transform | `backend/app/schemas/jobs.py` | exact |
| `frontend/src/lib/dates.ts` | utility | transform | `backend/app/services/stats_service.py` | role-match |
| `frontend/src/lib/format.ts` | utility | transform | `backend/app/services/csv_export.py` (datetime pt-BR) | partial |
| `frontend/src/lib/media.ts` | utility | transform | `backend/app/services/normalization.py` | role-match |
| `frontend/src/components/layout/*` | component | — | `04-UI-SPEC.md` Layout Contract | none |
| `frontend/src/components/summary/*` | component | request-response | `backend/app/schemas/stats.py` | partial |
| `frontend/src/components/filters/*` | component | transform | `test_api_jobs.py` (params de filtro) | partial |
| `frontend/src/components/jobs/*` | component | request-response | `backend/app/schemas/jobs.py` (`JobOut`) | partial |
| `frontend/src/components/ui/*` | component | — | `04-UI-SPEC.md` Component Inventory | none |
| `frontend/src/**/*.test.ts` | test | — | `backend/tests/test_api_jobs.py` | role-match |
| `nginx/Dockerfile` | config | — | `backend/Dockerfile` + multi-stage em `04-RESEARCH.md` | role-match |
| `nginx/default.conf` | config | request-response | `cups/entrypoint.sh` (envsubst pattern) + RESEARCH nginx | partial |
| `docker-compose.yml` *(modificar)* | config | — | `docker-compose.yml` atual | exact |
| `.env.example` *(modificar)* | config | — | `.env.example` atual | exact |
| `scripts/validate-phase4.sh` | utility | — | `scripts/validate-phase3.sh` | exact |

---

## Pattern Assignments

### `frontend/src/types/api.ts` (model, transform)

**Análogo:** `backend/app/schemas/jobs.py`, `stats.py`, `common.py`

**Espelhar tipos Pydantic em TypeScript** (`jobs.py` linhas 21–80):

```python
class JobOut(BaseModel):
    id: Optional[int] = None
    printer: str
    username: str
    job_id: int
    job_name: Optional[str] = None
    timestamp: datetime  # serializado ISO em America/Sao_Paulo
    pages: int
    color_mode: Optional[str] = None
    host_origin: Optional[str] = None
    media: Optional[str] = None
    sides: Optional[str] = None
```

```python
class JobFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    page: int = Field(1, ge=1)
    size: int = Field(50, ge=1, le=500)
    username: Optional[str] = None
    printer: Optional[str] = None
    search: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
```

```python
class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
```

```python
class StatsSummaryResponse(BaseModel):
    hoje: StatsBucket
    mes: StatsBucket
    total: StatsBucket
```

**Regra:** `timestamp` no TS é `string` (ISO já convertido pelo backend). Datas de filtro são `string` no formato `yyyy-MM-dd` (query params), não `Date` objects na camada API.

---

### `frontend/src/api/client.ts` (service, request-response)

**Análogo parcial:** `backend/app/core/config.py` + padrão de chamada em `backend/tests/test_api_jobs.py`

**Base URL e timezone** (`config.py` linhas 8–12):

```python
allowed_origins: str = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:5173",
)
api_timezone: str = os.environ.get("API_TIMEZONE", "America/Sao_Paulo")
```

**Padrão de request com query params** (`test_api_jobs.py` linhas 9–14, 63–66):

```python
r = client.get("/api/v1/jobs")
assert r.status_code == 200, r.text
body = r.json()
assert body == {"items": [], "total": 0, "page": 1, "size": 50}

r = client.get(
    "/api/v1/jobs",
    params={"date_from": "2026-05-26", "date_to": "2026-05-26"},
)
```

**Adaptação frontend:**

```typescript
const baseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: unknown,
  ) {
    super(String(detail))
  }
}

export async function getJson<T>(
  path: string,
  params?: URLSearchParams,
): Promise<T> {
  const qs = params?.toString()
  const url = `${baseUrl}${path}${qs ? `?${qs}` : ''}`
  const res = await fetch(url, { headers: { Accept: 'application/json' } })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new ApiError(res.status, (detail as { detail?: unknown })?.detail ?? res.statusText)
  }
  return res.json() as Promise<T>
}
```

**Erro 422:** backend retorna corpo FastAPI/Pydantic — tratar em UI de filtros (não silenciar). Espelhar asserts `test_list_jobs_pagination_size_too_large` (422 para `size=999`).

---

### `frontend/src/api/jobs.ts` (service, request-response)

**Análogo:** `backend/app/api/v1/jobs.py`

**Rota e shape de resposta** (`jobs.py` linhas 17–28):

```python
@router.get("", response_model=Page[JobOut])
def list_jobs_endpoint(
    filters: Annotated[JobFilters, Query()],
    db: Session = Depends(get_db_dep),
) -> Page[JobOut]:
    items, total = jobs_service.list_jobs(db, filters)
    return Page[JobOut](
        items=items,
        total=total,
        page=filters.page,
        size=filters.size,
    )
```

**Adaptação:**

```typescript
import { getJson } from './client'
import type { JobFilters, JobOut, Page } from '../types/api'
import { filtersToSearchParams } from '../lib/filters'

export function fetchJobs(filters: JobFilters): Promise<Page<JobOut>> {
  return getJson<Page<JobOut>>('/jobs', filtersToSearchParams(filters))
}
```

**Montagem de rotas** (`backend/app/api/v1/__init__.py` linhas 5–10) — paths relativos ao prefixo `/api/v1`:

```python
api_v1_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
```

---

### `frontend/src/api/stats.ts` (service, request-response)

**Análogo:** `backend/app/api/v1/stats.py`

```python
@router.get("/summary", response_model=StatsSummaryResponse)
def stats_summary_endpoint(
    top: int = Query(5, ge=1, le=50, ...),
    db: Session = Depends(get_db_dep),
) -> StatsSummaryResponse:
    return stats_service.compute_summary(db, top_n=top)
```

**Adaptação:** `GET /stats/summary` sem params no MVP (default `top=5` basta para cards que usam `[0]`).

```typescript
export function fetchStatsSummary(): Promise<StatsSummaryResponse> {
  return getJson<StatsSummaryResponse>('/stats/summary')
}
```

---

### `frontend/src/api/printers.ts` (service, request-response)

**Análogo:** `backend/app/api/v1/printers.py`

```python
@router.get("", response_model=list[str])
def list_printers_endpoint(db: Session = Depends(get_db_dep)) -> list[str]:
    return jobs_service.list_printer_names(db)
```

**Adaptação:**

```typescript
export function fetchPrinters(): Promise<string[]> {
  return getJson<string[]>('/printers')
}
```

---

### `frontend/src/api/export.ts` (service, file-I/O)

**Análogo:** `backend/app/api/v1/export.py` + `scripts/validate-phase3.sh` (checks 08–10)

**Handler com cap 100k** (`export.py` linhas 15–37):

```python
@router.get("/csv")
def export_csv_endpoint(
    filters: JobFilters = Depends(),
    db: Session = Depends(get_db_dep),
) -> StreamingResponse:
    total = csv_export.count_aggregated(db, filters)
    if total > csv_export.MAX_CSV_ROWS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(f"Export excede {csv_export.MAX_CSV_ROWS:,} linhas ..."),
        )
    return StreamingResponse(
        csv_export.iter_csv_rows(db, filters),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Total-Rows": str(total),
        },
    )
```

**Validação curl de headers** (`validate-phase3.sh` linhas 134–138):

```bash
check "08 CSV Content-Type text/csv" \
  bash -c "curl -s -o /dev/null -D - '$BASE_URL/api/v1/export/csv' | grep -qi '^content-type: text/csv'"
check "08b CSV Content-Disposition attachment" \
  bash -c "curl -s -o /dev/null -D - '$BASE_URL/api/v1/export/csv' | grep -qi '^content-disposition: attachment'"
```

**Adaptação frontend (sem `page`/`size` nos params — D-35):**

```typescript
export async function downloadCsv(filters: Omit<JobFilters, 'page' | 'size'>): Promise<void> {
  const params = filtersToSearchParams({ ...filters, page: 1, size: 50 })
  params.delete('page')
  params.delete('size')
  const res = await fetch(`/api/v1/export/csv?${params}`)
  if (res.status === 400) {
    const body = await res.json()
    throw new ExportCapError(body.detail)
  }
  if (!res.ok) throw new Error('export failed')
  const blob = await res.blob()
  const filename =
    res.headers.get('Content-Disposition')?.match(/filename="(.+)"/)?.[1] ??
    'print_jobs.csv'
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
```

---

### `frontend/src/lib/filters.ts` (utility, transform)

**Análogo:** `backend/app/schemas/jobs.py` (`JobFilters`)

**Serialização URL ↔ API** — espelhar nomes exatos dos campos Pydantic (`jobs.py` linhas 64–70):

```python
page: int = Field(1, ge=1)
size: int = Field(50, ge=1, le=500)
username: Optional[str] = None
printer: Optional[str] = None
search: Optional[str] = None
date_from: Optional[date] = None
date_to: Optional[date] = None
```

```typescript
export function filtersToSearchParams(f: JobFilters): URLSearchParams {
  const p = new URLSearchParams()
  p.set('page', String(f.page ?? 1))
  p.set('size', String(f.size ?? 50))
  if (f.date_from) p.set('date_from', f.date_from)
  if (f.date_to) p.set('date_to', f.date_to)
  if (f.username) p.set('username', f.username)
  if (f.printer) p.set('printer', f.printer)
  if (f.search) p.set('search', f.search)
  return p
}

export function searchParamsToFilters(params: URLSearchParams): JobFilters {
  return {
    page: Number(params.get('page') ?? 1),
    size: Number(params.get('size') ?? 50),
    date_from: params.get('date_from') ?? undefined,
    date_to: params.get('date_to') ?? undefined,
    username: params.get('username') ?? undefined,
    printer: params.get('printer') ?? undefined,
    search: params.get('search') ?? undefined,
  }
}
```

**Defaults da API** (`test_api_jobs.py` linha 13): lista vazia retorna `page: 1`, `size: 50`.

**Limpar filtros (D-22):** reset para `new URLSearchParams({ page: '1', size: '50' })` apenas.

---

### `frontend/src/lib/dates.ts` (utility, transform)

**Análogo:** `backend/app/services/stats_service.py` + `backend/app/core/config.py`

**Timezone compartilhada** (`stats_service.py` linhas 29–37, 40–49):

```python
_TZ = ZoneInfo(settings.api_timezone)

def _today_bounds_local() -> tuple[date, date]:
    now_local = datetime.now(_TZ)
    today = now_local.date()
    return today, today

def _month_bounds_local() -> tuple[date, date]:
    now_local = datetime.now(_TZ)
    first = now_local.date().replace(day=1)
    # ... último dia do mês calendário
    return first, last
```

**Diferença crítica (pitfall RESEARCH):** preset **“Mês atual”** no filtro da tabela = 1º dia → **hoje** (`presetMonthToDate`). Bucket `stats.mes` na API = mês calendário **fechado** (1º → último dia). Cards **nunca** derivam dos filtros da tabela — só de `/stats/summary`.

**Preset “Últimos 7 dias”:** alinhar com `subDays(end, 6)` inclusive (7 dias corridos).

**Formato enviado à API:** `yyyy-MM-dd` strings (mesmo tipo que `JobFilters.date_from` Pydantic `date`).

---

### `frontend/src/lib/media.ts` (utility, transform)

**Análogo:** `backend/app/services/normalization.py`

**Padrão idempotente com fallback** (`normalization.py` linhas 29–42):

```python
def normalize_printer_name(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    s = raw.strip()
    # ... mapa estático + fallback valor bruto
    return s
```

**Adaptação para `formatMediaLabel`:**

```typescript
const MEDIA_LABELS: Record<string, string> = {
  iso_a4_210x297mm: 'A4',
  na_letter_8.5x11in: 'Carta',
}

export function formatMediaLabel(raw: string | null | undefined): string {
  if (!raw) return '—'
  return MEDIA_LABELS[raw] ?? raw
}
```

Sem i18n; mapa extensível (D-32).

---

### `frontend/src/lib/format.ts` (utility, transform)

**Análogo parcial:** `backend/app/schemas/jobs.py` serializer + comentários em `test_api_jobs.py`

**Timestamp já em SP na API** (`jobs.py` linhas 46–52):

```python
@field_serializer("timestamp")
def _serialize_timestamp_in_sao_paulo(self, value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(_API_TZ).isoformat()
```

**Teste documenta offset** (`test_api_jobs.py` linhas 111+): não aplicar segunda conversão de timezone no cliente — `format(parseISO(row.timestamp), 'dd/MM/yyyy HH:mm')`.

**Números pt-BR nos cards (D-12):** `new Intl.NumberFormat('pt-BR').format(n)` para `"1.284 páginas"`.

---

### `frontend/src/hooks/useJobs.ts` (hook, request-response)

**Análogo parcial:** `backend/tests/test_api_jobs.py` + TanStack Query em `04-RESEARCH.md`

**Query key deve incluir filtros serializados** — espelhar variedade de params dos testes:

```python
# username contains case-insensitive
client.get("/api/v1/jobs", params={"username": "usr1"})
# printer exact match
client.get("/api/v1/jobs", params={"printer": "alpha"})
# search in job_name
client.get("/api/v1/jobs", params={"search": "B.pdf"})
```

```typescript
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { fetchJobs } from '../api/jobs'
import type { JobFilters } from '../types/api'

export function useJobs(filters: JobFilters) {
  return useQuery({
    queryKey: ['jobs', filters],
    queryFn: () => fetchJobs(filters),
    placeholderData: keepPreviousData,
  })
}
```

**CORS em dev:** `main.py` linhas 85–91 — GET only; dev Vite em `:5173` precisa proxy ou `ALLOWED_ORIGINS`.

---

### `frontend/src/hooks/useStatsSummary.ts` (hook, request-response)

**Análogo parcial:** `backend/app/schemas/stats.py` + `test_api_stats.py`

```typescript
export function useStatsSummary() {
  return useQuery({
    queryKey: ['stats', 'summary'],
    queryFn: () => fetchStatsSummary(),
    staleTime: 60_000,
  })
}
```

Cards leem `data.hoje.jobs`, `data.hoje.pages`, `data.mes.top_users[0]`, `data.mes.top_printers[0]` — empty state se array vazio (D-12).

---

### `frontend/src/hooks/usePrinters.ts` (hook, request-response)

**Análogo:** `backend/app/api/v1/printers.py`

```typescript
export function usePrinters() {
  return useQuery({
    queryKey: ['printers'],
    queryFn: () => fetchPrinters(),
    staleTime: 5 * 60_000,
  })
}
```

Lista estável; combobox filtra client-side (D-20).

---

### `frontend/src/hooks/useUrlFilters.ts` (hook, transform)

**Análogo:** `JobFilters` + ausência de React Router (D-44)

**Padrão:** `window.location.search` + `history.replaceState` (não `pushState` em cada keystroke de debounced `search`).

Sincronizar com `lib/filters.ts` `searchParamsToFilters` / `filtersToSearchParams`.

**Debounce 300ms** só para escrever `search` na URL (D-60) — valor local no input até debounce disparar.

---

### `frontend/vite.config.ts` (config, request-response)

**Análogo parcial:** `backend/app/main.py` prefixo `/api/v1`

```python
app.include_router(api_v1_router, prefix="/api/v1")
```

**Proxy dev (D-57) — sem rewrite:**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // NÃO rewrite — preserva /api/v1
      },
    },
  },
})
```

---

### `frontend/src/main.tsx` (provider)

**Análogo parcial:** `backend/app/main.py` (montagem da app + middleware)

```python
app = FastAPI(...)
app.add_middleware(CORSMiddleware, ...)
app.include_router(api_v1_router, prefix="/api/v1")
```

**Adaptação:**

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
})

// <QueryClientProvider client={queryClient}><App /></QueryClientProvider>
```

---

### `frontend/src/components/**` (component)

**Análogo:** `04-UI-SPEC.md` (sem `.tsx` no repo)

| Subpasta | Contrato UI-SPEC | Dados |
|----------|------------------|-------|
| `layout/` | Shell 220px sidebar, PageHeader + Export outline | — |
| `summary/` | 4 cards, grid, empty “Sem dados no período” | `StatsSummaryResponse` |
| `filters/` | Presets segmented, filtros sempre visíveis | URL + `usePrinters` |
| `jobs/` | Tabela ~40px, sticky header, zebra `#FAFAFC` | `Page<JobOut>` |
| `ui/` | Button, Input, Skeleton, ErrorBanner, EmptyState | tokens `:root` |

**Mapeamento colunas tabela (D-24–D-25):** usar `JobOut` fields diretamente; `media` via `formatMediaLabel`; `pages` `text-right`; `username` `truncate` + `title`.

**Combobox impressora:** `@headlessui/react` — exemplo canônico em `04-RESEARCH.md` seção Code Examples (sem arquivo local).

---

### `nginx/Dockerfile` (config)

**Análogo:** `backend/Dockerfile` + padrão multi-stage em `04-RESEARCH.md`

**Backend — stages COPY + ENTRYPOINT** (`backend/Dockerfile` linhas 1–13):

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
COPY app/ ./app/
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
```

**Adaptação nginx (build Node → serve nginx):**

```dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
```

**Convenções herdadas:** `WORKDIR`, `COPY` explícito, imagens Alpine/slim, `EXPOSE` apenas onde há porta pública (80).

---

### `nginx/default.conf` (config, request-response)

**Análogo parcial:** comentário compose Fase 4 + `04-RESEARCH.md` Pattern 6

**Compose preparado** (`docker-compose.yml` linha 33):

```yaml
  # Fase 4+: frontend + nginx (proxy :80 → dashboard + API)
```

**Config nginx canônica (RESEARCH — copiar estrutura):**

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    gzip on;
    gzip_types text/css application/javascript application/json;

    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|svg|ico|woff2?)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Trailing slash:** `location /api/` + `proxy_pass http://backend:8000/api/` — obrigatório para preservar `/api/v1/...`.

---

### `docker-compose.yml` (config, modificar)

**Análogo:** `docker-compose.yml` atual (serviços `cups` + `backend`)

**Padrão de serviço existente** (linhas 19–31):

```yaml
  backend:
    build: ./backend
    env_file: .env
    environment:
      DB_PATH: ${DB_PATH:-/app/data/printwatch.db}
      ...
    volumes:
      - cups_logs:/var/log/cups:ro
      - db_data:/app/data
    restart: unless-stopped
    depends_on:
      - cups
```

**Adição Fase 4 (D-56):**

```yaml
  nginx:
    build:
      context: .
      dockerfile: nginx/Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

**Não expor `backend` no host** (D-56) — remover `ports: 8000:8000` se adicionado na Fase 3. Backend só via rede Docker `backend:8000`.

**Manter comentário de expansão** no topo (linhas 1–2) atualizado após nginx ativo.

---

### `.env.example` (config, modificar)

**Análogo:** `.env.example` atual

**Padrão de documentação** (linhas 1–7):

```bash
# PrintWatch — variáveis de ambiente (Fase 1)
# Copie este arquivo para .env antes de executar `docker compose up -d`:
#   cp .env.example .env
```

**Adicionar Fase 4:**

```bash
# Fase 3/4 — API CORS (dev Vite :5173)
ALLOWED_ORIGINS=http://localhost:5173,http://<VM_HOST>

# Fase 4 — frontend (opcional; vazio = same-origin /api/v1)
# VITE_API_BASE_URL=
```

Espelhar default de `config.py` (`allowed_origins`).

---

### `scripts/validate-phase4.sh` (utility)

**Análogo:** `scripts/validate-phase3.sh` — **match estrutural exato**

**Cabeçalho e helpers** (`validate-phase3.sh` linhas 1–65):

```bash
#!/usr/bin/env bash
# PrintWatch — validação Fase 3 (Backend API)
# Uso: bash scripts/validate-phase3.sh [--quick]
set -euo pipefail

if [[ -n "${MSYSTEM:-}" ]] || [[ "$(uname -s 2>/dev/null)" == MINGW* ]]; then
  export MSYS_NO_PATHCONV=1
fi

QUICK=false
FAILURES=0
WARNINGS=0
BASE_URL="${BASE_URL:-http://localhost:8000}"

pass() { echo "  [PASS] $*"; }
fail() { echo "  [FAIL] $*" >&2; FAILURES=$((FAILURES + 1)); }
warn() { echo "  [WARN] $*"; WARNINGS=$((WARNINGS + 1)); }

check_http() {
  local label="$1"
  local expected_code="$2"
  local url="$3"
  ...
}
```

**Adaptação Fase 4:**

| Check | Fonte fase 3 | URL Fase 4 |
|-------|--------------|------------|
| Health | check 03–04 | `http://localhost/api/v1/health` |
| Jobs shape | check 05 | via nginx proxy |
| Stats shape | *(novo)* | `/api/v1/stats/summary` |
| Export CSV | checks 08–10 | mesmo path via :80 |
| SPA index | *(novo)* | `curl -sf http://localhost/` contém `<div id="root">` ou asset Vite |
| gzip | *(novo)* | header em `.js` hashed |

**Default `BASE_URL`:** `http://localhost` (nginx :80), não `:8000`.

Reutilizar checks 11–15 de validação de filtros/422/CORS onde aplicável (CORS ainda relevante para dev `:5173`).

---

### `frontend/vitest.config.ts` + `frontend/src/lib/*.test.ts` (test)

**Análogo:** `backend/pytest.ini` + `backend/tests/test_api_jobs.py`

**Estrutura de teste de contrato** (`test_api_jobs.py` linhas 9–14):

```python
def test_list_jobs_empty_returns_page_schema(client: TestClient) -> None:
    r = client.get("/api/v1/jobs")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body == {"items": [], "total": 0, "page": 1, "size": 50}
```

**Vitest deve cobrir (Wave 0):**

- `filtersToSearchParams` / `searchParamsToFilters` round-trip
- `presetToday`, `presetLast7Days`, `presetMonthToDate` formato `yyyy-MM-dd`
- `formatMediaLabel` mapa + fallback

**Não duplicar** testes E2E HTTP no Vitest — isso fica em `validate-phase4.sh`.

---

## Shared Patterns

### Prefixo API versionado

**Source:** `backend/app/main.py` linha 93  
**Apply to:** `api/client.ts`, `vite.config.ts` proxy, `nginx/default.conf`

```python
app.include_router(api_v1_router, prefix="/api/v1")
```

Cliente usa paths relativos `/jobs`, `/stats/summary` com `baseUrl = '/api/v1'`.

---

### Paginação e filtros (contrato único)

**Source:** `backend/app/schemas/jobs.py`  
**Apply to:** `types/api.ts`, `lib/filters.ts`, `hooks/useJobs.ts`, export (sem page/size)

Defaults: `page=1`, `size=50`. Validação 422 para `size>500`, `page<1`, `date_from > date_to` — UI não precisa prevalidar tudo, mas deve exibir erro API.

---

### Timezone America/Sao_Paulo

**Source:** `backend/app/core/config.py`, `jobs.py` serializer, `stats_service.py`  
**Apply to:** `lib/dates.ts`, `lib/format.ts`

- Filtros: calcular presets com `@date-fns/tz`
- Exibição: confiar no ISO já convertido pela API
- Cards stats: independentes dos filtros da tabela

---

### Docker Compose — expansão incremental

**Source:** `docker-compose.yml` + `02-PATTERNS.md`  
**Apply to:** serviço `nginx`

Padrão: `build`, `env_file`, `depends_on`, `restart: unless-stopped`, volumes nomeados existentes intactos.

---

### Validação Nyquist

**Source:** `scripts/validate-phase3.sh`  
**Apply to:** `scripts/validate-phase4.sh`

`set -euo pipefail`, `pass`/`fail`/`warn`, `--quick`, `MSYS_NO_PATHCONV`, checks numerados, `BASE_URL` configurável.

---

### Scripts bash entrypoint

**Source:** `backend/entrypoint.sh`, `cups/entrypoint.sh`  
**Apply to:** *(nginx usa imagem oficial — sem entrypoint custom no MVP)*

```bash
#!/bin/bash
set -euo pipefail
export VAR="${VAR:-default}"
mkdir -p "$(dirname "$path")"
exec <processo-principal>
```

---

### Transformação com fallback (labels)

**Source:** `backend/app/services/normalization.py`  
**Apply to:** `lib/media.ts`, exibição de `username` truncado

Idempotente, sem throw, fallback = valor bruto.

---

## No Analog Found

| File / Area | Role | Data Flow | Reason |
|-------------|------|-----------|--------|
| `frontend/src/App.tsx` | component | request-response | Primeiro componente React do projeto |
| `frontend/src/components/ui/*` | component | — | Design system local; contrato só em `04-UI-SPEC.md` |
| `frontend/src/components/layout/*` | component | — | Layout Apple HIG — sem referência TSX no repo |
| `frontend/index.html` | config | — | Scaffold Vite padrão upstream |
| Headless Combobox | component | transform | `@headlessui/react` — usar RESEARCH Code Examples |
| Vitest + Testing Library | test | — | Stack nova; espelhar *estrutura* pytest, não código |

**Fallback para planner:** `04-RESEARCH.md` seções Standard Stack, Architecture Patterns, Code Examples, Anti-Patterns.

---

## Metadata

**Analog search scope:** `backend/app/{api,schemas,services,core}`, `backend/tests/`, `scripts/validate-phase*.sh`, `docker-compose.yml`, `.env.example`, `*/Dockerfile`, `*/entrypoint.sh`, `.planning/phases/{02,03,04}/*.md`  
**Files scanned:** ~45  
**Pattern extraction date:** 2026-05-27
