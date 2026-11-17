from django.test import TestCase
from django.urls import reverse


class SignupRedirectTests(TestCase):

    def signup(self, next_url):
        return self.client.post(reverse("signup"), {
            "username": "newuser",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "role": "seeker",
            "next": next_url,
        })

    def test_redirects_to_safe_next(self):
        response = self.signup("/12/")
        self.assertRedirects(response, "/12/", fetch_redirect_response=False)

    def test_ignores_external_next(self):
        response = self.signup("https://evil.example.com/")
        self.assertRedirects(response, reverse("job_list"), fetch_redirect_response=False)