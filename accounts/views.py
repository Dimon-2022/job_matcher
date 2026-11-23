from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from .forms import ProfileForm
from .models import Profile


class ProfileView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = ProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("profile")
    success_message = "Profile saved."

    def get_object(self, queryset=None):
        return get_object_or_404(Profile, user=self.request.user)

    def get_initial(self):
        initial = super().get_initial()
        self.skills_from_resume = False

        if not self.object.skills.exists():
            latest = self.request.user.resumes.order_by("-uploaded_at").first()
            if latest and latest.skills.exists():
                initial["skills"] = latest.skills.all()
                self.skills_from_resume = True

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["skills_from_resume"] = self.skills_from_resume
        return context