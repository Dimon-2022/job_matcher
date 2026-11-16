from django.urls import path

from . import views

urlpatterns = [
    path("notifications/", views.notification_list, name="notification_list"),
    path("notifications/toasts/", views.toasts, name="notification_toasts"),
    path("notifications/<int:pk>/open/", views.notification_open, name="notification_open"),
]