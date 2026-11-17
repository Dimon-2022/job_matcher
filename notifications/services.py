from django.urls import reverse
from pgvector.django import CosineDistance

from matching.services import calculate_score
from resumes.models import Resume
from .models import Notification

MATCH_THRESHOLD = 60


def find_matching_seekers(job, threshold=MATCH_THRESHOLD):
    if job.embedding is None:
        return []

    latest_resumes = (
        Resume.objects.filter(owner__profile__role="seeker", embedding__isnull=False)
        .order_by("owner_id", "-uploaded_at")
        .distinct("owner_id")
        .annotate(distance=CosineDistance("embedding", job.embedding))
        .prefetch_related("skills")
    )

    matches = []
    for resume in latest_resumes:
        job.distance = resume.distance
        score = calculate_score(job, set(resume.skills.all()))
        if score >= threshold:
            matches.append((resume.owner, score))
    return matches


def notify_new_match(job):
    for user, score in find_matching_seekers(job):
        Notification.objects.get_or_create(
            user=user,
            kind="new_match",
            job=job,
            defaults={
                "message": f"New job matches your profile ({score}%): {job.title} at {job.company}",
                "url": reverse("job_detail", args=[job.pk]),
            },
        )


def notify_job_closed(job):
    for user, score in find_matching_seekers(job):
        Notification.objects.get_or_create(
            user=user,
            kind="job_closed",
            job=job,
            defaults={
                "message": f"{job.title} at {job.company} is closed. See what it was about and similar open jobs.",
                "url": reverse("job_detail", args=[job.pk]),
            },
        )