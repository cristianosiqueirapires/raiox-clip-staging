# Raiox AI - CLIP Staging Server

## 🎯 Versão Atual Funcionando (11/06/2025)

Este repositório contém a versão **100% funcional** do servidor CLIP Staging do sistema Raiox AI.

### ✅ Status Validado
- **FastAPI funcionando** com processamento CLIP
- **Busca de similaridade** implementada e testada
- **PostgreSQL integrado** com pgvector
- **Upload para DigitalOcean Spaces** configurado
- **32 implantes reais** inseridos no banco de dados

### 🏗️ Arquitetura

```
/opt/raiox-app/
├── app/
│   ├── main.py          # API principal com correções aplicadas
│   ├── models/          # Modelos SQLAlchemy
│   ├── schemas/         # Schemas Pydantic
│   ├── db/              # Configuração do banco
│   └── core/            # Configurações centrais
├── config/              # Arquivos de configuração
├── logs/                # Logs do sistema
├── .env                 # Variáveis de ambiente
└── setup.sh             # Script de instalação
```

### 🔧 Principais Correções Aplicadas

#### 1. Função find_similar_implants
**PROBLEMA RESOLVIDO:** Função retornava lista vazia hardcoded
```python
def find_similar_implants(query_vector, db, limit=3):
    """Busca implantes similares usando pgvector"""
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host="159.65.183.73",
            database="raiox",
            user="raiox_user", 
            password="Xc7!rA2v9Z@1pQ3y"
        )
        
        cur = conn.cursor()
        vector_str = '[' + ','.join(map(str, query_vector.tolist())) + ']'
        
        cur.execute("""
            SELECT id, name, manufacturer, image_url
            FROM implants
            ORDER BY embedding <-> %s::vector
            LIMIT %s
        """, (vector_str, limit))
        
        rows = cur.fetchall()
        implants = []
        for row in rows:
            implants.append({
                "id": row[0],
                "name": row[1], 
                "manufacturer": row[2],
                "type": None,
                "image_url": row[3]
            })
        
        cur.close()
        conn.close()
        
        logger.info(f"Encontrados {len(implants)} implantes similares")
        return implants
        
    except Exception as e:
        logger.error(f"Erro na busca de implantes similares: {str(e)}")
        return []
```

#### 2. Permissões PostgreSQL
**PROBLEMA RESOLVIDO:** `permission denied for table implants`
```sql
GRANT SELECT ON implants TO raiox_user;
```

#### 3. Problemas SQL Recorrentes
- ✅ **Erro `%%` duplicados**: Resolvido usando psycopg2 direto
- ✅ **Erro `vector <-> numeric[]`**: Cast `::vector` aplicado
- ✅ **Sintaxe `:parameter`**: Substituído por `%s` do psycopg2

### 🧪 Teste de Validação

```bash
curl -H "X-Client-ID: test123" \
     -F "file=@imagem.jpg" \
     http://45.55.128.141:8000/upload
```

**Resposta Esperada:**
```json
[
  {
    "name": "Nobel Biocare Implant 2",
    "manufacturer": "Nobel Biocare",
    "type": null,
    "image_url": "https://raiox-images.nyc3.digitaloceanspaces.com/referencia/SEpl3TF2HXyV.webp",
    "id": 2
  },
  {
    "name": "Nobel Biocare Implant 3", 
    "manufacturer": "Nobel Biocare",
    "type": null,
    "image_url": "https://raiox-images.nyc3.digitaloceanspaces.com/referencia/d9u8TrHn4Xqr.webp",
    "id": 3
  },
  {
    "name": "Nobel Biocare Implant 1",
    "manufacturer": "Nobel Biocare", 
    "type": null,
    "image_url": "https://raiox-images.nyc3.digitaloceanspaces.com/referencia/M7ZMEtGI2liC.jpg",
    "id": 1
  }
]
```

### 📊 Dados Inseridos

**32 implantes reais** organizados por fabricante:
- **Nobel Biocare**: 8 implantes (Replace, N1, All-on-4, etc.)
- **Straumann**: 8 implantes (BLX, TLX, BL, etc.)
- **Neodent**: 8 implantes (Grand Morse, Drive, etc.)
- **Zimmer**: 8 implantes (TSV, Screw-Vent, etc.)

### 🔄 Serviços

```bash
# Status do serviço
systemctl status raiox-api

# Restart do serviço
systemctl restart raiox-api

# Logs em tempo real
journalctl -u raiox-api -f
```

### 🚨 Troubleshooting

Ver arquivo `TROUBLESHOOTING.md` para problemas comuns e soluções.

### 🔗 Servidores Relacionados

- **CLIP Staging**: 45.55.128.141 (este servidor)
- **PostgreSQL**: 159.65.183.73
- **CLIP Production**: 167.71.188.88

---

**Última atualização:** 11/06/2025  
**Status:** ✅ Sistema 100% funcional e validado

