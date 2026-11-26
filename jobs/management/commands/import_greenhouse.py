import requests
from django.utils.dateparse import parse_datetime

from jobs.importers import BaseImportCommand
from jobs.models import CompanyFeed

API_URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"

EUROPE_HINTS = (
    "europe", "emea", "eu ", "germany", "deutschland", "berlin", "munich", "münchen", "hamburg",
    "frankfurt", "cologne", "köln", "austria", "vienna", "wien", "switzerland", "zurich", "zürich",
    "slovakia", "bratislava", "košice", "kosice", "czech", "prague", "praha", "brno", "poland",
    "warsaw", "kraków", "krakow", "wrocław", "hungary", "budapest", "netherlands", "amsterdam",
    "spain", "madrid", "barcelona", "france", "paris", "ireland", "dublin", "portugal", "lisbon",
    "united kingdom", "london", "denmark", "copenhagen", "sweden", "stockholm", "finland",
    "helsinki", "norway", "oslo", "romania", "bucharest", "italy", "milan", "belgium", "brussels",
    "estonia", "tallinn", "latvia", "riga", "lithuania", "vilnius", "ukraine", "kyiv",
)


def is_in_europe(location):
    lowered = f" {location.lower()} "
    return any(hint in lowered for hint in EUROPE_HINTS)


class Command(BaseImportCommand):
    help = "Import European jobs from company Greenhouse boards"
    source = "greenhouse"
    trust_source_category = False
    default_limit = 300

    def fetch(self, limit):
        feeds = CompanyFeed.objects.filter(ats="greenhouse", is_active=True)
        for i, feed in enumerate(feeds):
            if i:
                self.pause()
            try:
                data = self.get_json(API_URL.format(slug=feed.slug), {"content": "true"})
            except requests.RequestException as error:
                self.stderr.write(f"! {feed.name}: {error}")
                continue
            for job in data.get("jobs", []):
                yield feed, job

    def parse(self, item):
        feed, job = item
        location = (job.get("location") or {}).get("name") or ""
        if not is_in_europe(location):
            return None

        return {
            "external_id": f"{feed.slug}-{job['id']}",
            "title": job.get("title"),
            "company": feed.name,
            "description": job.get("content"),
            "department": ", ".join(d.get("name", "") for d in job.get("departments") or []),
            "location": location,
            "work_mode": "remote" if "remote" in location.lower() else "onsite",
            "url": job.get("absolute_url"),
            "created_at": parse_datetime(job.get("first_published") or job.get("updated_at") or ""),
        }