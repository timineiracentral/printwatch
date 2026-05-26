# ROADMAP — PrintWatch MVP

**Milestone:** v1.0 MVP  
**Estrutura:** MVP Vertical — cada fase entrega capacidade funcional end-to-end  
**Total:** 5 fases | 23 requisitos | Granularidade: Standard

---

## Visão Geral

| # | Fase | Goal | Requirements | Success Criteria |
|---|------|------|--------------|-----------------|
| 1 | Infrastructure & Print Server | VM Ubuntu + CUPS recebendo jobs IPP | SERVER-01, SERVER-02, SERVER-03, DEPLOY-01, DEPLOY-02 | ✓ Complete (2026-05-26) |
| 2 | Log Pipeline & Data Layer | Jobs capturados e persistidos no banco | CAPTURE-01, CAPTURE-02, CAPTURE-03, CAPTURE-04, DATA-01, DATA-02, DATA-03, EXTEND-01, EXTEND-02, EXTEND-03 | 4 |
| 3 | Backend API | API REST servindo dados com filtros | DASH-06 (performance), EXPORT-01, EXPORT-02 | 3 |
| 4 | Dashboard Web | Interface completa para o admin de TI | DASH-01, DASH-02, DASH-03, DASH-04, DASH-05 | 4 |
| 5 | Client Config & Hardening | PCs Windows integrados, deploy documentado | SERVER-04, DEPLOY-03, DEPLOY-04 | 4 |

---

## Fase 1: Infrastructure & Print Server

**Goal:** VM Ubuntu 22.04 com Docker Compose funcionando e CUPS recebendo jobs de teste via IPP — base da cadeia de impressão.

**Mode:** mvp

**Requirements:**
- SERVER-01: CUPS na porta 631 acessível pela rede REDACTED_IP/16
- SERVER-02: `PageLogFormat` configurado para formato esperado pelo parser
- SERVER-03: Impressoras HP/Samsung adicionadas por IP (IPP/socket)
- DEPLOY-01: `docker compose up -d` funciona em Ubuntu 22.04
- DEPLOY-02: `.env.example` documentado

**Success Criteria:**
1. `docker compose up` inicia todos os containers sem erro em Ubuntu 22.04
2. CUPS responde na porta 631 e aceita conexões da faixa REDACTED_IP/16
3. Uma impressora HP ou Samsung de teste é adicionada via URI IPP no CUPS
4. Um job de teste enviado via IPP gera linha no `page_log` no formato esperado
5. `.env.example` contém todas as variáveis necessárias com valores de exemplo

**Plans:** 5 plans

Plans:
- [x] 01-01-PLAN.md — Scaffold deploy: compose (só CUPS), .env.example, validate-phase1.sh Wave 0
- [x] 01-02-PLAN.md — Container CUPS: Dockerfile, ACL REDACTED_IP/16, PageLogFormat, entrypoint
- [x] 01-03-PLAN.md — setup-printer.sh idempotente + docs preparação VM (VM_HOST, printwatch)
- [x] 01-04-PLAN.md — Validação E2E: job local lp, page_log regex, checkpoint job remoto IPP *(aprovado 2026-05-26 — DOMAIN\user.example, URI :631)*
- [x] 01-05-PLAN.md — **Deploy VM real:** SSH, Docker/Compose, bootstrap CUPS, rede/firewall, test_printer *(evidência 2026-05-26)*

---

## Fase 2: Log Pipeline & Data Layer

**Goal:** Cada job impresso aparece automaticamente no banco SQLite — pipeline completo de captura sem intervenção manual.

**Mode:** mvp

**Requirements:**
- CAPTURE-01: Todos os campos registrados por job (username AD, printer, pages, color_mode, host_origin, etc.)
- CAPTURE-02: Job aparece no banco em ≤ 30 segundos após impressão
- CAPTURE-03: Restart do watcher não duplica nem perde registros
- CAPTURE-04: CUPS continua funcionando se backend/watcher cair
- DATA-01: Retenção configurável via `LOG_RETENTION_DAYS`
- DATA-02: Volumes Docker garantem persistência após restart da VM
- DATA-03: SQLite com permissões 600
- EXTEND-01: Coluna `status` na tabela `print_jobs` (default `allowed`)
- EXTEND-02: Tabela `policies` criada vazia
- EXTEND-03: Hook `pre_process_job` retorna `True` no MVP

**Success Criteria:**
1. Job impresso de um PC Windows com usuário AD aparece no banco em ≤ 30 segundos com todos os campos preenchidos
2. Restart do container backend não cria duplicatas nem perde jobs ocorridos durante o downtime
3. Com o container backend parado, um job enviado ao CUPS é impresso fisicamente sem erro
4. VM reiniciada — todos os jobs anteriores estão no banco intactos

---

## Fase 3: Backend API

**Goal:** API FastAPI servindo dados de impressão com filtros, paginação e exportação CSV — pronta para o frontend consumir.

**Mode:** mvp

**Requirements:**
- EXPORT-01: `GET /export/csv` com filtros ativos
- EXPORT-02: CSV abre corretamente no Excel com encoding adequado
- DASH-06: Dashboard carrega em < 2s com até 50.000 registros (índices de BD)

**Endpoints entregues:**
- `GET /jobs` — lista com paginação e filtros (username, printer, date_from, date_to, search)
- `GET /jobs/{id}` — detalhes de um job
- `GET /stats/summary` — totais: hoje, mês, top usuários, top impressoras
- `GET /export/csv` — download CSV com filtros
- `GET /printers` — impressoras do CUPS
- `GET /health` — health check

**Success Criteria:**
1. `GET /jobs` com 50.000 registros retorna em < 500ms (índices criados)
2. `GET /export/csv?username=X` baixa CSV contendo apenas jobs do usuário X, abre corretamente no Excel
3. `GET /stats/summary` retorna jobs e páginas de hoje, mês e top 5 usuários corretamente
4. `GET /health` retorna 200 OK quando todos os serviços estão saudáveis

---

## Fase 4: Dashboard Web

**Goal:** Interface React completa e usável para o admin de TI visualizar histórico, filtrar e exportar relatórios.

**Mode:** mvp

**Requirements:**
- DASH-01: Acessível via browser na rede local
- DASH-02: Cards de sumário (jobs hoje, páginas hoje, top usuário, top impressora)
- DASH-03: Tabela paginada com todos os jobs, colunas: Data/Hora, Usuário, Impressora, Arquivo, Páginas, Papel, Origem
- DASH-04: Filtros: date range, usuário, impressora
- DASH-05: Busca por nome de arquivo

**Success Criteria:**
1. Dashboard abre em < 2 segundos em browser na rede local apuntando para `http://<ip-vm>`
2. Cards exibem totais corretos (validados contra o banco diretamente)
3. Filtro por usuário + impressora retorna apenas os jobs correspondentes na tabela
4. Busca por nome de arquivo parcial retorna resultados corretos
5. Botão exportar CSV com filtros ativos faz download do arquivo correto

---

## Fase 5: Client Config, Hardening & Documentation

**Goal:** PCs Windows da rede configurados para imprimir via PrintWatch, setup documentado e sistema pronto para produção.

**Mode:** mvp

**Requirements:**
- SERVER-04: Interface para adicionar impressoras + status online/offline
- DEPLOY-03: Script de setup do zero (instala Docker, configura, inicializa)
- DEPLOY-04: Documentação de configuração dos clientes Windows

**Success Criteria:**
1. Script de setup executado em Ubuntu 22.04 limpo resulta em sistema funcional sem passos manuais adicionais
2. Documentação de configuração Windows (IPP) testada e validada em pelo menos 1 PC real
3. Um PC Windows configurado envia job → aparece no dashboard em ≤ 30 segundos (critério de aceite global)
4. README.md cobre: pré-requisitos, deploy, configuração de impressoras, configuração de clientes Windows, troubleshooting básico

---

## Dependências entre Fases

```
Fase 1 (Infra + CUPS)
    └── Fase 2 (Log Pipeline + DB)
            └── Fase 3 (Backend API)
                    └── Fase 4 (Dashboard Web)
                            └── Fase 5 (Client Config + Docs)
```

As fases são sequenciais — cada uma depende da anterior estar funcionando.

---

## Fora do Escopo (v2)

- Autenticação no dashboard
- Políticas de impressão e cotas
- Integração LDAP/AD
- Relatórios por departamento
- API pública REST

---

*Roadmap criado: Maio 2026 | Próximo passo: `/gsd-discuss-phase 1`*
