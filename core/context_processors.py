from django.utils import timezone

from .sections import SECTIONS


def _active_section(request):
    match = getattr(request, "resolver_match", None)
    view_name = match.view_name if match else ""
    for section in SECTIONS:
        prefix = section.get("match", section["url_name"])
        if view_name == section["url_name"] or view_name.startswith(prefix):
            return section
    return None


def app_shell(request):
    """Data every signed-in page needs for the sidebar and topbar."""
    return {
        "nav_sections": SECTIONS,
        "active_section": _active_section(request),
        # localdate() uses TIME_ZONE (Asia/Jakarta), not the server clock's zone.
        "today": timezone.localdate(),
    }
