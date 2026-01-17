from django.shortcuts import render, HttpResponse
from django.http import HttpRequest
from .forms import UploadFileForm
import logging

from .service.FileProcessorService import FileProcessorService
from .service.EmailAnalyzerService import EmailAnalyzerService


logger = logging.getLogger(__name__)
fileProcessor = FileProcessorService(EmailAnalyzerService())

# Create your views here.
def home(request: HttpRequest) -> HttpResponse:
    return render(request, "home.html")

def classify_email(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            response = fileProcessor.handle_request(request)

            #logger.warning(f"Classification response: {response}")
            return render(request, "classify_email.html", {"data": response})
        else:
            logger.warning(f"Formulário inválido. Tente novamente. {form.errors}")
            return render(request, "home.html", {"form": form})