from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404

from resumes.models import Resume
from .services import find_matching_jobs


@login_required
def match_results(request, resume_id):
    resume = get_object_or_404(Resume, pk=resume_id, owner=request.user)
    jobs = find_matching_jobs(resume)
    page_obj = Paginator(jobs, 5).get_page(request.GET.get("page"))

    return render(request, "matching/results.html", {
        "resume": resume,
        "page_obj": page_obj,
    })