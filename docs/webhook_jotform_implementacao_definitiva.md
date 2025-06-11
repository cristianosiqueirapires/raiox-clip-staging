# Webhook Jotform - Documentação Definitiva para Implementação

## 📋 ÍNDICE
1. [Visão Geral](#visão-geral)
2. [Problemas Encontrados e Soluções](#problemas-encontrados-e-soluções)
3. [Implementação Passo a Passo](#implementação-passo-a-passo)
4. [Checklist de Validação](#checklist-de-validação)
5. [Troubleshooting Guide](#troubleshooting-guide)
6. [Comandos de Emergência](#comandos-de-emergência)

---

## 🎯 VISÃO GERAL

### Objetivo
Implementar endpoint `/jotform` no servidor CLIP Staging para receber dados de formulário Jotform, processar imagens de raio-x com CLIP e retornar implantes similares do PostgreSQL.

### Arquitetura
```
Jotform → FastAPI (/jotform) → CLIP → PostgreSQL → JSON Response
    ↓
DigitalOcean Spaces
```

### Servidor Alvo
- **IP:** 45.55.128.141
- **Serviço:** raiox-api
- **Porta:** 8000
- **Endpoint:** `/jotform`

---

## 🚨 PROBLEMAS ENCONTRADOS E SOLUÇÕES

### PROBLEMA 1: Erro de Indentação (IndentationError)
**Sintoma:**
```
IndentationError: unexpected indent (main.py, line 374)
```

**Causa:**
- Código do endpoint `/jotform` foi inserido após o bloco `if __name__ == "__main__":`
- Estrutura do arquivo corrompida durante edição

**Solução Definitiva:**
```bash
# 1. Criar backup
cp /opt/raiox-app/app/main.py /opt/raiox-app/app/main.py.backup_$(date +%Y%m%d_%H%M%S)

# 2. Separar arquivo em partes
head -370 /opt/raiox-app/app/main.py > /tmp/main_part1.py
tail -n +374 /opt/raiox-app/app/main.py > /tmp/main_part2.py

# 3. Reorganizar estrutura
cat /tmp/main_part1.py > /opt/raiox-app/app/main_fixed.py
cat /tmp/jotform_endpoint.py >> /opt/raiox-app/app/main_fixed.py

# 4. Verificar sintaxe
cd /opt/raiox-app && source venv/bin/activate && python -m py_compile app/main_fixed.py

# 5. Substituir arquivo
mv /opt/raiox-app/app/main.py /opt/raiox-app/app/main.py.broken
mv /opt/raiox-app/app/main_fixed.py /opt/raiox-app/app/main.py
```

**Prevenção:**
- SEMPRE verificar sintaxe antes de reiniciar serviço
- SEMPRE criar backup antes de editar
- NUNCA inserir código após `if __name__ == "__main__"`

### PROBLEMA 2: Função CLIP Não Definida
**Sintoma:**
```
"Erro no processamento: name 'process_image_with_clip' is not defined"
```

**Causa:**
- Endpoint `/jotform` chamava função `process_image_with_clip()` que não existe
- Função correta é `process_image()` que já estava implementada

**Solução Definitiva:**
```bash
# 1. Backup
cp /opt/raiox-app/app/main.py /opt/raiox-app/app/main.py.backup_$(date +%Y%m%d_%H%M%S)

# 2. Correção
sed -i 's/query_vector = process_image_with_clip(image_pil)/query_vector = process_image(image_data)/' /opt/raiox-app/app/main.py

# 3. Verificar correção
grep -A 3 -B 3 'query_vector = process_image' /opt/raiox-app/app/main.py
```

**Prevenção:**
- Verificar nomes de funções existentes antes de usar
- Usar `grep -n "def.*"` para listar todas as funções
- Testar endpoint após cada alteração

### PROBLEMA 3: Endpoint Não Aparece na Documentação
**Sintoma:**
- Endpoint existe no código mas não aparece em `/docs`
- OpenAPI JSON não lista o endpoint

**Causa:**
- Erro de sintaxe impede FastAPI de carregar endpoint
- Estrutura de arquivo corrompida

**Solução Definitiva:**
```bash
# 1. Verificar sintaxe
cd /opt/raiox-app && source venv/bin/activate && python -m py_compile app/main.py

# 2. Se erro, corrigir estrutura (ver PROBLEMA 1)

# 3. Verificar se endpoint aparece
curl -s http://localhost:8000/openapi.json | grep -o 'jotform'
```

**Prevenção:**
- SEMPRE verificar `/docs` após implementar endpoint
- SEMPRE testar sintaxe antes de reiniciar serviço

---

## 🔧 IMPLEMENTAÇÃO PASSO A PASSO

### PASSO 1: Preparação
```bash
# Conectar no servidor
ssh root@45.55.128.141

# Verificar status do serviço
systemctl status raiox-api --no-pager

# Criar backup
cp /opt/raiox-app/app/main.py /opt/raiox-app/app/main.py.backup_$(date +%Y%m%d_%H%M%S)
```

### PASSO 2: Implementar Endpoint
Criar arquivo `/tmp/jotform_endpoint.py`:
```python
@app.post("/jotform", response_model=List[ImplantSchema])
async def jotform_webhook(
    file: UploadFile = File(...),
    nome: str = Form(None),
    email: str = Form(None),
    paciente: str = Form(None),
    dente: str = Form(None),
    db=Depends(get_db)
):
    """
    Endpoint para receber dados do formulário Jotform
    Aceita multipart/form-data com arquivo de imagem e metadados
    """
    try:
        logger.info(f"Recebendo dados do Jotform - arquivo: {file.filename}, email: {email}")
        
        # Validar se é uma imagem
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem")
        
        # Ler dados da imagem
        image_data = await file.read()
        
        # Criar client_id baseado no email ou usar valor padrão
        client_id = email.replace('@', '_').replace('.', '_') if email else "jotform_user"
        
        # Criar metadata com informações do formulário
        metadata = {
            "nome": nome,
            "email": email,
            "paciente": paciente,
            "dente": dente,
            "origem": "jotform"
        }
        
        # Fazer upload para DigitalOcean Spaces na pasta clientes
        object_name = f"clientes/{client_id}/{file.filename}"
        spaces_url = upload_to_spaces(io.BytesIO(image_data), object_name)
        
        if not spaces_url:
            raise HTTPException(status_code=500, detail="Erro no upload da imagem")
        
        logger.info(f"Imagem enviada para Spaces: {spaces_url}")
        
        # Processar imagem com CLIP
        query_vector = process_image(image_data)
        
        if query_vector is None:
            raise HTTPException(status_code=500, detail="Erro no processamento da imagem com CLIP")
        
        logger.info("Imagem processada com CLIP, buscando implantes similares...")
        
        # Buscar implantes similares no PostgreSQL
        similar_implants = find_similar_implants(query_vector, db)
        
        # Converter para ImplantSchema
        result = []
        for implant in similar_implants:
            if isinstance(implant, dict):
                result.append(ImplantSchema(**implant))
            else:
                result.append(ImplantSchema(
                    id=implant.id,
                    name=implant.name,
                    manufacturer=implant.manufacturer,
                    type=getattr(implant, 'type', None),
                    image_url=implant.image_url
                ))
        
        logger.info(f"Processamento Jotform concluído para {client_id} - Encontrados {len(result)} implantes similares")
        return result
    
    except Exception as e:
        logger.error(f"Erro no processamento do Jotform: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### PASSO 3: Integrar ao Código Principal
```bash
# Encontrar linha do if __name__
grep -n 'if __name__' /opt/raiox-app/app/main.py

# Separar arquivo (assumindo linha 371)
head -370 /opt/raiox-app/app/main.py > /tmp/main_part1.py

# Combinar arquivos
cat /tmp/main_part1.py > /opt/raiox-app/app/main_fixed.py
cat /tmp/jotform_endpoint.py >> /opt/raiox-app/app/main_fixed.py
```

### PASSO 4: Validar e Aplicar
```bash
# Verificar sintaxe
cd /opt/raiox-app && source venv/bin/activate && python -m py_compile app/main_fixed.py

# Se OK, aplicar
mv /opt/raiox-app/app/main.py /opt/raiox-app/app/main.py.old
mv /opt/raiox-app/app/main_fixed.py /opt/raiox-app/app/main.py

# Reiniciar serviço
systemctl restart raiox-api

# Aguardar inicialização (30 segundos)
sleep 30

# Verificar status
systemctl status raiox-api --no-pager
```

### PASSO 5: Validar Endpoint
```bash
# Verificar se endpoint aparece
curl -s http://localhost:8000/openapi.json | grep -o 'jotform'

# Deve retornar várias linhas com 'jotform'
```

---

## ✅ CHECKLIST DE VALIDAÇÃO

### Antes da Implementação
- [ ] Backup do arquivo main.py criado
- [ ] Serviço raiox-api funcionando
- [ ] PostgreSQL com 32 implantes populados
- [ ] DigitalOcean Spaces configurado

### Durante a Implementação
- [ ] Sintaxe do código verificada
- [ ] Arquivo reorganizado corretamente
- [ ] Função `process_image` sendo usada (não `process_image_with_clip`)
- [ ] Endpoint inserido ANTES do `if __name__ == "__main__"`

### Após a Implementação
- [ ] Serviço reiniciado sem erros
- [ ] Endpoint aparece no OpenAPI JSON
- [ ] Teste manual retorna Status 200
- [ ] JSON com implantes similares retornado
- [ ] Logs sem erros críticos

### Teste Manual
```bash
# Criar script de teste
cat > /tmp/test_jotform.py << 'EOF'
import requests

url = "http://45.55.128.141:8000/jotform"
data = {
    'nome': 'Dr. Teste',
    'email': 'teste@effdental.com.br',
    'paciente': 'Paciente Teste',
    'dente': '16'
}

with open('/path/to/test/image.jpg', 'rb') as f:
    files = {'file': ('test.jpg', f, 'image/jpeg')}
    response = requests.post(url, data=data, files=files, timeout=60)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Implantes encontrados: {len(result)}")
    else:
        print(f"Erro: {response.text}")
EOF

python3 /tmp/test_jotform.py
```

---

## 🔍 TROUBLESHOOTING GUIDE

### Erro 500: Internal Server Error
**Possíveis Causas:**
1. Função CLIP não definida
2. Erro de sintaxe no código
3. Problema de conexão com PostgreSQL
4. Problema de upload para Spaces

**Diagnóstico:**
```bash
# Verificar logs
journalctl -u raiox-api --since '5 minutes ago' --no-pager

# Verificar sintaxe
cd /opt/raiox-app && source venv/bin/activate && python -m py_compile app/main.py
```

### Erro 422: Unprocessable Entity
**Possíveis Causas:**
1. Campos do formulário não conferem
2. Arquivo não é imagem válida
3. Formato de dados incorreto

**Diagnóstico:**
```bash
# Verificar estrutura do endpoint
grep -A 10 "def jotform_webhook" /opt/raiox-app/app/main.py
```

### Endpoint Não Aparece em /docs
**Possíveis Causas:**
1. Erro de sintaxe
2. Endpoint após `if __name__ == "__main__"`
3. Serviço não reiniciado

**Diagnóstico:**
```bash
# Verificar sintaxe
python -m py_compile /opt/raiox-app/app/main.py

# Verificar posição do endpoint
grep -n "def jotform_webhook" /opt/raiox-app/app/main.py
grep -n "if __name__" /opt/raiox-app/app/main.py
```

### Timeout na Requisição
**Possíveis Causas:**
1. Processamento CLIP muito lento
2. Conexão com PostgreSQL lenta
3. Upload para Spaces lento

**Diagnóstico:**
```bash
# Verificar recursos do servidor
top
free -h
df -h
```

---

## 🚨 COMANDOS DE EMERGÊNCIA

### Rollback Completo
```bash
# Parar serviço
systemctl stop raiox-api

# Restaurar backup
cp /opt/raiox-app/app/main.py.backup_YYYYMMDD_HHMMSS /opt/raiox-app/app/main.py

# Reiniciar serviço
systemctl start raiox-api

# Verificar status
systemctl status raiox-api --no-pager
```

### Verificação Rápida de Saúde
```bash
# Status do serviço
systemctl is-active raiox-api

# Teste de conectividade
curl -s http://localhost:8000/healthcheck

# Verificar logs recentes
journalctl -u raiox-api --since '1 minute ago' --no-pager
```

### Reinicialização Forçada
```bash
# Matar processo se necessário
pkill -f "uvicorn app.main:app"

# Reiniciar serviço
systemctl restart raiox-api

# Aguardar inicialização
sleep 30

# Verificar status
systemctl status raiox-api --no-pager
```

---

## 📊 MÉTRICAS DE SUCESSO

### Performance Esperada
- **Tempo de resposta:** 20-40 segundos
- **Status code:** 200
- **Implantes retornados:** 1-5 (dependendo da similaridade)
- **Uso de memória:** ~1GB
- **Uso de CPU:** Picos durante processamento CLIP

### Logs de Sucesso
```
INFO: Recebendo dados do Jotform - arquivo: test.jpg, email: teste@effdental.com.br
INFO: Imagem enviada para Spaces: https://raiox-images.nyc3.digitaloceanspaces.com/...
INFO: Imagem processada com CLIP, buscando implantes similares...
INFO: Processamento Jotform concluído para teste_effdental_com_br - Encontrados 3 implantes similares
```

---

## 🎯 CONCLUSÃO

Esta documentação garante que a implementação do webhook Jotform seja reproduzível e livre de erros recorrentes. Todos os problemas identificados têm soluções definitivas documentadas.

**PRINCÍPIOS FUNDAMENTAIS:**
1. **SEMPRE criar backup** antes de alterações
2. **SEMPRE verificar sintaxe** antes de aplicar
3. **SEMPRE testar** após implementação
4. **SEMPRE documentar** problemas e soluções

**RESULTADO ESPERADO:** Webhook Jotform 100% funcional em primeira tentativa seguindo esta documentação.

