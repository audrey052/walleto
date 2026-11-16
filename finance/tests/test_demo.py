from datetime import date, datetime, timezone as dt_timezone
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from finance.demo import DEMO_EMAIL, build_demo
from finance.models import Transaction, Transfer, Wallet

User = get_user_model()
TODAY = date(2026, 11, 16)


class DemoDataTests(TestCase):
    def test_shape_of_the_data(self):
        user = build_demo(TODAY)
        self.assertEqual(user.email, DEMO_EMAIL)
        self.assertFalse(user.has_usable_password())
        names = list(Wallet.objects.for_user(user).values_list("name", flat=True))
        self.assertEqual(names, ["BCA", "GoPay", "OVO", "Bank Jago", "Cash"])

        tx = Transaction.objects.filter(user=user)
        salaries = list(tx.filter(category__name="Salary").values_list("date", flat=True).order_by("date"))
        self.assertEqual(salaries, [date(2026, 9, 1), date(2026, 10, 1), date(2026, 11, 1)])
        self.assertEqual(tx.order_by("date").first().date, date(2026, 9, 1))
        self.assertLessEqual(tx.order_by("-date").first().date, TODAY)
        self.assertFalse(Transfer.objects.filter(user=user, date__gt=TODAY).exists())

        expense_days = set(tx.expense().values_list("date", flat=True))
        all_days = (TODAY - date(2026, 9, 1)).days + 1
        self.assertGreater(len(expense_days), all_days * 0.8)  # expenses on most days
        self.assertTrue(Transfer.objects.filter(user=user).exists())

    def test_amounts_are_irregular(self):
        user = build_demo(TODAY)
        amounts = Transaction.objects.filter(user=user).expense().values_list("amount", flat=True)
        self.assertTrue(any(a % 1000 for a in amounts))

    def test_balances_never_negative(self):
        user = build_demo(TODAY)
        for wallet in Wallet.objects.for_user(user).with_balance():
            with self.subTest(wallet=wallet.name):
                self.assertGreaterEqual(wallet.balance, 0)

    def test_same_date_gives_same_data(self):
        def snapshot():
            user = build_demo(TODAY)
            return list(Transaction.objects.filter(user=user).order_by("date", "description", "amount").values_list("date", "description", "amount"))
        self.assertEqual(snapshot(), snapshot())

    def test_reset_replaces_demo_data_and_leaves_others_alone(self):
        other = User.objects.create_user(email="sari@example.com", password="quiet-ledger-2026", full_name="Sari")
        Wallet.objects.create(user=other, name="Mandiri", initial_balance=5)
        user = build_demo(TODAY)
        Wallet.objects.create(user=user, name="Leftover")
        count = Transaction.objects.filter(user=user).count()
        build_demo(TODAY)
        self.assertFalse(Wallet.objects.filter(user=user, name="Leftover").exists())
        self.assertEqual(Transaction.objects.filter(user=user).count(), count)
        self.assertTrue(Wallet.objects.filter(user=other, name="Mandiri").exists())
        self.assertEqual(User.objects.filter(email=DEMO_EMAIL).count(), 1)

    def test_command(self):
        out = StringIO()
        with mock.patch("django.utils.timezone.now", return_value=datetime(2026, 11, 16, 3, tzinfo=dt_timezone.utc)):
            call_command("seed_demo", stdout=out)
        self.assertIn("Demo account demo@walleto.app ready", out.getvalue())
        self.assertIn("BCA", out.getvalue())


class DemoSignInTests(TestCase):
    url = reverse("accounts:demo")

    def test_creates_demo_when_missing_and_signs_in(self):
        self.assertFalse(User.objects.filter(email=DEMO_EMAIL).exists())
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("core:dashboard"), fetch_redirect_response=False)
        user = User.objects.get(email=DEMO_EMAIL)
        self.assertTrue(Wallet.objects.for_user(user).exists())
        page = self.client.get(reverse("core:dashboard"))
        self.assertEqual(page.context["user"], user)
        self.assertContains(page, "You&#x27;re using the demo account.")

    def test_reuses_existing_demo_data(self):
        build_demo(TODAY)
        count = Transaction.objects.count()
        self.client.post(self.url)
        self.assertEqual(Transaction.objects.count(), count)

    def test_get_does_nothing(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertFalse(User.objects.filter(email=DEMO_EMAIL).exists())

    def test_sign_in_page_offers_the_demo(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertContains(response, f'action="{self.url}"')
        self.assertContains(response, "Try demo account")
        self.assertNotContains(response, "disabled")
