from datetime import date

from django.conf import settings
from django.db import models
from django.db.models import F, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce, Lower
from django.utils import timezone

# Muted wallet colors from the Figma design (add-wallets design decision 6); used for the wallet dots.
WALLET_COLORS = ["#426050", "#597D73", "#8D826E", "#A39C87", "#1F5C4A"]


class WalletQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)

    def active(self):
        return self.filter(is_archived=False)

    def archived(self):
        return self.filter(is_archived=True)

    def with_balance(self):
        """Annotate `balance` = starting balance + income - expenses + transfers in - transfers out.

        Each part is a correlated subquery (design.md decision 3): summing over
        joined transactions and transfers in one query would multiply rows.
        """

        def total(queryset):
            sums = queryset.order_by().values("_group").annotate(total=Sum("amount")).values("total")
            return Coalesce(Subquery(sums, output_field=models.BigIntegerField()), 0)

        wallet_tx = Transaction.objects.filter(wallet=OuterRef("pk")).annotate(_group=F("wallet"))
        transfers_in = Transfer.objects.filter(to_wallet=OuterRef("pk")).annotate(_group=F("to_wallet"))
        transfers_out = Transfer.objects.filter(from_wallet=OuterRef("pk")).annotate(_group=F("from_wallet"))

        return self.annotate(
            balance=F("initial_balance")
            + total(wallet_tx.filter(kind=Category.Kind.INCOME))
            - total(wallet_tx.filter(kind=Category.Kind.EXPENSE))
            + total(transfers_in)
            - total(transfers_out)
        )

    def total_balance(self):
        return self.with_balance().aggregate(total=Sum("balance"))["total"] or 0


class Wallet(models.Model):
    class Type(models.TextChoices):
        CASH = "cash", "Cash"
        BANK = "bank", "Bank account"
        EWALLET = "ewallet", "E-wallet"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallets"
    )
    name = models.CharField(max_length=40)
    type = models.CharField(max_length=10, choices=Type.choices, default=Type.BANK)
    # Whole Rupiah (design.md decision 2).
    initial_balance = models.BigIntegerField("starting balance", default=0)
    color = models.CharField(max_length=7, blank=True)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = WalletQuerySet.as_manager()

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                "user",
                Lower("name"),
                condition=Q(is_archived=False),
                name="unique_active_wallet_name_per_user",
                violation_error_message="You already have a wallet with this name.",
            ),
            models.CheckConstraint(
                condition=Q(initial_balance__gte=0),
                name="wallet_initial_balance_not_negative",
            ),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        if not self.color:
            count = Wallet.objects.filter(user_id=self.user_id).count()
            self.color = WALLET_COLORS[count % len(WALLET_COLORS)]
        super().save(*args, **kwargs)

    def archive(self):
        self.is_archived = True
        self.archived_at = timezone.now()
        self.save(update_fields=["is_archived", "archived_at", "updated_at"])

    def restore(self):
        self.is_archived = False
        self.archived_at = None
        self.save(update_fields=["is_archived", "archived_at", "updated_at"])


class CategoryQuerySet(models.QuerySet):
    def for_user(self, user):
        """Defaults (user is NULL) plus the user's own categories."""
        return self.filter(Q(user__isnull=True) | Q(user=user))

    def expense(self):
        return self.filter(kind=Category.Kind.EXPENSE)

    def income(self):
        return self.filter(kind=Category.Kind.INCOME)


class Category(models.Model):
    class Kind(models.TextChoices):
        EXPENSE = "expense", "Expense"
        INCOME = "income", "Income"

    # NULL means a default category shared by every user (design.md decision 7).
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="categories",
    )
    name = models.CharField(max_length=40)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    color = models.CharField(max_length=7)
    icon = models.CharField(max_length=30, default="other")
    order = models.PositiveSmallIntegerField(default=100)
    # Weight for the first split of a monthly plan (add-budgets design decision 2).
    budget_share = models.PositiveSmallIntegerField(default=10)

    objects = CategoryQuerySet.as_manager()

    class Meta:
        ordering = ["kind", "order", "name"]
        verbose_name_plural = "categories"
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                "kind",
                condition=Q(user__isnull=True),
                name="unique_default_category_name",
            ),
            models.UniqueConstraint(
                "user",
                Lower("name"),
                "kind",
                condition=Q(user__isnull=False),
                name="unique_user_category_name",
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def is_default(self):
        return self.user_id is None


def month_bounds(year, month):
    """First day of the month and first day of the next month."""
    start = date(year, month, 1)
    end = date(year + (month == 12), month % 12 + 1, 1)
    return start, end


class TransactionQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)

    def in_month(self, year, month):
        start, end = month_bounds(year, month)
        return self.filter(date__gte=start, date__lt=end)

    def search(self, text):
        text = (text or "").strip()
        if not text:
            return self
        return self.filter(Q(description__icontains=text) | Q(note__icontains=text))

    def income(self):
        return self.filter(kind=Category.Kind.INCOME)

    def expense(self):
        return self.filter(kind=Category.Kind.EXPENSE)

    def totals(self):
        """Income, expenses and net in one query (transfers are a separate model)."""
        sums = self.aggregate(
            income=Coalesce(Sum("amount", filter=Q(kind=Category.Kind.INCOME)), 0),
            expense=Coalesce(Sum("amount", filter=Q(kind=Category.Kind.EXPENSE)), 0),
        )
        sums["net"] = sums["income"] - sums["expense"]
        return sums


class Transaction(models.Model):
    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        AI = "ai", "AI quick add"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions"
    )
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name="transactions")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="transactions")
    # Copied from the category on save (design.md decision 2), stored so sums need no join.
    kind = models.CharField(max_length=10, choices=Category.Kind.choices, editable=False)
    amount = models.BigIntegerField()
    date = models.DateField()
    description = models.CharField(max_length=80)
    note = models.CharField(max_length=120, blank=True)
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.MANUAL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TransactionQuerySet.as_manager()

    class Meta:
        ordering = ["-date", "-created_at", "-id"]
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["wallet", "kind"]),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="transaction_amount_positive"),
        ]

    def __str__(self):
        return f"{self.description} ({self.amount})"

    def save(self, *args, **kwargs):
        self.kind = self.category.kind
        self.description = self.description.strip()
        super().save(*args, **kwargs)

    @property
    def is_income(self):
        return self.kind == Category.Kind.INCOME


class TransferQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)

    def in_month(self, year, month):
        start, end = month_bounds(year, month)
        return self.filter(date__gte=start, date__lt=end)

    def touching(self, wallet):
        return self.filter(Q(from_wallet=wallet) | Q(to_wallet=wallet))

    def search(self, text):
        text = (text or "").strip()
        if not text:
            return self
        return self.filter(note__icontains=text)


class Transfer(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transfers"
    )
    from_wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name="transfers_out")
    to_wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name="transfers_in")
    amount = models.BigIntegerField()
    date = models.DateField()
    note = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TransferQuerySet.as_manager()

    class Meta:
        ordering = ["-date", "-created_at", "-id"]
        indexes = [models.Index(fields=["user", "date"])]
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="transfer_amount_positive"),
            models.CheckConstraint(
                condition=~Q(from_wallet=F("to_wallet")), name="transfer_wallets_differ"
            ),
        ]

    def __str__(self):
        return f"{self.from_wallet} → {self.to_wallet} ({self.amount})"


MIN_CATEGORY_LIMIT = 1_000
MIN_PLAN_TOTAL = 100_000


class BudgetQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)

    def in_month(self, year, month):
        return self.filter(month=date(year, month, 1))


class Budget(models.Model):
    """A spending limit for one expense category in one month (budgets spec).

    The monthly plan is the sum of a month's limits; it is never stored
    (add-budgets design decision 1).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets"
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="budgets")
    # Always the first day of the month.
    month = models.DateField()
    limit = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = BudgetQuerySet.as_manager()

    class Meta:
        ordering = ["month", "category__order", "category__name"]
        constraints = [
            models.UniqueConstraint(
                "user", "category", "month", name="unique_budget_per_category_month"
            ),
            models.CheckConstraint(
                condition=Q(limit__gte=MIN_CATEGORY_LIMIT), name="budget_limit_minimum"
            ),
        ]

    def __str__(self):
        return f"{self.category} {self.month:%b %Y}: {self.limit}"

    def save(self, *args, **kwargs):
        self.month = self.month.replace(day=1)
        super().save(*args, **kwargs)
