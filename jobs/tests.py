from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from datetime import timedelta
from django.utils import timezone

from .templatetags.job_extras import ago

from io import StringIO
from unittest.mock import patch, MagicMock

import requests
from django.core.management import call_command

from accounts.models import Profile
from .models import Job


class JobAccessTests(TestCase):

    def setUp(self):
        self.employer = User.objects.create_user(username="employer", password="pass12345")
        Profile.objects.create(user=self.employer, role="employer")

        self.other_employer = User.objects.create_user(username="other", password="pass12345")
        Profile.objects.create(user=self.other_employer, role="employer")

        self.seeker = User.objects.create_user(username="seeker", password="pass12345")
        Profile.objects.create(user=self.seeker, role="seeker")

        self.job = Job.objects.create(
            title="Python Developer",
            company="CodeWave",
            location="Košice",
            description="Build web apps with Django.",
            owner=self.employer,
        )

    def test_guest_redirected_to_login(self):
        response = self.client.get(reverse("job_create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_seeker_cannot_create_job(self):
        self.client.force_login(self.seeker)
        response = self.client.get(reverse("job_create"))
        self.assertEqual(response.status_code, 403)

    @patch("jobs.forms.geocode", return_value={"name": "Bratislava", "lat": 48.14, "lon": 17.10})
    def test_employer_can_create_job(self, mock_geocode):
        self.client.force_login(self.employer)
        response = self.client.post(reverse("job_create"), {
            "title": "Data Analyst",
            "company": "InsightLab",
            "location": "bratislava",
            "work_mode": "onsite",
            "category": "data_analyst",
            "level": "junior",
            "job_type": "full_time",
            "description": "Analyze data with SQL and Excel.",
        })
        self.assertEqual(response.status_code, 302)
        new_job = Job.objects.get(title="Data Analyst")
        self.assertEqual(new_job.owner, self.employer)
        self.assertEqual(new_job.location, "Bratislava")
        self.assertEqual(new_job.latitude, 48.14)

    def test_owner_can_edit_job(self):
        self.client.force_login(self.employer)
        response = self.client.get(reverse("job_update", args=[self.job.pk]))
        self.assertEqual(response.status_code, 200)

    def test_other_employer_cannot_edit_job(self):
        self.client.force_login(self.other_employer)
        response = self.client.get(reverse("job_update", args=[self.job.pk]))
        self.assertEqual(response.status_code, 404)

    def test_other_employer_cannot_delete_job(self):
        self.client.force_login(self.other_employer)
        response = self.client.post(reverse("job_delete", args=[self.job.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Job.objects.filter(pk=self.job.pk).exists())

    @patch("jobs.forms.geocode", return_value=None)
    def test_unknown_location_is_rejected(self, mock_geocode):
        self.client.force_login(self.employer)
        response = self.client.post(reverse("job_create"), {
            "title": "Backend Developer",
            "company": "CodeWave",
            "location": "Asdfghjkl",
            "work_mode": "onsite",
            "category": "backend",
            "level": "junior",
            "job_type": "full_time",
            "description": "Build APIs with Django.",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("location", response.context["form"].errors)

    def test_remote_job_without_location_is_ok(self):
        self.client.force_login(self.employer)
        response = self.client.post(reverse("job_create"), {
            "title": "Remote Developer",
            "company": "CodeWave",
            "location": "",
            "work_mode": "remote",
            "category": "backend",
            "level": "junior",
            "job_type": "full_time",
            "description": "Build APIs with Django.",
        })
        self.assertEqual(response.status_code, 302)

FAKE_API_RESPONSE = {
    "jobs": [
        {
            "id": 101,
            "title": "Senior Backend Developer",
            "company_name": "CloudNest",
            "description": "<p>Build APIs with <strong>Python</strong> and Django.</p>",
            "candidate_required_location": "Europe",
            "job_type": "full_time",
            "url": "https://remotive.com/jobs/101",
            "publication_date": "2026-11-01T10:00:00",
        },
        {
            "id": 102,
            "title": "Freelance Copywriter",
            "company_name": "WordsCo",
            "description": "Write marketing texts.",
            "candidate_required_location": "Worldwide",
            "job_type": "freelance",
            "url": "https://remotive.com/jobs/102",
            "publication_date": "2026-11-02T10:00:00",
        },
        {
            "id": 103,
            "title": "Junior Frontend Developer",
            "company_name": "PixelCraft",
            "description": "React and TypeScript.",
            "candidate_required_location": "Worldwide",
            "job_type": "internship",
            "url": "http://insecure-site.com/job",
            "publication_date": "2026-11-03T10:00:00",
        },
    ]
}


def fake_response(data):
    response = MagicMock()
    response.json.return_value = data
    response.raise_for_status.return_value = None
    return response


@patch("jobs.management.commands.import_remotive.requests.get")
class ImportRemotiveTests(TestCase):

    def run_import(self):
        out = StringIO()
        call_command("import_remotive", "--limit", "50", stdout=out)
        return out.getvalue()

    def test_it_jobs_are_imported(self, mock_get):
        mock_get.return_value = fake_response(FAKE_API_RESPONSE)
        self.run_import()

        self.assertEqual(Job.objects.filter(source="remotive").count(), 2)

        job = Job.objects.get(external_id="101")
        self.assertEqual(job.company, "CloudNest")
        self.assertEqual(job.work_mode, "remote")
        self.assertEqual(job.category, "backend")
        self.assertEqual(job.level, "senior")

    def test_non_it_jobs_are_skipped(self, mock_get):
        mock_get.return_value = fake_response(FAKE_API_RESPONSE)
        output = self.run_import()

        self.assertFalse(Job.objects.filter(external_id="102").exists())
        self.assertIn("skipped", output)

    def test_second_run_does_not_create_duplicates(self, mock_get):
        mock_get.return_value = fake_response(FAKE_API_RESPONSE)
        self.run_import()
        self.run_import()

        self.assertEqual(Job.objects.filter(source="remotive").count(), 2)

    def test_html_is_stripped_from_description(self, mock_get):
        mock_get.return_value = fake_response(FAKE_API_RESPONSE)
        self.run_import()

        job = Job.objects.get(external_id="101")
        self.assertNotIn("<p>", job.description)
        self.assertIn("Build APIs with Python and Django.", job.description)

    def test_non_https_url_is_not_saved(self, mock_get):
        mock_get.return_value = fake_response(FAKE_API_RESPONSE)
        self.run_import()

        job = Job.objects.get(external_id="103")
        self.assertEqual(job.url, "")
        self.assertEqual(job.job_type, "internship")
        self.assertEqual(job.level, "junior")

    def test_api_error_does_not_crash(self, mock_get):
        mock_get.side_effect = requests.ConnectionError("API is down")
        out = StringIO()
        err = StringIO()

        call_command("import_remotive", stdout=out, stderr=err)

        self.assertEqual(Job.objects.filter(source="remotive").count(), 0)
        self.assertIn("Request failed", err.getvalue())

class AgoFilterTests(TestCase):

    def check(self, delta, expected):
        result = ago(timezone.now() - delta).replace("\xa0", " ")
        self.assertEqual(result, expected)

    def test_just_now(self):
        self.check(timedelta(seconds=10), "just now")

    def test_days(self):
        self.check(timedelta(days=3), "3 days ago")

    def test_weeks(self):
        self.check(timedelta(days=15), "2 weeks ago")

    def test_months(self):
        self.check(timedelta(days=70), "2 months ago")

    def test_years(self):
        self.check(timedelta(days=800), "2 years ago")