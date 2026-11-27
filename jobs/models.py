from urllib.parse import urlparse

from django.conf import settings
from django.core.validators import URLValidator
from django.db import models
from django.utils import timezone
from pgvector.django import VectorField

from matching.services import get_embedding, extract_skills

from .geo import COUNTRY_CHOICES

CURRENCY_CHOICES = [
    ("EUR", "EUR €"), ("USD", "USD $"), ("GBP", "GBP £"), ("CHF", "CHF"),
    ("CZK", "CZK Kč"), ("PLN", "PLN zł"), ("HUF", "HUF Ft"), ("RON", "RON lei"),
    ("SEK", "SEK kr"), ("NOK", "NOK kr"), ("DKK", "DKK kr"),
]
SALARY_PERIOD_CHOICES = [("month", "per month"), ("year", "per year")]

CURRENCY_SYMBOLS = {
    "EUR": "€", "USD": "$", "GBP": "£", "CHF": "CHF", "CZK": "Kč", "PLN": "zł",
    "HUF": "Ft", "RON": "lei", "SEK": "kr", "NOK": "kr", "DKK": "kr",
}
SYMBOL_BEFORE = {"EUR", "USD", "GBP"}


def format_money(amount, currency):
    number = f"{amount:,}".replace(",", " ")
    symbol = CURRENCY_SYMBOLS.get(currency, currency)
    return f"{symbol}{number}" if currency in SYMBOL_BEFORE else f"{number} {symbol}"

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class ExchangeRate(models.Model):
    currency = models.CharField(max_length=3, unique=True)
    per_eur = models.DecimalField(max_digits=12, decimal_places=4)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"1 EUR = {self.per_eur} {self.currency}"

    @classmethod
    def to_eur_monthly(cls, amount, currency, period):
        if amount is None:
            return None
        currency = (currency or "EUR").upper()
        if currency == "EUR":
            value = float(amount)
        else:
            rate = cls.objects.filter(currency=currency).values_list("per_eur", flat=True).first()
            if rate is None:
                return None
            value = float(amount) / float(rate)
        if period == "year":
            value /= 12
        return int(round(value / 100) * 100)

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
        ("arbeitnow", "Arbeitnow"),
        ("jobicy", "Jobicy"),
        ("greenhouse", "Greenhouse"),
        ("personio", "Personio"),
    ]

    # Main info
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="other")
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default="junior")
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default="full_time")
    is_open = models.BooleanField(default=True)

    # Location
    location = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, blank=True, db_index=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    work_mode = models.CharField(max_length=10, choices=WORK_MODE_CHOICES, default="onsite")

    # Salary
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="EUR")
    salary_period = models.CharField(max_length=5, choices=SALARY_PERIOD_CHOICES, default="month")
    salary_eur_min = models.PositiveIntegerField(null=True, blank=True, editable=False)
    salary_eur_max = models.PositiveIntegerField(null=True, blank=True, editable=False, db_index=True)

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
        self.salary_eur_min = ExchangeRate.to_eur_monthly(self.salary_min, self.salary_currency, self.salary_period)
        self.salary_eur_max = ExchangeRate.to_eur_monthly(self.salary_max, self.salary_currency, self.salary_period)
        super().save(*args, **kwargs)
        self.skills.set(extract_skills(text))

    @property
    def salary_text(self):
        parts = [format_money(v, self.salary_currency) for v in (self.salary_min, self.salary_max) if v]
        if not parts:
            return ""
        return f"{' – '.join(parts)} / {self.salary_period}"

    @property
    def salary_eur_text(self):
        if self.salary_currency == "EUR" and self.salary_period == "month":
            return ""
        parts = [format_money(v, "EUR") for v in (self.salary_eur_min, self.salary_eur_max) if v]
        return f"≈ {' – '.join(parts)} / month" if parts else ""

class Application(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "job"], name="unique_application"),
        ]

    def __str__(self):
        return f"{self.user} → {self.job}"

class CompanyFeed(models.Model):
    ATS_CHOICES = [
        ("greenhouse", "Greenhouse"),
        ("personio", "Personio"),
    ]

    name = models.CharField(max_length=100)
    ats = models.CharField(max_length=20, choices=ATS_CHOICES)
    slug = models.CharField(max_length=100, help_text="greenhouse: boards.greenhouse.io/<slug>; personio: <slug>.jobs.personio.de")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["ats", "name"]
        constraints = [
            models.UniqueConstraint(fields=["ats", "slug"], name="unique_company_feed"),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_ats_display()})"