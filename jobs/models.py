from django.db import models
from pgvector.django import VectorField

class Job(models.Model):
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    embedding = VectorField(dimensions=384, null=True, blank=True)

