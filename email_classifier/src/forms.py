from django import forms


class UploadFileForm(forms.Form):
    emailTextArea = forms.CharField(widget=forms.Textarea, required=False)
    emailFile = forms.FileField(required=False)