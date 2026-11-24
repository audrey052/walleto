"""Home page (dashboard spec, add-dashboard design decision 6, add-date-range design decisions 4-7)."""

from urllib.parse import urlencode

from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from . import summary as summary_service
from .months import month_param
from .periods import Period, parse_period
from .views_activity import transactions_url


def dashboard_url(period):
    return f"{reverse('core:dashboard')}?{urlencode(period.query())}"


def change(tenths):
    """10.3% with an up or down arrow, or None for "—"."""
    if tenths is None:
        return None
    whole, tenth = divmod(abs(tenths), 10)
    return {"text": f"{whole}.{tenth}%", "up": tenths >= 0}


AXIS_DAYS = (1, 5, 10, 15, 20, 25)
LONG_RANGE = 31


def axis_labels(bars):
    """x-axis labels. Today, the first and the last day are always candidates;
    up to 31 bars also get days 1, 5, 10, 15, 20 and 25, longer ranges the first
    day of each month. A label right next to one already shown is left out, so
    two never run together ("2425")."""
    count = len(bars)
    if not count:
        return []
    today = next((i for i, bar in enumerate(bars) if bar.is_today), None)
    crosses_months = (bars[0].day.year, bars[0].day.month) != (bars[-1].day.year, bars[-1].day.month)

    shown = {today} if today is not None else set()
    for i in (0, count - 1):
        if today is None or abs(i - today) > 1:
            shown.add(i)
    if count > LONG_RANGE:
        candidates = [i for i, bar in enumerate(bars) if bar.day.day == 1]
    else:
        candidates = [i for i, bar in enumerate(bars) if bar.day.day in AXIS_DAYS]
    for i in candidates:
        if all(abs(i - j) > 1 for j in shown):
            shown.add(i)

    labels = []
    for i, bar in enumerate(bars):
        text = ""
        if i in shown:
            day = bar.day
            with_month = crosses_months and (i == 0 or day.day == 1)
            text = f"{day.day} {day.strftime('%b')}" if with_month else f"{day.day:02d}"
        labels.append({"text": text, "is_today": bar.is_today})
    return labels


def chart_footer(result, today):
    """ "01–24 Nov 2026" for a month (up to today in the current one), else the period's label."""
    period = result.period
    if not period.is_month:
        return period.label
    last = today.day if result.is_current else period.end.day
    return f"01–{last:02d} {period.start.strftime('%b %Y')}"


def dashboard(request):
    today = timezone.localdate()
    period = parse_period(request.GET, today)
    result = summary_service.period_summary(request.user, period, today)

    plan_month = Period.for_month(period.end.year, period.end.month)
    next_month = period.next_month(today)
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
            "period": period,
            "daily_meal": summary_service.DAILY_MEAL,
            "metrics": metrics,
            "axis_labels": axis_labels(result.chart.bars),
            "chart_footer": chart_footer(result, today),
            "month_start": period.start,
            "prev_url": dashboard_url(period.prev_month()),
            "next_url": dashboard_url(next_month) if next_month else None,
            "period_target": "#dashboard",
            "period_action": reverse("core:dashboard"),
            "period_fields": {},
            "plan_month": plan_month,
            "plan_month_url": dashboard_url(plan_month),
            "budget_url": f"{reverse('finance:budget')}?month={month_param(plan_month.start.year, plan_month.start.month)}",
            "transactions_url": transactions_url(period),
        },
    )
