from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from accounts.mixins import EmployerRequiredMixin
from .forms import JobForm
from .models import Job

class JobListView(ListView):
    model = Job
    template_name = 'jobs/job_list.html'
    paginate_by = 10
    ordering = ['-created_at'] #from new to old

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