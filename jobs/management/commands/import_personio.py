import requests
from defusedxml import ElementTree
from django.utils.dateparse import parse_datetime

from jobs.importers import BaseImportCommand, guess_level
from jobs.models import CompanyFeed

FEED_URL = "https://{slug}.jobs.personio.de/xml"
JOB_URL = "https://{slug}.jobs.personio.de/job/{id}"

EMPLOYMENT_MAP = {
    "intern": "internship",
    "trainee": "internship",
    "working_student": "part_time",
    "freelance": "freelance",
}

SENIORITY_MAP = {
    "student": "intern",
    "entry-level": "junior",
    "experienced": "middle",
    "executive": "lead",
}


def text(element, tag):
    found = element.find(tag)
    return (found.text or "").strip() if found is not None else ""


def build_description(position):
    parts = []
    for block in position.findall("jobDescriptions/jobDescription"):
        parts.append(f"{text(block, 'name')}\n{text(block, 'value')}")
    return "\n\n".join(parts)


class Command(BaseImportCommand):
    help = "Import jobs from company Personio career feeds (DACH)"
    source = "personio"
    trust_source_category = False
    default_limit = 300

    def fetch(self, limit):
        feeds = CompanyFeed.objects.filter(ats="personio", is_active=True)
        for i, feed in enumerate(feeds):
            if i:
                self.pause()
            try:
                response = self.get_response(FEED_URL.format(slug=feed.slug), {"language": "en"})
                root = ElementTree.fromstring(response.content)
            except (requests.RequestException, ElementTree.ParseError) as error:
                self.stderr.write(f"! {feed.name}: {error}")
                continue
            for position in root.findall("position"):
                yield feed, position

    def parse(self, item):
        feed, position = item
        job_id = text(position, "id")
        title = text(position, "name")
        office = text(position, "office")
        schedule = text(position, "schedule")

        job_type = EMPLOYMENT_MAP.get(text(position, "employmentType"))
        if not job_type:
            job_type = "part_time" if schedule == "part-time" else "full_time"

        return {
            "external_id": f"{feed.slug}-{job_id}",
            "title": title,
            "company": text(position, "subcompany") or feed.name,
            "description": build_description(position),
            "department": text(position, "department"),
            "level": SENIORITY_MAP.get(text(position, "seniority")) or guess_level(title),
            "job_type": job_type,
            "location": office,
            "work_mode": "remote" if "remote" in office.lower() else "onsite",
            "url": JOB_URL.format(slug=feed.slug, id=job_id),
            "created_at": parse_datetime(text(position, "createdAt")),
        }