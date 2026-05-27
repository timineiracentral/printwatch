# Phase 6: Costing & Chargeback — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `06-CONTEXT.md`.

**Date:** 2026-05-27  
**Phase:** 6-costing-chargeback  
**Areas discussed:** Tarifa e vigência, Mono/color e páginas pendentes, Atribuição chargeback, UI Settings tarifas, Export CSV, Limite Fase 6 vs 7

---

## 1. Modelo de tarifa e vigência

| Option | Description | Selected |
|--------|-------------|----------|
| Tarifa única ativa | Uma linha mono/color; mudança sobrescreve | |
| Histórico com vigência | Novas tarifas com `valid_from`; custo usa tarifa da data do job | ✓ |

**User's choice:** Histórico para quando a tarifa mudar.  
**Notes:** Custo histórico deve refletir tarifa vigente na data do evento, não a tarifa atual.

---

## 2. Regra mono vs color

| Option | Description | Selected |
|--------|-------------|----------|
| NULL = mono (conservador) | Todas páginas sem modo contam como P&B | |
| NULL excluído + correção manual | Não fatura até classificar; admin pode preencher depois | ✓ |
| NULL = 50/50 ou ignorar job inteiro | — | |

**User's choice:** Trabalhar para sempre registrar color/P&B na captura; se NULL, não levar a folha em consideração; opção de preencher manualmente — após preencher, entra no cálculo.  
**Notes:** Inclui esforço em CUPS/parser, não só regra de billing.

---

## 3. Atribuição para chargeback

| Option | Description | Selected |
|--------|-------------|----------|
| CC usuário → CC dept → Não atribuído | Precedência padrão ORG | ✓ |
| Usuário desconhecido no mesmo bucket CC | — | |
| Usuário desconhecido = bucket próprio | Separado de “Não atribuído” | ✓ |
| printer_id NULL misturado em CC | — | |
| printer_id NULL = linha/bucket separado | “Impressora não cadastrada” | ✓ |
| Incluir outside_policy no chargeback | — | |
| Excluir outside_policy | Só auditoria | ✓ |

**User's choice:** CC: override usuário → CC dept → Não atribuído; usuário desconhecido bucket próprio; printer_id nulo flag/linha “impressora não cadastrada”; outside_policy fora do chargeback.

---

## 4. Onde configurar tarifas

| Option | Description | Selected |
|--------|-------------|----------|
| Nova seção Settings | Página dedicada “Tarifas” | ✓ |
| Subpágina Import / outra entidade | — | |

**User's choice:** Nova sessão (seção) em Settings.

---

## 5. Formato export chargeback

| Option | Description | Selected |
|--------|-------------|----------|
| Um CSV com coluna group_by | — | |
| Dois CSVs (CC + dept) | Mesmo período, colunas mono/color/custo + não atribuído + pendentes opcional | ✓ |
| Incluir outside_policy | — | |
| Sem outside_policy | ✓ |

**User's choice:** Dois CSVs; colunas mono/color/custo + não atribuído + opcional páginas pendentes; sem outside_policy.

---

## 6. Limite Fase 6 vs Fase 7

| Option | Description | Selected |
|--------|-------------|----------|
| Estender stats/summary com custo agora | — | |
| Fase 6: tarifas, custo jobs API, exports, correção manual | ✓ |
| Fase 7: /manager e stats visuais | ✓ |
| Jobs UI: só coluna custo opcional | Sem cards gerenciais | ✓ |

**User's choice:** Fase 6 = tarifas, custo na API jobs, exports, correção manual color_mode. Fase 7 = `/manager` e stats visuais. Jobs `/` só coluna custo opcional.

---

## Claude's Discretion

- UX da correção manual (modal vs inline)
- Schema `cost_rates` (`valid_to` vs só `valid_from`)
- Aliases CUPS → mono/color
- Rotas/nomes finais dos CSV

## Deferred Ideas

- Tarifa por impressora (v1.6+)
- outside_policy em exports de custo
- Dashboard gerencial (Fase 7)
