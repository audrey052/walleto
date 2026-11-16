from django.contrib import admin

from .models import Category, Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "type", "initial_balance", "is_archived", "created_at"]
    list_filter = ["type", "is_archived"]
    search_fields = ["name", "user__email"]
    readonly_fields = ["created_at", "updated_at", "archived_at"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "kind", "is_default", "user", "color", "icon", "order"]
    list_filter = ["kind"]
    search_fields = ["name", "user__email"]

    @admin.display(boolean=True, description="Default")
    def is_default(self, obj):
        return obj.is_default
