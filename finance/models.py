from django.conf import settings
from django.db import models
from django.db.models import F, Q, Sum
from django.db.models.functions import Lower
from django.utils import timezone

# Muted monogram colors taken from the Figma wallet cards (design.md decision 6).
WALLET_COLORS = ["#426050", "#597D73", "#8D826E", "#A39C87", "#1F5C4A"]


class WalletQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(user=user)

    def active(self):
        return self.filter(is_archived=False)

    def archived(self):
        return self.filter(is_archived=True)

    def with_balance(self):
        """Annotate `balance`. Until transactions exist it equals the starting balance.

        MVP 2 extends only this method with income, expenses and transfers.
        """
        return self.annotate(balance=F("initial_balance"))

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

    @property
    def monogram(self):
        """Short label for the wallet tile (wallets spec, "Wallet monogram")."""
        if self.type == self.Type.CASH:
            return "Rp"
        words = self.name.split()
        if not words:
            return "?"
        if len(words) >= 2:
            return (words[0][0] + words[1][0]).upper()
        word = words[0]
        if len(word) <= 4:
            return word.upper()
        return word[0].upper() + word[1].lower()

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
