import html
import time

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.html import strip_tags

from jobs.models import Job
from matching.services import classify_job
from notifications.services import notify_new_match

HEADERS = {"User-Agent": "JobMatcher/1.0 (student project)"}


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


def clean_text(value):
    return strip_tags(html.unescape(value or "")).strip()


class BaseImportCommand(BaseCommand):
    source = None
    trust_source_category = True
    default_limit = 50
    pause_seconds = 1

    def fetch(self, limit):
        raise NotImplementedError

    def parse(self, item):
        raise NotImplementedError

    def get_json(self, url, params=None):
        response = requests.get(url, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response.json()

    def pause(self):
        time.sleep(self.pause_seconds)

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=self.default_limit)

    def handle(self, *args, **options):
        limit = options["limit"]
        stats = {"new": 0, "updated": 0, "skipped": 0}

        try:
            for item in self.fetch(limit):
                if sum(stats.values()) >= limit:
                    break
                self.import_item(item, stats)
        except requests.RequestException as error:
            self.stderr.write(self.style.ERROR(f"Request failed: {error}"))

        self.stdout.write(self.style.SUCCESS(
            f"[{self.source}] new {stats['new']}, updated {stats['updated']}, skipped {stats['skipped']}"
        ))

    def import_item(self, item, stats):
        data = self.parse(item)
        if data is None:
            stats["skipped"] += 1
            return

        title = clean_text(data.get("title"))
        description = clean_text(data.get("description"))

        category = classify_job(title, description)
        if category.startswith("not_it"):
            if not self.trust_source_category:
                stats["skipped"] += 1
                self.stdout.write(f"- [{category}] {title}")
                return
            category = "other"

        url = data.get("url") or ""
        if not url.startswith("https://"):
            url = ""

        job, created = Job.objects.update_or_create(
            source=self.source,
            external_id=str(data["external_id"]),
            defaults={
                "title": title[:200],
                "company": (clean_text(data.get("company")) or "Unknown")[:200],
                "description": description,
                "category": category,
                "level": data.get("level") or guess_level(title),
                "job_type": data.get("job_type") or "full_time",
                "location": (data.get("location") or "")[:100],
                "work_mode": data.get("work_mode") or "remote",
                "salary_min": data.get("salary_min"),
                "salary_max": data.get("salary_max"),
                "url": url,
                "created_at": data.get("created_at") or timezone.now(),
            },
        )

        if created:
            stats["new"] += 1
            notify_new_match(job)
        else:
            stats["updated"] += 1
        self.stdout.write(f"{'+' if created else '~'} [{category}] {title}")