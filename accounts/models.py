from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    ROLE_CHOICES = [
        ("employer", "Employer"),
        ("seeker", "Job seeker"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    bio = models.TextField(max_length=500, blank=True)
    city = models.CharField(max_length=100, blank=True)
    open_to_remote = models.BooleanField(default=True)
    skills = models.ManyToManyField("jobs.Skill", blank=True, related_name="profiles")

    def __str__(self):
        return f"{self.user.username} ({self.role})"