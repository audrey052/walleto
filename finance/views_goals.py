"""Savings goals page, goal detail, and the goal modals (savings-goals spec)."""

from django.contrib import messages
from django.db import transaction as db_transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.htmx import redirect_after_save, render_form, safe_next
from core.templatetags.money import rupiah

from . import goals
from .forms import DepositForm, GoalForm, WithdrawForm
from .models import GoalContribution, SavingsGoal


def _own_goal(request, pk, *, active=False):
    """The user's goal (never a deleted one); `active` also hides completed goals. 404 otherwise."""
    queryset = SavingsGoal.objects.for_user(request.user).with_saved()
    if active:
        queryset = queryset.active()
    return get_object_or_404(queryset, pk=pk)


def _detail_url(goal):
    return reverse("finance:goal_detail", args=[goal.pk])


def _other_goals_order(summary):
    goal = summary.goal
    return (goal.deadline is None, goal.deadline or goal.start_date, goal.created_at, goal.pk)


# ---------- pages ----------

def goal_list(request):
    today = timezone.localdate()
    own = SavingsGoal.objects.for_user(request.user).with_saved()
    active = [goals.summarize(g, g.saved, today) for g in own.active()]
    main_goal = goals.main_goal([s.goal for s in active])
    main = next((s for s in active if s.goal is main_goal), None)
    others = sorted((s for s in active if s is not main), key=_other_goals_order)
    completed = [goals.summarize(g, g.saved, today) for g in own.completed().order_by("-completed_at")]
    return render(
        request,
        "finance/goals.html",
        {
            "main": main,
            "others": others,
            "completed": completed,
            "ledger_heights": goals.LEDGER_HEIGHTS,
        },
    )


def goal_detail(request, pk):
    today = timezone.localdate()
    goal = _own_goal(request, pk)
    summary = goals.summarize(goal, goal.saved, today)
    movements = list(goal.contributions.select_related("wallet"))
    end = min(today, goal.completed_at.date()) if goal.completed_at else today
    series = goals.saved_series(
        goal.start_date, max(end, goal.start_date), [(m.date, m.is_deposit, m.amount) for m in movements]
    )
    chart = {
        "saved": [[day.isoformat(), value] for day, value in series],
        "plan": (
            [[day.isoformat(), value] for day, value in goals.plan_series(goal.start_date, goal.deadline, goal.target)]
            if goal.deadline else None
        ),
        "target": goal.target,
    }
    return render(
        request,
        "finance/goal_detail.html",
        {"summary": summary, "goal": goal, "movements": movements, "chart": chart},
    )


# ---------- create and edit ----------

def _goal_form(request, form, *, title, action, submit_label, delete_url=None):
    return render_form(
        request,
        {
            "form": form,
            "title": title,
            "action": action,
            "body": "finance/_goal_fields.html",
            "submit_label": submit_label,
            "delete_url": delete_url,
            "next": safe_next(request, ""),
            "cancel_url": reverse("finance:goals"),
        },
    )


def goal_create(request):
    form = GoalForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Goal created.")
        return redirect_after_save(request, reverse("finance:goals"))
    return _goal_form(
        request, form, title="New savings goal", action=reverse("finance:goal_create"), submit_label="Create goal"
    )


def goal_edit(request, pk):
    goal = _own_goal(request, pk)
    form = GoalForm(request.POST or None, user=request.user, instance=goal)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Goal updated.")
        return redirect_after_save(request, safe_next(request, reverse("finance:goals")))
    return _goal_form(
        request, form, title="Edit goal", action=reverse("finance:goal_edit", args=[pk]),
        submit_label="Save changes", delete_url=reverse("finance:goal_delete", args=[pk]),
    )


# ---------- deposits and withdrawals ----------

def _movement(request, pk, form_class, *, title, submit_label, message):
    goal = _own_goal(request, pk, active=True)
    form = form_class(request.POST or None, user=request.user, goal=goal)
    if request.method == "POST" and form.is_valid():
        record = form.save()
        messages.success(request, message.format(goal=goal.name, wallet=record.wallet.name))
        return redirect_after_save(request, safe_next(request, reverse("finance:goals")))
    return render_form(
        request,
        {
            "form": form,
            "goal": goal,
            "is_deposit": form_class is DepositForm,
            "title": title,
            "description": f"{goal.name} · {rupiah(goal.saved)} of {rupiah(goal.target)} saved",
            "action": request.path,
            "body": "finance/_goal_movement_fields.html",
            "submit_label": submit_label,
            "next": safe_next(request, ""),
            "cancel_url": _detail_url(goal),
        },
    )


def goal_deposit(request, pk):
    return _movement(
        request, pk, DepositForm, title="Add to this goal", submit_label="Add money", message="Added to {goal}."
    )


def goal_withdraw(request, pk):
    return _movement(
        request, pk, WithdrawForm, title="Move money back", submit_label="Move money back",
        message="Moved back to {wallet}.",
    )


# ---------- main, complete, reopen ----------

@require_POST
def goal_make_main(request, pk):
    goal = _own_goal(request, pk, active=True)
    with db_transaction.atomic():
        SavingsGoal.objects.filter(user=request.user, is_main=True).update(is_main=False)
        SavingsGoal.objects.filter(pk=goal.pk).update(is_main=True)
    messages.success(request, f"{goal.name} is now your main goal.")
    return redirect(safe_next(request, reverse("finance:goals")))


@require_POST
def goal_complete(request, pk):
    goal = _own_goal(request, pk, active=True)
    if goal.saved < goal.target:
        messages.error(request, f"{goal.name} hasn't reached its target yet.")
    else:
        SavingsGoal.objects.filter(pk=goal.pk).update(completed_at=timezone.now(), is_main=False)
        messages.success(request, f"{goal.name} completed.")
    return redirect(safe_next(request, reverse("finance:goals")))


@require_POST
def goal_reopen(request, pk):
    goal = _own_goal(request, pk)
    if goal.completed_at is None:
        raise Http404
    SavingsGoal.objects.filter(pk=goal.pk).update(completed_at=None)
    messages.success(request, f"{goal.name} is active again.")
    return redirect(safe_next(request, reverse("finance:goals")))


# ---------- delete ----------

def goal_delete(request, pk):
    """GET asks first; POST soft-deletes, and only an empty goal (design decision 2)."""
    goal = _own_goal(request, pk)
    holds_money = goal.saved != 0
    if request.method == "POST":
        if holds_money:
            messages.error(request, f"Move the {rupiah(goal.saved)} in {goal.name} back to a wallet first.")
            return redirect_after_save(request, _detail_url(goal))
        SavingsGoal.objects.filter(pk=goal.pk).update(deleted_at=timezone.now(), is_main=False)
        messages.success(request, "Goal deleted.")
        return redirect_after_save(request, reverse("finance:goals"))
    return render_form(
        request,
        {
            "goal": goal,
            "holds_money": holds_money,
            "title": "Move the money back first" if holds_money else f"Delete {goal.name}?",
            "action": reverse("finance:goal_delete", args=[pk]),
            "body": "finance/_goal_delete_body.html",
            "submit_label": "Delete goal",
            "danger": True,
            "hide_submit": holds_money,
            "cancel_url": _detail_url(goal),
        },
    )


def movement_delete(request, pk):
    """GET asks first; POST removes it, unless that would make the goal's saved amount negative."""
    record = get_object_or_404(
        GoalContribution.objects.select_related("goal", "wallet").filter(
            goal__deleted_at__isnull=True, goal__completed_at__isnull=True
        ),
        pk=pk, user=request.user,
    )
    saved = SavingsGoal.objects.with_saved().get(pk=record.goal_id).saved
    blocked = record.is_deposit and saved - record.amount < 0
    if request.method == "POST":
        if blocked:
            messages.error(request, "Removing this deposit would leave the goal below Rp0. Remove the withdrawals first.")
        else:
            record.delete()
            messages.success(request, "Deposit removed." if record.is_deposit else "Withdrawal removed.")
        return redirect_after_save(request, _detail_url(record.goal))
    return render_form(
        request,
        {
            "record": record,
            "blocked": blocked,
            "title": "Remove this deposit?" if record.is_deposit else "Remove this withdrawal?",
            "action": reverse("finance:goal_movement_delete", args=[pk]),
            "body": "finance/_goal_movement_delete_body.html",
            "submit_label": "Remove",
            "danger": True,
            "hide_submit": blocked,
            "cancel_url": _detail_url(record.goal),
        },
    )
