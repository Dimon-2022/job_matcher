from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import UpdateView

from jobs.models import Application, Job

from .forms import ProfileForm
from .models import Profile

ACTIVITY_WEEKS = 52


def build_activity(queryset, weeks=ACTIVITY_WEEKS):
    today = timezone.localdate()
    start = today - timedelta(days=today.weekday(), weeks=weeks - 1)

    counts = dict(
        queryset.filter(created_at__date__gte=start)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(n=Count("id"))
        .values_list("day", "n")
    )

    grid = []
    for w in range(weeks):
        week = []
        for d in range(7):
            day = start + timedelta(weeks=w, days=d)
            n = counts.get(day, 0)
            week.append({
                "date": day,
                "count": n,
                "level": min(n, 4),      # 0..4 → відтінок зеленого
                "future": day > today,
            })
        grid.append(week)

    return grid, sum(counts.values())


class ProfileView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = ProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("profile")
    success_message = "Profile saved."

    def get_object(self, queryset=None):
        return get_object_or_404(Profile, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if self.object.role == "employer":
            activity_qs = Job.objects.filter(owner=user)
            context["activity_label"] = "jobs posted"
        else:
            activity_qs = Application.objects.filter(user=user)
            context["activity_label"] = "applications"
            context["recent_applications"] = activity_qs.select_related("job")[:10]

            latest = user.resumes.order_by("-uploaded_at").first()
            context["resume_skills"] = latest.skills.all() if latest else None

        context["activity"], context["activity_total"] = build_activity(activity_qs)
        return context