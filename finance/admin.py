from django.contrib import admin

from .models import Budget, Category, Transaction, Transfer, Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "type", "initial_balance", "is_archived", "created_at"]
    list_filter = ["type", "is_archived"]
    search_fields = ["name", "user__email"]
    readonly_fields = ["created_at", "updated_at", "archived_at"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "kind", "is_default", "user", "color", "icon", "order", "budget_share"]
    list_filter = ["kind"]
    search_fields = ["name", "user__email"]

    @admin.display(boolean=True, description="Default")
    def is_default(self, obj):
        return obj.is_default


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["date", "description", "kind", "amount", "category", "wallet", "user", "source"]
    list_filter = ["kind", "source", "category"]
    search_fields = ["description", "note", "user__email"]
    date_hierarchy = "date"


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ["date", "from_wallet", "to_wallet", "amount", "user"]
    search_fields = ["note", "user__email"]
    date_hierarchy = "date"


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ["month", "category", "limit", "user"]
    list_filter = ["month", "category"]
    search_fields = ["user__email"]
