# Manual de Coleta e Padronização de Imagens Reais para o Raiox AI

## Versão 1.0 - Junho 2025

Este manual detalha o processo completo de coleta, padronização e uso de imagens reais de implantes dentários para simulação, testes e alimentação do banco de dados de referência do sistema Raiox AI.

## Índice

1. [Introdução](#1-introdução)
2. [Busca de Imagens](#2-busca-de-imagens)
3. [Padronização de Nomenclatura](#3-padronização-de-nomenclatura)
4. [Processamento de Imagens](#4-processamento-de-imagens)
5. [Upload para DigitalOcean Spaces](#5-upload-para-digitalocean-spaces)
6. [Extração de Embeddings](#6-extração-de-embeddings)
7. [Inserção no Banco de Dados](#7-inserção-no-banco-de-dados)
8. [Simulação de Casos Reais](#8-simulação-de-casos-reais)
9. [Considerações Éticas e Legais](#9-considerações-éticas-e-legais)

## 1. Introdução

Para que o sistema Raiox AI funcione corretamente, é necessário um banco de dados de referência com imagens reais de implantes dentários. Este manual descreve o processo que utilizamos para coletar, padronizar e utilizar essas imagens durante o desenvolvimento e testes do sistema.

## 2. Busca de Imagens

### 2.1 Fontes de Imagens

As principais fontes de imagens utilizadas foram:

- **Google Images**: Busca por termos específicos como "dental implant X-ray", "Nobel Biocare implant radiograph", "Straumann implant X-ray", etc.
- **Catálogos de fabricantes**: Sites oficiais da Nobel Biocare, Straumann, Neodent, etc.
- **Artigos científicos**: Publicações em revistas odontológicas com imagens de raio-X de implantes.
- **Bancos de imagens médicas**: Repositórios específicos para imagens médicas e odontológicas.

### 2.2 Termos de Busca Eficientes

Para encontrar imagens de qualidade, utilizamos combinações dos seguintes termos:

- Fabricantes: "Nobel Biocare", "Straumann", "Neodent", "Zimmer", etc.
- Modelos: "Replace", "Active", "Bone Level", "Tapered", etc.
- Diâmetros: "3.5mm", "4.0mm", "4.3mm", etc.
- Qualificadores: "dental implant", "radiograph", "X-ray", "periapical", "panoramic"

### 2.3 Critérios de Seleção

Ao selecionar imagens, aplicamos os seguintes critérios:

- **Qualidade**: Imagens nítidas, com boa resolução e contraste
- **Visibilidade**: Implante claramente visível na radiografia
- **Representatividade**: Diferentes ângulos, posições e contextos clínicos
- **Diversidade**: Variedade de fabricantes, modelos e diâmetros
- **Formato**: Preferência por formatos JPG ou PNG

### 2.4 Ferramentas de Download

Para baixar as imagens, utilizamos:

- Download direto do navegador (clique direito > Salvar imagem como...)
- Extensões de navegador como "Image Downloader" para Chrome
- Scripts Python com bibliotecas como `requests` e `BeautifulSoup` para download em lote

```python
import requests
from bs4 import BeautifulSoup
import os

def download_images(search_term, output_dir, max_images=20):
    """
    Download images from Google Images based on search term
    """
    # Criar diretório se não existir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Simular busca no Google Images
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    search_url = f"https://www.google.com/search?q={search_term}&tbm=isch"
    response = requests.get(search_url, headers=headers)
    
    # Extrair URLs das imagens
    soup = BeautifulSoup(response.text, 'html.parser')
    image_tags = soup.find_all('img')
    
    # Download das imagens
    count = 0
    for img in image_tags:
        if count >= max_images:
            break
        
        img_url = img.get('src')
        if img_url and img_url.startswith('http'):
            try:
                img_data = requests.get(img_url, headers=headers).content
                img_name = f"{search_term.replace(' ', '_')}_{count}.jpg"
                img_path = os.path.join(output_dir, img_name)
                
                with open(img_path, 'wb') as f:
                    f.write(img_data)
                
                print(f"Downloaded: {img_path}")
                count += 1
            except Exception as e:
                print(f"Error downloading {img_url}: {str(e)}")

# Exemplo de uso
download_images("Nobel Biocare Replace 4.3mm dental implant xray", "implant_images/nobel")
download_images("Straumann Bone Level 4.1mm dental implant xray", "implant_images/straumann")
```

## 3. Padronização de Nomenclatura

Para facilitar a organização e o uso das imagens, adotamos um sistema padronizado de nomenclatura:

### 3.1 Convenção de Nomenclatura

O formato padrão é:
```
FABRICANTE_MODELO_DIAMETRO.jpg
```

Exemplos:
- `NOBEL_REPLACE_4.3mm.jpg`
- `STRAUMANN_BL_4.1mm.jpg`
- `NEODENT_DRIVE_3.5mm.jpg`

### 3.2 Regras de Nomenclatura

- **FABRICANTE**: Sempre em maiúsculas, sem espaços
- **MODELO**: Abreviação do modelo, em maiúsculas, sem espaços
  - Replace = REPLACE
  - Bone Level = BL
  - Bone Level Tapered = BLT
- **DIAMETRO**: Sempre em milímetros, com precisão de uma casa decimal
  - 3.5mm, 4.0mm, 4.3mm, etc.

### 3.3 Script de Renomeação

Para renomear imagens em lote, utilizamos o seguinte script Python:

```python
import os
import re

def rename_implant_images(directory):
    """
    Renomeia imagens de implantes seguindo o padrão FABRICANTE_MODELO_DIAMETRO.jpg
    """
    # Mapeamento de termos para padronização
    fabricantes = {
        "nobel": "NOBEL",
        "nobelbiocare": "NOBEL",
        "straumann": "STRAUMANN",
        "neodent": "NEODENT",
        "zimmer": "ZIMMER"
    }
    
    modelos = {
        "replace": "REPLACE",
        "active": "ACTIVE",
        "conical": "CC",
        "bonelevel": "BL",
        "bone-level": "BL",
        "tapered": "BLT",
        "tissue-level": "TL",
        "drive": "DRIVE"
    }
    
    # Padrão para extrair diâmetro
    diametro_pattern = re.compile(r'(\d+[.,]\d+)(?:mm|MM)')
    
    # Listar arquivos no diretório
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            # Inicializar componentes
            fabricante = "UNKNOWN"
            modelo = "UNKNOWN"
            diametro = "0.0mm"
            
            # Extrair informações do nome original
            name_parts = filename.lower().replace('.jpg', '').replace('.jpeg', '').replace('.png', '').split('_')
            
            # Identificar fabricante
            for part in name_parts:
                for key, value in fabricantes.items():
                    if key in part:
                        fabricante = value
                        break
            
            # Identificar modelo
            for part in name_parts:
                for key, value in modelos.items():
                    if key in part:
                        modelo = value
                        break
            
            # Extrair diâmetro
            for part in name_parts:
                match = diametro_pattern.search(part)
                if match:
                    diametro = match.group(1).replace(',', '.') + "mm"
                    break
            
            # Criar novo nome
            new_name = f"{fabricante}_{modelo}_{diametro}.jpg"
            
            # Renomear arquivo
            old_path = os.path.join(directory, filename)
            new_path = os.path.join(directory, new_name)
            
            os.rename(old_path, new_path)
            print(f"Renamed: {filename} -> {new_name}")

# Exemplo de uso
rename_implant_images("implant_images")
```

## 4. Processamento de Imagens

Antes de usar as imagens no sistema, realizamos um processamento para padronizá-las:

### 4.1 Redimensionamento

Todas as imagens são redimensionadas para 224x224 pixels, que é o tamanho esperado pelo modelo CLIP:

```python
from PIL import Image
import os

def resize_images(directory, size=(224, 224)):
    """
    Redimensiona todas as imagens em um diretório para o tamanho especificado
    """
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            img_path = os.path.join(directory, filename)
            try:
                with Image.open(img_path) as img:
                    # Converter para RGB se for RGBA
                    if img.mode == 'RGBA':
                        img = img.convert('RGB')
                    
                    # Redimensionar
                    resized_img = img.resize(size, Image.LANCZOS)
                    
                    # Salvar
                    resized_img.save(img_path)
                    print(f"Resized: {filename}")
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

# Exemplo de uso
resize_images("implant_images")
```

### 4.2 Normalização de Contraste

Para melhorar a qualidade das imagens, aplicamos normalização de contraste:

```python
import cv2
import numpy as np
import os

def normalize_contrast(directory):
    """
    Aplica normalização de contraste (CLAHE) em todas as imagens
    """
    # Criar objeto CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            img_path = os.path.join(directory, filename)
            try:
                # Ler imagem
                img = cv2.imread(img_path)
                
                # Converter para escala de cinza
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                
                # Aplicar CLAHE
                normalized = clahe.apply(gray)
                
                # Converter de volta para BGR
                normalized_bgr = cv2.cvtColor(normalized, cv2.COLOR_GRAY2BGR)
                
                # Salvar
                cv2.imwrite(img_path, normalized_bgr)
                print(f"Normalized: {filename}")
            except Exception as e:
                print(f"Error normalizing {filename}: {str(e)}")

# Exemplo de uso
normalize_contrast("implant_images")
```

### 4.3 Pré-processamento para CLIP

Antes de extrair os embeddings, aplicamos o pré-processamento específico do CLIP:

```python
import torch
import clip
from PIL import Image
import os

def preprocess_for_clip(directory, output_dir):
    """
    Aplica o pré-processamento do CLIP em todas as imagens
    """
    # Carregar modelo CLIP
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    
    # Criar diretório de saída
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            img_path = os.path.join(directory, filename)
            out_path = os.path.join(output_dir, filename)
            
            try:
                # Abrir imagem
                image = Image.open(img_path)
                
                # Aplicar pré-processamento
                processed_img = preprocess(image)
                
                # Converter tensor para imagem e salvar
                # Nota: Isso é apenas para visualização, na prática usamos o tensor diretamente
                processed_np = processed_img.permute(1, 2, 0).numpy()
                processed_np = (processed_np * 255).astype(np.uint8)
                processed_pil = Image.fromarray(processed_np)
                processed_pil.save(out_path)
                
                print(f"Preprocessed: {filename}")
            except Exception as e:
                print(f"Error preprocessing {filename}: {str(e)}")

# Exemplo de uso
preprocess_for_clip("implant_images", "preprocessed_images")
```

## 5. Upload para DigitalOcean Spaces

Após o processamento, as imagens são enviadas para o DigitalOcean Spaces:

### 5.1 Configuração do DigitalOcean Spaces

```python
import boto3
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar cliente S3 para DigitalOcean Spaces
s3 = boto3.client(
    's3',
    endpoint_url=f"https://{os.getenv('DO_SPACES_REGION', 'nyc3')}.digitaloceanspaces.com",
    aws_access_key_id=os.getenv('DO_SPACES_KEY'),
    aws_secret_access_key=os.getenv('DO_SPACES_SECRET')
)
```

### 5.2 Upload de Imagens

```python
def upload_images_to_spaces(directory, bucket_name, prefix="referencia/"):
    """
    Faz upload de todas as imagens em um diretório para o DigitalOcean Spaces
    """
    uploaded_urls = []
    
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            local_path = os.path.join(directory, filename)
            object_name = prefix + filename
            
            try:
                # Upload do arquivo
                s3.upload_file(
                    local_path,
                    bucket_name,
                    object_name,
                    ExtraArgs={'ACL': 'public-read'}
                )
                
                # Gerar URL
                url = f"https://{bucket_name}.{os.getenv('DO_SPACES_REGION')}.digitaloceanspaces.com/{object_name}"
                uploaded_urls.append({"filename": filename, "url": url})
                
                print(f"Uploaded: {filename} -> {url}")
            except Exception as e:
                print(f"Error uploading {filename}: {str(e)}")
    
    return uploaded_urls

# Exemplo de uso
uploaded_images = upload_images_to_spaces(
    "implant_images", 
    os.getenv('DO_SPACES_BUCKET', 'raiox-images')
)

# Salvar URLs em um arquivo JSON para referência
import json
with open("uploaded_images.json", "w") as f:
    json.dump(uploaded_images, f, indent=2)
```

### 5.3 Organização no Spaces

No DigitalOcean Spaces, organizamos as imagens em diretórios:

- `raiox-images/referencia/` - Imagens de referência para o banco de dados
- `raiox-images/uploads/` - Imagens enviadas pelos usuários via webhook
- `raiox-images/test/` - Imagens para testes e validação

## 6. Extração de Embeddings

Para cada imagem, extraímos o embedding vetorial usando o modelo CLIP:

```python
import torch
import clip
from PIL import Image
import numpy as np
import json
import os

def extract_embeddings(image_urls):
    """
    Extrai embeddings CLIP de uma lista de URLs de imagens
    """
    # Carregar modelo CLIP
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    
    embeddings = []
    
    for item in image_urls:
        filename = item["filename"]
        url = item["url"]
        
        try:
            # Baixar imagem
            import requests
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Error downloading {url}: {response.status_code}")
                continue
            
            # Processar imagem
            image = Image.open(io.BytesIO(response.content))
            image_input = preprocess(image).unsqueeze(0).to(device)
            
            # Extrair embedding
            with torch.no_grad():
                image_features = model.encode_image(image_input)
                # Normalizar o vetor
                image_features /= image_features.norm(dim=-1, keepdim=True)
                # Converter para numpy array
                embedding = image_features.cpu().numpy()[0].tolist()
            
            # Extrair metadados do nome do arquivo
            parts = filename.replace('.jpg', '').replace('.jpeg', '').replace('.png', '').split('_')
            fabricante = parts[0] if len(parts) > 0 else "UNKNOWN"
            modelo = parts[1] if len(parts) > 1 else "UNKNOWN"
            diametro = parts[2] if len(parts) > 2 else "0.0mm"
            
            # Adicionar à lista
            embeddings.append({
                "filename": filename,
                "url": url,
                "fabricante": fabricante,
                "modelo": modelo,
                "diametro": diametro,
                "embedding": embedding
            })
            
            print(f"Extracted embedding: {filename}")
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
    
    # Salvar embeddings em arquivo JSON
    with open("implant_embeddings.json", "w") as f:
        json.dump(embeddings, f, indent=2)
    
    return embeddings

# Exemplo de uso
with open("uploaded_images.json", "r") as f:
    uploaded_images = json.load(f)

embeddings = extract_embeddings(uploaded_images)
```

## 7. Inserção no Banco de Dados

Os embeddings extraídos são inseridos no banco de dados PostgreSQL com pgvector:

```python
import psycopg2
import json
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def insert_embeddings_to_db(embeddings_file):
    """
    Insere embeddings no banco de dados PostgreSQL com pgvector
    """
    # Carregar embeddings do arquivo JSON
    with open(embeddings_file, "r") as f:
        embeddings = json.load(f)
    
    # Conectar ao banco de dados
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "raiox_db"),
        user=os.getenv("DB_USER", "raiox_user"),
        password=os.getenv("DB_PASSWORD")
    )
    
    # Criar cursor
    cur = conn.cursor()
    
    # Verificar se a extensão pgvector está instalada
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    # Criar tabela se não existir
    cur.execute("""
    CREATE TABLE IF NOT EXISTS implants (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        manufacturer VARCHAR(255),
        type VARCHAR(255),
        image_url TEXT,
        embedding vector(512)
    );
    """)
    
    # Criar índice para busca vetorial se não existir
    cur.execute("""
    CREATE INDEX IF NOT EXISTS implants_embedding_idx 
    ON implants 
    USING hnsw (embedding vector_cosine_ops);
    """)
    
    # Preparar dados para inserção
    data = []
    for item in embeddings:
        name = f"{item['modelo']} {item['diametro']}"
        manufacturer = item['fabricante']
        type = item['modelo']
        image_url = item['url']
        embedding = item['embedding']
        
        data.append((name, manufacturer, type, image_url, embedding))
    
    # Inserir dados
    execute_values(
        cur,
        """
        INSERT INTO implants (name, manufacturer, type, image_url, embedding)
        VALUES %s
        """,
        data,
        template="(%s, %s, %s, %s, %s::vector)"
    )
    
    # Commit e fechar conexão
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"Inserted {len(data)} implants into database")

# Exemplo de uso
insert_embeddings_to_db("implant_embeddings.json")
```

## 8. Simulação de Casos Reais

Para testar o sistema, simulamos casos reais usando as imagens coletadas:

### 8.1 Script de Simulação de Webhook

```python
import requests
import argparse
import json
import random
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def simulate_webhook(api_url):
    """
    Simula uma chamada de webhook do Jotform para a API Raiox
    """
    # Carregar URLs das imagens
    with open("uploaded_images.json", "r") as f:
        images = json.load(f)
    
    # Selecionar uma imagem aleatória
    image = random.choice(images)
    
    # Preparar dados do webhook
    webhook_data = {
        "image_url": image["url"],
        "client_id": f"test_client_{random.randint(1000, 9999)}",
        "metadata": {
            "client_name": "Paciente de Teste",
            "submission_date": "2025-06-10",
            "notes": "Simulação de caso real para teste"
        }
    }
    
    print(f"Enviando webhook para {api_url}/webhook")
    print(f"Imagem: {image['filename']}")
    print(f"URL: {image['url']}")
    
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

# Exemplo de uso
def main():
    parser = argparse.ArgumentParser(description='Simulador de Webhook para Raiox AI')
    parser.add_argument('--api', default='http://localhost:8000', help='URL da API Raiox')
    parser.add_argument('--count', type=int, default=1, help='Número de simulações')
    
    args = parser.parse_args()
    
    for i in range(args.count):
        print(f"\nSimulação {i+1}/{args.count}")
        simulate_webhook(args.api)

if __name__ == "__main__":
    main()
```

### 8.2 Script de Teste de Precisão

```python
import requests
import json
import os
import pandas as pd
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def test_accuracy(api_url, test_images_file):
    """
    Testa a precisão do sistema usando imagens de teste
    """
    # Carregar imagens de teste
    with open(test_images_file, "r") as f:
        test_images = json.load(f)
    
    results = []
    
    for image in test_images:
        filename = image["filename"]
        url = image["url"]
        expected_fabricante = image["fabricante"]
        expected_modelo = image["modelo"]
        
        print(f"Testando: {filename}")
        
        try:
            # Enviar imagem para API
            response = requests.post(
                f"{api_url}/webhook",
                json={
                    "image_url": url,
                    "client_id": "accuracy_test",
                    "metadata": {"test": True}
                }
            )
            
            if response.status_code != 200:
                print(f"  Erro: {response.status_code} - {response.text}")
                continue
            
            # Analisar resultados
            implants = response.json()
            
            # Verificar se algum dos implantes retornados corresponde ao esperado
            matches = []
            for i, implant in enumerate(implants):
                is_match_fabricante = expected_fabricante in implant["manufacturer"]
                is_match_modelo = expected_modelo in implant["name"]
                
                matches.append({
                    "position": i+1,
                    "match_fabricante": is_match_fabricante,
                    "match_modelo": is_match_modelo,
                    "full_match": is_match_fabricante and is_match_modelo
                })
            
            # Determinar melhor match
            best_match = None
            for match in matches:
                if match["full_match"]:
                    best_match = match
                    break
            
            if not best_match and any(m["match_fabricante"] for m in matches):
                best_match = next(m for m in matches if m["match_fabricante"])
            
            # Adicionar resultado
            result = {
                "filename": filename,
                "expected_fabricante": expected_fabricante,
                "expected_modelo": expected_modelo,
                "found_match": best_match is not None,
                "match_position": best_match["position"] if best_match else None,
                "full_match": best_match["full_match"] if best_match else False,
                "top_result": implants[0]["name"] if implants else None
            }
            
            results.append(result)
            
            print(f"  Resultado: {'✓' if result['found_match'] else '✗'} (Posição: {result['match_position']})")
        
        except Exception as e:
            print(f"  Erro: {str(e)}")
    
    # Calcular métricas
    df = pd.DataFrame(results)
    accuracy = df["found_match"].mean() * 100
    full_match_accuracy = df["full_match"].mean() * 100
    top1_accuracy = (df["match_position"] == 1).mean() * 100
    
    print("\nResultados:")
    print(f"Total de testes: {len(results)}")
    print(f"Acurácia geral: {accuracy:.2f}%")
    print(f"Acurácia de match completo: {full_match_accuracy:.2f}%")
    print(f"Acurácia Top-1: {top1_accuracy:.2f}%")
    
    # Salvar resultados
    df.to_csv("accuracy_results.csv", index=False)
    
    return {
        "total_tests": len(results),
        "accuracy": accuracy,
        "full_match_accuracy": full_match_accuracy,
        "top1_accuracy": top1_accuracy,
        "detailed_results": results
    }

# Exemplo de uso
accuracy_results = test_accuracy(
    "http://localhost:8000",
    "test_images.json"
)

# Salvar métricas
with open("accuracy_metrics.json", "w") as f:
    json.dump(accuracy_results, f, indent=2)
```

## 9. Considerações Éticas e Legais

### 9.1 Direitos Autorais

Ao coletar imagens da internet, é importante considerar:

- Use imagens de domínio público ou com licenças que permitam uso
- Dê preferência a imagens de catálogos oficiais dos fabricantes
- Para imagens de artigos científicos, verifique as políticas de uso justo
- Considere o uso apenas para fins educacionais e de pesquisa

### 9.2 Privacidade de Dados

Para proteger a privacidade dos pacientes:

- Nunca use imagens que contenham informações de identificação pessoal
- Verifique se as imagens estão completamente anonimizadas
- Remova metadados DICOM que possam conter informações sensíveis
- Obtenha consentimento quando usar imagens de casos reais

### 9.3 Uso Responsável

- Use as imagens apenas para os fins específicos do projeto
- Não compartilhe as imagens coletadas com terceiros
- Documente a fonte de cada imagem quando possível
- Considere criar um conjunto de dados sintético para uso público

## Conclusão

Este manual detalhou o processo completo de coleta, padronização e uso de imagens reais para o sistema Raiox AI. Seguindo estas diretrizes, é possível criar um banco de dados de referência robusto e eficaz para a identificação de implantes dentários em radiografias.

O processo de simulação de casos reais é fundamental para validar o sistema antes de sua implantação em produção, garantindo que ele seja capaz de identificar corretamente os implantes em diferentes contextos clínicos.

---

*Documento criado por Manus AI - Junho 2025*
