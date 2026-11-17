from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("savings-goals/", views.savings, name="savings"),
    path("assistant/", views.assistant, name="assistant"),
    path("styleguide/", views.styleguide, name="styleguide"),
]
