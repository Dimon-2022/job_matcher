from django import forms
from django.contrib.auth.forms import UserCreationForm

from accounts.models import Profile


class SignUpForm(UserCreationForm):
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES)