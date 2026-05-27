---
created: 2026-05-27T20:00:00Z
title: Política de acesso usuário–impressora (Fase 5.2)
area: planning
files:
  - .planning/PROJECT.md
  - .planning/REQUIREMENTS.md
  - .planning/ROADMAP.md
---

## Problem

TI precisa orientar instalação de impressoras no Windows (IPP) por usuário, auditar uso fora da política e exportar roteiro de setup — sem bloquear impressão no CUPS. Fase 5 entregou master data; falta N:N User↔Printer permissivo, UI, export TI e indicador soft em jobs.

## Solution

Fase **5.2** antes da Fase 6: `user_printer_access` + API; UI ficha usuário (e vista invertida opcional na impressora); UX fila detectada sem jargão CUPS; export roteiro TI; flag read-only "fora da política" em jobs/export. Bloqueio CUPS, herança por dept e portal self-service ficam fora (v2.5+). Ver ACCESS-01–05 em REQUIREMENTS.md e decisões em PROJECT.md.
