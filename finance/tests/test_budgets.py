"""Budgets spec: model constraints and the calculations in finance/budgets.py."""

from datetime import date

from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase

from finance import budgets
from finance.models import Budget, Category, Transaction, Transfer, Wallet

from .test_views import make_user

NOV = (2026, 11)
TODAY = date(2026, 11, 17)


def category(name):
    return Category.objects.get(user=None, name=name)


class BudgetFixtures:
    def setUp(self):
        self.user = make_user()
        self.wallet = Wallet.objects.create(user=self.user, name="BCA", initial_balance=50_000_000)
        self.food = category("Food & drinks")
        self.transport = category("Transport")
        self.health = category("Health")

    def spend(self, amount, cat=None, day=date(2026, 11, 10), user=None, wallet=None):
        return Transaction.objects.create(
            user=user or self.user, wallet=wallet or self.wallet, category=cat or self.food,
            amount=amount, date=day, description="Test",
        )

    def limit(self, cat, amount, month=date(2026, 11, 1), user=None):
        return Budget.objects.create(user=user or self.user, category=cat, month=month, limit=amount)


class BudgetModelTests(BudgetFixtures, TestCase):
    def test_month_is_normalised_to_first_day(self):
        budget = self.limit(self.food, 3_000_000, month=date(2026, 11, 17))
        self.assertEqual(budget.month, date(2026, 11, 1))

    def test_one_limit_per_category_and_month(self):
        self.limit(self.food, 3_000_000)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.limit(self.food, 2_000_000)

    def test_limit_minimum(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.limit(self.food, 999)

    def test_default_shares_add_up_to_100(self):
        shares = Category.objects.filter(user=None, kind="expense").values_list("budget_share", flat=True)
        self.assertEqual(sum(shares), 100)
        self.assertEqual(self.food.budget_share, 30)


class DistributeTests(SimpleTestCase):
    DEFAULTS = {"food": 30, "shop": 15, "transport": 15, "bills": 15, "fun": 10, "other": 10, "health": 5}

    def test_first_split(self):
        parts = budgets.distribute(8_000_000, self.DEFAULTS)
        self.assertEqual(parts["food"], 2_400_000)
        self.assertEqual(sum(parts.values()), 8_000_000)

    def test_parts_add_up_exactly(self):
        for total in (8_000_001, 100_003, 1_234_567):
            with self.subTest(total=total):
                self.assertEqual(sum(budgets.distribute(total, self.DEFAULTS).values()), total)

    def test_rescale_is_proportional(self):
        parts = budgets.distribute(6_000_000, {"food": 3_000_000, "transport": 1_000_000})
        self.assertEqual(parts, {"food": 4_500_000, "transport": 1_500_000})

    def test_leftover_goes_to_largest_remainder_then_order(self):
        self.assertEqual(budgets.distribute(10, {"a": 1, "b": 1, "c": 1}), {"a": 4, "b": 3, "c": 3})


class StatusTests(SimpleTestCase):
    def test_statuses(self):
        cases = [
            (0, 1_600_000, "normal", 0),
            (1_359_999, 1_600_000, "normal", 84),
            (1_360_000, 1_600_000, "warning", 85),
            (1_600_000, 1_600_000, "warning", 100),
            (1_600_001, 1_600_000, "over", 100),
            (1_700_000, 1_600_000, "over", 106),
        ]
        for spent, limit, expected_status, expected_percent in cases:
            with self.subTest(spent=spent):
                self.assertEqual(budgets.status(spent, limit), expected_status)
                self.assertEqual(budgets.percent(spent, limit), expected_percent)

    def test_crossing(self):
        limit = 2_400_000
        self.assertEqual(budgets.crossing(2_000_000, 2_100_000, limit), "warning")
        self.assertEqual(budgets.crossing(2_350_000, 2_450_000, limit), "over")
        self.assertEqual(budgets.crossing(1_000_000, 2_500_000, limit), "over")
        self.assertIsNone(budgets.crossing(2_160_000, 2_184_000, limit))  # 90% -> 91%
        self.assertIsNone(budgets.crossing(2_500_000, 2_600_000, limit))  # already over
        self.assertIsNone(budgets.crossing(100_000, 200_000, limit))


class DaysLeftTests(SimpleTestCase):
    def test_days_left(self):
        self.assertEqual(budgets.days_left(2026, 11, date(2026, 11, 17)), 14)
        self.assertEqual(budgets.days_left(2026, 11, date(2026, 11, 30)), 1)
        self.assertEqual(budgets.days_left(2027, 2, date(2027, 2, 1)), 28)
        self.assertEqual(budgets.days_left(2028, 2, date(2028, 2, 1)), 29)
        self.assertEqual(budgets.days_left(2026, 10, date(2026, 11, 17)), 0)
        self.assertEqual(budgets.days_left(2026, 12, date(2026, 11, 17)), 31)

    def test_per_day(self):
        self.assertEqual(budgets.per_day(2_800_000, 14), 200_000)
        self.assertEqual(budgets.per_day(150_000, 1), 150_000)
        self.assertEqual(budgets.per_day(100, 3), 33)
        self.assertIsNone(budgets.per_day(0, 14))
        self.assertIsNone(budgets.per_day(-200_000, 14))
        self.assertIsNone(budgets.per_day(500_000, 0))


class MonthBudgetTests(BudgetFixtures, TestCase):
    def test_plan_is_sum_of_limits(self):
        self.limit(self.food, 3_000_000)
        self.limit(self.transport, 1_500_000)
        self.limit(self.health, 500_000)
        result = budgets.month_budget(self.user, *NOV, TODAY)
        self.assertEqual(result.plan, 5_000_000)
        self.assertTrue(result.has_plan)

    def test_spent_counts_only_this_months_expenses(self):
        self.limit(self.food, 3_000_000)
        self.spend(67_500)
        self.spend(24_000)
        self.spend(50_000, day=date(2026, 10, 31))
        salary = category("Salary")
        self.spend(12_500_000, cat=salary)
        jago = Wallet.objects.create(user=self.user, name="Jago")
        Transfer.objects.create(user=self.user, from_wallet=self.wallet, to_wallet=jago, amount=500_000, date=date(2026, 11, 5))
        result = budgets.month_budget(self.user, *NOV, TODAY)
        self.assertEqual(result.rows[0].spent, 91_500)
        self.assertEqual(result.spent, 91_500)

    def test_archived_wallets_count(self):
        self.limit(self.food, 3_000_000)
        cash = Wallet.objects.create(user=self.user, name="Cash", initial_balance=100_000)
        self.spend(40_000, wallet=cash)
        cash.archive()
        self.assertEqual(budgets.month_budget(self.user, *NOV, TODAY).rows[0].spent, 40_000)

    def test_unbudgeted_spending_counts_toward_plan(self):
        self.limit(self.food, 3_000_000)
        self.spend(300_000, cat=self.health)
        result = budgets.month_budget(self.user, *NOV, TODAY)
        self.assertEqual(result.spent, 300_000)
        health = next(row for row in result.unbudgeted if row.category == self.health)
        self.assertEqual(health.spent, 300_000)
        self.assertEqual(result.unbudgeted[0].category, self.health)

    def test_rows_sorted_by_spent(self):
        self.limit(self.food, 3_000_000)
        self.limit(self.transport, 1_000_000)
        self.spend(100_000)
        self.spend(400_000, cat=self.transport)
        names = [row.category.name for row in budgets.month_budget(self.user, *NOV, TODAY).rows]
        self.assertEqual(names, ["Transport", "Food & drinks"])

    def test_over_plan(self):
        self.limit(self.food, 8_000_000)
        self.spend(8_200_000)
        result = budgets.month_budget(self.user, *NOV, TODAY)
        self.assertEqual(result.remaining, -200_000)
        self.assertEqual(result.over_by, 200_000)
        self.assertEqual(result.status, "over")
        self.assertIsNone(result.per_day)

    def test_per_day_and_days_left(self):
        self.limit(self.food, 3_000_000)
        self.spend(200_000)
        result = budgets.month_budget(self.user, *NOV, TODAY)
        self.assertEqual(result.days_left, 14)
        self.assertEqual(result.per_day, 200_000)

    def test_no_plan(self):
        result = budgets.month_budget(self.user, *NOV, TODAY)
        self.assertFalse(result.has_plan)
        self.assertEqual(len(result.unbudgeted), 7)

    def test_plan_limits_first_split_and_rescale(self):
        first = budgets.plan_limits(self.user, *NOV, 8_000_000)
        self.assertEqual(first[self.food.pk], 2_400_000)
        self.assertEqual(sum(first.values()), 8_000_000)

        self.limit(self.food, 3_000_000)
        self.limit(self.transport, 1_000_000)
        rescaled = budgets.plan_limits(self.user, *NOV, 6_000_000)
        self.assertEqual(rescaled, {self.food.pk: 4_500_000, self.transport.pk: 1_500_000})


class MonthBudgetPrivacyTests(BudgetFixtures, TestCase):
    def test_other_users_data_never_counts(self):
        other = make_user("sari@example.com", "Sari Wulandari")
        other_wallet = Wallet.objects.create(user=other, name="BCA", initial_balance=10_000_000)
        self.limit(self.food, 9_000_000, user=other)
        self.spend(5_000_000, user=other, wallet=other_wallet)

        result = budgets.month_budget(self.user, *NOV, TODAY)
        self.assertFalse(result.has_plan)
        self.assertEqual(result.spent, 0)

        self.limit(self.food, 3_000_000)
        result = budgets.month_budget(self.user, *NOV, TODAY)
        self.assertEqual(result.plan, 3_000_000)
        self.assertEqual(result.rows[0].spent, 0)
