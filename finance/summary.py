"""The Dashboard's monthly summary (dashboard spec, add-dashboard design decisions 1 and 2).

`month_summary()` computes every Dashboard figure for one user and one month, so
the view only displays it and the Assistant (MVP 7) can reuse it. All of it is
integer math on whole Rupiah, built on the same querysets and `month_budget`
as the Transactions and Budget pages so the numbers match.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date

from django.db.models import Q, Sum
from django.db.models.functions import Coalesce

from . import budgets
from .models import Category, Transaction, month_bounds
from .months import shift

EMPTY_CHART_TOP = 100_000

# The flat daily amount the Remaining line divides by: "Enough for N days of meals".
DAILY_MEAL = 50_000

# Projection kinds (dashboard spec, "Projection line" and "How a past month ended").
MEAL_DAYS = "meal_days"
OVER = "over"
ENDED_LEFT = "ended_left"
ENDED_OVER = "ended_over"


# ---------- value objects ----------

@dataclass(frozen=True)
class Projection:
    kind: str
    days: int | None = None
    amount: int | None = None


@dataclass(frozen=True)
class CategoryLine:
    category: Category
    spent: int
    limit: int | None
    percent: int | None
    bar: int  # bar width in percent: the budget used, or the share of the largest category without a limit


@dataclass(frozen=True)
class DayBar:
    day: date
    amount: int
    height: int  # percent of the chart's top value
    is_today: bool
    is_future: bool


@dataclass(frozen=True)
class DailyChart:
    bars: list
    top: int
    y_labels: list  # five labels, top first
    budget_line: int | None  # bottom offset in percent, or None without a plan


@dataclass(frozen=True)
class MonthSummary:
    year: int
    month: int
    is_current: bool
    income: int
    expense: int
    prev_income: int
    prev_expense: int
    income_change_tenths: int | None
    expense_change_tenths: int | None
    plan: int
    plan_spent: int
    remaining: int
    has_plan: bool
    plan_percent: int
    projection: Projection | None
    daily: list  # [(date, expense)] for every day of the month
    daily_budget: int | None
    chart: DailyChart
    categories: list

    @property
    def over_by(self):
        return max(-self.remaining, 0)


# ---------- pure helpers ----------

def change_tenths(current, previous):
    """Change from `previous` to `current` in tenths of a percent, rounded half
    away from zero, or None when there is nothing to compare with."""
    if previous <= 0:
        return None
    diff = (current - previous) * 1000
    tenths = (abs(diff) * 2 + previous) // (2 * previous)
    return tenths if diff >= 0 else -tenths


def projection(*, year, month, today, plan, expense, has_plan):
    """The line under Remaining, or None when the month has no plan."""
    if not has_plan:
        return None
    remaining = plan - expense
    if (year, month) < (today.year, today.month):
        if remaining >= 0:
            return Projection(ENDED_LEFT, amount=remaining)
        return Projection(ENDED_OVER, amount=-remaining)
    if remaining < 0:
        return Projection(OVER, amount=-remaining)
    return Projection(MEAL_DAYS, days=remaining // DAILY_MEAL)


def nice_top(value):
    """The smallest 1, 2, 2.5 or 5 x 10^n step, times four, that is at least `value`."""
    quarter = max(value, 1)
    quarter = -(-quarter // 4)
    magnitude = 1
    while magnitude * 10 <= quarter:
        magnitude *= 10
    for factor in (1, 2, 2.5, 5, 10):
        step = int(factor * magnitude)
        if step >= quarter:
            return step * 4
    return magnitude * 40


def short_amount(value):
    """Axis label: 0, 750k, 1.5M."""
    if value == 0:
        return "0"
    if value >= 1_000_000:
        millions = value / 1_000_000
        return f"{millions:g}M" if millions == int(millions) else f"{millions:.1f}M"
    return f"{value // 1000}k"


def daily_chart(daily, daily_budget, *, today):
    peak = max([amount for _, amount in daily] + [daily_budget or 0])
    top = nice_top(peak) if peak else EMPTY_CHART_TOP  # an empty month still gets a readable scale
    bars = [
        DayBar(
            day=day,
            amount=amount,
            height=round(amount * 100 / top),
            is_today=day == today,
            is_future=day > today,
        )
        for day, amount in daily
    ]
    labels = [short_amount(top * part // 4) for part in (4, 3, 2, 1, 0)]
    line = round(daily_budget * 100 / top) if daily_budget else None
    return DailyChart(bars=bars, top=top, y_labels=labels, budget_line=line)


def category_lines(month_plan):
    """Expense categories with spending, largest first, with limit and percent."""
    lines = [(row.category, row.spent, row.limit) for row in month_plan.rows if row.spent > 0]
    lines += [(row.category, row.spent, None) for row in month_plan.unbudgeted if row.spent > 0]
    lines.sort(key=lambda line: -line[1])  # stable: ties keep the category order
    largest = lines[0][1] if lines else 0
    result = []
    for category, spent, limit in lines:
        pct = budgets.percent(spent, limit) if limit else None
        bar = min(pct, 100) if pct is not None else spent * 100 // largest
        result.append(CategoryLine(category, spent, limit, pct, bar))
    return result


# ---------- one month, from the database ----------

def _two_month_totals(user, year, month):
    """(income, expense, prev_income, prev_expense) for the month and the month before, in one query."""
    prev_start = month_bounds(*shift(year, month, -1))[0]
    start, end = month_bounds(year, month)
    this, prev = Q(date__gte=start), Q(date__lt=start)
    income, expense = Q(kind=Category.Kind.INCOME), Q(kind=Category.Kind.EXPENSE)
    row = Transaction.objects.for_user(user).filter(date__gte=prev_start, date__lt=end).aggregate(
        income=Coalesce(Sum("amount", filter=this & income), 0),
        expense=Coalesce(Sum("amount", filter=this & expense), 0),
        prev_income=Coalesce(Sum("amount", filter=prev & income), 0),
        prev_expense=Coalesce(Sum("amount", filter=prev & expense), 0),
    )
    return row["income"], row["expense"], row["prev_income"], row["prev_expense"]


def _daily_expenses(user, year, month):
    rows = (
        Transaction.objects.for_user(user).in_month(year, month).expense()
        .order_by().values("date").annotate(total=Sum("amount"))
    )
    by_day = {row["date"]: row["total"] for row in rows}
    days = calendar.monthrange(year, month)[1]
    return [(date(year, month, d), by_day.get(date(year, month, d), 0)) for d in range(1, days + 1)]


def month_summary(user, year, month, today):
    income, expense, prev_income, prev_expense = _two_month_totals(user, year, month)

    plan = budgets.month_budget(user, year, month, today)
    days = calendar.monthrange(year, month)[1]
    daily = _daily_expenses(user, year, month)
    daily_budget = plan.plan // days if plan.has_plan else None

    return MonthSummary(
        year=year,
        month=month,
        is_current=(year, month) == (today.year, today.month),
        income=income,
        expense=expense,
        prev_income=prev_income,
        prev_expense=prev_expense,
        income_change_tenths=change_tenths(income, prev_income),
        expense_change_tenths=change_tenths(expense, prev_expense),
        plan=plan.plan,
        plan_spent=plan.spent,
        remaining=plan.remaining,
        has_plan=plan.has_plan,
        plan_percent=plan.percent,
        projection=projection(
            year=year, month=month, today=today,
            plan=plan.plan, expense=plan.spent, has_plan=plan.has_plan,
        ),
        daily=daily,
        daily_budget=daily_budget,
        chart=daily_chart(daily, daily_budget, today=today),
        categories=category_lines(plan),
    )
