"""assistant spec: the tools, without any model (add-assistant design decision 2)."""

from datetime import date

from django.test import TestCase
from django.urls import reverse

from assistant import tools
from finance.models import GoalContribution, SavingsGoal, Transaction, Wallet
from finance.tests.test_summary import SummaryFixtures
from finance.tests.test_views import make_user

TODAY = date(2026, 11, 15)


class ToolCase(SummaryFixtures, TestCase):
    def run_tool(self, name, user=None, **args):
        return tools.run_tool(name, args, user=user or self.user, today=TODAY)


class RegistryTests(ToolCase):
    def test_unknown_tool_and_arguments(self):
        self.assertIn("error", self.run_tool("delete_everything").data)
        self.assertIn("Unknown arguments", self.run_tool("query_transactions", user_id=99).data["error"])

    def test_bad_periods_are_errors(self):
        for args in ({"month": "November"}, {"month": "2026-13"}, {"from": "2026-11-01"},
                     {"from": "2026-11-01", "to": "2026-02-30"}, {"month": "2027-01"}):
            with self.subTest(args=args):
                self.assertIn("error", self.run_tool("query_transactions", **args).data)

    def test_unknown_names_list_the_choices(self):
        result = self.run_tool("query_transactions", category="Pets")
        self.assertIn("There is no category called 'Pets'", result.data["error"])
        self.assertIn("Food & drinks", result.data["error"])

    def test_schemas_offer_only_the_users_names(self):
        other = make_user(email="other@example.com", name="Other")
        Wallet.objects.create(user=other, name="Secret Bank")
        specs = {s["function"]["name"]: s["function"]["parameters"] for s in tools.tool_specs(self.user)}
        self.assertEqual(set(specs), set(tools.TOOLS))
        self.assertEqual(specs["add_transaction"]["properties"]["wallet"]["enum"], ["BCA", "GoPay"])
        self.assertNotIn("Secret Bank", str(specs))


class QueryTransactionsTests(ToolCase):
    def test_spending_in_a_category(self):
        self.add(1_000_000, day=date(2026, 11, 3))
        self.add(405_500, day=date(2026, 11, 12))
        self.add(80_000, cat=self.transport)
        result = self.run_tool("query_transactions", month="2026-11", category="food & drinks")
        self.assertEqual(result.data["expenses"], {"amount": 1_405_500, "text": "Rp1.405.500"})
        self.assertEqual(result.counted, 2)
        self.assertEqual(result.cards[0]["rows"][0], ["Expenses", "Rp1.405.500"])
        # Same figure as the Transactions page for the same month and filter.
        self.client.force_login(self.user)
        page = self.client.get(reverse("finance:transactions"), {"month": "2026-11", "category": self.food.pk})
        self.assertEqual(page.context["summary"]["expense"], 1_405_500)

    def test_compared_with_the_previous_period(self):
        self.add(110_000, cat=self.transport, day=date(2026, 11, 10))
        self.add(100_000, cat=self.transport, day=date(2026, 10, 30))
        self.add(999_000, cat=self.transport, day=date(2026, 10, 1))  # before the previous 14 days
        result = self.run_tool("query_transactions", category="Transport", **{"from": "2026-11-02", "to": "2026-11-15"})
        self.assertEqual(result.data["previous_period"], "19 Oct – 1 Nov 2026")
        self.assertEqual(result.data["previous_expenses"]["amount"], 100_000)
        self.assertEqual(result.data["expense_change"], "↑ 10.0%")

    def test_keyword_and_kind(self):
        self.add(25_000, text="Kopi Kenangan")
        self.add(30_000, text="kopi susu", cat=self.shopping)
        self.add(5_000_000, cat=self.salary, text="Salary")
        self.assertEqual(self.run_tool("query_transactions", keyword="KOPI").counted, 2)
        income = self.run_tool("query_transactions", kind="income")
        self.assertEqual((income.data["income"]["amount"], income.counted), (5_000_000, 1))
        self.assertIn("income_change", income.data)

    def test_no_data(self):
        result = self.run_tool("query_transactions", month="2026-10")
        self.assertEqual(result.counted, 0)
        self.assertEqual(result.cards, [])
        self.assertIn("No transactions", result.data["note"])


class SummaryAndBudgetTests(ToolCase):
    def test_monthly_summary(self):
        self.limit(self.food, 5_000_000)
        self.add(1_200_000)
        self.add(10_000_000, cat=self.salary)
        result = self.run_tool("get_monthly_summary", month="2026-11")
        self.assertEqual(result.data["remaining"]["amount"], 3_800_000)
        self.assertEqual(result.data["top_categories"], [{"category": "Food & drinks", "spent": "Rp1.200.000"}])
        self.assertEqual(result.counted, 2)

    def test_budget_question(self):
        from finance.budgets import month_budget

        self.limit(self.food, 5_000_000)
        self.limit(self.shopping, 2_700_000)
        self.add(5_808_490)
        result = self.run_tool("check_budget")
        self.assertEqual(result.data["remaining"]["text"], "Rp1.891.510")
        self.assertEqual(result.data["remaining"]["amount"], month_budget(self.user, 2026, 11, TODAY).remaining)
        self.assertEqual(result.data["days_left"], 16)
        self.assertEqual(result.data["per_day"]["amount"], 1_891_510 // 16)

    def test_one_category(self):
        self.limit(self.food, 2_000_000)
        self.add(1_500_000)
        result = self.run_tool("check_budget", category="Food & drinks")
        self.assertEqual((result.data["limit"]["amount"], result.data["spent"]["amount"], result.data["remaining"]["amount"]),
                         (2_000_000, 1_500_000, 500_000))
        self.assertEqual(result.data["percent_used"], 75)
        self.assertFalse(self.run_tool("check_budget", category="Transport").data["has_limit"])
        self.assertIn("error", self.run_tool("check_budget", category="Salary").data)  # income, not a budget category

    def test_month_without_a_plan(self):
        result = self.run_tool("check_budget", month="2026-10")
        self.assertFalse(result.data["has_monthly_plan"])
        self.assertEqual(result.cards, [])


class GoalProgressTests(ToolCase):
    def setUp(self):
        super().setUp()
        self.laptop = SavingsGoal.objects.create(user=self.user, name="New laptop", target=15_000_000,
                                                 start_date=date(2026, 9, 1), deadline=date(2027, 1, 31))
        GoalContribution.objects.create(user=self.user, goal=self.laptop, wallet=self.bca, kind="deposit", amount=2_250_000, date=date(2026, 9, 5))
        SavingsGoal.objects.create(user=self.user, name="Bali trip", target=6_000_000, start_date=date(2026, 9, 1))

    def test_goal_progress(self):
        from finance import goals

        result = self.run_tool("get_goal_progress", goal="new laptop")
        summary = goals.summarize(self.laptop, 2_250_000, TODAY)
        goal = result.data["goals"][0]
        self.assertEqual((goal["saved"]["amount"], goal["to_go"]["amount"], goal["status"]),
                         (2_250_000, summary.to_go, summary.status_label))
        self.assertEqual(goal["per_month"]["amount"], summary.per_month)

    def test_all_goals_and_unknown(self):
        self.assertEqual(len(self.run_tool("get_goal_progress").data["goals"]), 2)
        self.assertIn("error", self.run_tool("get_goal_progress", goal="Car").data)


class AddTransactionTests(ToolCase):
    def draft(self, **overrides):
        args = {"description": "Bakmi GM", "amount": 45_000, "category": "Food & drinks", "wallet": "GoPay", "date": "2026-11-15"}
        return self.run_tool("add_transaction", **{**args, **overrides})

    def test_valid_draft_is_not_saved(self):
        result = self.draft()
        card = result.cards[0]
        self.assertEqual((card["type"], card["state"]), ("draft", "pending"))
        self.assertEqual(card["fields"]["amount"], 45_000)
        self.assertEqual(card["fields"]["wallet_id"], self.gopay.pk)
        self.assertEqual(card["fields"]["kind"], "expense")
        self.assertIn("Not saved", result.data["status"])
        self.assertEqual(Transaction.objects.count(), 0)

    def test_date_defaults_to_today(self):
        result = self.run_tool("add_transaction", description="Grab", amount=18_000, category="Transport", wallet="GoPay")
        self.assertEqual(result.cards[0]["fields"]["date"], "2026-11-15")

    def test_invalid_drafts(self):
        cases = {
            "unknown wallet": {"wallet": "Dana"},
            "zero amount": {"amount": 0},
            "future date": {"date": "2030-01-01"},
        }
        for name, overrides in cases.items():
            with self.subTest(name):
                result = self.draft(**overrides)
                self.assertIn("error", result.data)
                self.assertEqual(result.cards, [])

    def test_archived_wallet_is_refused(self):
        self.gopay.archive()
        self.assertIn("no active wallet called 'GoPay'", self.draft().data["error"])


class ToolPrivacyTests(ToolCase):
    def test_another_users_data(self):
        other = make_user(email="other@example.com", name="Other")
        wallet = Wallet.objects.create(user=other, name="Other BCA")
        self.add(9_000_000, user=other, wallet=wallet)
        self.limit(self.food, 9_000_000, user=other)
        SavingsGoal.objects.create(user=other, name="Their car", target=5_000_000, start_date=TODAY)
        self.add(50_000)

        food = self.run_tool("query_transactions", category="Food & drinks")
        self.assertEqual((food.data["expenses"]["amount"], food.counted), (50_000, 1))
        self.assertFalse(self.run_tool("check_budget").data["has_monthly_plan"])
        self.assertEqual(self.run_tool("get_goal_progress").data["goals"], [])
        self.assertIn("error", self.run_tool("get_goal_progress", goal="Their car").data)
        self.assertIn("error", self.run_tool("query_transactions", wallet="Other BCA").data)
        self.assertIn("error", self.run_tool("add_transaction", description="x", amount=1_000, category="Food & drinks", wallet="Other BCA").data)
