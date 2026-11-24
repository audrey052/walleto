"""period-picker spec: reading, cleaning and naming a period."""

from datetime import date

from django.test import SimpleTestCase, TestCase

from finance.periods import Period, parse_period

TODAY = date(2026, 11, 24)


def parse(**params):
    return parse_period(params, TODAY)


class ParsePeriodTests(SimpleTestCase):
    def test_old_month_link(self):
        self.assertEqual(parse(month="2026-10"), Period(date(2026, 10, 1), date(2026, 10, 31)))

    def test_nothing_is_the_current_month(self):
        self.assertEqual(parse(), Period(date(2026, 11, 1), date(2026, 11, 30)))

    def test_range_link(self):
        self.assertEqual(parse(**{"from": "2026-11-10", "to": "2026-11-24"}), Period(date(2026, 11, 10), date(2026, 11, 24)))

    def test_range_that_is_a_whole_month(self):
        period = parse(**{"from": "2026-10-01", "to": "2026-10-31"})
        self.assertTrue(period.is_month)
        self.assertEqual(period.query(), {"month": "2026-10"})

    def test_future_end_date(self):
        self.assertEqual(parse(**{"from": "2026-11-10", "to": "2026-12-10"}), Period(date(2026, 11, 10), TODAY))

    def test_the_current_month_is_still_a_whole_month(self):
        # 1-30 November with today the 24th: the month, not a range cut to today.
        self.assertTrue(parse(month="2026-11").is_month)

    def test_reversed_range(self):
        self.assertEqual(parse(**{"from": "2026-11-24", "to": "2026-11-10"}), Period(date(2026, 11, 10), TODAY))

    def test_too_long(self):
        period = parse(**{"from": "2026-01-01", "to": "2026-11-24"})
        self.assertEqual((period.start, period.days), (date(2026, 1, 1), 92))

    def test_unreadable_dates(self):
        self.assertEqual(parse(**{"from": "yesterday"}), Period(date(2026, 11, 1), date(2026, 11, 30)))
        self.assertEqual(parse(**{"from": "2026-11-10", "to": "2026-13-01"}).month, (2026, 11))

    def test_range_wins_over_month(self):
        period = parse(month="2026-10", **{"from": "2026-11-10", "to": "2026-11-24"})
        self.assertEqual(period, Period(date(2026, 11, 10), date(2026, 11, 24)))

    def test_whole_range_in_the_future(self):
        self.assertEqual(parse(**{"from": "2026-12-01", "to": "2026-12-05"}), Period(TODAY, TODAY))


class PeriodTests(SimpleTestCase):
    def test_labels(self):
        self.assertEqual(Period.for_month(2026, 11).label, "November 2026")
        self.assertEqual(Period(date(2026, 11, 10), date(2026, 11, 24)).label, "10 Nov – 24 Nov 2026")
        self.assertEqual(Period(date(2025, 12, 28), date(2026, 1, 3)).label, "28 Dec 2025 – 3 Jan 2026")
        self.assertEqual(Period(TODAY, TODAY).label, "24 Nov 2026")

    def test_query_and_slug(self):
        period = Period(date(2026, 11, 10), date(2026, 11, 24))
        self.assertEqual(period.query(), {"from": "2026-11-10", "to": "2026-11-24"})
        self.assertEqual(period.slug, "2026-11-10_2026-11-24")
        self.assertEqual(Period.for_month(2026, 11).slug, "2026-11")

    def test_previous_month(self):
        self.assertEqual(Period.for_month(2026, 11).previous(), Period.for_month(2026, 10))
        self.assertEqual(Period.for_month(2026, 1).previous(), Period.for_month(2025, 12))

    def test_previous_15_days(self):
        period = Period(date(2026, 11, 10), date(2026, 11, 24))
        self.assertEqual(period.days, 15)
        self.assertEqual(period.previous(), Period(date(2026, 10, 26), date(2026, 11, 9)))

    def test_previous_from_a_range(self):
        self.assertEqual(Period(date(2026, 11, 10), date(2026, 11, 24)).prev_month(), Period.for_month(2026, 10))

    def test_next_from_a_range_in_an_earlier_month(self):
        self.assertEqual(Period(date(2026, 10, 5), date(2026, 10, 12)).next_month(TODAY), Period.for_month(2026, 11))

    def test_no_next_month_after_today(self):
        self.assertIsNone(Period.for_month(2026, 11).next_month(TODAY))
        self.assertIsNone(Period(date(2026, 11, 10), date(2026, 11, 24)).next_month(TODAY))



class InPeriodQueryTests(TestCase):
    def test_both_end_days_are_included(self):
        from finance.models import Category, GoalContribution, SavingsGoal, Transaction, Transfer, Wallet

        from .test_views import make_user

        user = make_user()
        bca = Wallet.objects.create(user=user, name="BCA", initial_balance=5_000_000)
        gopay = Wallet.objects.create(user=user, name="GoPay", type="ewallet")
        food = Category.objects.get(user=None, name="Food & drinks")
        goal = SavingsGoal.objects.create(user=user, name="Laptop", target=1_000_000, start_date=date(2026, 11, 1), deadline=date(2027, 6, 30))
        for day in (9, 10, 24, 25):
            when = date(2026, 11, day)
            Transaction.objects.create(user=user, wallet=bca, category=food, amount=1_000, date=when, description="x")
            Transfer.objects.create(user=user, from_wallet=bca, to_wallet=gopay, amount=1_000, date=when)
            GoalContribution.objects.create(user=user, goal=goal, wallet=bca, amount=1_000, date=when)
        start, end = date(2026, 11, 10), date(2026, 11, 24)
        for model in (Transaction, Transfer, GoalContribution):
            days = sorted(r.date.day for r in model.objects.for_user(user).in_period(start, end))
            self.assertEqual(days, [10, 24], model.__name__)
            self.assertEqual(model.objects.for_user(user).in_month(2026, 11).count(), 4)
