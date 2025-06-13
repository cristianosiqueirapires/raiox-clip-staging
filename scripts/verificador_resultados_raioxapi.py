#!/usr/bin/env python3

import requests
import json
import os
from datetime import datetime

# Configurações da API JotForm
JOTFORM_API_KEY = os.getenv("JOTFORM_API_KEY")
FORM_ID = "251627519817061"  # ID do formulário de resultados
FORM_ID_PRINCIPAL = "251625025918659"  # ID do formulário principal

# URL da API JotForm
JOTFORM_API_BASE_URL = "https://api.jotform.com"

# Mapeamento de campos do JotForm (IDs reais do formulário )
FIELD_IDS = {
    "nome_completo": "12",
    "nome_contato_eff": "24",
    "email": "14",
    "nome_paciente": "4",
    "numero_dente": "6",
    "raiox_anexos": "17",  # Campo de upload de imagens do raio-X

    "resultado_analise_raioxapi": "48",  # Campo de resultado da análise
    "status": "49",  # Campo de status
}

def get_form_submissions(form_id, api_key, status="ACTIVE"):
    """Obtém as submissões de um formulário."""
    headers = {
        "APIKey": api_key
    }
    url = f"{JOTFORM_API_BASE_URL}/form/{form_id}/submissions?limit=1000&status={status}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Levanta um erro para códigos de status HTTP ruins (4xx ou 5xx)
        return response.json()["content"]
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter submissões do formulário: {e}")
        return []

def create_form_submission(form_id, api_key, data):
    """Cria uma nova submissão em um formulário."""
    headers = {
        "APIKey": api_key,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    url = f"{JOTFORM_API_BASE_URL}/form/{form_id}/submissions"
    
    # Preparar o payload com tratamento seguro para cada campo
    payload = {}
    
    # Tratar nome_completo de forma segura
    if "nome_completo" in data and data["nome_completo"]:
        nome_parts = data["nome_completo"].split(" ", 1)
        payload["submission[" + FIELD_IDS["nome_completo"] + "_first]"] = nome_parts[0]
        payload["submission[" + FIELD_IDS["nome_completo"] + "_last]"] = nome_parts[1] if len(nome_parts) > 1 else ""
    
    # Adicionar campos restantes com verificação de existência
    for field in ["nome_contato_eff", "email", "nome_paciente", "numero_dente", "resultado_analise_raioxapi", "status"]:
        if field in data and data[field] is not None:
            payload["submission[" + FIELD_IDS[field] + "]"] = data[field]
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        print(f"Nova submissão criada com sucesso no formulário {form_id}.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao criar nova submissão no formulário {form_id}: {e}")
        print(f"Resposta da API: {response.text if 'response' in locals() else 'N/A'}")
        return None

def formatar_mensagem_em_analise(dentista, paciente, numero_dente):
    """Formata uma mensagem de status 'Em Análise' para exibição no JotForm."""
    
    texto = f"""
🔍 ANÁLISE DE IMPLANTES RAIOXAPI - DENTE {numero_dente}
👨‍⚕️ Dentista: {dentista}
👤 Paciente: {paciente}

⏳ STATUS: EM ANÁLISE

Sua solicitação de análise foi recebida e está sendo processada pelo sistema RAIOXAPI.
As imagens de raio-X estão sendo analisadas para identificação de implantes similares.

O resultado será disponibilizado assim que o processamento for concluído pelo sistema CLIP.

📝 OBSERVAÇÕES:
- Você receberá uma notificação quando a análise estiver concluída
- Em caso de dúvidas, entre em contato com o suporte técnico da EFF
"""
    
    return texto

def formatar_exemplo_resultado(dentista, paciente, numero_dente):
    """Formata um exemplo de resultado com 3 implantes para exibição no JotForm."""
    
    texto = f"""
🔍 ANÁLISE DE IMPLANTES RAIOXAPI - DENTE {numero_dente}
👨‍⚕️ Dentista: {dentista}
👤 Paciente: {paciente}

🦷 IMPLANTES SIMILARES ENCONTRADOS:
==================================================

#1 - Nobel Biocare Implant 2
   🏷️  Marca: Nobel Biocare
   🔩 Tipo: Implante padrão
   📊 Acurácia: 91.1%
   ✅ Excelente compatibilidade
   🔗 Ref: https://raiox-images.nyc3.digitaloceanspaces.com/referencia/SEpl3TF2HXyV.webp

#2 - Nobel Biocare Implant 3
   🏷️  Marca: Nobel Biocare
   🔩 Tipo: Implante padrão
   📊 Acurácia: 87.6%
   🟡 Boa compatibilidade
   🔗 Ref: https://raiox-images.nyc3.digitaloceanspaces.com/referencia/d9u8TrHn4Xqr.webp

#3 - Nobel Biocare Implant 1
   🏷️  Marca: Nobel Biocare
   🔩 Tipo: Implante padrão
   📊 Acurácia: 82.4%
   🟠 Compatibilidade moderada
   🔗 Ref: https://raiox-images.nyc3.digitaloceanspaces.com/referencia/M7ZMEtGI2liC.jpg

📝 OBSERVAÇÕES:
Análise realizada com sucesso. Aguardando revisão técnica da EFF.
"""
    
    return texto

def extrair_valor_seguro(answers, field_id, default="N/A" ):
    """Extrai um valor de forma segura do dicionário de respostas."""
    if field_id not in answers:
        return default
    
    answer = answers[field_id].get("answer", default)
    
    # Se for um dicionário, tenta extrair valores específicos
    if isinstance(answer, dict):
        # Para campos de nome completo
        if "first" in answer and "last" in answer:
            return f"{answer.get('first', '')} {answer.get('last', '')}".strip()
        # Para outros tipos de campos estruturados
        return str(answer)
    
    # Se for uma string, lista ou outro tipo, converte para string
    return str(answer) if answer is not None else default

def verificar_e_atualizar_resultados():
    """Verifica submissões pendentes no formulário principal e cria novas submissões no formulário de resultados."""
    print("Verificando submissões pendentes no formulário principal...")
    # Obter submissões do formulário principal (o original, com assinatura)
    submissions_main_form = get_form_submissions(FORM_ID_PRINCIPAL, JOTFORM_API_KEY)

    if not submissions_main_form:
        print("Nenhuma submissão encontrada no formulário principal ou erro ao buscar submissões.")
        return

    # Obter submissões do formulário de resultados para verificar quais já foram processadas
    submissions_results_form = get_form_submissions(FORM_ID, JOTFORM_API_KEY)
    processed_submissions = set()
    
    if submissions_results_form:
        for submission in submissions_results_form:
            # Extrair o nome do paciente como identificador
            try:
                nome_paciente = extrair_valor_seguro(submission.get("answers", {}), FIELD_IDS["nome_paciente"])
                if nome_paciente and nome_paciente != "N/A":
                    processed_submissions.add(nome_paciente)
            except Exception as e:
                print(f"Erro ao processar submissão existente: {str(e)}")

    for submission in submissions_main_form:
        try:
            submission_id = submission["id"]
            answers = submission["answers"]
            
            # Campo de status do formulário principal (para verificar se já foi processado)
            status_main_form_field_id = "49" # ID do campo status no formulário principal
            current_status_main_form = extrair_valor_seguro(answers, status_main_form_field_id, "Pendente")

            # Extrair dados dos campos do formulário principal de forma segura
            nome_completo = extrair_valor_seguro(answers, FIELD_IDS["nome_completo"])
            nome_contato_eff = extrair_valor_seguro(answers, FIELD_IDS["nome_contato_eff"])
            email = extrair_valor_seguro(answers, FIELD_IDS["email"])
            nome_paciente = extrair_valor_seguro(answers, FIELD_IDS["nome_paciente"])
            numero_dente = extrair_valor_seguro(answers, FIELD_IDS["numero_dente"])

            # Verificar se esta submissão já foi processada (usando o nome do paciente como identificador)
            if nome_paciente in processed_submissions:
                print(f"Submissão para paciente '{nome_paciente}' já foi processada. Pulando.")
                continue

            # Apenas processar submissões que ainda não foram enviadas para o formulário de resultados
            # ou que estão com status Pendente/Em Análise no formulário principal
            if current_status_main_form in ["Pendente", "Em Análise"]:
                print(f"Submissão {submission_id} do formulário principal está com status '{current_status_main_form}'. Criando entrada no formulário de resultados...")
                
                # Inicializar dados para o formulário de resultados
                resultado_data = {
                    "nome_completo": nome_completo,
                    "nome_contato_eff": nome_contato_eff,
                    "email": email,
                    "nome_paciente": nome_paciente,
                    "numero_dente": numero_dente,
                    "resultado_analise_raioxapi": formatar_mensagem_em_analise(nome_completo, nome_paciente, numero_dente),
                    "status": "Em Análise"
                }
                
                # Criar uma nova submissão no formulário de resultados com os dados processados
                create_form_submission(FORM_ID, JOTFORM_API_KEY, resultado_data)
            else:
                print(f"Submissão {submission_id} do formulário principal com status '{current_status_main_form}'. Nenhuma ação necessária.")
        except Exception as e:
            print(f"Erro ao processar submissão {submission.get('id', 'desconhecido')}: {str(e)}")
            continue

if __name__ == "__main__":
    # Certifique-se de que a variável de ambiente JOTFORM_API_KEY esteja definida
    if not JOTFORM_API_KEY:
        print("Erro: A variável de ambiente JOTFORM_API_KEY não está definida.")
        print("Por favor, defina-a antes de executar o script.")
    else:
        verificar_e_atualizar_resultados()
