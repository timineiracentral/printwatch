# Phase 4: Dashboard Web - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-27
**Phase:** 04-dashboard-web
**Areas discussed:** Visual direction (Apple HIG + PaperCut), Summary cards, Date presets, Printer filter, Table density, Deploy/nginx, Media column, Stack/architecture, Performance

---

## 1 — Cards “top” (DASH-02)

| Opção | Descrição | Selecionado |
|-------|-----------|-------------|
| Jobs hoje + páginas hoje + top usuário **hoje** + top impressora **hoje** | Máxima reatividade operacional | |
| Jobs hoje + páginas hoje + top usuário **do mês** + top impressora **do mês** | Menos volatilidade; alinha REQUIREMENTS | ✓ |
| Fonte `hoje.top_*[0]` | Top do dia | |
| Fonte `mes.top_*[0]` | Top do mês calendário | ✓ |

**User's choice:** Jobs hoje (`stats.hoje.jobs`); páginas hoje (`stats.hoje.pages`); top usuário do mês (`stats.mes.top_users[0]`); top impressora do mês (`stats.mes.top_printers[0]`).

**Notes:**
- Motivo: mais útil gerencialmente; reduz volatilidade visual; alinha `REQUIREMENTS.md` DASH-02; “top do dia” oscila demais operacionalmente.
- Exibir total junto ao top: formato **"Maria Silva — 1.284 páginas"** (formatação pt-BR).

---

## 2 — Presets de data (DASH-04)

| Opção | Descrição | Selecionado |
|-------|-----------|-------------|
| Apenas date pickers custom | Mínimo | |
| Presets + intervalo custom | Hoje / 7 dias / Mês atual + pickers | ✓ |
| Presets em modal | Economiza espaço | |
| Presets visíveis acima da tabela | Troca instantânea, estilo analytics | ✓ |

**User's choice:** Presets **Hoje**, **Últimos 7 dias**, **Mês atual** + date picker para intervalo custom. Presets acima da tabela; sem modal; sensação Apple/PaperCut analytics.

**Notes:** Filtros na URL; refetch imediato ao trocar preset.

---

## 3 — Filtro de impressora (DASH-04)

| Opção | Descrição | Selecionado |
|-------|-----------|-------------|
| Campo texto livre | Flexível; risco de typo | |
| Dropdown `/api/v1/printers` match exato | Previsível; UX rápida | ✓ |
| Dropdown sem busca interna | Simples | |
| Dropdown com busca interna (typeahead) | Listas longas | ✓ |

**User's choice:** Dropdown de `/api/v1/printers`; match exato no param `printer`; busca interna no dropdown; sem free text nesta fase.

---

## 4 — Densidade da tabela (DASH-03)

| Opção | Descrição | Selecionado |
|-------|-----------|-------------|
| Confortável (~44px) | Mais espaço | |
| Semi-compacto (~40px) | Apple Settings + PaperCut | ✓ |
| Compacto denso (~32px) | Mais linhas; menos legível | |

**User's choice:** ~40px por linha; sticky header; zebra extremamente sutil; hover discreto; sem grid pesada.

---

## 5 — Deploy MVP (DASH-01)

| Opção | Descrição | Selecionado |
|-------|-----------|-------------|
| Apenas Vite dev `:5173` no MVP | Mais rápido de entregar | |
| nginx `:80` + compose integrado | Cenário real rede local desde o início | ✓ |
| TLS nesta fase | Segurança transporte | |
| Sem TLS | Rede local controlada | ✓ |

**User's choice:** nginx nesta fase; porta **80**; `http://VM_HOST`; Vite build estático; proxy `/api` → FastAPI; sem TLS; sem auth; sem reverse proxy complexo.

**Notes:** Manter simplicidade; validar acesso real da rede local; evitar retrabalho de `:5173` em produção.

---

## 6 — Coluna Papel (DASH-03)

| Opção | Descrição | Selecionado |
|-------|-----------|-------------|
| `media` bruto sempre | Zero código | |
| `media` bruto no MVP | Simples | parcial |
| Helper local com mapa + fallback bruto | UX limpa; custo baixo | ✓ |
| i18n / serviço de tradução | Escalável | (deferido) |

**User's choice:** Helper `formatMediaLabel` com mapa local (ex. `iso_a4_210x297mm` → A4, `na_letter_8.5x11in` → Carta); fallback = valor bruto.

---

## Visual direction (discussão inicial — consolidada no CONTEXT)

| Direção | Selecionado |
|---------|-------------|
| Apple HIG como referência primária UX/layout | ✓ |
| PaperCut green `#00AE5B` como acento | ✓ |
| Branco predominante, calmo, sem NOC/SOC | ✓ |
| Sem MUI, sem dark, sem charts MVP, sem admin template genérico | ✓ |
| Stack React + Vite + TS + Tailwind + TanStack Query | ✓ |

**Notes:** Consulta Apple HIG via context7 na discussão (layout, spacing, tabelas, search, loading, cor, acessibilidade). Usuário forneceu brief detalhado antes das decisões finais acima.

---

## Diretrizes adicionais (user-provided)

- Desktop-first; mobile apenas funcional
- Tabela = centro do produto; cards discretos
- Muito espaço em branco; animações mínimas; skeleton elegante
- Filtros instantâneos; export CSV visível; busca sempre acessível
- Paginação server-side; debounce busca; sem client-side filtering pesado

---

## Claude's Discretion

- Subdivisão exata de componentes e primitivos `ui/`
- Inter vs system fonts
- Implementação combobox (Headless UI vs alternativa)
- Waves dos plans de execução
- `VITE_API_BASE_URL` em prod vs same-origin implícito

---

## Deferred Ideas

- Gráficos/charts complexos
- Tema dark / visual cyberpunk
- Material UI / design system gigante
- Free text impressora
- WebSocket realtime
- TLS e autenticação (v2)
- Virtualização de tabela (salvo profiling)
- i18n completo para media labels
- Sort customizável na tabela
