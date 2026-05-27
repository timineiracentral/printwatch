---
phase: 04-dashboard-web
plan: "03"
subsystem: ui
tags: [react, tailwind, layout, primitives, lucide-react, accessibility]

requires:
  - phase: 04-01
    provides: Tailwind v4, CSS tokens, frontend scaffold
  - phase: 04-02
    provides: data layer hooks (not wired in shell yet)

provides:
  - UI primitives Button, Input, Skeleton, ErrorBanner, EmptyState
  - AppShell + Sidebar + PageHeader layout
  - Shell visível com copy pt-BR e slot Exportar CSV

affects: [04-04, 04-05, 04-06, 04-07]

tech-stack:
  added: []
  patterns:
    - "Button variants secondary/ghost only (no primary in MVP)"
    - "Skeleton pulse via CSS class + prefers-reduced-motion"
    - "AppShell desktop-first 220px sidebar, mobile hamburger"

key-files:
  created:
    - frontend/src/components/ui/Button.tsx
    - frontend/src/components/ui/Input.tsx
    - frontend/src/components/ui/Skeleton.tsx
    - frontend/src/components/ui/ErrorBanner.tsx
    - frontend/src/components/ui/EmptyState.tsx
    - frontend/src/components/layout/AppShell.tsx
    - frontend/src/components/layout/Sidebar.tsx
    - frontend/src/components/layout/PageHeader.tsx
  modified:
    - frontend/src/index.css
    - frontend/src/App.tsx

key-decisions:
  - "Exportar CSV disabled no header até plan 06 (D-34 visibilidade)"
  - "Sem React Router; nav Jobs é link estático # (D-44)"
  - "Área main com placeholder textual até plans 04-05 (cards/filtros/tabela)"

patterns-established:
  - "Focus ring 2px outline-offset-2 em todos os interativos (D-08)"
  - "Sidebar active: accent-tint bg + accent text semibold"

requirements-completed: []

duration: 12min
completed: 2026-05-27
---

# Phase 4 Plan 03: Shell UI + Primitivos Summary

**Shell PrintWatch com sidebar Jobs, header "Histórico de impressão", primitivos Tailwind locais (secondary/ghost) e skeleton acessível — fundação visual antes de cards e tabela.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-05-27T14:00:00Z
- **Completed:** 2026-05-27T14:12:00Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments

- Primitivos `Button` (secondary/ghost), `Input` com label, `Skeleton`, `ErrorBanner`, `EmptyState` sem MUI/shadcn/Radix themes
- `index.css` com animação skeleton 1.5s e `prefers-reduced-motion: reduce`
- `AppShell` + `Sidebar` 220px + `PageHeader` com título pt-BR e ação Exportar CSV
- Sidebar colapsável em viewport &lt;1024px (hamburger + overlay)
- `App.tsx` monta shell sem `BrowserRouter`; build frontend OK

## Task Commits

1. **Task 1: Primitivos UI** - `f2288af` (feat)
2. **Task 2: AppShell + Sidebar + PageHeader + wire App** - `aaffade` (feat)

**Plan metadata:** `102df80` (docs)

## Files Created/Modified

- `frontend/src/components/ui/Button.tsx` - variants secondary/ghost, focus ring
- `frontend/src/components/ui/Input.tsx` - border/radius 8px, label opcional
- `frontend/src/components/ui/Skeleton.tsx` - classe `skeleton-pulse`
- `frontend/src/components/ui/ErrorBanner.tsx` - copy D-51 + Tentar novamente
- `frontend/src/components/ui/EmptyState.tsx` - heading/body/CTA ghost
- `frontend/src/components/layout/AppShell.tsx` - flex sidebar + main max-w 1400px
- `frontend/src/components/layout/Sidebar.tsx` - PrintWatch logo, Jobs ativo
- `frontend/src/components/layout/PageHeader.tsx` - título + slot actions
- `frontend/src/App.tsx` - AppShell sem smoke JSON do plan 02
- `frontend/src/index.css` - skeleton keyframes + reduced motion

## Decisions Made

- Exportar CSV visível porém `disabled` até implementação no plan 06
- Placeholder curto na main até cards/filtros (plans 04-05)
- nginx/curl :80 adiado ao plan 04-07 (serviço ainda ausente no compose)

## Deviations from Plan

### Auto-fixed Issues

None - plan executed with expected infra deferral.

### Deferred Verification

- `docker compose up -d --build nginx` — serviço `nginx` não existe ainda (plan **04-07**). Build `npm run build` passou como verificação principal.
- `curl -sf http://localhost/` — bloqueado até deploy nginx; smoke visual via `npm run dev` ou após 04-07.

## Known Stubs

| Stub | File | Reason |
|------|------|--------|
| Exportar CSV disabled | `App.tsx` | D-34 — wired no plan 06 |
| Main placeholder copy | `App.tsx` | Cards/filtros/tabela nos plans 04-05 |
| Nav Jobs `href="#"` | `Sidebar.tsx` | Sem React Router (D-44) |

## Self-Check

- FOUND: frontend/src/components/ui/Button.tsx
- FOUND: frontend/src/components/layout/AppShell.tsx
- FOUND: frontend/src/App.tsx
- FOUND: .planning/phases/04-dashboard-web/04-03-SUMMARY.md
- FOUND: f2288af
- FOUND: aaffade

## Self-Check: PASSED
