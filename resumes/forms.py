from django import forms
from .models import Resume


class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ["file"]
        widgets = {
            "file": forms.FileInput(attrs={"class": "form-control", "accept": ".pdf"}),
        }