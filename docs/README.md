# Raiox AI FastAPI - README

## Visão Geral

Este pacote contém todos os arquivos necessários para implementar a arquitetura FastAPI do projeto Raiox AI. A API permite o processamento de imagens de raio-X usando o modelo CLIP para encontrar implantes similares.

## Estrutura do Projeto

```
/opt/raiox-app/
├── app/
│   ├── __init__.py
│   ├── main.py            # Arquivo principal da aplicação FastAPI
│   ├── models/            # Modelos SQLAlchemy
│   │   ├── __init__.py
│   │   └── implant.py
│   ├── schemas/           # Schemas Pydantic
│   │   ├── __init__.py
│   │   ├── implant.py
│   │   └── webhook.py
│   ├── db/                # Configuração do banco de dados
│   │   ├── __init__.py
│   │   └── session.py
│   ├── core/              # Configurações centrais
│   ├── services/          # Serviços
│   └── utils/             # Utilitários
├── venv/                  # Ambiente virtual Python
├── logs/                  # Logs da aplicação
└── static/                # Arquivos estáticos
```

## Requisitos

- Python 3.11+
- PostgreSQL com extensão pgvector
- Nginx (opcional, para proxy reverso)

## Instalação

1. Clone este repositório ou extraia o arquivo zip
2. Execute o script de instalação:

```bash
sudo bash setup.sh
```

O script irá:
- Atualizar o sistema
- Instalar dependências necessárias
- Configurar o ambiente virtual Python
- Instalar pacotes Python necessários
- Configurar o serviço systemd
- Configurar o Nginx (opcional)

## Acesso à API

- Documentação Swagger: http://seu-ip:8000/docs
- Endpoint Healthcheck: http://seu-ip:8000/healthcheck

## Endpoints Principais

- `GET /healthcheck`: Verifica o status da API
- `POST /webhook`: Processa imagens a partir de URLs
- `POST /upload`: Processa imagens enviadas diretamente
- `GET /implants`: Lista implantes cadastrados
- `GET /implants/{implant_id}`: Obtém detalhes de um implante específico

## Solução de Problemas

Se encontrar problemas durante a instalação ou execução, verifique os logs:

```bash
journalctl -u raiox-api -n 100
```

## Documentação Adicional

Para mais detalhes sobre a implementação, consulte o arquivo `implementacao_raiox_fastapi.md` incluído neste pacote.
