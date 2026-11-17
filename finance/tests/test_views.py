from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from finance.models import Wallet

User = get_user_model()
HTMX = {"HTTP_HX_REQUEST": "true"}


def make_user(email="aditya@example.com", name="Aditya Ramadhan"):
    return User.objects.create_user(email=email, password="quiet-ledger-2026", full_name=name)


class WalletTestCase(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)
        self.list_url = reverse("finance:wallets")
        self.create_url = reverse("finance:wallet_create")

    def wallet(self, name="BCA", balance=0, user=None, **kwargs):
        return Wallet.objects.create(
            user=user or self.user, name=name, initial_balance=balance, **kwargs
        )


class WalletListTests(WalletTestCase):
    def test_empty_state(self):
        response = self.client.get(self.list_url)
        self.assertContains(response, "Add your first wallet")
        self.assertNotContains(response, "Total balance")

    def test_total_and_rows_of_active_wallets(self):
        self.wallet("BCA", 7842500)
        self.wallet("GoPay", 647500, type="ewallet")
        self.wallet("Cash", 485000, type="cash")
        self.wallet("OVO", 328000).archive()
        response = self.client.get(self.list_url)
        self.assertEqual(response.context["total_balance"], 8975000)
        self.assertContains(response, "Rp</span>8.975.000")
        self.assertEqual([w.name for w in response.context["wallets"]], ["BCA", "GoPay", "Cash"])
        self.assertContains(response, "Across 3 wallets")
        self.assertContains(response, "Archived wallets (1)")

    def test_shows_only_own_wallets(self):
        self.wallet("BCA", 100)
        self.wallet("Mandiri", 999, user=make_user("sari@example.com", "Sari"))
        response = self.client.get(self.list_url)
        self.assertContains(response, "BCA")
        self.assertNotContains(response, "Mandiri")
        self.assertEqual(response.context["total_balance"], 100)

    def test_type_label_rendered(self):
        self.wallet("Dompet", type="cash")
        response = self.client.get(self.list_url)
        self.assertContains(response, "Cash")

    def test_wallets_is_the_active_section_on_every_wallet_page(self):
        wallet = self.wallet()
        for url in [
            self.list_url,
            self.create_url,
            reverse("finance:wallet_edit", args=[wallet.pk]),
            reverse("finance:wallet_archive", args=[wallet.pk]),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).context["active_section"]["key"], "wallets")

    def test_visitors_are_sent_to_sign_in(self):
        self.client.logout()
        response = self.client.get(self.list_url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.list_url}")


class WalletCreateTests(WalletTestCase):
    def post(self, htmx=False, **data):
        payload = {"name": "BCA", "type": "bank", "initial_balance": "7.842.500"}
        payload.update(data)
        return self.client.post(self.create_url, payload, **(HTMX if htmx else {}))

    def test_htmx_get_returns_modal_fragment(self):
        response = self.client.get(self.create_url, **HTMX)
        self.assertContains(response, "<dialog")
        self.assertNotContains(response, "<html")

    def test_plain_get_returns_full_page(self):
        response = self.client.get(self.create_url)
        self.assertContains(response, "<html")
        self.assertContains(response, "Add wallet")

    def test_htmx_create_redirects_with_toast(self):
        response = self.post(htmx=True)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response["HX-Redirect"], self.list_url)
        wallet = Wallet.objects.get(user=self.user)
        self.assertEqual((wallet.name, wallet.type, wallet.initial_balance), ("BCA", "bank", 7842500))
        page = self.client.get(self.list_url)
        self.assertContains(page, "Wallet added.")
        self.assertContains(page, "Rp</span>7.842.500")

    def test_plain_create_redirects(self):
        response = self.post()
        self.assertRedirects(response, self.list_url, fetch_redirect_response=False)
        self.assertTrue(Wallet.objects.filter(user=self.user, name="BCA").exists())

    def test_empty_balance_means_zero(self):
        self.post(initial_balance="")
        self.assertEqual(Wallet.objects.get(user=self.user).initial_balance, 0)

    def test_missing_name_keeps_modal_open_with_values(self):
        response = self.post(htmx=True, name="   ", initial_balance="2.500.000")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<dialog")
        self.assertContains(response, "Enter a name for this wallet.")
        self.assertContains(response, 'value="2.500.000"')
        self.assertFalse(Wallet.objects.exists())

    def test_duplicate_name_ignoring_case(self):
        self.wallet("GoPay")
        response = self.post(name="gopay")
        self.assertContains(response, "You already have a wallet with this name.")
        self.assertEqual(Wallet.objects.count(), 1)

    def test_archived_name_can_be_reused(self):
        self.wallet("OVO").archive()
        self.post(name="OVO")
        self.assertEqual(Wallet.objects.filter(name="OVO", is_archived=False).count(), 1)

    def test_negative_balance(self):
        response = self.post(initial_balance="-1.000")
        self.assertContains(response, "Amount cannot be negative.")
        self.assertFalse(Wallet.objects.exists())

    def test_balance_not_a_number(self):
        response = self.post(initial_balance="dua juta")
        self.assertContains(response, "Enter an amount in Rupiah, for example 2.500.000.")
        self.assertFalse(Wallet.objects.exists())

    def test_wallet_belongs_to_the_signed_in_user(self):
        other = make_user("sari@example.com", "Sari")
        self.post(user=other.pk)  # extra fields are ignored
        self.assertEqual(Wallet.objects.get().user, self.user)


class WalletEditTests(WalletTestCase):
    def test_rename(self):
        wallet = self.wallet("BCA", 100)
        url = reverse("finance:wallet_edit", args=[wallet.pk])
        response = self.client.post(
            url, {"name": "BCA Tahapan", "type": "bank", "initial_balance": "100"}, **HTMX
        )
        self.assertEqual(response["HX-Redirect"], self.list_url)
        wallet.refresh_from_db()
        self.assertEqual(wallet.name, "BCA Tahapan")
        self.assertContains(self.client.get(self.list_url), "Wallet updated.")

    def test_keeping_the_same_name_is_not_a_duplicate(self):
        wallet = self.wallet("BCA", 100)
        url = reverse("finance:wallet_edit", args=[wallet.pk])
        response = self.client.post(url, {"name": "bca", "type": "bank", "initial_balance": "250"})
        self.assertRedirects(response, self.list_url, fetch_redirect_response=False)
        wallet.refresh_from_db()
        self.assertEqual((wallet.name, wallet.initial_balance), ("bca", 250))

    def test_renaming_to_another_active_wallet_is_refused(self):
        self.wallet("GoPay")
        wallet = self.wallet("OVO")
        url = reverse("finance:wallet_edit", args=[wallet.pk])
        response = self.client.post(url, {"name": "GOPAY", "type": "ewallet", "initial_balance": "0"})
        self.assertContains(response, "You already have a wallet with this name.")

    def test_form_shows_current_values(self):
        wallet = self.wallet("BCA", 7842500)
        response = self.client.get(reverse("finance:wallet_edit", args=[wallet.pk]), **HTMX)
        self.assertContains(response, 'value="BCA"')
        self.assertContains(response, 'value="7.842.500"')


class WalletArchiveRestoreTests(WalletTestCase):
    def test_get_shows_confirmation_and_changes_nothing(self):
        wallet = self.wallet("OVO")
        response = self.client.get(reverse("finance:wallet_archive", args=[wallet.pk]), **HTMX)
        self.assertContains(response, "Archive OVO?")
        wallet.refresh_from_db()
        self.assertFalse(wallet.is_archived)

    def test_archive_hides_from_cards_and_total(self):
        self.wallet("BCA", 1000)
        ovo = self.wallet("OVO", 500)
        response = self.client.post(reverse("finance:wallet_archive", args=[ovo.pk]), **HTMX)
        self.assertEqual(response["HX-Redirect"], self.list_url)
        page = self.client.get(self.list_url)
        self.assertEqual([w.name for w in page.context["wallets"]], ["BCA"])
        self.assertEqual(page.context["total_balance"], 1000)
        self.assertEqual([w.name for w in page.context["archived_wallets"]], ["OVO"])
        self.assertContains(page, "OVO archived.")

    def test_restore(self):
        ovo = self.wallet("OVO", 500)
        ovo.archive()
        response = self.client.post(reverse("finance:wallet_restore", args=[ovo.pk]))
        self.assertRedirects(response, self.list_url, fetch_redirect_response=False)
        page = self.client.get(self.list_url)
        self.assertEqual(page.context["total_balance"], 500)
        self.assertContains(page, "OVO restored.")

    def test_restore_blocked_by_active_name(self):
        old = self.wallet("OVO")
        old.archive()
        self.wallet("ovo")
        self.client.post(reverse("finance:wallet_restore", args=[old.pk]))
        old.refresh_from_db()
        self.assertTrue(old.is_archived)
        page = self.client.get(self.list_url)
        self.assertContains(page, "You already have an active wallet named OVO.")

    def test_restore_requires_post(self):
        ovo = self.wallet("OVO")
        ovo.archive()
        response = self.client.get(reverse("finance:wallet_restore", args=[ovo.pk]))
        self.assertEqual(response.status_code, 405)
        ovo.refresh_from_db()
        self.assertTrue(ovo.is_archived)


class WalletPrivacyTests(WalletTestCase):
    def setUp(self):
        super().setUp()
        self.other = make_user("sari@example.com", "Sari")
        self.theirs = self.wallet("Mandiri", 999, user=self.other)

    def test_edit_another_users_wallet(self):
        url = reverse("finance:wallet_edit", args=[self.theirs.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        response = self.client.post(url, {"name": "Hacked", "type": "bank", "initial_balance": "0"})
        self.assertEqual(response.status_code, 404)
        self.theirs.refresh_from_db()
        self.assertEqual(self.theirs.name, "Mandiri")

    def test_archive_another_users_wallet(self):
        url = reverse("finance:wallet_archive", args=[self.theirs.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.theirs.refresh_from_db()
        self.assertFalse(self.theirs.is_archived)

    def test_restore_another_users_wallet(self):
        self.theirs.archive()
        url = reverse("finance:wallet_restore", args=[self.theirs.pk])
        self.assertEqual(self.client.post(url).status_code, 404)
        self.theirs.refresh_from_db()
        self.assertTrue(self.theirs.is_archived)
