from django.db import models
from pgvector.django import VectorField
from matching.services import get_embedding, extract_skills
from django.conf import settings

from matching.services import get_embedding

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Job(models.Model):
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    embedding = VectorField(dimensions=384, null=True, blank=True)
    skills = models.ManyToManyField(Skill, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="jobs")

    def save(self, *args, **kwargs):
        text = f"{self.title} {self.description}"
        self.embedding = get_embedding(text)
        super().save(*args, **kwargs)
        self.skills.set(extract_skills(text))