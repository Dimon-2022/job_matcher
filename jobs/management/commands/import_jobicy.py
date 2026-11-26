from django.utils.dateparse import parse_datetime

from jobs.importers import BaseImportCommand, guess_level

API_URL = "https://jobicy.com/api/v2/remote-jobs"
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


class Command(BaseImportCommand):
    help = "Import remote IT jobs in Europe from Jobicy"
    source = "jobicy"
    default_limit = 100

    def fetch(self, limit):
        for i, industry in enumerate(INDUSTRIES):
            if i:
                self.pause()
            data = self.get_json(API_URL, {"count": limit, "geo": "europe", "industry": industry})
            yield from data.get("jobs", [])

    def parse(self, item):
        title = item.get("jobTitle") or ""
        currency = item.get("salaryCurrency")
        period = item.get("salaryPeriod")
        return {
            "external_id": item["id"],
            "title": title,
            "company": item.get("companyName"),
            "description": item.get("jobDescription"),
            "level": map_level(item.get("jobLevel"), title),
            "job_type": map_job_type(item.get("jobType")),
            "location": item.get("jobGeo"),
            "work_mode": "remote",
            "salary_min": monthly_eur(item.get("salaryMin"), currency, period),
            "salary_max": monthly_eur(item.get("salaryMax"), currency, period),
            "url": item.get("url"),
            "created_at": parse_datetime(item.get("pubDate") or ""),
        }