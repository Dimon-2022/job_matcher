from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from accounts.mixins import EmployerRequiredMixin
from .forms import JobForm
from .models import Job
from django.db.models import F, Q, Count
from datetime import timedelta
from django.utils import timezone


from django.db.models.functions import TruncWeek
from django.views.generic import TemplateView


class JobListView(ListView):
    model = Job
    template_name = "jobs/job_list.html"
    paginate_by = 10

    def get_queryset(self):
        jobs = Job.objects.prefetch_related("skills")
        params = self.request.GET

        q = params.get("q")
        if q:
            jobs = jobs.filter(Q(title__icontains=q) | Q(description__icontains=q))

        company = params.get("company")
        if company:
            jobs = jobs.filter(company__iexact=company)

        location = params.get("location")
        if location:
            jobs = jobs.filter(Q(location__iexact=location) | Q(work_mode="remote"))

        for field in ("category", "level", "job_type", "work_mode"):
            value = params.get(field)
            if value:
                jobs = jobs.filter(**{field: value})

        skill = params.get("skill")
        if skill:
            jobs = jobs.filter(skills__name=skill)

        sort = params.get("sort")
        if sort == "salary":
            jobs = jobs.order_by(F("salary_max").desc(nulls_last=True))
        elif sort == "oldest":
            jobs = jobs.order_by("created_at")
        else:
            jobs = jobs.order_by("-created_at")

        salary_from = params.get("salary_from")
        if salary_from and salary_from.isdigit():
            jobs = jobs.filter(salary_max__gte=int(salary_from))

        posted = params.get("posted")
        if posted in ("1", "7", "30"):
            since = timezone.now() - timedelta(days=int(posted))
            jobs = jobs.filter(created_at__gte=since)

        return jobs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)

        context["querystring"] = params.urlencode()
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

        return context


class JobDetailView(DetailView):
    model = Job
    template_name = "jobs/job_detail.html"


class JobCreateView(EmployerRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/job_form.html'
    success_url = reverse_lazy('my_jobs')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MyJobsView(EmployerRequiredMixin, ListView):
    template_name = 'jobs/my_jobs.html'

    def get_queryset(self):
        return Job.objects.filter(owner=self.request.user).order_by('-created_at')


class JobUpdateView(EmployerRequiredMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/job_form.html'
    success_url = reverse_lazy('my_jobs')

    def get_queryset(self):
        return Job.objects.filter(owner=self.request.user)


class JobDeleteView(EmployerRequiredMixin, DeleteView):
    model = Job
    template_name = 'jobs/job_confirm_delete.html'
    success_url = reverse_lazy('my_jobs')

    def get_queryset(self):
        return Job.objects.filter(owner=self.request.user)

class StatsView(TemplateView):
    template_name = "jobs/stats.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        jobs = Job.objects.all()
        total = jobs.count()

        category_labels = dict(Job.CATEGORY_CHOICES)
        by_category = (
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

        level_labels = dict(Job.LEVEL_CHOICES)
        by_level = jobs.values("level").annotate(total=Count("id")).order_by("-total")
        for row in by_level:
            row["label"] = level_labels.get(row["level"], row["level"])

        by_week = (
            jobs.annotate(week=TruncWeek("created_at"))
            .values("week")
            .annotate(total=Count("id"))
            .order_by("week")
        )

        context.update({
            "total": total,
            "by_category": by_category,
            "by_level": by_level,
            "by_week": by_week,
        })
        return context
