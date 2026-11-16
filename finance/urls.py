from django.urls import path

from . import views

app_name = "finance"

urlpatterns = [
    path("wallets/", views.wallet_list, name="wallets"),
    path("wallets/new/", views.wallet_create, name="wallet_create"),
    path("wallets/<int:pk>/edit/", views.wallet_edit, name="wallet_edit"),
    path("wallets/<int:pk>/archive/", views.wallet_archive, name="wallet_archive"),
    path("wallets/<int:pk>/restore/", views.wallet_restore, name="wallet_restore"),
]
