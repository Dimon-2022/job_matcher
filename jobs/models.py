from urllib.parse import urlparse

from django.conf import settings
from django.core.validators import URLValidator
from django.db import models
from django.utils import timezone
from pgvector.django import VectorField

from matching.services import get_embedding, extract_skills


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Job(models.Model):
    CATEGORY_CHOICES = [
        # Development
        ("backend", "Backend"),
        ("frontend", "Frontend"),
        ("fullstack", "Full-stack"),
        ("mobile", "Mobile (iOS / Android)"),
        ("gamedev", "Game Development"),
        ("embedded", "Embedded / IoT"),
        # Infrastructure
        ("devops", "DevOps / SRE"),
        ("cloud", "Cloud"),
        ("sysadmin", "System Administration"),
        ("network", "Networking"),
        ("security", "Cybersecurity"),
        # Data & AI
        ("data_analyst", "Data Analysis / BI"),
        ("data_engineer", "Data Engineering"),
        ("data_science", "Data Science"),
        ("ml_ai", "Machine Learning / AI"),
        ("database", "Database Administration"),
        # Quality
        ("qa_manual", "QA Manual"),
        ("qa_automation", "QA Automation"),
        # Design & product
        ("ui_ux", "UI / UX Design"),
        ("product", "Product Management"),
        ("project", "Project Management"),
        ("business_analyst", "Business Analysis"),
        # Other
        ("support", "IT Support / Helpdesk"),
        ("erp", "ERP / CRM (SAP, Salesforce)"),
        ("tech_writer", "Technical Writing"),
        ("other", "Other"),
    ]

    JOB_TYPE_CHOICES = [
        ("full_time", "Full-time"),
        ("part_time", "Part-time"),
        ("freelance", "Freelance / Contract"),
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

    WORK_MODE_CHOICES = [
        ("onsite", "On-site"),
        ("remote", "Remote"),
        ("hybrid", "Hybrid"),
    ]

    SOURCE_CHOICES = [
        ("manual", "Posted on Job Matcher"),
        ("remotive", "Remotive"),
        ("jooble", "Jooble"),
    ]

    # Main info
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="other")
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default="junior")
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default="full_time")

    # Location
    location = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    work_mode = models.CharField(max_length=10, choices=WORK_MODE_CHOICES, default="onsite")

    # Salary
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)

    # Source
    url = models.URLField(blank=True, validators=[URLValidator(schemes=["https"])])
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="manual")
    external_id = models.CharField(max_length=100, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="jobs",
    )

    # Technical
    created_at = models.DateTimeField(default=timezone.now)
    embedding = VectorField(dimensions=384, null=True, blank=True)
    skills = models.ManyToManyField(Skill, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "external_id"],
                condition=~models.Q(external_id=""),
                name="unique_external_job",
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def url_domain(self):
        return urlparse(self.url).netloc.removeprefix("www.")

    def save(self, *args, **kwargs):
        text = f"{self.title} {self.description}"
        self.embedding = get_embedding(text)
        super().save(*args, **kwargs)
        self.skills.set(extract_skills(text))