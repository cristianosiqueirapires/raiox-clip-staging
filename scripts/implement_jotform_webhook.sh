#!/bin/bash

# Script de implementação do Webhook Jotform
# Uso: ./implement_jotform_webhook.sh

set -e

echo "🎯 Iniciando implementação do Webhook Jotform..."

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Este script deve ser executado como root"
    exit 1
fi

# Configurações
APP_DIR="/opt/raiox-app"
BACKUP_DIR="/opt/raiox-app/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "📁 Criando diretório de backup..."
mkdir -p $BACKUP_DIR

echo "💾 Criando backup do main.py..."
cp $APP_DIR/app/main.py $BACKUP_DIR/main.py.backup_$TIMESTAMP

echo "🔍 Verificando se endpoint jotform já existe..."
if grep -q "def jotform_webhook" $APP_DIR/app/main.py; then
    echo "✅ Endpoint jotform já existe no código"
else
    echo "➕ Adicionando endpoint jotform..."
    
    # Encontrar linha do if __name__
    LINE_NUM=$(grep -n "if __name__" $APP_DIR/app/main.py | cut -d: -f1)
    
    if [ -z "$LINE_NUM" ]; then
        echo "❌ Não foi possível encontrar 'if __name__' no arquivo"
        exit 1
    fi
    
    echo "📝 Inserindo endpoint na linha $LINE_NUM..."
    
    # Separar arquivo
    head -$((LINE_NUM-1)) $APP_DIR/app/main.py > /tmp/main_part1.py
    tail -n +$LINE_NUM $APP_DIR/app/main.py > /tmp/main_part2.py
    
    # Criar endpoint jotform
    cat > /tmp/jotform_endpoint.py << 'EOF'

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


EOF
    
    # Combinar arquivos
    cat /tmp/main_part1.py > $APP_DIR/app/main_fixed.py
    cat /tmp/jotform_endpoint.py >> $APP_DIR/app/main_fixed.py
    cat /tmp/main_part2.py >> $APP_DIR/app/main_fixed.py
    
    # Verificar sintaxe
    echo "🔍 Verificando sintaxe do código..."
    cd $APP_DIR && source venv/bin/activate && python -m py_compile app/main_fixed.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Sintaxe verificada com sucesso"
        mv $APP_DIR/app/main.py $APP_DIR/app/main.py.old
        mv $APP_DIR/app/main_fixed.py $APP_DIR/app/main.py
    else
        echo "❌ Erro de sintaxe no código"
        exit 1
    fi
fi

echo "🔧 Verificando se função process_image está sendo usada corretamente..."
if grep -q "process_image_with_clip" $APP_DIR/app/main.py; then
    echo "🔧 Corrigindo chamada da função CLIP..."
    sed -i 's/query_vector = process_image_with_clip(image_pil)/query_vector = process_image(image_data)/' $APP_DIR/app/main.py
fi

echo "🔄 Reiniciando serviço raiox-api..."
systemctl restart raiox-api

echo "⏳ Aguardando inicialização do serviço..."
sleep 30

echo "🔍 Verificando status do serviço..."
if systemctl is-active --quiet raiox-api; then
    echo "✅ Serviço raiox-api está ativo"
else
    echo "❌ Serviço raiox-api não está ativo"
    systemctl status raiox-api
    exit 1
fi

echo "🔍 Verificando se endpoint aparece na documentação..."
if curl -s http://localhost:8000/openapi.json | grep -q "jotform"; then
    echo "✅ Endpoint /jotform encontrado na documentação"
else
    echo "❌ Endpoint /jotform não encontrado na documentação"
    exit 1
fi

echo "🧪 Testando endpoint com healthcheck..."
if curl -s http://localhost:8000/healthcheck | grep -q "ok"; then
    echo "✅ API respondendo corretamente"
else
    echo "❌ API não está respondendo"
    exit 1
fi

echo ""
echo "🎉 IMPLEMENTAÇÃO CONCLUÍDA COM SUCESSO!"
echo ""
echo "📋 INFORMAÇÕES DO WEBHOOK:"
echo "   URL: http://$(hostname -I | awk '{print $1}'):8000/jotform"
echo "   Método: POST"
echo "   Formato: multipart/form-data"
echo ""
echo "📁 CAMPOS ACEITOS:"
echo "   - file (obrigatório): Arquivo de imagem"
echo "   - nome (opcional): Nome do dentista"
echo "   - email (opcional): Email do dentista"
echo "   - paciente (opcional): Nome do paciente"
echo "   - dente (opcional): Número do dente"
echo ""
echo "🔍 VERIFICAÇÕES:"
echo "   - Documentação: http://$(hostname -I | awk '{print $1}'):8000/docs"
echo "   - Status: systemctl status raiox-api"
echo "   - Logs: journalctl -u raiox-api -f"
echo ""
echo "💾 BACKUP CRIADO EM: $BACKUP_DIR/main.py.backup_$TIMESTAMP"
echo ""
echo "✅ WEBHOOK JOTFORM PRONTO PARA USO!"

