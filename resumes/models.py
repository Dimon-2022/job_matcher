from django.db import models
from pgvector.django import VectorField

class Resume(models.Model):
    file = models.FileField(upload_to='resumes/')
    text = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    embedding = VectorField(dimensions=384, null=True, blank=True)

    def __str__(self):
        return f"Resume #{self.pk}"
