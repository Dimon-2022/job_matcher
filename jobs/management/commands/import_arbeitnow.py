import html
import time
from datetime import datetime, timezone as dt_timezone

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.html import strip_tags

from jobs.management.commands.import_remotive import guess_level
from jobs.models import Job
from matching.services import classify_job
from notifications.services import notify_new_match

API_URL = "https://www.arbeitnow.com/api/job-board-api"
HEADERS = {"User-Agent": "JobMatcher/1.0 (student project)"}

INTERN_WORDS = ("intern", "praktikum", "werkstudent", "working student")
PART_TIME_WORDS = ("part", "teilzeit", "minijob")
FREELANCE_WORDS = ("freelance", "contract", "freiberuf")


def map_job_type(job_types):
    text = " ".join(job_types).lower()
    if any(word in text for word in INTERN_WORDS):
        return "internship"
    if any(word in text for word in PART_TIME_WORDS):
        return "part_time"
    if any(word in text for word in FREELANCE_WORDS):
        return "freelance"
    return "full_time"


def map_level(title, job_types):
    text = " ".join(job_types).lower()
    if any(word in text for word in INTERN_WORDS):
        return "intern"
    if "berufseinsteiger" in text or "entry" in text:
        return "junior"
    return guess_level(title)


def parse_created_at(value):
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=dt_timezone.utc)
    return timezone.now()


class Command(BaseCommand):
    help = "Import IT jobs from Arbeitnow (Germany / Europe)"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        limit = options["limit"]
        url = API_URL
        processed = created_count = skipped = 0

        while url and processed < limit:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            payload = response.json()

            for item in payload.get("data", []):
                if processed >= limit:
                    break
                processed += 1

                title = html.unescape(item.get("title", "")).strip()
                description = strip_tags(html.unescape(item.get("description", ""))).strip()
                company = html.unescape(item.get("company_name", "")).strip() or "Unknown"
                job_types = item.get("job_types") or []

                category = classify_job(title, description)
                if category.startswith("not_it"):
                    skipped += 1
                    self.stdout.write(f"- [{category}] {title}")
                    continue

                job_url = item.get("url", "")
                if not job_url.startswith("https://"):
                    job_url = ""

                job, created = Job.objects.update_or_create(
                    source="arbeitnow",
                    external_id=item["slug"],
                    defaults={
                        "title": title[:200],
                        "company": company[:200],
                        "description": description,
                        "category": category,
                        "level": map_level(title, job_types),
                        "job_type": map_job_type(job_types),
                        "location": (item.get("location") or "")[:100],
                        "work_mode": "remote" if item.get("remote") else "onsite",
                        "url": job_url,
                        "created_at": parse_created_at(item.get("created_at")),
                    },
                )

                if created:
                    created_count += 1
                    notify_new_match(job)
                self.stdout.write(f"{'+' if created else '~'} [{category}] {title}")

            url = (payload.get("links") or {}).get("next")
            if url:
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS(
            f"Processed {processed}, new {created_count}, skipped (not IT) {skipped}"
        ))