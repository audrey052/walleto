from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    BaseUserCreationForm,
    UserChangeForm,
)

from .models import User


def _style_fields(form):
    """Give every widget the shared `.input` class (the app's one text-field style)."""
    for field in form.fields.values():
        css = field.widget.attrs.get("class", "")
        field.widget.attrs["class"] = f"{css} input".strip()


class RegistrationForm(BaseUserCreationForm):
    """Sign-up form: full name, email and a password typed twice."""

    class Meta:
        model = User
        fields = ["full_name", "email"]
        widgets = {
            "full_name": forms.TextInput(
                attrs={"autocomplete": "name", "placeholder": "Admin"}
            ),
            "email": forms.EmailInput(
                attrs={"autocomplete": "email", "placeholder": "you@example.com"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["full_name"].label = "Full name"
        self.fields["email"].label = "Email"
        self.fields["password1"].label = "Password"
        self.fields["password2"].label = "Confirm password"
        self.fields["password1"].help_text = "At least 8 characters, not only numbers."
        self.fields["password2"].help_text = ""
        _style_fields(self)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class EmailAuthenticationForm(AuthenticationForm):
    """Sign-in form whose single error never reveals whether the email exists."""

    error_messages = {
        "invalid_login": "Email or password is incorrect.",
        "inactive": "Email or password is incorrect.",
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields["username"].label = "Email"
        self.fields["username"].widget.attrs.update(
            {"autocomplete": "email", "placeholder": "you@example.com"}
        )
        self.fields["password"].label = "Password"
        _style_fields(self)


class AdminUserCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ["email", "full_name"]


class AdminUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"
