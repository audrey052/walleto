from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from finance.models import WALLET_COLORS, Category, Wallet

User = get_user_model()


def make_user(email="aditya@example.com", name="Aditya Ramadhan"):
    return User.objects.create_user(email=email, password="quiet-ledger-2026", full_name=name)


class WalletModelTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_monograms_follow_the_spec(self):
        cases = [
            ("BCA", Wallet.Type.BANK, "BCA"),
            ("OVO", Wallet.Type.EWALLET, "OVO"),
            ("Jago", Wallet.Type.BANK, "JAGO"),
            ("Bank Jago", Wallet.Type.BANK, "BJ"),
            ("GoPay", Wallet.Type.EWALLET, "Go"),
            ("Dompet", Wallet.Type.CASH, "Rp"),
        ]
        for name, kind, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(Wallet(name=name, type=kind).monogram, expected)

    def test_colors_are_assigned_in_turn(self):
        wallets = [
            Wallet.objects.create(user=self.user, name=f"Wallet {i}")
            for i in range(len(WALLET_COLORS) + 1)
        ]
        self.assertEqual([w.color for w in wallets[:-1]], WALLET_COLORS)
        self.assertEqual(wallets[-1].color, WALLET_COLORS[0])

    def test_name_is_trimmed(self):
        wallet = Wallet.objects.create(user=self.user, name="  BCA  ")
        self.assertEqual(wallet.name, "BCA")

    def test_active_names_are_unique_per_user_ignoring_case(self):
        Wallet.objects.create(user=self.user, name="GoPay")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Wallet.objects.create(user=self.user, name="gopay")

    def test_other_users_may_use_the_same_name(self):
        Wallet.objects.create(user=self.user, name="BCA")
        Wallet.objects.create(user=make_user("sari@example.com", "Sari"), name="BCA")
        self.assertEqual(Wallet.objects.filter(name="BCA").count(), 2)

    def test_archived_name_can_be_reused(self):
        old = Wallet.objects.create(user=self.user, name="OVO")
        old.archive()
        Wallet.objects.create(user=self.user, name="OVO")
        self.assertEqual(Wallet.objects.filter(name="OVO").count(), 2)

    def test_negative_starting_balance_is_rejected_by_the_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Wallet.objects.create(user=self.user, name="BCA", initial_balance=-1)

    def test_archive_and_restore(self):
        wallet = Wallet.objects.create(user=self.user, name="OVO")
        wallet.archive()
        wallet.refresh_from_db()
        self.assertTrue(wallet.is_archived)
        self.assertIsNotNone(wallet.archived_at)
        wallet.restore()
        wallet.refresh_from_db()
        self.assertFalse(wallet.is_archived)
        self.assertIsNone(wallet.archived_at)

    def test_balance_and_total_of_active_wallets(self):
        Wallet.objects.create(user=self.user, name="BCA", initial_balance=7842500)
        Wallet.objects.create(user=self.user, name="GoPay", initial_balance=647500)
        Wallet.objects.create(user=self.user, name="Cash", type="cash", initial_balance=485000)
        archived = Wallet.objects.create(user=self.user, name="OVO", initial_balance=328000)
        archived.archive()
        Wallet.objects.create(user=make_user("sari@example.com", "Sari"), name="BCA", initial_balance=1)

        mine = Wallet.objects.for_user(self.user)
        self.assertEqual(mine.active().total_balance(), 8975000)
        self.assertEqual(mine.active().with_balance().get(name="BCA").balance, 7842500)
        self.assertEqual(list(mine.archived().values_list("name", flat=True)), ["OVO"])

    def test_total_of_no_wallets_is_zero(self):
        self.assertEqual(Wallet.objects.for_user(self.user).active().total_balance(), 0)


class CategoryModelTests(TestCase):
    def test_nine_defaults_exist(self):
        defaults = Category.objects.filter(user__isnull=True)
        self.assertEqual(defaults.count(), 9)
        self.assertEqual(defaults.expense().count(), 7)
        self.assertEqual(defaults.income().count(), 2)

    def test_expense_defaults_are_in_display_order(self):
        names = list(Category.objects.filter(user__isnull=True).expense().values_list("name", flat=True))
        self.assertEqual(
            names,
            ["Food & drinks", "Shopping", "Transport", "Bills & utilities", "Entertainment", "Health", "Others"],
        )

    def test_income_defaults(self):
        names = list(Category.objects.filter(user__isnull=True).income().values_list("name", flat=True))
        self.assertEqual(names, ["Salary", "Other income"])

    def test_every_default_has_color_and_known_icon(self):
        from core.templatetags.icons import PATHS

        for category in Category.objects.filter(user__isnull=True):
            with self.subTest(category=category.name):
                self.assertRegex(category.color, r"^#[0-9A-F]{6}$")
                self.assertIn(category.icon, PATHS)

    def test_new_user_sees_defaults(self):
        user = make_user()
        self.assertEqual(Category.objects.for_user(user).count(), 9)

    def test_users_do_not_see_each_others_categories(self):
        owner = make_user()
        other = make_user("sari@example.com", "Sari")
        Category.objects.create(user=owner, name="Pets", kind="expense", color="#1F5C4A")
        self.assertIn("Pets", Category.objects.for_user(owner).values_list("name", flat=True))
        self.assertNotIn("Pets", Category.objects.for_user(other).values_list("name", flat=True))

    def test_category_names_are_unique_per_user_and_kind(self):
        owner = make_user()
        Category.objects.create(user=owner, name="Pets", kind="expense", color="#1F5C4A")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Category.objects.create(user=owner, name="pets", kind="expense", color="#1F5C4A")
        # Same name as income is a different category.
        Category.objects.create(user=owner, name="Pets", kind="income", color="#1F5C4A")
