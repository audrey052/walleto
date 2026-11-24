"""Transactions page, and add / edit / delete for transactions and transfers."""

import csv
from urllib.parse import urlencode

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import dateformat, timezone

from core.htmx import redirect_after_save, render_form, safe_next
from core.templatetags.money import rupiah

from . import budgets
from .forms import TransactionForm, TransferForm
from .models import Budget, Category, GoalContribution, Transaction, Transfer, Wallet
from .months import month_param as _month_param
from .periods import Period, parse_period

PAGE_SIZE = 50


# ---------- helpers ----------

def _int_or_none(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def transactions_url(period, *, view="finance:transactions", **filters):
    """Transactions (or its export) for a period, keeping the filters (add-date-range design decision 3)."""
    params = period.query()
    params.update({k: v for k, v in filters.items() if v})
    return f"{reverse(view)}?{urlencode(params)}"


# ---------- shared period + filter query ----------

def _activity(request):
    """The selected period and filters, the filtered querysets and the merged entries.

    Used by the page and by the CSV export, so both always show the same rows.
    """
    user = request.user
    today = timezone.localdate()
    period = parse_period(request.GET, today)

    wallets = Wallet.objects.for_user(user)
    categories = Category.objects.for_user(user)
    wallet = wallets.filter(pk=_int_or_none(request.GET.get("wallet"))).first()
    category = categories.filter(pk=_int_or_none(request.GET.get("category"))).first()
    query = (request.GET.get("q") or "").strip()

    transactions = (
        Transaction.objects.for_user(user).in_period(period.start, period.end).select_related("wallet", "category")
    )
    transfers = Transfer.objects.for_user(user).in_period(period.start, period.end).select_related("from_wallet", "to_wallet")
    # Goal deposits and withdrawals, deleted goals included (add-savings-goals design decision 9).
    goal_moves = GoalContribution.objects.for_user(user).in_period(period.start, period.end).select_related("goal", "wallet")
    if wallet:
        transactions = transactions.filter(wallet=wallet)
        transfers = transfers.touching(wallet)
        goal_moves = goal_moves.touching(wallet)
    if category:
        transactions = transactions.filter(category=category)
        transfers = transfers.none()  # transfers have no category (transfers spec)
        goal_moves = goal_moves.none()
    if query:
        transactions = transactions.search(query)
        transfers = transfers.search(query)
        goal_moves = goal_moves.search(query)

    # Merge every kind of entry, newest first (design decision 4).
    entries = (
        [(t, "transaction") for t in transactions]
        + [(t, "transfer") for t in transfers]
        + [(m, "goal") for m in goal_moves]
    )
    entries.sort(key=lambda pair: (pair[0].date, pair[0].created_at, pair[0].pk), reverse=True)

    return {
        "today": today, "period": period,
        "wallets": wallets, "categories": categories,
        "wallet": wallet, "category": category, "query": query,
        "transactions": transactions, "entries": entries,
        "filters": {
            "wallet": wallet.pk if wallet else None,
            "category": category.pk if category else None,
            "q": query,
        },
    }


# ---------- page ----------

def transaction_list(request):
    data = _activity(request)
    today, period = data["today"], data["period"]
    wallets, categories = data["wallets"], data["categories"]
    wallet, category, query = data["wallet"], data["category"], data["query"]
    transactions, entries, filters = data["transactions"], data["entries"], data["filters"]

    page = Paginator(entries, PAGE_SIZE).get_page(request.GET.get("page"))

    next_month = period.next_month(today)

    def page_url(number):
        return transactions_url(period, **filters, page=number)

    context = {
        "period": period,
        "prev_url": transactions_url(period.prev_month(), **filters),
        "next_url": transactions_url(next_month, **filters) if next_month else None,
        "period_target": "#transactions-page",
        "period_fields": {k: v for k, v in filters.items() if v},
        "summary": transactions.totals(),
        "page": page,
        "page_prev_url": page_url(page.previous_page_number()) if page.has_previous() else None,
        "page_next_url": page_url(page.next_page_number()) if page.has_next() else None,
        "entries": page.object_list,
        "entry_count": len(entries),
        "export_url": transactions_url(period, view="finance:transactions_export", **filters),
        "wallet_options": wallets.order_by("is_archived", "created_at"),
        "category_options": categories,
        "selected_wallet": wallet,
        "selected_category": category,
        "query": query,
        "has_filters": bool(wallet or category or query),
        "clear_url": transactions_url(period),
        "has_wallets": wallets.active().exists(),
        "current_url": request.get_full_path(),
    }
    return render(request, "finance/transactions.html", context)


def _csv_text(value):
    """Stop spreadsheet apps from running user text as a formula (CSV injection)."""
    text = str(value)
    return f"'{text}" if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


def transaction_export(request):
    """The rows the page shows for the same period and filters, as CSV (all pages)."""
    data = _activity(request)
    filename = f"walleto-transactions-{data['period'].slug}.csv"
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("﻿")  # BOM so Excel opens UTF-8 (→, é) correctly

    writer = csv.writer(response)
    writer.writerow(["Date", "Type", "Description", "Note", "Category", "Wallet", "Amount"])
    for entry, kind in data["entries"]:
        if kind == "transaction":
            signed = entry.amount if entry.is_income else -entry.amount
            writer.writerow([
                entry.date.isoformat(), entry.get_kind_display(), _csv_text(entry.description),
                _csv_text(entry.note), _csv_text(entry.category.name), _csv_text(entry.wallet.name), signed,
            ])
        elif kind == "goal":
            # transactions spec, "Goal movements in the CSV export"
            writer.writerow([
                entry.date.isoformat(), "Savings", _csv_text(entry.route), _csv_text(entry.note),
                "Savings goal", _csv_text(entry.wallet.name), entry.amount,
            ])
        else:
            route = _csv_text(f"{entry.from_wallet.name} → {entry.to_wallet.name}")
            writer.writerow([
                entry.date.isoformat(), "Transfer", route, _csv_text(entry.note), "", route, entry.amount,
            ])
    return response


# ---------- budget warning (transactions spec, add-budgets design decision 7) ----------

def _budget_watch(user, data):
    """Before saving: the limit and spent amount of the category and month the
    expense ends up in, or None when there is nothing to warn about."""
    category, day = data["category"], data["date"]
    if category.kind != Category.Kind.EXPENSE:
        return None
    budget = Budget.objects.for_user(user).in_month(day.year, day.month).filter(category=category).first()
    if budget is None:
        return None
    before = budgets.category_spent(user, category, day.year, day.month)
    return {"user": user, "category": category, "day": day, "limit": budget.limit, "before": before}


def _budget_warning(request, watch):
    """After saving: a toast when the save crossed 85% or 100% of the limit."""
    if watch is None:
        return
    category, day, limit = watch["category"], watch["day"], watch["limit"]
    after = budgets.category_spent(watch["user"], category, day.year, day.month)
    crossed = budgets.crossing(watch["before"], after, limit)
    link = f"{reverse('finance:budget')}?month={_month_param(day.year, day.month)}"
    month_name = dateformat.format(day, "F")
    if crossed == budgets.OVER:
        messages.error(
            request, f"{category.name} is over its {month_name} budget by {rupiah(after - limit)}.", extra_tags=link
        )
    elif crossed == budgets.WARNING:
        messages.warning(
            request,
            f"{category.name} is at {budgets.percent(after, limit)}% of its {month_name} budget.",
            extra_tags=link,
        )


# ---------- transactions ----------

def _own_transaction(request, pk):
    return get_object_or_404(Transaction.objects.select_related("wallet", "category"), pk=pk, user=request.user)


def _after_save_url(request, record):
    return safe_next(request, transactions_url(Period.for_month(record.date.year, record.date.month)))


def _transaction_form(request, form, *, title, action, submit_label, delete_url=None):
    has_wallets = bool(form.instance.pk) or Wallet.objects.for_user(request.user).active().exists()
    return render_form(
        request,
        {
            "form": form,
            "title": title,
            "action": action,
            "body": "finance/_transaction_fields.html",
            "submit_label": submit_label,
            "delete_url": delete_url,
            "next": safe_next(request, ""),
            "cancel_url": safe_next(request, reverse("finance:transactions")),
            "has_wallets": has_wallets,
            "hide_submit": not has_wallets,
        },
    )


def transaction_create(request):
    form = TransactionForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        watch = _budget_watch(request.user, form.cleaned_data)
        record = form.save()
        messages.success(request, "Transaction added.")
        _budget_warning(request, watch)
        return redirect_after_save(request, _after_save_url(request, record))
    return _transaction_form(
        request, form, title="Add transaction",
        action=reverse("finance:transaction_create"), submit_label="Add transaction",
    )


def transaction_edit(request, pk):
    record = _own_transaction(request, pk)
    form = TransactionForm(request.POST or None, instance=record, user=request.user)
    if request.method == "POST" and form.is_valid():
        watch = _budget_watch(request.user, form.cleaned_data)
        record = form.save()
        messages.success(request, "Transaction updated.")
        _budget_warning(request, watch)
        return redirect_after_save(request, _after_save_url(request, record))
    return _transaction_form(
        request, form, title="Edit transaction",
        action=reverse("finance:transaction_edit", args=[pk]), submit_label="Save changes",
        delete_url=reverse("finance:transaction_delete", args=[pk]),
    )


def transaction_delete(request, pk):
    record = _own_transaction(request, pk)
    if request.method == "POST":
        url = _after_save_url(request, record)
        record.delete()
        messages.success(request, "Transaction deleted.")
        return redirect_after_save(request, url)
    return render_form(
        request,
        {
            "record": record,
            "title": "Delete this transaction?",
            "action": reverse("finance:transaction_delete", args=[pk]),
            "body": "finance/_transaction_delete_body.html",
            "submit_label": "Delete transaction",
            "danger": True,
            "next": safe_next(request, ""),
            "cancel_url": reverse("finance:transactions"),
        },
    )


# ---------- transfers ----------

def _own_transfer(request, pk):
    return get_object_or_404(
        Transfer.objects.select_related("from_wallet", "to_wallet"), pk=pk, user=request.user
    )


def _transfer_wallets(form, original=None):
    """{id: {name, balance}} for the live preview (transfers spec, "Transfer preview").

    When editing, the balances are shown as they were before this transfer, so the
    preview and the server's overdraft check agree.
    """
    wallets = form.fields["from_wallet"].queryset.with_balance()
    data = {str(w.pk): {"name": w.name, "balance": w.balance} for w in wallets}
    if original:
        source, target, amount = original
        if str(source) in data:
            data[str(source)]["balance"] += amount
        if str(target) in data:
            data[str(target)]["balance"] -= amount
    return data


def _transfer_form(request, form, *, title, action, submit_label, delete_url=None, original=None):
    enough = form.has_enough_wallets
    return render_form(
        request,
        {
            "form": form,
            "title": title,
            "description": "Move money between your own wallets. It doesn't count as income or spending.",
            "action": action,
            "body": "finance/_transfer_fields.html",
            "submit_label": submit_label,
            "delete_url": delete_url,
            "hide_submit": not enough,
            "enough_wallets": enough,
            "next": safe_next(request, ""),
            "cancel_url": safe_next(request, reverse("finance:transactions")),
            "transfer_wallets": _transfer_wallets(form, original) if enough else {},
            "form_x_data": "transferForm" if enough else "",
            "submit_x_text": "" if original else "submitLabel",
            "submit_x_disabled": "insufficient" if enough else "",
        },
    )


def transfer_create(request):
    form = TransferForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.has_enough_wallets and form.is_valid():
        record = form.save()
        messages.success(request, "Transfer recorded.")
        return redirect_after_save(request, _after_save_url(request, record))
    return _transfer_form(
        request, form, title="Transfer between wallets",
        action=reverse("finance:transfer_create"), submit_label="Record transfer",
    )


def transfer_edit(request, pk):
    record = _own_transfer(request, pk)
    original = (record.from_wallet_id, record.to_wallet_id, record.amount)
    form = TransferForm(request.POST or None, instance=record, user=request.user)
    if request.method == "POST" and form.is_valid():
        record = form.save()
        messages.success(request, "Transfer updated.")
        return redirect_after_save(request, _after_save_url(request, record))
    return _transfer_form(
        request, form, title="Edit transfer",
        action=reverse("finance:transfer_edit", args=[pk]), submit_label="Save changes",
        delete_url=reverse("finance:transfer_delete", args=[pk]), original=original,
    )


def transfer_delete(request, pk):
    record = _own_transfer(request, pk)
    if request.method == "POST":
        url = _after_save_url(request, record)
        record.delete()
        messages.success(request, "Transfer deleted.")
        return redirect_after_save(request, url)
    return render_form(
        request,
        {
            "record": record,
            "title": "Delete this transfer?",
            "action": reverse("finance:transfer_delete", args=[pk]),
            "body": "finance/_transfer_delete_body.html",
            "submit_label": "Delete transfer",
            "danger": True,
            "next": safe_next(request, ""),
            "cancel_url": reverse("finance:transactions"),
        },
    )
