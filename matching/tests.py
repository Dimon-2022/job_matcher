from django.test import TestCase

from jobs.models import Job, Skill
from .services import calculate_score


class CalculateScoreTests(TestCase):

    def setUp(self):
        self.python = Skill.objects.create(name="Python")
        self.django = Skill.objects.create(name="Django")
        self.docker = Skill.objects.create(name="Docker")

        self.job = Job.objects.create(
            title="Backend Developer",
            company="Test",
            description="We use Python, Django and Docker.",
        )
        self.job.distance = 0.5

    def test_job_skills_are_extracted(self):
        self.assertEqual(set(self.job.skills.all()), {self.python, self.django, self.docker})

    def test_partial_skill_match(self):
        resume_skills = {self.python, self.django}
        score = calculate_score(self.job, resume_skills)
        self.assertEqual(score, 60)
        self.assertEqual(self.job.matched_skills, {self.python, self.django})
        self.assertEqual(self.job.missing_skills, {self.docker})

    def test_no_common_skills(self):
        score = calculate_score(self.job, set())
        self.assertEqual(score, 20)
        self.assertEqual(self.job.missing_skills, {self.python, self.django, self.docker})

    def test_job_without_skills(self):
        job = Job.objects.create(title="Chef", company="Test", description="Cook pasta.")
        job.distance = 0.5
        score = calculate_score(job, {self.python})
        self.assertEqual(score, 20)