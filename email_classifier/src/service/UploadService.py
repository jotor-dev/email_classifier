import os
import PyPDF2
from dotenv import load_dotenv
from typing import List, Dict
from django.core.files.uploadedfile import UploadedFile
from django.http import HttpRequest
from huggingface_hub import InferenceClient
import logging
from pathlib import Path

load_dotenv()

API_TOKEN: str = os.getenv("API_TOKEN")
API_URL: str = os.getenv("API_URL")
MODEL_NAME: str = os.getenv("MODEL_NAME")
headers: dict = {"Authorization": f"Bearer {API_TOKEN}"}
BASE_DIR = Path(__file__).resolve().parent.parent.parent

client = InferenceClient(provider="auto", api_key=API_TOKEN)
logger = logging.getLogger(__name__)

def query_huggingface_api(text: str) -> list:
    try:
        response = client.zero_shot_classification(
            text,
            model=MODEL_NAME,
            candidate_labels=["Produtivo", "Improdutivo"]
        )
        return response
    except Exception as e:
        print(f"Error querying Huggingface API: {e}")
        return {"error": str(e)}

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
            content += page.extract_text()

        return content

def handle_file(f: UploadedFile) -> dict:
    file_path = BASE_DIR / 'src' / 'files' / f.name

    file_path.parent.mkdir(parents=True, exist_ok=True)

    save_uploaded_file(f, file_path)

    if f.name.endswith(".pdf"):
        content = read_content_file_pdf(file_path)
    else:
        content = read_content_file(file_path)

    return query_huggingface_api(content)

def handle_text_area(text: str) -> dict:
    return query_huggingface_api(text)

def handle_request(request: HttpRequest) -> List[Dict[str, any]]:
    files: List[UploadedFile] = request.FILES.getlist('emailFile')
    text_area: str = request.POST.get('emailTextArea', '')
    result = []

    if text_area.strip():
        try:
            content = handle_text_area(text_area)
            result.append(formatSucess("Texto Inserido", content))

        except Exception as e:
            logger.warning(f"Error processing text area input: {e}")
            result.append(formatError("Texto Inserido", str(e)))

    for f in files:
        try:
            content = handle_file(f)
            result.append(formatSucess(f.name, content))

        except Exception as e:
            logger.warning(f"Error processing file {f.name}: {e}")
            result.append(formatError(f.name, str(e)))

    return result

def formatSucess(nome: str, content: dict) -> dict:
    best_prediction = content[0]

    return {
        "nome": nome,
        "categoria": best_prediction.label,
        "porcentagem": round(best_prediction.score * 100, 2),
        "sugestao": "Resposta" if best_prediction.label == "Produtivo" else "Improdutivo",
        "sucesso": True
    }

def formatError(nome: str, error: str) -> dict:
    return {
        "nome": nome,
        "error": error,
        "sucesso": False
    }