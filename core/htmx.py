"""Helpers for views that serve both HTMX fragments and full pages."""

from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme


def is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def render_form(request, context, *, status=200):
    """Render a form as a modal fragment for HTMX, or as a full page otherwise.

    `context` needs: title, action, body (template name), submit_label.
    Optional: description, danger, form, delete_url, hide_submit, next, cancel_url.
    """
    template = "components/modal_form.html" if is_htmx(request) else "components/form_page.html"
    return render(request, template, context, status=status)


def redirect_after_save(request, to):
    """Full-page redirect: HX-Redirect for HTMX requests, a normal 302 otherwise."""
    if is_htmx(request):
        response = HttpResponse(status=204)
        response["HX-Redirect"] = to
        return response
    return redirect(to)


def safe_next(request, default):
    """The `next` parameter if it points to this site, otherwise `default`."""
    candidate = request.POST.get("next") or request.GET.get("next")
    if candidate and url_has_allowed_host_and_scheme(
        candidate, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return candidate
    return default
