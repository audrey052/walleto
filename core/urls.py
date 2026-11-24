from django.urls import path

from finance.views_dashboard import dashboard

from . import views

app_name = "core"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("assistant/", views.assistant, name="assistant"),
    path("styleguide/", views.styleguide, name="styleguide"),
]
