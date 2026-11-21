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