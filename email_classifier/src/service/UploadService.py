import os, PyPDF2, logging, re, json, os
import requests
from dotenv import load_dotenv
from typing import List, Dict
from django.core.files.uploadedfile import UploadedFile
from django.http import HttpRequest
from pathlib import Path

load_dotenv()

API_TOKEN: str = os.getenv("API_TOKEN")
API_URL: str = os.getenv("API_URL")
MODEL_NAME: str = os.getenv("MODEL_NAME")
BASE_DIR = Path(__file__).resolve().parent.parent.parent

logger = logging.getLogger(__name__)

def formatar_json(texto: str) -> dict:
    try:
        match = re.search(r'\{.*\}', texto, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError("Formato JSON não detectado.")
    except Exception as e:
        logger.error(f"Falha ao formatar JSON: {e}")
        raise

def query_analyse_email(text: str) -> dict:
    prompt = f"""
    Você é um Assistente. Sua missão é analisar e-mails e decidir se eles exigem ação humana (Produtivo) ou se são distrações/automáticos (Improdutivo).

    REGRAS PARA A SUGESTÃO:
    1. Se for PRODUTIVO: Escreva uma resposta curta, profissional e personalizada que o usuário possa enviar agora.
    2. Se for IMPRODUTIVO: Sugira uma ação de limpeza em relação ao email.
    3. Nunca use frases genéricas. Seja claro.

    Email: "{text[:1200]}"

    Responda estritamente neste formato JSON:
    {{
        "categoria": "Produtivo" ou "Improdutivo",
        "porcentagem": 0-100 que indica a confiança na categorização,
        "sugestão": "sua sugestão executiva aqui"
    }}
    """

    try:
        response = requests.post(
            url=API_URL,
            headers={
                "Authorization": f"Bearer {API_TOKEN}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000", 
                "Email Classifier": "Email Classifier App"
            },
            data=json.dumps({
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}]
            }),
            timeout=30
        )

        response.raise_for_status()
        
        response = response.json()
        response = response['choices'][0]['message']['content']

        return formatar_json(response)

    except Exception as e:
        logger.error(f"Erro na análise: {e}")
        return {
            "categoria": "Indefinido",
            "porcentagem": 0,
            "sugestão": "O sistema não pôde gerar uma resposta automática para este item."
        }

def save_uploaded_file(f: UploadedFile, file_path: str) -> None:
    with open(file_path, "wb+") as destination:
        for chunk in f.chunks():
            destination.write(chunk)

def read_content_file(file_path: str) -> str:
    with open(file_path, "r") as file:
        content = file.read()
    
    return content

def read_content_file_pdf(file_path: str) -> str:
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)

        content = ""
        for page in reader.pages:
            text_page = page.extract_text()
            if text_page:
                content += text_page

        return content

def normalize_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def handle_file(f: UploadedFile) -> dict:
    file_path = BASE_DIR / 'src' / 'files' / f.name

    file_path.parent.mkdir(parents=True, exist_ok=True)

    save_uploaded_file(f, file_path)

    if f.name.endswith(".pdf"):
        text = read_content_file_pdf(file_path)
    else:
        text = read_content_file(file_path)

    if not text:
        return {"categoria": "Erro", "porcentagem": 0, "sugestão": "Erro na extração do texto."}

    return query_analyse_email(normalize_text(text))

def handle_text_area(text: str) -> dict:
    return query_analyse_email(normalize_text(text))

def handle_request(request: HttpRequest) -> List[Dict[str, any]]:
    files: List[UploadedFile] = request.FILES.getlist('emailFile')
    text_area: str = request.POST.get('emailTextArea', '')
    result = []

    if text_area.strip():
        try:
            content = handle_text_area(text_area)
            result.append(formatSucess("Texto Inserido", content))

        except Exception as e:
            logger.exception(f"Error processing text area input: {e}")
            result.append(formatError("Texto Inserido", str(e)))

    if not files:
        return result
    
    for f in files:
        try:
            content = handle_file(f)
            result.append(formatSucess(f.name, content))

        except Exception as e:
            logger.exception(f"Error processing file {f.name}: {e}")
            result.append(formatError(f.name, str(e)))

    return result

def formatSucess(nome: str, content: dict) -> dict:

    return {
        "nome": nome,
        "categoria": content["categoria"],
        "porcentagem": content["porcentagem"],
        "sugestão": content["sugestão"],
        "sucesso": True
    }

def formatError(nome: str, error: str) -> dict:
    return {
        "nome": nome,
        "error": error,
        "sucesso": False
    }