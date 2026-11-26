from datetime import datetime, timezone as dt_timezone

from jobs.importers import BaseImportCommand, guess_level

API_URL = "https://www.arbeitnow.com/api/job-board-api"

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
    if "leitung" in text or "lead" in text:
        return "lead"
    if "berufserfahren" in text or "experienced" in text:
        return "middle"
    return guess_level(title)


def parse_created_at(value):
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=dt_timezone.utc)
    return None


class Command(BaseImportCommand):
    help = "Import IT jobs from Arbeitnow (Germany / Europe)"
    source = "arbeitnow"
    trust_source_category = False
    default_limit = 100

    def fetch(self, limit):
        url = API_URL
        while url:
            payload = self.get_json(url)
            yield from payload.get("data", [])
            url = (payload.get("links") or {}).get("next")
            if url:
                self.pause()

    def parse(self, item):
        job_types = item.get("job_types") or []
        title = item.get("title") or ""
        return {
            "external_id": item["slug"],
            "title": title,
            "company": item.get("company_name"),
            "description": item.get("description"),
            "level": map_level(title, job_types),
            "job_type": map_job_type(job_types),
            "location": item.get("location"),
            "work_mode": "remote" if item.get("remote") else "onsite",
            "url": item.get("url"),
            "created_at": parse_created_at(item.get("created_at")),
        }