"""Rupiah display helpers, following the `money-format` spec.

    {% load money %}
    {{ 847500|rupiah }}                   -> Rp847.500
    {{ 67500|rupiah_signed:"expense" }}   -> −Rp67.500
    {% amount 847500 %}                   -> styled markup (smaller "Rp", tabular digits)
    {% amount 12500000 kind="income" %}   -> "+Rp12.500.000" in the accent color
"""

from decimal import Decimal, ROUND_HALF_UP

from django import template
from django.utils.html import format_html

register = template.Library()

MINUS = "−"  # typographic minus sign, not a hyphen


def _to_int(value):
    """Round to whole Rupiah. Accepts int, Decimal or numeric strings."""
    if value is None or value == "":
        return 0
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _digits(number):
    """847500 -> '847.500' (dot as thousands separator)."""
    return f"{abs(number):,}".replace(",", ".")


def _sign(number, kind):
    if kind == "expense":
        return MINUS if number != 0 else ""
    if kind == "income":
        return "+" if number != 0 else ""
    return MINUS if number < 0 else ""


@register.filter
def rupiah(value):
    number = _to_int(value)
    return f"{_sign(number, None)}Rp{_digits(number)}"


@register.filter
def thousands(value):
    """70000 -> '70.000': an amount for an input box, without the Rp prefix."""
    return _digits(_to_int(value))


@register.filter
def rupiah_signed(value, kind):
    """kind is "income" or "expense"; the amount itself is always positive."""
    number = _to_int(value)
    return f"{_sign(number, kind)}Rp{_digits(number)}"


@register.simple_tag
def amount(value, kind=None, css_class=""):
    number = _to_int(value)
    classes = "amount"
    if kind == "income":
        classes += " amount-income"
    if css_class:
        classes += f" {css_class}"
    return format_html(
        '<span class="{}">{}<span class="currency">Rp</span>{}</span>',
        classes,
        _sign(number, kind),
        _digits(number),
    )
