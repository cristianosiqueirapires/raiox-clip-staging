# Mapeamento Completo do Servidor Staging 45.55.128.141

## Data do Mapeamento: 13/06/2025

### Estrutura Principal do Projeto

#### /opt/raiox-app/ (Aplicação Principal)
- **Arquivos de Configuração:**
  - `.env` - Configurações de ambiente
  - `.env.backup` e `.env.backup2` - Backups das configurações
  - `requirements.txt` - Dependências Python
  - `setup.sh` - Script de instalação

- **Documentação:**
  - `README.md` - Documentação principal
  - `manual-definitivo-raiox-ai-v2.md` - Manual definitivo v2
  - `manual-definitivo-raiox-ai.md` - Manual definitivo v1
  - `manual-coleta-imagens-reais.md` - Manual de coleta de imagens
  - `manual-para-manus-gemini.txt` - Manual para Manus/Gemini
  - `raiox-ai-engenharia-gpt.txt` - Documentação de engenharia
  - `melhorias-futuras-raiox-ai.md` - Melhorias futuras
  - `implementacao_raiox_fastapi.md` - Implementação FastAPI

- **Código da Aplicação (app/):**
  - `main.py` - Aplicação principal FastAPI
  - `analise_tracker.py` - Tracker de análises
  - `models/implant.py` - Modelo de implante
  - `models/__init__.py` - Inicialização dos modelos
  - `db/session.py` - Sessão do banco de dados
  - `db/__init__.py` - Inicialização do DB
  - `schemas/webhook.py` - Schema do webhook
  - `schemas/implant.py` - Schema do implante
  - `schemas/__init__.py` - Inicialização dos schemas

#### Scripts de Verificação e Agendamento

##### /root/ (Scripts Principais)
- `agendador_verificador_raioxapi.py` (5.259 bytes) - Script de agendamento
- `verificador_resultados_raioxapi.py` (9.977 bytes) - Verificador de resultados

##### /opt/ (Scripts Auxiliares)
- `verificador_clip_real.py` (6.891 bytes) - Verificador CLIP real

#### Serviços Systemd Ativos
- `raiox-api.service` - Serviço da API Raiox
- `raiox-app.service` - Aplicação principal Raiox
- `raioxapi-verificador.service` - Serviço verificador de resultados

#### Arquivos de Configuração de Serviços
- `/etc/systemd/system/raiox-api.service`
- `/etc/systemd/system/raiox-app.service`
- `/etc/systemd/system/raioxapi-verificador.service`

#### Backup Existente
- `/root/backup_raiox_20250611_200322/raiox-clip-staging.tar.gz`

### Novos Scripts Identificados (desde último backup)
1. **agendador_verificador_raioxapi.py** - Script de agendamento integrado
2. **verificador_resultados_raioxapi.py** - Verificador de resultados atualizado
3. **verificador_clip_real.py** - Verificador CLIP para testes reais
4. **raioxapi-verificador.service** - Novo serviço systemd

### Status dos Serviços
- Todos os serviços estão **loaded active running**
- Não há crontab configurado (serviços gerenciados via systemd)

### Próximos Passos
1. Baixar todos os arquivos identificados
2. Organizar nos repositórios GitHub apropriados
3. Atualizar documentação com novos scripts
4. Sincronizar com repositórios existentes

