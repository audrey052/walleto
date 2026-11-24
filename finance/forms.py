from django import forms
from django.db.models import Max, Q
from django.utils import dateformat, timezone

from core.forms import AmountField
from core.templatetags.money import rupiah

from . import budgets
from .models import (
    MIN_CATEGORY_LIMIT, MIN_GOAL_TARGET, MIN_PLAN_TOTAL,
    Category, GoalContribution, SavingsGoal, Transaction, Transfer, Wallet,
)

DUPLICATE_NAME = "You already have a wallet with this name."
AMOUNT_POSITIVE = "Amount must be greater than 0."
FUTURE_DATE = "Date can't be in the future."
SAME_WALLET = "Choose two different wallets."
NOT_ENOUGH = "Not enough in {name}. Choose another wallet or a smaller amount."


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
        widget=forms.TextInput(attrs={"placeholder": "67.500"}),
    )


class WalletForm(forms.ModelForm):
    initial_balance = AmountField(
        label="Starting balance",
        required=False,
        help_text="How much was in this wallet before you started using Walleto. Leave empty for Rp0.",
        widget=forms.TextInput(attrs={"placeholder": "2.500.000"}),
    )

    class Meta:
        model = Wallet
        fields = ["name", "type", "initial_balance"]
        labels = {"name": "Name", "type": "Type"}
        error_messages = {"name": {"required": "Enter a name for this wallet."}}
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "BCA, GoPay, Cash", "autocomplete": "off"}),
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
            "description": forms.TextInput(attrs={"placeholder": "GoFood, Indomaret, Salary", "autocomplete": "off"}),
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "note": forms.TextInput(attrs={"placeholder": "Lunch with the team"}),
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
            "note": forms.TextInput(attrs={"placeholder": "Top up for the week"}),
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
            # Start with the first two active wallets, as the Figma transfer modal does.
            first_two = list(Wallet.objects.for_user(user).active().values_list("pk", flat=True)[:2])
            if len(first_two) == 2:
                self.initial.setdefault("from_wallet", first_two[0])
                self.initial.setdefault("to_wallet", first_two[1])
        _style(self)
        # Large amount box from the Figma transfer modal; the box itself is drawn by the template.
        self.fields["amount"].widget.attrs.update({
            "class": "h-[53px] w-full min-w-0 bg-transparent text-[27px] font-medium tracking-[-0.8px] text-forest tabular-nums outline-none placeholder:text-placeholder",
            "placeholder": "0",
        })

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
        amount = cleaned.get("amount")
        if source and amount and not self.has_error("to_wallet"):
            # transfers spec, "A transfer can't overdraw its source". In clean() the
            # instance still holds the saved values, so an edit can add back its own amount.
            available = Wallet.objects.with_balance().get(pk=source.pk).balance
            if self.instance.pk and self.instance.from_wallet_id == source.pk:
                available += self.instance.amount
            if amount > available:
                self.add_error("amount", NOT_ENOUGH.format(name=source.name))
        # Model constraints skip fields that already have errors, so the
        # database's same-wallet check never adds a second, less friendly message.
        return cleaned


PLAN_TOO_SMALL = "The plan must be at least Rp100.000."
LIMIT_TOO_SMALL = "The limit must be at least Rp1.000."


class PlanForm(forms.Form):
    """One total for the month: first split or proportional rescale (budgets spec)."""

    total = AmountField(
        label="Monthly spending budget (Rp)",
        error_messages={"required": PLAN_TOO_SMALL},
        widget=forms.TextInput(attrs={"placeholder": "8.000.000"}),
    )

    def __init__(self, *args, user, year, month, **kwargs):
        self.user, self.year, self.month = user, year, month
        super().__init__(*args, **kwargs)
        _style(self)

    def clean_total(self):
        total = self.cleaned_data["total"]
        if total is None or total < MIN_PLAN_TOTAL:
            raise forms.ValidationError(PLAN_TOO_SMALL)
        self.limits = budgets.plan_limits(self.user, self.year, self.month, total)
        if min(self.limits.values()) < MIN_CATEGORY_LIMIT:
            raise forms.ValidationError(
                "That total would make a category limit smaller than Rp1.000. Enter a larger total."
            )
        return total


class CategoryLimitForm(forms.Form):
    limit = AmountField(
        label="Monthly limit (Rp)",
        error_messages={"required": LIMIT_TOO_SMALL},
        widget=forms.TextInput(attrs={"placeholder": "2.400.000"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)

    def clean_limit(self):
        limit = self.cleaned_data["limit"]
        if limit is None or limit < MIN_CATEGORY_LIMIT:
            raise forms.ValidationError(LIMIT_TOO_SMALL)
        return limit


# ---------- savings goals (savings-goals spec) ----------

GOAL_NAME_USED = "You already have a goal with this name."
GOAL_TARGET_TOO_SMALL = "The target must be at least Rp1.000."
DEADLINE_NOT_FUTURE = "The deadline must be after today."
CHOOSE_WALLET = "Choose a wallet."
BEFORE_START = "The date can't be before this goal started ({start})."
GOAL_HOLDS_ONLY = "This goal holds only {amount}."


class GoalForm(forms.ModelForm):
    target = AmountField(
        label="Target",
        error_messages={"required": GOAL_TARGET_TOO_SMALL},
        widget=forms.TextInput(attrs={"placeholder": "6.000.000"}),
    )

    class Meta:
        model = SavingsGoal
        fields = ["name", "target", "deadline"]
        labels = {"name": "Name", "deadline": "Deadline (optional)"}
        error_messages = {"name": {"required": "Enter a name for this goal."}}
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Bali trip, Emergency fund", "autocomplete": "off"}),
            "deadline": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.instance.user = user
        self._saved_deadline = self.instance.deadline if self.instance.pk else None
        _style(self)

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())
        if not name:
            raise forms.ValidationError("Enter a name for this goal.")
        clashes = SavingsGoal.objects.for_user(self.user).active().filter(name__iexact=name)
        if self.instance.pk:
            clashes = clashes.exclude(pk=self.instance.pk)
        if clashes.exists():
            raise forms.ValidationError(GOAL_NAME_USED)
        return name

    def clean_target(self):
        target = self.cleaned_data["target"]
        if target is None or target < MIN_GOAL_TARGET:
            raise forms.ValidationError(GOAL_TARGET_TOO_SMALL)
        return target

    def clean_deadline(self):
        deadline = self.cleaned_data.get("deadline")
        # An edit may keep a deadline that has since passed (spec, "Edit and delete goals").
        if deadline and deadline <= timezone.localdate() and deadline != self._saved_deadline:
            raise forms.ValidationError(DEADLINE_NOT_FUTURE)
        return deadline

    def save(self, commit=True):
        if not self.instance.pk:
            self.instance.start_date = timezone.localdate()
            # A new goal goes to the end of the user's order.
            last = SavingsGoal.objects.for_user(self.user).aggregate(last=Max("position"))["last"]
            self.instance.position = 0 if last is None else last + 1
        return super().save(commit)


class _GoalMovementForm(_DateNotInFuture, forms.ModelForm):
    """Deposit or withdrawal between one of the user's active wallets and a goal."""

    kind = None
    amount = _positive_amount_field()

    class Meta:
        model = GoalContribution
        fields = ["wallet", "amount", "date", "note"]
        labels = {"note": "Note (optional)"}
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "note": forms.TextInput(attrs={"placeholder": "After payday"}),
        }

    def __init__(self, *args, user, goal, **kwargs):
        self.user, self.goal = user, goal
        super().__init__(*args, **kwargs)
        self.instance.user, self.instance.goal, self.instance.kind = user, goal, self.kind
        field = self.fields["wallet"]
        field.queryset = Wallet.objects.for_user(user).active().with_balance()
        field.label_from_instance = lambda w: f"{w.name} · {rupiah(w.balance)}"
        field.empty_label = "Choose a wallet"
        field.error_messages.update({"required": CHOOSE_WALLET, "invalid_choice": CHOOSE_WALLET})
        if not self.is_bound:
            self.initial.setdefault("date", timezone.localdate())
            first = field.queryset.first()
            if first:
                self.initial.setdefault("wallet", first.pk)
        _style(self)

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount is None or amount <= 0:
            raise forms.ValidationError(AMOUNT_POSITIVE)
        return amount

    def clean_date(self):
        value = super().clean_date()
        if value < self.goal.start_date:
            start = self.goal.start_date
            raise forms.ValidationError(BEFORE_START.format(start=f"{start.day} {dateformat.format(start, 'M Y')}"))
        return value


class DepositForm(_GoalMovementForm):
    kind = GoalContribution.Kind.DEPOSIT

    def clean(self):
        cleaned = super().clean()
        wallet, amount = cleaned.get("wallet"), cleaned.get("amount")
        if wallet and amount and amount > Wallet.objects.with_balance().get(pk=wallet.pk).balance:
            self.add_error("amount", NOT_ENOUGH.format(name=wallet.name))
        return cleaned


class WithdrawForm(_GoalMovementForm):
    kind = GoalContribution.Kind.WITHDRAWAL

    def clean(self):
        cleaned = super().clean()
        amount = cleaned.get("amount")
        saved = SavingsGoal.objects.with_saved().get(pk=self.goal.pk).saved
        if amount and amount > saved:
            self.add_error("amount", GOAL_HOLDS_ONLY.format(amount=rupiah(saved)))
        return cleaned
