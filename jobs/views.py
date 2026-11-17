from datetime import timedelta
from urllib.parse import urlencode

from django.db.models import Count, F, Q
from django.db.models.functions import TruncWeek
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)
from pgvector.django import CosineDistance

from accounts.mixins import EmployerRequiredMixin
from matching.services import calculate_score
from .forms import JobForm
from .models import Job


# ---------- Job lists ----------

class JobListView(ListView):
    model = Job
    template_name = "jobs/job_list.html"
    paginate_by = 10
    page_title = "All jobs"
    page_subtitle = ""
    show_closed = False
    show_tabs = True

    def get_queryset(self):
        params = self.request.GET
        jobs = Job.objects.prefetch_related("skills").filter(is_open=not self.show_closed)

        q = params.get("q")
        if q:
            jobs = jobs.filter(Q(title__icontains=q) | Q(description__icontains=q))

        company = params.get("company")
        if company:
            jobs = jobs.filter(company__iexact=company)

        location = params.get("location")
        if location:
            city_filter = Q(location__iexact=location)
            if params.get("include_remote"):
                city_filter |= Q(work_mode="remote")
            jobs = jobs.filter(city_filter)

        for field in ("category", "level", "job_type", "work_mode"):
            value = params.get(field)
            if value:
                jobs = jobs.filter(**{field: value})

        skill = params.get("skill")
        if skill:
            jobs = jobs.filter(skills__name=skill)

        salary_from = params.get("salary_from")
        if salary_from and salary_from.isdigit():
            jobs = jobs.filter(salary_max__gte=int(salary_from))

        posted = params.get("posted")
        if posted in ("1", "7", "30"):
            since = timezone.now() - timedelta(days=int(posted))
            jobs = jobs.filter(created_at__gte=since)

        sort = params.get("sort")
        if sort == "salary":
            ordering = [F("salary_max").desc(nulls_last=True)]
        elif sort == "oldest":
            ordering = ["created_at"]
        else:
            ordering = ["-created_at"]

        return jobs.order_by("-is_open", *ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        params = self.request.GET.copy()
        params.pop("page", None)
        active = {key: value for key, value in params.items() if value}

        context["has_filters"] = bool(active)
        context["querystring"] = urlencode(active)
        context["categories"] = Job.CATEGORY_CHOICES
        context["levels"] = Job.LEVEL_CHOICES
        context["work_modes"] = Job.WORK_MODE_CHOICES
        context["posted_options"] = [
            ("", "Any time"),
            ("1", "Last 24 hours"),
            ("7", "Last 7 days"),
            ("30", "Last 30 days"),
        ]
        context["sort_options"] = [
            ("", "Newest first"),
            ("oldest", "Oldest first"),
            ("salary", "Highest salary"),
        ]

        page_obj = context["page_obj"]
        context["page_range"] = page_obj.paginator.get_elided_page_range(
            page_obj.number, on_each_side=2, on_ends=1
        )

        context["page_title"] = self.page_title
        context["page_subtitle"] = self.page_subtitle
        context["show_closed"] = self.show_closed
        context["show_tabs"] = self.show_tabs
        closed_ids = set(Job.objects.filter(is_open=False).values_list("pk", flat=True))
        seen_ids = set(self.request.session.get("seen_closed_ids", []))

        context["closed_count"] = len(closed_ids)
        context["new_closed_count"] = len(closed_ids - seen_ids)
        context["closed_ids"] = closed_ids

        return context

    def get_template_names(self):
        if self.request.headers.get("HX-Request"):
            return ["jobs/_job_results.html"]
        return [self.template_name]


class StudentJobsView(JobListView):
    page_title = "Jobs for students"
    page_subtitle = "Internships, part-time and junior positions that fit your study schedule."
    show_tabs = False

    def get_queryset(self):
        return super().get_queryset().filter(
            Q(job_type__in=["internship", "part_time", "brigada"])
            | Q(level__in=["intern", "junior"])
        )


class FreelanceJobsView(JobListView):
    page_title = "Freelance jobs"
    page_subtitle = "Project-based and contract work you can do on your own schedule."
    show_tabs = False

    def get_queryset(self):
        return super().get_queryset().filter(job_type="freelance")


class ClosedJobsView(JobListView):
    page_title = "Recently closed jobs"
    page_subtitle = "See what employers were looking for and check whether you would have matched."
    show_closed = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.request.user.is_authenticated:
            self.request.session["seen_closed_ids"] = list(context["closed_ids"])
            context["new_closed_count"] = 0
        return context


# ---------- Single job ----------

class JobDetailView(DetailView):
    model = Job
    template_name = "jobs/job_detail.html"


class JobInsightView(View):
    def get(self, request, pk):
        job = get_object_or_404(Job, pk=pk)

        similar_jobs = (
            Job.objects.filter(is_open=True)
            .exclude(pk=job.pk)
            .annotate(distance=CosineDistance("embedding", job.embedding))
            .order_by("distance")[:3]
        )

        match = None
        user = request.user
        if user.is_authenticated and hasattr(user, "profile") and user.profile.role == "seeker":
            resume = user.resumes.order_by("-uploaded_at").first()
            if resume and resume.embedding is not None:
                scored_job = (
                    Job.objects.annotate(distance=CosineDistance("embedding", resume.embedding))
                    .prefetch_related("skills")
                    .get(pk=job.pk)
                )
                score = calculate_score(scored_job, set(resume.skills.all()))
                match = {
                    "score": score,
                    "matched": scored_job.matched_skills,
                    "missing": scored_job.missing_skills,
                }

        return render(request, "jobs/_job_insight.html", {
            "job": job,
            "similar_jobs": similar_jobs,
            "match": match,
        })


# ---------- Employer CRUD ----------

class JobCreateView(EmployerRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = "jobs/job_form.html"
    success_url = reverse_lazy("my_jobs")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MyJobsView(EmployerRequiredMixin, ListView):
    template_name = "jobs/my_jobs.html"

    def get_queryset(self):
        return Job.objects.filter(owner=self.request.user).order_by("-created_at")


class JobUpdateView(EmployerRequiredMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = "jobs/job_form.html"
    success_url = reverse_lazy("my_jobs")

    def get_queryset(self):
        return Job.objects.filter(owner=self.request.user)


class JobDeleteView(EmployerRequiredMixin, DeleteView):
    model = Job
    template_name = "jobs/job_confirm_delete.html"
    success_url = reverse_lazy("my_jobs")

    def get_queryset(self):
        return Job.objects.filter(owner=self.request.user)


class JobToggleOpenView(EmployerRequiredMixin, View):
    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk, owner=request.user)
        Job.objects.filter(pk=job.pk).update(is_open=not job.is_open)
        return redirect("my_jobs")


# ---------- Stats ----------

class StatsView(TemplateView):
    template_name = "jobs/stats.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        jobs = Job.objects.all()
        total = jobs.count()

        # Jobs by category + junior share
        category_labels = dict(Job.CATEGORY_CHOICES)
        by_category = list(
            jobs.values("category")
            .annotate(
                total=Count("id"),
                junior=Count("id", filter=Q(level__in=["intern", "junior"])),
            )
            .order_by("-total")
        )
        for row in by_category:
            row["label"] = category_labels.get(row["category"], row["category"])
            row["junior_share"] = round(row["junior"] / row["total"] * 100) if row["total"] else 0

        # Jobs by level
        level_labels = dict(Job.LEVEL_CHOICES)
        by_level = list(jobs.values("level").annotate(total=Count("id")).order_by("-total"))
        for row in by_level:
            row["label"] = level_labels.get(row["level"], row["level"])

        # Jobs per week, with empty weeks filled as zero
        by_week = list(
            jobs.annotate(week=TruncWeek("created_at"))
            .values("week")
            .annotate(total=Count("id"))
            .order_by("week")
        )
        if by_week:
            totals_by_week = {row["week"]: row["total"] for row in by_week}
            week = by_week[0]["week"]
            last_week = by_week[-1]["week"]
            by_week = []
            while week <= last_week:
                by_week.append({"week": week, "total": totals_by_week.get(week, 0)})
                week += timedelta(weeks=1)

        # Level structure inside each category
        category_order = [row["category"] for row in by_category]
        counts = {}
        for row in jobs.values("category", "level").annotate(total=Count("id")):
            counts.setdefault(row["category"], {})[row["level"]] = row["total"]

        level_series = [
            {
                "label": label,
                "counts": [counts.get(category, {}).get(level, 0) for category in category_order],
            }
            for level, label in Job.LEVEL_CHOICES
        ]

        chart_data = {
            "categories": {
                "labels": [row["label"] for row in by_category],
                "totals": [row["total"] for row in by_category],
                "levels": level_series,
            },
            "weeks": {
                "labels": [row["week"].strftime("%d %b") for row in by_week],
                "totals": [row["total"] for row in by_week],
            },
        }

        context.update({
            "total": total,
            "by_category": by_category,
            "by_level": by_level,
            "by_week": by_week,
            "chart_data": chart_data,
        })
        return context