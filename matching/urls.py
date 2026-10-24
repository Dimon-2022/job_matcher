from django.urls import path

from . import views

urlpatterns = [
    path("results/<int:resume_id>/", views.match_results, name="match_results"),
]