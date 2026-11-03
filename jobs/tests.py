from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

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

    def test_employer_can_create_job(self):
        self.client.force_login(self.employer)
        response = self.client.post(reverse("job_create"), {
            "title": "Data Analyst",
            "company": "InsightLab",
            "location": "Bratislava",
            "description": "Analyze data with SQL and Excel.",
        })
        self.assertEqual(response.status_code, 302)
        new_job = Job.objects.get(title="Data Analyst")
        self.assertEqual(new_job.owner, self.employer)

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