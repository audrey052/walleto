"""Transactions page, and add / edit / delete for transactions and transfers."""

from datetime import date
from itertools import groupby
from urllib.parse import urlencode

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone

from core.htmx import redirect_after_save, render_form, safe_next

from .forms import TransactionForm, TransferForm
from .models import Category, Transaction, Transfer, Wallet

PAGE_SIZE = 50


# ---------- helpers ----------

def _parse_month(value, today):
    """`YYYY-MM` -> (year, month); invalid or future values fall back to the current month."""
    try:
        year, month = (int(part) for part in (value or "").split("-"))
        if not 1 <= month <= 12 or year < 2000:
            raise ValueError
    except ValueError:
        return today.year, today.month
    if (year, month) > (today.year, today.month):
        return today.year, today.month
    return year, month


def _shift(year, month, delta):
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


def _month_param(year, month):
    return f"{year:04d}-{month:02d}"


def _int_or_none(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def transactions_url(year, month, **filters):
    params = {"month": _month_param(year, month)}
    params.update({k: v for k, v in filters.items() if v})
    return f"{reverse('finance:transactions')}?{urlencode(params)}"


# ---------- page ----------

def transaction_list(request):
    user = request.user
    today = timezone.localdate()
    year, month = _parse_month(request.GET.get("month"), today)

    wallets = Wallet.objects.for_user(user)
    categories = Category.objects.for_user(user)
    wallet = wallets.filter(pk=_int_or_none(request.GET.get("wallet"))).first()
    category = categories.filter(pk=_int_or_none(request.GET.get("category"))).first()
    query = (request.GET.get("q") or "").strip()

    transactions = (
        Transaction.objects.for_user(user).in_month(year, month).select_related("wallet", "category")
    )
    transfers = Transfer.objects.for_user(user).in_month(year, month).select_related("from_wallet", "to_wallet")
    if wallet:
        transactions = transactions.filter(wallet=wallet)
        transfers = transfers.touching(wallet)
    if category:
        transactions = transactions.filter(category=category)
        transfers = transfers.none()  # transfers have no category (transfers spec)
    if query:
        transactions = transactions.search(query)
        transfers = transfers.search(query)

    # Merge both kinds of entries, newest first (design decision 4).
    entries =[(t, "transaction") for t in transactions] + [(t, "transfer") for t in transfers]
    entries.sort(key=lambda pair: (pair[0].date, pair[0].created_at, pair[0].pk), reverse=True)

    page = Paginator(entries, PAGE_SIZE).get_page(request.GET.get("page"))

    # Full-day subtotals from the database, so a day split across pages stays correct.
    day_totals = {
        row["date"]: row["income"] - row["expense"]
        for row in transactions.order_by().values("date").annotate(
            income=Coalesce(Sum("amount", filter=Q(kind=Category.Kind.INCOME)), 0),
            expense=Coalesce(Sum("amount", filter=Q(kind=Category.Kind.EXPENSE)), 0),
        )
    }
    days = [
        {"date": day, "net": day_totals.get(day, 0), "entries": list(items)}
        for day, items in groupby(page.object_list, key=lambda pair: pair[0].date)
    ]

    filters = {
        "wallet": wallet.pk if wallet else None,
        "category": category.pk if category else None,
        "q": query,
    }
    prev_year, prev_month = _shift(year, month, -1)
    next_year, next_month = _shift(year, month, 1)
    is_current = (year, month) == (today.year, today.month)

    def page_url(number):
        return transactions_url(year, month, **filters, page=number)

    context = {
        "month_start": date(year, month, 1),
        "month_param": _month_param(year, month),
        "is_current_month": is_current,
        "prev_url": transactions_url(prev_year, prev_month, **filters),
        "next_url": None if is_current else transactions_url(next_year, next_month, **filters),
        "summary": transactions.totals(),
        "page": page,
        "page_prev_url": page_url(page.previous_page_number()) if page.has_previous() else None,
        "page_next_url": page_url(page.next_page_number()) if page.has_next() else None,
        "days": days,
        "entry_count": len(entries),
        "wallet_options": wallets.order_by("is_archived", "created_at"),
        "category_options": categories,
        "selected_wallet": wallet,
        "selected_category": category,
        "query": query,
        "has_filters": bool(wallet or category or query),
        "clear_url": transactions_url(year, month),
        "can_transfer": wallets.active().count() >= 2,
        "has_wallets": wallets.active().exists(),
        "current_url": request.get_full_path(),
    }
    return render(request, "finance/transactions.html", context)


# ---------- transactions ----------

def _own_transaction(request, pk):
    return get_object_or_404(Transaction.objects.select_related("wallet", "category"), pk=pk, user=request.user)


def _after_save_url(request, record):
    return safe_next(request, transactions_url(record.date.year, record.date.month))


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
        record = form.save()
        messages.success(request, "Transaction added.")
        return redirect_after_save(request, _after_save_url(request, record))
    return _transaction_form(
        request, form, title="Add transaction",
        action=reverse("finance:transaction_create"), submit_label="Add transaction",
    )


def transaction_edit(request, pk):
    record = _own_transaction(request, pk)
    form = TransactionForm(request.POST or None, instance=record, user=request.user)
    if request.method == "POST" and form.is_valid():
        record = form.save()
        messages.success(request, "Transaction updated.")
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


def _transfer_form(request, form, *, title, action, submit_label, delete_url=None):
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
    form = TransferForm(request.POST or None, instance=record, user=request.user)
    if request.method == "POST" and form.is_valid():
        record = form.save()
        messages.success(request, "Transfer updated.")
        return redirect_after_save(request, _after_save_url(request, record))
    return _transfer_form(
        request, form, title="Edit transfer",
        action=reverse("finance:transfer_edit", args=[pk]), submit_label="Save changes",
        delete_url=reverse("finance:transfer_delete", args=[pk]),
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
