from django.db import models
from pgvector.django import VectorField
from matching.services import get_embedding, extract_skills
from django.conf import settings
from django.core.validators import URLValidator
from urllib.parse import urlparse

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Job(models.Model):
    CATEGORY_CHOICES = [
        ("backend", "Backend"),
        ("frontend", "Frontend"),
        ("fullstack", "Full-stack"),
        ("mobile", "Mobile (iOS / Android)"),
        ("gamedev", "Game Development"),
        ("embedded", "Embedded / IoT"),

        ("devops", "DevOps / SRE"),
        ("cloud", "Cloud"),
        ("sysadmin", "System Administration"),
        ("network", "Networking"),
        ("security", "Cybersecurity"),

        ("data_analyst", "Data Analysis / BI"),
        ("data_engineer", "Data Engineering"),
        ("data_science", "Data Science"),
        ("ml_ai", "Machine Learning / AI"),
        ("database", "Database Administration"),

        ("qa_manual", "QA Manual"),
        ("qa_automation", "QA Automation"),

        ("ui_ux", "UI / UX Design"),
        ("product", "Product Management"),
        ("project", "Project Management"),
        ("business_analyst", "Business Analysis"),

        ("support", "IT Support / Helpdesk"),
        ("erp", "ERP / CRM (SAP, Salesforce)"),
        ("tech_writer", "Technical Writing"),
        ("other", "Other"),
    ]

    JOB_TYPE_CHOICES = [
        ("full_time", "Full-time"),
        ("part_time", "Part-time"),
        ("internship", "Internship"),
        ("brigada", "Student job"),
    ]

    LEVEL_CHOICES = [
        ("intern", "Intern"),
        ("junior", "Junior"),
        ("middle", "Middle"),
        ("senior", "Senior"),
        ("lead", "Lead"),
    ]

    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    embedding = VectorField(dimensions=384, null=True, blank=True)
    skills = models.ManyToManyField(Skill, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="jobs")
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="other")
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default="full_time")
    url = models.URLField(
        blank=True,
        validators=[URLValidator(schemes=["https"])],
    )
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default="junior")

    @property
    def url_domain(self):
        return urlparse(self.url).netloc

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        text = f"{self.title} {self.description}"
        self.embedding = get_embedding(text)
        super().save(*args, **kwargs)
        self.skills.set(extract_skills(text))