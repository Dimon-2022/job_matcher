from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from .forms import (
    ResumeForm,
    MAX_FILE_SIZE,
    ERROR_NOT_PDF_EXTENSION,
    ERROR_TOO_LARGE,
    ERROR_INVALID_PDF,
)

from accounts.models import Profile
from .models import Resume


class ResumeAccessTests(TestCase):

    def setUp(self):
        self.seeker = User.objects.create_user(username="seeker", password="pass12345")
        Profile.objects.create(user=self.seeker, role="seeker")

        self.other_seeker = User.objects.create_user(username="other", password="pass12345")
        Profile.objects.create(user=self.other_seeker, role="seeker")

        self.employer = User.objects.create_user(username="employer", password="pass12345")
        Profile.objects.create(user=self.employer, role="employer")

        self.resume = Resume.objects.create(
            file="resumes/test.pdf",
            text="Python developer with Django experience.",
            owner=self.seeker,
        )

    def test_guest_cannot_upload(self):
        response = self.client.get(reverse("upload_resume"))
        self.assertEqual(response.status_code, 302)

    def test_employer_cannot_see_my_resumes(self):
        self.client.force_login(self.employer)
        response = self.client.get(reverse("my_resumes"))
        self.assertEqual(response.status_code, 403)

    def test_owner_sees_own_matches(self):
        self.client.force_login(self.seeker)
        response = self.client.get(reverse("match_results", args=[self.resume.pk]))
        self.assertEqual(response.status_code, 200)

    def test_other_seeker_cannot_see_matches(self):
        self.client.force_login(self.other_seeker)
        response = self.client.get(reverse("match_results", args=[self.resume.pk]))
        self.assertEqual(response.status_code, 404)

    def test_other_seeker_cannot_delete_resume(self):
        self.client.force_login(self.other_seeker)
        response = self.client.post(reverse("resume_delete", args=[self.resume.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Resume.objects.filter(pk=self.resume.pk).exists())

class ResumeFormTests(TestCase):

    def make_file(self, name, content):
        return SimpleUploadedFile(name, content, content_type="application/pdf")

    def test_valid_pdf_is_accepted(self):
        form = ResumeForm(files={"file": self.make_file("cv.pdf", b"%PDF-1.4 test content")})
        self.assertTrue(form.is_valid())

    def test_wrong_extension_is_rejected(self):
        form = ResumeForm(files={"file": self.make_file("cv.txt", b"%PDF-1.4 test content")})
        self.assertFalse(form.is_valid())
        self.assertIn(ERROR_NOT_PDF_EXTENSION, form.errors["file"])

    def test_renamed_file_is_rejected(self):
        form = ResumeForm(files={"file": self.make_file("cv.pdf", b"MZ fake executable")})
        self.assertFalse(form.is_valid())
        self.assertIn(ERROR_INVALID_PDF, form.errors["file"])

    def test_too_large_file_is_rejected(self):
        big_content = b"%PDF-" + b"0" * MAX_FILE_SIZE
        form = ResumeForm(files={"file": self.make_file("cv.pdf", big_content)})
        self.assertFalse(form.is_valid())
        self.assertIn(ERROR_TOO_LARGE, form.errors["file"])