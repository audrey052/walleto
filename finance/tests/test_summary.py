"""Dashboard spec: the monthly summary service in finance/summary.py."""

from datetime import date

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from finance import summary
from finance.models import Budget, Category, GoalContribution, SavingsGoal, Transaction, Transfer, Wallet
from finance.periods import Period
from finance.summary import Projection, change_tenths, month_summary, projection

from .test_views import make_user

TODAY = date(2026, 11, 15)


def category(name):
    return Category.objects.get(user=None, name=name)


class SummaryFixtures:
    def setUp(self):
        self.user = make_user()
        self.bca = Wallet.objects.create(user=self.user, name="BCA", initial_balance=50_000_000)
        self.gopay = Wallet.objects.create(user=self.user, name="GoPay", type="ewallet")
        self.food = category("Food & drinks")
        self.shopping = category("Shopping")
        self.transport = category("Transport")
        self.salary = category("Salary")

    def add(self, amount, cat=None, day=date(2026, 11, 10), user=None, wallet=None, text="Test"):
        return Transaction.objects.create(
            user=user or self.user, wallet=wallet or self.bca, category=cat or self.food,
            amount=amount, date=day, description=text,
        )

    def limit(self, cat, amount, month=date(2026, 11, 1), user=None):
        return Budget.objects.create(user=user or self.user, category=cat, month=month, limit=amount)


class ChangeTests(SimpleTestCase):
    def test_change_against_last_month(self):
        # 5.847.500 vs 5.300.000 is +10.33%, shown as 10.3%.
        self.assertEqual(change_tenths(5_847_500, 5_300_000), 103)

    def test_down_and_half_up(self):
        self.assertEqual(change_tenths(900_000, 1_000_000), -100)
        self.assertEqual(change_tenths(1_000_500, 1_000_000), 1)  # 0.05% rounds to 0.1%

    def test_nothing_last_month(self):
        self.assertIsNone(change_tenths(4_000_000, 0))


class ProjectionTests(SimpleTestCase):
    def project(self, today, plan, expense, year=2026, month=11, has_plan=True):
        return projection(year=year, month=month, today=today, plan=plan, expense=expense, has_plan=has_plan)

    def test_days_of_meals(self):
        # Rp2.000.000 left at Rp50.000 a day is 40 days of meals.
        self.assertEqual(
            self.project(date(2026, 11, 15), 8_000_000, 6_000_000),
            Projection(summary.MEAL_DAYS, days=40),
        )

    def test_days_are_rounded_down(self):
        self.assertEqual(self.project(TODAY, 8_000_000, 7_920_000), Projection(summary.MEAL_DAYS, days=1))
        self.assertEqual(self.project(TODAY, 8_000_000, 7_960_000), Projection(summary.MEAL_DAYS, days=0))

    def test_no_spending_yet(self):
        self.assertEqual(self.project(TODAY, 8_000_000, 0), Projection(summary.MEAL_DAYS, days=160))

    def test_over_the_plan(self):
        self.assertEqual(
            self.project(TODAY, 8_000_000, 8_250_000),
            Projection(summary.OVER, amount=250_000),
        )

    def test_past_month(self):
        self.assertEqual(
            self.project(TODAY, 6_000_000, 5_700_000, month=10),
            Projection(summary.ENDED_LEFT, amount=300_000),
        )
        self.assertEqual(
            self.project(TODAY, 6_000_000, 6_100_000, month=10),
            Projection(summary.ENDED_OVER, amount=100_000),
        )

    def test_no_plan_has_no_line(self):
        self.assertIsNone(self.project(TODAY, 0, 500_000, has_plan=False))


class ChartHelperTests(SimpleTestCase):
    def test_nice_top(self):
        self.assertEqual(summary.nice_top(99_500), 100_000)
        self.assertEqual(summary.nice_top(300_000), 400_000)
        self.assertEqual(summary.nice_top(730_000), 800_000)
        self.assertEqual(summary.nice_top(0), 4)

    def test_empty_month_has_a_readable_scale(self):
        chart = summary.daily_chart([(date(2025, 1, d), 0) for d in range(1, 32)], None, today=TODAY)
        self.assertEqual(chart.y_labels, ["100k", "75k", "50k", "25k", "0"])

    def test_short_amount(self):
        self.assertEqual(summary.short_amount(0), "0")
        self.assertEqual(summary.short_amount(750_000), "750k")
        self.assertEqual(summary.short_amount(1_000_000), "1M")
        self.assertEqual(summary.short_amount(1_500_000), "1.5M")


class MonthSummaryTests(SummaryFixtures, TestCase):
    def test_plan_and_spending(self):
        self.limit(self.food, 5_000_000)
        self.limit(self.shopping, 3_000_000)
        self.add(5_847_500)
        result = month_summary(self.user, 2026, 11, TODAY)
        self.assertTrue(result.has_plan)
        self.assertEqual(result.plan, 8_000_000)
        self.assertEqual(result.plan_spent, 5_847_500)
        self.assertEqual(result.remaining, 2_152_500)
        self.assertEqual(result.expense, 5_847_500)

    def test_change_against_last_month(self):
        self.add(5_847_500)
        self.add(5_300_000, day=date(2026, 10, 3))
        result = month_summary(self.user, 2026, 11, TODAY)
        self.assertEqual(result.prev_expense, 5_300_000)
        self.assertEqual(result.expense_change_tenths, 103)

    def test_nothing_last_month(self):
        self.add(10_000_000, cat=self.salary)
        result = month_summary(self.user, 2026, 11, TODAY)
        self.assertEqual(result.income, 10_000_000)
        self.assertIsNone(result.income_change_tenths)

    def test_only_this_month_and_the_month_before(self):
        self.add(2_000_000, day=date(2026, 9, 30))  # two months back: not counted
        self.add(1_000_000, day=date(2026, 10, 1))
        self.add(3_000_000, day=date(2026, 11, 30))
        result = month_summary(self.user, 2026, 11, TODAY)
        self.assertEqual((result.expense, result.prev_expense), (3_000_000, 1_000_000))

    def test_transfers_and_goal_moves_do_not_count(self):
        Transfer.objects.create(user=self.user, from_wallet=self.bca, to_wallet=self.gopay, amount=500_000, date=date(2026, 11, 3))
        goal = SavingsGoal.objects.create(user=self.user, name="Laptop", target=10_000_000, start_date=date(2026, 11, 1), deadline=date(2027, 6, 30))
        GoalContribution.objects.create(user=self.user, goal=goal, wallet=self.bca, amount=700_000, date=date(2026, 11, 4))
        result = month_summary(self.user, 2026, 11, TODAY)
        self.assertEqual((result.income, result.expense), (0, 0))

    def test_daily_bars(self):
        self.add(67_500, day=date(2026, 11, 12))
        self.add(32_000, day=date(2026, 11, 12))
        self.add(10_000_000, cat=self.salary, day=date(2026, 11, 12))  # income is not a bar
        result = month_summary(self.user, 2026, 11, TODAY)
        self.assertEqual(len(result.daily), 30)
        self.assertEqual(result.daily[11], (date(2026, 11, 12), 99_500))
        bar = result.chart.bars[11]
        self.assertEqual(bar.amount, 99_500)
        self.assertFalse(bar.is_future)
        self.assertTrue(result.chart.bars[14].is_today)
        self.assertTrue(result.chart.bars[15].is_future)

    def test_daily_budget_line(self):
        self.limit(self.food, 6_000_000)
        self.limit(self.shopping, 3_000_000)
        result = month_summary(self.user, 2026, 11, TODAY)
        self.assertEqual(result.daily_budget, 300_000)
        self.assertEqual(result.chart.top, 400_000)
        self.assertEqual(result.chart.budget_line, 75)

    def test_no_plan_no_budget_line(self):
        self.add(50_000)
        result = month_summary(self.user, 2026, 11, TODAY)
        self.assertFalse(result.has_plan)
        self.assertIsNone(result.daily_budget)
        self.assertIsNone(result.chart.budget_line)
        self.assertIsNone(result.projection)

    def test_ordered_by_spending(self):
        self.limit(self.food, 2_800_000)
        self.limit(self.shopping, 1_600_000)
        self.add(2_147_500)
        self.add(1_389_500, cat=self.shopping)
        self.add(150_000, cat=self.transport)  # no limit
        lines = month_summary(self.user, 2026, 11, TODAY).categories
        self.assertEqual([line.category for line in lines], [self.food, self.shopping, self.transport])
        self.assertEqual([line.percent for line in lines], [76, 86, None])
        self.assertEqual(lines[2].limit, None)
        self.assertEqual(lines[0].bar, 76)
        self.assertEqual(lines[2].bar, 150_000 * 100 // 2_147_500)

    def test_categories_without_spending_are_left_out(self):
        self.limit(self.food, 2_800_000)
        self.assertEqual(month_summary(self.user, 2026, 11, TODAY).categories, [])

    def test_only_the_users_own_data(self):
        other = make_user(email="other@example.com", name="Other")
        wallet = Wallet.objects.create(user=other, name="Other BCA")
        self.add(400_000, user=other, wallet=wallet)
        self.limit(self.food, 9_000_000, user=other)
        result = month_summary(self.user, 2026, 11, TODAY)
        self.assertEqual((result.expense, result.plan, result.categories), (0, 0, []))


class FiguresMatchTests(SummaryFixtures, TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        self.limit(self.food, 5_000_000)
        self.limit(self.shopping, 3_000_000)
        self.add(4_000_000)
        self.add(1_847_500, cat=self.shopping, wallet=self.gopay)
        self.add(12_000_000, cat=self.salary)
        self.add(250_000, cat=self.transport, day=date(2026, 11, 2))

    def test_same_numbers_as_transactions_and_budget(self):
        from finance.budgets import month_budget

        result = month_summary(self.user, 2026, 11, TODAY)
        page = self.client.get(reverse("finance:transactions"), {"month": "2026-11"})
        self.assertEqual(result.income, page.context["summary"]["income"])
        self.assertEqual(result.expense, page.context["summary"]["expense"])

        plan = month_budget(self.user, 2026, 11, TODAY)
        self.assertEqual(result.plan, plan.plan)
        self.assertEqual(result.remaining, plan.remaining)
        spent = {row.category: row.spent for row in plan.rows + plan.unbudgeted if row.spent}
        self.assertEqual({line.category: line.spent for line in result.categories}, spent)

    def test_fixed_query_count(self):
        # This and last month's totals, categories, limits, spent per category, daily.
        with self.assertNumQueries(5):
            month_summary(self.user, 2026, 11, TODAY)
        for day in range(1, 15):
            self.add(10_000, day=date(2026, 11, day))
        with self.assertNumQueries(5):
            month_summary(self.user, 2026, 11, TODAY)


class PeriodSummaryTests(SummaryFixtures, TestCase):
    """add-date-range: Home for a range of days (today is 15 Nov 2026)."""

    RANGE = Period(date(2026, 11, 1), date(2026, 11, 15))

    def test_change_against_the_previous_days(self):
        # 1-15 Nov (15 days) against 17-31 Oct.
        self.add(1_100_000, day=date(2026, 11, 3))
        self.add(1_000_000, day=date(2026, 10, 20))
        self.add(5_000_000, day=date(2026, 10, 16))  # just before the previous 15 days
        result = summary.period_summary(self.user, self.RANGE, TODAY)
        self.assertEqual((result.expense, result.prev_expense), (1_100_000, 1_000_000))
        self.assertEqual(result.expense_change_tenths, 100)
        self.assertEqual(result.compare_label, "vs. previous 15 days")

    def test_compare_labels(self):
        self.assertEqual(summary.period_summary(self.user, Period(TODAY, TODAY), TODAY).compare_label, "vs. previous day")
        self.assertEqual(month_summary(self.user, 2026, 11, TODAY).compare_label, "vs. last month")

    def test_range_bars(self):
        self.limit(self.food, 9_000_000)
        week = Period(date(2026, 11, 9), date(2026, 11, 15))
        result = summary.period_summary(self.user, week, TODAY)
        self.assertEqual([bar.day.day for bar in result.chart.bars], [9, 10, 11, 12, 13, 14, 15])
        self.assertIsNone(result.chart.budget_line)
        self.assertTrue(result.chart.bars[-1].is_today)

    def test_share_in_a_range(self):
        self.limit(self.food, 2_000_000)
        self.add(600_000)
        self.add(400_000, cat=self.transport)
        lines = summary.period_summary(self.user, self.RANGE, TODAY).categories
        self.assertEqual([(line.category, line.share, line.percent) for line in lines], [(self.food, 60, None), (self.transport, 40, None)])

    def test_a_range_has_no_plan(self):
        self.limit(self.food, 8_000_000)
        self.add(500_000)
        result = summary.period_summary(self.user, self.RANGE, TODAY)
        self.assertFalse(result.is_month)
        self.assertFalse(result.has_plan)
        self.assertIsNone(result.projection)
        self.assertIsNone(result.daily_budget)

    def test_only_the_users_own_data_in_a_range(self):
        other = make_user(email="other@example.com", name="Other")
        wallet = Wallet.objects.create(user=other, name="Other BCA")
        self.add(400_000, user=other, wallet=wallet)
        result = summary.period_summary(self.user, self.RANGE, TODAY)
        self.assertEqual((result.expense, result.categories), (0, []))
        self.assertEqual(sum(amount for _, amount in result.daily), 0)

    def test_fixed_query_counts(self):
        self.add(10_000)
        with self.assertNumQueries(5):
            summary.period_summary(self.user, Period.for_month(2026, 11), TODAY)
        with self.assertNumQueries(3):
            summary.period_summary(self.user, self.RANGE, TODAY)
