---
id: GAP-02-02
type: investigation
status: pending
priority: medium
created: "2026-05-26"
phase_origin: 02-log-pipeline-data-layer
resolves_phase: "3"
source_evidence: "DB query 2026-05-26 — username=user.example (sem prefixo AD)"
component: cups + parser (a definir após investigação)
---

# GAP-02-02 — Username sem domínio AD (`DOMAIN\usuario`)

## Sintoma

Jobs enviados de PC Windows com usuário AD são gravados como:

```
username = user.example
```

Esperado conforme D-14 e D-08: `username = DOMAIN\user.example` (preservar o formato AD bruto).

## Contexto

A decisão D-14 do STATE.md registrou que jobs Windows IPP gravariam username
no formato `DOMAIN\usuario`. A evidência atual contradiz essa premissa.

## Investigação necessária ANTES de qualquer alteração de código

NÃO assumir bug no parser. A causa pode estar em qualquer camada:

1. **Cliente Windows IPP** — qual valor o spooler envia em `requesting-user-name`?
   - Comando: `Get-PrintJob` durante envio ou trace IPP local
2. **CUPS recebimento** — o que aparece em `/var/log/cups/access_log` no campo de usuário?
   - Ex: `CLIENT_HOST - user.example ...` vs `CLIENT_HOST - DOMAIN\user.example ...`
3. **page_log bruto** — o que o CUPS registra após processar?
   - Coletar linha bruta com `docker compose exec cups tail -n 1 /var/log/cups/page_log`
4. **Parser** — só relevante se as camadas acima já enviam o domínio

## Possíveis causas (a confirmar)

- (a) Windows IPP envia bare username por design (sem domínio NTLM)
- (b) CUPS strip do `DOMAIN\` no processamento
- (c) PageLogFormat usa `%u` que pode normalizar
- (d) Parser está descartando — improvável (não há logic de strip no parser)

## Decisão registrada

D-14 do STATE foi baseado em premissa não verificada. Após investigação:
- Se for (a): atualizar D-14 — domínio AD não chega no CUPS via IPP Windows;
  considerar enriquecimento via LDAP/AD lookup numa fase futura (v2 conforme ROADMAP)
- Se for (b) ou (c): ajustar CUPS config
- Se for (d): ajustar parser

## Impacto

Médio — quebra requisito implícito de auditoria por usuário AD.
Para o MVP, `username` ainda permite identificar quem imprimiu (apenas sem o prefixo do domínio).

## Tracking

- Coletar evidência bruta antes de qualquer mudança
- Documentar conclusão como nova decisão (D-XX) no STATE.md
- Atualizar/superseder D-14 se necessário
