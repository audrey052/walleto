"""Small server-rendered charts.

    {% load charts %}
    {% sparkline wallet.history label="BCA, last 30 days" %}

The geometry follows `Sparkline` in the Figma Make source (WalletsPage.tsx):
a 120x32 box, the line between y=5 and y=27, a faint baseline at y=29 and a
dot on the last point. A flat series is drawn at mid-height.
"""

from django import template
from django.utils.html import format_html

register = template.Library()

WIDTH, HEIGHT = 120, 32


def sparkline_points(values):
    values = list(values)
    if not values:
        return []
    low, high = min(values), max(values)
    spread = (high - low) or 1
    count = len(values)
    points = []
    for index, value in enumerate(values):
        x = 3 + (index / (count - 1)) * 114 if count > 1 else 117
        y = 16 if high == low else 27 - ((value - low) / spread) * 22
        points.append((round(x, 2), round(y, 2)))
    return points


@register.simple_tag
def sparkline(values, label=""):
    points = sparkline_points(values)
    if not points:
        return ""
    path = " ".join(f"{'M' if i == 0 else 'L'}{x},{y}" for i, (x, y) in enumerate(points))
    last_x, last_y = points[-1]
    return format_html(
        '<svg class="sparkline" width="{}" height="{}" viewBox="0 0 {} {}" fill="none" role="img" aria-label="{}">'
        '<path d="M3 29H117" stroke="currentColor" opacity="0.12"/>'
        '<path d="{}" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
        '<circle cx="{}" cy="{}" r="2" fill="currentColor"/>'
        "</svg>",
        WIDTH, HEIGHT, WIDTH, HEIGHT, label, path, last_x, last_y,
    )
