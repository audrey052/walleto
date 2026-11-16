"""Line icons from the Walleto Figma design (24x24, 1.5px stroke, currentColor).

    {% load icons %}
    {% icon "wallet" %}
    {% icon "plus" size=16 css_class="text-forest" %}
"""

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

PATHS = {
    "dashboard": (
        '<rect x="3" y="3" width="7" height="7" rx="1.2"/>'
        '<rect x="14" y="3" width="7" height="7" rx="1.2"/>'
        '<rect x="3" y="14" width="7" height="7" rx="1.2"/>'
        '<rect x="14" y="14" width="7" height="7" rx="1.2"/>'
    ),
    "transactions": '<path d="M4 7h15m-4-4 4 4-4 4M20 17H5m4-4-4 4 4 4"/>',
    "wallet": (
        '<path d="M20 8V5a2 2 0 0 0-2-2L5 6a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h15V8H5a2 2 0 0 1 0-4"/>'
        '<path d="M20 12h-5v5h5M16 14.5h.1"/>'
    ),
    "budget": '<path d="M20.5 13A9 9 0 1 1 11 3v10z"/><path d="M15 2.5V9h6.5A9 9 0 0 0 15 2.5Z"/>',
    "goal": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    "assistant": '<path d="M20 11.5a8 8 0 0 1-8 8H5l-3 2v-10a9 9 0 0 1 18 0Z"/><path d="M7 10h8M7 14h5"/>',
    "arrow-right": '<path d="M4 12h16m-6-6 6 6-6 6"/>',
    "arrow-up": '<path d="M7 17 17 7H7m10 0v10"/>',
    "arrow-down": '<path d="m7 7 10 10M7 17h10V7"/>',
    "chevron-left": '<path d="m14 6-6 6 6 6"/>',
    "chevron-right": '<path d="m10 6 6 6-6 6"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "close": '<path d="m6 6 12 12M6 18 18 6"/>',
    "check": '<path d="m5 12 4 4L19 6"/>',
    "bell": '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
    "download": '<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4m10-4v4M3 11h18M7 15h2m4 0h2"/>',
    "food": '<path d="M5 3v6a3 3 0 0 0 6 0V3M8 3v18m12 0V3c-4 2-5 8 0 9"/>',
    "car": '<path d="m5 6-2 7v6h3v-3h12v3h3v-6l-2-7ZM3 12h18M7 6l1-3h8l1 3"/><path d="M6 14h2m8 0h2"/>',
    "bag": '<path d="M5 7h14l2 14H3ZM8 8V6a4 4 0 0 1 8 0v2"/>',
    "home": '<path d="m3 10 9-7 9 7M5 9v12h14V9M9 21v-8h6v8"/>',
    "other": '<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
    "grid": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 9v12"/>',
    "collapse": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16m7-11-3 3 3 3"/>',
    "help": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-1 .5-1 1-1 2.2M12 17h.01"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
    "send": '<path d="m21 3-7 18-4-7-7-4 18-7ZM10 14l5-5"/>',
    "logout": '<path d="M9 3H4v18h5m5-14 5 5-5 5M9 12h11"/>',
    # Added for the default categories (MVP 1), drawn in the same 24px / 1.5px style.
    "heart": '<path d="M12 20s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7.2a4.3 4.3 0 0 1 7.5 2.6C19.5 15.4 12 20 12 20Z"/>',
    "ticket": (
        '<path d="M3 8a2 2 0 0 0 2-2h14a2 2 0 0 0 2 2v2a2 2 0 0 0 0 4v2a2 2 0 0 0-2 2H5a2 2 0 0 0-2-2v-2a2 2 0 0 0 0-4Z"/>'
        '<path d="M14 6v2m0 3v2m0 3v2"/>'
    ),
    "briefcase": (
        '<rect x="3" y="7" width="18" height="13" rx="2"/>'
        '<path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 13h18"/>'
    ),
    "gift": (
        '<rect x="3" y="8" width="18" height="4" rx="1"/>'
        '<path d="M5 12v9h14v-9M12 8v13M12 8S10.5 3.5 8 4.5 8.5 8 12 8Zm0 0s1.5-4.5 4-3.5S15.5 8 12 8Z"/>'
    ),
    "archive": '<rect x="3" y="4" width="18" height="5" rx="1"/><path d="M5 9v11h14V9M10 13h4"/>',
    "edit": '<path d="M4 20h4L19 9l-4-4L4 16v4ZM13.5 6.5l4 4"/>',
    "restore": '<path d="M4 12a8 8 0 1 0 2.3-5.6M4 4v4h4"/>',
}


@register.simple_tag
def icon(name, size=20, css_class=""):
    paths = PATHS.get(name)
    if paths is None:
        raise template.TemplateSyntaxError(f"Unknown icon: {name!r}")
    return format_html(
        '<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
        'stroke-linejoin="round" class="{css_class}" aria-hidden="true">{paths}</svg>',
        size=size,
        css_class=css_class,
        paths=mark_safe(paths),  # static strings defined above, never user input
    )
