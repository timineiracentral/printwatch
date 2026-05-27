---
id: GAP-02-02
type: investigation
status: resolved
priority: medium
created: "2026-05-26"
resolved: "2026-05-27"
resolved_in: 03-06
phase_origin: 02-log-pipeline-data-layer
resolves_phase: "3"
classification: "(a) Windows IPP envia bare username — domínio AD não chega ao CUPS no caminho observado"
recommendation: "(1) Aceitar status quo — username AS-IS; sem mudança de código na Fase 3"
source_evidence: "page_log + SQLite correlacionados 2026-05-27 12:34:02 UTC"
component: cups PageLogFormat %u + parser (sem alteração)
---

# GAP-02-02 — Username sem domínio AD (`DOMAIN\usuario`)

## Sintoma

Jobs de PC Windows AD gravados recentemente como `user.example` (sem `DOMAIN\`).

## Resolução (2026-05-27 — Plano 03-06)

Investigação observacional na VM: `page_log` bruto mostra `%u` = `user.example` **antes** do parser. Job de teste (2026-05-27 12:34:02) correlacionado 1:1 com SQLite (`pages=0`; operador confirmou **sem impressão física**, mas log/DB registraram o job).

**Classificação:** (a) — bare username na origem do log CUPS para o caminho IPP Windows atual.

**Decisão:** (1) — aceitar status quo; não concatenar domínio artificialmente; não alterar parser. D-14 revisada no STATE.md. Enriquecimento LDAP/AD → candidato v2.

**Evidência completa:** `.planning/phases/03-backend-api/03-INVESTIGATION-username-ad.md` (local, gitignored).

**Dados históricos:** 53 jobs com `DOMAIN\user.example` permanecem no banco AS-IS (forense).
