from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.htmx import redirect_after_save, render_form

from .forms import WalletForm
from .models import Wallet


def _own_wallet(request, pk):
    """Another user's wallet answers 404, as if it did not exist (wallets spec)."""
    return get_object_or_404(Wallet, pk=pk, user=request.user)


def wallet_list(request):
    wallets = Wallet.objects.for_user(request.user)
    return render(
        request,
        "finance/wallets.html",
        {
            "wallets": wallets.active().with_balance(),
            "archived_wallets": wallets.archived().with_balance().order_by("-archived_at"),
            "total_balance": wallets.active().total_balance(),
        },
    )


def _wallet_form_response(request, form, *, title, description, action, submit_label):
    return render_form(
        request,
        {
            "form": form,
            "title": title,
            "description": description,
            "action": action,
            "body": "finance/_wallet_fields.html",
            "submit_label": submit_label,
            "cancel_url": reverse("finance:wallets"),
        },
    )


def wallet_create(request):
    form = WalletForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Wallet added.")
        return redirect_after_save(request, reverse("finance:wallets"))
    return _wallet_form_response(
        request,
        form,
        title="Add wallet",
        description="A place where you keep money: cash, a bank account or an e-wallet.",
        action=reverse("finance:wallet_create"),
        submit_label="Add wallet",
    )


def wallet_edit(request, pk):
    wallet = _own_wallet(request, pk)
    form = WalletForm(request.POST or None, instance=wallet, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Wallet updated.")
        return redirect_after_save(request, reverse("finance:wallets"))
    return _wallet_form_response(
        request,
        form,
        title="Edit wallet",
        description=None,
        action=reverse("finance:wallet_edit", args=[wallet.pk]),
        submit_label="Save changes",
    )


def wallet_archive(request, pk):
    wallet = _own_wallet(request, pk)
    if request.method == "POST":
        if not wallet.is_archived:
            wallet.archive()
            messages.success(request, f"{wallet.name} archived.")
        return redirect_after_save(request, reverse("finance:wallets"))
    return render_form(
        request,
        {
            "wallet": wallet,
            "title": f"Archive {wallet.name}?",
            "description": None,
            "action": reverse("finance:wallet_archive", args=[wallet.pk]),
            "body": "finance/_wallet_archive_body.html",
            "submit_label": "Archive wallet",
            "cancel_url": reverse("finance:wallets"),
        },
    )


@require_POST
def wallet_restore(request, pk):
    wallet = _own_wallet(request, pk)
    if wallet.is_archived:
        clash = (
            Wallet.objects.for_user(request.user)
            .active()
            .filter(name__iexact=wallet.name)
            .exists()
        )
        if clash:
            messages.error(
                request,
                f"You already have an active wallet named {wallet.name}. "
                "Rename it before restoring this one.",
            )
        else:
            wallet.restore()
            messages.success(request, f"{wallet.name} restored.")
    return redirect("finance:wallets")
