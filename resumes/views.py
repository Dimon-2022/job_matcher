from django.shortcuts import render, redirect

from .forms import ResumeForm
from .services import extract_text_from_pdf


def upload_resume(request):
    if request.method == "POST":
        form = ResumeForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.text = extract_text_from_pdf(resume.file)
            resume.save()
            return redirect("upload_resume")
    else:
        form = ResumeForm()

    return render(request, "resumes/upload.html", {"form": form})