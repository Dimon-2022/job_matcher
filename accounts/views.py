from django.contrib.auth import login
from django.http import HttpResponse
from django.shortcuts import render, redirect

from accounts.forms import SignUpForm
from .models import Profile

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user, role=form.cleaned_data['role'])
            login(request, user)
            return redirect('job_list')
    else:
        form = SignUpForm()

    return render(request, 'registration/signup.html', {'form': form})
