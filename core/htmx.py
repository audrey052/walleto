"""Helpers for views that serve both HTMX fragments and full pages."""

from django.http import HttpResponse
from django.shortcuts import redirect, render


def is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def render_form(request, context, *, status=200):
    """Render a form as a modal fragment for HTMX, or as a full page otherwise.

    `context` needs: title, action, body (template name), submit_label.
    Optional: description, danger, form.
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
