from django.shortcuts import render, get_object_or_404
from pgvector.django import CosineDistance

from jobs.models import Job
from resumes.models import Resume

def match_results(request, resume_id):
    resume = get_object_or_404(Resume, pk=resume_id)

    jobs = Job.objects.annotate(
        distance=CosineDistance("embedding", resume.embedding)
    ).order_by("distance")[:10]

    for job in jobs:
        job.score = round((1 - job.distance) * 100)

    return render(request, "matching/results.html", {
        "resume": resume,
        "jobs": jobs,
    })
