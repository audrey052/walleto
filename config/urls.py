from django.contrib import admin
from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.urls import include, path
from django.views.decorators.http import require_GET


@login_not_required
@require_GET
def healthz(request):
    """Render's health check (deployment spec): no sign-in, no database."""
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    path("healthz", healthz, name="healthz"),
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include("core.urls")),
    path("", include("finance.urls")),
    path("", include("assistant.urls")),
]
