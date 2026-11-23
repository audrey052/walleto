"""redesign-wallets-page: history, breakdown, page, sparkline, overdraft rule and transfer preview."""

import json
from datetime import date, datetime, timedelta, timezone as dt_timezone
from unittest import mock

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from core.templatetags.charts import sparkline, sparkline_points
from finance.forms import TransferForm
from finance.history import balance_history
from finance.models import Category, Transaction, Transfer, Wallet

from .test_views import make_user

HTMX = {"HTTP_HX_REQUEST": "true"}
NOW = datetime(2026, 11, 17, 3, 0, tzinfo=dt_timezone.utc)  # 17 Nov 2026, 10:00 Jakarta
TODAY = date(2026, 11, 17)


def cat(name):
    return Category.objects.get(user=None, name=name)


class WalletsTestCase(TestCase):
    def setUp(self):
        patcher = mock.patch("django.utils.timezone.now", return_value=NOW)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.user = make_user()
        self.client.force_login(self.user)
        self.bca = Wallet.objects.create(user=self.user, name="BCA", initial_balance=500_000)
        self.gopay = Wallet.objects.create(user=self.user, name="GoPay", type="ewallet", initial_balance=467_500)
        self.page = reverse("finance:wallets")

    def spend(self, amount, wallet, day=TODAY):
        return Transaction.objects.create(
            user=self.user, wallet=wallet, category=cat("Food & drinks"),
            amount=amount, date=day, description="Test",
        )

    def transfer(self, amount, source, target, day=TODAY, note=""):
        return Transfer.objects.create(
            user=self.user, from_wallet=source, to_wallet=target, amount=amount, date=day, note=note,
        )

    def history(self):
        return balance_history(Wallet.objects.for_user(self.user).with_balance(), TODAY)


class BalanceHistoryTests(WalletsTestCase):
    def test_trend_follows_an_expense(self):
        self.spend(67_500, self.gopay)
        points = self.history()[self.gopay.pk]
        self.assertEqual(len(points), 30)
        self.assertEqual(points[-2:], [467_500, 400_000])

    def test_transfer_moves_both_lines(self):
        self.transfer(100_000, self.bca, self.gopay, day=TODAY - timedelta(days=3))
        history = self.history()
        # The transfer is dated three days ago: its day is the 4th point from the end.
        self.assertEqual(history[self.bca.pk][-5:], [500_000, 400_000, 400_000, 400_000, 400_000])
        self.assertEqual(history[self.gopay.pk][-4], 567_500)
        self.assertEqual(history[self.gopay.pk][-5], 467_500)

    def test_no_activity_is_flat(self):
        self.assertEqual(set(self.history()[self.bca.pk]), {500_000})

    def test_activity_before_the_window_is_in_the_starting_point(self):
        self.spend(100_000, self.bca, day=TODAY - timedelta(days=45))
        self.assertEqual(set(self.history()[self.bca.pk]), {400_000})

    def test_query_count_is_fixed(self):
        for index in range(3):
            Wallet.objects.create(user=self.user, name=f"Extra {index}")
        wallets = list(Wallet.objects.for_user(self.user).with_balance())
        # Transactions, transfers and goal movements: one query each (add-savings-goals).
        with self.assertNumQueries(3):
            balance_history(wallets, TODAY)


class SparklineTests(SimpleTestCase):
    def test_points_scale_between_min_and_max(self):
        points = sparkline_points([0, 50, 100])
        self.assertEqual(points, [(3.0, 27.0), (60.0, 16.0), (117.0, 5.0)])

    def test_flat_series_is_mid_height(self):
        self.assertEqual({y for _, y in sparkline_points([5, 5, 5])}, {16})

    def test_svg(self):
        svg = sparkline([1, 2], label="BCA, last 30 days")
        self.assertIn('aria-label="BCA, last 30 days"', svg)
        self.assertIn('<circle cx="117.0" cy="5.0"', svg)
        self.assertEqual(sparkline([]), "")


class WalletsPageTests(WalletsTestCase):
    def test_breakdown_by_type(self):
        Wallet.objects.create(user=self.user, name="Jago", initial_balance=3_275_000)
        response = self.client.get(self.page)
        breakdown = {item["label"]: item["total"] for item in response.context["breakdown"]}
        self.assertEqual(breakdown, {"Bank accounts": 3_775_000, "E-wallets": 467_500, "Cash": 0})
        self.assertEqual(sum(breakdown.values()), response.context["total_balance"])
        self.assertContains(response, "Across 3 wallets")
        self.assertContains(response, "As of 17 Nov 2026")
        self.assertContains(response, "19 Oct–17 Nov 2026")

    def test_rows_link_to_activity_and_offer_actions(self):
        response = self.client.get(self.page)
        for wallet in (self.bca, self.gopay):
            self.assertContains(response, f"{reverse('finance:transactions')}?wallet={wallet.pk}")
            self.assertContains(response, reverse("finance:wallet_edit", args=[wallet.pk]))
            self.assertContains(response, reverse("finance:wallet_archive", args=[wallet.pk]))
        self.assertContains(response, 'class="sparkline"', count=2)

    def test_archived_wallet_leaves_table_and_breakdown(self):
        self.gopay.archive()
        response = self.client.get(self.page)
        self.assertEqual([w.name for w in response.context["wallets"]], ["BCA"])
        breakdown = {item["label"]: item["total"] for item in response.context["breakdown"]}
        self.assertEqual(breakdown["E-wallets"], 0)
        self.assertContains(response, "Archived wallets (1)")

    def test_transfer_money_disabled_with_one_wallet(self):
        self.gopay.archive()
        response = self.client.get(self.page)
        self.assertFalse(response.context["can_transfer"])
        self.assertContains(response, "disabled title=\"Add a second wallet")
        self.assertNotContains(response, "Move money")

    def test_recent_transfers_three_newest(self):
        for day in range(1, 6):
            self.transfer(10_000 * day, self.bca, self.gopay, day=date(2026, 11, day))
        response = self.client.get(self.page)
        self.assertEqual([t.amount for t in response.context["recent_transfers"]], [50_000, 40_000, 30_000])
        self.assertContains(response, "Recent transfers")
        self.assertContains(response, "Between your wallets")

    def test_no_transfers_no_list(self):
        self.assertNotContains(self.client.get(self.page), "Recent transfers")


class OverdraftTests(WalletsTestCase):
    def form(self, amount, instance=None, source=None):
        data = {
            "from_wallet": (source or self.bca).pk, "to_wallet": self.gopay.pk,
            "amount": amount, "date": "2026-11-17", "note": "",
        }
        return TransferForm(data, instance=instance, user=self.user)

    def test_too_much(self):
        form = self.form("600.000")
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["amount"], ["Not enough in BCA. Choose another wallet or a smaller amount."])

    def test_exactly_the_balance(self):
        self.assertTrue(self.form("500.000").is_valid())

    def test_edit_counts_its_own_amount(self):
        record = self.transfer(200_000, self.bca, self.gopay)
        self.spend(200_000, self.bca)  # BCA now holds Rp100.000
        self.assertTrue(self.form("300.000", instance=Transfer.objects.get(pk=record.pk)).is_valid())
        # A fresh instance each time: is_valid() writes the new amount onto the instance.
        self.assertFalse(self.form("300.001", instance=Transfer.objects.get(pk=record.pk)).is_valid())

    def test_other_users_wallets_still_rejected(self):
        other = make_user("sari@example.com", "Sari")
        theirs = Wallet.objects.create(user=other, name="Mandiri", initial_balance=9_000_000)
        form = self.form("1.000", source=theirs)
        self.assertFalse(form.is_valid())
        self.assertIn("from_wallet", form.errors)

    def test_view_shows_the_message(self):
        response = self.client.post(reverse("finance:transfer_create"), {
            "from_wallet": self.bca.pk, "to_wallet": self.gopay.pk,
            "amount": "600.000", "date": "2026-11-17", "note": "",
        }, **HTMX)
        self.assertContains(response, "Not enough in BCA. Choose another wallet or a smaller amount.")
        self.assertFalse(Transfer.objects.exists())


class TransferModalTests(WalletsTestCase):
    def wallets_json(self, response):
        html = response.content.decode()
        start = html.index('id="transfer-wallets" type="application/json">') + len('id="transfer-wallets" type="application/json">')
        return json.loads(html[start:html.index("</script>", start)])

    def test_modal_includes_balances(self):
        response = self.client.get(reverse("finance:transfer_create"), **HTMX)
        self.assertContains(response, 'x-data="transferForm"')
        self.assertContains(response, 'x-text="submitLabel"')
        self.assertEqual(self.wallets_json(response), {
            str(self.bca.pk): {"name": "BCA", "balance": 500_000},
            str(self.gopay.pk): {"name": "GoPay", "balance": 467_500},
        })

    def test_edit_shows_balances_before_the_transfer(self):
        record = self.transfer(200_000, self.bca, self.gopay)
        response = self.client.get(reverse("finance:transfer_edit", args=[record.pk]), **HTMX)
        self.assertEqual(self.wallets_json(response)[str(self.bca.pk)]["balance"], 500_000)
        self.assertEqual(self.wallets_json(response)[str(self.gopay.pk)]["balance"], 467_500)
        self.assertNotContains(response, 'x-text="submitLabel"')

    def test_transfer_from_transactions_page_still_works(self):
        response = self.client.post(reverse("finance:transfer_create"), {
            "from_wallet": self.bca.pk, "to_wallet": self.gopay.pk,
            "amount": "200.000", "date": "2026-11-17", "note": "",
            "next": reverse("finance:transactions"),
        })
        self.assertRedirects(response, reverse("finance:transactions"), fetch_redirect_response=False)
        self.assertEqual(Transfer.objects.get().amount, 200_000)
