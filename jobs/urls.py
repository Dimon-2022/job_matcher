from django.urls import path

from . import views

urlpatterns = [
    path("", views.JobListView.as_view(), name="job_list"),
    path("mine/", views.MyJobsView.as_view(), name="my_jobs"),
    path("new/", views.JobCreateView.as_view(), name="job_create"),
    path("<int:pk>/", views.JobDetailView.as_view(), name="job_detail"),
    path("<int:pk>/edit/", views.JobUpdateView.as_view(), name="job_update"),
    path("<int:pk>/delete/", views.JobDeleteView.as_view(), name="job_delete"),
]