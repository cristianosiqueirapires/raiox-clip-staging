#!/usr/bin/env python3

import time
import subprocess
import os
import argparse
import datetime
import signal
import sys

# Configurações padrão
DEFAULT_INTERVAL = 60  # 1 minuto em segundos (ajustado conforme solicitado)
SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verificador_resultados_raioxapi.py")

# Variável global para controle de execução
running = True

def signal_handler(sig, frame):
    """Manipulador de sinal para interrupção (Ctrl+C)"""
    global running
    print("\n🛑 Interrupção detectada. Finalizando após a execução atual...")
    running = False

def format_time(seconds):
    """Formata o tempo em segundos para um formato legível"""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

def run_verificador(jotform_api_key):
    """Executa o script verificador_resultados_raioxapi.py"""
    print(f"\n{'='*60}")
    print(f"⏱️  Iniciando verificação em {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    env = os.environ.copy()
    env["JOTFORM_API_KEY"] = jotform_api_key
    
    try:
        result = subprocess.run(
            ["python3", SCRIPT_PATH],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"📋 Saída do verificador:")
        print(result.stdout)
        
        if result.stderr:
            print(f"⚠️  Erros:")
            print(result.stderr)
            
        print(f"✅ Verificação concluída com código de saída: {result.returncode}")
    except Exception as e:
        print(f"❌ Erro ao executar o verificador: {str(e)}")

def main():
    """Função principal do agendador"""
    parser = argparse.ArgumentParser(description="Agendador para o verificador de resultados RAIOXAPI")
    parser.add_argument(
        "-i", "--interval", 
        type=int, 
        default=DEFAULT_INTERVAL,
        help=f"Intervalo entre execuções em segundos (padrão: {DEFAULT_INTERVAL})"
    )
    parser.add_argument(
        "-k", "--api-key",
        type=str,
        help="Chave da API JotForm (se não fornecida, será usada a variável de ambiente JOTFORM_API_KEY)"
    )
    parser.add_argument(
        "-o", "--once",
        action="store_true",
        help="Executar apenas uma vez e sair"
    )
    parser.add_argument(
        "-m", "--monitor",
        action="store_true",
        help="Ativar monitoramento de performance (tempo de execução e uso de recursos)"
    )
    
    args = parser.parse_args()
    
    # Configurar manipulador de sinal para Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Obter a chave da API
    jotform_api_key = args.api_key or os.getenv("JOTFORM_API_KEY")
    if not jotform_api_key:
        print("❌ Erro: A chave da API JotForm não foi fornecida.")
        print("Por favor, defina a variável de ambiente JOTFORM_API_KEY ou use a opção --api-key.")
        sys.exit(1)
    
    # Executar uma vez se solicitado
    if args.once:
        print("🔄 Modo de execução única")
        run_verificador(jotform_api_key)
        return
    
    # Modo de execução contínua
    print(f"🔄 Iniciando agendador com intervalo de {format_time(args.interval)}")
    print("Pressione Ctrl+C para interromper")
    
    try:
        execution_count = 0
        while running:
            execution_count += 1
            
            # Monitoramento de performance
            if args.monitor:
                start_time = time.time()
                print(f"\n📊 Execução #{execution_count} - Monitoramento ativado")
            
            # Executar o verificador
            run_verificador(jotform_api_key)
            
            # Exibir estatísticas de performance
            if args.monitor:
                execution_time = time.time() - start_time
                print(f"⏱️  Tempo de execução: {execution_time:.2f} segundos")
                
                # Em um sistema real, você poderia adicionar mais métricas:
                # - Uso de memória
                # - Número de submissões processadas
                # - Taxa de sucesso/falha
            
            # Aguardar o próximo intervalo
            if running:
                print(f"\n⏳ Aguardando {format_time(args.interval)} até a próxima execução...")
                
                # Aguardar em pequenos intervalos para permitir interrupção rápida
                wait_interval = 1  # 1 segundo para resposta rápida
                for _ in range(int(args.interval / wait_interval)):
                    if not running:
                        break
                    time.sleep(wait_interval)
                
                # Aguardar o tempo restante
                remaining = args.interval % wait_interval
                if remaining > 0 and running:
                    time.sleep(remaining)
    
    except Exception as e:
        print(f"❌ Erro no agendador: {str(e)}")
    
    print("👋 Agendador finalizado")

if __name__ == "__main__":
    main()
