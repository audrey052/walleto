"""Dashboard spec: the page and its month picker."""

from datetime import date, datetime
from datetime import timezone as dt_timezone
from unittest import mock

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from finance.models import Wallet

from .test_summary import SummaryFixtures
from .test_views import make_user

# 15 Nov 2026, 10:00 in Jakarta.
NOW = datetime(2026, 11, 15, 3, 0, tzinfo=dt_timezone.utc)


@mock.patch("django.utils.timezone.now", return_value=NOW)
class DashboardPageTests(SummaryFixtures, TestCase):
    url = reverse("core:dashboard")

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def get(self, **params):
        return self.client.get(self.url, params)

    def test_sign_in_lands_on_the_dashboard(self, _now):
        self.client.logout()
        response = self.client.post(reverse("accounts:login"), {"username": "aditya@example.com", "password": "quiet-ledger-2026"})
        self.assertRedirects(response, self.url)

    def test_plan_and_spending(self, _now):
        self.limit(self.food, 5_000_000)
        self.limit(self.shopping, 3_000_000)
        self.add(5_847_500)
        response = self.get()
        self.assertContains(response, "Remaining this month")
        self.assertContains(response, "<h1>Home</h1>", html=True)
        self.assertContains(response, "<title>Home · Walleto</title>", html=True)
        self.assertContains(response, '<span class="currency">Rp</span>2.152.500', html=False)
        self.assertContains(response, "Rp5.847.500</strong> of Rp8.000.000 planned", html=False)
        # Rp2.152.500 left at Rp50.000 a day: 43 days of meals.
        self.assertContains(response, "Enough for 43 days of meals at Rp50.000 a day")
        self.assertContains(response, "Total income")
        self.assertContains(response, "Total expenses")
        self.assertNotContains(response, 'class="sparkline"')

    def test_less_than_a_day_of_meals(self, _now):
        self.limit(self.food, 1_000_000)
        self.add(980_000)
        self.assertContains(self.get(), "Not enough for a day of meals at Rp50.000")

    def test_one_day_of_meals(self, _now):
        self.limit(self.food, 1_000_000)
        self.add(940_000)
        self.assertContains(self.get(), "Enough for 1 day of meals at Rp50.000 a day")

    def test_over_the_plan(self, _now):
        self.limit(self.food, 8_000_000)
        self.add(8_250_000)
        response = self.get()
        self.assertContains(response, "Over your plan by Rp250.000")
        self.assertContains(response, "amount-display text-clay")

    def test_no_plan(self, _now):
        self.add(50_000)
        response = self.get(month="2026-10")
        self.assertContains(response, "October has no monthly plan")
        self.assertNotContains(response, "Remaining this month")
        self.assertContains(response, f'href="{reverse("finance:budget")}?month=2026-10"')
        self.assertContains(response, "Set a monthly plan")
        self.assertNotContains(response, "data-projection")
        self.assertNotContains(response, "data-daily-budget")

    def test_change_and_dash(self, _now):
        self.add(5_847_500)
        self.add(5_300_000, day=date(2026, 10, 3))
        self.add(10_000_000, cat=self.salary)
        content = self.get().content.decode()
        self.assertIn("10.3%", content)
        self.assertIn("—", content)  # no income in October
        self.assertEqual(content.count("vs. last month"), 2)

    def test_earlier_month(self, _now):
        self.limit(self.food, 6_000_000, month=date(2026, 10, 1))
        self.add(5_700_000, day=date(2026, 10, 3))
        self.add(1_000_000)
        response = self.get(month="2026-10")
        self.assertContains(response, "October 2026")
        self.assertContains(response, "Ended October with Rp300.000 left")
        self.assertEqual(response.context["s"].expense, 5_700_000)
        # October is complete: 31 bars and no future days.
        self.assertContains(response, 'class="day-bar ', count=31)
        self.assertContains(response, f'href="{self.url}?month=2026-11"')

    def test_future_month(self, _now):
        response = self.get(month="2026-12")
        self.assertEqual((response.context["s"].year, response.context["s"].month), (2026, 11))
        self.assertContains(response, "November 2026")
        self.assertNotContains(response, 'aria-label="Next month"')

    def test_daily_bars_and_budget_line(self, _now):
        self.limit(self.food, 9_000_000)
        self.add(67_500, day=date(2026, 11, 12))
        self.add(32_000, day=date(2026, 11, 12))
        response = self.get()
        self.assertContains(response, 'aria-label="12 Nov: Rp99.500"')
        self.assertContains(response, "<span>Rp300.000</span>", html=False)
        self.assertContains(response, "Daily budget")
        # 15 bars up to today, today marked; 15 empty days after.
        self.assertContains(response, 'class="day-bar ', count=15)
        self.assertContains(response, 'class="day-bar is-today"', count=1)

    def test_open_a_category(self, _now):
        self.limit(self.food, 2_800_000)
        self.limit(self.shopping, 1_600_000)
        self.add(2_147_500)
        self.add(1_389_500, cat=self.shopping)
        content = self.get().content.decode()
        self.assertLess(content.index(">Food &amp; drinks<"), content.index(">Shopping<"))
        self.assertIn(">\n                      76%", content.replace("\r", ""))
        self.assertIn(f'href="{reverse("finance:transactions")}?month=2026-11&amp;category={self.shopping.pk}"', content)
        self.assertIn("Percentage of each category's budget", content)

    def test_no_limit(self, _now):
        self.limit(self.food, 2_800_000)
        self.add(150_000, cat=self.transport)
        self.assertContains(self.get(), "No limit")

    def test_no_expenses(self, _now):
        self.assertContains(self.get(), "No expenses in November yet.")

    def test_another_users_spending(self, _now):
        other = make_user(email="other@example.com", name="Other")
        wallet = Wallet.objects.create(user=other, name="Other BCA")
        self.add(400_000, user=other, wallet=wallet, text="Not mine")
        self.limit(self.food, 9_000_000, user=other)
        response = self.get()
        self.assertEqual(response.context["s"].expense, 0)
        self.assertFalse(response.context["s"].has_plan)
        self.assertNotContains(response, "Rp400.000")

    def test_htmx_month_switch_attributes(self, _now):
        content = self.get().content.decode()
        self.assertIn('id="dashboard"', content)
        self.assertIn(f'hx-get="{self.url}?month=2026-10"', content)
        self.assertIn('hx-select="#dashboard"', content)
        self.assertIn('hx-push-url="true"', content)

    def test_requires_sign_in(self, _now):
        self.client.logout()
        self.assertEqual(self.get().status_code, 302)


class AxisLabelTests(SimpleTestCase):
    def bars(self, days, today):
        from finance.summary import DayBar
        return [DayBar(date(2026, 11, d), 0, 0, d == today, d > today) for d in range(1, days + 1)]

    def test_fixed_days_last_day_and_today(self):
        from finance.views_dashboard import axis_labels
        texts = [label["text"] for label in axis_labels(self.bars(30, 14))]
        self.assertEqual([t for t in texts if t], ["01", "05", "10", "14", "20", "25", "30"])

    def test_day_next_to_today_is_left_out(self):
        from finance.views_dashboard import axis_labels
        texts = [label["text"] for label in axis_labels(self.bars(30, 24))]
        self.assertEqual([t for t in texts if t], ["01", "05", "10", "15", "20", "24", "30"])
