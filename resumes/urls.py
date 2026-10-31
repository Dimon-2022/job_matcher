from django.urls import path

from . import views

urlpatterns = [
    path("upload/", views.upload_resume, name="upload_resume"),
    path("my-resumes/", views.MyResumesView.as_view(), name="my_resumes"),
    path("resumes/<int:pk>/delete/", views.ResumeDeleteView.as_view(), name="resume_delete"),
]