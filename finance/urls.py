from django.urls import path

from . import views, views_activity

app_name = "finance"

urlpatterns = [
    path("wallets/", views.wallet_list, name="wallets"),
    path("wallets/new/", views.wallet_create, name="wallet_create"),
    path("wallets/<int:pk>/edit/", views.wallet_edit, name="wallet_edit"),
    path("wallets/<int:pk>/archive/", views.wallet_archive, name="wallet_archive"),
    path("wallets/<int:pk>/restore/", views.wallet_restore, name="wallet_restore"),
    path("transactions/", views_activity.transaction_list, name="transactions"),
    path("transactions/new/", views_activity.transaction_create, name="transaction_create"),
    path("transactions/<int:pk>/edit/", views_activity.transaction_edit, name="transaction_edit"),
    path("transactions/<int:pk>/delete/", views_activity.transaction_delete, name="transaction_delete"),
    path("transfers/new/", views_activity.transfer_create, name="transfer_create"),
    path("transfers/<int:pk>/edit/", views_activity.transfer_edit, name="transfer_edit"),
    path("transfers/<int:pk>/delete/", views_activity.transfer_delete, name="transfer_delete"),
]
