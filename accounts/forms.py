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

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["bio", "city", "open_to_remote"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3, "placeholder": "Student at TUKE, looking for a Python internship..."}),
        }
        labels = {
            "bio": "About me",
            "city": "City",
            "open_to_remote": "Open to remote work",
        }