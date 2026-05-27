---
phase: 5
slug: master-data-organization
status: approved
shadcn_initialized: false
preset: none
created: 2026-05-27
approved: 2026-05-27
---

# Phase 5 — UI Design Contract (Settings)

> Contrato visual para cadastro operacional (Settings). Estende Fase 4 — mesmos tokens, sem novo design system.  
> Fontes: `05-CONTEXT.md` (D-08–D-10, D-13), `04-UI-SPEC.md`.

---

## Design System (herdado)

| Property | Value |
|----------|-------|
| Tool | **none** (igual Fase 4) |
| Styling | Tailwind + CSS variables `:root` |
| Icons | lucide-react |
| Componentes | Reutilizar `frontend/src/components/ui/*` (Button, Input, Table, Badge, Dialog) |
| Proibido | shadcn completo, dark mode, charts, CRUD enterprise denso |

**Acento:** `--accent` `#00AE5B` — ações primárias (Salvar, Cadastrar).

---

## Information Architecture

### Navegação (Sidebar)

```
PrintWatch
├── Jobs          → /           (audit — existente)
└── Configurações → grupo expandível ou seção
    ├── Impressoras      → /settings/printers
    ├── Departamentos    → /settings/departments
    ├── Centros de custo → /settings/cost-centers
    ├── Usuários         → /settings/users
    └── Importar CSV     → /settings/import
```

| Token | Value |
|-------|-------|
| Item ativo | `bg-[var(--accent-tint)]` + `text-[var(--accent)]` + `font-semibold` |
| Item inativo | `text-[var(--text-secondary)]` hover `bg-[var(--bg-muted)]` |
| Separador de grupo | Label 12px uppercase "Configurações" com `mt-6 mb-2` |

**D-09:** `/manager` reservado para Fase 7 — não adicionar link nesta fase.

---

## Layout por página Settings

### Padrão CRUD (printers, departments, cost-centers, users)

```
PageHeader: título + botão primário "Nova …"
[Banner opcional — ex.: filas não mapeadas]
DataTable: colunas fixas + ações linha (Editar | Desativar)
Empty state: ícone + texto + CTA "Cadastrar primeira …"
```

| Elemento | Treatment |
|----------|-------------|
| Tabela | Mesma linguagem da JobsTable: header sticky, linha 40px, zebra sutil |
| Formulário | Dialog modal (não página separada) — largura `max-w-lg` |
| Desativar | Confirmação inline ou dialog — nunca hard delete |
| Busca | Input 240px no header da tabela, debounce 300ms |

### Página Impressoras — destaque unmapped (D-13)

Banner acima da tabela quando `unmapped-queues.length > 0`:

| Property | Value |
|----------|-------|
| Background | `#FFF8E6` (warning tint) |
| Border | `1px solid #F5D90A` |
| Texto | "N filas no log ainda não cadastradas" + link "Ver filas" |
| CTA | Botão secundário "Cadastrar fila" abre dialog com `cups_queue_name` pré-preenchido |

### Página Importar CSV

```
PageHeader: "Importar CSV"
Cards em grid 2 colunas (≥1024px): um card por entidade (dept, CC, users, printers)
Cada card: título, descrição curta, "Baixar modelo", file input, botão Importar
Após import: painel de resultado (total, criados, atualizados, erros expandíveis por linha)
```

---

## Form Fields (por entidade)

### Printer

| Field | Control | Validation hint |
|-------|---------|-----------------|
| display_name | Input | obrigatório |
| cups_queue_name | Input | obrigatório, hint "nome exato da fila CUPS" |
| ip_address | Input | opcional |
| manufacturer_model | Input | opcional |
| location | Input | opcional |
| department_id | Select | opcional |
| is_active | Toggle | default true |

### Department / Cost Center

| Field | Control |
|-------|---------|
| code | Input uppercase auto |
| name | Input |
| cost_center_id (dept only) | Select opcional |
| is_active | Toggle |

### User

| Field | Control |
|-------|---------|
| cups_username | Input (readonly após create) |
| display_name | Input |
| department_id | Select |
| cost_center_id | Select opcional override |
| is_active | Toggle |

---

## Typography & Spacing

Herdar escala Fase 4 (Display 24px, Heading 17px, Body 14px, Label 12px).  
Gap entre header e conteúdo: `24px`. Gap tabela ↔ paginação: `16px`.

---

## Accessibility

- Dialog: focus trap, `aria-labelledby`, Esc fecha
- Tabelas: `scope="col"` nos `<th>`
- Botões de ação linha: `aria-label` descritivo ("Editar impressora X")
- Banner unmapped: `role="status"`

---

## Responsive

| Breakpoint | Behavior |
|------------|----------|
| ≥1024px | Sidebar fixa; tabela full width |
| <1024px | Sidebar colapsável (igual Fase 4); tabela `overflow-x-auto`; dialog full width menos margem 16px |

---

## States

| State | Treatment |
|-------|-----------|
| Loading | Skeleton 5 linhas na tabela |
| Error API | Alert vermelho discreto acima da tabela + retry |
| Empty | Ilustração mínima (ícone Printer) + CTA |
| Success save | Toast verde 3s ou banner dismissível |

---

## Anti-patterns (proibido)

- Wizard multi-step para CRUD simples
- Tabs aninhadas dentro de Settings
- Edição inline na tabela (usar dialog)
- Remover link Jobs ou quebrar layout audit em `/`

---

*Phase 5 UI contract — 2026-05-27*
