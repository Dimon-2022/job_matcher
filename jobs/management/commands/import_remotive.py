from datetime import timezone as dt_timezone

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from jobs.importers import BaseImportCommand

API_URL = "https://remotive.com/api/remote-jobs"

JOB_TYPE_MAP = {
    "full_time": "full_time",
    "part_time": "part_time",
    "internship": "internship",
    "contract": "freelance",
    "freelance": "freelance",
}


def parse_date(value):
    dt = parse_datetime(value or "")
    if dt is None:
        return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, dt_timezone.utc)
    return dt


class Command(BaseImportCommand):
    help = "Import remote software jobs from Remotive"
    source = "remotive"

    def fetch(self, limit):
        data = self.get_json(API_URL, {"category": "software-dev", "limit": limit})
        return data.get("jobs", [])

    def parse(self, item):
        return {
            "external_id": item["id"],
            "title": item.get("title"),
            "company": item.get("company_name"),
            "description": item.get("description"),
            "job_type": JOB_TYPE_MAP.get(item.get("job_type", "")),
            "location": item.get("candidate_required_location"),
            "work_mode": "remote",
            "url": item.get("url"),
            "created_at": parse_date(item.get("publication_date")),
        }