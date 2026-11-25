"""assistant spec: rest-of-month plans and report figures, without any model."""

from datetime import date

from django.test import TestCase

from assistant import planning
from finance.budgets import month_budget
from finance.models import Budget, GoalContribution, SavingsGoal, Wallet
from finance.summary import period_summary
from finance.periods import Period
from finance.tests.test_summary import SummaryFixtures
from finance.tests.test_views import make_user

TODAY = date(2026, 11, 25)  # 6 days left including today


class PlanFactsTests(SummaryFixtures, TestCase):
    def setUp(self):
        super().setUp()
        self.limit(self.food, 1_600_000)
        self.limit(self.transport, 500_000)
        self.add(1_405_500, day=date(2026, 11, 10))
        self.add(455_500, cat=self.transport, day=date(2026, 11, 12))
        self.add(80_000, cat=self.shopping, day=date(2026, 11, 12))  # no limit: not in the plan

    def test_facts(self):
        facts = planning.plan_facts(self.user, TODAY)
        self.assertEqual((facts.plan, facts.days_left), (2_100_000, 6))
        food = next(r for r in facts.rows if r.name == "Food & drinks")
        self.assertEqual((food.limit, food.spent, food.left, food.daily_average), (1_600_000, 1_405_500, 194_500, 56_220))
        self.assertEqual(facts.left, 194_500 + 44_500)
        self.assertTrue(facts.can_plan)

    def test_no_plan_or_nothing_left(self):
        other = make_user(email="o@example.com", name="O")
        self.assertFalse(planning.plan_facts(other, TODAY).can_plan)
        self.add(500_000, day=date(2026, 11, 20))  # food now over by more than what transport has left
        self.assertFalse(planning.plan_facts(self.user, TODAY).can_plan)

    def check(self, **amounts):
        return planning.check_plan(planning.plan_facts(self.user, TODAY), amounts)

    def test_valid_plan(self):
        rows, error = planning.check_plan(planning.plan_facts(self.user, TODAY), {"Food & drinks": 150_000, "transport": 89_000})
        self.assertIsNone(error)
        food = next(r for r in rows if r["name"] == "Food & drinks")
        self.assertEqual((food["amount"], food["per_day"]), (150_000, 25_000))

    def test_amounts_do_not_add_up(self):
        rows, error = planning.check_plan(planning.plan_facts(self.user, TODAY), {"Food & drinks": 200_000, "Transport": 100_000})
        self.assertIsNone(rows)
        self.assertIn("Rp61.000 over", error)
        self.assertIn("exactly to Rp239.000", error)

    def test_unknown_missing_negative_and_text(self):
        facts = planning.plan_facts(self.user, TODAY)
        self.assertIn("not one of the limited categories", planning.check_plan(facts, {"Shopping": 239_000})[1])
        self.assertIn("missing: Transport", planning.check_plan(facts, {"Food & drinks": 239_000})[1])
        self.assertIn("cannot be negative", planning.check_plan(facts, {"Food & drinks": 250_000, "Transport": -11_000})[1])
        self.assertIn("whole number", planning.check_plan(facts, {"Food & drinks": "a lot", "Transport": 0})[1])

    def test_limit_under_minimum(self):
        Budget.objects.create(user=self.user, category=self.salary.__class__.objects.get(user=None, name="Health"), month=date(2026, 11, 1), limit=200_000)
        facts = planning.plan_facts(self.user, TODAY)
        rows, error = planning.check_plan(facts, {"Food & drinks": 239_000, "Transport": 200_000, "Health": 0})
        self.assertIn("Health would end with a limit under Rp1.000", error)

    def test_another_users_limits_never_counted(self):
        other = make_user(email="o@example.com", name="O")
        Budget.objects.create(user=other, category=self.food, month=date(2026, 11, 1), limit=9_000_000)
        self.assertEqual(planning.plan_facts(self.user, TODAY).plan, 2_100_000)


class ApplyPlanTests(SummaryFixtures, TestCase):
    def setUp(self):
        super().setUp()
        self.limit(self.food, 1_600_000)
        self.limit(self.transport, 500_000)
        self.limit(self.food, 999_000, month=date(2026, 10, 1))
        self.add(1_405_500, day=date(2026, 11, 10))
        self.add(455_500, cat=self.transport, day=date(2026, 11, 12))

    def test_plan_total_unchanged_and_other_months_untouched(self):
        rows, _ = planning.check_plan(planning.plan_facts(self.user, TODAY), {"Food & drinks": 150_000, "Transport": 89_000})
        total = planning.apply_plan(self.user, rows, TODAY)
        self.assertEqual(total, 2_100_000)
        limits = dict(Budget.objects.filter(user=self.user, month=date(2026, 11, 1)).values_list("category__name", "limit"))
        self.assertEqual(limits, {"Food & drinks": 1_555_500, "Transport": 544_500})
        self.assertEqual(Budget.objects.get(user=self.user, month=date(2026, 10, 1)).limit, 999_000)

    def test_all_or_nothing(self):
        rows, _ = planning.check_plan(planning.plan_facts(self.user, TODAY), {"Food & drinks": 150_000, "Transport": 89_000})
        Budget.objects.filter(user=self.user, category=self.transport).delete()
        with self.assertRaises(ValueError):
            planning.apply_plan(self.user, rows, TODAY)
        self.assertEqual(Budget.objects.get(user=self.user, category=self.food, month=date(2026, 11, 1)).limit, 1_600_000)


class ReportFiguresTests(SummaryFixtures, TestCase):
    def setUp(self):
        super().setUp()
        october = date(2026, 10, 1)
        self.limit(self.food, 2_000_000, month=october)
        self.limit(self.shopping, 1_000_000, month=october)
        for n in range(12):
            self.add(10_000 * (n + 1), day=date(2026, 10, n + 1), text=f"Food {n}")
        self.add(400_000, cat=self.shopping, day=date(2026, 10, 15), text="Shoes")
        self.add(90_000, cat=self.transport, day=date(2026, 10, 16), text="Grab")  # no limit
        self.add(12_000_000, cat=self.salary, day=date(2026, 10, 1))
        goal = SavingsGoal.objects.create(user=self.user, name="Laptop", target=10_000_000, start_date=date(2026, 9, 1), deadline=date(2027, 6, 30))
        GoalContribution.objects.create(user=self.user, goal=goal, wallet=self.bca, kind="deposit", amount=2_000_000, date=date(2026, 10, 2))

    def test_figures_match_home_and_budget(self):
        figures = planning.report_figures(self.user, 2026, 10, TODAY)
        home = period_summary(self.user, Period.for_month(2026, 10), TODAY)
        budget = month_budget(self.user, 2026, 10, TODAY)
        self.assertEqual((figures["income"], figures["expenses"]), (home.income, home.expense))
        self.assertEqual((figures["plan"], figures["remaining"]), (budget.plan, budget.remaining))
        food = next(c for c in figures["categories"] if c["name"] == "Food & drinks")
        self.assertEqual((food["spent"], food["limit"], food["percent"]), (780_000, 2_000_000, 39))
        transport = next(c for c in figures["categories"] if c["name"] == "Transport")
        self.assertIsNone(transport["limit"])
        self.assertEqual(figures["label"], "October 2026")

    def test_largest_expenses_in_order(self):
        largest = planning.report_figures(self.user, 2026, 10, TODAY)["largest"]
        self.assertEqual(len(largest), 10)
        self.assertEqual([t["amount"] for t in largest[:3]], [400_000, 120_000, 110_000])

    def test_goals(self):
        goal = planning.report_figures(self.user, 2026, 10, TODAY)["goals"][0]
        self.assertEqual((goal["name"], goal["saved"], goal["target"], goal["percent"]), ("Laptop", 2_000_000, 10_000_000, 20))

    def test_summary_check(self):
        figures = planning.report_figures(self.user, 2026, 10, TODAY)
        self.assertTrue(planning.check_summary("You spent Rp1.270.000 and kept Food & drinks at 39%.", figures))
        self.assertFalse(planning.check_summary("You spent Rp999.999 on fun.", figures))
        self.assertFalse(planning.check_summary("Food reached 77%.", figures))
        self.assertFalse(planning.check_summary("", figures))
        self.assertIn("Rp1.270.000", planning.code_summary(figures))

    def test_another_users_data_never_included(self):
        other = make_user(email="o@example.com", name="O")
        wallet = Wallet.objects.create(user=other, name="Other BCA")
        self.add(5_000_000, user=other, wallet=wallet, day=date(2026, 10, 3), text="Not mine")
        figures = planning.report_figures(self.user, 2026, 10, TODAY)
        self.assertNotIn("Not mine", [t["description"] for t in figures["largest"]])
        self.assertEqual(figures["expenses"], 1_270_000)

    def test_pdf_and_html(self):
        from assistant import report

        figures = planning.report_figures(self.user, 2026, 10, TODAY)
        html = report.report_html(figures, "A calm month.")
        self.assertIn("October 2026", html)
        self.assertIn("Rp1.270.000", html)
        self.assertIn("A calm month.", html)
        self.assertIn("Laptop", html)
        pdf = report.report_pdf(figures, "A calm month.")
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 1500)
