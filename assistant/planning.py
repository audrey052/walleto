"""Rest-of-month plans and monthly report figures (assistant spec, add-assistant-planning
design decisions 1, 2, 3 and 5).

Pure code over the user's own data, tested without a model: the model only proposes
plan amounts and writes the report's summary sentence, and both are checked here.
"""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass, field
from datetime import date

from django.db import transaction

from core.templatetags.money import rupiah
from finance import budgets, goals
from finance.models import MIN_CATEGORY_LIMIT, Budget, SavingsGoal, Transaction
from finance.periods import Period
from finance.summary import period_summary

LARGEST_EXPENSES = 10


# ---------- rest-of-month plan ----------

@dataclass(frozen=True)
class PlanRow:
    category_id: int
    name: str
    limit: int
    spent: int
    left: int  # limit - spent, negative when over
    daily_average: int  # spent so far per elapsed day


@dataclass(frozen=True)
class PlanFacts:
    year: int
    month: int
    plan: int
    left: int  # what is left of the category limits: sum(limit - spent)
    days_left: int
    rows: list = field(default_factory=list)

    @property
    def month_param(self):
        return f"{self.year:04d}-{self.month:02d}"

    @property
    def can_plan(self):
        return bool(self.rows) and self.left > 0


def plan_facts(user, today):
    """The current month's facts for a plan (design decision 1)."""
    plan = budgets.month_budget(user, today.year, today.month, today)
    rows = [
        PlanRow(row.category.pk, row.category.name, row.limit, row.spent, row.remaining, row.spent // today.day)
        for row in sorted(plan.rows, key=lambda r: r.category.name)
    ]
    return PlanFacts(
        year=today.year, month=today.month, plan=plan.plan,
        left=sum(r.left for r in rows), days_left=plan.days_left, rows=rows,
    )


def check_plan(facts, amounts):
    """Validate proposed amounts {name_or_id: amount}. Returns (rows, None) or (None, error).

    `rows` is [{category_id, name, spent, left_now, amount, per_day}] in the facts' order.
    """
    if not facts.can_plan:
        return None, "There is nothing left of this month's category limits to plan."
    by_key = {}
    for row in facts.rows:
        by_key[str(row.category_id)] = row
        by_key[row.name.casefold()] = row
    chosen = {}
    for key, value in amounts.items():
        row = by_key.get(str(key).strip().casefold())
        if row is None:
            names = ", ".join(r.name for r in facts.rows)
            return None, f"'{key}' is not one of the limited categories ({names})."
        if row.category_id in chosen:
            return None, f"{row.name} appears more than once."
        if isinstance(value, bool) or not isinstance(value, int):
            try:
                value = int(str(value).replace(".", "").replace(",", "").strip())
            except ValueError:
                return None, f"The amount for {row.name} must be a whole number of Rupiah."
        if value < 0:
            return None, f"The amount for {row.name} cannot be negative."
        chosen[row.category_id] = value
    missing = [r.name for r in facts.rows if r.category_id not in chosen]
    if missing:
        return None, "Give an amount for every limited category; missing: " + ", ".join(missing) + "."
    total = sum(chosen.values())
    if total != facts.left:
        diff = total - facts.left
        direction = "over" if diff > 0 else "under"
        return None, (f"The amounts add up to {rupiah(total)}, {rupiah(abs(diff))} {direction} what is left "
                      f"({rupiah(facts.left)}). They must add up exactly to {rupiah(facts.left)}.")
    for row in facts.rows:
        if row.spent + chosen[row.category_id] < MIN_CATEGORY_LIMIT:
            return None, f"{row.name} would end with a limit under {rupiah(MIN_CATEGORY_LIMIT)}; give it more."
    days = max(facts.days_left, 1)
    return [
        {
            "category_id": r.category_id, "name": r.name, "spent": r.spent, "left_now": r.left,
            "amount": chosen[r.category_id], "per_day": chosen[r.category_id] // days,
        }
        for r in facts.rows
    ], None


def apply_plan(user, rows, today):
    """Set each limit to spent + amount for the current month, all or nothing (design decision 3)."""
    month_start = date(today.year, today.month, 1)
    with transaction.atomic():
        for row in rows:
            updated = Budget.objects.for_user(user).filter(
                month=month_start, category_id=row["category_id"],
            ).update(limit=row["spent"] + row["amount"])
            if updated != 1:
                raise ValueError(f"No limit for {row['name']} this month.")
    return budgets.month_budget(user, today.year, today.month, today).plan


# ---------- monthly report ----------

def report_figures(user, year, month, today):
    """Every number the report shows, as plain JSON-ready values (design decision 5)."""
    period = Period.for_month(year, month)
    summary = period_summary(user, period, today)
    plan = budgets.month_budget(user, year, month, today)
    categories = [
        {"name": r.category.name, "spent": r.spent, "limit": r.limit, "percent": r.percent}
        for r in plan.rows if r.spent or r.limit
    ] + [
        {"name": r.category.name, "spent": r.spent, "limit": None, "percent": None}
        for r in plan.unbudgeted if r.spent
    ]
    categories.sort(key=lambda c: -c["spent"])
    largest = (
        Transaction.objects.for_user(user).in_period(period.start, period.end).expense()
        .select_related("category", "wallet").order_by("-amount", "-date", "-pk")[:LARGEST_EXPENSES]
    )
    goal_rows = [
        goals.summarize(g, g.saved, today)
        for g in SavingsGoal.objects.for_user(user).with_saved().active().order_by("position", "created_at", "id")
    ]
    return {
        "month": f"{year:04d}-{month:02d}",
        "label": period.label,
        "income": summary.income,
        "expenses": summary.expense,
        "has_plan": plan.has_plan,
        "plan": plan.plan,
        "remaining": plan.remaining,
        "categories": categories,
        "largest": [
            {"date": t.date.isoformat(), "description": t.description, "category": t.category.name,
             "wallet": t.wallet.name, "amount": t.amount}
            for t in largest
        ],
        "goals": [
            {"name": s.goal.name, "saved": s.saved, "target": s.goal.target, "percent": s.percent,
             "status": s.status_label or ""}
            for s in goal_rows
        ],
    }


def figures_text(figures):
    """The figures as short text for the summary call and the model."""
    lines = [f"Month: {figures['label']}", f"Income: {rupiah(figures['income'])}", f"Expenses: {rupiah(figures['expenses'])}"]
    if figures["has_plan"]:
        lines += [f"Plan: {rupiah(figures['plan'])}", f"Remaining: {rupiah(figures['remaining'])}"]
    for c in figures["categories"]:
        part = f"Category {c['name']}: spent {rupiah(c['spent'])}"
        if c["limit"]:
            part += f" of {rupiah(c['limit'])} ({c['percent']}%)"
        lines.append(part)
    for g in figures["goals"]:
        lines.append(f"Goal {g['name']}: {rupiah(g['saved'])} of {rupiah(g['target'])} ({g['percent']}%)")
    return "\n".join(lines)


AMOUNT_RE = re.compile(r"Rp\s?[\d.]+")
PERCENT_RE = re.compile(r"\d+(?:[.,]\d+)?\s?%")


def _allowed(figures):
    amounts = {figures["income"], figures["expenses"], figures["plan"], figures["remaining"], abs(figures["remaining"])}
    percents = set()
    for c in figures["categories"]:
        amounts.update(v for v in (c["spent"], c["limit"]) if v is not None)
        if c["percent"] is not None:
            percents.add(c["percent"])
    for t in figures["largest"]:
        amounts.add(t["amount"])
    for g in figures["goals"]:
        amounts.update((g["saved"], g["target"]))
        percents.add(g["percent"])
    return {rupiah(a).replace("−", "") for a in amounts}, {f"{p}%" for p in percents}


def check_summary(text, figures):
    """True when every Rp amount and percent in the text is one of the figures."""
    if not text or not text.strip():
        return False
    amounts, percents = _allowed(figures)
    for found in AMOUNT_RE.findall(text):
        if found.replace(" ", "").rstrip(".") not in amounts:
            return False
    for found in PERCENT_RE.findall(text):
        if found.replace(" ", "") not in percents:
            return False
    return True


def code_summary(figures):
    """A plain summary written from the figures when the model's cannot be used."""
    text = f"In {figures['label']} you spent {rupiah(figures['expenses'])} and received {rupiah(figures['income'])}."
    if figures["has_plan"]:
        if figures["remaining"] >= 0:
            text += f" {rupiah(figures['remaining'])} of the {rupiah(figures['plan'])} plan was left."
        else:
            text += f" Spending went {rupiah(-figures['remaining'])} over the {rupiah(figures['plan'])} plan."
    if figures["categories"]:
        top = figures["categories"][0]
        text += f" {top['name']} was the largest category at {rupiah(top['spent'])}."
    return text


def month_has_started(year, month, today):
    return (year, month) <= (today.year, today.month)


def last_day(year, month):
    return date(year, month, calendar.monthrange(year, month)[1])
