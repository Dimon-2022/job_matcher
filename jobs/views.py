from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from accounts.mixins import EmployerRequiredMixin
from .forms import JobForm
from .models import Job
from django.db.models import F, Q

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

        location = params.get("location")
        if location:
            jobs = jobs.filter(location__iexact=location)

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

        return jobs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        context["querystring"] = params.urlencode()
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