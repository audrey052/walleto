from django.utils import timezone

from .sections import SECTIONS


def app_shell(request):
    """Data every signed-in page needs for the sidebar and topbar."""
    match = getattr(request, "resolver_match", None)
    active_key = match.url_name if match and match.namespace == "core" else None
    active = next((s for s in SECTIONS if s["key"] == active_key), None)
    return {
        "nav_sections": SECTIONS,
        "active_section": active,
        # localdate() uses TIME_ZONE (Asia/Jakarta), not the server clock's zone.
        "today": timezone.localdate(),
    }
