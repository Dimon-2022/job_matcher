from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class EmployerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return hasattr(user, "profile") and user.profile.role == "employer"

class SeekerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return hasattr(user, "profile") and user.profile.role == "seeker"