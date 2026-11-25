import html
import time

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.html import strip_tags

from jobs.management.commands.import_remotive import guess_level
from jobs.models import Job
from matching.services import classify_job
from notifications.services import notify_new_match

API_URL = "https://jobicy.com/api/v2/remote-jobs"
HEADERS = {"User-Agent": "JobMatcher/1.0 (student project)"}
INDUSTRIES = ["engineering", "data-science"]

JOB_TYPE_MAP = {
    "full-time": "full_time",
    "part-time": "part_time",
    "internship": "internship",
    "contract": "freelance",
}


def map_job_type(job_types):
    for value in job_types or []:
        if value.lower() in JOB_TYPE_MAP:
            return JOB_TYPE_MAP[value.lower()]
    return "full_time"


def map_level(job_level, title):
    level = (job_level or "").lower()
    if "intern" in level:
        return "intern"
    if "junior" in level or "entry" in level:
        return "junior"
    if "mid" in level:
        return "middle"
    if "lead" in level:
        return "lead"
    if "senior" in level:
        return "senior"
    return guess_level(title)


def monthly_eur(value, currency, period):
    if not value or currency != "EUR":
        return None
    if period == "yearly":
        value = value / 12
    elif period != "monthly":
        return None
    return int(round(value / 100) * 100)


class Command(BaseCommand):
    help = "Import remote IT jobs in Europe from Jobicy"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=100)

    def handle(self, *args, **options):
        created_count = updated = 0

        for i, industry in enumerate(INDUSTRIES):
            if i:
                time.sleep(1)
            response = requests.get(
                API_URL,
                params={"count": options["count"], "geo": "europe", "industry": industry},
                headers=HEADERS,
                timeout=15,
            )
            response.raise_for_status()

            for item in response.json().get("jobs", []):
                title = html.unescape(item.get("jobTitle", "")).strip()
                description = strip_tags(html.unescape(item.get("jobDescription", ""))).strip()

                category = classify_job(title, description)
                if category.startswith("not_it"):
                    category = "other"

                job_url = item.get("url", "")
                if not job_url.startswith("https://"):
                    job_url = ""

                currency = item.get("salaryCurrency")
                period = item.get("salaryPeriod")

                job, created = Job.objects.update_or_create(
                    source="jobicy",
                    external_id=str(item["id"]),
                    defaults={
                        "title": title[:200],
                        "company": (html.unescape(item.get("companyName", "")).strip() or "Unknown")[:200],
                        "description": description,
                        "category": category,
                        "level": map_level(item.get("jobLevel"), title),
                        "job_type": map_job_type(item.get("jobType")),
                        "location": (item.get("jobGeo") or "")[:100],
                        "work_mode": "remote",
                        "salary_min": monthly_eur(item.get("salaryMin"), currency, period),
                        "salary_max": monthly_eur(item.get("salaryMax"), currency, period),
                        "url": job_url,
                        "created_at": parse_datetime(item.get("pubDate") or "") or timezone.now(),
                    },
                )

                if created:
                    created_count += 1
                    notify_new_match(job)
                else:
                    updated += 1
                self.stdout.write(f"{'+' if created else '~'} [{category}] {title}")

        self.stdout.write(self.style.SUCCESS(f"New {created_count}, updated {updated}"))