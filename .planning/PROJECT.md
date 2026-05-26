# PrintWatch — Project Context

**Versão:** 1.0  
**Inicializado:** Maio 2026  
**Status:** Em planejamento

---

## What This Is

PrintWatch é um sistema self-hosted de monitoramento de impressão. Age como print server intermediário: todos os jobs de impressão passam por ele, são registrados em banco de dados e expostos em um dashboard web acessível pela rede local.

**Core Value:** Registrar 100% dos jobs de impressão com rastreabilidade completa (quem, o quê, quando, quantas páginas) — substituindo soluções pagas como PaperCut em ambientes de pequeno/médio porte.

---

## Contexto do Ambiente

| Atributo | Valor |
|----------|-------|
| Rede local | REDACTED_IP/16 |
| Usuários estimados | 20–100 |
| Impressoras | HP e Samsung, conectadas por IP na rede (sem USB compartilhado) |
| Domínio Windows | Sim — Active Directory ativo; usernames serão no formato `DOMINIO\usuario` |
| Hypervisor | XCP-ng Center |
| Servidor | VM Ubuntu 22.04 LTS existente (a ser reutilizada/formatada para este projeto) |
| Clientes | Windows 10/11 configurados via IPP apontando para a VM |

---

## Problema

Ambientes corporativos sem controle de impressão sofrem com:
- Impossibilidade de rastrear quem imprimiu o quê e quando
- Sem visibilidade de desperdício de papel/toner
- Sem base para cobrar por departamento ou aplicar políticas de impressão futuramente

**Decisão de arquitetura registrada:** A alternativa de rodar no Windows Server (VM DHCP existente) foi avaliada e descartada. Razões: (1) risco operacional — a VM DHCP serve o Fortigate, qualquer instabilidade derrubaria toda a rede; (2) Event Log do Windows não expõe `color_mode` e `sides` nativamente via Event ID 307; (3) CUPS é o padrão industrial para este caso de uso. VM Linux nova/reutilizada no XCP-ng elimina todos esses riscos sem custo de licença.

---

## O Que Será Construído (MVP)

Um servidor de impressão intermediário com:
1. **Print Server (CUPS)** — recebe jobs dos PCs Windows via IPP, encaminha para a impressora física, grava `page_log`
2. **Log Watcher** — monitora o `page_log` em tempo real e persiste cada job no banco
3. **API REST (FastAPI)** — expõe os dados com filtros e exportação CSV
4. **Dashboard Web (React)** — interface para o admin de TI visualizar histórico e gerar relatórios

---

## Stack Tecnológica

| Camada | Tecnologia | Justificativa |
|--------|-----------|---------------|
| Print Server | CUPS 2.4+ | Padrão Linux, logs nativos, extensível |
| Log Watcher | Python 3 + watchdog | Lê `page_log` em tempo real, sem polling |
| Banco | SQLite (via SQLAlchemy) | Zero config, suficiente para MVP (20–100 usuários) |
| Backend API | FastAPI (Python) | Rápido de desenvolver, async nativo |
| Frontend | React + Vite + TailwindCSS | Moderno, fácil de manter |
| Deploy | Docker Compose | Reproduzível, deploy em 1 comando |
| Proxy | Nginx | Serve frontend + proxia API |

---

## Usuários

| Perfil | Quem | Necessidade |
|--------|------|-------------|
| Administrador de TI | Instala/mantém o sistema | Ver logs, exportar relatórios, configurar impressoras |
| Gestor | Coordenador/gerente | Ver relatório de uso por período |
| Usuário final | Funcionário | Não interage (transparente) |

---

## Requirements

### Validated

*(Nenhum ainda — será validado após deploy)*

### Active

- [ ] Registrar 100% dos jobs com: usuário (domínio AD), impressora, nome do arquivo, páginas, cópias, papel, frente/verso, color_mode, IP de origem, data/hora
- [ ] Dashboard web acessível por browser na rede local (192.0.2.50)
- [ ] Filtros por período, usuário, impressora e busca por nome de arquivo
- [ ] Exportação de relatório em CSV compatível com Excel
- [ ] Interface para adicionar impressoras HP/Samsung via URI IPP
- [ ] Logs retidos por mínimo 1 ano (configurável)
- [ ] Se o dashboard cair, a impressão física continua funcionando
- [ ] Deploy reproduzível via Docker Compose em Ubuntu 22.04
- [ ] Configuração de clientes Windows via IPP documentada

### Out of Scope (MVP)

- Autenticação no dashboard — ambiente de rede local controlada por firewall
- Cotas e bloqueios de impressão — Fase 2
- Integração com Active Directory/LDAP — Fase 2 (username vem via IPP nativamente)
- Impressoras USB compartilhadas — apenas impressoras de rede com IP
- App mobile — desnecessário para o perfil de uso
- API pública REST — Fase 2

---

## Key Decisions

| Decisão | Justificativa | Resultado |
|---------|---------------|-----------|
| Linux (Ubuntu 22.04) em vez de Windows Server | CUPS nativo, isolamento do servidor DHCP crítico, sem custo de licença | Decidido |
| VM reutilizada (Ubuntu 22.04 existente) em vez de nova | Já provisionada no XCP-ng, mesma versão do PRD | Decidido |
| SQLite em vez de PostgreSQL/MySQL | Volume de 20–100 usuários não justifica servidor de BD separado no MVP | Decidido |
| Docker Compose em vez de instalação bare-metal | Reproduzibilidade, facilidade de backup e migração | Decidido |
| CUPS como print server intermediário | Padrão industrial, logs estruturados, suporte a IPP nativo para Windows | Decidido |

---

## Riscos Conhecidos

| Risco | Probabilidade | Mitigação |
|-------|---------------|-----------|
| Username AD chega como `DOMINIO\usuario` em vez de apenas `usuario` | Alta | Normalizar no parser do log_watcher; documentar formato esperado |
| HP/Samsung não expor `color_mode` via CUPS page_log | Média | Testar na fase de setup; campo fica `null` se não disponível (aceitável no MVP) |
| PCs Windows não enviarem username correto via IPP | Média | Documentar configuração de driver; fallback para IP de origem |
| CUPS não gravar page_log por padrão | Alta (já mapeado) | Script de setup configura `PageLogFormat` explicitamente |

---

## Evolution

Este documento evolui nas transições de fase e marcos de milestone.

**Após cada transição de fase** (via `/gsd-transition`):
1. Requisitos invalidados? → Mover para Out of Scope com razão
2. Requisitos validados? → Mover para Validated com referência à fase
3. Novos requisitos emergiram? → Adicionar em Active
4. Decisões a registrar? → Adicionar em Key Decisions

**Após cada milestone** (via `/gsd-complete-milestone`):
1. Revisão completa de todas as seções
2. Core Value check — ainda é a prioridade certa?
3. Auditoria de Out of Scope — razões ainda válidas?

---
*Last updated: Maio 2026 após inicialização*
