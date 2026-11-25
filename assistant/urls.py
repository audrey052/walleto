from django.urls import path

from . import views

app_name = "assistant"

urlpatterns = [
    path("assistant/ask/", views.ask, name="ask"),
    path("assistant/new/", views.new_chat, name="new"),
    path("assistant/drafts/<int:message_id>/save/", views.save_draft, name="save_draft"),
    path("assistant/drafts/<int:message_id>/cancel/", views.cancel_draft, name="cancel_draft"),
    path("assistant/plans/<int:message_id>/apply/", views.apply_plan, name="apply_plan"),
    path("assistant/reports/<int:message_id>.pdf", views.report_pdf, name="report_pdf"),
]
