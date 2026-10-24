from django.db import models
from pgvector.django import VectorField

from jobs.models import Skill
from matching.services import get_embedding, extract_skills


class Resume(models.Model):
    file = models.FileField(upload_to='resumes/')
    text = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    embedding = VectorField(dimensions=384, null=True, blank=True)
    skills = models.ManyToManyField(Skill, blank=True)

    def save(self, *args, **kwargs):
        if self.text:
            self.embedding = get_embedding(self.text)
        super().save(*args, **kwargs)
        if self.text:
            self.skills.set(extract_skills(self.text))

    def __str__(self):
        return f"Resume #{self.pk}"
