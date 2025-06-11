# Raiox AI - CLIP Staging Server

## 🎯 VISÃO GERAL

Sistema de processamento de imagens de raio-x dentário usando CLIP (Contrastive Language-Image Pre-training) para identificação e busca de similaridade de implantes dentários. Este repositório contém o código do servidor de staging que processa imagens e retorna implantes similares através de busca vetorial.

## 🏗️ ARQUITETURA

### Servidor CLIP Staging
- **IP:** 45.55.128.141
- **Porta:** 8000
- **Tecnologia:** FastAPI + CLIP ViT-B-32
- **Função:** Processamento principal e API

### Componentes Integrados
- **CLIP (ViT-B-32):** Processamento de imagens e geração de embeddings
- **PostgreSQL + pgvector:** Busca de similaridade vetorial (servidor separado)
- **DigitalOcean Spaces:** Armazenamento de imagens
- **Jotform:** Interface de entrada via webhook

## 🚀 FUNCIONALIDADES

### Endpoints Disponíveis
- `GET /healthcheck` - Status do sistema
- `POST /upload` - Upload direto de imagens
- `POST /webhook` - Webhook genérico
- `POST /jotform` - **Webhook específico Jotform** ✨ **NOVO**
- `GET /implants` - Listar implantes
- `GET /implants/{id}` - Detalhes de implante específico
- `GET /docs` - Documentação Swagger

### Webhook Jotform (Implementação Recente)
**URL:** `http://45.55.128.141:8000/jotform`

**Campos Aceitos:**
- `file` (obrigatório) - Arquivo de imagem para análise
- `nome` (opcional) - Nome do dentista
- `email` (opcional) - Email do dentista
- `paciente` (opcional) - Nome do paciente
- `dente` (opcional) - Número do dente

**Fluxo de Processamento:**
1. Recebe imagem via formulário Jotform
2. Valida formato da imagem
3. Salva no DigitalOcean Spaces (`clientes/{email}/`)
4. Processa com CLIP (ViT-B-32)
5. Busca implantes similares no PostgreSQL
6. Retorna JSON com resultados

## 📊 BASE DE DADOS

### Implantes Disponíveis
- **Total:** 32 implantes reais
- **Fabricantes:** Nobel Biocare, Straumann, Neodent, Zimmer
- **Distribuição:** 8 implantes por fabricante
- **Embeddings:** 512 dimensões por implante

### Exemplo de Resposta
```json
[
  {
    "id": 2,
    "name": "Nobel Biocare Implant 2",
    "manufacturer": "Nobel Biocare",
    "type": null,
    "image_url": "https://raiox-images.nyc3.digitaloceanspaces.com/referencia/SEpl3TF2HXyV.webp"
  }
]
```

## 🔧 INSTALAÇÃO E CONFIGURAÇÃO

### Pré-requisitos
- Ubuntu 22.04
- Python 3.11
- PostgreSQL com pgvector
- DigitalOcean Spaces configurado

### Instalação Rápida
```bash
# Clonar repositório
git clone https://github.com/cristianosiqueirapires/raiox-clip-staging.git
cd raiox-clip-staging

# Executar script de setup
chmod +x setup.sh
./setup.sh

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas credenciais

# Iniciar serviço
systemctl start raiox-api
systemctl enable raiox-api
```

### Configuração do Serviço
O serviço é gerenciado via systemd:
```bash
# Status
systemctl status raiox-api

# Logs
journalctl -u raiox-api -f

# Reiniciar
systemctl restart raiox-api
```

## 📁 ESTRUTURA DO PROJETO

```
raiox-clip-staging/
├── app/                    # Código principal da aplicação
│   ├── main.py            # FastAPI app com todos os endpoints
│   ├── models/            # Modelos SQLAlchemy
│   ├── schemas/           # Schemas Pydantic
│   └── db/                # Configuração do banco
├── config/                # Configurações do sistema
│   ├── raiox-api.service  # Configuração systemd
│   └── nginx-raiox-api    # Configuração Nginx (opcional)
├── docs/                  # Documentação completa
│   ├── webhook_jotform_implementacao_definitiva.md
│   ├── webhook_jotform_final_report.md
│   ├── raiox_arquitetura_completa_diagrama.md
│   ├── manual-definitivo-raiox-ai-v2.md
│   └── ...
├── setup.sh              # Script de instalação
├── .env                  # Variáveis de ambiente
└── README.md             # Este arquivo
```

## 🧪 TESTES

### Teste Manual do Webhook Jotform
```python
import requests

url = "http://45.55.128.141:8000/jotform"
data = {
    'nome': 'Dr. Teste',
    'email': 'teste@effdental.com.br',
    'paciente': 'Paciente Teste',
    'dente': '16'
}

with open('imagem_teste.jpg', 'rb') as f:
    files = {'file': ('teste.jpg', f, 'image/jpeg')}
    response = requests.post(url, data=data, files=files, timeout=60)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Implantes encontrados: {len(result)}")
```

### Resultados Esperados
- **Status Code:** 200
- **Tempo de resposta:** 20-40 segundos
- **Implantes retornados:** 1-5 (dependendo da similaridade)
- **Formato:** JSON com array de implantes

## 🔍 TROUBLESHOOTING

### Problemas Comuns

#### Erro 500: Internal Server Error
```bash
# Verificar logs
journalctl -u raiox-api --since '5 minutes ago'

# Verificar sintaxe
cd /opt/raiox-app && python -m py_compile app/main.py
```

#### Endpoint não aparece em /docs
```bash
# Verificar se endpoint está antes do if __name__
grep -n "def jotform_webhook" app/main.py
grep -n "if __name__" app/main.py
```

#### Timeout na requisição
```bash
# Verificar recursos
top
free -h
df -h
```

### Comandos de Emergência
```bash
# Rollback para backup
cp app/main.py.backup_YYYYMMDD_HHMMSS app/main.py
systemctl restart raiox-api

# Verificação rápida
systemctl is-active raiox-api
curl -s http://localhost:8000/healthcheck
```

## 📈 PERFORMANCE

### Métricas Atuais
- **Memória:** ~1GB por processo
- **CPU:** Picos durante processamento CLIP
- **Throughput:** 1-2 requisições simultâneas
- **Modelo CLIP:** ~350MB em memória

### Otimizações Futuras
- [ ] GPU para processamento CLIP
- [ ] Cache de embeddings
- [ ] Load balancer
- [ ] Monitoramento com Prometheus

## 🔐 SEGURANÇA

### Configurações Atuais
- CORS habilitado para todos os origins
- Validação de tipos de arquivo
- Logs de auditoria
- Isolamento de dados por cliente

### Melhorias Planejadas
- [ ] Autenticação JWT
- [ ] Rate limiting
- [ ] Validação de origem
- [ ] Criptografia de dados sensíveis

## 🌐 INTEGRAÇÃO COM JOTFORM

### Configuração no Jotform
1. Acesse as configurações do formulário
2. Vá em Integrações → Webhooks
3. Configure URL: `http://45.55.128.141:8000/jotform`
4. Método: POST
5. Teste com uma imagem

### Campos do Formulário
O webhook aceita qualquer campo do formulário Jotform, mas os principais são:
- Campo de upload de arquivo (obrigatório)
- Nome do dentista
- Email do dentista
- Nome do paciente
- Número do dente

## 📚 DOCUMENTAÇÃO ADICIONAL

### Documentos Disponíveis
- **Implementação Definitiva:** `docs/webhook_jotform_implementacao_definitiva.md`
- **Relatório Final:** `docs/webhook_jotform_final_report.md`
- **Arquitetura Completa:** `docs/raiox_arquitetura_completa_diagrama.md`
- **Manual Definitivo:** `docs/manual-definitivo-raiox-ai-v2.md`
- **Melhorias Futuras:** `docs/melhorias-futuras-raiox-ai.md`

### Guias Específicos
- Implementação passo a passo do webhook
- Troubleshooting de problemas comuns
- Comandos de emergência e rollback
- Arquitetura completa do sistema
- Próximos passos e melhorias

## 🎯 STATUS ATUAL

### ✅ FUNCIONALIDADES IMPLEMENTADAS
- [x] Sistema CLIP funcionando 100%
- [x] Webhook Jotform operacional
- [x] Integração com PostgreSQL
- [x] Upload para DigitalOcean Spaces
- [x] Busca de similaridade vetorial
- [x] API REST completa
- [x] Documentação abrangente

### 🔄 PRÓXIMOS PASSOS
- [ ] Sistema Admin (Fase 3)
- [ ] Interface web de gerenciamento
- [ ] Dashboard com métricas
- [ ] Otimizações de performance
- [ ] Monitoramento avançado

## 🤝 CONTRIBUIÇÃO

### Como Contribuir
1. Fork do repositório
2. Criar branch para feature
3. Implementar mudanças
4. Testar localmente
5. Criar Pull Request

### Padrões de Código
- Python PEP 8
- Documentação em português
- Testes obrigatórios
- Logs estruturados

## 📞 SUPORTE

### Contato
- **Desenvolvedor:** Cristiano Siqueira Pires
- **Email:** cristianosiqueirapires@gmail.com
- **GitHub:** @cristianosiqueirapires

### Logs e Monitoramento
```bash
# Logs em tempo real
journalctl -u raiox-api -f

# Status do sistema
systemctl status raiox-api

# Verificar saúde
curl http://45.55.128.141:8000/healthcheck
```

---

## 🏆 CONQUISTAS RECENTES

### Webhook Jotform Implementado ✨
- **Data:** 11/06/2025
- **Status:** 100% Funcional
- **Teste:** Validado com sucesso
- **Documentação:** Completa e definitiva

### Problemas Resolvidos
- ✅ Erro de indentação no código
- ✅ Função CLIP não definida
- ✅ Endpoint não aparecendo em /docs
- ✅ Formato de dados do Jotform
- ✅ Integração com PostgreSQL

**SISTEMA COMPLETO E OPERACIONAL PARA PRODUÇÃO** 🚀

