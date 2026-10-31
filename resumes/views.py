from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .forms import ResumeForm
from .services import extract_text_from_pdf

@login_required
def upload_resume(request):
    if request.method == "POST":
        form = ResumeForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.owner = request.user
            resume.text = extract_text_from_pdf(resume.file)
            resume.save()
            return redirect("match_results", resume_id=resume.pk)
    else:
        form = ResumeForm()

    return render(request, "resumes/upload.html", {"form": form})
