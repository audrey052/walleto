from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from finance.demo import build_demo, get_demo_user
from finance.models import Wallet

from .forms import EmailAuthenticationForm, RegistrationForm


class SignInView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Welcome back, {self.request.user.get_short_name()}.")
        return response


@login_not_required
def register(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, "Account created. Welcome to Walleto.")
            return redirect("core:dashboard")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


@login_not_required
@require_POST
def demo_sign_in(request):
    """Sign in as the shared demo user (demo-account spec). POST only."""
    user = get_demo_user()
    if not Wallet.objects.for_user(user).exists():
        user = build_demo(timezone.localdate())
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    messages.info(request, "You're using the demo account.")
    return redirect("core:dashboard")
