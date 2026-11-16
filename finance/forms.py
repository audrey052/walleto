from django import forms
from django.db.models import Q
from django.utils import timezone

from core.forms import AmountField

from .models import Category, Transaction, Transfer, Wallet

DUPLICATE_NAME = "You already have a wallet with this name."
AMOUNT_POSITIVE = "Amount must be greater than 0."
FUTURE_DATE = "Date can't be in the future."
SAME_WALLET = "Choose two different wallets."


def _style(form):
    """Give every widget the shared `.input` class from docs/STYLE.md."""
    for field in form.fields.values():
        css = field.widget.attrs.get("class", "")
        field.widget.attrs["class"] = f"{css} input".strip()


def _wallet_choices(user, *keep):
    """The user's active wallets, plus wallets already on the record being edited."""
    keep_ids = [w.pk for w in keep if w is not None and w.pk]
    return Wallet.objects.for_user(user).filter(Q(is_archived=False) | Q(pk__in=keep_ids))


def _wallet_label(wallet):
    return f"{wallet.name} (archived)" if wallet.is_archived else wallet.name


class _DateNotInFuture:
    def clean_date(self):
        value = self.cleaned_data["date"]
        if value > timezone.localdate():
            raise forms.ValidationError(FUTURE_DATE)
        return value


def _positive_amount_field(label="Amount"):
    return AmountField(
        label=label,
        error_messages={"required": AMOUNT_POSITIVE},
        widget=forms.TextInput(attrs={"placeholder": "e.g. 67.500"}),
    )


class WalletForm(forms.ModelForm):
    initial_balance = AmountField(
        label="Starting balance",
        required=False,
        help_text="How much was in this wallet before you started using Walleto. Leave empty for Rp0.",
        widget=forms.TextInput(attrs={"placeholder": "e.g. 2.500.000"}),
    )

    class Meta:
        model = Wallet
        fields = ["name", "type", "initial_balance"]
        labels = {"name": "Name", "type": "Type"}
        error_messages = {"name": {"required": "Enter a name for this wallet."}}
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. BCA, GoPay, Cash", "autocomplete": "off"}),
        }

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        # Set the owner before validation so model constraints are checked too.
        self.instance.user = user
        _style(self)

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())
        if not name:
            raise forms.ValidationError("Enter a name for this wallet.")
        clashes = Wallet.objects.for_user(self.user).active().filter(name__iexact=name)
        if self.instance.pk:
            clashes = clashes.exclude(pk=self.instance.pk)
        if clashes.exists():
            raise forms.ValidationError(DUPLICATE_NAME)
        return name


class TransactionForm(_DateNotInFuture, forms.ModelForm):
    amount = _positive_amount_field()

    class Meta:
        model = Transaction
        fields = ["description", "amount", "category", "wallet", "date", "note"]
        labels = {"note": "Note (optional)"}
        error_messages = {"description": {"required": "Enter a description, for example GoFood."}}
        widgets = {
            "description": forms.TextInput(attrs={"placeholder": "e.g. GoFood, Indomaret, Salary", "autocomplete": "off"}),
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "note": forms.TextInput(attrs={"placeholder": "e.g. Lunch with the team"}),
        }

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.instance.user = user

        wallet_field = self.fields["wallet"]
        wallet_field.queryset = _wallet_choices(user, getattr(self.instance, "wallet", None))
        wallet_field.label_from_instance = _wallet_label
        wallet_field.empty_label = "Choose a wallet"

        # One list grouped by kind: income or expense follows from the category (design decision 2).
        categories = Category.objects.for_user(user)
        category_field = self.fields["category"]
        category_field.queryset = categories
        category_field.widget.choices = [("", "Choose a category")] + [
            (label, [(c.pk, c.name) for c in categories if c.kind == kind])
            for kind, label in Category.Kind.choices
        ]

        if not self.instance.pk and not self.is_bound:
            self.initial.setdefault("date", timezone.localdate())
            active = list(wallet_field.queryset[:2])
            if len(active) == 1:
                self.initial.setdefault("wallet", active[0].pk)
        _style(self)

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount is None or amount <= 0:
            raise forms.ValidationError(AMOUNT_POSITIVE)
        return amount


class TransferForm(_DateNotInFuture, forms.ModelForm):
    amount = _positive_amount_field()

    class Meta:
        model = Transfer
        fields = ["from_wallet", "to_wallet", "amount", "date", "note"]
        labels = {"from_wallet": "From", "to_wallet": "To", "note": "Note (optional)"}
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "note": forms.TextInput(attrs={"placeholder": "e.g. Top up for the week"}),
        }

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.instance.user = user
        keep = (getattr(self.instance, "from_wallet", None), getattr(self.instance, "to_wallet", None))
        for name in ("from_wallet", "to_wallet"):
            field = self.fields[name]
            field.queryset = _wallet_choices(user, *keep)
            field.label_from_instance = _wallet_label
            field.empty_label = "Choose a wallet"
        if not self.instance.pk and not self.is_bound:
            self.initial.setdefault("date", timezone.localdate())
        _style(self)

    @property
    def has_enough_wallets(self):
        return Wallet.objects.for_user(self.user).active().count() >= 2 or bool(self.instance.pk)

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount is None or amount <= 0:
            raise forms.ValidationError(AMOUNT_POSITIVE)
        return amount

    def clean(self):
        cleaned = super().clean()
        source, target = cleaned.get("from_wallet"), cleaned.get("to_wallet")
        if source and target and source == target:
            self.add_error("to_wallet", SAME_WALLET)
        # Model constraints skip fields that already have errors, so the
        # database's same-wallet check never adds a second, less friendly message.
        return cleaned
