# Manual Definitivo de Implementação do Raiox AI com FastAPI

## Versão 2.0 - Junho 2025

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
10. [Servidor Admin e Painel de Aprovação](#10-servidor-admin-e-painel-de-aprovação)
11. [Ambiente de Testes e Simulação](#11-ambiente-de-testes-e-simulação)
12. [API de Retorno para Jotform](#12-api-de-retorno-para-jotform)
13. [Segurança e Boas Práticas](#13-segurança-e-boas-práticas)
14. [Solução de Problemas Comuns](#14-solução-de-problemas-comuns)
15. [Referências e Recursos](#15-referências-e-recursos)

## 1. Arquitetura Geral

O Raiox AI é um sistema de análise de imagens de raio-X que utiliza o modelo CLIP para encontrar implantes similares em um banco de dados. A arquitetura completa é composta por:

- **API FastAPI Principal**: Recebe imagens via webhook ou upload direto, processa com CLIP e retorna implantes similares
- **Banco de Dados PostgreSQL**: Armazena implantes, embeddings vetoriais e resultados de análises
- **pgvector**: Extensão do PostgreSQL para busca de similaridade vetorial
- **CLIP**: Modelo de IA para extração de embeddings de imagens
- **DigitalOcean Spaces**: Armazenamento de imagens
- **Servidor Admin**: Painel administrativo para aprovação de casos pela Brenda
- **Ambiente de Testes**: Servidor dedicado para testes sem afetar a produção
- **API de Retorno**: Endpoint para enviar resultados de volta ao Jotform

### Diagrama de Fluxo Completo

```
Jotform (imagem) → FastAPI /webhook →
download Spaces → CLIP encode → pgvector query →
top-3 implantes → salvar em results → 
Painel Admin (aprovação) → API de Retorno → Jotform (cliente)
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

### Modelo de Dados Completo

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

-- Tabela de casos (submissões do Jotform)
CREATE TABLE cases (
    id SERIAL PRIMARY KEY,
    jotform_submission_id VARCHAR(255) UNIQUE,
    client_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de imagens de casos
CREATE TABLE case_images (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id) ON DELETE CASCADE,
    image_url TEXT
);

-- Tabela de resultados
CREATE TABLE results (
    id SERIAL PRIMARY KEY,
    case_image_id INTEGER REFERENCES case_images(id) ON DELETE CASCADE,
    implant_id INTEGER REFERENCES implants(id),
    similarity FLOAT,
    approved BOOLEAN DEFAULT FALSE,
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by VARCHAR(255)
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

### Modelos Adicionais para Casos e Resultados

Arquivo: `/opt/raiox-app/app/models/case.py`

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    jotform_submission_id = Column(String, unique=True, index=True)
    client_name = Column(String)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    images = relationship("CaseImage", back_populates="case", cascade="all, delete-orphan")

class CaseImage(Base):
    __tablename__ = "case_images"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"))
    image_url = Column(String)
    
    case = relationship("Case", back_populates="images")
    results = relationship("Result", back_populates="case_image", cascade="all, delete-orphan")

class Result(Base):
    __tablename__ = "results"
    
    id = Column(Integer, primary_key=True, index=True)
    case_image_id = Column(Integer, ForeignKey("case_images.id", ondelete="CASCADE"))
    implant_id = Column(Integer, ForeignKey("implants.id"))
    similarity = Column(Float)
    approved = Column(Boolean, default=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String, nullable=True)
    
    case_image = relationship("CaseImage", back_populates="results")
    implant = relationship("Implant")
```

Arquivo: `/opt/raiox-app/app/models/__init__.py`

```python
from .implant import Implant
from .case import Case, CaseImage, Result
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

Arquivo: `/opt/raiox-app/app/schemas/case.py`

```python
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class ResultBase(BaseModel):
    implant_id: int
    similarity: float

class ResultCreate(ResultBase):
    case_image_id: int

class ResultSchema(ResultBase):
    id: int
    approved: bool = False
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True

class CaseImageBase(BaseModel):
    image_url: str

class CaseImageCreate(CaseImageBase):
    case_id: int

class CaseImageSchema(CaseImageBase):
    id: int
    results: List[ResultSchema] = []

    class Config:
        orm_mode = True
        from_attributes = True

class CaseBase(BaseModel):
    jotform_submission_id: str
    client_name: Optional[str] = None
    status: str = "pending"

class CaseCreate(CaseBase):
    pass

class CaseSchema(CaseBase):
    id: int
    created_at: datetime
    images: List[CaseImageSchema] = []

    class Config:
        orm_mode = True
        from_attributes = True

class CaseApproveRequest(BaseModel):
    approved_by: str
    implant_ids: List[int]
```

Arquivo: `/opt/raiox-app/app/schemas/__init__.py`

```python
from .webhook import WebhookRequest
from .implant import ImplantSchema, ImplantBase, ImplantCreate
from .case import CaseSchema, CaseCreate, CaseImageSchema, ResultSchema, CaseApproveRequest
```

### Arquivo Principal (main.py)

Arquivo: `/opt/raiox-app/app/main.py`

```python
from app.schemas import ImplantSchema, WebhookRequest, CaseSchema, CaseApproveRequest
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
from datetime import datetime
from dotenv import load_dotenv
from pgvector.sqlalchemy import Vector

from app.models import Implant, Case, CaseImage, Result

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
        
        # Criar caso no banco de dados
        new_case = Case(
            jotform_submission_id=request.client_id,
            client_name=request.metadata.get("client_name") if request.metadata else None,
            status="pending"
        )
        db.add(new_case)
        db.flush()
        
        # Criar imagem do caso
        new_case_image = CaseImage(
            case_id=new_case.id,
            image_url=image_url
        )
        db.add(new_case_image)
        db.flush()
        
        # Salvar resultados
        for implant in similar_implants:
            new_result = Result(
                case_image_id=new_case_image.id,
                implant_id=implant["id"],
                similarity=implant.get("score", 0.0)
            )
            db.add(new_result)
        
        db.commit()
        
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

# Endpoint para listar casos pendentes
@app.get("/cases", response_model=List[CaseSchema])
def get_cases(status: str = "pending", skip: int = 0, limit: int = 20, db=Depends(get_db)):
    cases = db.query(Case).filter(Case.status == status).offset(skip).limit(limit).all()
    return cases

# Endpoint para obter um caso específico
@app.get("/cases/{case_id}", response_model=CaseSchema)
def get_case(case_id: int, db=Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso não encontrado")
    return case

# Endpoint para aprovar um caso
@app.post("/cases/{case_id}/approve", response_model=CaseSchema)
def approve_case(case_id: int, request: CaseApproveRequest, db=Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Caso não encontrado")
    
    # Atualizar status do caso
    case.status = "approved"
    
    # Atualizar resultados aprovados
    for image in case.images:
        for result in image.results:
            if result.implant_id in request.implant_ids:
                result.approved = True
                result.approved_at = datetime.now()
                result.approved_by = request.approved_by
    
    db.commit()
    
    # Enviar resultados para Jotform (implementado na seção 12)
    send_results_to_jotform(case.jotform_submission_id, request.implant_ids, db)
    
    return case

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
                SELECT id, name, manufacturer, image_url, embedding <-> :query_vector AS score
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
                    "image_url": row[3],
                    "score": float(row[4])
                })
            
            return implants
    except Exception as e:
        logger.error(f"Erro ao buscar implantes similares: {str(e)}")
        raise

# Função para enviar resultados para Jotform
def send_results_to_jotform(submission_id, implant_ids, db):
    try:
        # Obter detalhes dos implantes aprovados
        implants = []
        for implant_id in implant_ids:
            implant = db.query(Implant).filter(Implant.id == implant_id).first()
            if implant:
                implants.append(implant.to_dict())
        
        # Preparar dados para envio
        jotform_data = {
            "submissionID": submission_id,
            "status": "approved",
            "implants": implants
        }
        
        # Enviar para Jotform via API
        import requests
        jotform_api_key = os.getenv("JOTFORM_API_KEY")
        if not jotform_api_key:
            logger.warning("Jotform API key não encontrada, pulando envio de resultados")
            return
        
        headers = {
            "Content-Type": "application/json",
            "APIKEY": jotform_api_key
        }
        
        response = requests.post(
            f"https://api.jotform.com/submission/{submission_id}",
            json=jotform_data,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Erro ao enviar resultados para Jotform: {response.status_code} - {response.text}")
        else:
            logger.info(f"Resultados enviados com sucesso para Jotform: {submission_id}")
    
    except Exception as e:
        logger.error(f"Erro ao enviar resultados para Jotform: {str(e)}")

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
> 5. Sempre salve os resultados no banco de dados para permitir aprovação posterior pelo painel admin.

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

## 10. Servidor Admin e Painel de Aprovação

Esta seção detalha a implementação do servidor admin separado que permite à Brenda visualizar e aprovar casos pendentes.

### Estrutura do Servidor Admin

```
/opt/raiox-admin/
├── app.py                # Aplicação Flask principal
├── templates/            # Templates HTML
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   └── case_detail.html
├── static/               # Arquivos estáticos
│   ├── css/
│   └── js/
├── venv/                 # Ambiente virtual Python
└── config.py             # Configurações
```

### Implementação do Painel Admin (Flask)

Arquivo: `/opt/raiox-admin/app.py`

```python
from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from functools import wraps

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "raiox-admin-secret")

# Configuração do banco de dados
DB_USER = os.getenv("DB_USER", "raiox_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Xc7!rA2v9Z@1pQ3y")
DB_NAME = os.getenv("DB_NAME", "raiox_db")
DB_HOST = os.getenv("DB_HOST", "localhost")

# Configuração da API principal
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Função para conectar ao banco de dados
def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    conn.cursor_factory = RealDictCursor
    return conn

# Decorator para verificar login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Por favor, faça login para acessar esta página', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Rota de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Verificação simples (em produção, use autenticação mais segura)
        if username == 'brenda' and password == os.getenv("ADMIN_PASSWORD", "raiox123"):
            session['user'] = username
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha incorretos', 'danger')
    
    return render_template('login.html')

# Rota de logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

# Rota principal - Dashboard
@app.route('/')
@login_required
def dashboard():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Buscar casos pendentes
    cur.execute("""
        SELECT c.id, c.jotform_submission_id, c.client_name, c.created_at, 
               COUNT(ci.id) as image_count
        FROM cases c
        LEFT JOIN case_images ci ON c.id = ci.case_id
        WHERE c.status = 'pending'
        GROUP BY c.id
        ORDER BY c.created_at DESC
    """)
    pending_cases = cur.fetchall()
    
    # Buscar casos aprovados recentemente
    cur.execute("""
        SELECT c.id, c.jotform_submission_id, c.client_name, c.created_at, 
               COUNT(ci.id) as image_count
        FROM cases c
        LEFT JOIN case_images ci ON c.id = ci.case_id
        WHERE c.status = 'approved'
        GROUP BY c.id
        ORDER BY c.created_at DESC
        LIMIT 5
    """)
    recent_approved = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('dashboard.html', 
                          pending_cases=pending_cases, 
                          recent_approved=recent_approved)

# Rota para detalhes do caso
@app.route('/case/<int:case_id>')
@login_required
def case_detail(case_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Buscar detalhes do caso
    cur.execute("""
        SELECT c.id, c.jotform_submission_id, c.client_name, c.status, c.created_at
        FROM cases c
        WHERE c.id = %s
    """, (case_id,))
    case = cur.fetchone()
    
    if not case:
        cur.close()
        conn.close()
        flash('Caso não encontrado', 'danger')
        return redirect(url_for('dashboard'))
    
    # Buscar imagens do caso
    cur.execute("""
        SELECT ci.id, ci.image_url
        FROM case_images ci
        WHERE ci.case_id = %s
    """, (case_id,))
    images = cur.fetchall()
    
    # Para cada imagem, buscar os resultados (implantes similares)
    for image in images:
        cur.execute("""
            SELECT r.id, r.similarity, r.approved, r.approved_at, r.approved_by,
                   i.id as implant_id, i.name, i.manufacturer, i.image_url
            FROM results r
            JOIN implants i ON r.implant_id = i.id
            WHERE r.case_image_id = %s
            ORDER BY r.similarity ASC
        """, (image['id'],))
        image['results'] = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('case_detail.html', case=case, images=images)

# Rota para aprovar um caso
@app.route('/case/<int:case_id>/approve', methods=['POST'])
@login_required
def approve_case(case_id):
    # Obter implantes selecionados
    selected_implants = request.form.getlist('selected_implants')
    
    if not selected_implants:
        flash('Selecione pelo menos um implante para aprovar', 'warning')
        return redirect(url_for('case_detail', case_id=case_id))
    
    # Converter para inteiros
    implant_ids = [int(implant_id) for implant_id in selected_implants]
    
    # Chamar API para aprovar o caso
    try:
        response = requests.post(
            f"{API_URL}/cases/{case_id}/approve",
            json={
                "approved_by": session['user'],
                "implant_ids": implant_ids
            }
        )
        
        if response.status_code == 200:
            flash('Caso aprovado com sucesso!', 'success')
        else:
            flash(f'Erro ao aprovar caso: {response.text}', 'danger')
    
    except Exception as e:
        flash(f'Erro ao aprovar caso: {str(e)}', 'danger')
    
    return redirect(url_for('case_detail', case_id=case_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### Configuração do Serviço para o Painel Admin

Arquivo: `/etc/systemd/system/raiox-admin.service`

```ini
[Unit]
Description=Raiox AI Admin Panel
After=network.target

[Service]
User=root
WorkingDirectory=/opt/raiox-admin
ExecStart=/opt/raiox-admin/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Lições Aprendidas
> **IMPORTANTE**: 
> 1. O servidor admin deve acessar o mesmo banco de dados que a API principal para visualizar os casos pendentes.
> 2. Implemente autenticação adequada para proteger o painel administrativo.
> 3. Use o endpoint de aprovação da API principal para manter a lógica de negócios centralizada.

## 11. Ambiente de Testes e Simulação

Esta seção detalha a implementação do ambiente de testes e as ferramentas para simulação de webhooks.

### Configuração do Ambiente de Testes

O ambiente de testes é uma réplica do ambiente de produção, mas com um banco de dados separado e configurado para permitir testes sem afetar dados reais.

```bash
# Criar banco de dados de teste
sudo -u postgres psql -c "CREATE DATABASE raiox_test OWNER raiox_user;"
sudo -u postgres psql -d raiox_test -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Configurar variáveis de ambiente para teste
cat > /opt/raiox-app/.env.test << 'EOT'
DB_USER=raiox_user
DB_PASSWORD=Xc7!rA2v9Z@1pQ3y
DB_NAME=raiox_test
DB_HOST=localhost

DO_SPACES_KEY=seu_key_aqui
DO_SPACES_SECRET=seu_secret_aqui
DO_SPACES_BUCKET=raiox-images-test
DO_SPACES_REGION=nyc3

TESTING=true
EOT
```

### Script para Simulação de Webhook

Arquivo: `/opt/raiox-app/test/simulate_webhook.py`

```python
import requests
import argparse
import json
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def simulate_webhook(image_url, client_id, api_url):
    """
    Simula uma chamada de webhook do Jotform para a API Raiox.
    """
    webhook_data = {
        "image_url": image_url,
        "client_id": client_id,
        "metadata": {
            "client_name": "Cliente de Teste",
            "submission_date": "2025-06-10"
        }
    }
    
    print(f"Enviando webhook para {api_url}/webhook")
    print(f"Dados: {json.dumps(webhook_data, indent=2)}")
    
    try:
        response = requests.post(
            f"{api_url}/webhook",
            json=webhook_data
        )
        
        print(f"Status: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2)}")
        
        return response.json()
    
    except Exception as e:
        print(f"Erro: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Simulador de Webhook Jotform para Raiox AI')
    parser.add_argument('--image', required=True, help='URL da imagem de raio-X')
    parser.add_argument('--client', default='test_client_001', help='ID do cliente')
    parser.add_argument('--api', default='http://localhost:8000', help='URL da API Raiox')
    
    args = parser.parse_args()
    
    simulate_webhook(args.image, args.client, args.api)

if __name__ == "__main__":
    main()
```

### Script para Testes com Imagens Reais

Arquivo: `/opt/raiox-app/test/test_real_images.py`

```python
import os
import glob
import requests
import json
import time
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def test_with_real_images(images_dir, api_url):
    """
    Testa a API com imagens reais de raio-X.
    """
    # Listar todas as imagens no diretório
    image_files = glob.glob(os.path.join(images_dir, "*.jpg")) + \
                 glob.glob(os.path.join(images_dir, "*.png"))
    
    print(f"Encontradas {len(image_files)} imagens para teste")
    
    results = []
    
    for image_file in image_files:
        print(f"\nTestando com imagem: {os.path.basename(image_file)}")
        
        # Fazer upload da imagem
        with open(image_file, 'rb') as f:
            files = {'file': (os.path.basename(image_file), f, 'image/jpeg')}
            
            try:
                response = requests.post(
                    f"{api_url}/upload",
                    files=files
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    implants = response.json()
                    print(f"Encontrados {len(implants)} implantes similares:")
                    for i, implant in enumerate(implants):
                        print(f"  {i+1}. {implant['name']} ({implant['manufacturer']})")
                    
                    results.append({
                        "image": os.path.basename(image_file),
                        "status": response.status_code,
                        "implants": implants
                    })
                else:
                    print(f"Erro: {response.text}")
                    results.append({
                        "image": os.path.basename(image_file),
                        "status": response.status_code,
                        "error": response.text
                    })
            
            except Exception as e:
                print(f"Erro: {str(e)}")
                results.append({
                    "image": os.path.basename(image_file),
                    "status": "error",
                    "error": str(e)
                })
            
            # Aguardar um pouco entre as requisições
            time.sleep(1)
    
    # Salvar resultados em um arquivo JSON
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nTestes concluídos. Resultados salvos em test_results.json")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Testes com imagens reais para Raiox AI')
    parser.add_argument('--dir', required=True, help='Diretório com imagens de teste')
    parser.add_argument('--api', default='http://localhost:8000', help='URL da API Raiox')
    
    args = parser.parse_args()
    
    test_with_real_images(args.dir, args.api)

if __name__ == "__main__":
    main()
```

### Lições Aprendidas
> **IMPORTANTE**: 
> 1. Sempre teste com imagens reais de raio-X para validar a precisão do modelo CLIP e a busca de similaridade.
> 2. Use um ambiente de testes separado para evitar afetar dados de produção.
> 3. Simule chamadas de webhook para testar o fluxo completo sem depender de submissões reais do Jotform.
> 4. Mantenha um conjunto de imagens de teste representativas para validar alterações no sistema.

## 12. API de Retorno para Jotform

Esta seção detalha a implementação da API de retorno para enviar resultados aprovados de volta ao Jotform.

### Configuração da API Jotform

Para integrar com o Jotform, você precisa:

1. Obter uma chave de API do Jotform
2. Configurar um webhook no Jotform para enviar submissões para sua API
3. Implementar a lógica para enviar resultados de volta ao Jotform

### Implementação da API de Retorno

A função `send_results_to_jotform` já foi incluída no arquivo `main.py` na seção 5. Aqui está um detalhamento adicional:

```python
def send_results_to_jotform(submission_id, implant_ids, db):
    try:
        # Obter detalhes dos implantes aprovados
        implants = []
        for implant_id in implant_ids:
            implant = db.query(Implant).filter(Implant.id == implant_id).first()
            if implant:
                implants.append({
                    "id": implant.id,
                    "name": implant.name,
                    "manufacturer": implant.manufacturer,
                    "type": implant.type,
                    "image_url": implant.image_url
                })
        
        # Preparar dados para envio
        jotform_data = {
            "submissionID": submission_id,
            "status": "approved",
            "implants": implants
        }
        
        # Enviar para Jotform via API
        import requests
        jotform_api_key = os.getenv("JOTFORM_API_KEY")
        if not jotform_api_key:
            logger.warning("Jotform API key não encontrada, pulando envio de resultados")
            return
        
        headers = {
            "Content-Type": "application/json",
            "APIKEY": jotform_api_key
        }
        
        # Método 1: Atualizar a submissão existente
        response = requests.post(
            f"https://api.jotform.com/submission/{submission_id}",
            json=jotform_data,
            headers=headers
        )
        
        # Método 2: Enviar para um webhook personalizado do Jotform
        webhook_url = os.getenv("JOTFORM_WEBHOOK_URL")
        if webhook_url:
            webhook_response = requests.post(
                webhook_url,
                json=jotform_data,
                headers=headers
            )
            
            if webhook_response.status_code != 200:
                logger.error(f"Erro ao enviar para webhook Jotform: {webhook_response.status_code} - {webhook_response.text}")
        
        if response.status_code != 200:
            logger.error(f"Erro ao enviar resultados para Jotform: {response.status_code} - {response.text}")
        else:
            logger.info(f"Resultados enviados com sucesso para Jotform: {submission_id}")
    
    except Exception as e:
        logger.error(f"Erro ao enviar resultados para Jotform: {str(e)}")
```

### Configuração das Variáveis de Ambiente

Adicione as seguintes variáveis ao arquivo `.env`:

```
JOTFORM_API_KEY=seu_api_key_aqui
JOTFORM_WEBHOOK_URL=https://webhook.site/seu-id-personalizado
```

### Lições Aprendidas
> **IMPORTANTE**: 
> 1. Teste a API de retorno com um webhook de teste (como webhook.site) antes de integrar com o Jotform real.
> 2. Implemente tratamento de erros robusto para lidar com falhas na comunicação com o Jotform.
> 3. Mantenha logs detalhados de todas as comunicações com o Jotform para depuração.
> 4. Considere implementar um mecanismo de retry para casos em que a comunicação com o Jotform falhe temporariamente.

## 13. Segurança e Boas Práticas

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

# Jotform
JOTFORM_API_KEY=seu_api_key_aqui
JOTFORM_WEBHOOK_URL=https://webhook.site/seu-id-personalizado
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

## 14. Solução de Problemas Comuns

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

### Erro: "Webhook não recebe imagens do Jotform"

**Soluções**:
1. Verificar se o webhook está configurado corretamente no Jotform
2. Verificar se a URL do webhook está acessível publicamente
3. Verificar logs do servidor para ver se as requisições estão chegando
4. Usar o script de simulação de webhook para testar a API

### Lição Aprendida
> **IMPORTANTE**: Sempre verifique os logs detalhados do serviço (`journalctl -u raiox-api -n 100`) para identificar a causa raiz de problemas.

## 15. Referências e Recursos

### Documentação Oficial

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [pgvector](https://github.com/pgvector/pgvector)
- [CLIP](https://github.com/openai/CLIP)
- [Pydantic](https://docs.pydantic.dev/)
- [Jotform API](https://api.jotform.com/docs/)

### Recursos Adicionais

- [Guia de Implementação Raiox AI](https://github.com/seu-usuario/raiox-ai-docs)
- [Exemplos de Código](https://github.com/seu-usuario/raiox-ai-examples)

---

## Conclusão

Este manual consolidou todo o conhecimento adquirido durante a implementação do projeto Raiox AI com FastAPI, incluindo as melhores práticas, soluções para problemas comuns e lições aprendidas. Seguindo este guia, você poderá implementar e manter o sistema de forma eficiente e robusta.

O sistema completo inclui:
1. API FastAPI principal para processamento de imagens e busca de similaridade
2. Banco de dados PostgreSQL com pgvector para armazenamento e busca vetorial
3. Servidor Admin para aprovação de casos pela Brenda
4. Ambiente de testes para validação sem afetar a produção
5. API de retorno para enviar resultados aprovados de volta ao Jotform

Para qualquer dúvida ou problema não coberto neste manual, consulte os logs detalhados do serviço e a documentação oficial das tecnologias utilizadas.

---

*Documento criado por Manus AI - Junho 2025*
