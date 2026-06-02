# Runbook — Fleet Health e Toner (Fase 8)

Operação do monitoramento de frota (`/fleet`), health CUPS/ping em background e telemetria SNMP.

## Variáveis de ambiente

| Variável | Default | Descrição |
|----------|---------|-----------|
| `SNMP_COMMUNITY` | `public` | Community SNMP v2c global (read-only) |
| `FLEET_HEALTH_INTERVAL_SEC` | `900` | Intervalo do ciclo CUPS/ping (15 min) |
| `FLEET_SNMP_INTERVAL_SEC` | `43200` | Intervalo do ciclo SNMP (12 h) — deve ser **maior** que health |
| `CUPS_HOST` | `cups` | Host CUPS para referência operacional |
| `CUPS_PORT` | `631` | Porta IPP |

## Migration

```bash
cd backend
python -m alembic upgrade head
```

Revision esperada em head: `a3b7c2d4e5f6` (`fleet_health_toner`).

## Fluxo de health (FLEET-01/02)

1. Worker `_fleet_health_loop` consulta `lpstat -p {cups_queue_name}` (timeout 5s).
2. Se CUPS falhar e `ip_address` existir → fallback `ping -c 1` (Linux) ou `ping -n 1` (Windows).
3. Sem IP → status `unknown` (D-07).
4. Falha catastrófica do ciclo → todas ativas `unknown` (D-08).
5. `GET /api/v1/fleet` lê **somente cache** — nunca bloqueia em subprocess/SNMP.

## Opt-in SNMP (TONER-01)

1. Cadastrar `ip_address` em Settings → Impressoras.
2. Marcar **Monitorar toner via SNMP**.
3. Opcional: community override por impressora (campo mascarado na API).
4. **Testar SNMP** — `POST /api/v1/printers/{id}/snmp-test` (on-demand, não afeta GET /fleet).

OIDs MVP (RFC 3805):

- Contador total: `1.3.6.1.2.1.43.10.2.1.4`
- Níveis toner (walk): `1.3.6.1.2.1.43.11.1.1.9`

Piloto vendor-specific (mono/color separados): ver spike `snmpwalk` em impressora HP/Samsung antes de OIDs proprietários (D-18).

## Troubleshooting

| Sintoma | Causa provável | Ação |
|---------|----------------|------|
| Status `unknown` | Sem IP ou falha total do ciclo | Verificar IP; logs `fleet health cycle` |
| Status `offline` + ping falha | Impressora desligada/rede | TI rede; conferir IP |
| Toner **Indisponível** | SNMP timeout/falha (D-13) | Testar SNMP; firewall UDP 161; community |
| Toner **Não monitorado** | `snmp_enabled=false` | Habilitar opt-in |
| % antigo após falha | Bug se % aparecer com unavailable | Deve mostrar Indisponível sem % — reportar |
| Manager lento | SNMP no summary | Summary usa só SELECT cache — não deve await SNMP |

## UI

- `/fleet` — overview completo (sidebar entre Gerencial e Configurações).
- `/manager` — seção compacta frota + link "Ver frota completa".
- Jobs — badge **Offline** / **Desconhecido** na coluna impressora quando `printer_id` mapeado.

## Referências

- `.planning/research/PITFALLS.md` (#4 request path, #6 SQLite locks)
- `docs/manager-analytics-runbook.md` — contadores e reconciliação
