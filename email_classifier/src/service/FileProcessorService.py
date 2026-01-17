import PyPDF2, logging, re
from typing import List, Dict
from django.core.files.uploadedfile import UploadedFile
from django.http import HttpRequest
from pathlib import Path
from .EmailAnalyzerService import EmailAnalyzerService

class FileProcessorService:

    def __init__(self, analyzer: EmailAnalyzerService) -> None:
        self.BASE_DIR = Path(__file__).resolve().parent.parent.parent
        self.logger = logging.getLogger(__name__)
        self.analyzer = analyzer

    def handle_request(self, request: HttpRequest) -> List[Dict[str, any]]:
        files: List[UploadedFile] = request.FILES.getlist('emailFile')
        text_area: str = request.POST.get('emailTextArea', '')
        result = []

        if text_area.strip():
            try:
                content = self.handle_text_area(text_area)
                result.append(self.formatSucess("Texto Inserido", content))

            except Exception as e:
                self.logger.exception(f"Error processing text area input: {e}")
                result.append(self.formatError("Texto Inserido", str(e)))

        if not files:
            return result
        
        for f in files:
            try:
                content = self.handle_file(f)
                result.append(self.formatSucess(f.name, content))

            except Exception as e:
                self.logger.exception(f"Error processing file {f.name}: {e}")
                result.append(self.formatError(f.name, str(e)))

        return result

    def save_uploaded_file(self, f: UploadedFile, file_path: str) -> None:
        with open(file_path, "wb+") as destination:
            for chunk in f.chunks():
                destination.write(chunk)

    def read_content_file(self, file_path: str) -> str:
        with open(file_path, "r") as file:
            content = file.read()
        
        return content

    def read_content_file_pdf(self, file_path: str) -> str:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)

            content = ""
            for page in reader.pages:
                text_page = page.extract_text()
                if text_page:
                    content += text_page

            return content

    def handle_file(self, f: UploadedFile) -> dict:
        file_path = self.BASE_DIR / 'src' / 'files' / f.name

        file_path.parent.mkdir(parents=True, exist_ok=True)

        self.save_uploaded_file(f, file_path)

        if f.name.endswith(".pdf"):
            text = self.read_content_file_pdf(file_path)
        else:
            text = self.read_content_file(file_path)

        if not text:
            return {"categoria": "Erro", "porcentagem": 0, "sugestão": "Erro na extração do texto."}

        return self.analyzer.query_analyse_email(self.normalize_text(text))

    def handle_text_area(self, text: str) -> dict:
        return self.analyzer.query_analyse_email(self.normalize_text(text))

    def normalize_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text

    def formatSucess(self, nome: str, content: dict) -> dict:

        return {
            "nome": nome,
            "categoria": content["categoria"],
            "porcentagem": content["porcentagem"],
            "sugestão": content["sugestão"],
            "sucesso": True
        }

    def formatError(self, nome: str, error: str) -> dict:
        return {
            "nome": nome,
            "error": error,
            "sucesso": False
        }