"""Dashboard page (dashboard spec, add-dashboard design decision 6)."""

from datetime import date

from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from . import summary as summary_service
from .months import month_param, parse_month, shift


def dashboard_url(year, month):
    return f"{reverse('core:dashboard')}?month={month_param(year, month)}"


def change(tenths):
    """10.3% with an up or down arrow, or None for "—"."""
    if tenths is None:
        return None
    whole, tenth = divmod(abs(tenths), 10)
    return {"text": f"{whole}.{tenth}%", "up": tenths >= 0}


AXIS_DAYS = (1, 5, 10, 15, 20, 25)


def axis_labels(bars):
    """x-axis labels: days 1, 5, 10, 15, 20, 25, the last day and today, but a
    fixed day right next to today is left out so the two never run together."""
    today = next((bar.day.day for bar in bars if bar.is_today), None)
    last = len(bars)
    labels = []
    for bar in bars:
        day = bar.day.day
        shown = bar.is_today or (
            (day in AXIS_DAYS or day == last) and (today is None or abs(day - today) > 1)
        )
        labels.append({"text": f"{day:02d}" if shown else "", "is_today": bar.is_today})
    return labels


def dashboard(request):
    today = timezone.localdate()
    year, month = parse_month(request.GET.get("month"), today)
    result = summary_service.month_summary(request.user, year, month, today)

    prev_year, prev_month = shift(year, month, -1)
    next_year, next_month = shift(year, month, 1)
    month_query = month_param(year, month)
    metrics = [
        {
            "kind": "income", "label": "Total income", "value": result.income,
            "change": change(result.income_change_tenths),
            "good": (result.income_change_tenths or 0) >= 0,
        },
        {
            "kind": "expense", "label": "Total expenses", "value": result.expense,
            "change": change(result.expense_change_tenths),
            "good": (result.expense_change_tenths or 0) <= 0,
        },
    ]

    return render(
        request,
        "finance/dashboard.html",
        {
            "s": result,
            "daily_meal": summary_service.DAILY_MEAL,
            "metrics": metrics,
            "axis_labels": axis_labels(result.chart.bars),
            "chart_last_day": today.day if result.is_current else len(result.daily),
            "month_start": date(year, month, 1),
            "prev_url": dashboard_url(prev_year, prev_month),
            "next_url": None if result.is_current else dashboard_url(next_year, next_month),
            "budget_url": f"{reverse('finance:budget')}?month={month_query}",
            "transactions_url": f"{reverse('finance:transactions')}?month={month_query}",
        },
    )
