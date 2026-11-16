"""Create the default categories shared by every user (categories spec)."""

from django.db import migrations

# (name, kind, color, icon, order). Colors follow the chart palette in sequence.
DEFAULT_CATEGORIES = [
    ("Food & drinks", "expense", "#1F5C4A", "food", 10),
    ("Shopping", "expense", "#688373", "bag", 20),
    ("Transport", "expense", "#99AA99", "car", 30),
    ("Bills & utilities", "expense", "#B8AD92", "home", 40),
    ("Entertainment", "expense", "#D2CDBF", "ticket", 50),
    ("Health", "expense", "#1F5C4A", "heart", 60),
    ("Others", "expense", "#688373", "other", 70),
    ("Salary", "income", "#1F5C4A", "briefcase", 10),
    ("Other income", "income", "#688373", "gift", 20),
]


def create_defaults(apps, schema_editor):
    Category = apps.get_model("finance", "Category")
    for name, kind, color, icon, order in DEFAULT_CATEGORIES:
        Category.objects.update_or_create(
            user=None,
            name=name,
            kind=kind,
            defaults={"color": color, "icon": icon, "order": order},
        )


def remove_defaults(apps, schema_editor):
    Category = apps.get_model("finance", "Category")
    names = [name for name, *_ in DEFAULT_CATEGORIES]
    Category.objects.filter(user=None, name__in=names).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_defaults, remove_defaults),
    ]
