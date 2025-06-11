# Melhorias Futuras para o Raiox AI

## Versão 1.0 - Junho 2025

Este documento detalha as melhorias planejadas para a Fase 2 do projeto Raiox AI, incluindo configurações avançadas, scripts de teste, considerações de segurança e roadmap de desenvolvimento.

## Índice

1. [Configuração Avançada do Serviço](#1-configuração-avançada-do-serviço)
2. [Nginx Reverse-Proxy com HTTPS](#2-nginx-reverse-proxy-com-https)
3. [Painel Administrativo](#3-painel-administrativo)
4. [Retorno ao Jotform](#4-retorno-ao-jotform)
5. [Troubleshooting](#5-troubleshooting)
6. [LGPD e Considerações Éticas](#6-lgpd-e-considerações-éticas)
7. [Scripts Utilitários](#7-scripts-utilitários)
8. [Roadmap da Fase 2](#8-roadmap-da-fase-2)

## 1. Configuração Avançada do Serviço

### 1.1 Serviço Systemd Completo

Para garantir que o serviço Raiox API inicie automaticamente e seja gerenciado adequadamente pelo sistema, uma configuração systemd mais robusta pode ser implementada:

```ini
# /etc/systemd/system/raiox-api.service
[Unit]
Description=Raiox AI FastAPI
After=network.target

[Service]
User=root
WorkingDirectory=/opt/raiox
EnvironmentFile=/opt/raiox/.env
ExecStart=/opt/raiox/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Esta configuração inclui:
- Múltiplos workers para melhor performance
- Reinício automático em caso de falha
- Arquivo de variáveis de ambiente separado
- Dependência explícita da rede

Para ativar:
```bash
sudo systemctl enable raiox-api
sudo systemctl start raiox-api
```

## 2. Nginx Reverse-Proxy com HTTPS

### 2.1 Configuração do Nginx

Para expor a API com um domínio próprio e preparar para HTTPS:

```nginx
server {
  listen 80;
  server_name api.raiox.ai;
  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

### 2.2 Ativação da Configuração

```bash
ln -s /etc/nginx/sites-available/raiox /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

### 2.3 Configuração de HTTPS (Futuro)

Quando o domínio estiver apontando para o servidor:

```bash
certbot --nginx -d api.raiox.ai
```

## 3. Painel Administrativo

### 3.1 Estrutura Básica

Um painel administrativo em Flask para gerenciar casos pendentes:

```
/opt/raiox-admin/
  app.py
  templates/
    base.html
    login.html
    dashboard.html
    case_detail.html
  static/
    css/
    js/
    img/
```

### 3.2 Implementação Básica do app.py

```python
from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import os
from dotenv import load_dotenv
from functools import wraps

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_key")

# Configuração do banco de dados
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "raiox_db")
DB_USER = os.getenv("DB_USER", "raiox_user")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    conn.autocommit = True
    return conn

# Decorator para verificar login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, client_id, submission_date, status FROM cases ORDER BY submission_date DESC")
    cases = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('dashboard.html', cases=cases)

@app.route('/case/<int:case_id>')
@login_required
def case_detail(case_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Obter detalhes do caso
    cur.execute("SELECT * FROM cases WHERE id = %s", (case_id,))
    case = cur.fetchone()
    
    # Obter implantes sugeridos
    cur.execute("SELECT * FROM case_implants WHERE case_id = %s", (case_id,))
    implants = cur.fetchall()
    
    cur.close()
    conn.close()
    
    if case is None:
        flash('Caso não encontrado', 'error')
        return redirect(url_for('index'))
    
    return render_template('case_detail.html', case=case, implants=implants)

@app.route('/approve/<int:case_id>', methods=['POST'])
@login_required
def approve_case(case_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Atualizar status do caso
    cur.execute("UPDATE cases SET status = 'approved', approved_at = NOW() WHERE id = %s", (case_id,))
    
    # Enviar resposta para Jotform (implementação futura)
    # send_jotform_callback(case_id)
    
    cur.close()
    conn.close()
    
    flash('Caso aprovado com sucesso', 'success')
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Verificação simples - deve ser substituída por autenticação segura
        if username == os.getenv("ADMIN_USER", "admin") and password == os.getenv("ADMIN_PASSWORD", "password"):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('Credenciais inválidas', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

## 4. Retorno ao Jotform

### 4.1 Endpoint de Callback

Implementação de um endpoint para enviar resultados de volta ao Jotform:

```python
@app.post("/callback")
async def jotform_callback(case_id: int, db: Session = Depends(get_db)):
    """
    Envia resultados aprovados de volta para o Jotform
    """
    try:
        # Obter caso do banco de dados
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Caso não encontrado")
        
        if case.status != "approved":
            raise HTTPException(status_code=400, detail="Caso não aprovado")
        
        # Obter implantes sugeridos
        implants = db.query(CaseImplant).filter(CaseImplant.case_id == case_id).all()
        
        # Preparar dados para envio
        payload = {
            "approved": True,
            "submission_id": case.submission_id,
            "top_implants": [
                {
                    "name": implant.name,
                    "manufacturer": implant.manufacturer,
                    "confidence": implant.confidence
                }
                for implant in implants
            ]
        }
        
        # Enviar para Jotform
        jotform_api_key = os.getenv("JOTFORM_API_KEY")
        headers = {
            "Content-Type": "application/json",
            "APIKEY": jotform_api_key
        }
        
        response = requests.post(
            f"https://api.jotform.com/submission/{case.submission_id}",
            json=payload,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Erro ao enviar para Jotform: {response.text}")
            raise HTTPException(status_code=500, detail="Erro ao enviar para Jotform")
        
        # Atualizar status do caso
        case.callback_sent = True
        case.callback_sent_at = datetime.now()
        db.commit()
        
        return {"success": True, "message": "Callback enviado com sucesso"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar callback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar callback: {str(e)}")
```

## 5. Troubleshooting

### 5.1 Tabela de Erros Comuns e Soluções

| Erro | Causa | Solução |
|------|-------|---------|
| `operator does not exist: vector <-> numeric[]` | Parâmetro de bind não convertido para vector | Usar `::vector` no SQL ou converter no código |
| `psycopg2.OperationalError (timeout)` | Senha com caracteres especiais mal escapados | URL-encode a senha ou trocar caracteres especiais |
| `ModuleNotFoundError: No module named 'pgvector'` | Módulo pgvector não instalado | `pip install pgvector` no ambiente virtual |
| `fastapi.exceptions.FastAPIError: Invalid args for response field!` | Uso de modelo SQLAlchemy como response_model | Criar e usar schema Pydantic correspondente |
| `NameError: name 'get_db' is not defined` | Função de dependência não importada | Adicionar import correto para a função |
| `sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) FATAL: password authentication failed` | Credenciais incorretas do banco de dados | Verificar variáveis de ambiente e .env |

## 6. LGPD e Considerações Éticas

### 6.1 Conformidade com LGPD

- **Consentimento explícito**: Adicionar checkbox de consentimento no formulário Jotform
- **Política de retenção**: Implementar exclusão automática de uploads após 90 dias
- **Anonimização**: Usar hash para identificar clientes em vez de dados pessoais
- **Termos de uso**: Adicionar página com termos de uso e política de privacidade
- **Direito ao esquecimento**: Implementar endpoint para exclusão de dados a pedido do usuário

### 6.2 Implementação da Política de Retenção

```python
@app.on.after_startup
async def setup_cleanup_task():
    """
    Configura tarefa periódica para limpar uploads antigos
    """
    asyncio.create_task(cleanup_old_uploads())

async def cleanup_old_uploads():
    """
    Remove uploads com mais de 90 dias
    """
    while True:
        try:
            # Aguardar até meia-noite
            tomorrow = datetime.now() + timedelta(days=1)
            midnight = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)
            seconds_until_midnight = (midnight - datetime.now()).total_seconds()
            await asyncio.sleep(seconds_until_midnight)
            
            # Conectar ao banco de dados
            async with async_session() as db:
                # Encontrar uploads antigos
                ninety_days_ago = datetime.now() - timedelta(days=90)
                old_cases = await db.execute(
                    select(Case).where(Case.created_at < ninety_days_ago)
                )
                old_cases = old_cases.scalars().all()
                
                # Excluir arquivos do storage
                s3 = boto3.client(
                    's3',
                    endpoint_url=f"https://{os.getenv('DO_SPACES_REGION')}.digitaloceanspaces.com",
                    aws_access_key_id=os.getenv('DO_SPACES_KEY'),
                    aws_secret_access_key=os.getenv('DO_SPACES_SECRET')
                )
                
                for case in old_cases:
                    # Excluir imagem do Spaces
                    if case.image_path:
                        try:
                            s3.delete_object(
                                Bucket=os.getenv('DO_SPACES_BUCKET'),
                                Key=case.image_path
                            )
                            logger.info(f"Excluída imagem antiga: {case.image_path}")
                        except Exception as e:
                            logger.error(f"Erro ao excluir imagem: {str(e)}")
                    
                    # Atualizar registro no banco
                    case.image_path = None
                    case.status = "archived"
                
                await db.commit()
                logger.info(f"Limpeza concluída: {len(old_cases)} casos arquivados")
        
        except Exception as e:
            logger.error(f"Erro na limpeza automática: {str(e)}")
        
        # Aguardar 24 horas antes da próxima verificação
        await asyncio.sleep(86400)
```

## 7. Scripts Utilitários

### 7.1 Script de Teste de Webhook (test_webhook.py)

Este script simula chamadas do Jotform para o ambiente de staging:

```python
import requests
import argparse
import json
import random
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def simulate_webhook(api_url, image_path=None, image_url=None):
    """
    Simula uma chamada de webhook do Jotform para a API Raiox
    
    Parâmetros:
    - api_url: URL da API (staging ou produção)
    - image_path: Caminho local para imagem de teste (opcional)
    - image_url: URL de imagem de teste (opcional)
    """
    # Se não foi fornecida imagem, usar uma das imagens de teste
    if not image_url and not image_path:
        test_images = [
            "https://raiox-images.nyc3.digitaloceanspaces.com/referencia/NOBEL_REPLACE_4.3mm.jpg",
            "https://raiox-images.nyc3.digitaloceanspaces.com/referencia/STRAUMANN_BL_4.1mm.jpg"
        ]
        image_url = random.choice(test_images)
    
    # Se foi fornecido caminho local, fazer upload para um storage temporário
    if image_path:
        # Configurar cliente S3
        s3 = boto3.client(
            's3',
            endpoint_url=f"https://{os.getenv('DO_SPACES_REGION')}.digitaloceanspaces.com",
            aws_access_key_id=os.getenv('DO_SPACES_KEY'),
            aws_secret_access_key=os.getenv('DO_SPACES_SECRET')
        )
        
        # Upload da imagem
        filename = os.path.basename(image_path)
        object_name = f"test/{filename}"
        
        try:
            s3.upload_file(
                image_path,
                os.getenv('DO_SPACES_BUCKET'),
                object_name,
                ExtraArgs={'ACL': 'public-read'}
            )
            
            # Gerar URL
            image_url = f"https://{os.getenv('DO_SPACES_BUCKET')}.{os.getenv('DO_SPACES_REGION')}.digitaloceanspaces.com/{object_name}"
            print(f"Imagem enviada: {image_url}")
        except Exception as e:
            print(f"Erro ao enviar imagem: {str(e)}")
            return None
    
    # Preparar dados do webhook
    webhook_data = {
        "image_url": image_url,
        "client_id": f"test_client_{random.randint(1000, 9999)}",
        "metadata": {
            "client_name": "Paciente de Teste",
            "submission_date": "2025-06-10",
            "notes": "Simulação de caso para teste"
        }
    }
    
    print(f"Enviando webhook para {api_url}/webhook")
    print(f"URL da imagem: {image_url}")
    
    try:
        response = requests.post(
            f"{api_url}/webhook",
            json=webhook_data
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Implantes similares encontrados:")
            for i, implant in enumerate(response.json()):
                print(f"  {i+1}. {implant['name']} ({implant['manufacturer']})")
        else:
            print(f"Erro: {response.text}")
        
        return response.json() if response.status_code == 200 else None
    
    except Exception as e:
        print(f"Erro: {str(e)}")
        return None

# Função principal
def main():
    parser = argparse.ArgumentParser(description='Simulador de Webhook para Raiox AI')
    parser.add_argument('--api', default='http://staging.raiox-ai.com:8000', help='URL da API Raiox')
    parser.add_argument('--image', help='Caminho local para imagem de teste')
    parser.add_argument('--url', help='URL de imagem de teste')
    parser.add_argument('--count', type=int, default=1, help='Número de simulações')
    
    args = parser.parse_args()
    
    for i in range(args.count):
        print(f"\nSimulação {i+1}/{args.count}")
        simulate_webhook(args.api, args.image, args.url)

if __name__ == "__main__":
    main()
```

### 7.2 Script de Teste de Carga (locustfile.py)

Este script simula múltiplos uploads simultâneos para testar a capacidade do servidor:

```python
from locust import HttpUser, task, between
import random
import os
import json

class RaioxUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        """
        Carrega URLs de imagens de teste
        """
        # Carregar URLs de imagens de teste
        with open("test_images.json", "r") as f:
            self.test_images = json.load(f)
    
    @task
    def test_webhook(self):
        """
        Simula uma chamada de webhook
        """
        # Selecionar imagem aleatória
        image = random.choice(self.test_images)
        
        # Preparar dados do webhook
        webhook_data = {
            "image_url": image["url"],
            "client_id": f"load_test_{random.randint(1000, 9999)}",
            "metadata": {
                "client_name": "Teste de Carga",
                "submission_date": "2025-06-10",
                "notes": "Simulação para teste de carga"
            }
        }
        
        # Enviar webhook
        with self.client.post(
            "/webhook",
            json=webhook_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Falha: {response.status_code} - {response.text}")
    
    @task(weight=2)
    def test_upload(self):
        """
        Simula upload de imagem
        """
        # Selecionar arquivo de teste aleatório
        test_files = [
            "test_images/test1.jpg",
            "test_images/test2.jpg",
            "test_images/test3.jpg"
        ]
        file_path = random.choice(test_files)
        
        # Preparar arquivo para upload
        files = {
            "file": (os.path.basename(file_path), open(file_path, "rb"), "image/jpeg")
        }
        
        # Enviar upload
        with self.client.post(
            "/upload",
            files=files,
            data={"client_id": f"load_test_{random.randint(1000, 9999)}"},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Falha: {response.status_code} - {response.text}")
```

Para executar o teste de carga:

```bash
locust -f locustfile.py --host=http://staging.raiox-ai.com:8000 --users 100 --spawn-rate 10
```

## 8. Roadmap da Fase 2

### 8.1 Melhorias Planejadas

1. **Migrar para GPU**
   - Implementar suporte a GPU (RunPod ou DigitalOcean A10G)
   - Otimizar processamento CLIP para GPU
   - Reduzir tempo de resposta para menos de 1 segundo

2. **Habilitar HTTPS com domínio**
   - Registrar domínio api.raiox.ai
   - Configurar certificado SSL com Let's Encrypt
   - Implementar HSTS e outras medidas de segurança

3. **Incrementar dataset para 1.000 imagens**
   - Coletar mais imagens de referência
   - Padronizar e processar novas imagens
   - Melhorar precisão da busca por similaridade

4. **Implementar painel Flask + JWT**
   - Desenvolver interface administrativa completa
   - Implementar autenticação segura com JWT
   - Adicionar dashboard com métricas e estatísticas

5. **Importar infraestrutura para Terraform**
   - Documentar infraestrutura como código
   - Configurar Terraform Cloud backend
   - Automatizar provisionamento de ambientes

### 8.2 Cronograma Estimado

| Melhoria | Prazo Estimado | Prioridade |
|----------|----------------|------------|
| Migrar para GPU | 2 semanas | Alta |
| Habilitar HTTPS | 1 semana | Média |
| Incrementar dataset | 4 semanas | Alta |
| Implementar painel | 3 semanas | Média |
| Importar para Terraform | 2 semanas | Baixa |

## Conclusão

Este documento detalha as melhorias planejadas para a Fase 2 do projeto Raiox AI. Estas melhorias visam aumentar a robustez, segurança e escalabilidade do sistema, além de adicionar funcionalidades importantes como o painel administrativo e o retorno automático ao Jotform.

A implementação destas melhorias deve seguir o cronograma estimado, priorizando as melhorias de maior impacto para o negócio, como a migração para GPU e o incremento do dataset.

---

*Documento criado por Manus AI - Junho 2025*
