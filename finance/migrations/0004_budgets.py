"""Budgets: category limits per month, and default shares for the first split."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

# Default shares (add-budgets design decision 2); they add up to 100.
DEFAULT_SHARES = {
    "Food & drinks": 30,
    "Shopping": 15,
    "Transport": 15,
    "Bills & utilities": 15,
    "Entertainment": 10,
    "Others": 10,
    "Health": 5,
}


def set_shares(apps, schema_editor):
    Category = apps.get_model("finance", "Category")
    for name, share in DEFAULT_SHARES.items():
        Category.objects.filter(user=None, kind="expense", name=name).update(budget_share=share)


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0003_transactions_and_transfers"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="budget_share",
            field=models.PositiveSmallIntegerField(default=10),
        ),
        migrations.RunPython(set_shares, migrations.RunPython.noop),
        migrations.CreateModel(
            name="Budget",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("month", models.DateField()),
                ("limit", models.BigIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="budgets", to="finance.category")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="budgets", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["month", "category__order", "category__name"],
                "constraints": [
                    models.UniqueConstraint(models.F("user"), models.F("category"), models.F("month"), name="unique_budget_per_category_month"),
                    models.CheckConstraint(condition=models.Q(("limit__gte", 1000)), name="budget_limit_minimum"),
                ],
            },
        ),
    ]
