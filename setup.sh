#!/bin/bash

# Script de instalação e configuração do ambiente para o Raiox AI FastAPI
# Autor: Manus AI
# Data: Junho 2025

# Atualizar o sistema
apt update && apt upgrade -y

# Instalar dependências básicas
apt install -y python3-pip python3-venv postgresql postgresql-contrib nginx

# Criar diretório para a aplicação
mkdir -p /opt/raiox-app/logs
mkdir -p /opt/raiox-app/static
mkdir -p /opt/raiox-app/app/models
mkdir -p /opt/raiox-app/app/schemas
mkdir -p /opt/raiox-app/app/db
mkdir -p /opt/raiox-app/app/core
mkdir -p /opt/raiox-app/app/services
mkdir -p /opt/raiox-app/app/utils

# Criar ambiente virtual Python
cd /opt/raiox-app
python3 -m venv venv
source venv/bin/activate

# Instalar dependências Python
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv pgvector torch clip boto3 pillow

# Copiar arquivos da aplicação
echo "Copiando arquivos da aplicação..."
# (Aqui você deve copiar os arquivos do diretório atual para os diretórios apropriados)

# Configurar o serviço systemd
cp config/raiox-api.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable raiox-api
systemctl start raiox-api

# Configurar Nginx (opcional)
cp config/nginx-raiox-api /etc/nginx/sites-available/raiox-api
ln -sf /etc/nginx/sites-available/raiox-api /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

echo "Instalação concluída! O serviço Raiox AI FastAPI está rodando na porta 8000."
echo "Acesse a documentação em: http://seu-ip:8000/docs"
