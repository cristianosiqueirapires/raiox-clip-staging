# Raiox AI - Sistema CLIP Staging

## Backup do Servidor CLIP Staging - Sistema Raiox AI

**Data da Atualização:** 13 de Junho de 2025  
**Servidor:** 45.55.128.141 (raiox-clip-staging)

### Visão Geral

Este repositório contém o backup completo e atualizado do servidor staging do sistema Raiox AI, incluindo todos os novos scripts de agendamento, verificação e integração com JotForm desenvolvidos recentemente.

### Novos Recursos Adicionados

#### Scripts de Agendamento e Verificação

1. **agendador_verificador_raioxapi.py** - Script principal de agendamento
   - Gerencia agendamentos automáticos de verificação
   - Integração com sistema de notificações
   - Monitoramento contínuo de resultados

2. **agendador_verificador_raioxapi_integrado.py** - Versão integrada
   - Versão aprimorada com integração completa
   - Suporte a múltiplos tipos de verificação
   - Logs detalhados de execução

3. **verificador_resultados_raioxapi.py** - Verificador de resultados
   - Validação automática de resultados da API
   - Detecção de anomalias e inconsistências
   - Relatórios de status em tempo real

4. **verificador_resultados_clip_real.py** - Verificador CLIP real
   - Testes com imagens reais do sistema
   - Validação de embeddings CLIP
   - Comparação com resultados esperados

5. **verificador_clip_real.py** - Verificador CLIP simplificado
   - Versão otimizada para testes rápidos
   - Integração com pipeline de CI/CD
   - Suporte a testes automatizados

#### Serviços Systemd

- **raiox-api.service** - Serviço principal da API
- **raiox-app.service** - Aplicação principal Raiox
- **raioxapi-verificador.service** - Serviço de verificação automática

### Integração com JotForm

O sistema agora inclui integração completa com JotForm para:

- Recebimento automático de submissões
- Processamento de imagens via webhook
- Retorno de resultados para o formulário
- Notificações automáticas de status

Documentação detalhada disponível em: `docs/SOLUÇÃOCOMPLETAINTEGRADA-RAIOXAI+JOTFORM.md`

### Estrutura do Projeto

```
raiox-clip-staging/
├── app/                    # Aplicação principal FastAPI
│   ├── main.py            # Endpoint principal da API
│   ├── analise_tracker.py # Rastreamento de análises
│   ├── models/            # Modelos de dados
│   ├── schemas/           # Schemas Pydantic
│   └── db/                # Configuração do banco
├── scripts/               # Scripts de automação
│   ├── agendador_verificador_raioxapi.py
│   ├── agendador_verificador_raioxapi_integrado.py
│   ├── verificador_resultados_raioxapi.py
│   ├── verificador_resultados_clip_real.py
│   └── verificador_clip_real.py
├── config/                # Arquivos de configuração
│   ├── raiox-api.service
│   ├── raiox-app.service
│   └── raioxapi-verificador.service
├── docs/                  # Documentação
│   ├── mapeamento_servidor_staging.md
│   ├── SOLUÇÃOCOMPLETAINTEGRADA-RAIOXAI+JOTFORM.md
│   └── [outros manuais]
└── logs/                  # Logs da aplicação
```

### Configuração e Deployment

#### Pré-requisitos

- Python 3.11+
- PostgreSQL com extensão pgvector
- CUDA (para processamento CLIP)
- Nginx (proxy reverso)

#### Instalação

```bash
# Clonar repositório
git clone https://github.com/cristianosiqueirapires/raiox-clip-staging.git
cd raiox-clip-staging

# Instalar dependências
pip install -r requirements.txt

# Configurar ambiente
cp .env.backup .env
# Editar .env com suas configurações

# Executar setup
chmod +x setup.sh
./setup.sh
```

#### Serviços Systemd

```bash
# Copiar arquivos de serviço
sudo cp config/*.service /etc/systemd/system/

# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar e iniciar serviços
sudo systemctl enable raiox-app.service
sudo systemctl enable raiox-api.service
sudo systemctl enable raioxapi-verificador.service

sudo systemctl start raiox-app.service
sudo systemctl start raiox-api.service
sudo systemctl start raioxapi-verificador.service
```

### Monitoramento e Logs

#### Verificação de Status

```bash
# Status dos serviços
sudo systemctl status raiox-app.service
sudo systemctl status raiox-api.service
sudo systemctl status raioxapi-verificador.service

# Logs em tempo real
sudo journalctl -u raiox-app.service -f
sudo journalctl -u raioxapi-verificador.service -f
```

#### Scripts de Verificação

```bash
# Executar verificação manual
python scripts/verificador_resultados_raioxapi.py

# Verificação com imagens reais
python scripts/verificador_clip_real.py

# Agendador (executado automaticamente via systemd)
python scripts/agendador_verificador_raioxapi.py
```

### Atualizações Recentes

#### 13/06/2025
- ✅ Adicionados novos scripts de agendamento e verificação
- ✅ Integração completa com JotForm implementada
- ✅ Serviços systemd configurados e testados
- ✅ Documentação atualizada com novos recursos
- ✅ Backup completo do servidor staging realizado

#### Próximos Passos
- 🔄 Migração para Terraform (Infrastructure as Code)
- 🔄 Implementação de CI/CD automatizado
- 🔄 Monitoramento avançado com alertas
- 🔄 Testes de carga e performance

### Suporte e Manutenção

Para questões técnicas ou suporte:
- Consulte a documentação em `docs/`
- Verifique logs em `logs/app.log`
- Execute scripts de verificação em `scripts/`

### Segurança

- Todas as credenciais estão em arquivos `.env` (não versionados)
- Acesso SSH configurado com chaves públicas
- Serviços executam com usuários específicos
- Logs rotacionados automaticamente

---

**Nota:** Este é um backup de segurança do servidor staging. Para deployment em produção, consulte a documentação específica de produção.

