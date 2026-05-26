# Phase 1: Infrastructure & Print Server - Context

**Gathered:** 2026-05-26
**Status:** Ready for planning

<domain>
## Phase Boundary

VM Ubuntu 22.04 reutilizada com IP estático, Docker Compose subindo **apenas o serviço CUPS**, impressora de teste cadastrada via script idempotente, e validação de que jobs geram linhas válidas no `page_log`. Não inclui backend, frontend, nginx, watcher, banco, dashboard, observabilidade, integração AD ou HA.

**Cadeia alvo desta fase:** Docker Compose → CUPS → Impressora → `page_log` válido

</domain>

<decisions>
## Implementation Decisions

### Escopo do Docker Compose (Fase 1)
- **D-01:** Subir **somente** o container/serviço CUPS via `docker compose up -d`.
- **D-02:** Backend, frontend e nginx **não entram** nesta fase — nem como stub ou serviço vazio.
- **D-03:** `docker-compose.yml` deve ser escrito já pensando em expansão futura (comentários ou estrutura clara), mas **sem** serviços placeholder ativos.
- **D-04:** Objetivo exclusivo: validar cadeia de impressão e logging (`page_log`).

### Restrição de rede do CUPS
- **D-05:** Restringir acesso CUPS **apenas** à rede `REDACTED_IP/16`.
- **D-06:** **Não** usar ranges amplos (192.168/10/172 genéricos da SPEC) nesta fase.
- **D-07:** Adotar postura **deny-by-default** no `cupsd.conf` — permitir explicitamente só `REDACTED_IP/16`.
- **D-08:** `ALLOWED_NETWORK=REDACTED_IP/16` deve existir no `.env.example` desde a Fase 1 e ser consumido pela configuração do CUPS.

### Cadastro da impressora de teste
- **D-09:** Sem UI web nesta fase (SERVER-04 é Fase 5).
- **D-10:** Cadastro via **script shell versionado** no repositório + **documentação** do passo manual equivalente.
- **D-11:** Script deve usar `lpadmin` de forma **idempotente** (reexecutável sem duplicar impressora).
- **D-12:** Impressoras de teste: HP ou Samsung por **IPP ou socket**, conforme disponibilidade do equipamento.

### Validação do job de teste
- **D-13:** Validar em **dois modos**:
  1. Job local via `lp` **dentro do container** (sanidade rápida)
  2. Job remoto via **IPP** de uma máquina na rede `REDACTED_IP/16`
- **D-14:** Critérios de aceite do `page_log`:
  - Linha presente no `page_log` após cada job
  - `username` no formato `DOMINIO\usuario`
  - Nome da impressora correto
  - Timestamp correto
- **D-15:** `PageLogFormat` deve ser configurado explicitamente no `cupsd.conf` (SERVER-02) conforme SPEC.md §3.1 — adaptando ACL de rede para `REDACTED_IP/16`.

### Preparação da VM e variáveis de ambiente
- **D-16:** Reutilizar VM Ubuntu 22.04 existente no XCP-ng (não provisionar nova).
- **D-17:** IP estático **obrigatório** na Fase 1: `VM_HOST`.
- **D-18:** Hostname deve ser definido na Fase 1 — usar `printwatch` (alinhado ao nome do projeto/serviço).
- **D-19:** Credenciais admin do CUPS **não versionadas** — apenas placeholders no `.env.example` (`CUPS_ADMIN_USER`, `CUPS_ADMIN_PASSWORD`).
- **D-20:** `.env.example` documenta todas as variáveis necessárias para esta fase (DEPLOY-02).

### Princípios operacionais (Fase 1)
- **D-21:** Priorizar **simplicidade operacional** — chegar rápido ao `page_log` válido.
- **D-22:** Sem observabilidade/dashboard, integração AD, otimização HA/redundância nesta fase.

### Claude's Discretion
- Formato exato do hostname DNS interno (FQDN vs short name) — default `printwatch`, ajustável no plano se o AD exigir sufixo.
- Nome do arquivo/script de setup da impressora e localização no repo (`scripts/` vs `cups/`).
- Detalhes do Dockerfile/entrypoint do CUPS desde que respeitem D-01 a D-20.
- Driver/protocolo IPP vs socket para impressora específica de teste — escolher o que funcionar com o hardware disponível.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos e arquitetura
- `.planning/PROJECT.md` — Contexto do ambiente (rede REDACTED_IP/16, AD, stack, decisões de plataforma)
- `.planning/REQUIREMENTS.md` — SERVER-01, SERVER-02, SERVER-03, DEPLOY-01, DEPLOY-02
- `.planning/ROADMAP.md` — Goal, success criteria e requirements da Fase 1
- `PRD.md` — Visão do produto e critérios de aceite globais
- `SPEC.md` §3.1 — Container CUPS, `PageLogFormat`, estrutura `cups/` e volumes (adaptar ACL de rede para REDACTED_IP/16)
- `SPEC.md` §3.5 — Estrutura-alvo do `docker-compose.yml` (implementar só serviço `cups` nesta fase)
- `SPEC.md` §5 — Variáveis de ambiente (`.env.example`)

### Nota de compatibilidade GSD
- `.planning/ROADMAP.md` usa headings `## Fase N:` — deve ser migrado para `### Phase N:` para parsing automático do GSD (ver deferred).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Nenhum — projeto greenfield; SPEC.md define estrutura-alvo a ser criada nesta fase.

### Established Patterns
- Nenhum código existente ainda.
- `.planning/codebase/*.md` não mapeado — seguir SPEC.md e decisões D-01 a D-22.

### Integration Points
- Volume compartilhável futuro: `/var/log/cups` (Fase 2 watcher lerá `page_log` daqui).
- Porta 631 exposta para clientes Windows via IPP (validação remota na Fase 1; integração documentada na Fase 5).

</code_context>

<specifics>
## Specific Ideas

- VM IP fixo: **VM_HOST**
- Fluxo mínimo desejado: `docker compose up` → CUPS aceita IPP → impressora cadastrada → job local + remoto → linha no `page_log`
- Username AD esperado: `DOMINIO\usuario` (normalização detalhada na Fase 2)

</specifics>

<deferred>
## Deferred Ideas

- **ROADMAP GSD parsing** — Migrar headings de `## Fase N:` para `### Phase N:` em `.planning/ROADMAP.md` para compatibilidade com `gsd-tools` (solicitado pelo usuário para correção posterior).
- **UI de cadastro de impressoras** — SERVER-04, Fase 5.
- **Backend/frontend/nginx no compose** — Fases 2–4; não stub na Fase 1.
- **Integração AD/LDAP** — Fase 2+.
- **Observabilidade e dashboard** — Fases 3–4.
- **HA/redundância** — fora do MVP.

</deferred>

---

*Phase: 1-Infrastructure & Print Server*
*Context gathered: 2026-05-26*
