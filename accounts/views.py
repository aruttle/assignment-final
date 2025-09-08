from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.urls import reverse
from django.contrib.auth.views import LoginView

from .forms import SignUpForm, BootstrapAuthenticationForm

def signup(request):
    next_url = request.GET.get("next") or reverse("my_bookings")
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(next_url)
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form, "next": next_url})

class NiceLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = BootstrapAuthenticationForm
