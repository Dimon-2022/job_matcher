from django.contrib.auth import login
from django.shortcuts import render, redirect

from django.utils.http import url_has_allowed_host_and_scheme

from accounts.forms import SignUpForm
from .models import Profile

def signup(request):
    next_url = request.POST.get("next") or request.GET.get("next")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user, role=form.cleaned_data["role"])
            login(request, user)

            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect("job_list")
    else:
        form = SignUpForm()

    return render(request, "registration/signup.html", {"form": form, "next": next_url})
