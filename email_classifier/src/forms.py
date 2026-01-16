from django import forms


class UploadFileForm(forms.Form):
    emailFile = forms.FileField()