# Phase 1: Infrastructure & Print Server - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-26
**Phase:** 1-Infrastructure & Print Server
**Areas discussed:** Escopo do Docker Compose, Restrição de rede do CUPS, Cadastro da impressora de teste, Validação do job de teste, Preparação da VM e variáveis

---

## Escopo do Docker Compose

| Option | Description | Selected |
|--------|-------------|----------|
| Apenas CUPS | Subir somente o serviço CUPS; validar impressão e logging | ✓ |
| Compose completo | Todos os serviços (cups, backend, frontend, nginx) | |
| Stubs vazios | Compose com serviços placeholder sem implementação | |

**User's choice:** Apenas CUPS — sem backend/frontend/nginx, nem stub. `docker-compose.yml` preparado para expansão futura sem serviços vazios.
**Notes:** Objetivo é validar exclusivamente Docker Compose → CUPS → Impressora → page_log válido.

---

## Restrição de rede do CUPS

| Option | Description | Selected |
|--------|-------------|----------|
| Apenas REDACTED_IP/16 | Rede corporativa específica, deny-by-default | ✓ |
| Ranges amplos (SPEC) | 192.168/10/172 conforme SPEC.md §3.1 | |

**User's choice:** Restringir apenas a REDACTED_IP/16; deny-by-default; `ALLOWED_NETWORK=REDACTED_IP/16` no `.env.example`.
**Notes:** Evitar expansão acidental da superfície de ataque.

---

## Cadastro da impressora de teste

| Option | Description | Selected |
|--------|-------------|----------|
| Script + documentação | `lpadmin` idempotente versionado + passo manual documentado | ✓ |
| Apenas manual | Documentação sem script | |
| UI web | Interface para adicionar impressoras | |

**User's choice:** Script shell idempotente + documentação; HP/Samsung por IPP/socket; sem UI.
**Notes:** SERVER-04 (UI) pertence à Fase 5.

---

## Validação do job de teste

| Option | Description | Selected |
|--------|-------------|----------|
| Ambos (local + remoto) | `lp` no container + IPP de máquina na rede | ✓ |
| Apenas local | `lp` dentro do container | |
| Apenas remoto | IPP de cliente na rede | |

**User's choice:** Validar dos dois modos.
**Notes:** Aceite exige linha no page_log com username `DOMINIO\usuario`, impressora correta e timestamp correto.

---

## Preparação da VM e variáveis

| Option | Description | Selected |
|--------|-------------|----------|
| VM reutilizada + IP estático | IP VM_HOST, hostname definido, credenciais só no .env | ✓ |
| VM nova | Provisionar nova VM | |
| Credenciais versionadas | Admin CUPS no repo | |

**User's choice:** VM reutilizada; IP estático VM_HOST; hostname definido; credenciais admin não versionadas (placeholders no `.env.example`).
**Notes:** Simplicidade operacional; sem AD, observabilidade ou HA nesta fase.

---

## Claude's Discretion

- FQDN exato do hostname (default proposto: `printwatch`)
- Localização/nome do script de setup da impressora
- IPP vs socket para impressora de teste específica

## Deferred Ideas

- Corrigir ROADMAP para `### Phase N:` (compatibilidade GSD)
- UI de impressoras (Fase 5)
- Backend/frontend/nginx (Fases 2–4)
- Integração AD, dashboard, HA
