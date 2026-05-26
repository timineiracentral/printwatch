# REQUIREMENTS — PrintWatch MVP

**Versão:** 1.0  
**Referência:** PRD v1.0, SPEC v1.0, PROJECT.md  
**Ambiente:** Ubuntu 22.04 LTS + XCP-ng | Rede REDACTED_IP/16 | AD Domain | HP + Samsung (IP)

---

## v1 Requirements

### Captura de Jobs (CAPTURE)

- [x] **CAPTURE-01**: Sistema registra cada job de impressão contendo: `timestamp`, `username` (formato `DOMINIO\usuario` do AD), `printer`, `job_name`, `pages`, `copies`, `media`, `sides`, `color_mode` (quando disponível — HP/Samsung via CUPS), `host_origin` (IP ou hostname do cliente Windows)
- [x] **CAPTURE-02**: Captura ocorre em tempo real — job aparece no dashboard em até 30 segundos após ser enviado pelo cliente Windows
- [x] **CAPTURE-03**: Em caso de restart do serviço, o watcher retoma da última posição lida (sem duplicar nem perder registros)
- [x] **CAPTURE-04**: Se o serviço do dashboard/backend cair, a impressão física continua funcionando normalmente (CUPS é independente)

### Print Server (SERVER)

- [x] **SERVER-01**: CUPS configurado como print server intermediário acessível via IPP na porta 631 pela faixa REDACTED_IP/16
- [x] **SERVER-02**: `PageLogFormat` configurado explicitamente no `cupsd.conf` para garantir o formato esperado pelo parser
- [x] **SERVER-03**: Suporte a impressoras HP e Samsung conectadas por IP (protocolo IPP ou socket)
- [ ] **SERVER-04**: Interface para adicionar impressoras via URI (IPP, socket) com listagem de status (online/offline)

### Dashboard Web (DASH)

- [ ] **DASH-01**: Dashboard acessível via browser (HTTP porta 80) em qualquer máquina da rede REDACTED_IP/16
- [ ] **DASH-02**: Cards de sumário na página principal: total de jobs hoje, total de páginas hoje, top usuário do mês, top impressora
- [ ] **DASH-03**: Tabela paginada com todos os jobs (mais recentes primeiro), colunas: Data/Hora, Usuário, Impressora, Arquivo, Páginas, Papel, Origem
- [ ] **DASH-04**: Filtros: por intervalo de data (date range), por usuário, por impressora
- [ ] **DASH-05**: Busca por nome de arquivo/documento
- [ ] **DASH-06**: Dashboard carrega em menos de 2 segundos com até 50.000 registros

### Exportação (EXPORT)

- [ ] **EXPORT-01**: Botão de exportar CSV com os filtros ativos aplicados
- [ ] **EXPORT-02**: CSV abre corretamente no Excel/LibreOffice com todos os campos e encoding correto (UTF-8 BOM ou compatível)

### Retenção e Persistência (DATA)

- [x] **DATA-01**: Logs retidos por no mínimo 1 ano por padrão (configurável via variável de ambiente `LOG_RETENTION_DAYS`)
- [x] **DATA-02**: Reiniciar a VM não perde nenhum log já registrado (volumes Docker persistentes)
- [x] **DATA-03**: Banco SQLite com permissões restritivas (600) — não acessível diretamente pela rede

### Deploy e Configuração (DEPLOY)

- [x] **DEPLOY-01**: Deploy reproduzível via `docker compose up -d` em Ubuntu 22.04 LTS
- [x] **DEPLOY-02**: Arquivo `.env.example` documenta todas as variáveis de ambiente configuráveis
- [ ] **DEPLOY-03**: Script de setup configura o ambiente do zero (instala Docker, clona repositório, inicializa)
- [ ] **DEPLOY-04**: Documentação de configuração dos clientes Windows (adicionar impressora IPP com URL `http://<ip-da-vm>:631/printers/<nome>`)

### Extensibilidade (EXTEND)

- [ ] **EXTEND-01**: Coluna `status` na tabela `print_jobs` (valores: `allowed`/`blocked`/`pending`) — sempre `allowed` no MVP, preparada para Fase 2
- [ ] **EXTEND-02**: Tabela `policies` criada no banco desde o início (vazia no MVP)
- [x] **EXTEND-03**: Hook `pre_process_job(job_data)` no log_watcher que retorna `True` sempre no MVP — ponto de extensão para políticas na Fase 2

---

## v2 Requirements (Fora do MVP)

- Autenticação no dashboard (login com usuário/senha)
- Políticas de impressão (bloqueio colorido, cotas por usuário, apenas A4)
- Notificações por e-mail ao atingir quota
- Integração com Active Directory / LDAP para autenticação
- Relatórios por departamento
- API REST pública para integrações externas
- Suporte a impressoras USB compartilhadas

---

## Out of Scope

- **App mobile** — perfil de uso é exclusivamente admin de TI via browser
- **Impressoras USB diretas** — ambiente usa apenas impressoras com IP de rede
- **Exposição à internet** — acesso apenas rede local, sem port forward externo
- **Autenticação no MVP** — controlada por firewall/roteador no MVP
- **Multi-site** — ambiente único, sem necessidade de agentes remotos

---

## Critérios de Aceite Globais

1. Um PC Windows envia job → aparece no dashboard em ≤ 30 segundos *(CAPTURE-01, CAPTURE-02)*
2. Filtro por usuário retorna apenas os jobs daquele usuário *(DASH-04)*
3. CSV exportado abre corretamente no Excel com todos os campos *(EXPORT-01, EXPORT-02)*
4. Dashboard cai → impressão física continua funcionando *(CAPTURE-04)*
5. VM reinicia → nenhum log é perdido *(DATA-02)*
6. `docker compose up -d` em Ubuntu 22.04 sem configuração manual adicional *(DEPLOY-01)*

---

## Traceability

*(Será preenchido pelo roadmapper — mapeamento Fase → REQ-IDs)*

| Fase | Requirements |
|------|-------------|
| TBD | TBD |
