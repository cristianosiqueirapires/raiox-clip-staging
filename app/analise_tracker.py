import hashlib
import uuid
from datetime import datetime
from typing import Optional

class AnaliseTracker:
    """
    Sistema de rastreamento para análises do Raiox AI
    Vincula submissões originais com processamento IA e aprovação
    """
    
    @staticmethod
    def gerar_analise_id(submission_id: str, email: str, dente: str) -> str:
        """
        Gera ID único para análise baseado em dados do formulário
        
        Args:
            submission_id: ID da submissão do Jotform
            email: Email do dentista
            dente: Número do dente
            
        Returns:
            ID único no formato: {submission_id}_{hash_email}_{dente}
            Exemplo: "5123456789_a1b2c3_21"
        """
        # Hash do email para anonimização (LGPD)
        email_hash = hashlib.md5(email.encode()).hexdigest()[:6]
        
        # Combinar dados para ID único
        analise_id = f"{submission_id}_{email_hash}_{dente}"
        
        return analise_id
    
    @staticmethod
    def extrair_dados_tracking(form_data: dict) -> dict:
        """
        Extrai dados necessários para tracking do form_data do Jotform
        
        Args:
            form_data: Dados do formulário Jotform
            
        Returns:
            Dict com dados de tracking
        """
        # Extrair dados do formulário (baseado no formulário existente)
        submission_id = form_data.get("submissionID", "")
        
        # Campos do formulário atual
        nome_data = form_data.get("q4_nome", {})
        if isinstance(nome_data, dict):
            nome = f"{nome_data.get('first', '')} {nome_data.get('last', '')}".strip()
        else:
            nome = str(nome_data) if nome_data else ""
            
        email = form_data.get("q13_email", "")
        paciente = form_data.get("q5_nomeDo", "")
        dente = form_data.get("q16_qualO", "")
        
        # Gerar timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Gerar ID único da análise
        analise_id = AnaliseTracker.gerar_analise_id(submission_id, email, dente)
        
        return {
            "analise_id": analise_id,
            "submission_id": submission_id,
            "dentista_nome": nome,
            "dentista_email": email,
            "paciente_nome": paciente,
            "dente_numero": dente,
            "timestamp": timestamp,
            "timestamp_iso": datetime.now().isoformat()
        }
    
    @staticmethod
    def criar_dados_caso(tracking_data: dict, spaces_url: str) -> dict:
        """
        Cria estrutura completa dos dados do caso para armazenamento
        
        Args:
            tracking_data: Dados de tracking extraídos
            spaces_url: URL da imagem no DigitalOcean Spaces
            
        Returns:
            Dict com dados completos do caso
        """
        return {
            "analise_id": tracking_data["analise_id"],
            "submission_id": tracking_data["submission_id"],
            "dentista": {
                "nome": tracking_data["dentista_nome"],
                "email": tracking_data["dentista_email"]
            },
            "caso": {
                "paciente": tracking_data["paciente_nome"],
                "dente": tracking_data["dente_numero"],
                "imagem_url": spaces_url
            },
            "timestamps": {
                "submissao": tracking_data["timestamp"],
                "submissao_iso": tracking_data["timestamp_iso"],
                "processamento": datetime.now().isoformat()
            }
        }
    
    @staticmethod
    def validar_analise_id(analise_id: str) -> bool:
        """
        Valida formato do ID de análise
        
        Args:
            analise_id: ID a ser validado
            
        Returns:
            True se válido, False caso contrário
        """
        if not analise_id:
            return False
            
        # Formato esperado: {submission_id}_{hash_email}_{dente}
        partes = analise_id.split("_")
        
        if len(partes) != 3:
            return False
            
        submission_id, email_hash, dente = partes
        
        # Validações básicas
        if not submission_id.isdigit():
            return False
            
        if len(email_hash) != 6:
            return False
            
        if not dente.isdigit():
            return False
            
        return True
    
    @staticmethod
    def extrair_submission_id(analise_id: str) -> Optional[str]:
        """
        Extrai submission ID original do analise_id
        
        Args:
            analise_id: ID da análise
            
        Returns:
            Submission ID original ou None se inválido
        """
        if not AnaliseTracker.validar_analise_id(analise_id):
            return None
            
        return analise_id.split("_")[0]
    
    @staticmethod
    def log_tracking_info(tracking_data: dict, logger):
        """
        Log estruturado das informações de tracking
        
        Args:
            tracking_data: Dados de tracking
            logger: Logger para output
        """
        logger.info("=== TRACKING INFO ===")
        logger.info(f"Análise ID: {tracking_data['analise_id']}")
        logger.info(f"Submission ID: {tracking_data['submission_id']}")
        logger.info(f"Dentista: {tracking_data['dentista_nome']}")
        logger.info(f"Email: {tracking_data['dentista_email']}")
        logger.info(f"Paciente: {tracking_data['paciente_nome']}")
        logger.info(f"Dente: {tracking_data['dente_numero']}")
        logger.info(f"Timestamp: {tracking_data['timestamp']}")
        logger.info("=====================")

# Exemplo de uso:
"""
# No endpoint /jotform/resultados
form_data = await request.form()

# Extrair dados de tracking
tracking_data = AnaliseTracker.extrair_dados_tracking(form_data)

# Log das informações
AnaliseTracker.log_tracking_info(tracking_data, logger)

# Criar dados completos do caso
dados_caso = AnaliseTracker.criar_dados_caso(tracking_data, spaces_url)

# Incluir na resposta
response_data = {
    "analise_id": tracking_data["analise_id"],
    "dados_caso": dados_caso,
    "resultados_ia": resultado_formatado,
    # ... resto dos dados
}
"""

