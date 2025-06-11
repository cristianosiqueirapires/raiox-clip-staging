#!/bin/bash

# Script de teste do Webhook Jotform
# Uso: ./test_jotform_webhook.sh [imagem.jpg]

set -e

# Configurações
SERVER_IP="45.55.128.141"
ENDPOINT_URL="http://$SERVER_IP:8000/jotform"
TEST_IMAGE=${1:-"test_image.jpg"}

echo "🧪 Testando Webhook Jotform..."
echo "📡 URL: $ENDPOINT_URL"
echo "🖼️ Imagem: $TEST_IMAGE"
echo ""

# Verificar se arquivo de imagem existe
if [ ! -f "$TEST_IMAGE" ]; then
    echo "❌ Arquivo de imagem não encontrado: $TEST_IMAGE"
    echo "💡 Uso: $0 [caminho_para_imagem.jpg]"
    exit 1
fi

# Verificar se é uma imagem
if ! file "$TEST_IMAGE" | grep -q -E "(JPEG|PNG|GIF|BMP|TIFF)"; then
    echo "❌ Arquivo não é uma imagem válida: $TEST_IMAGE"
    exit 1
fi

echo "📋 Dados de teste:"
echo "   Nome: Dr. Teste Automatizado"
echo "   Email: teste@effdental.com.br"
echo "   Paciente: Paciente Teste"
echo "   Dente: 16"
echo ""

echo "📡 Enviando requisição..."

# Fazer requisição POST
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    -F "file=@$TEST_IMAGE" \
    -F "nome=Dr. Teste Automatizado" \
    -F "email=teste@effdental.com.br" \
    -F "paciente=Paciente Teste" \
    -F "dente=16" \
    "$ENDPOINT_URL")

# Separar resposta e código HTTP
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$RESPONSE" | head -n -1)

echo "📊 Resultado:"
echo "   Status Code: $HTTP_CODE"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ SUCESSO!"
    echo ""
    echo "📋 Resposta:"
    echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"
    echo ""
    
    # Contar implantes encontrados
    IMPLANT_COUNT=$(echo "$RESPONSE_BODY" | python3 -c "import json, sys; data=json.load(sys.stdin); print(len(data))" 2>/dev/null || echo "0")
    echo "🎯 Implantes encontrados: $IMPLANT_COUNT"
    
    if [ "$IMPLANT_COUNT" -gt 0 ]; then
        echo "✅ TESTE PASSOU - Sistema funcionando corretamente!"
    else
        echo "⚠️ AVISO - Nenhum implante encontrado (pode ser normal)"
    fi
else
    echo "❌ ERRO!"
    echo ""
    echo "📄 Resposta de erro:"
    echo "$RESPONSE_BODY"
    echo ""
    
    # Sugestões de troubleshooting
    echo "🔍 Troubleshooting:"
    case $HTTP_CODE in
        422)
            echo "   - Verificar formato dos dados enviados"
            echo "   - Verificar se arquivo é uma imagem válida"
            ;;
        500)
            echo "   - Verificar logs do servidor: journalctl -u raiox-api -f"
            echo "   - Verificar se PostgreSQL está acessível"
            echo "   - Verificar se CLIP está funcionando"
            ;;
        404)
            echo "   - Verificar se endpoint /jotform existe"
            echo "   - Verificar documentação: http://$SERVER_IP:8000/docs"
            ;;
        *)
            echo "   - Verificar se serviço está rodando: systemctl status raiox-api"
            echo "   - Verificar conectividade: ping $SERVER_IP"
            ;;
    esac
    
    exit 1
fi

echo ""
echo "🎉 TESTE CONCLUÍDO COM SUCESSO!"

