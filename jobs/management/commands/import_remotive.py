import html
from datetime import timezone as dt_timezone

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.html import strip_tags

from jobs.models import Job
from matching.services import classify_job
from notifications.services import notify_new_match

API_URL = "https://remotive.com/api/remote-jobs"
HEADERS = {"User-Agent": "JobMatcher/1.0 (student project)"}

JOB_TYPE_MAP = {
    "full_time": "full_time",
    "part_time": "part_time",
    "internship": "internship",
    "contract": "freelance",
    "freelance": "freelance",
}


def guess_level(title):
    lowered = title.lower()
    if any(word in lowered for word in ("intern", "trainee", "praktikant", "werkstudent")):
        return "intern"
    if any(word in lowered for word in ("junior", "jr.", "entry", "graduate")):
        return "junior"
    if any(word in lowered for word in ("lead", "principal", "staff", "head of")):
        return "lead"
    if any(word in lowered for word in ("senior", "sr.")):
        return "senior"
    return "middle"


def parse_date(value):
    dt = parse_datetime(value or "")
    if dt is None:
        return timezone.now()
    if timezone.is_naive(dt):  # Remotive дає дату без часового поясу
        dt = timezone.make_aware(dt, dt_timezone.utc)
    return dt


class Command(BaseCommand):
    help = "Import remote software jobs from Remotive"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)

    def handle(self, *args, **options):
        limit = options["limit"]

        try:
            response = requests.get(
                API_URL,
                params={"category": "software-dev", "limit": limit},
                headers=HEADERS,
                timeout=15,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            self.stderr.write(self.style.ERROR(f"Request failed: {error}"))
            return

        # Remotive іноді ігнорує limit — обрізаємо самі
        items = response.json().get("jobs", [])[:limit]
        created_count = updated = 0

        for item in items:
            title = html.unescape(item.get("title", "")).strip()
            description = strip_tags(html.unescape(item.get("description", ""))).strip()

            category = classify_job(title, description)
            if category.startswith("not_it"):
                category = "other"  # ми вже взяли лише software-dev: довіряємо джерелу

            job_url = item.get("url", "")
            if not job_url.startswith("https://"):
                job_url = ""

            job, created = Job.objects.update_or_create(
                source="remotive",
                external_id=str(item["id"]),
                defaults={
                    "title": title[:200],
                    "company": (html.unescape(item.get("company_name", "")).strip() or "Unknown")[:200],
                    "description": description,
                    "category": category,
                    "level": guess_level(title),
                    "job_type": JOB_TYPE_MAP.get(item.get("job_type", ""), "full_time"),
                    "location": (item.get("candidate_required_location") or "")[:100],
                    "work_mode": "remote",
                    "url": job_url,
                    "created_at": parse_date(item.get("publication_date")),
                },
            )

            if created:
                created_count += 1
                notify_new_match(job)
            else:
                updated += 1
            self.stdout.write(f"{'+' if created else '~'} [{category}] {title}")

        self.stdout.write(self.style.SUCCESS(f"New {created_count}, updated {updated}"))