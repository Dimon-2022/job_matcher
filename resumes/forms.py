from django import forms

from .models import Resume

MAX_FILE_SIZE = 5 * 1024 * 1024 #5 MB

ERROR_NOT_PDF_EXTENSION = "Only PDF files are allowed."
ERROR_TOO_LARGE = "File is too large (max 5 MB)."
ERROR_INVALID_PDF = "This file is not a valid PDF."

PDF_SIGNATURE = b"%PDF-"

class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ["file"]
        widgets = {
            "file": forms.FileInput(attrs={"accept": ".pdf,application/pdf"}),
        }

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if not file:
            return file

        if not file.name.lower().endswith(".pdf"):
            raise forms.ValidationError(ERROR_NOT_PDF_EXTENSION)

        if file.size > MAX_FILE_SIZE:
            raise forms.ValidationError(ERROR_TOO_LARGE)

        header = file.read(len(PDF_SIGNATURE))
        file.seek(0)
        if header != PDF_SIGNATURE:
            raise forms.ValidationError(ERROR_INVALID_PDF)

        return file