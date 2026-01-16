from django import forms


class UploadFileForm(forms.Form):
    emailTextArea = forms.CharField(widget=forms.Textarea, required=False)
    emailFile = forms.FileField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        text = cleaned_data.get("emailTextArea", "").strip()
        files = self.files.getlist("emailFile")

        if not text and not files:
            raise forms.ValidationError("Insira texto ou faça upload de pelo menos um arquivo.")
        
        return cleaned_data