---
phase: 4
slug: dashboard-web
status: approved
shadcn_initialized: false
preset: none
created: 2026-05-27
approved: 2026-05-27
---

# Phase 4 — UI Design Contract

> Contrato visual e de interação para o Dashboard Web PrintWatch.  
> Fontes: `04-CONTEXT.md` (D-01..D-67), Apple HIG, acento PaperCut `#00AE5B`.  
> Gerado por `/gsd-ui-phase 4` — verificado contra 6 dimensões.

---

## Design System

| Property | Value |
|----------|-------|
| Tool | **none** (sem shadcn — decisão explícita D-64) |
| Preset | not applicable |
| Component library | Primitivos locais em `frontend/src/components/ui/` + **@headlessui/react** apenas para combobox de impressora |
| Styling | **Tailwind CSS** + CSS variables em `:root` |
| Icon library | **lucide-react** (stroke 1.5–2, tamanho 16–20px) |
| Font | `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` |

**Proibido nesta fase:** MUI, Ant Design, Bootstrap, shadcn/ui completo, tema dark, gradientes decorativos, sombras pesadas, charts.

---

## Visual Hierarchy & Focal Point

| Priority | Element | Treatment |
|----------|---------|-------------|
| 1 (focal) | **Tabela de jobs** | Maior área útil; sticky header; corpo 14px; ocupa ~55–65% da viewport em desktop |
| 2 | Barra de filtros + presets | Segunda faixa de atenção; fundo branco; presets como segmented control |
| 3 | Cards de sumário | Discretos; uma linha; não competem com a tabela |
| 4 | Sidebar + header | Navegação estável; baixo contraste visual |
| 5 | Exportar CSV | Visível no header; estilo secundário (outline) |

**Tom geral:** calmo, enterprise premium, muito whitespace — **não** NOC/SOC/war room.

---

## Layout Contract

### Shell (desktop ≥1024px)

```
┌ Sidebar 220px ─┬─ Main (flex-1, max-w ~1400px, mx-auto) ─────────────┐
│ Logo PrintWatch │ PageHeader: título + Exportar CSV                  │
│ Nav: Jobs ●     │ SummaryCards (4 col grid)                        │
│                 │ FilterBar: presets | dates | user | printer | search│
│                 │ JobsTable (flex-1 min-h)                           │
│                 │ JobsPagination                                   │
└─────────────────┴──────────────────────────────────────────────────┘
```

| Token | Value |
|-------|-------|
| Sidebar width | `220px` |
| Main padding | `24px` (lg) horizontal; `20px` vertical abaixo do header |
| Section gap (cards → filters → table) | `24px` |
| Card grid | `grid-cols-4` gap `16px` (≥1280px); `grid-cols-2` (1024–1279) |
| Page background | `--bg-canvas` `#F5F5F7` |
| Surface background | `--bg-surface` `#FFFFFF` |

### Breakpoints

| Breakpoint | Behavior |
|------------|----------|
| ≥1280px | Layout completo; 4 cards em linha |
| 1024–1279px | Cards 2×2; tabela full width |
| <1024px | Sidebar colapsável (ícone/hamburger); filtros empilhados; tabela `overflow-x-auto` |

---

## Spacing Scale

Valores declarados (múltiplos de 4):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Gap ícone+texto inline |
| sm | 8px | Padding interno compacto (pills, badges) |
| md | 16px | Padding de card; gap entre campos de filtro |
| lg | 24px | Padding de seção; gap entre blocos principais |
| xl | 32px | Margem inferior de page header |
| 2xl | 48px | Reservado — separação maior se necessário |

**Exceções justificadas:**

| Value | Usage |
|-------|-------|
| 12px | Padding horizontal de preset pills |
| 20px | Padding interno de cards de sumário |
| 40px | Altura mínima de linha da tabela (semi-compact) |
| 44px | Altura mínima de alvos de toque em mobile (acessibilidade) |

---

## Typography

**Máximo 4 tamanhos, 2 pesos** (400 regular, 600 semibold).

| Role | Size | Weight | Line Height | Usage |
|------|------|--------|-------------|-------|
| Display | 24px | 600 | 1.2 | Título da página: "Histórico de impressão" |
| Heading | 17px | 600 | 1.25 | Labels de seção; cabeçalhos de coluna da tabela |
| Body | 14px | 400 | 1.5 | Células da tabela; valores dos cards; inputs |
| Label | 12px | 400 | 1.4 | Labels de filtro; meta ("Mostrando 1–50 de 12.345"); subtítulo dos cards |

**Card de sumário:**

| Part | Style |
|------|-------|
| Título do card | Label 12px, cor `--text-secondary`, uppercase opcional ou sentence case |
| Valor principal | Body 14px semibold (600) para números; Display 24px apenas se valor numérico isolado (jobs/páginas hoje) |
| Top nome + páginas | Body 14px regular, uma linha: `"Maria Silva — 1.284 páginas"` |

---

## Color

### 60 / 30 / 10

| Role | Hex | % | Usage |
|------|-----|---|-------|
| Dominant | `#F5F5F7` | 60% | Canvas da página, fundo atrás do conteúdo |
| Secondary | `#FFFFFF` | 30% | Sidebar, cards, filter bar, superfície da tabela |
| Accent | `#00AE5B` | 10% | Ver elementos abaixo — **nunca** fundo dominante |

### Semantic tokens (CSS variables)

```css
:root {
  --bg-canvas: #F5F5F7;
  --bg-surface: #FFFFFF;
  --text-primary: #1D1D1F;
  --text-secondary: #6E6E73;
  --text-tertiary: #AEAEB2;
  --border: #D2D2D7;
  --border-subtle: #E8E8ED;
  --accent: #00AE5B;
  --accent-hover: #009952;
  --accent-tint: #E8F7EF;
  --row-hover: #F9F9FB;
  --row-stripe: #FAFAFC;
  --destructive: #FF3B30;
  --focus-ring: #00AE5B;
}
```

### Accent reservado para (lista fechada)

- Item **ativo** na sidebar (`Jobs`)
- Preset de data **selecionado** (pill/segmented)
- **Focus ring** de inputs e combobox (outline 2px + offset 2px)
- Indicador de loading fino no topo da tabela (opcional, 2px height)

**NÃO usar accent em:** fundo de cards, linhas inteiras da tabela, todos os botões, ícones decorativos, bordas padrão.

### Destructive

| Element | Color | When |
|---------|-------|------|
| Banner de erro API | `#FF3B30` texto/ícone em fundo `#FFF5F5` ou borda destructive | Falha de fetch |
| Nenhuma ação destrutiva no MVP | — | Sem delete/block nesta fase |

---

## Component Inventory

| Component | Variant / spec | Notes |
|-----------|----------------|-------|
| `AppShell` | Sidebar 220px + main | Logo texto "PrintWatch" 17px semibold |
| `SidebarNavItem` | default / active | Active: `--accent-tint` bg + `--accent` text |
| `PageHeader` | title + actions slot | Export à direita |
| `SummaryCard` | metric / top | Border 1px `--border`; radius 12px; shadow `0 1px 2px rgba(0,0,0,0.04)` |
| `DatePresetGroup` | segmented pills | Hoje \| 7 dias \| Mês atual |
| `DateRangeInputs` | two `type="date"` | Labels "De" / "Até" |
| `FilterInput` | text | Usuário, Arquivo (search) |
| `PrinterCombobox` | Headless UI | Lista `/printers`; busca interna; clearable |
| `Button` | primary / secondary / ghost | Ver abaixo |
| `JobsTable` | sticky header, zebra | Row min-height 40px |
| `JobsPagination` | prev/next + page numbers | Meta label 12px |
| `Skeleton` | card / row | Pulse suave; `prefers-reduced-motion: reduce` → sem pulse |
| `EmptyState` | table / card | Ícone lucide neutro 48px, copy abaixo |
| `ErrorBanner` | inline | Dismiss opcional; botão "Tentar novamente" |

### Button variants

| Variant | Style | Usage |
|---------|-------|-------|
| **secondary** (outline) | Border `--border`; text `--text-primary`; hover `--row-hover` | **Exportar CSV** |
| **ghost** | Sem border; text `--text-secondary` | Limpar filtros |
| **primary** (filled accent) | Bg `--accent`; text white | Reservado — **não usar** no MVP salvo CTA futuro |

---

## Interaction & Motion

| Interaction | Behavior | Duration |
|-------------|----------|----------|
| Preset date click | Atualiza URL; refetch imediato | 0ms perceived (loading na tabela) |
| Search input | Debounce **300ms** | — |
| Filter change | Opacity tabela `0.6` + barra 2px indeterminada no topo | 150ms fade |
| Row hover | Background `--row-hover` | 150ms |
| Card/table skeleton | Pulse opacity | 1.5s; disabled se `reduce-motion` |
| Page change | Scroll to top of table (opcional) | instant |

---

## States Contract

### Loading

| Context | UI |
|---------|-----|
| Initial page | 4 card skeletons (retângulos 20px + 32px) + 8 row skeletons |
| Filter refetch | Tabela semi-transparente + thin progress bar |
| Export | Botão disabled + spinner 16px + label "Exportando…" |
| Stats cards | Skeleton apenas no primeiro load; stale data OK em refetch |

### Empty

| Context | Heading | Body | CTA |
|---------|---------|------|-----|
| Tabela sem jobs (sem filtros) | Nenhum job registrado ainda | Os jobs aparecerão aqui após a primeira impressão. | — |
| Tabela sem resultados (com filtros) | Nenhum job encontrado | Ajuste o período, usuário ou impressora e tente novamente. | **Limpar filtros** (ghost) |
| Card top vazio | Sem dados no período | — | — |

### Error

| Context | Copy |
|---------|------|
| API jobs/stats fail | **Não foi possível carregar os dados.** Verifique se o servidor está online e tente novamente. → **Tentar novamente** |
| Export 400 (>100k) | Usar `detail` do backend + sufixo: "Reduza o período ou adicione filtros." |
| Export network fail | **Falha ao exportar.** Verifique a conexão e tente novamente. |

---

## Copywriting Contract

| Element | Copy (pt-BR) |
|---------|----------------|
| Page title | Histórico de impressão |
| Primary action (header) | **Exportar CSV** |
| Secondary action | **Limpar filtros** |
| Preset: Hoje | Hoje |
| Preset: 7 days | Últimos 7 dias |
| Preset: month | Mês atual |
| Filter label: De / Até | De / Até |
| Filter label: user | Usuário |
| Filter label: printer | Impressora |
| Filter label: search | Arquivo |
| Placeholder: user | Filtrar por usuário… |
| Placeholder: search | Buscar por nome do arquivo… |
| Placeholder: printer | Selecionar impressora… |
| Pagination meta | Mostrando {from}–{to} de {total} jobs |
| Card: jobs today | Jobs hoje |
| Card: pages today | Páginas hoje |
| Card: top user | Top usuário do mês |
| Card: top printer | Top impressora do mês |
| Empty table (filtered) | Nenhum job encontrado |
| Empty table body (filtered) | Ajuste o período, usuário ou impressora e tente novamente. |
| Error banner | Não foi possível carregar os dados. |
| Error retry | Tentar novamente |
| Export loading | Exportando… |
| Destructive confirmation | *N/A — sem ações destrutivas no MVP* |

**Formatação numérica:** `pt-BR` — `1.284` páginas (ponto como separador de milhar).

**Datas na tabela:** exibir `dd/MM/yyyy HH:mm` derivado do ISO `timestamp` da API (já em America/Sao_Paulo).

---

## Table Specification

| Column | Width hint | Align | Format |
|--------|------------|-------|--------|
| Data/Hora | 140px | left | `dd/MM/yyyy HH:mm` |
| Usuário | 160px flex | left | truncate + title tooltip |
| Impressora | 140px | left | truncate |
| Arquivo | 1fr min 180px | left | truncate + title |
| Páginas | 72px | right | número pt-BR |
| Papel | 80px | left | `formatMediaLabel(media)` |
| Origem | 120px | left | `host_origin` ou "—" |

| Property | Value |
|----------|-------|
| Header | sticky top 0; bg `--bg-surface`; border-bottom `--border` |
| Row height | min **40px** |
| Zebra | even rows `--row-stripe` (opacidade ~diferença mínima) |
| Hover | `--row-hover` |
| Borders | horizontal only, `--border-subtle`; **no** vertical grid |

---

## Media Label Helper

`formatMediaLabel(raw)` em `frontend/src/lib/media.ts`:

| Raw (API) | Label |
|-----------|-------|
| `iso_a4_210x297mm` | A4 |
| `na_letter_8.5x11in` | Carta |
| *other* | raw (fallback) |

---

## Accessibility

| Requirement | Implementation |
|-------------|----------------|
| Contrast | Texto primário `#1D1D1F` em `#FFFFFF` — WCAG AA |
| Focus | Ring 2px `--focus-ring`, offset 2px em todos os interativos |
| Color alone | Estados ativos usam bg tint + peso semibold, não só cor |
| Motion | `@media (prefers-reduced-motion: reduce)` desliga pulse skeleton |
| Table | `<table>` semântico com `<th scope="col">` |
| Combobox | Headless UI — ARIA listbox pattern |
| Icons | `aria-hidden` quando decorativos; botões com `aria-label` se icon-only |

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | not applicable |
| third-party | none | not applicable |

---

## Alignment Checklist (CONTEXT.md)

| Decision | UI-SPEC section |
|----------|-----------------|
| D-01..D-09 Visual Apple + PaperCut | Color, Typography, Visual Hierarchy |
| D-10..D-14 Cards | SummaryCard, Copywriting |
| D-15..D-23 Filters | FilterBar, DatePresetGroup, URL state |
| D-24..D-30 Table | Table Specification |
| D-31..D-33 Media | Media Label Helper |
| D-34..D-37 Export | Button secondary, Copywriting |
| D-49..D-51 States | States Contract |
| D-52..D-57 Deploy | Out of UI-SPEC scope (infra plan) |

---

## Checker Sign-Off

| Dimension | Result | Notes |
|-----------|--------|-------|
| 1 Copywriting | **PASS** | CTAs específicos; empty/error com próximo passo |
| 2 Visuals | **PASS** | Focal point = tabela declarado |
| 3 Color | **PASS** | 60/30/10 + accent list fechada |
| 4 Typography | **PASS** | 4 sizes, 2 weights |
| 5 Spacing | **PASS** | Múltiplos de 4; exceções documentadas |
| 6 Registry Safety | **PASS** | shadcn none |

**Approval:** approved 2026-05-27
