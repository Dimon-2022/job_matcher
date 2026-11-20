from html import unescape

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.html import strip_tags

from jobs.models import Job
from matching.services import classify_job
from notifications.services import notify_new_match

API_URL = "https://remotive.com/api/remote-jobs"

JOB_TYPE_MAP = {
    "full_time": "full_time",
    "part_time": "part_time",
    "internship": "internship",
    "freelance": "freelance",
    "contract": "freelance",
}


def guess_level(title):
    title = title.lower()
    words = title.split()
    if "intern" in title:
        return "intern"
    if "junior" in title or "jr" in words:
        return "junior"
    if "lead" in title or "principal" in title or "head of" in title:
        return "lead"
    if "senior" in title or "sr" in words:
        return "senior"
    return "middle"


def parse_date(value):
    date = parse_datetime(value or "")
    if date is None:
        return timezone.now()
    if timezone.is_naive(date):
        date = timezone.make_aware(date)
    return date


class Command(BaseCommand):
    help = "Import remote IT jobs from the Remotive public API"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100, help="How many jobs to import")

    def handle(self, *args, **options):
        limit = options["limit"]
        self.stdout.write(f"Fetching up to {limit} jobs from Remotive...")

        try:
            response = requests.get(
                API_URL,
                params={"category": "software-dev", "limit": limit},
                headers={"User-Agent": "JobMatcher/1.0 (student project)"},
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            self.stderr.write(self.style.ERROR(f"Request failed: {error}"))
            return

        items = response.json().get("jobs", [])[:limit]
        created_count = updated_count = skipped_count = 0

        for item in items:
            title = unescape(item.get("title", ""))[:200]
            description = unescape(strip_tags(item.get("description", "")))
            category = classify_job(title, description)

            if category.startswith("not_it"):
                skipped_count += 1
                self.stdout.write(f"  - skipped ({category}): {title}")
                continue

            url = item.get("url", "")

            job, created = Job.objects.update_or_create(
                source="remotive",
                external_id=str(item["id"]),
                defaults={
                    "title": title,
                    "company": unescape(item.get("company_name", ""))[:200],
                    "description": description,
                    "location": item.get("candidate_required_location", "")[:200],
                    "work_mode": "remote",
                    "job_type": JOB_TYPE_MAP.get(item.get("job_type"), "full_time"),
                    "category": category,
                    "level": guess_level(title),
                    "url": url if url.startswith("https://") else "",
                    "created_at": parse_date(item.get("publication_date")),
                },
            )

            if created:
                created_count += 1
                notify_new_match(job)
            else:
                updated_count += 1
            self.stdout.write(f"  {'+' if created else '~'} [{category}] {title}")

        self.stdout.write(self.style.SUCCESS(
            f"Done: {created_count} created, {updated_count} updated, {skipped_count} skipped."
        ))