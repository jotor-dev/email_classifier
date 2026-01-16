from django.shortcuts import render, HttpResponse
from django.http import HttpRequest
from django.contrib import messages
from .forms import UploadFileForm
import logging


from .service.UploadService import handle_request

# Create your views here.
def home(request: HttpRequest) -> HttpResponse:
    return render(request, "home.html")

def classify_email(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            response = handle_request(request)

            logger = logging.getLogger(__name__)
            logger.warning(f"Classification response: {response}")
            return render(request, "classify_email.html", {"data": response})
        else:
            messages.error(request, "Formulário inválido. Tente novamente.")
            return render(request, "classify_email.html", {"form": form})