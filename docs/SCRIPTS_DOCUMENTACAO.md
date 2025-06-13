# Scripts de Automação - Raiox AI

## Visão Geral

Este diretório contém todos os scripts de automação, agendamento e verificação do sistema Raiox AI, incluindo as mais recentes implementações de integração com JotForm.

## Scripts Disponíveis

### Scripts de Agendamento

#### agendador_verificador_raioxapi.py
**Função:** Script principal de agendamento de verificações automáticas
**Características:**
- Execução periódica de verificações
- Integração com sistema de notificações
- Monitoramento contínuo de resultados
- Logs detalhados de execução

**Uso:**
```bash
python agendador_verificador_raioxapi.py
```

#### agendador_verificador_raioxapi_integrado.py
**Função:** Versão integrada e aprimorada do agendador
**Características:**
- Integração completa com todos os sistemas
- Suporte a múltiplos tipos de verificação
- Configuração flexível via arquivo de configuração
- Tratamento avançado de erros

**Uso:**
```bash
python agendador_verificador_raioxapi_integrado.py
```

### Scripts de Verificação

#### verificador_resultados_raioxapi.py
**Função:** Verificador principal de resultados da API
**Características:**
- Validação automática de resultados
- Detecção de anomalias e inconsistências
- Relatórios de status em tempo real
- Integração com sistema de alertas

**Uso:**
```bash
python verificador_resultados_raioxapi.py
```

#### verificador_resultados_clip_real.py
**Função:** Verificador especializado para testes com imagens reais
**Características:**
- Testes com dataset de imagens reais
- Validação de embeddings CLIP
- Comparação com resultados esperados
- Métricas de precisão e recall

**Uso:**
```bash
python verificador_resultados_clip_real.py
```

#### verificador_clip_real.py
**Função:** Verificador CLIP simplificado para testes rápidos
**Características:**
- Versão otimizada para execução rápida
- Integração com pipeline de CI/CD
- Suporte a testes automatizados
- Relatórios resumidos

**Uso:**
```bash
python verificador_clip_real.py
```

### Scripts de Integração JotForm

#### implement_jotform_webhook.sh
**Função:** Script de implementação do webhook JotForm
**Características:**
- Configuração automática do webhook
- Testes de conectividade
- Validação de endpoints

#### test_jotform_webhook.sh
**Função:** Script de teste do webhook JotForm
**Características:**
- Testes automatizados de integração
- Simulação de submissões
- Validação de respostas

## Configuração dos Scripts

### Variáveis de Ambiente

Todos os scripts utilizam as seguintes variáveis de ambiente (configuradas em `.env`):

```bash
# API Configuration
RAIOX_API_URL=http://localhost:8000
RAIOX_API_KEY=your_api_key_here

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/raiox_db

# JotForm Configuration
JOTFORM_API_KEY=your_jotform_api_key
JOTFORM_WEBHOOK_URL=https://your-domain.com/webhook

# Notification Configuration
NOTIFICATION_EMAIL=admin@yourdomain.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/your/webhook/url
```

### Agendamento via Systemd

Os scripts são executados automaticamente via serviços systemd:

```bash
# Verificar status do serviço
sudo systemctl status raioxapi-verificador.service

# Logs do serviço
sudo journalctl -u raioxapi-verificador.service -f

# Reiniciar serviço
sudo systemctl restart raioxapi-verificador.service
```

### Agendamento via Cron (alternativo)

Para agendamento via cron, adicione as seguintes linhas ao crontab:

```bash
# Verificação a cada 15 minutos
*/15 * * * * /opt/raiox-app/venv/bin/python /opt/raiox-app/scripts/verificador_resultados_raioxapi.py

# Agendador principal a cada hora
0 * * * * /opt/raiox-app/venv/bin/python /opt/raiox-app/scripts/agendador_verificador_raioxapi.py

# Verificação CLIP diária às 2h
0 2 * * * /opt/raiox-app/venv/bin/python /opt/raiox-app/scripts/verificador_clip_real.py
```

## Logs e Monitoramento

### Localização dos Logs

- **Logs da aplicação:** `/opt/raiox-app/logs/app.log`
- **Logs dos scripts:** `/opt/raiox-app/logs/scripts/`
- **Logs do systemd:** `journalctl -u raioxapi-verificador.service`

### Monitoramento

```bash
# Verificar últimas execuções
tail -f /opt/raiox-app/logs/app.log

# Verificar status dos scripts
ps aux | grep verificador

# Verificar uso de recursos
htop
```

## Troubleshooting

### Problemas Comuns

1. **Script não executa:**
   - Verificar permissões: `chmod +x script.py`
   - Verificar ambiente virtual: `which python`
   - Verificar dependências: `pip list`

2. **Erro de conexão com API:**
   - Verificar se API está rodando: `curl http://localhost:8000/health`
   - Verificar configurações de rede
   - Verificar logs da API

3. **Erro de banco de dados:**
   - Verificar conexão: `psql -h localhost -U user -d raiox_db`
   - Verificar extensão pgvector: `SELECT * FROM pg_extension WHERE extname = 'vector';`

### Debug Mode

Para executar scripts em modo debug:

```bash
# Definir variável de ambiente
export DEBUG=1

# Executar script
python verificador_resultados_raioxapi.py
```

## Desenvolvimento

### Adicionando Novos Scripts

1. Criar arquivo no diretório `scripts/`
2. Seguir padrão de nomenclatura: `[funcao]_[sistema]_[versao].py`
3. Incluir docstring e comentários
4. Adicionar testes unitários
5. Atualizar esta documentação

### Padrões de Código

- Usar Python 3.11+
- Seguir PEP 8
- Incluir type hints
- Usar logging ao invés de print
- Tratar exceções adequadamente

### Testes

```bash
# Executar testes unitários
python -m pytest tests/

# Executar testes de integração
python -m pytest tests/integration/

# Cobertura de código
coverage run -m pytest
coverage report
```

---

**Última atualização:** 13/06/2025  
**Responsável:** Sistema de Backup Automatizado

