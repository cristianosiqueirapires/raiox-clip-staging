# Raiox AI - Diagrama de Arquitetura Completa

## 🏗️ VISÃO GERAL DA ARQUITETURA

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RAIOX AI ECOSYSTEM                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   JOTFORM       │    │  CLIP STAGING   │    │  POSTGRESQL     │
│                 │    │                 │    │                 │
│ 📋 Formulário   │───▶│ 🤖 FastAPI      │───▶│ 🗄️ Database     │
│ 🖼️ Upload       │    │ 🧠 CLIP ViT-B32 │    │ 📊 pgvector     │
│ 📤 Webhook      │    │ 🔄 Processamento│    │ 💾 32 Implantes │
│                 │    │                 │    │                 │
│ URL: form.jot.. │    │ IP: 45.55.128.. │    │ IP: 159.65.183..│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │ DIGITALOCEAN    │              │
         │              │ SPACES          │              │
         │              │                 │              │
         │              │ 🗂️ Armazenamento│              │
         │              │ 📁 clientes/    │              │
         │              │ 📁 referencia/  │              │
         │              │ 🌐 CDN Global   │              │
         │              │                 │              │
         │              │ URL: raiox-img..│              │
         │              └─────────────────┘              │
         │                                               │
         └─────────────────────────────────────────────────┘
```

## 🖥️ SERVIDORES E COMPONENTES

### 1. SERVIDOR CLIP STAGING
**IP:** `45.55.128.141`  
**Função:** Processamento principal e API  
**Tecnologias:**
- Ubuntu 22.04
- Python 3.11
- FastAPI + Uvicorn
- CLIP (ViT-B-32)
- Torch + OpenCLIP

**Endpoints:**
- `GET /healthcheck` - Status do sistema
- `POST /upload` - Upload direto de imagens
- `POST /webhook` - Webhook genérico
- `POST /jotform` - **Webhook específico Jotform**
- `GET /implants` - Listar implantes
- `GET /docs` - Documentação Swagger

**Serviços:**
- `raiox-api.service` (systemd)
- Porta 8000
- Auto-restart habilitado

### 2. SERVIDOR POSTGRESQL
**IP:** `159.65.183.73`  
**Função:** Banco de dados e busca vetorial  
**Tecnologias:**
- Ubuntu 22.04
- PostgreSQL 14
- pgvector extension
- psycopg2

**Banco de Dados:**
- **Nome:** `raiox`
- **Usuário:** `raiox_user`
- **Tabela principal:** `implants`
- **Registros:** 32 implantes reais

**Estrutura da Tabela:**
```sql
CREATE TABLE implants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    manufacturer VARCHAR(255),
    type VARCHAR(255),
    image_url TEXT,
    embedding vector(512)
);
```

### 3. DIGITALOCEAN SPACES
**URL:** `https://raiox-images.nyc3.digitaloceanspaces.com`  
**Função:** Armazenamento de imagens  
**Tecnologias:**
- S3-compatible storage
- CDN global
- Boto3 integration

**Estrutura de Pastas:**
```
raiox-images/
├── clientes/           # Imagens enviadas via Jotform
│   └── {email_id}/     # Organizadas por cliente
├── referencia/         # Imagens de referência dos 32 implantes
├── uploads/            # Uploads diretos via API
└── raiox-imagens/      # Imagens históricas
```

### 4. JOTFORM
**URL:** `https://form.jotform.com/251488352368668`  
**Função:** Interface de entrada  
**Configuração:**
- Webhook URL: `http://45.55.128.141:8000/jotform`
- Método: POST
- Formato: multipart/form-data

**Campos do Formulário:**
- `file` - Arquivo de imagem (obrigatório)
- `nome` - Nome do dentista
- `email` - Email do dentista
- `paciente` - Nome do paciente
- `dente` - Número do dente

## 🔄 FLUXO DE DADOS COMPLETO

### FLUXO PRINCIPAL (Jotform → Resultado)
```
1. 👨‍⚕️ DENTISTA
   ├── Acessa formulário Jotform
   ├── Preenche dados (nome, email, paciente, dente)
   ├── Faz upload da imagem de raio-x
   └── Submete formulário

2. 📋 JOTFORM
   ├── Recebe dados do formulário
   ├── Envia via webhook POST para CLIP Staging
   └── Formato: multipart/form-data

3. 🤖 CLIP STAGING (FastAPI)
   ├── Endpoint /jotform recebe requisição
   ├── Valida se arquivo é imagem
   ├── Cria client_id baseado no email
   ├── Faz upload para DigitalOcean Spaces
   ├── Processa imagem com CLIP (ViT-B-32)
   ├── Gera embedding 512D
   ├── Consulta PostgreSQL para implantes similares
   └── Retorna JSON com resultados

4. 🗄️ POSTGRESQL
   ├── Recebe query com embedding
   ├── Executa busca de similaridade (pgvector)
   ├── Calcula distância do cosseno
   ├── Retorna top 3 implantes mais similares
   └── Inclui metadados (nome, fabricante, URL)

5. 📤 RESPOSTA
   ├── JSON estruturado com implantes similares
   ├── Cada implante inclui: id, name, manufacturer, image_url
   └── Status 200 para sucesso
```

### FLUXO DE ARMAZENAMENTO
```
IMAGEM ORIGINAL (Jotform)
         ↓
VALIDAÇÃO (FastAPI)
         ↓
UPLOAD (DigitalOcean Spaces)
         ↓
PROCESSAMENTO (CLIP)
         ↓
EMBEDDING (512 dimensões)
         ↓
BUSCA (PostgreSQL + pgvector)
         ↓
RESULTADO (JSON)
```

## 🔧 INTEGRAÇÕES E CONEXÕES

### CONEXÕES DE REDE
```
Jotform ──HTTP POST──▶ CLIP Staging:8000
                            │
                            ├──TCP:5432──▶ PostgreSQL
                            │
                            └──HTTPS──▶ DigitalOcean Spaces
```

### AUTENTICAÇÃO E SEGURANÇA
- **PostgreSQL:** Usuário/senha específico (`raiox_user`)
- **DigitalOcean Spaces:** Access Key + Secret Key
- **FastAPI:** CORS habilitado para todos os origins
- **SSH:** Chaves públicas configuradas para acesso

### DEPENDÊNCIAS CRÍTICAS
```
CLIP Staging depende de:
├── PostgreSQL (busca de similaridade)
├── DigitalOcean Spaces (armazenamento)
└── Modelo CLIP (processamento)

PostgreSQL depende de:
├── pgvector extension
└── Dados dos 32 implantes

DigitalOcean Spaces depende de:
└── Credenciais AWS S3 compatíveis
```

## 📊 DADOS E VOLUMES

### BASE DE DADOS
- **32 implantes** de referência
- **4 fabricantes:** Nobel Biocare, Straumann, Neodent, Zimmer
- **8 implantes por fabricante**
- **Embeddings 512D** para cada implante

### ARMAZENAMENTO
- **DigitalOcean Spaces:** 3.8 MB, 105 items
- **PostgreSQL:** ~50MB (dados + índices)
- **Modelo CLIP:** ~350MB em memória

### PERFORMANCE
- **Tempo de resposta:** 20-40 segundos
- **Throughput:** 1-2 requisições simultâneas
- **Memória:** ~1GB por processo FastAPI
- **CPU:** Picos durante processamento CLIP

## 🚀 ESCALABILIDADE E FUTURO

### PRÓXIMAS EXPANSÕES
```
FASE 3: SISTEMA ADMIN
├── Interface web de gerenciamento
├── Dashboard com métricas
├── CRUD de implantes
└── Logs e monitoramento

FASE 4: OTIMIZAÇÕES
├── Cache de embeddings
├── GPU para CLIP
├── Load balancer
└── Backup automatizado
```

### PONTOS DE MELHORIA
1. **GPU para CLIP:** Reduzir tempo de processamento
2. **Cache Redis:** Evitar reprocessamento
3. **Load Balancer:** Distribuir carga
4. **Monitoring:** Prometheus + Grafana
5. **Backup:** Automatizado para PostgreSQL

## 🎯 RESUMO EXECUTIVO

### COMPONENTES PRINCIPAIS
- **3 servidores** (CLIP Staging, PostgreSQL, DigitalOcean Spaces)
- **1 interface** (Jotform)
- **4 tecnologias core** (FastAPI, CLIP, PostgreSQL, pgvector)

### CAPACIDADES ATUAIS
- ✅ **Processamento de imagens** com IA
- ✅ **Busca de similaridade** vetorial
- ✅ **Armazenamento escalável** na nuvem
- ✅ **Interface web** para dentistas
- ✅ **API REST** completa

### STATUS OPERACIONAL
- 🟢 **CLIP Staging:** Funcionando 100%
- 🟢 **PostgreSQL:** Funcionando 100%
- 🟢 **DigitalOcean Spaces:** Funcionando 100%
- 🟢 **Webhook Jotform:** Funcionando 100%

**SISTEMA COMPLETO E OPERACIONAL PARA PRODUÇÃO** ✅

