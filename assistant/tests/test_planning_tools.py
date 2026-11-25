"""assistant spec: the planning and report tools, and the loop with a fake model."""

from datetime import date

from django.test import TestCase, override_settings

from assistant import agent, tools
from assistant.llm import AssistantUnavailable, FakeClient, Reply, ToolCall
from assistant.models import Conversation, Message
from finance.tests.test_summary import SummaryFixtures

TODAY = date(2026, 11, 25)


class PlanToolCase(SummaryFixtures, TestCase):
    def setUp(self):
        super().setUp()
        self.limit(self.food, 1_600_000)
        self.limit(self.transport, 500_000)
        self.add(1_405_500, day=date(2026, 11, 10))
        self.add(455_500, cat=self.transport, day=date(2026, 11, 12))

    def run_tool(self, name, client=None, **args):
        return tools.run_tool(name, args, user=self.user, today=TODAY, client=client)


class PlanToolTests(PlanToolCase):
    def test_facts_tool(self):
        result = self.run_tool("plan_rest_of_month")
        self.assertEqual(result.data["left_of_limits"]["amount"], 239_000)
        self.assertEqual(result.data["days_left"], 6)
        self.assertIn("add up exactly to 239000", result.data["next_step"])
        self.assertEqual(result.cards, [])

    def test_no_plan(self):
        from finance.models import Budget

        Budget.objects.filter(user=self.user).delete()
        result = self.run_tool("plan_rest_of_month")
        self.assertFalse(result.data["has_monthly_plan"])
        self.assertIn("Budget page", result.data["note"])

    def test_valid_proposal_gives_a_card(self):
        result = self.run_tool("propose_budget_plan", amounts=[
            {"category": "Food & drinks", "amount": 150_000}, {"category": "Transport", "amount": 89_000}])
        card = result.cards[0]
        self.assertEqual((card["type"], card["state"], card["month"], card["left"]), ("plan", "pending", "2026-11", 239_000))
        self.assertEqual([r["amount"] for r in card["rows"]], [150_000, 89_000])
        self.assertIn("Not applied", result.data["status"])

    def test_bad_proposal_is_an_error_without_card(self):
        result = self.run_tool("propose_budget_plan", amounts=[{"category": "Food & drinks", "amount": 300_000},
                                                                {"category": "Transport", "amount": 0}])
        self.assertIn("Rp61.000 over", result.data["error"])
        self.assertEqual(result.cards, [])
        self.assertIn("error", self.run_tool("propose_budget_plan", amounts="all of it").data)


class ReportToolTests(PlanToolCase):
    def test_summary_from_the_model(self):
        client = FakeClient([Reply(text="You spent Rp1.861.000 this month.")])
        result = self.run_tool("generate_report", client=client, month="2026-11")
        card = result.cards[0]
        self.assertEqual((card["type"], card["month"], card["label"]), ("report", "2026-11", "November 2026"))
        self.assertEqual(card["summary"], "You spent Rp1.861.000 this month.")
        self.assertIsNone(client.calls[0]["tools"])
        self.assertIn("Rp1.861.000", client.calls[0]["messages"][0]["content"])

    def test_invented_number_falls_back(self):
        result = self.run_tool("generate_report", client=FakeClient([Reply(text="You saved Rp999.999!")]))
        self.assertNotIn("Rp999.999", result.cards[0]["summary"])
        self.assertIn("Rp1.861.000", result.cards[0]["summary"])

    def test_model_failure_falls_back(self):
        result = self.run_tool("generate_report", client=FakeClient([AssistantUnavailable("down")]))
        self.assertIn("In November 2026 you spent", result.cards[0]["summary"])

    def test_future_month_refused(self):
        result = self.run_tool("generate_report", client=FakeClient([]), month="2026-12")
        self.assertIn("not started", result.data["error"])
        self.assertEqual(result.cards, [])


@override_settings(ASSISTANT_MAX_TOOL_ROUNDS=4)
class PlanLoopTests(PlanToolCase):
    def test_facts_then_bad_then_fixed_proposal(self):
        chat = Conversation.objects.create(user=self.user)
        client = FakeClient([
            Reply(tool_calls=[ToolCall("c1", "plan_rest_of_month", {})]),
            Reply(tool_calls=[ToolCall("c2", "propose_budget_plan", {"amounts": [
                {"category": "Food & drinks", "amount": 200_000}, {"category": "Transport", "amount": 100_000}]})]),
            Reply(tool_calls=[ToolCall("c3", "propose_budget_plan", {"amounts": [
                {"category": "Food & drinks", "amount": 150_000}, {"category": "Transport", "amount": 89_000}]})]),
            Reply(text="Here is a plan; check it and apply it to Budget."),
        ])
        answer = agent.ask(chat, "Help me plan the rest of the month", user=self.user, today=TODAY, client=client)
        self.assertEqual(answer.text, "Here is a plan; check it and apply it to Budget.")
        cards = [c for m in chat.messages.filter(role=Message.Role.TOOL) for c in m.cards]
        self.assertEqual([c["type"] for c in cards], ["plan"])
        self.assertIn("plan_rest_of_month, then propose_budget_plan", client.calls[0]["messages"][0]["content"])
