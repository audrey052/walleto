"""Replace `SavingsGoal.is_main` with `position` (drag-and-drop order; the first goal is the main one).

Existing goals keep the order the old rule gave: the goal made main first,
then the nearest deadline, then goals without a deadline, oldest first.
"""

from collections import defaultdict

from django.db import migrations, models


def number_goals(apps, schema_editor):
    SavingsGoal = apps.get_model("finance", "SavingsGoal")
    by_user = defaultdict(list)
    for goal in SavingsGoal.objects.all():
        by_user[goal.user_id].append(goal)
    for goals in by_user.values():
        goals.sort(key=lambda g: (not g.is_main, g.deadline is None, g.deadline or g.start_date, g.created_at, g.pk))
        for index, goal in enumerate(goals):
            goal.position = index
            goal.save(update_fields=["position"])


class Migration(migrations.Migration):
    dependencies = [("finance", "0005_savings_goals")]

    operations = [
        migrations.AddField(
            model_name="savingsgoal", name="position", field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(number_goals, migrations.RunPython.noop),
        migrations.RemoveField(model_name="savingsgoal", name="is_main"),
        migrations.AlterModelOptions(name="savingsgoal", options={"ordering": ["position", "created_at", "id"]}),
    ]
