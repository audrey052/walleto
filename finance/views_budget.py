"""Budget page, plan and category-limit modals, and copy last month (budgets spec)."""

from datetime import date

from django.contrib import messages
from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import dateformat, timezone
from django.views.decorators.http import require_POST

from core.htmx import redirect_after_save, render_form

from . import budgets
from .forms import CategoryLimitForm, PlanForm
from .models import Budget
from .months import month_param, parse_month, shift


def _month(request):
    today = timezone.localdate()
    year, month = parse_month(request.GET.get("month"), today, allow_next=True)
    return today, year, month


def budget_url(year, month, view="finance:budget", *args):
    return f"{reverse(view, args=args)}?month={month_param(year, month)}"


def _own_category(request, category_id):
    """Only expense categories the user can see; anything else is 404 (budgets spec, privacy)."""
    return get_object_or_404(budgets.expense_categories(request.user), pk=category_id)


# ---------- page ----------

def budget_page(request):
    today, year, month = _month(request)
    plan = budgets.month_budget(request.user, year, month, today)

    prev_year, prev_month = shift(year, month, -1)
    next_year, next_month = shift(year, month, 1)
    at_latest = (year, month) == shift(today.year, today.month, 1)
    can_copy = not plan.has_plan and (
        Budget.objects.for_user(request.user).in_month(prev_year, prev_month).exists()
    )

    return render(
        request,
        "finance/budget.html",
        {
            "plan": plan,
            "month_start": date(year, month, 1),
            "is_past": (year, month) < (today.year, today.month),
            "prev_url": budget_url(prev_year, prev_month),
            "next_url": None if at_latest else budget_url(next_year, next_month),
            "plan_url": budget_url(year, month, "finance:budget_plan"),
            "copy_url": budget_url(year, month, "finance:budget_copy"),
            "can_copy": can_copy,
            "prev_month_start": date(prev_year, prev_month, 1),
            "month_query": f"?month={month_param(year, month)}",
        },
    )


# ---------- monthly plan ----------

def budget_plan(request):
    today, year, month = _month(request)
    current = budgets.limits_for(request.user, year, month)
    form = PlanForm(
        request.POST or None,
        user=request.user, year=year, month=month,
        initial={"total": sum(current.values()) or None},
    )
    if request.method == "POST" and form.is_valid():
        with db_transaction.atomic():
            for category_id, limit in form.limits.items():
                Budget.objects.update_or_create(
                    user=request.user, category_id=category_id, month=date(year, month, 1),
                    defaults={"limit": limit},
                )
        messages.success(request, "Your monthly spending plan has been updated.")
        return redirect_after_save(request, budget_url(year, month))
    return render_form(
        request,
        {
            "form": form,
            "title": "Give your month a plan.",
            "description": "Your category limits will adjust proportionally.",
            "action": budget_url(year, month, "finance:budget_plan"),
            "body": "finance/_budget_plan_fields.html",
            "submit_label": "Save monthly plan",
            "cancel_url": budget_url(year, month),
            "month_start": date(year, month, 1),
            "is_first_split": not current,
        },
    )


# ---------- one category ----------

def budget_category(request, category_id):
    today, year, month = _month(request)
    category = _own_category(request, category_id)
    existing = Budget.objects.for_user(request.user).in_month(year, month).filter(category=category).first()
    form = CategoryLimitForm(request.POST or None, initial={"limit": existing.limit if existing else None})
    if request.method == "POST" and form.is_valid():
        Budget.objects.update_or_create(
            user=request.user, category=category, month=date(year, month, 1),
            defaults={"limit": form.cleaned_data["limit"]},
        )
        messages.success(request, f"{category.name} budget updated.")
        return redirect_after_save(request, budget_url(year, month))
    return render_form(
        request,
        {
            "form": form,
            "title": "Edit budget" if existing else f"Set a limit for {category.name}",
            "description": f"{category.name} · {dateformat.format(date(year, month, 1), 'F Y')}",
            "action": budget_url(year, month, "finance:budget_category", category.pk),
            "body": "finance/_budget_limit_fields.html",
            "submit_label": "Save limit",
            "delete_url": budget_url(year, month, "finance:budget_category_remove", category.pk) if existing else None,
            "delete_label": "Remove limit",
            "cancel_url": budget_url(year, month),
            "spent": budgets.category_spent(request.user, category, year, month),
        },
    )


def budget_category_remove(request, category_id):
    """GET asks for confirmation; only POST removes (same pattern as deleting a transaction)."""
    today, year, month = _month(request)
    category = _own_category(request, category_id)
    existing = get_object_or_404(
        Budget.objects.for_user(request.user).in_month(year, month), category=category
    )
    if request.method == "POST":
        existing.delete()
        messages.success(request, f"{category.name} limit removed.")
        return redirect_after_save(request, budget_url(year, month))
    return render_form(
        request,
        {
            "category": category,
            "limit": existing.limit,
            "title": f"Remove the {category.name} limit?",
            "action": budget_url(year, month, "finance:budget_category_remove", category.pk),
            "body": "finance/_budget_remove_body.html",
            "submit_label": "Remove limit",
            "danger": True,
            "cancel_url": budget_url(year, month),
        },
    )


# ---------- copy last month ----------

@require_POST
def budget_copy(request):
    today, year, month = _month(request)
    own = Budget.objects.for_user(request.user)
    prev_year, prev_month = budgets.previous_month(year, month)
    previous = list(own.in_month(prev_year, prev_month))
    if previous and not own.in_month(year, month).exists():
        visible = set(budgets.expense_categories(request.user).values_list("pk", flat=True))
        Budget.objects.bulk_create([
            Budget(user=request.user, category_id=b.category_id, month=date(year, month, 1), limit=b.limit)
            for b in previous if b.category_id in visible
        ])
        messages.success(request, f"Copied {dateformat.format(date(prev_year, prev_month, 1), 'F')}'s budget.")
    return redirect(budget_url(year, month))
