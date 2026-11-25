from datetime import date, datetime, timedelta, timezone as dt_timezone
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from finance.forms import TransactionForm, TransferForm
from finance.models import Category, Transaction, Transfer, Wallet

User = get_user_model()
HTMX = {"HTTP_HX_REQUEST": "true"}
# Freeze "today" at 16 Nov 2026, 10:00 in Jakarta (03:00 UTC).
NOW = datetime(2026, 11, 16, 3, 0, tzinfo=dt_timezone.utc)


def make_user(email="aditya@example.com", name="Aditya Ramadhan"):
    return User.objects.create_user(email=email, password="quiet-ledger-2026", full_name=name)


def cat(name):
    return Category.objects.get(user=None, name=name)


class ActivityTestCase(TestCase):
    def setUp(self):
        patcher = mock.patch("django.utils.timezone.now", return_value=NOW)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.user = make_user()
        self.client.force_login(self.user)
        self.bca = Wallet.objects.create(user=self.user, name="BCA", initial_balance=1_000_000)
        self.gopay = Wallet.objects.create(user=self.user, name="GoPay", type="ewallet")
        self.url = reverse("finance:transactions")

    def tx(self, description="GoFood", amount=67_500, category="Food & drinks", wallet=None, day=date(2026, 11, 14), note=""):
        return Transaction.objects.create(
            user=self.user, wallet=wallet or self.gopay, category=cat(category),
            amount=amount, date=day, description=description, note=note,
        )

    def transfer(self, amount=200_000, day=date(2026, 11, 12), source=None, target=None):
        return Transfer.objects.create(
            user=self.user, from_wallet=source or self.bca, to_wallet=target or self.gopay,
            amount=amount, date=day,
        )

    def balance(self, wallet):
        return Wallet.objects.with_balance().get(pk=wallet.pk).balance


class TransactionFormTests(ActivityTestCase):
    def data(self, **overrides):
        data = {
            "description": "GoFood", "amount": "67.500", "category": cat("Food & drinks").pk,
            "wallet": self.gopay.pk, "date": "2026-11-16", "note": "",
        }
        data.update(overrides)
        return data

    def test_valid_and_kind_from_category(self):
        form = TransactionForm(self.data(category=cat("Salary").pk), user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().kind, "income")

    def test_defaults_to_today_in_jakarta(self):
        self.assertEqual(TransactionForm(user=self.user).initial["date"], date(2026, 11, 16))

    def test_zero_or_empty_amount(self):
        for amount in ["0", ""]:
            with self.subTest(amount=amount):
                form = TransactionForm(self.data(amount=amount), user=self.user)
                self.assertEqual(form.errors["amount"], ["Amount must be greater than 0."])

    def test_future_date(self):
        form = TransactionForm(self.data(date="2026-11-17"), user=self.user)
        self.assertEqual(form.errors["date"], ["Date can't be in the future."])

    def test_only_active_own_wallets_offered(self):
        archived = Wallet.objects.create(user=self.user, name="OVO")
        archived.archive()
        theirs = Wallet.objects.create(user=make_user("sari@example.com", "Sari"), name="Mandiri")
        offered = set(TransactionForm(user=self.user).fields["wallet"].queryset)
        self.assertEqual(offered, {self.bca, self.gopay})
        form = TransactionForm(self.data(wallet=theirs.pk), user=self.user)
        self.assertIn("wallet", form.errors)
        form = TransactionForm(self.data(wallet=archived.pk), user=self.user)
        self.assertIn("wallet", form.errors)

    def test_archived_wallet_kept_when_editing(self):
        record = self.tx()
        self.gopay.archive()
        form = TransactionForm(instance=record, user=self.user)
        self.assertIn(self.gopay, form.fields["wallet"].queryset)

    def test_other_users_category_rejected(self):
        other = make_user("sari@example.com", "Sari")
        pets = Category.objects.create(user=other, name="Pets", kind="expense", color="#1F5C4A")
        form = TransactionForm(self.data(category=pets.pk), user=self.user)
        self.assertIn("category", form.errors)

    def test_categories_grouped_by_kind(self):
        choices = TransactionForm(user=self.user).fields["category"].widget.choices
        self.assertEqual([group for group, _ in choices[1:]], ["Expense", "Income"])


class TransferFormTests(ActivityTestCase):
    def data(self, **overrides):
        data = {"from_wallet": self.bca.pk, "to_wallet": self.gopay.pk, "amount": "200.000", "date": "2026-11-16", "note": ""}
        data.update(overrides)
        return data

    def test_valid(self):
        form = TransferForm(self.data(), user=self.user)
        self.assertTrue(form.is_valid(), form.errors)

    def test_same_wallet(self):
        form = TransferForm(self.data(to_wallet=self.bca.pk), user=self.user)
        self.assertEqual(form.errors["to_wallet"], ["Choose two different wallets."])

    def test_needs_two_wallets(self):
        loner = make_user("solo@example.com", "Solo")
        Wallet.objects.create(user=loner, name="Cash", type="cash")
        self.assertFalse(TransferForm(user=loner).has_enough_wallets)
        self.assertTrue(TransferForm(user=self.user).has_enough_wallets)

    def test_other_users_wallet_rejected(self):
        theirs = Wallet.objects.create(user=make_user("sari@example.com", "Sari"), name="Mandiri")
        form = TransferForm(self.data(to_wallet=theirs.pk), user=self.user)
        self.assertIn("to_wallet", form.errors)


class TransactionsPageTests(ActivityTestCase):
    def test_defaults_to_current_month_with_summary(self):
        self.tx("Salary", 12_500_000, "Salary", self.bca, date(2026, 11, 1))
        self.tx("GoFood", 5_847_500)
        self.transfer(500_000)
        self.tx("October", 999, day=date(2026, 10, 31))
        response = self.client.get(self.url)
        self.assertEqual(response.context["period"].month, (2026, 11))
        self.assertEqual(response.context["summary"], {"income": 12_500_000, "expense": 5_847_500, "net": 6_652_500})
        self.assertNotContains(response, "October")
        self.assertIsNone(response.context["next_url"])

    def test_previous_month_and_bad_or_future_values(self):
        self.tx("October", 999, day=date(2026, 10, 31))
        response = self.client.get(self.url, {"month": "2026-10"})
        self.assertContains(response, "October")
        self.assertIn("month=2026-11", response.context["next_url"])
        for bad in ["2026-13", "abc", "2027-01"]:
            with self.subTest(month=bad):
                self.assertEqual(self.client.get(self.url, {"month": bad}).context["period"].month, (2026, 11))

    def test_rows_grouped_by_day_with_transfer_row(self):
        self.tx("GoFood", 67_500)
        self.tx("Grab", 32_000, "Transport")
        self.transfer(200_000, day=date(2026, 11, 14))
        self.tx("Salary", 5_000_000, "Salary", self.bca, date(2026, 11, 12))
        self.transfer(100_000, day=date(2026, 11, 10))
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["entries"]), 5)
        self.assertEqual(response.context["summary"]["expense"], 99_500)  # transfers excluded
        # No Date column: each day has its own header, newest first.
        self.assertNotContains(response, '<th scope="col">Date</th>', html=False)
        groups = response.context["day_groups"]
        self.assertEqual([g["date"] for g in groups], [date(2026, 11, 14), date(2026, 11, 12), date(2026, 11, 10)])
        self.assertEqual((groups[0]["count"], groups[0]["expense"], groups[0]["income"]), (3, 99_500, 0))
        self.assertContains(response, "14 Nov 2026")
        self.assertContains(response, "Saturday")
        self.assertContains(response, "Daily expenses")
        self.assertContains(response, "Daily income")
        self.assertContains(response, "No income or expenses")  # 10 Nov: only a transfer
        self.assertNotContains(response, "Wallet transfers are not counted as expenses.")  # removed
        self.assertNotContains(response, "transactions shown")
        self.assertContains(response, "BCA → GoPay")
        self.assertContains(response, '5 transactions <i class="dot-sep"></i> November 2026', html=False)
        self.assertContains(response, "Expenses")
        self.assertNotContains(response, "Monthly expenses")
        self.assertNotContains(response, ">Net")

    def test_newest_first(self):
        self.tx("Older", day=date(2026, 11, 2))
        self.tx("Newer", day=date(2026, 11, 15))
        entries = self.client.get(self.url).context["entries"]
        self.assertEqual([e.description for e, _ in entries], ["Newer", "Older"])

    def test_search_is_case_insensitive_and_covers_notes(self):
        self.tx("Kopi Kenangan")
        self.tx("Fore", note="kopi susu")
        self.tx("Indomaret", category="Shopping")
        response = self.client.get(self.url, {"q": "KOPI"})
        names = [e.description for e, kind in response.context["entries"]]
        self.assertCountEqual(names, ["Kopi Kenangan", "Fore"])

    def test_wallet_filter_keeps_its_transfers(self):
        self.tx("GoFood", wallet=self.gopay)
        self.tx("Indomaret", wallet=self.bca, category="Shopping")
        self.transfer()
        entries = self.client.get(self.url, {"wallet": self.gopay.pk}).context["entries"]
        self.assertEqual(sorted(kind for _, kind in entries), ["transaction", "transfer"])

    def test_category_filter_hides_transfers(self):
        self.tx("GoFood")
        self.transfer()
        response = self.client.get(self.url, {"category": cat("Food & drinks").pk})
        self.assertEqual([kind for _, kind in response.context["entries"]], ["transaction"])

    def test_filters_ignore_other_users_ids(self):
        other = make_user("sari@example.com", "Sari")
        theirs = Wallet.objects.create(user=other, name="Mandiri")
        self.tx("GoFood")
        response = self.client.get(self.url, {"wallet": theirs.pk})
        self.assertIsNone(response.context["selected_wallet"])
        self.assertContains(response, "GoFood")

    def test_one_add_transaction_button(self):
        # Empty month: only the empty state's button. With entries: only the heading's.
        empty = self.client.get(self.url).content.decode()
        self.assertEqual(empty.count("Add transaction"), 1)
        self.assertIn("No transactions in November 2026", empty)
        self.tx("GoFood")
        full = self.client.get(self.url).content.decode()
        self.assertEqual(full.count("Add transaction"), 1)
        # A search with no results keeps the heading button (that empty state only offers Clear filters).
        filtered = self.client.get(self.url, {"q": "nothing-like-this"}).content.decode()
        self.assertEqual(filtered.count("Add transaction"), 1)

    def test_no_transfer_button(self):
        # Transfers start from Wallets only; their rows here still open the edit modal.
        self.assertNotContains(self.client.get(self.url), reverse("finance:transfer_create"))

    def test_no_results_empty_state(self):
        self.tx("GoFood")
        response = self.client.get(self.url, {"q": "nothing-like-this"})
        self.assertContains(response, "No transactions here yet.")
        self.assertContains(response, "Clear filters")

    def test_pagination(self):
        for i in range(60):
            self.tx(f"Item {i}", 1_000, day=date(2026, 11, 14))
        first = self.client.get(self.url)
        second = self.client.get(self.url, {"page": 2})
        self.assertEqual(first.context["page"].paginator.num_pages, 2)
        self.assertEqual(len(first.context["entries"]), 50)
        self.assertEqual(len(second.context["entries"]), 10)
        self.assertEqual(second.context["summary"]["expense"], 60_000)  # summary covers the whole month
        self.assertIn("page=2", first.context["page_next_url"])
        # A day split across pages shows the whole day's count and total on both pages.
        for page in (first, second):
            day = page.context["day_groups"][0]
            self.assertEqual((day["count"], day["expense"]), (60, 60_000))

    def test_only_own_transactions_listed(self):
        other = make_user("sari@example.com", "Sari")
        theirs = Wallet.objects.create(user=other, name="Mandiri")
        Transaction.objects.create(user=other, wallet=theirs, category=cat("Others"), amount=1, date=date(2026, 11, 10), description="Secret")
        self.assertNotContains(self.client.get(self.url), "Secret")

    def test_transactions_section_is_active(self):
        record = self.tx()
        for url in [self.url, reverse("finance:transaction_edit", args=[record.pk]), reverse("finance:transfer_create")]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).context["active_section"]["key"], "transactions")


class TransactionExportTests(ActivityTestCase):
    export_url = reverse("finance:transactions_export")

    def rows(self, **params):
        response = self.client.get(self.export_url, params)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        text = response.content.decode("utf-8-sig")
        import csv, io
        return response, list(csv.reader(io.StringIO(text)))

    def test_exports_month_with_signed_amounts_and_transfers(self):
        self.tx("GoFood", 67_500)
        self.tx("Salary", 12_500_000, "Salary", self.bca, date(2026, 11, 1))
        self.transfer(200_000)
        self.tx("October", 999, day=date(2026, 10, 31))
        response, rows = self.rows(month="2026-11")
        self.assertIn('filename="walleto-transactions-2026-11.csv"', response["Content-Disposition"])
        self.assertEqual(rows[0], ["Date", "Type", "Description", "Note", "Category", "Wallet", "Amount"])
        self.assertEqual(rows[1], ["2026-11-14", "Expense", "GoFood", "", "Food & drinks", "GoPay", "-67500"])
        self.assertEqual(rows[2], ["2026-11-12", "Transfer", "BCA → GoPay", "", "", "BCA → GoPay", "200000"])
        self.assertEqual(rows[3], ["2026-11-01", "Income", "Salary", "", "Salary", "BCA", "12500000"])
        self.assertEqual(len(rows), 4)

    def test_export_follows_filters_and_has_all_pages(self):
        for i in range(60):
            self.tx(f"Kopi {i}", 1_000)
        self.tx("Grab", 32_000, "Transport")
        _, rows = self.rows(q="kopi")
        self.assertEqual(len(rows), 61)

    def test_export_neutralises_formulas(self):
        self.tx("=HYPERLINK(\"http://evil\")")
        _, rows = self.rows()
        self.assertEqual(rows[1][2], "'=HYPERLINK(\"http://evil\")")

    def test_export_only_own_rows(self):
        other = make_user("sari@example.com", "Sari")
        theirs = Wallet.objects.create(user=other, name="Mandiri")
        Transaction.objects.create(user=other, wallet=theirs, category=cat("Others"), amount=1, date=date(2026, 11, 10), description="Secret")
        _, rows = self.rows()
        self.assertNotIn("Secret", str(rows))

    def test_page_links_export_with_current_filters(self):
        response = self.client.get(self.url, {"q": "kopi", "month": "2026-11"})
        self.assertIn("/transactions/export/?month=2026-11&amp;q=kopi", response.content.decode())


class TransactionCrudTests(ActivityTestCase):
    def post_create(self, **overrides):
        data = {
            "description": "GoFood", "amount": "67.500", "category": cat("Food & drinks").pk,
            "wallet": self.gopay.pk, "date": "2026-11-14", "note": "",
        }
        data.update(overrides)
        return self.client.post(reverse("finance:transaction_create"), data, **HTMX)

    def test_create_redirects_to_its_month_with_toast(self):
        response = self.post_create()
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response["HX-Redirect"], f"{self.url}?month=2026-11")
        self.assertEqual(self.balance(self.gopay), -67_500)
        self.assertContains(self.client.get(self.url), "Transaction added.")

    def test_create_respects_safe_next_only(self):
        response = self.post_create(next="/wallets/")
        self.assertEqual(response["HX-Redirect"], "/wallets/")
        response = self.post_create(next="https://evil.example.com/")
        self.assertEqual(response["HX-Redirect"], f"{self.url}?month=2026-11")

    def test_create_error_keeps_modal(self):
        response = self.post_create(amount="0")
        self.assertContains(response, "<dialog")
        self.assertContains(response, "Amount must be greater than 0.")
        self.assertFalse(Transaction.objects.exists())

    def test_edit_updates_balance(self):
        record = self.tx()
        url = reverse("finance:transaction_edit", args=[record.pk])
        self.assertContains(self.client.get(url, **HTMX), "Delete")
        self.client.post(url, {
            "description": "GoFood", "amount": "72.500", "category": cat("Food & drinks").pk,
            "wallet": self.gopay.pk, "date": "2026-11-14", "note": "",
        }, **HTMX)
        self.assertEqual(self.balance(self.gopay), -72_500)
        self.assertContains(self.client.get(self.url), "Transaction updated.")

    def test_delete_confirms_then_removes(self):
        record = self.tx()
        url = reverse("finance:transaction_delete", args=[record.pk])
        self.assertContains(self.client.get(url, **HTMX), "Delete this transaction?")
        self.assertTrue(Transaction.objects.filter(pk=record.pk).exists())
        response = self.client.post(url, **HTMX)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Transaction.objects.filter(pk=record.pk).exists())
        self.assertEqual(self.balance(self.gopay), 0)
        self.assertContains(self.client.get(self.url), "Transaction deleted.")

    def test_create_without_wallets_explains(self):
        loner = make_user("solo@example.com", "Solo")
        self.client.force_login(loner)
        response = self.client.get(reverse("finance:transaction_create"), **HTMX)
        self.assertContains(response, "Add a wallet")
        self.assertNotContains(response, 'type="submit"')


class TransferCrudTests(ActivityTestCase):
    def test_create_moves_money_and_keeps_total(self):
        total = Wallet.objects.for_user(self.user).active().total_balance()
        response = self.client.post(reverse("finance:transfer_create"), {
            "from_wallet": self.bca.pk, "to_wallet": self.gopay.pk, "amount": "200.000", "date": "2026-11-16", "note": "",
            "next": "/wallets/",
        }, **HTMX)
        self.assertEqual(response["HX-Redirect"], "/wallets/")
        self.assertEqual((self.balance(self.bca), self.balance(self.gopay)), (800_000, 200_000))
        self.assertEqual(Wallet.objects.for_user(self.user).active().total_balance(), total)
        self.assertContains(self.client.get("/wallets/"), "Transfer recorded.")

    def test_one_wallet_explains_and_refuses(self):
        loner = make_user("solo@example.com", "Solo")
        cash = Wallet.objects.create(user=loner, name="Cash", type="cash")
        self.client.force_login(loner)
        url = reverse("finance:transfer_create")
        self.assertContains(self.client.get(url, **HTMX), "A transfer needs two wallets")
        self.client.post(url, {"from_wallet": cash.pk, "to_wallet": cash.pk, "amount": "1", "date": "2026-11-16"})
        self.assertFalse(Transfer.objects.exists())

    def test_edit_and_delete(self):
        record = self.transfer()
        self.client.post(reverse("finance:transfer_edit", args=[record.pk]), {
            "from_wallet": self.bca.pk, "to_wallet": self.gopay.pk, "amount": "50.000", "date": "2026-11-12", "note": "top up",
        }, **HTMX)
        self.assertEqual(self.balance(self.gopay), 50_000)
        self.assertContains(self.client.get(self.url), "Transfer updated.")
        self.client.post(reverse("finance:transfer_delete", args=[record.pk]), **HTMX)
        self.assertEqual((self.balance(self.bca), self.balance(self.gopay)), (1_000_000, 0))
        self.assertContains(self.client.get(self.url), "Transfer deleted.")


class WalletsPageActivityTests(ActivityTestCase):
    def test_rows_show_real_balance_and_activity_link(self):
        self.tx("GoFood", 67_500)
        response = self.client.get(reverse("finance:wallets"))
        balances = {w.name: w.balance for w in response.context["wallets"]}
        self.assertEqual(balances, {"BCA": 1_000_000, "GoPay": -67_500})
        self.assertContains(response, f"{self.url}?wallet={self.gopay.pk}")
        self.assertContains(response, "−Rp67.500")
        self.assertContains(response, "Transfer")

    def test_archived_wallet_history_stays_visible(self):
        self.tx("GoFood")
        self.gopay.archive()
        self.assertContains(self.client.get(self.url), "GoFood")


class ActivityPrivacyTests(ActivityTestCase):
    def setUp(self):
        super().setUp()
        other = make_user("sari@example.com", "Sari")
        a = Wallet.objects.create(user=other, name="Mandiri")
        b = Wallet.objects.create(user=other, name="Dana")
        self.their_tx = Transaction.objects.create(user=other, wallet=a, category=cat("Others"), amount=5, date=date(2026, 11, 1), description="Theirs")
        self.their_transfer = Transfer.objects.create(user=other, from_wallet=a, to_wallet=b, amount=5, date=date(2026, 11, 1))

    def test_other_users_records_are_404(self):
        for name, pk in [
            ("finance:transaction_edit", self.their_tx.pk),
            ("finance:transaction_delete", self.their_tx.pk),
            ("finance:transfer_edit", self.their_transfer.pk),
            ("finance:transfer_delete", self.their_transfer.pk),
        ]:
            with self.subTest(view=name):
                url = reverse(name, args=[pk])
                self.assertEqual(self.client.get(url).status_code, 404)
                self.assertEqual(self.client.post(url).status_code, 404)
        self.assertTrue(Transaction.objects.filter(pk=self.their_tx.pk).exists())
        self.assertTrue(Transfer.objects.filter(pk=self.their_transfer.pk).exists())


class TransactionsRangeTests(ActivityTestCase):
    """add-date-range: Transactions for a range of days (today is 16 Nov 2026)."""

    RANGE = {"from": "2026-11-10", "to": "2026-11-16"}

    def setUp(self):
        super().setUp()
        self.tx("Before", 11_000, day=date(2026, 11, 9))
        self.tx("Start", 100_000, day=date(2026, 11, 10))
        self.tx("Salary", 5_000_000, "Salary", self.bca, date(2026, 11, 12))
        self.tx("End", 200_000, day=date(2026, 11, 16))

    def test_a_range_of_days(self):
        response = self.client.get(self.url, self.RANGE)
        self.assertEqual([e.description for e, _ in response.context["entries"]], ["End", "Salary", "Start"])
        self.assertContains(response, "10 Nov – 16 Nov 2026")
        self.assertContains(response, '3 transactions <i class="dot-sep"></i> 10 Nov – 16 Nov 2026', html=False)

    def test_range_summary(self):
        summary = self.client.get(self.url, self.RANGE).context["summary"]
        self.assertEqual((summary["income"], summary["expense"]), (5_000_000, 300_000))

    def test_filters_keep_the_range(self):
        response = self.client.get(self.url, {**self.RANGE, "wallet": self.gopay.pk})
        content = response.content.decode()
        self.assertIn('<input type="hidden" name="from" value="2026-11-10">', content)
        self.assertIn('<input type="hidden" name="to" value="2026-11-16">', content)
        self.assertTrue(response.context["clear_url"].endswith("?from=2026-11-10&to=2026-11-16"))
        self.assertIn(f"wallet={self.gopay.pk}", response.context["export_url"])
        self.assertIn("from=2026-11-10", response.context["export_url"])

    def test_export_a_range(self):
        response = self.client.get(reverse("finance:transactions_export"), self.RANGE)
        self.assertIn('filename="walleto-transactions-2026-11-10_2026-11-16.csv"', response["Content-Disposition"])
        body = response.content.decode("utf-8-sig")
        self.assertIn("Start", body)
        self.assertNotIn("Before", body)

    def test_a_whole_month_keeps_its_file_name(self):
        response = self.client.get(reverse("finance:transactions_export"), {"from": "2026-10-01", "to": "2026-10-31"})
        self.assertIn('filename="walleto-transactions-2026-10.csv"', response["Content-Disposition"])

    def test_arrows_and_picker(self):
        response = self.client.get(self.url, self.RANGE)
        self.assertIn("month=2026-10", response.context["prev_url"])
        self.assertIsNone(response.context["next_url"])
        self.assertContains(response, 'hx-target="#transactions-page"')
        self.assertNotContains(response, "Last 7 days")
        self.assertContains(response, 'name="from" x-ref="from" value="2026-11-10" max="2026-11-16"')
        # The picker's form keeps the filters too.
        self.assertContains(self.client.get(self.url, {**self.RANGE, "q": "kopi"}), '<input type="hidden" name="q" value="kopi">', count=1)

    def test_another_users_entries_stay_out(self):
        other = make_user(email="other@example.com", name="Other")
        wallet = Wallet.objects.create(user=other, name="Other BCA")
        Transaction.objects.create(user=other, wallet=wallet, category=cat("Food & drinks"), amount=777_000, date=date(2026, 11, 12), description="Not mine")
        response = self.client.get(self.url, self.RANGE)
        self.assertNotContains(response, "Not mine")
        self.assertEqual(response.context["summary"]["expense"], 300_000)
        export = self.client.get(reverse("finance:transactions_export"), self.RANGE).content.decode("utf-8-sig")
        self.assertNotIn("Not mine", export)
