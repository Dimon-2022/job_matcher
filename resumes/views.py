from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DeleteView

from accounts.mixins import SeekerRequiredMixin
from .forms import ResumeForm
from .models import Resume
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

class MyResumesView(SeekerRequiredMixin,ListView):
    template_name = "resumes/my_resumes.html"
    context_object_name = "resumes"

    def get_queryset(self):
        return Resume.objects.filter(owner=self.request.user).order_by("-uploaded_at")

class ResumeDeleteView(SeekerRequiredMixin, DeleteView):
    model = Resume
    template_name = "resumes/resume_confirm_delete.html"
    success_url = reverse_lazy("resumes")

    def get_queryset(self):
        return Resume.objects.filter(owner=self.request.user)