"""The Assistant's tools: plain functions over the user's own data (assistant spec,
add-assistant design decision 2).

Every tool takes the signed-in user and today from the request, never from the
model. Categories, wallets and goals are passed by name and resolved inside the
user's own querysets. Bad arguments come back as {"error": ...} so the model can
correct itself; tools never raise for them. Each result carries:

- `data`: JSON for the model (amounts as integers and as "Rp1.405.500" text);
- `cards`: what the page shows, built here from the same figures;
- `counted`: the number of transactions behind the answer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from core.templatetags.money import rupiah
from finance import budgets, goals
from finance.forms import TransactionForm
from finance.models import Category, SavingsGoal, Transaction, Wallet
from finance.periods import Period, parse_period
from finance.summary import change_tenths, period_summary


@dataclass
class ToolResult:
    data: dict
    cards: list = field(default_factory=list)
    counted: int = 0


def error(message):
    return ToolResult({"error": message})


# ---------- helpers ----------

MONTH_RE = re.compile(r"^\d{4}-\d{2}$")
DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _period(args, today):
    """A Period from `month` or `from`/`to`, or an error message."""
    month, start, end = args.get("month"), args.get("from"), args.get("to")
    if start or end:
        if not (start and end and DAY_RE.match(str(start)) and DAY_RE.match(str(end))):
            return None, "Give both 'from' and 'to' as YYYY-MM-DD."
        try:
            date.fromisoformat(start), date.fromisoformat(end)
        except ValueError:
            return None, "'from' and 'to' must be real dates (YYYY-MM-DD)."
        if date.fromisoformat(start) > today:
            return None, "That period starts after today; there is no data yet."
        return parse_period({"from": start, "to": end}, today), None
    if month:
        if not MONTH_RE.match(str(month)) or not 1 <= int(str(month)[5:]) <= 12:
            return None, "Give 'month' as YYYY-MM."
        if str(month) > today.strftime("%Y-%m"):
            return None, "That month has not started yet; there is no data."
        return parse_period({"month": month}, today), None
    return parse_period({}, today), None  # the current month


def _by_name(queryset, name, label):
    """The one object whose name matches (any case), or an error message listing the choices."""
    wanted = (name or "").strip().casefold()
    for item in queryset:
        if item.name.casefold() == wanted:
            return item, None
    names = ", ".join(sorted(item.name for item in queryset))
    return None, f"There is no {label} called '{name}'. Choose one of: {names}."


def _money(value):
    return {"amount": value, "text": rupiah(value)}


def _change_text(tenths):
    if tenths is None:
        return None
    whole, tenth = divmod(abs(tenths), 10)
    return f"{'↑' if tenths >= 0 else '↓'} {whole}.{tenth}%"


def _figures(title, rows, note=""):
    """A figures card: [(label, value text)] rows under a title."""
    return {"type": "figures", "title": title, "rows": [[label, value] for label, value in rows], "note": note}


# ---------- tools ----------

def query_transactions(user, today, **args):
    period, problem = _period(args, today)
    if problem:
        return error(problem)
    qs = Transaction.objects.for_user(user)
    labels = []
    if args.get("category"):
        category, problem = _by_name(Category.objects.for_user(user), args["category"], "category")
        if problem:
            return error(problem)
        qs, labels = qs.filter(category=category), labels + [category.name]
    if args.get("wallet"):
        wallet, problem = _by_name(Wallet.objects.for_user(user), args["wallet"], "wallet")
        if problem:
            return error(problem)
        qs, labels = qs.filter(wallet=wallet), labels + [wallet.name]
    if args.get("keyword"):
        qs, labels = qs.search(args["keyword"]), labels + [f"“{args['keyword']}”"]
    kind = args.get("kind")
    if kind:
        if kind not in ("income", "expense"):
            return error("'kind' must be 'income' or 'expense'.")
        qs = qs.filter(kind=kind)

    now = qs.in_period(period.start, period.end)
    before = period.previous()
    then = qs.in_period(before.start, before.end)
    totals, previous = now.totals(), then.totals()
    count = now.count()
    measure = kind or "expense"
    change = change_tenths(totals[measure], previous[measure])

    data = {
        "period": period.label,
        "filters": labels,
        "transactions": count,
        "income": _money(totals["income"]),
        "expenses": _money(totals["expense"]),
        "previous_period": before.label,
        "previous_income": _money(previous["income"]),
        "previous_expenses": _money(previous["expense"]),
        f"{measure}_change": _change_text(change) or "no data in the previous period",
    }
    if count == 0:
        data["note"] = "No transactions in this period with these filters."
    rows = []
    if kind != "income":
        rows.append(("Expenses", rupiah(totals["expense"])))
    if kind != "expense" and (kind == "income" or totals["income"]):
        rows.append(("Income", rupiah(totals["income"])))
    rows.append((f"vs. {before.label}", _change_text(change) or "—"))
    title = " · ".join(labels + [period.label])
    return ToolResult(data, [_figures(title, rows)] if count else [], count)


def get_monthly_summary(user, today, **args):
    period, problem = _period({"month": args.get("month")} if args.get("month") else {}, today)
    if problem:
        return error(problem)
    s = period_summary(user, period, today)
    count = Transaction.objects.for_user(user).in_period(period.start, period.end).count()
    data = {
        "month": period.label,
        "transactions": count,
        "income": _money(s.income),
        "expenses": _money(s.expense),
        "expenses_change_vs_last_month": _change_text(s.expense_change_tenths) or "no data last month",
        "has_monthly_plan": s.has_plan,
        "top_categories": [{"category": line.category.name, "spent": rupiah(line.spent)} for line in s.categories[:5]],
    }
    rows = [("Income", rupiah(s.income)), ("Expenses", rupiah(s.expense))]
    if s.has_plan:
        data.update(plan=_money(s.plan), remaining=_money(s.remaining))
        rows += [("Plan", rupiah(s.plan)), ("Remaining", rupiah(s.remaining))]
    return ToolResult(data, [_figures(period.label, rows)], count)


def check_budget(user, today, **args):
    period, problem = _period({"month": args.get("month")} if args.get("month") else {}, today)
    if problem:
        return error(problem)
    year, month = period.month
    plan = budgets.month_budget(user, year, month, today)
    if not plan.has_plan:
        return ToolResult({"month": period.label, "has_monthly_plan": False,
                           "note": "This month has no monthly plan on the Budget page."})

    if args.get("category"):
        category, problem = _by_name(budgets.expense_categories(user), args["category"], "expense category")
        if problem:
            return error(problem)
        count = Transaction.objects.for_user(user).in_month(year, month).filter(category=category).count()
        row = next((r for r in plan.rows if r.category == category), None)
        if row is None:
            spent = next((r.spent for r in plan.unbudgeted if r.category == category), 0)
            data = {"month": period.label, "category": category.name, "has_limit": False, "spent": _money(spent)}
            return ToolResult(data, [_figures(f"{category.name} · {period.label}", [("Spent", rupiah(spent)), ("Limit", "No limit")])], count)
        per_day = budgets.per_day(row.remaining, plan.days_left)
        data = {
            "month": period.label, "category": category.name, "has_limit": True,
            "limit": _money(row.limit), "spent": _money(row.spent), "remaining": _money(row.remaining),
            "percent_used": row.percent, "days_left": plan.days_left,
            "per_day": _money(per_day) if per_day is not None else None,
        }
        rows = [("Limit", rupiah(row.limit)), ("Spent", rupiah(row.spent)), ("Remaining", rupiah(row.remaining))]
        if per_day is not None:
            rows.append(("Per day", rupiah(per_day)))
        return ToolResult(data, [_figures(f"{category.name} · {period.label}", rows)], count)

    count = Transaction.objects.for_user(user).in_month(year, month).expense().count()
    data = {
        "month": period.label, "has_monthly_plan": True,
        "plan": _money(plan.plan), "spent": _money(plan.spent), "remaining": _money(plan.remaining),
        "percent_used": plan.percent, "days_left": plan.days_left,
        "per_day": _money(plan.per_day) if plan.per_day is not None else None,
        "categories_over_limit": [r.category.name for r in plan.rows if r.over_by],
    }
    rows = [("Plan", rupiah(plan.plan)), ("Spent", rupiah(plan.spent)), ("Remaining", rupiah(plan.remaining))]
    if plan.per_day is not None:
        rows.append(("Per day", rupiah(plan.per_day)))
    return ToolResult(data, [_figures(f"Budget · {period.label}", rows)], count)


def get_goal_progress(user, today, **args):
    own = SavingsGoal.objects.for_user(user).with_saved().active().order_by("position", "created_at", "id")
    if args.get("goal"):
        goal, problem = _by_name(own, args["goal"], "active savings goal")
        if problem:
            return error(problem)
        own = [goal]
    summaries = [goals.summarize(g, g.saved, today) for g in own]
    if not summaries:
        return ToolResult({"goals": [], "note": "There are no active savings goals."})
    data = {"goals": [
        {
            "goal": s.goal.name, "saved": _money(s.saved), "target": _money(s.goal.target),
            "to_go": _money(s.to_go), "percent": s.percent, "reached": s.reached,
            "status": s.status_label or None,
            "deadline": s.goal.deadline.isoformat() if s.goal.deadline else None,
            "per_month": _money(s.per_month) if s.per_month else None,
        }
        for s in summaries
    ]}
    cards = []
    for s in summaries:
        rows = [("Saved", rupiah(s.saved)), ("Target", rupiah(s.goal.target)), ("To go", rupiah(s.to_go))]
        if s.per_month:
            rows.append(("Per month", rupiah(s.per_month)))
        # Only "Behind" and "Past deadline" are shown, as on the Savings goals page.
        cards.append(_figures(s.goal.name, rows, note="" if s.status == goals.ON_TRACK else s.status_label))
    return ToolResult(data, cards)


def add_transaction(user, today, **args):
    """Check a transaction like the Transactions form does, without saving it (design decision 2)."""
    category, problem = _by_name(Category.objects.for_user(user), args.get("category"), "category")
    if problem:
        return error(problem)
    wallet, problem = _by_name(Wallet.objects.for_user(user).active(), args.get("wallet"), "active wallet")
    if problem:
        return error(problem)
    amount = args.get("amount")
    form = TransactionForm(
        data={
            "description": args.get("description", ""),
            "amount": str(amount) if amount is not None else "",
            "category": category.pk,
            "wallet": wallet.pk,
            "date": args.get("date") or today.isoformat(),
            "note": args.get("note", ""),
        },
        user=user,
    )
    if not form.is_valid():
        messages = [f"{name}: {' '.join(errors)}" for name, errors in form.errors.items()]
        return error("The transaction is not valid. " + " ".join(messages))
    clean = form.cleaned_data
    fields = {
        "description": clean["description"], "amount": clean["amount"],
        "category_id": category.pk, "category": category.name, "kind": category.kind,
        "wallet_id": wallet.pk, "wallet": wallet.name,
        "date": clean["date"].isoformat(), "note": clean.get("note") or "",
    }
    data = {
        "draft": {**fields, "amount": rupiah(clean["amount"])},
        "status": "Not saved. The user must press Save on the card to record it.",
    }
    return ToolResult(data, [{"type": "draft", "state": "pending", "fields": fields}])


# ---------- registry and schemas ----------

PERIOD_PROPS = {
    "month": {"type": "string", "description": "A whole month as YYYY-MM. Omit for the current month."},
    "from": {"type": "string", "description": "First day of a range, YYYY-MM-DD (with 'to')."},
    "to": {"type": "string", "description": "Last day of a range, YYYY-MM-DD (with 'from')."},
}


def _schemas(user):
    categories = sorted(Category.objects.for_user(user).values_list("name", flat=True))
    expense_categories = sorted(budgets.expense_categories(user).values_list("name", flat=True))
    wallets = sorted(Wallet.objects.for_user(user).values_list("name", flat=True))
    active_wallets = sorted(Wallet.objects.for_user(user).active().values_list("name", flat=True))
    goal_names = sorted(SavingsGoal.objects.for_user(user).active().values_list("name", flat=True))

    def enum(names, description):
        spec = {"type": "string", "description": description}
        if names:
            spec["enum"] = names
        return spec

    return {
        "query_transactions": {
            "description": "Use for any 'how much did I spend / earn / pay' question: totals and count of the user's "
                           "transactions for a period, optionally filtered by category, wallet, keyword or kind, "
                           "with the same filters' totals for the previous period of the same length.",
            "properties": {
                **PERIOD_PROPS,
                "category": enum(categories, "Only this category."),
                "wallet": enum(wallets, "Only this wallet."),
                "keyword": {"type": "string", "description": "Text to find in descriptions and notes, e.g. 'kopi'."},
                "kind": {"type": "string", "enum": ["income", "expense"], "description": "Only income or only expenses."},
            },
            "required": [],
        },
        "get_monthly_summary": {
            "description": "Use for an overview of a whole month ('summary', 'how did the month go'): income, expenses, "
                           "change vs. last month, monthly plan and remaining, and top categories.",
            "properties": {"month": PERIOD_PROPS["month"]},
            "required": [],
        },
        "check_budget": {
            "description": "A month's budget: plan, spent, remaining and per day; or one expense category's limit, spent and remaining.",
            "properties": {"month": PERIOD_PROPS["month"], "category": enum(expense_categories, "One expense category.")},
            "required": [],
        },
        "get_goal_progress": {
            "description": "Saved, target, amount to go, status and monthly amount for one active savings goal, or all of them.",
            "properties": {"goal": enum(goal_names, "One goal by name. Omit for all active goals.")},
            "required": [],
        },
        "add_transaction": {
            "description": "Prepare a transaction for the user to confirm. It is NOT saved: the page shows a card with Save. "
                           "Use only when the user asks to record income or an expense.",
            "properties": {
                "description": {"type": "string", "description": "Short name, e.g. 'Bakmi GM'."},
                "amount": {"type": "integer", "description": "Whole Rupiah, e.g. 45000 for '45rb' or '45k', 2000000 for '2jt'."},
                "category": enum(categories, "The category; its kind decides income or expense."),
                "wallet": enum(active_wallets, "The wallet the money came from or went to."),
                "date": {"type": "string", "description": "YYYY-MM-DD; today when not said. Never in the future."},
                "note": {"type": "string", "description": "Optional note."},
            },
            "required": ["description", "amount", "category", "wallet"],
        },
    }


TOOLS = {
    "query_transactions": query_transactions,
    "get_monthly_summary": get_monthly_summary,
    "check_budget": check_budget,
    "get_goal_progress": get_goal_progress,
    "add_transaction": add_transaction,
}


def tool_specs(user):
    """The tool list for the model, with this user's names as allowed values."""
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": spec["description"],
                "parameters": {
                    "type": "object",
                    "properties": spec["properties"],
                    "required": spec["required"],
                    "additionalProperties": False,
                },
            },
        }
        for name, spec in _schemas(user).items()
    ]


def run_tool(name, args, *, user, today):
    """Run one tool. Unknown tools and wrong arguments become an error result."""
    fn = TOOLS.get(name)
    if fn is None:
        return error(f"There is no tool called '{name}'.")
    if not isinstance(args, dict):
        return error("Arguments must be a JSON object.")
    allowed = set(_schemas(user)[name]["properties"])
    unknown = set(args) - allowed
    if unknown:
        return error(f"Unknown arguments: {', '.join(sorted(unknown))}.")
    return fn(user, today, **args)
