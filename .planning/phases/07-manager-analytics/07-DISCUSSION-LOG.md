# Phase 7: Manager Analytics — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-02  
**Phase:** 7-Manager Analytics  
**Areas discussed:** Período e comparativo, Regras de custo, Rankings Top 10, API/performance/navegação, Mono/color e pendências, MVP contadores (expansão de escopo)

---

## Período e comparativo

| Option | Description | Selected |
|--------|-------------|----------|
| Igual auditoria | Hoje, 7 dias, Mês atual + custom | ✓ |
| Foco gerencial | 30/90/mês sem Hoje | |
| Ampliado | Hoje + 7 + 30 + 90 + mês + custom | |

| Default ao abrir | | |
| Últimos 30 dias | | ✓ |
| Mês atual | | |
| Últimos 90 dias | | |

**User's choice:** Presets = auditoria; default = 30 dias; comparativo e exibição = "você decide" → capturado em CONTEXT D-03, D-04 (híbrido + delta %).

---

## Regras de custo

**User's choice:** Todas as opções = "você decide" → CONTEXT D-05–D-08 alinhadas à Fase 6 (faturável, excluir outside_policy, sem tarifa = "—", buckets nos tops).

---

## Rankings Top 10

| Option | Description | Selected |
|--------|-------------|----------|
| Três tabelas empilhadas | | ✓ |
| Grid 2 colunas | | |
| Cards top 3 + ver todos | | |

**User's choice:** Layout = três tabelas; demais = discrição → D-09–D-12.

---

## API, performance e navegação

**User's choice:** Todas = "você decide" → CONTEXT D-17–D-21 (novo `/manager/summary`, manter SummaryCards home, nav entre Jobs/Settings, sem export manager).

---

## Mono/color e pendências (área adicional)

**User's notes (freeform):** Pré-requisito Fase 6/captura: color_mode obrigatório para custo confiável; fallback correção manual; manager mostra pendências; bloqueador go-live >X% sem plano.

**User's choice:** Detalhes de cards/tops/go-live = discrição → D-13–D-16.

---

## MVP contadores (expansão de escopo)

| Roadmap option | Description | Selected |
|----------------|-------------|----------|
| A | Fase 7 só ANAL | |
| B | ANAL + spike, METER v1.6 | |
| C | ANAL + MVP manual contadores | ✓ |

| Leitura MVP | | |
| Manual + CSV import | | ✓ |
| Só manual | | |

| SNMP auto Fase 7 | | |
| Não — Fase 8 | | ✓ |

| UI contadores | | |
| Seção abaixo dos tops | | ✓ |

**User's choice:** Escopo C; manual + CSV; sem SNMP; seção abaixo; custo delta e reconciliação = discrição → D-22–D-28.

---

## Claude's Discretion

Período anterior (modo híbrido), exibição comparativo, regras de custo detalhadas, ordenação tops, dept vs CC, charts, API shape, home cards link, label sidebar, limiares %, schema readings, fallback custo contador só-total (proporção jobs).

---

## Deferred Ideas

- SNMP/IPP automático contadores → Fase 8  
- Gráficos série temporal → futuro  
- Export manager CSV → fora  
- Aba jobs vs contador → seção única escolhida  
