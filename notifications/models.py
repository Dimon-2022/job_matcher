from django.conf import settings
from django.db import models


class Notification(models.Model):
    KIND_CHOICES = [
        ("job_closed", "Job closed"),
        ("new_match", "New matching job"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    message = models.CharField(max_length=255)
    url = models.CharField(max_length=255, blank=True)
    job = models.ForeignKey(
        "jobs.Job",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    is_read = models.BooleanField(default=False)
    is_toast_shown = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.message}"