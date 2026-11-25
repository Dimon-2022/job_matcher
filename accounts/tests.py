from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.core.cache import cache

from .models import Profile

PASSWORD = "S3cure-pass-123"


def make_verified_user(email, role="seeker"):
    user = User.objects.create_user(username=email.split("@")[0], email=email, password=PASSWORD)
    EmailAddress.objects.create(user=user, email=email, verified=True, primary=True)
    Profile.objects.create(user=user, role=role)
    return user


class SignupTests(TestCase):
    def setUp(self):
        cache.clear()

    def signup(self, **extra):
        data = {"email": "new@example.com", "password1": PASSWORD, "password2": PASSWORD, "role": "seeker"}
        data.update(extra)
        return self.client.post(reverse("account_signup"), data)

    def test_signup_creates_profile_with_role(self):
        self.signup(role="employer")
        user = User.objects.get(email="new@example.com")
        self.assertEqual(user.profile.role, "employer")

    def test_signup_sends_verification_email(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.signup()
        self.assertEqual(len(mail.outbox), 1)
        self.assertFalse(EmailAddress.objects.get(email="new@example.com").verified)

    def test_unverified_user_is_not_logged_in(self):
        self.signup()
        self.client.post(reverse("account_login"), {"login": "new@example.com", "password": PASSWORD})
        self.assertNotIn("_auth_user_id", self.client.session)


class LoginRedirectTests(TestCase):
    def setUp(self):
        make_verified_user("seeker@example.com")

    def login(self, next_url):
        return self.client.post(
            reverse("account_login"),
            {"login": "seeker@example.com", "password": PASSWORD, "next": next_url},
        )

    def test_safe_next_is_followed(self):
        response = self.login("/stats/")
        self.assertRedirects(response, "/stats/", fetch_redirect_response=False)

    def test_external_next_is_ignored(self):
        response = self.login("https://evil.com/")
        self.assertRedirects(response, reverse("job_list"), fetch_redirect_response=False)

from jobs.models import Skill, Application, Job


class ProfileTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_verified_user("seeker@example.com")

    def test_guest_redirected_to_login(self):
        response = self.client.get(reverse("profile"))
        self.assertIn(reverse("account_login"), response.url)

    def test_user_updates_own_profile(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("profile"), {
            "bio": "Student",
            "city": "Košice",
            "open_to_remote": "on",
        })

        self.assertRedirects(response, reverse("profile"))
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.city, "Košice")

    def test_profile_shows_application_count(self):
        employer = make_verified_user("boss@example.com", role="employer")
        job = Job.objects.create(title="Junior Python", company="X", description="Python", owner=employer)
        Application.objects.create(user=self.user, job=job)
        self.client.force_login(self.user)

        response = self.client.get(reverse("profile"))

        self.assertEqual(response.context["activity_total"], 1)
        self.assertContains(response, "Junior Python")