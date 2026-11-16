from django.conf import settings
from django.http import Http404
from django.shortcuts import render

from .sections import SECTIONS_BY_KEY


def _placeholder(request, key):
    """Render a section page whose feature is not built yet."""
    return render(
        request,
        "core/placeholder.html",
        {"section": SECTIONS_BY_KEY[key]},
    )


def dashboard(request):
    return _placeholder(request, "dashboard")


def budget(request):
    return _placeholder(request, "budget")


def savings(request):
    return _placeholder(request, "savings")


def assistant(request):
    return _placeholder(request, "assistant")


STYLEGUIDE_ICONS = [
    "dashboard", "transactions", "wallet", "budget", "goal", "assistant",
    "plus", "check", "close", "search", "bell", "calendar", "download",
    "arrow-right", "arrow-up", "arrow-down", "chevron-left", "chevron-right",
    "chevron-down", "food", "car", "bag", "home", "other", "info", "help",
    "send", "logout", "collapse",
]

STYLEGUIDE_CATEGORIES = [
    {"name": "Food & drinks", "color": "#1F5C4A", "icon": "food"},
    {"name": "Shopping", "color": "#688373", "icon": "bag"},
    {"name": "Transport", "color": "#99AA99", "icon": "car"},
    {"name": "Bills & utilities", "color": "#B8AD92", "icon": "home"},
    {"name": "Others", "color": "#D2CDBF", "icon": "other"},
]


def styleguide(request):
    """Every shared component with sample content. Development only."""
    if not settings.DEBUG:
        raise Http404
    return render(
        request,
        "core/styleguide.html",
        {
            "page_title": "Style guide",
            "icons": STYLEGUIDE_ICONS,
            "categories": STYLEGUIDE_CATEGORIES,
            "sample_amounts": [0, 67500, 847500, 12500000, -150000],
        },
    )
