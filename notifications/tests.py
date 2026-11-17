from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile
from jobs.models import Job, Skill
from resumes.models import Resume
from .models import Notification


class NotificationTriggerTests(TestCase):

    def setUp(self):
        Skill.objects.create(name="Python")
        Skill.objects.create(name="Django")

        self.seeker = User.objects.create_user(username="seeker", password="pass12345")
        Profile.objects.create(user=self.seeker, role="seeker")
        Resume.objects.create(
            file="resumes/test.pdf",
            text="Python developer with Django experience, building web apps.",
            owner=self.seeker,
        )

        self.employer = User.objects.create_user(username="employer", password="pass12345")
        Profile.objects.create(user=self.employer, role="employer")
        self.client.force_login(self.employer)

    def post_job(self, title, description):
        return self.client.post(reverse("job_create"), {
            "title": title,
            "company": "TestCo",
            "location": "",
            "work_mode": "remote",
            "category": "backend",
            "level": "junior",
            "job_type": "full_time",
            "description": description,
        })

    def test_matching_job_notifies_seeker(self):
        self.post_job("Junior Python Developer", "Build web apps with Python and Django.")
        self.assertTrue(Notification.objects.filter(user=self.seeker, kind="new_match").exists())

    def test_unrelated_job_does_not_notify(self):
        self.post_job("Chef", "Cook Italian pasta and pizza in a restaurant kitchen.")
        self.assertFalse(Notification.objects.filter(user=self.seeker).exists())

    def test_closing_job_notifies_matched_seeker(self):
        self.post_job("Junior Python Developer", "Build web apps with Python and Django.")
        job = Job.objects.get(title="Junior Python Developer")

        self.client.post(reverse("job_toggle_open", args=[job.pk]))

        self.assertTrue(Notification.objects.filter(user=self.seeker, kind="job_closed", job=job).exists())

    def test_closing_twice_does_not_duplicate(self):
        self.post_job("Junior Python Developer", "Build web apps with Python and Django.")
        job = Job.objects.get(title="Junior Python Developer")

        for _ in range(3):
            self.client.post(reverse("job_toggle_open", args=[job.pk]))

        self.assertEqual(Notification.objects.filter(kind="job_closed", job=job).count(), 1)