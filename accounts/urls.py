from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("sign-in/", views.SignInView.as_view(), name="login"),
    path("register/", views.register, name="register"),
    path("demo/", views.demo_sign_in, name="demo"),
    # LogoutView only accepts POST in Django 5, so a plain link cannot sign anyone out.
    path("sign-out/", LogoutView.as_view(), name="logout"),
]
