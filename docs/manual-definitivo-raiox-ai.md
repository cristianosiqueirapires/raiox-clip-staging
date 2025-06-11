# Manual Definitivo de Implementação do Raiox AI com FastAPI

## Versão 1.0 - Junho 2025

Este manual consolida todo o conhecimento adquirido durante a implementação do projeto Raiox AI com FastAPI, incluindo as melhores práticas, soluções para problemas comuns e lições aprendidas. Este documento serve como referência definitiva para futuras implementações ou manutenções do sistema.

## Índice

1. [Arquitetura Geral](#1-arquitetura-geral)
2. [Ambiente e Dependências](#2-ambiente-e-dependências)
3. [Estrutura do Projeto](#3-estrutura-do-projeto)
4. [Banco de Dados e pgvector](#4-banco-de-dados-e-pgvector)
5. [Implementação da API FastAPI](#5-implementação-da-api-fastapi)
6. [Processamento de Imagens com CLIP](#6-processamento-de-imagens-com-clip)
7. [Configuração do Serviço](#7-configuração-do-serviço)
8. [Nginx e Acesso Externo](#8-nginx-e-acesso-externo)
9. [CI/CD e Automação](#9-cicd-e-automação)
10. [Segurança e Boas Práticas](#10-segurança-e-boas-práticas)
11. [Solução de Problemas Comuns](#11-solução-de-problemas-comuns)
12. [Referências e Recursos](#12-referências-e-recursos)

## 1. Arquitetura Geral

O Raiox AI é um sistema de análise de imagens de raio-X que utiliza o modelo CLIP para encontrar implantes similares em um banco de dados. A arquitetura é composta por:

- **API FastAPI**: Recebe imagens via webhook ou upload direto, processa com CLIP e retorna implantes similares
- **Banco de Dados PostgreSQL**: Armazena implantes, embeddings vetoriais e resultados de análises
- **pgvector**: Extensão do PostgreSQL para busca de similaridade vetorial
- **CLIP**: Modelo de IA para extração de embeddings de imagens
- **DigitalOcean Spaces**: Armazenamento de imagens

### Diagrama de Fluxo

```
Jotform (imagem) → FastAPI /webhook →
download Spaces → CLIP encode → pgvector query →
top-3 implantes → salvar em results → notificar usuário
```

## 2. Ambiente e Dependências

### Sistema Operacional
- Ubuntu 22.04 LTS

### Dependências Principais
- Python 3.11+
- PostgreSQL 14+ com extensão pgvector
- Nginx (opcional para proxy reverso)
- Pacotes Python essenciais:
  - fastapi
  - uvicorn
  - sqlalchemy
  - psycopg2-binary
  - pgvector
  - torch
  - clip
  - pydantic
  - python-dotenv

### Instalação do Ambiente

```bash
# Atualizar o sistema
apt update && apt upgrade -y

# Instalar dependências básicas
apt install -y python3.11 python3.11-venv python3-pip git nginx postgresql postgresql-contrib

# Criar ambiente virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependências Python
pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy psycopg2-binary pgvector torch clip pydantic python-dotenv
```

### Lição Aprendida
> **IMPORTANTE**: Sempre use tmux ou screen para sessões SSH longas. Isso evita que a instalação seja interrompida se a conexão SSH cair. Use `tmux new -s raiox` para iniciar uma sessão e `tmux attach -t raiox` para reconectar.

## 3. Estrutura do Projeto

A estrutura de diretórios recomendada é:

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

### Criação da Estrutura

```bash
# Criar diretórios
mkdir -p /opt/raiox-app/app/{models,schemas,db,core,services,utils} /opt/raiox-app/logs /opt/raiox-app/static

# Criar arquivos __init__.py
touch /opt/raiox-app/app/__init__.py
touch /opt/raiox-app/app/models/__init__.py
touch /opt/raiox-app/app/schemas/__init__.py
touch /opt/raiox-app/app/db/__init__.py
touch /opt/raiox-app/app/core/__init__.py
touch /opt/raiox-app/app/services/__init__.py
touch /opt/raiox-app/app/utils/__init__.py
```

## 4. Banco de Dados e pgvector

### Instalação do pgvector

```bash
# Instalar dependências
apt install -y build-essential postgresql-server-dev-14 git

# Instalar pgvector
git clone --branch v0.7.0 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
cd ..
rm -rf pgvector

# Habilitar a extensão no PostgreSQL
sudo -u postgres psql -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Configuração do Banco de Dados

```bash
# Criar usuário e banco de dados
sudo -u postgres psql -c "CREATE USER raiox_user WITH PASSWORD 'Xc7!rA2v9Z@1pQ3y';"
sudo -u postgres psql -c "CREATE DATABASE raiox_db OWNER raiox_user;"

# Habilitar a extensão pgvector no banco
sudo -u postgres psql -d raiox_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Modelo de Dados

```sql
-- Tabela de implantes
CREATE TABLE implants (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    manufacturer VARCHAR(255),
    type VARCHAR(255),
    image_url TEXT,
    embedding VECTOR(512)  -- Dimensão do vetor CLIP
);

-- Índice para busca vetorial
CREATE INDEX ON implants USING hnsw (embedding vector_cosine_ops);
```

### Configuração SQLAlchemy

Arquivo: `/opt/raiox-app/app/db/session.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Configuração do banco de dados PostgreSQL
DB_USER = os.getenv("DB_USER", "raiox_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Xc7!rA2v9Z@1pQ3y")
DB_NAME = os.getenv("DB_NAME", "raiox_db")
DB_HOST = os.getenv("DB_HOST", "localhost")

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Função para obter uma sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Arquivo: `/opt/raiox-app/app/db/__init__.py`

```python
from .session import get_db, Base, engine
```

### Modelo SQLAlchemy para Implant

Arquivo: `/opt/raiox-app/app/models/implant.py`

```python
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector
import numpy as np
from typing import List

from app.db.session import Base

class Implant(Base):
    __tablename__ = "implants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    manufacturer = Column(String)
    type = Column(String)
    image_url = Column(String)
    embedding = Column(Vector(512))  # Dimensão do vetor CLIP
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "manufacturer": self.manufacturer,
            "type": self.type,
            "image_url": self.image_url
        }
```

Arquivo: `/opt/raiox-app/app/models/__init__.py`

```python
from .implant import Implant
```

### Lição Aprendida
> **IMPORTANTE**: A extensão pgvector deve ser instalada no ambiente virtual Python E no PostgreSQL. Muitos erros ocorrem quando apenas um dos dois está instalado.

## 5. Implementação da API FastAPI

### Schemas Pydantic

Arquivo: `/opt/raiox-app/app/schemas/implant.py`

```python
from pydantic import BaseModel
from typing import Optional, List

class ImplantBase(BaseModel):
    name: str
    manufacturer: Optional[str] = None
    type: Optional[str] = None
    image_url: Optional[str] = None

class ImplantCreate(ImplantBase):
    pass

class ImplantSchema(ImplantBase):
    id: int

    class Config:
        orm_mode = True
        from_attributes = True  # Versão atualizada do orm_mode para Pydantic v2
```

Arquivo: `/opt/raiox-app/app/schemas/webhook.py`

```python
from pydantic import BaseModel
from typing import Optional

class WebhookRequest(BaseModel):
    image_url: str
    client_id: str
    metadata: Optional[dict] = None
```

Arquivo: `/opt/raiox-app/app/schemas/__init__.py`

```python
from .webhook import WebhookRequest
from .implant import ImplantSchema, ImplantBase, ImplantCreate
```

### Arquivo Principal (main.py)

Arquivo: `/opt/raiox-app/app/main.py`

```python
from app.schemas import ImplantSchema
from app.schemas import WebhookRequest
from app.db.session import get_db
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import logging
import boto3
from botocore.exceptions import NoCredentialsError
import torch
import clip
from PIL import Image
import io
import numpy as np
from dotenv import load_dotenv
from pgvector.sqlalchemy import Vector

from app.models import Implant

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/opt/raiox-app/logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("raiox-api")

# Configurar conexão com o banco de dados
DB_USER = os.getenv("DB_USER", "raiox_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Xc7!rA2v9Z@1pQ3y")
DB_NAME = os.getenv("DB_NAME", "raiox_db")
DB_HOST = os.getenv("DB_HOST", "localhost")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Configurar conexão com DigitalOcean Spaces
s3 = boto3.client(
    's3',
    endpoint_url=f"https://{os.getenv('DO_SPACES_REGION', 'nyc3')}.digitaloceanspaces.com",
    aws_access_key_id=os.getenv('DO_SPACES_KEY'),
    aws_secret_access_key=os.getenv('DO_SPACES_SECRET')
)

# Carregar modelo CLIP
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# Inicializar a aplicação FastAPI
app = FastAPI(
    title="Raiox AI API",
    description="API para processamento de imagens de raio-x e busca de implantes similares",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint de healthcheck
@app.get("/healthcheck")
def healthcheck():
    return {"status": "ok", "version": "1.0.0"}

# Endpoint para receber webhook
@app.post("/webhook", response_model=List[ImplantSchema])
async def webhook(request: WebhookRequest, db=Depends(get_db)):
    logger.info(f"Recebido webhook para cliente {request.client_id}")
    
    try:
        # Baixar imagem da URL
        import requests
        response = requests.get(request.image_url)
        if response.status_code != 200:
            logger.error(f"Erro ao baixar imagem da URL: {response.status_code}")
            raise HTTPException(status_code=400, detail="Não foi possível baixar a imagem da URL fornecida")
        
        image_data = response.content
        
        # Fazer upload para DigitalOcean Spaces
        object_name = f"uploads/{request.client_id}/{os.path.basename(request.image_url)}"
        try:
            s3.upload_fileobj(
                io.BytesIO(image_data),
                os.getenv('DO_SPACES_BUCKET', 'raiox-images'),
                object_name,
                ExtraArgs={'ACL': 'public-read'}
            )
            image_url = f"https://{os.getenv('DO_SPACES_BUCKET')}.{os.getenv('DO_SPACES_REGION')}.digitaloceanspaces.com/{object_name}"
        except NoCredentialsError:
            logger.error("Credenciais do DigitalOcean Spaces não encontradas")
            image_url = request.image_url
        
        # Processar imagem com CLIP
        image = Image.open(io.BytesIO(image_data))
        image_input = preprocess(image).unsqueeze(0).to(device)
        
        with torch.no_grad():
            image_features = model.encode_image(image_input)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            image_embedding = image_features.cpu().numpy()[0]
        
        # Buscar implantes similares
        similar_implants = find_similar_implants(image_embedding, db)
        
        # Converter para ImplantSchema
        result = []
        for implant in similar_implants:
            result.append(ImplantSchema(
                id=implant["id"],
                name=implant["name"],
                manufacturer=implant["manufacturer"],
                image_url=implant["image_url"]
            ))
        
        return result
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar webhook: {str(e)}")

# Endpoint para upload de imagem
@app.post("/upload", response_model=List[ImplantSchema])
async def upload_image(file: UploadFile = File(...), db=Depends(get_db)):
    logger.info(f"Recebido upload de imagem: {file.filename}")
    
    try:
        # Verificar tipo de arquivo
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem")
        
        # Ler conteúdo do arquivo
        image_data = await file.read()
        
        # Fazer upload para DigitalOcean Spaces
        object_name = f"uploads/manual/{file.filename}"
        try:
            s3.upload_fileobj(
                io.BytesIO(image_data),
                os.getenv('DO_SPACES_BUCKET', 'raiox-images'),
                object_name,
                ExtraArgs={'ACL': 'public-read'}
            )
            image_url = f"https://{os.getenv('DO_SPACES_BUCKET')}.{os.getenv('DO_SPACES_REGION')}.digitaloceanspaces.com/{object_name}"
        except NoCredentialsError:
            logger.error("Credenciais do DigitalOcean Spaces não encontradas")
            image_url = None
        
        # Processar imagem com CLIP
        image = Image.open(io.BytesIO(image_data))
        image_input = preprocess(image).unsqueeze(0).to(device)
        
        with torch.no_grad():
            image_features = model.encode_image(image_input)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            image_embedding = image_features.cpu().numpy()[0]
        
        # Buscar implantes similares
        similar_implants = find_similar_implants(image_embedding, db)
        
        # Converter para ImplantSchema
        result = []
        for implant in similar_implants:
            result.append(ImplantSchema(
                id=implant["id"],
                name=implant["name"],
                manufacturer=implant["manufacturer"],
                image_url=implant["image_url"]
            ))
        
        return result
    except Exception as e:
        logger.error(f"Erro ao processar upload de imagem: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar upload de imagem: {str(e)}")

# Endpoint para listar implantes
@app.get("/implants", response_model=List[ImplantSchema])
def get_implants(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, name, manufacturer, image_url
            FROM implants
            ORDER BY id
            LIMIT :limit OFFSET :skip
        """), {"skip": skip, "limit": limit})
        
        implants = []
        for row in result:
            implants.append(ImplantSchema(
                id=row[0],
                name=row[1],
                manufacturer=row[2],
                image_url=row[3]
            ))
        
        return implants

# Endpoint para obter um implante específico
@app.get("/implants/{implant_id}", response_model=ImplantSchema)
def get_implant(implant_id: int, db=Depends(get_db)):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, name, manufacturer, image_url
            FROM implants
            WHERE id = :id
        """), {"id": implant_id})
        
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Implante não encontrado")
        
        return ImplantSchema(
            id=row[0],
            name=row[1],
            manufacturer=row[2],
            image_url=row[3]
        )

# Função para fazer upload de arquivo para DigitalOcean Spaces
def upload_to_spaces(file_data, object_name):
    try:
        s3.upload_fileobj(
            io.BytesIO(file_data),
            os.getenv('DO_SPACES_BUCKET', 'raiox-images'),
            object_name,
            ExtraArgs={'ACL': 'public-read'}
        )
        return f"https://{os.getenv('DO_SPACES_BUCKET')}.{os.getenv('DO_SPACES_REGION')}.digitaloceanspaces.com/{object_name}"
    except Exception as e:
        logger.error(f"Erro ao enviar arquivo para Spaces: {str(e)}")
        raise

# Função para encontrar implantes similares
def find_similar_implants(query_vector, db, limit=3):
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, name, manufacturer, image_url
                FROM implants
                ORDER BY embedding <-> :query_vector
                LIMIT :limit
            """), {"query_vector": query_vector.tolist(), "limit": limit})
            
            implants = []
            for row in result:
                implants.append({
                    "id": row[0],
                    "name": row[1],
                    "manufacturer": row[2],
                    "image_url": row[3]
                })
            
            return implants
    except Exception as e:
        logger.error(f"Erro ao buscar implantes similares: {str(e)}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Lições Aprendidas
> **IMPORTANTE**: 
> 1. Sempre use `response_model=ImplantSchema` em vez de `response_model=Implant` nos endpoints FastAPI. O response_model deve ser um modelo Pydantic, não um modelo SQLAlchemy.
> 2. Certifique-se de que a função `get_db()` esteja corretamente definida e importada.
> 3. Verifique a ortografia correta de `sqlalchemy` (não `sqlFalchemy`).
> 4. Ao retornar objetos nos endpoints, converta-os explicitamente para o schema Pydantic correspondente.

## 6. Processamento de Imagens com CLIP

### Instalação do CLIP

```bash
pip install ftfy regex tqdm
pip install git+https://github.com/openai/CLIP.git
```

### Extração de Embeddings

```python
import torch
import clip
from PIL import Image

# Carregar modelo CLIP
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# Processar imagem
image = Image.open("caminho/para/imagem.jpg")
image_input = preprocess(image).unsqueeze(0).to(device)

# Extrair embedding
with torch.no_grad():
    image_features = model.encode_image(image_input)
    # Normalizar o vetor
    image_features /= image_features.norm(dim=-1, keepdim=True)
    # Converter para numpy array
    image_embedding = image_features.cpu().numpy()[0]
```

### Busca de Similaridade com pgvector

```python
# Usando SQLAlchemy
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa

# Consulta de similaridade
vec_param = sa.bindparam('v', value=list(query_vec), type_=Vector(512))
stmt = sa.text("""
    SELECT id, name, embedding <-> :v AS score
    FROM implants
    ORDER BY embedding <-> :v
    LIMIT 3
""").bindparams(v=vec_param)

# Executar consulta
result = conn.execute(stmt)
```

### Lição Aprendida
> **IMPORTANTE**: Para vetores normalizados (como os do CLIP), a distância do cosseno (`<->`) é a melhor escolha para busca de similaridade. O pgvector também suporta distância L2 (`<=>`) e produto interno (`<#>`).

## 7. Configuração do Serviço

### Arquivo de Serviço Systemd

Arquivo: `/etc/systemd/system/raiox-api.service`

```ini
[Unit]
Description=Raiox AI FastAPI Service
After=network.target

[Service]
User=root
WorkingDirectory=/opt/raiox-app
ExecStart=/opt/raiox-app/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### Ativação do Serviço

```bash
# Recarregar configurações do systemd
systemctl daemon-reload

# Habilitar o serviço para iniciar automaticamente
systemctl enable raiox-api

# Iniciar o serviço
systemctl start raiox-api

# Verificar status
systemctl status raiox-api
```

### Lição Aprendida
> **IMPORTANTE**: Certifique-se de que o diretório de trabalho (`WorkingDirectory`) e o caminho para o Python do ambiente virtual estejam corretos. Erros comuns incluem caminhos incorretos ou permissões insuficientes.

## 8. Nginx e Acesso Externo

### Configuração do Nginx

Arquivo: `/etc/nginx/sites-available/raiox-api`

```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/raiox-app/static;
    }
}
```

### Ativação da Configuração

```bash
# Criar link simbólico
ln -sf /etc/nginx/sites-available/raiox-api /etc/nginx/sites-enabled/

# Testar configuração
nginx -t

# Reiniciar Nginx
systemctl restart nginx
```

### Lição Aprendida
> **IMPORTANTE**: Se preferir manter o acesso direto pela porta 8000 (sem Nginx), certifique-se de que a porta esteja aberta no firewall: `ufw allow 8000/tcp`.

## 9. CI/CD e Automação

### GitHub Actions para Deploy Automático

Arquivo: `.github/workflows/deploy.yml`

```yaml
name: Deploy Raiox AI
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Production
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.HOST }}
          username: root
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/raiox-app
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            sudo systemctl restart raiox-api
```

### Configuração de Segredos no GitHub

1. No repositório GitHub, vá em Settings > Secrets and variables > Actions
2. Adicione os seguintes segredos:
   - `HOST`: IP do servidor
   - `SSH_KEY`: Conteúdo da chave SSH privada

### Lição Aprendida
> **IMPORTANTE**: Para automação completa, use tokens da DigitalOcean para criar e configurar servidores programaticamente, evitando problemas de conexão SSH manual. Configure tmux para manter sessões ativas mesmo com quedas de conexão.

## 10. Segurança e Boas Práticas

### Variáveis de Ambiente

Arquivo: `/opt/raiox-app/.env`

```
# Banco de dados
DB_USER=raiox_user
DB_PASSWORD=Xc7!rA2v9Z@1pQ3y
DB_NAME=raiox_db
DB_HOST=localhost

# DigitalOcean Spaces
DO_SPACES_KEY=seu_key_aqui
DO_SPACES_SECRET=seu_secret_aqui
DO_SPACES_BUCKET=raiox-images
DO_SPACES_REGION=nyc3
```

### Proteção de Dados Sensíveis

- Nunca versione arquivos `.env` ou credenciais
- Use `.gitignore` para excluir arquivos sensíveis
- Armazene segredos em GitHub Secrets ou gerenciadores de segredos

### Logging Estruturado

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/opt/raiox-app/logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("raiox-api")

# Uso
logger.info("Mensagem informativa")
logger.error("Erro: %s", str(erro))
```

### Lição Aprendida
> **IMPORTANTE**: Sempre use tratamento de exceções adequado e logging detalhado para facilitar a depuração de problemas em produção.

## 11. Solução de Problemas Comuns

### Erro: "ModuleNotFoundError: No module named 'pgvector'"

**Solução**: Instalar o pacote pgvector no ambiente virtual Python.

```bash
pip install pgvector
```

### Erro: "NameError: name 'get_db' is not defined"

**Solução**: Verificar se a função `get_db()` está definida e importada corretamente.

```python
from app.db.session import get_db
```

### Erro: "NameError: name 'WebhookRequest' is not defined"

**Solução**: Verificar se a classe `WebhookRequest` está definida e importada corretamente.

```python
from app.schemas import WebhookRequest
```

### Erro: "Invalid args for response field! Hint: check that <class 'app.models.implant.Implant'> is a valid Pydantic field type"

**Solução**: Usar `ImplantSchema` (modelo Pydantic) em vez de `Implant` (modelo SQLAlchemy) como response_model.

```python
@app.get("/implants", response_model=List[ImplantSchema])
```

### Erro: "ModuleNotFoundError: No module named 'typing_extensions'"

**Solução**: Instalar o pacote typing_extensions.

```bash
pip install typing_extensions
```

### Erro: "Connection refused" ao acessar a API

**Soluções**:
1. Verificar se o serviço está rodando: `systemctl status raiox-api`
2. Verificar se a porta está aberta: `netstat -tulpn | grep 8000`
3. Verificar logs: `journalctl -u raiox-api -n 100`
4. Verificar firewall: `ufw status`

### Lição Aprendida
> **IMPORTANTE**: Sempre verifique os logs detalhados do serviço (`journalctl -u raiox-api -n 100`) para identificar a causa raiz de problemas.

## 12. Referências e Recursos

### Documentação Oficial

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [pgvector](https://github.com/pgvector/pgvector)
- [CLIP](https://github.com/openai/CLIP)
- [Pydantic](https://docs.pydantic.dev/)

### Recursos Adicionais

- [Guia de Implementação Raiox AI](https://github.com/seu-usuario/raiox-ai-docs)
- [Exemplos de Código](https://github.com/seu-usuario/raiox-ai-examples)

---

## Conclusão

Este manual consolidou todo o conhecimento adquirido durante a implementação do projeto Raiox AI com FastAPI, incluindo as melhores práticas, soluções para problemas comuns e lições aprendidas. Seguindo este guia, você poderá implementar e manter o sistema de forma eficiente e robusta.

Para qualquer dúvida ou problema não coberto neste manual, consulte os logs detalhados do serviço e a documentação oficial das tecnologias utilizadas.

---

*Documento criado por Manus AI - Junho 2025*
