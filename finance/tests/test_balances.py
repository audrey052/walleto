from datetime import date

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from finance.models import Category, Transaction, Transfer, Wallet

User = get_user_model()


class BalanceTests(TestCase):
    """Wallets spec, "Wallets page and total balance" (MODIFIED in MVP 2)."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="aditya@example.com", password="quiet-ledger-2026", full_name="Aditya"
        )
        self.food = Category.objects.get(user=None, name="Food & drinks")
        self.salary = Category.objects.get(user=None, name="Salary")
        self.bca = Wallet.objects.create(user=self.user, name="BCA", initial_balance=1_000_000)
        self.gopay = Wallet.objects.create(user=self.user, name="GoPay", type="ewallet", initial_balance=0)

    def tx(self, wallet, category, amount, day=date(2026, 11, 10)):
        return Transaction.objects.create(
            user=self.user, wallet=wallet, category=category, amount=amount,
            date=day, description="x",
        )

    def transfer(self, source, target, amount):
        return Transfer.objects.create(
            user=self.user, from_wallet=source, to_wallet=target, amount=amount, date=date(2026, 11, 10)
        )

    def balances(self):
        return dict(Wallet.objects.for_user(self.user).with_balance().values_list("name", "balance"))

    def test_spec_example(self):
        # Start 1.000.000, income 500.000, expenses 200.000, in 50.000, out 300.000 -> 1.050.000
        self.tx(self.bca, self.salary, 500_000)
        self.tx(self.bca, self.food, 200_000)
        self.transfer(self.gopay, self.bca, 50_000)
        self.transfer(self.bca, self.gopay, 300_000)
        self.assertEqual(self.balances()["BCA"], 1_050_000)
        self.assertEqual(self.balances()["GoPay"], 250_000)

    def test_many_rows_do_not_multiply(self):
        # Several transactions AND several transfers on the same wallet: a join would multiply sums.
        for _ in range(3):
            self.tx(self.bca, self.food, 10_000)
            self.tx(self.bca, self.salary, 100_000)
            self.transfer(self.bca, self.gopay, 1_000)
        self.assertEqual(self.balances()["BCA"], 1_000_000 + 300_000 - 30_000 - 3_000)

    def test_transfers_do_not_change_the_total(self):
        before = Wallet.objects.for_user(self.user).active().total_balance()
        self.transfer(self.bca, self.gopay, 200_000)
        after = Wallet.objects.for_user(self.user).active().total_balance()
        self.assertEqual(before, after)
        self.assertEqual(self.balances(), {"BCA": 800_000, "GoPay": 200_000})

    def test_negative_balance(self):
        cash = Wallet.objects.create(user=self.user, name="Cash", type="cash", initial_balance=20_000)
        self.tx(cash, self.food, 50_000)
        self.assertEqual(self.balances()["Cash"], -30_000)

    def test_editing_and_deleting_updates_balance(self):
        t = self.tx(self.bca, self.food, 67_500)
        t.amount = 72_500
        t.save()
        self.assertEqual(self.balances()["BCA"], 1_000_000 - 72_500)
        t.delete()
        self.assertEqual(self.balances()["BCA"], 1_000_000)

    def test_wallet_without_activity(self):
        self.assertEqual(self.balances()["GoPay"], 0)


class TransactionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="a@example.com", password="quiet-ledger-2026", full_name="A")
        self.wallet = Wallet.objects.create(user=self.user, name="BCA")

    def make(self, category_name, amount=1000):
        return Transaction.objects.create(
            user=self.user, wallet=self.wallet, amount=amount, date=date(2026, 11, 1),
            category=Category.objects.get(user=None, name=category_name), description="  GoFood  ",
        )

    def test_kind_follows_category(self):
        self.assertEqual(self.make("Food & drinks").kind, "expense")
        self.assertEqual(self.make("Salary").kind, "income")

    def test_description_is_trimmed(self):
        self.assertEqual(self.make("Food & drinks").description, "GoFood")

    def test_amount_must_be_positive(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make("Food & drinks", amount=0)

    def test_wallet_with_history_cannot_be_deleted(self):
        from django.db.models import ProtectedError

        self.make("Food & drinks")
        with self.assertRaises(ProtectedError):
            self.wallet.delete()

    def test_month_filter_and_totals(self):
        self.make("Food & drinks", 30_000)
        self.make("Salary", 100_000)
        Transaction.objects.create(
            user=self.user, wallet=self.wallet, amount=999, date=date(2026, 10, 31),
            category=Category.objects.get(user=None, name="Food & drinks"), description="October",
        )
        november = Transaction.objects.for_user(self.user).in_month(2026, 11)
        self.assertEqual(november.count(), 2)
        self.assertEqual(november.totals(), {"income": 100_000, "expense": 30_000, "net": 70_000})

    def test_december_month_bounds(self):
        Transaction.objects.create(
            user=self.user, wallet=self.wallet, amount=1, date=date(2026, 12, 31),
            category=Category.objects.get(user=None, name="Others"), description="NYE",
        )
        self.assertEqual(Transaction.objects.in_month(2026, 12).count(), 1)
        self.assertEqual(Transaction.objects.in_month(2027, 1).count(), 0)

    def test_search_description_and_note(self):
        t = self.make("Food & drinks")
        t.note = "Kopi Kenangan"
        t.save()
        self.assertEqual(Transaction.objects.search("kopi").count(), 1)
        self.assertEqual(Transaction.objects.search("gofood").count(), 1)
        self.assertEqual(Transaction.objects.search("tuku").count(), 0)


class TransferModelTests(TestCase):
    def test_same_wallet_is_rejected_by_the_database(self):
        user = User.objects.create_user(email="a@example.com", password="quiet-ledger-2026", full_name="A")
        wallet = Wallet.objects.create(user=user, name="BCA")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Transfer.objects.create(user=user, from_wallet=wallet, to_wallet=wallet, amount=1, date=date(2026, 11, 1))
