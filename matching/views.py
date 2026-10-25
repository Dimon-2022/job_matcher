from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from pgvector.django import CosineDistance

from jobs.models import Job
from resumes.models import Resume

THRESHOLD = 60


def match_results(request, resume_id):
    resume = get_object_or_404(Resume, pk=resume_id)
    resume_skills = set(resume.skills.all())

    jobs = Job.objects.annotate(
        distance=CosineDistance("embedding", resume.embedding)
    ).prefetch_related("skills")

    matched = []
    for job in jobs:
        job_skills = set(job.skills.all())
        common = job_skills & resume_skills

        if job_skills:
            skill_score = len(common) / len(job_skills)
        else:
            skill_score = 0

        semantic = 1 - job.distance
        job.score = round((0.6 * skill_score + 0.4 * semantic) * 100)

        if job.score >= THRESHOLD:
            matched.append(job)

    matched = sorted(matched, key=lambda job: job.score, reverse=True)

    paginator = Paginator(matched, 5)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "matching/results.html", {
        "resume": resume,
        "page_obj": page_obj,
    })