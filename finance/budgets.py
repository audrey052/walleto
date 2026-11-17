"""Budget calculations (budgets spec, add-budgets design decision 4).

Everything here is integer math on whole Rupiah. The views and templates only
display what these functions return.
"""

import calendar
from dataclasses import dataclass, field
from datetime import date

from django.db.models import Sum

from .models import Budget, Category, Transaction

WARNING_PERCENT = 85

NORMAL, WARNING, OVER = "normal", "warning", "over"


# ---------- pure helpers ----------

def distribute(total, weights):
    """Split `total` by `weights` ({key: weight}, in display order) with the
    largest remainder method, so the parts add up to exactly `total`.

    Ties go to the key that comes first. Keys with weight 0 get 0.
    """
    weight_sum = sum(weights.values())
    if weight_sum <= 0:
        raise ValueError("At least one weight must be above zero.")
    parts, remainders = {}, []
    for index, (key, weight) in enumerate(weights.items()):
        share, remainder = divmod(total * weight, weight_sum)
        parts[key] = share
        remainders.append((-remainder, index, key))
    leftover = total - sum(parts.values())
    for _, _, key in sorted(remainders)[:leftover]:
        parts[key] += 1
    return parts


def status(spent, limit):
    """normal below 85%, warning from 85% to 100% inclusive, over above 100%."""
    if spent > limit:
        return OVER
    if spent * 100 >= WARNING_PERCENT * limit:
        return WARNING
    return NORMAL


def percent(spent, limit):
    """Percent spent, rounded down (so 84.99% never reads as 85%)."""
    if limit <= 0:
        return 0
    return max(spent, 0) * 100 // limit


def crossing(before, after, limit):
    """Which line a save crossed: "over", "warning", or None (transactions spec)."""
    old, new = status(before, limit), status(after, limit)
    if new == OVER and old != OVER:
        return OVER
    if new == WARNING and old == NORMAL:
        return WARNING
    return None


def days_left(year, month, today):
    """Today plus the remaining days of the month; 0 for past months, all days for future ones."""
    last_day = calendar.monthrange(year, month)[1]
    if (year, month) < (today.year, today.month):
        return 0
    if (year, month) > (today.year, today.month):
        return last_day
    return last_day - today.day + 1


def per_day(remaining, days):
    """What can be spent per day for the rest of the month, or None."""
    if remaining > 0 and days > 0:
        return remaining // days
    return None


# ---------- one month, from the database ----------

@dataclass
class BudgetRow:
    category: Category
    limit: int
    spent: int

    @property
    def remaining(self):
        return self.limit - self.spent

    @property
    def over_by(self):
        return max(self.spent - self.limit, 0)

    @property
    def percent(self):
        return percent(self.spent, self.limit)

    @property
    def status(self):
        return status(self.spent, self.limit)


@dataclass
class UnbudgetedRow:
    category: Category
    spent: int


@dataclass
class MonthBudget:
    year: int
    month: int
    plan: int
    spent: int
    days_left: int
    rows: list = field(default_factory=list)
    unbudgeted: list = field(default_factory=list)

    @property
    def has_plan(self):
        return bool(self.rows)

    @property
    def remaining(self):
        return self.plan - self.spent

    @property
    def over_by(self):
        return max(self.spent - self.plan, 0)

    @property
    def percent(self):
        return percent(self.spent, self.plan)

    @property
    def status(self):
        return status(self.spent, self.plan)

    @property
    def per_day(self):
        return per_day(self.remaining, self.days_left)


def expense_categories(user):
    return Category.objects.for_user(user).expense()


def spent_by_category(user, year, month):
    """{category_id: spent} for the user's expenses in the month (one grouped query)."""
    rows = (
        Transaction.objects.for_user(user).in_month(year, month).expense()
        .order_by().values("category").annotate(total=Sum("amount"))
    )
    return {row["category"]: row["total"] for row in rows}


def category_spent(user, category, year, month):
    return (
        Transaction.objects.for_user(user).in_month(year, month).expense()
        .filter(category=category).aggregate(total=Sum("amount"))["total"] or 0
    )


def limits_for(user, year, month):
    """{category_id: limit} for the month."""
    return dict(
        Budget.objects.for_user(user).in_month(year, month).values_list("category", "limit")
    )


def month_budget(user, year, month, today):
    categories = list(expense_categories(user))
    limits = limits_for(user, year, month)
    spent = spent_by_category(user, year, month)

    rows, unbudgeted = [], []
    for category in categories:
        if category.pk in limits:
            rows.append(BudgetRow(category, limits[category.pk], spent.get(category.pk, 0)))
        else:
            unbudgeted.append(UnbudgetedRow(category, spent.get(category.pk, 0)))
    # Highest spending first; ties keep the category order.
    rows.sort(key=lambda row: -row.spent)
    unbudgeted.sort(key=lambda row: -row.spent)

    return MonthBudget(
        year=year,
        month=month,
        plan=sum(limits.values()),
        spent=sum(spent.values()),
        days_left=days_left(year, month, today),
        rows=rows,
        unbudgeted=unbudgeted,
    )


def plan_limits(user, year, month, total):
    """New {category_id: limit} for a plan total: the first split when the month
    is empty, a proportional rescale of the current limits otherwise."""
    current = limits_for(user, year, month)
    if current:
        ordered = {c.pk: current[c.pk] for c in expense_categories(user) if c.pk in current}
        return distribute(total, ordered)
    return distribute(total, {c.pk: c.budget_share for c in expense_categories(user)})


def previous_month(year, month):
    return (year - 1, 12) if month == 1 else (year, month - 1)


def month_start(year, month):
    return date(year, month, 1)
