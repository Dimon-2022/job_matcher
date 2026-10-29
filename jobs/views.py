from django.shortcuts import render
from django.views.generic import ListView, DetailView

from jobs.models import Job


class JobListView(ListView):
    model = Job
    template_name = 'jobs/job_list.html'
    paginate_by = 10
    ordering = ['-created_at'] #from new to old

class JobDetailView(DetailView):
    model = Job
    template_name = "jobs/job_detail.html"