"""Middleware for the app shell (polish-and-deploy design decision 5)."""

from urllib.parse import urlencode, urlsplit

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import resolve_url

from .htmx import is_htmx


class HtmxLoginRedirect:
    """Turn a redirect to sign-in during an HTMX request into a full-page HX-Redirect.

    Without this, HTMX follows the 302 and draws the sign-in page inside a modal, card or list.
    `next` is the page the user was looking at (HX-Current-URL), not the fragment address.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not is_htmx(request) or response.status_code not in (301, 302):
            return response
        login_path = resolve_url(settings.LOGIN_URL)
        if urlsplit(response.get("Location", "")).path != login_path:
            return response
        current = urlsplit(request.headers.get("HX-Current-URL", ""))
        page = current.path + (f"?{current.query}" if current.query else "") if current.path else "/"
        replacement = HttpResponse(status=204)
        replacement["HX-Redirect"] = f"{login_path}?{urlencode({'next': page})}"
        return replacement
