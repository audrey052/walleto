from datetime import datetime, timezone as dt_timezone
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.template import Context, Template
from django.test import TestCase, override_settings
from django.urls import reverse

from core.templatetags.money import amount, rupiah, rupiah_signed

User = get_user_model()


class RupiahFormatTests(TestCase):
    """Scenarios from the money-format spec."""

    def test_typical_amount(self):
        self.assertEqual(rupiah(847500), "Rp847.500")

    def test_large_amount(self):
        self.assertEqual(rupiah(12500000), "Rp12.500.000")

    def test_zero(self):
        self.assertEqual(rupiah(0), "Rp0")

    def test_negative_balance_uses_unicode_minus(self):
        self.assertEqual(rupiah(-150000), "−Rp150.000")

    def test_expense_row(self):
        self.assertEqual(rupiah_signed(67500, "expense"), "−Rp67.500")

    def test_income_row(self):
        self.assertEqual(rupiah_signed(12500000, "income"), "+Rp12.500.000")

    def test_decimal_and_string_inputs(self):
        self.assertEqual(rupiah(Decimal("847500.00")), "Rp847.500")
        self.assertEqual(rupiah("1000"), "Rp1.000")

    def test_amount_tag_markup(self):
        html = amount(12500000, kind="income")
        self.assertIn("amount-income", html)
        self.assertIn('<span class="currency">Rp</span>12.500.000', html)
        self.assertTrue(html.startswith('<span class="amount amount-income">+'))

    def test_filters_in_templates(self):
        rendered = Template("{% load money %}{{ v|rupiah }}").render(Context({"v": 847500}))
        self.assertEqual(rendered, "Rp847.500")


class AppShellTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="aditya@example.com", password="quiet-ledger-2026", full_name="Aditya Ramadhan"
        )
        self.client.force_login(self.user)

    def test_sidebar_lists_six_sections_and_marks_one_active(self):
        response = self.client.get(reverse("finance:wallets"))
        content = response.content.decode()
        for title in ["Home", "Transactions", "Wallets", "Budget", "Savings goals", "Assistant"]:
            self.assertIn(title, content)
        # Sidebar and bottom navigation each mark exactly one item as current.
        self.assertEqual(content.count('aria-current="page"'), 2)
        self.assertEqual(response.context["active_section"]["key"], "wallets")

    def test_home_is_dashboard(self):
        response = self.client.get("/")
        self.assertContains(response, "Your money this month at a glance.")

    def test_profile_shows_initials_name_and_email(self):
        response = self.client.get(reverse("core:dashboard"))
        self.assertContains(response, ">AR<")
        self.assertContains(response, "Aditya Ramadhan")
        self.assertContains(response, "aditya@example.com")

    def test_today_follows_jakarta_time_and_is_not_shown(self):
        # 23:30 UTC on 14 Nov is already 15 Nov in Jakarta (UTC+7). The shell no longer prints the date.
        fixed = datetime(2026, 11, 14, 23, 30, tzinfo=dt_timezone.utc)
        with mock.patch("django.utils.timezone.now", return_value=fixed):
            response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.context["today"].isoformat(), "2026-11-15")
        self.assertNotContains(response, "Sunday, 15 Nov 2026")


class StyleguideTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(
            email="dev@example.com", password="quiet-ledger-2026", full_name="Dev"
        )
        self.client.force_login(user)

    @override_settings(DEBUG=True)
    def test_available_in_development(self):
        response = self.client.get(reverse("core:styleguide"))
        self.assertEqual(response.status_code, 200)
        for text in ["Add transaction", "Food &amp; drinks", "progressbar", "<dialog", "No transactions yet"]:
            self.assertContains(response, text)

    @override_settings(DEBUG=False)
    def test_not_found_in_production(self):
        response = self.client.get(reverse("core:styleguide"))
        self.assertEqual(response.status_code, 404)


class CopyrightTests(TestCase):
    def test_copyright_on_pages_and_sign_in(self):
        from django.utils import timezone

        year = timezone.localdate().year
        user = get_user_model().objects.create_user(email="c@example.com", password="quiet-ledger-2026", full_name="C D")
        self.assertContains(self.client.get(reverse("accounts:login")), f"© {year} Walleto")
        self.client.force_login(user)
        # Once, in the page footer (not in the sidebar).
        self.assertContains(self.client.get(reverse("finance:wallets")), f'<footer class="app-footer">© {year} Walleto. All rights reserved.</footer>', count=1, html=True)
        # The Assistant has it too, under the chat.
        self.assertContains(self.client.get(reverse("core:assistant")), f"© {year} Walleto", count=1)
