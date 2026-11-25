"""assistant spec: the plan card's Apply, the report download and their privacy (with a fake model)."""

from datetime import date, datetime
from datetime import timezone as dt_timezone
from unittest import mock

from django.urls import reverse

from assistant.llm import Reply, ToolCall
from assistant.models import Message
from finance.models import Budget
from finance.tests.test_views import make_user

from .test_views import HTMX, PAGE, AssistantPageCase

PROPOSAL = {"amounts": [{"category": "Food & drinks", "amount": 150_000}, {"category": "Transport", "amount": 89_000}]}


class PlanCase(AssistantPageCase):
    def setUp(self):
        super().setUp()
        self.limit(self.food, 1_600_000)
        self.limit(self.transport, 500_000)
        self.add(1_405_500, day=date(2026, 11, 10))
        self.add(455_500, cat=self.transport, day=date(2026, 11, 12))

    def plan_card(self):
        self.script(
            Reply(tool_calls=[ToolCall("c1", "plan_rest_of_month", {})]),
            Reply(tool_calls=[ToolCall("c2", "propose_budget_plan", PROPOSAL)]),
            Reply(text="Here is a plan; check it and apply it to Budget."),
        )
        self.ask("Help me plan the rest of the month")
        return Message.objects.get(tool_name="propose_budget_plan")

    def limits(self):
        rows = Budget.objects.filter(user=self.user, month=date(2026, 11, 1))
        return {b.category_id: b.limit for b in rows}

    def apply(self, row, amounts=None):
        data = {f"amount_{cat.pk}": value for cat, value in (amounts or {}).items()}
        return self.client.post(reverse("assistant:apply_plan", args=[row.pk]), data, **HTMX)


class PlanTests(PlanCase):
    def test_suggestion_shown(self):
        self.assertContains(self.client.get(PAGE), "Help me plan the rest of the month")

    def test_apply(self):
        row = self.plan_card()
        before = self.limits()
        page = self.client.get(PAGE)
        self.assertContains(page, "Apply to Budget")
        self.assertEqual(self.limits(), before)  # nothing changes before Apply
        response = self.apply(row)
        self.assertContains(response, "Applied to Budget")
        self.assertEqual(self.limits(), {self.food.pk: 1_555_500, self.transport.pk: 544_500})
        self.assertEqual(sum(self.limits().values()), sum(before.values()))  # plan total unchanged
        self.assertEqual(Message.objects.get(pk=row.pk).cards[0]["state"], "applied")

    def test_edited_amounts(self):
        row = self.plan_card()
        self.apply(row, {self.food: "100.000", self.transport: "139.000"})
        self.assertEqual(self.limits(), {self.food.pk: 1_505_500, self.transport.pk: 594_500})

    def test_edited_amounts_that_do_not_add_up(self):
        row = self.plan_card()
        before = self.limits()
        response = self.apply(row, {self.food: 200_000, self.transport: 100_000})
        self.assertContains(response, "Rp61.000 over")
        self.assertEqual(self.limits(), before)
        self.assertEqual(Message.objects.get(pk=row.pk).cards[0]["state"], "pending")

    def test_applied_twice(self):
        row = self.plan_card()
        self.apply(row)
        self.apply(row, {self.food: 239_000, self.transport: 0})
        self.assertEqual(self.limits(), {self.food.pk: 1_555_500, self.transport.pk: 544_500})

    def test_month_has_passed(self):
        row = self.plan_card()
        before = self.limits()
        later = datetime(2026, 12, 2, 3, 0, tzinfo=dt_timezone.utc)
        with mock.patch("django.utils.timezone.now", return_value=later):
            self.client.force_login(self.user)  # the first session is older than two weeks by then
            response = self.apply(row)
        self.assertContains(response, "month that has ended")
        self.assertEqual(self.limits(), before)
        self.assertEqual(Message.objects.get(pk=row.pk).cards[0]["state"], "expired")


class ReportTests(PlanCase):
    def report_card(self):
        self.script(
            Reply(tool_calls=[ToolCall("c1", "generate_report", {"month": "2026-10"})]),
            Reply(text="Nothing to summarise."),  # the summary call
            Reply(text="Your October report is ready."),
        )
        self.ask("Make a report for October")
        return Message.objects.get(tool_name="generate_report")

    def test_report_for_a_month(self):
        row = self.report_card()
        self.assertContains(self.client.get(PAGE), "Monthly report · October 2026")
        response = self.client.get(reverse("assistant:report_pdf", args=[row.pk]))
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="walleto-report-2026-10.pdf"')
        self.assertTrue(response.content.startswith(b"%PDF"))


class PlanPrivacyTests(PlanCase):
    def test_another_users_plan(self):
        row = self.plan_card()
        before = self.limits()
        self.client.force_login(make_user(email="other@example.com", name="Other"))
        self.assertEqual(self.client.post(reverse("assistant:apply_plan", args=[row.pk])).status_code, 404)
        self.assertEqual(self.limits(), before)
        self.assertEqual(Message.objects.get(pk=row.pk).cards[0]["state"], "pending")

    def test_another_users_report(self):
        row = ReportTests.report_card(self)
        self.client.force_login(make_user(email="other@example.com", name="Other"))
        self.assertEqual(self.client.get(reverse("assistant:report_pdf", args=[row.pk])).status_code, 404)

    def test_wrong_card_type(self):
        row = self.plan_card()
        self.assertEqual(self.client.get(reverse("assistant:report_pdf", args=[row.pk])).status_code, 404)
