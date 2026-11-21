from django import forms

from .models import Profile


class RoleSignupForm(forms.Form):
    role = forms.ChoiceField(
        choices=Profile.ROLE_CHOICES,
        widget=forms.RadioSelect,
        label="I am",
    )

    def signup(self, request, user):
        Profile.objects.create(user=user, role=self.cleaned_data["role"])