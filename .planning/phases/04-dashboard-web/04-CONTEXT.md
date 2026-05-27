# Phase 4: Dashboard Web - Context

**Gathered:** 2026-05-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Interface React completa e usável para o admin de TI visualizar histórico de impressão agregado por job, filtrar (período, usuário, impressora, arquivo), consultar sumários e exportar CSV — acessível via browser na rede local (`http://<VM_HOST>` na porta 80).

**Cadeia alvo desta fase:** `Browser :80 → nginx (SPA estático + proxy /api/v1) → FastAPI (Fase 3) → SQLite`

**Requisitos do roadmap:** DASH-01, DASH-02, DASH-03, DASH-04, DASH-05; herança EXPORT-01 (botão export com filtros ativos); DASH-06 (carregamento < 2s com até 50k registros — via paginação server-side + índices Fase 3).

**Não inclui:** autenticação/login, TLS/HTTPS, WebSocket/realtime, SSR, gráficos/charts complexos, design system gigante, microfrontends, state management global (Redux/Zustand), Material UI / Ant Design / Bootstrap, tema dark/cyberpunk, i18n completo, filtro impressora free-text, TLS, reverse proxy avançado, UI de cadastro de impressoras (SERVER-04 → Fase 5), polling CUPS online/offline.

</domain>

<decisions>
## Implementation Decisions

### A. Direção visual — Apple HIG + PaperCut

- **D-01:** Estética **Apple-like**: clean, minimalista, branco predominante, hierarquia tipográfica forte, muito espaço em branco, sensação **calma** (evitar visual NOC/SOC, admin template genérico, dashboards poluídos).
- **D-02:** Verde de acento inspirado no PaperCut: primário **`#00AE5B`**, hover **`#009952`**, tint de fundo **`#E8F7EF`**. Usar verde apenas para ações primárias, estados ativos e foco — não como fundo dominante.
- **D-03:** Fundos: canvas **`#F5F5F7`** (cinza Apple), superfícies (cards, barra de filtros) **`#FFFFFF`**. Texto primário **`#1D1D1F`**, secundário **`#6E6E73`**, bordas **`#D2D2D7`**.
- **D-04:** Cards de sumário **discretos**: borda `1px`, radius ~12px, sombra mínima (`0 1px 2px` no máximo) — **sem** gradientes, **sem** sombras pesadas, **sem** widgets decorativos.
- **D-05:** Tipografia: stack de sistema `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` (Inter opcional se o planner preferir consistência cross-OS). Escala clara: título de página, labels de filtro, corpo de tabela, meta.
- **D-06:** Espaçamento alinhado ao HIG: escala Tailwind baseada em **16px** como unidade confortável (4/8/12/16/20/24/32); margens generosas; controles agrupados logicamente (sumário → filtros → tabela).
- **D-07:** Motion: animações **mínimas** (150–200ms); respeitar `prefers-reduced-motion`; sem parallax; feedback de hover/focus discreto.
- **D-08:** Acessibilidade: contraste adequado (texto primário em fundo claro); estados não dependem só de cor; focus ring visível (verde com offset); suporte a navegação por teclado nos controles principais.
- **D-09:** Referência de design obrigatória para planner/UI: [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/) — layout, listas/tabelas, search fields, loading, cor, tipografia, empty states (consultado via context7 na discussão).

### B. Cards de sumário (DASH-02)

- **D-10:** Quatro cards na página principal:
  1. **Jobs hoje** — `stats.hoje.jobs`
  2. **Páginas hoje** — `stats.hoje.pages`
  3. **Top usuário do mês** — `stats.mes.top_users[0]`
  4. **Top impressora do mês** — `stats.mes.top_printers[0]`
- **D-11:** Motivo da escolha **mês** para tops (não “top do dia”): mais útil gerencialmente, menos volatilidade visual, alinha com `REQUIREMENTS.md` DASH-02 (“top usuário do mês”).
- **D-12:** Cards de top exibem **nome + total de páginas** no mesmo bloco, formato: `"Maria Silva — 1.284 páginas"` (número formatado pt-BR com separador de milhar). Se `top_users` ou `top_printers` vazio: empty state do card (“Sem dados no período”).
- **D-13:** Fonte de dados: **única** chamada `GET /api/v1/stats/summary` (sem recalcular tops no cliente). Cache TanStack Query com `staleTime` ~30–60s.
- **D-14:** **Sem gráficos/charts** nesta fase — cards numéricos/textuais apenas.

### C. Filtros e presets de data (DASH-04, DASH-05)

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

### D. Tabela de jobs (DASH-03)

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

### E. Coluna Papel — normalização leve

- **D-31:** MVP exibe valor derivado de `media` com **helper local simples** (`formatMediaLabel(raw)`), mapa estático, **fallback = valor bruto** se não reconhecido.
- **D-32:** Mapeamentos iniciais (extensível sem i18n):

  | Valor CUPS/API (exemplo) | Rótulo UI |
  |--------------------------|-----------|
  | `iso_a4_210x297mm` | A4 |
  | `na_letter_8.5x11in` | Carta |
  | (outros) | valor bruto |

- **D-33:** Sem camada de i18n; sem serviço de tradução; mapa em `frontend/src/lib/media.ts` (ou equivalente).

### F. Export CSV (EXPORT-01)

- **D-34:** Botão **Exportar CSV** claramente visível no header da página principal (ação secundária outline ou equivalente discreto).
- **D-35:** Export usa **mesmos query params de filtro** da tabela (`username`, `printer`, `search`, `date_from`, `date_to`) — **sem** `page`/`size`.
- **D-36:** Implementação: `GET /api/v1/export/csv` → download via `blob` + `<a download>` ou navegação controlada; exibir loading no botão durante download.
- **D-37:** Erro **400** (cap 100k linhas): exibir mensagem do backend e sugerir estreitar período/filtros (não falhar silenciosamente).

### G. Stack e arquitetura frontend

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

### H. Layout e UX

- **D-46:** **Desktop-first**; mobile apenas funcional (sidebar colapsável, tabela com scroll horizontal, filtros empilhados) — não é critério de aceite principal.
- **D-47:** Shell: **sidebar estreita** (~220px) com branding PrintWatch + item **Jobs** (único no MVP); área principal com título, export, cards, filtros, tabela, paginação.
- **D-48:** **Tabela é o centro do produto** — maior área visual; cards secundários.
- **D-49:** Loading: **skeleton elegante** nos 4 cards + ~8 linhas da tabela no carregamento inicial; refetch de filtros com opacidade reduzida na tabela + indicador fino indeterminado (estilo HIG).
- **D-50:** Empty state (zero jobs): mensagem clara + CTA “Limpar filtros”. Empty com filtros ativos: mensagem específica (“Ajuste o período ou a impressora”).
- **D-51:** Erro API: banner discreto com “Tentar novamente” (refetch Query).

### I. Deploy — nginx + Docker Compose (DASH-01)

- **D-52:** **nginx nesta fase** — servido em **porta 80** no host; acesso alvo `http://<VM_HOST>` (sem `:5173` em produção).
- **D-53:** Estratégia: **Vite build estático** (`frontend/dist`) copiado para imagem nginx; `try_files` SPA fallback para `index.html`.
- **D-54:** nginx **proxy** `location /api/` → `http://backend:8000/api/` (preservar prefixo `/api/v1`).
- **D-55:** **Sem TLS** nesta fase; **sem** autenticação; **sem** reverse proxy complexo (rate limit, mTLS, etc.).
- **D-56:** `docker-compose.yml`: adicionar serviços `frontend` (build stage ou artefato) + `nginx` (`depends_on: backend`); **única porta pública do dashboard: 80** (backend pode permanecer sem `ports:` no host — apenas rede interna Docker).
- **D-57:** Dev local: Vite `server.proxy` `/api` → `http://localhost:8000` para DX; produção usa same-origin (CORS irrelevante no browser para dashboard em :80).
- **D-58:** Atualizar `.env.example` com variáveis Fase 4 se necessário (`VITE_*` mínimo); `ALLOWED_ORIGINS` pode incluir `http://VM_HOST` (já previsto Fase 3).

### J. Performance (DASH-06)

- **D-59:** Paginação server-side **obrigatória** — nunca client-side filter sobre dataset completo.
- **D-60:** Debounce **300ms** em `search` (arquivo).
- **D-61:** Evitar virtualização no MVP salvo profiling com `size=500` mostrar lag — default `size=50`.
- **D-62:** Meta de experiência: shell + skeleton < ~500ms; dados cards + tabela em paralelo (`stats` + `jobs`); TTFB API < 500ms (dependência Fase 3 / índices).
- **D-63:** Build produção: gzip nginx para estáticos; cache immutable para assets hashed do Vite.

### K. Diretrizes transversais para o planner

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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos e roadmap
- `.planning/PROJECT.md` — Stack React+Vite+Tailwind, perfis de usuário, Out of Scope (sem auth)
- `.planning/REQUIREMENTS.md` — DASH-01..06, EXPORT-01; critérios de aceite globais
- `.planning/ROADMAP.md` — Fase 4 goal, requirements, success criteria (5 critérios)
- `.planning/STATE.md` — Status do projeto e decisões acumuladas

### Contexto Fase 3 (contrato API — MANDATORY)
- `.planning/phases/03-backend-api/03-CONTEXT.md` — D-01..D-34: agregação por job, filtros, paginação, stats, CSV, CORS, timezone
- `.planning/phases/03-backend-api/03-RESEARCH.md` — Padrões FastAPI, compose, CORS, export streaming

### Design e UX (discussão Fase 4)
- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/) — layout, spacing, tabelas, search, loading, cor, acessibilidade (referência primária visual/UX)
- PaperCut branding docs — verde `#00ae5b` em [Customize Login page](https://www.papercut.com/help/manuals/ng-mf/common/customize-login-page/) (acento, não layout)

### Código backend a consumir
- `backend/app/api/v1/jobs.py` — `GET /api/v1/jobs`, `GET /api/v1/jobs/{id}`
- `backend/app/api/v1/stats.py` — `GET /api/v1/stats/summary`
- `backend/app/api/v1/printers.py` — `GET /api/v1/printers`
- `backend/app/api/v1/export.py` — `GET /api/v1/export/csv`
- `backend/app/schemas/jobs.py` — `JobOut`, `JobFilters`, `Page`
- `backend/app/schemas/stats.py` — `StatsSummaryResponse`, `StatsBucket`, `TopEntry`
- `backend/app/core/config.py` — `ALLOWED_ORIGINS`, `api_timezone`
- `docker-compose.yml` — expandir com `frontend` + `nginx` (comentário Fase 4 existente)

### Infra e deploy
- `.planning/phases/02-log-pipeline-data-layer/02-PATTERNS.md` — Padrões Docker/nginx/envsubst aplicáveis
- `.env.example` — estender para Fase 4 conforme planner

### Validação
- `scripts/validate-phase3.sh` — Modelo para `scripts/validate-phase4.sh`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **API Fase 3 implementada** em `backend/app/api/v1/` — jobs, stats, export, printers, health; frontend consome diretamente via proxy nginx.
- **`JobFilters`** — query params padronizados (`page`, `size`, `username`, `printer`, `search`, `date_from`, `date_to`); espelhar em `frontend/src/lib/filters.ts` ↔ URL.
- **`StatsSummaryResponse`** — buckets `hoje`, `mes`, `total` com `top_users`/`top_printers` por `SUM(pages)`; cards usam `hoje.*` e `mes.top_*[0]`.
- **`Page[T]`** em `backend/app/schemas/common.py` — `{ items, total, page, size }` para paginação.
- **CSV export** — UTF-8 BOM, `;`, cabeçalhos pt-BR, cap 100k (D-11..D-18 Fase 3); frontend só dispara download.

### Established Patterns
- Decisões numeradas **D-NN por fase** (Fase 4: D-01..D-67).
- Validação Nyquist via `validate-phaseN.sh`.
- Timezone **America/Sao_Paulo** na borda HTTP; banco UTC (Fase 3 D-10/D-20).
- Prefixo **`/api/v1/*`** versionado.
- `docker-compose.yml` com comentário preparado para frontend/nginx Fase 4.

### Integration Points
- **nginx :80** — único ponto de entrada do dashboard na rede local (DASH-01).
- **Backend** — rede Docker interna; nginx proxy `/api/` → `backend:8000`; CORS necessário principalmente para **dev Vite** (`localhost:5173`).
- **Sem WebSocket** — refetch manual ou automático via Query ao mudar filtros; sem polling de stats no MVP.
- **Fase 5** — SERVER-04 adicionará tela/rota de impressoras; manter shell extensível.

</code_context>

<specifics>
## Specific Ideas

- Visual: **Apple (espaço, hierarquia, feedback discreto) + PaperCut (verde funcional, confiança enterprise)**.
- Cards top: **"Nome — N páginas"** com formatação pt-BR (ex. 1.284).
- Presets de data com sensação **analytics** (Apple/PaperCut) — troca instantânea, sem modal.
- Tabela: referência **Apple Settings + PaperCut admin** — semi-compact ~40px, não ERP espaçado.
- Tom geral: produto **premium calmo**, não war room.
- Busca por arquivo **sempre acessível** na barra de filtros.
- Export CSV **sempre visível** no header.

</specifics>

<deferred>
## Deferred Ideas

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

</deferred>

---

*Phase: 4-Dashboard Web*
*Context gathered: 2026-05-27*
