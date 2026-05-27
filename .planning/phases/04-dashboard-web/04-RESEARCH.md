# Phase 4: Dashboard Web - Research

**Researched:** 2026-05-27  
**Domain:** React 18 + Vite + TypeScript + Tailwind CSS SPA; TanStack Query v5; nginx :80 + Docker Compose; consumo da API FastAPI Fase 3  
**Confidence:** HIGH (stack e contratos API); MEDIUM (Docker/nginx multi-stage — padrão estabelecido, sem implementação prévia no repo)

## Summary

A Fase 4 é **greenfield frontend**: não existe pasta `frontend/` no repositório. O dashboard consome exclusivamente a API já implementada em `backend/app/api/v1/` via same-origin em produção (`Browser → nginx:80 → proxy /api/ → backend:8000`) e via `server.proxy` do Vite em desenvolvimento.

As decisões de `04-CONTEXT.md` fixam stack (React 18, Vite, TS, Tailwind, TanStack Query v5, Headless UI Combobox, lucide-react, date-fns + `@date-fns/tz`), UX Apple/PaperCut, URL como fonte da verdade dos filtros, paginação server-side obrigatória e deploy nginx na porta 80. O planner deve espelhar schemas Pydantic em TypeScript, evitar Redux/Zustand, e não introduzir React Router até a Fase 5.

**Primary recommendation:** Scaffold `frontend/` com Vite React-TS + Tailwind v4 (`@tailwindcss/vite`), camada `api/*` + hooks Query, página única com filtros sincronizados via `URLSearchParams` (sem React Router), build multi-stage Docker copiando `dist/` para `nginx`, e `validate-phase4.sh` no padrão Nyquist das fases 2–3.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Listagem/filtros/paginação de jobs | API / Backend | Browser (UI + URL state) | Agregação SQL, índices e `Page.total` são server-side (D-59, DASH-06) |
| Cards de sumário (hoje, tops mês) | API / Backend | Browser (render) | `GET /stats/summary` pré-computa buckets; cliente não recalcula tops (D-13) |
| Lista de impressoras (dropdown) | API / Backend | Browser (combobox + filtro local) | `DISTINCT printer` no SQLite; match exato no param `printer` (D-20) |
| Export CSV | API / Backend | Browser (blob download) | Streaming + cap 100k no backend; frontend só repassa filtros (D-35) |
| Presets de data (Hoje/7d/Mês) | Browser | API (interpreta `date_from`/`date_to`) | Cálculo de intervalo em `America/Sao_Paulo` no cliente; API valida range (D-42, Fase 3 D-10) |
| Formatação exibição (pt-BR, `dd/MM/yyyy HH:mm`) | Browser | — | `timestamp` já serializado em SP pela API; `format(parseISO(...))` |
| Normalização coluna Papel | Browser | — | `formatMediaLabel` mapa local (D-31–D-33) |
| Autenticação / TLS | — | — | Fora do escopo MVP |
| Servir SPA + proxy API | CDN/Static (nginx) | Docker Compose | Única porta pública :80 (D-52, D-56) |
| Persistência / retenção | Database | — | Sem mudança nesta fase |

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### A. Direção visual — Apple HIG + PaperCut

- **D-01:** Estética **Apple-like**: clean, minimalista, branco predominante, hierarquia tipográfica forte, muito espaço em branco, sensação **calma** (evitar visual NOC/SOC, admin template genérico, dashboards poluídos).
- **D-02:** Verde de acento inspirado no PaperCut: primário **`#00AE5B`**, hover **`#009952`**, tint de fundo **`#E8F7EF`**. Usar verde apenas para ações primárias, estados ativos e foco — não como fundo dominante.
- **D-03:** Fundos: canvas **`#F5F5F7`** (cinza Apple), superfícies (cards, barra de filtros) **`#FFFFFF`**. Texto primário **`#1D1D1F`**, secundário **`#6E6E73`**, bordas **`#D2D2D7`**.
- **D-04:** Cards de sumário **discretos**: borda `1px`, radius ~12px, sombra mínima (`0 1px 2px` no máximo) — **sem** gradientes, **sem** sombras pesadas, **sem** widgets decorativos.
- **D-05:** Tipografia: stack de sistema `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` (Inter opcional se o planner preferir consistência cross-OS). Escala clara: título de página, labels de filtro, corpo de tabela, meta.
- **D-06:** Espaçamento alinhado ao HIG: escala Tailwind baseada em **16px** como unidade confortável (4/8/12/16/20/24/32); margens generosas; controles agrupados logicamente (sumário → filtros → tabela).
- **D-07:** Motion: animações **mínimas** (150–200ms); respeitar `prefers-reduced-motion`; sem parallax; feedback de hover/focus discreto.
- **D-08:** Acessibilidade: contraste adequado (texto primário em fundo claro); estados não dependem só de cor; focus ring visível (verde com offset); suporte a navegação por teclado nos controles principais.
- **D-09:** Referência de design obrigatória para planner/UI: [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/) — layout, listas/tabelas, search fields, loading, cor, tipografia, empty states (consultado via context7 na discussão).

#### B. Cards de sumário (DASH-02)

- **D-10:** Quatro cards na página principal:
  1. **Jobs hoje** — `stats.hoje.jobs`
  2. **Páginas hoje** — `stats.hoje.pages`
  3. **Top usuário do mês** — `stats.mes.top_users[0]`
  4. **Top impressora do mês** — `stats.mes.top_printers[0]`
- **D-11:** Motivo da escolha **mês** para tops (não “top do dia”): mais útil gerencialmente, menos volatilidade visual, alinha com `REQUIREMENTS.md` DASH-02 (“top usuário do mês”).
- **D-12:** Cards de top exibem **nome + total de páginas** no mesmo bloco, formato: `"Maria Silva — 1.284 páginas"` (número formatado pt-BR com separador de milhar). Se `top_users` ou `top_printers` vazio: empty state do card (“Sem dados no período”).
- **D-13:** Fonte de dados: **única** chamada `GET /api/v1/stats/summary` (sem recalcular tops no cliente). Cache TanStack Query com `staleTime` ~30–60s.
- **D-14:** **Sem gráficos/charts** nesta fase — cards numéricos/textuais apenas.

#### C. Filtros e presets de data (DASH-04, DASH-05)

- **D-15:** Filtros **sempre visíveis** acima da tabela — **não** esconder em modal ou drawer.
- **D-16:** Presets de data rápidos (troca instantânea, UX tipo analytics Apple/PaperCut):
  - **Hoje**
  - **Últimos 7 dias**
  - **Mês atual** (1º dia → hoje, calendário `America/Sao_Paulo`, coerente com API Fase 3)
- **D-17:** Além dos presets: **intervalo custom** via date picker (`date_from` / `date_to`) — inputs `type="date"` ou componente equivalente leve.
- **D-18:** Presets atualizam `date_from`/`date_to` na **URL** (`searchParams`) e disparam refetch imediato da tabela.
- **D-19:** Filtro **usuário**: campo texto; API usa `username` **contains case-insensitive** (D-09 Fase 3) — sem dropdown de usuários nesta fase.
- **D-20:** Filtro **impressora**: **dropdown** alimentado por `GET /api/v1/printers`; **match exato** no param `printer`; **busca interna** no dropdown (typeahead/combobox); **sem free text** nesta fase.
- **D-21:** Busca por **arquivo/documento** (`search`): campo sempre acessível na barra de filtros; **debounce 300ms** antes de refetch; API `job_name LIKE %term%`.
- **D-22:** Botão **Limpar filtros** reseta URL para defaults (sem filtros, `page=1`, `size=50`).
- **D-23:** **Fonte da verdade dos filtros:** URL query string — `date_from`, `date_to`, `username`, `printer`, `search`, `page`, `size`. Permite compartilhar link e debug.

#### D. Tabela de jobs (DASH-03)

- **D-24:** Colunas obrigatórias (ordem): **Data/Hora**, **Usuário**, **Impressora**, **Arquivo**, **Páginas**, **Papel**, **Origem**.
- **D-25:** Mapeamento API → UI:

  | Coluna UI | Campo `JobOut` |
  |-----------|----------------|
  | Data/Hora | `timestamp` (ISO serializado em America/Sao_Paulo) |
  | Usuário | `username` |
  | Impressora | `printer` |
  | Arquivo | `job_name` |
  | Páginas | `pages` (alinhado à direita) |
  | Papel | `media` (via helper D-32) |
  | Origem | `host_origin` |

- **D-26:** Densidade **semi-compacta confortável**: altura de linha alvo **~40px**; leitura contínua (referência: Apple Settings + tabelas PaperCut).
- **D-27:** **Sticky header** na tabela; **zebra extremamente sutil** (quase invisível, ex. `#FAFAFC` alternado); **hover de linha discreto** (`#F9F9FB`); **sem grid pesada** — separadores horizontais leves ou zebra apenas.
- **D-28:** Paginação **server-side obrigatória** via `GET /api/v1/jobs` — defaults `page=1`, `size=50`; expor seletor de página e total (`Page.total`). **Nunca** carregar 50k+ registros no browser.
- **D-29:** Ordem default da API: `timestamp DESC` (sem controle de sort no MVP).
- **D-30:** Username longo (`DOMINIO\usuario`): `truncate` com `title` tooltip no hover.

#### E. Coluna Papel — normalização leve

- **D-31:** MVP exibe valor derivado de `media` com **helper local simples** (`formatMediaLabel(raw)`), mapa estático, **fallback = valor bruto** se não reconhecido.
- **D-32:** Mapeamentos iniciais (extensível sem i18n):

  | Valor CUPS/API (exemplo) | Rótulo UI |
  |--------------------------|-----------|
  | `iso_a4_210x297mm` | A4 |
  | `na_letter_8.5x11in` | Carta |
  | (outros) | valor bruto |

- **D-33:** Sem camada de i18n; sem serviço de tradução; mapa em `frontend/src/lib/media.ts` (ou equivalente).

#### F. Export CSV (EXPORT-01)

- **D-34:** Botão **Exportar CSV** claramente visível no header da página principal (ação secundária outline ou equivalente discreto).
- **D-35:** Export usa **mesmos query params de filtro** da tabela (`username`, `printer`, `search`, `date_from`, `date_to`) — **sem** `page`/`size`.
- **D-36:** Implementação: `GET /api/v1/export/csv` → download via `blob` + `<a download>` ou navegação controlada; exibir loading no botão durante download.
- **D-37:** Erro **400** (cap 100k linhas): exibir mensagem do backend e sugerir estreitar período/filtros (não falhar silenciosamente).

#### G. Stack e arquitetura frontend

- **D-38:** **React 18 + Vite + TypeScript + Tailwind CSS** — conforme `PROJECT.md`; sem MUI, sem Ant Design, sem Bootstrap.
- **D-39:** Estado servidor: **TanStack Query v5** para `jobs`, `stats/summary`, `printers` — **sem** Redux/Zustand/global store no MVP.
- **D-40:** HTTP: `fetch` encapsulado em `api/client.ts`; base URL **`/api/v1`** (same-origin via nginx em produção).
- **D-41:** Ícones: **lucide-react** (traço fino, estilo compatível com Apple-like).
- **D-42:** Datas no cliente: **date-fns** para calcular presets (Hoje, 7 dias, Mês atual) em timezone **`America/Sao_Paulo`** — alinhado à API.
- **D-43:** Combobox impressora: **@headlessui/react** (ou primitivo acessível equivalente leve) — única dependência UI “headless” recomendada; evitar biblioteca de componentes completa.
- **D-44:** **Uma rota/página** no MVP (`/`) — sem React Router até existir segunda tela (Fase 5 SERVER-04).
- **D-45:** Estrutura de pastas conforme proposta da discussão:

  ```
  frontend/
  ├── src/
  │   ├── api/          # client, jobs, stats, printers, export
  │   ├── hooks/        # useJobs, useStatsSummary, usePrinters
  │   ├── components/   # layout, summary, filters, jobs, ui/
  │   ├── lib/          # format.ts, filters.ts, media.ts
  │   └── types/        # api.ts
  nginx/
  ├── Dockerfile
  └── default.conf
  ```

#### H. Layout e UX

- **D-46:** **Desktop-first**; mobile apenas funcional (sidebar colapsável, tabela com scroll horizontal, filtros empilhados) — não é critério de aceite principal.
- **D-47:** Shell: **sidebar estreita** (~220px) com branding PrintWatch + item **Jobs** (único no MVP); área principal com título, export, cards, filtros, tabela, paginação.
- **D-48:** **Tabela é o centro do produto** — maior área visual; cards secundários.
- **D-49:** Loading: **skeleton elegante** nos 4 cards + ~8 linhas da tabela no carregamento inicial; refetch de filtros com opacidade reduzida na tabela + indicador fino indeterminado (estilo HIG).
- **D-50:** Empty state (zero jobs): mensagem clara + CTA “Limpar filtros”. Empty com filtros ativos: mensagem específica (“Ajuste o período ou a impressora”).
- **D-51:** Erro API: banner discreto com “Tentar novamente” (refetch Query).

#### I. Deploy — nginx + Docker Compose (DASH-01)

- **D-52:** **nginx nesta fase** — servido em **porta 80** no host; acesso alvo `http://<VM_HOST>` (sem `:5173` em produção).
- **D-53:** Estratégia: **Vite build estático** (`frontend/dist`) copiado para imagem nginx; `try_files` SPA fallback para `index.html`.
- **D-54:** nginx **proxy** `location /api/` → `http://backend:8000/api/` (preservar prefixo `/api/v1`).
- **D-55:** **Sem TLS** nesta fase; **sem** autenticação; **sem** reverse proxy complexo (rate limit, mTLS, etc.).
- **D-56:** `docker-compose.yml`: adicionar serviços `frontend` (build stage ou artefato) + `nginx` (`depends_on: backend`); **única porta pública do dashboard: 80** (backend pode permanecer sem `ports:` no host — apenas rede interna Docker).
- **D-57:** Dev local: Vite `server.proxy` `/api` → `http://localhost:8000` para DX; produção usa same-origin (CORS irrelevante no browser para dashboard em :80).
- **D-58:** Atualizar `.env.example` com variáveis Fase 4 se necessário (`VITE_*` mínimo); `ALLOWED_ORIGINS` pode incluir `http://VM_HOST` (já previsto Fase 3).

#### J. Performance (DASH-06)

- **D-59:** Paginação server-side **obrigatória** — nunca client-side filter sobre dataset completo.
- **D-60:** Debounce **300ms** em `search` (arquivo).
- **D-61:** Evitar virtualização no MVP salvo profiling com `size=500` mostrar lag — default `size=50`.
- **D-62:** Meta de experiência: shell + skeleton < ~500ms; dados cards + tabela em paralelo (`stats` + `jobs`); TTFB API < 500ms (dependência Fase 3 / índices).
- **D-63:** Build produção: gzip nginx para estáticos; cache immutable para assets hashed do Vite.

#### K. Diretrizes transversais para o planner

- **D-64:** **Estabilidade > abstração** — componentes simples, ~6 primitivos UI (`Button`, `Input`, `Select`, `Skeleton`, etc.), sem Storybook obrigatório.
- **D-65:** Reutilizar contratos API existentes (`JobOut`, `JobFilters`, `Page`, `StatsSummaryResponse`) — tipos TypeScript espelhando `backend/app/schemas/`.
- **D-66:** Não criar segunda camada de “repository” no frontend — hooks Query chamam `api/*` diretamente.
- **D-67:** Validação: `scripts/validate-phase4.sh` no padrão Nyquist das fases anteriores + checkpoint humano (cards vs SQL, filtros, export, abertura < 2s na rede local).

### Claude's Discretion

- Nome exato dos arquivos de componente e subdivisão de `ui/`.
- Se usar Inter vs apenas system font stack.
- Implementação exata do combobox (Headless UI vs nativo `<select>` com filtro — preferir combobox se esforço baixo).
- Detalhe do skeleton (CSS puro vs pequeno componente).
- Ordem dos plans em waves (scaffold → API hooks → shell → cards → filtros → tabela → export → nginx → validate).
- Variáveis de ambiente `VITE_API_BASE_URL` vazia em prod (same-origin) vs explícita.

### Deferred Ideas (OUT OF SCOPE)

- **Gráficos/charts** (tendência diária, pizza por impressora) — pós-MVP; cards numéricos bastam.
- **Tema dark** — fora do escopo; usuário rejeitou explicitamente.
- **Material UI / shadcn completo / design system grande** — evitar nesta fase.
- **Filtro impressora free-text** — Fase 4 usa dropdown exato; autocomplete livre = futuro se necessário.
- **Dropdown de usuários** — API já suporta contains em texto; lista de usuários = otimização futura.
- **React Router / multi-página** — Fase 5 SERVER-04 (cadastro impressoras).
- **TLS / autenticação** — v2 (`REQUIREMENTS.md` Out of Scope MVP).
- **WebSocket / realtime** — fora desta fase; refresh manual ou refetch on filter.
- **Virtualização de tabela** — só se profiling justificar com `size` alto.
- **i18n completo para `media`** — mapa local simples no MVP (D-32); catálogo extensível depois.
- **Sort customizável na tabela** — API fixa em `timestamp DESC`; revisitável.
- **Rate limiting frontend** — rede local controlada; sem necessidade MVP.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DASH-01 | Dashboard acessível via browser HTTP porta 80 na rede local | nginx `ports: "80:80"`; SPA `try_files`; compose `nginx` + `depends_on: backend` (D-52–D-56) |
| DASH-02 | Cards: jobs hoje, páginas hoje, top usuário mês, top impressora | `GET /api/v1/stats/summary`; cards usam `hoje.*` e `mes.top_*[0]` (D-10–D-14) |
| DASH-03 | Tabela paginada, colunas definidas, mais recentes primeiro | `GET /api/v1/jobs`; `Page[JobOut]`; colunas D-24–D-30; `placeholderData: keepPreviousData` |
| DASH-04 | Filtros date range, usuário, impressora | URL state; presets + `type="date"`; combobox `/printers`; username text (D-15–D-23) |
| DASH-05 | Busca por nome de arquivo | param `search`; debounce 300ms (D-21, D-60) |
| DASH-06 | Carrega em < 2s com até 50k registros | Server-side pagination only; parallel Query; índices Fase 3; nginx gzip/cache (D-59–D-63) |
| EXPORT-01 | Botão CSV com filtros ativos | `GET /api/v1/export/csv`; blob download; sem page/size (D-34–D-37) |
</phase_requirements>

## Project Constraints (from .cursor/rules/)

- Trabalho de implementação deve seguir fluxo GSD (`/gsd-execute-phase`, `/gsd-quick`, etc.) — não editar fora de workflow salvo pedido explícito do usuário.
- Convenções de stack/arquitetura ainda não documentadas em `.cursor/rules/` — seguir `PROJECT.md`, `04-CONTEXT.md` e padrões do backend existente.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `react` | **^18.3.1** (pin; não usar 19.x) | UI | Decisão D-38; React 19 é latest no npm mas fora do contrato |
| `react-dom` | **^18.3.1** | DOM render | Par com React 18 |
| `vite` | **^6.3.0** (ou ^7.x se planner validar) | Build/dev server | Oficial Vite; proxy dev documentado [VERIFIED: context7 `/vitejs/vite`] |
| `@vitejs/plugin-react` | **^6.0.2** | JSX/ Fast Refresh | Par oficial React+Vite [VERIFIED: npm registry] |
| `typescript` | **^5.8.x** | Tipos | Padrão template Vite React-TS [VERIFIED: npm registry] |
| `tailwindcss` | **^4.3.0** | Estilos utilitários | Instalação oficial via `@tailwindcss/vite` [VERIFIED: context7] |
| `@tailwindcss/vite` | **^4.3.0** | Plugin Vite Tailwind v4 | Substitui PostCSS manual [VERIFIED: context7] |
| `@tanstack/react-query` | **^5.100.x** | Server state / cache | Decisão D-39; v5 `placeholderData: keepPreviousData` [VERIFIED: context7 `/tanstack/query`] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `@headlessui/react` | **^2.2.10** | Combobox impressora | D-43; filtro interno na lista [VERIFIED: context7 `/tailwindlabs/headlessui`] |
| `lucide-react` | **^1.16.0** | Ícones stroke fino | D-41 |
| `date-fns` | **^4.3.0** | `format`, `subDays`, helpers | Exibição `dd/MM/yyyy HH:mm` [VERIFIED: context7 `/date-fns/date-fns`] |
| `@date-fns/tz` | **^1.5.0** | `TZDate.tz('America/Sao_Paulo')` | Presets Hoje/7d/Mês alinhados à API [VERIFIED: context7 `/date-fns/tz`] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Headless UI Combobox | `<select>` nativo | Mais rápido, pior typeahead/a11y — só se esforço combobox bloquear |
| `URLSearchParams` nativo | `react-router` | Router proibido no MVP (D-44) |
| `@date-fns/tz` | `date-fns-tz` (marnusw) | Pacote oficial date-fns org preferido [VERIFIED: context7] |
| nginx multi-stage | Servir via FastAPI `StaticFiles` | Viola separação D-52; nginx já decidido |

**Installation:**

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install react@^18.3.1 react-dom@^18.3.1
npm install @tanstack/react-query @headlessui/react lucide-react date-fns @date-fns/tz
npm install -D tailwindcss @tailwindcss/vite
```

**Version verification (2026-05-27, `npm view`):** react 19.2.6 latest (não usar); react@18.3.1; vite 8.0.14 latest; @tanstack/react-query 5.100.14; tailwindcss 4.3.0; @headlessui/react 2.2.10; date-fns 4.3.0; @date-fns/tz 1.5.0; lucide-react 1.16.0.

## Package Legitimacy Audit

> `slopcheck install` foi executado sem flag `--json` (não suportada nesta versão). **Atenção:** slopcheck consultou **PyPI** por padrão e marcou incorretamente pacotes npm como `[SLOP]` — **não confiar nesse resultado para este ecossistema.** Legitimidade abaixo baseada em `npm view` + documentação Context7.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| react | npm | 10+ yrs | muito alto | github.com/facebook/react | PyPI false positive | Approved — pin **18.3.1** |
| react-dom | npm | 10+ yrs | muito alto | github.com/facebook/react | PyPI false positive | Approved |
| vite | npm | 5+ yrs | muito alto | github.com/vitejs/vite | PyPI false positive | Approved |
| typescript | npm | 10+ yrs | muito alto | github.com/microsoft/TypeScript | OK (PyPI unrelated) | Approved |
| tailwindcss | npm | 6+ yrs | muito alto | github.com/tailwindlabs/tailwindcss | OK (PyPI unrelated) | Approved |
| @tailwindcss/vite | npm | 1+ yr | alto | github.com/tailwindlabs/tailwindcss | PyPI false positive | Approved [VERIFIED: context7] |
| @tanstack/react-query | npm | 5+ yrs | muito alto | github.com/TanStack/query | PyPI false positive | Approved [VERIFIED: context7] |
| @headlessui/react | npm | 4+ yrs | alto | github.com/tailwindlabs/headlessui | PyPI false positive | Approved [VERIFIED: context7] |
| date-fns | npm | 8+ yrs | muito alto | github.com/date-fns/date-fns | PyPI false positive | Approved [VERIFIED: context7] |
| @date-fns/tz | npm | 1+ yr | médio | github.com/date-fns/tz | PyPI false positive | Approved [VERIFIED: context7] |
| lucide-react | npm | 3+ yrs | alto | github.com/lucide-icons/lucide | PyPI false positive | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none (veredictos PyPI inválidos para npm).

**postinstall scripts:** `npm view … scripts.postinstall` vazio para `@tanstack/react-query`, `@headlessui/react`, `lucide-react`.

## Architecture Patterns

### System Architecture Diagram

```
[Admin Browser :80]
        │
        ▼
┌───────────────────┐
│ nginx (static)    │
│  try_files → SPA  │
│  /api/* proxy     │
└─────────┬─────────┘
          │ proxy_pass http://backend:8000/api/
          ▼
┌───────────────────┐
│ FastAPI :8000     │
│ /api/v1/jobs      │
│ /api/v1/stats/... │
│ /api/v1/printers  │
│ /api/v1/export/csv│
└─────────┬─────────┘
          ▼
     [SQLite db_data]

Dev (opcional):
[Browser :5173] ──proxy /api──► [localhost:8000 ou backend container]
```

### API Contract Summary (Fase 3 — código existente)

| Endpoint | Response | Query params |
|----------|----------|--------------|
| `GET /api/v1/jobs` | `Page[JobOut]` | `page`, `size` (1–500), `username`, `printer`, `search`, `date_from`, `date_to` |
| `GET /api/v1/stats/summary` | `StatsSummaryResponse` | `top` (1–50, default 5) — UI usa default |
| `GET /api/v1/printers` | `string[]` | — |
| `GET /api/v1/export/csv` | stream CSV | mesmos filtros de jobs **sem** `page`/`size`; 400 se >100k |

Montagem de rotas: `backend/app/api/v1/__init__.py` — prefixo global `/api/v1` em `main.py`.

### Recommended Project Structure

```
frontend/
├── index.html
├── vite.config.ts
├── package.json
├── src/
│   ├── main.tsx              # QueryClientProvider
│   ├── App.tsx               # página única (sem Router)
│   ├── index.css             # @import "tailwindcss" + :root tokens (04-UI-SPEC)
│   ├── api/
│   │   ├── client.ts         # getJson, baseUrl, ApiError
│   │   ├── jobs.ts
│   │   ├── stats.ts
│   │   ├── printers.ts
│   │   └── export.ts
│   ├── hooks/
│   │   ├── useUrlFilters.ts  # URL ↔ JobFilters (sem react-router)
│   │   ├── useJobs.ts
│   │   ├── useStatsSummary.ts
│   │   └── usePrinters.ts
│   ├── components/
│   │   ├── layout/           # AppShell, Sidebar, PageHeader
│   │   ├── summary/          # SummaryCards
│   │   ├── filters/          # FilterBar, DatePresetGroup, PrinterCombobox
│   │   ├── jobs/             # JobsTable, JobsPagination
│   │   └── ui/               # Button, Input, Skeleton, ErrorBanner, EmptyState
│   ├── lib/
│   │   ├── filters.ts        # serialize/deserialize URL ↔ API params
│   │   ├── dates.ts          # presets America/Sao_Paulo
│   │   ├── format.ts         # pt-BR number, datetime display
│   │   └── media.ts          # formatMediaLabel
│   └── types/
│       └── api.ts            # espelha Pydantic schemas
nginx/
├── Dockerfile                # multi-stage: copy dist
└── default.conf
scripts/
└── validate-phase4.sh
```

### Pattern 1: Vite dev proxy (same path as produção)

**What:** Proxy `/api` para backend **sem** `rewrite` — preserva `/api/v1/...`.  
**When:** Desenvolvimento local (`npm run dev`).  
**Example:**

```typescript
// frontend/vite.config.ts
// Source: [VERIFIED: context7] https://github.com/vitejs/vite/blob/main/docs/config/server-options.md
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
        // NÃO usar rewrite — backend monta em /api/v1
      },
    },
  },
})
```

### Pattern 2: TanStack Query — jobs paginados + stats paralelos

**What:** Query keys incluem filtros serializados; paginação usa `placeholderData: keepPreviousData`.  
**When:** Tabela e cards na mesma página.

```typescript
// Source: [VERIFIED: context7] https://github.com/tanstack/query — migrating-to-v5
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

export function useStatsSummary() {
  return useQuery({
    queryKey: ['stats', 'summary'],
    queryFn: () => fetchStatsSummary(),
    staleTime: 60_000,
  })
}
```

```typescript
// main.tsx — Source: [VERIFIED: context7] /tanstack/query
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})
```

### Pattern 3: URL filters sem React Router (D-44)

**What:** `useSyncExternalStore` ou hook leve sobre `window.location.search` + `history.replaceState`.  
**When:** Qualquer mudança de filtro/preset/página.

```typescript
// lib/filters.ts — date params como yyyy-MM-dd (API JobFilters usa date)
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
```

**Debounce `search`:** manter valor local no input; só escrever `search` na URL após 300ms (`useDebouncedValue`) para não poluir histórico.

### Pattern 4: Date presets — America/Sao_Paulo

**What:** `TZDate.tz('America/Sao_Paulo')` para “hoje” e limites de mês; formatar `date_from`/`date_to` como `yyyy-MM-dd` via `format` do date-fns.  
**Align com API:** `stats_service._today_bounds_local` e `_month_bounds_local` usam a mesma timezone (`settings.api_timezone` default `America/Sao_Paulo`).

```typescript
// Source: [VERIFIED: context7] https://github.com/date-fns/tz
import { TZDate } from '@date-fns/tz'
import { format, subDays } from 'date-fns'

const TZ = 'America/Sao_Paulo'

export function presetToday(): { date_from: string; date_to: string } {
  const today = TZDate.tz(TZ)
  const s = format(today, 'yyyy-MM-dd')
  return { date_from: s, date_to: s }
}

export function presetLast7Days(): { date_from: string; date_to: string } {
  const end = TZDate.tz(TZ)
  const start = subDays(end, 6)
  return {
    date_from: format(start, 'yyyy-MM-dd'),
    date_to: format(end, 'yyyy-MM-dd'),
  }
}

export function presetMonthToDate(): { date_from: string; date_to: string } {
  const now = TZDate.tz(TZ)
  const first = new TZDate(now.getFullYear(), now.getMonth(), 1, TZ)
  return {
    date_from: format(first, 'yyyy-MM-dd'),
    date_to: format(now, 'yyyy-MM-dd'),
  }
}
```

**Exibição na tabela:** API já retorna `timestamp` ISO em SP (`JobOut` serializer). Usar `format(parseISO(row.timestamp), 'dd/MM/yyyy HH:mm')` — não reconverter timezone.

### Pattern 5: Headless UI Printer Combobox

**What:** Lista de `GET /printers`; filtro client-side; valor enviado como match exato.  
**Example:** ver seção Code Examples.

### Pattern 6: nginx + Docker Compose (DASH-01)

**What:** Imagem nginx com `dist/` do build Vite; proxy API; gzip + cache assets hashed.

**`nginx/default.conf`:**

```nginx
# SPA + API proxy — try_files pattern [CITED: https://nginx.org/en/docs/http/ngx_http_core_module.html]
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    gzip on;
    gzip_types text/css application/javascript application/json;

    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
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

**`nginx/Dockerfile` (multi-stage):**

```dockerfile
# Stage 1 — build
FROM node:22-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2 — serve
FROM nginx:1.27-alpine
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
```

**`docker-compose.yml` additions:**

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

  # backend: SEM ports: no host (rede interna apenas) — D-56
```

**Nota:** Remover exposição `8000:8000` do backend no host se existir após Fase 3 — dashboard e validação E2E devem usar `http://localhost` (nginx), não `:8000`.

### Anti-Patterns to Avoid

- **Client-side filter em 50k rows:** viola D-59/DASH-06.
- **React Router para “rotas” internas:** D-44 proíbe até Fase 5.
- **Recalcular tops no browser:** viola D-13.
- **proxy_pass sem trailing slash consistente:** `location /api/` + `proxy_pass http://backend:8000/api/` preserva path [CITED: https://nginx.org/en/docs/http/ngx_http_proxy_module.html].
- **rewrite no Vite proxy removendo `/api`:** quebra prefixo `/api/v1`.
- **Material UI / shadcn completo:** viola D-38, D-64, UI-SPEC.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Server state cache | Custom fetch + useState global | TanStack Query v5 | Invalidação, dedupe, loading/error, paginação |
| Combobox acessível | `<div>` + key handlers ad hoc | `@headlessui/react` Combobox | WAI-ARIA, focus trap, keyboard |
| Date presets em SP | `new Date()` local do browser | `@date-fns/tz` `TZDate.tz` | DST e “hoje” divergem do backend |
| CSV download | Form POST custom | `fetch` + `blob()` + `<a download>` | API já stream + Content-Disposition |
| Debounce | setTimeout espalhado | um hook `useDebouncedValue` | D-60 testável |
| Paginação UI state só em React | state local sem URL | URL + Query | Share link, debug (D-23) |
| Reverse proxy | Caddy/Traefik nesta fase | nginx | Decisão D-52; já no PROJECT.md |

## Common Pitfalls

### Pitfall 1: CORS em produção vs dev

**What goes wrong:** Dashboard em `:80` same-origin não precisa CORS; dev em `:5173` precisa `ALLOWED_ORIGINS` com `http://localhost:5173` (Fase 3 D-27).  
**How to avoid:** Testar dev com proxy Vite; validar preflight no `validate-phase4.sh` espelhando check 14–15 da fase 3.

### Pitfall 2: Mês atual preset ≠ API “mês” nos cards

**What goes wrong:** Preset “Mês atual” no filtro da tabela vai até **hoje**; bucket `stats.mes` na API é **mês calendário completo** (1º → último dia).  
**Why:** `presetMonthToDate` (D-16) vs `stats_service._month_bounds_local` (mês fechado).  
**How to avoid:** Documentar na UI; cards sempre de `/stats/summary`, não derivados dos filtros da tabela.

### Pitfall 3: Export inclui page/size

**What goes wrong:** CSV truncado ou 400 inesperado.  
**How to avoid:** `export.ts` monta params só de filtros (D-35).

### Pitfall 4: Timestamp double timezone shift

**What goes wrong:** Converter ISO da API (já SP) como UTC e formatar de novo.  
**How to avoid:** `parseISO` + `format` sem `utcToZonedTime` extra.

### Pitfall 5: nginx serve API 404 para rotas SPA

**What goes wrong:** Refresh em path futuro quebra.  
**How to avoid:** MVP é página única `/`; `try_files` fallback `index.html` apenas em `location /`, não em `/api/`.

### Pitfall 6: React 19 por default do `create vite`

**What goes wrong:** Incompatibilidade com decisão D-38.  
**How to avoid:** Pin explícito `react@^18.3.1` após scaffold.

## Code Examples

### API client

```typescript
// frontend/src/api/client.ts
const baseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

export async function getJson<T>(path: string, params?: URLSearchParams): Promise<T> {
  const qs = params?.toString()
  const url = `${baseUrl}${path}${qs ? `?${qs}` : ''}`
  const res = await fetch(url, { headers: { Accept: 'application/json' } })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new ApiError(res.status, detail?.detail ?? res.statusText)
  }
  return res.json() as Promise<T>
}
```

### Export CSV blob

```typescript
// frontend/src/api/export.ts
export async function downloadCsv(filters: ExportFilters): Promise<void> {
  const params = filtersToSearchParams(filters) // sem page/size
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

### Headless UI Combobox (impressora)

```tsx
// Source: [VERIFIED: context7] /tailwindlabs/headlessui
import {
  Combobox,
  ComboboxButton,
  ComboboxInput,
  ComboboxOption,
  ComboboxOptions,
} from '@headlessui/react'
import { useState } from 'react'

export function PrinterCombobox({
  printers,
  value,
  onChange,
}: {
  printers: string[]
  value: string | null
  onChange: (v: string | null) => void
}) {
  const [query, setQuery] = useState('')
  const filtered =
    query === ''
      ? printers
      : printers.filter((p) => p.toLowerCase().includes(query.toLowerCase()))

  return (
    <Combobox value={value} onChange={onChange} onClose={() => setQuery('')}>
      <div className="relative">
        <ComboboxInput
          className="w-full rounded-lg border px-3 py-2"
          displayValue={(p: string | null) => p ?? ''}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Selecionar impressora…"
        />
        <ComboboxButton className="absolute inset-y-0 right-2">▼</ComboboxButton>
        <ComboboxOptions className="mt-1 max-h-60 overflow-auto rounded-lg border bg-white shadow">
          {filtered.map((p) => (
            <ComboboxOption key={p} value={p} className="cursor-pointer px-3 py-2 data-[focus]:bg-[var(--row-hover)]">
              {p}
            </ComboboxOption>
          ))}
        </ComboboxOptions>
      </div>
    </Combobox>
  )
}
```

### Tailwind v4 + tokens (04-UI-SPEC)

```css
/* frontend/src/index.css — Source: [VERIFIED: context7] tailwindcss.com/installation/using-vite */
@import "tailwindcss";

:root {
  --bg-canvas: #F5F5F7;
  --bg-surface: #FFFFFF;
  --text-primary: #1D1D1F;
  --accent: #00AE5B;
  /* … demais tokens em 04-UI-SPEC.md */
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `keepPreviousData: true` (RQ v4) | `placeholderData: keepPreviousData` (RQ v5) | TanStack Query v5 | Paginação sem flash [VERIFIED: context7] |
| Tailwind PostCSS pipeline | `@tailwindcss/vite` plugin | Tailwind v4 | Menos config [VERIFIED: context7] |
| `date-fns-tz` third-party | `@date-fns/tz` official | 2024+ | Preferir pacote date-fns org |
| Backend exposto :8000 | nginx :80 only | Fase 4 D-56 | CORS simplificado em prod |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Pin Vite 6.x em vez de 8.x latest | Standard Stack | Breaking changes Vite 8 — planner deve smoke-test `npm run build` |
| A2 | Backend **não** expõe porta 8000 no host após Fase 4 | nginx pattern | Quebra workflows que usam `localhost:8000` direto |
| A3 | `VITE_API_BASE_URL` vazio → `/api/v1` relativo | API client | Dev sem proxy precisa env explícita |
| A4 | Vitest para Wave 0 tests | Validation | Planner escolhe runner se diferente |

## Open Questions (RESOLVED)

1. **Backend `ports: 8000` no compose hoje?** — **RESOLVED**
   - **Decisão:** Remover `ports: 8000:8000` do serviço `backend` ao adicionar nginx (D-56). API acessível via `http://localhost/api/v1/*` (nginx) ou `docker compose exec backend curl http://127.0.0.1:8000/api/v1/health` para debug direto.
   - **Rationale:** Única porta pública do dashboard é :80; evita expor API sem proxy em produção.

2. **Inter vs system font** — **RESOLVED**
   - **Decisão:** System font stack per D-05 / UI-SPEC (`system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`). Inter **não** adicionar no MVP.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js + npm | Vite build/dev | ✓ (assumido dev) | 20+ LTS | Docker build stage only on VM |
| Docker Compose | DASH-01 prod | ✓ (Fases 1–3) | — | — |
| nginx image | Serve SPA | ✓ via Docker Hub | 1.27-alpine | — |
| Backend API | All data | ✓ implementado | 0.3.0 | Bloqueia fase |
| `ALLOWED_ORIGINS` | Dev CORS | ⚠️ `.env.example` sem var ainda | — | Planner adiciona em Fase 4 |

**Missing dependencies with no fallback:**
- Dados no SQLite para validar cards/filtros (precisa jobs de teste ou checkpoint humano).

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | **Vitest** ^3.x + **@testing-library/react** (Wave 0 — não existe ainda) |
| Config file | `frontend/vitest.config.ts` (criar) |
| Quick run command | `cd frontend && npm test -- --run` |
| Full suite command | `bash scripts/validate-phase4.sh --quick` + `npm test` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DASH-01 | HTTP :80 serve index + proxy API | integration | `curl -sf http://localhost/` ; `curl -sf http://localhost/api/v1/health` | ❌ Wave 0 `validate-phase4.sh` |
| DASH-02 | Cards batem com API | integration | `curl -sf http://localhost/api/v1/stats/summary \| jq .hoje.jobs` | ❌ Wave 0 |
| DASH-03 | Tabela paginada | unit + integration | Vitest `filtersToSearchParams`; curl `/api/v1/jobs?page=1&size=50` | ❌ Wave 0 |
| DASH-04 | Filtros na URL | unit | Vitest round-trip URL ↔ filters | ❌ Wave 0 |
| DASH-05 | Debounce search | unit | Vitest debounce hook (fake timers) | ❌ Wave 0 |
| DASH-06 | Performance | manual + script | checkpoint humano <2s; curl -w `%{time_total}` jobs | ❌ checkpoint |
| EXPORT-01 | CSV download | integration | curl `-D -` export com filtros; header `attachment` | ❌ Wave 0 (espelhar validate-phase3 checks 08–10) |

### Sampling Rate

- **Per task commit:** `cd frontend && npm test -- --run` (quando existir)
- **Per wave merge:** `bash scripts/validate-phase4.sh --quick`
- **Phase gate:** validate full + checkpoint humano ROADMAP critérios 1–5

### Wave 0 Gaps

- [ ] `frontend/` scaffold Vite React-TS + Tailwind v4
- [ ] `frontend/vitest.config.ts` + testes `lib/filters.ts`, `lib/dates.ts`, `lib/media.ts`
- [ ] `scripts/validate-phase4.sh` — checks: nginx up, `/` 200, `/api/v1/health`, jobs shape, stats shape, export headers, CORS dev (opcional), gzip header em `.js`
- [ ] `nginx/Dockerfile` + `default.conf`
- [ ] `docker-compose.yml` serviço `nginx`
- [ ] `.env.example`: `ALLOWED_ORIGINS`, `VITE_API_BASE_URL` (opcional)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | MVP sem login |
| V3 Session Management | no | — |
| V4 Access Control | partial | Rede local REDACTED_IP/16; sem auth app |
| V5 Input Validation | yes | API Pydantic `JobFilters` extra=forbid; frontend valida formato date/url params |
| V6 Cryptography | no | Sem TLS nesta fase (D-55) |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| XSS em `job_name` / `username` | Spoofing/Tampering | React escape default; não `dangerouslySetInnerHTML` |
| CSV injection no Excel | Tampering | Dados do backend; documentar em Fase 5 se necessário |
| Exposição API sem auth | Information disclosure | Firewall rede; não port-forward internet (PROJECT.md) |
| CORS overly permissive | Tampering | Sem `*`; GET only (backend já configurado) |

## Sources

### Primary (HIGH confidence)

- [VERIFIED: context7] `/vitejs/vite` — build, `server.proxy`, static deploy
- [VERIFIED: context7] `/tanstack/query` — v5 `placeholderData: keepPreviousData`, `QueryClientProvider`
- [VERIFIED: context7] `/websites/tailwindcss_installation_using-vite` — Tailwind v4 + Vite plugin
- [VERIFIED: context7] `/tailwindlabs/headlessui` — Combobox React
- [VERIFIED: context7] `/date-fns/tz` — `TZDate.tz`, America/Sao_Paulo presets
- [VERIFIED: context7] `/date-fns/date-fns` — `format`, `parseISO`
- [CITED: https://nginx.org/en/docs/http/ngx_http_core_module.html] — `try_files`
- [CITED: https://nginx.org/en/docs/http/ngx_http_proxy_module.html] — `proxy_pass` URI replacement
- Código repo: `backend/app/schemas/*.py`, `backend/app/api/v1/*.py`, `docker-compose.yml`

### Secondary (MEDIUM confidence)

- `04-UI-SPEC.md` — tokens, copy, component inventory
- `scripts/validate-phase3.sh` — template Nyquist para phase 4
- `.planning/phases/03-backend-api/03-CONTEXT.md` — contratos API

### Tertiary (LOW confidence)

- Versão exata Vite 6 vs 8 para este repo — validar no primeiro `npm run build` (A1)

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — Context7 + npm view + decisões CONTEXT
- Architecture: **HIGH** — API implementada; padrões nginx documentados oficialmente
- Pitfalls: **HIGH** — derivados de decisões explícitas e código `stats_service` / serializers
- Docker/nginx: **MEDIUM** — padrão industry-standard; sem arquivo nginx pré-existente no repo

**Research date:** 2026-05-27  
**Valid until:** 2026-06-26 (stack estável); rever TanStack/Vite minors em 7 dias se planner usar latest tags
