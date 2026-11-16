from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

User = get_user_model()

STRONG_PASSWORD = "quiet-ledger-2026"


class UserModelTests(TestCase):
    def test_create_user_without_username(self):
        user = User.objects.create_user(
            email="aditya@example.com", password=STRONG_PASSWORD, full_name="Aditya Ramadhan"
        )
        self.assertEqual(user.email, "aditya@example.com")
        self.assertTrue(user.check_password(STRONG_PASSWORD))
        self.assertFalse(user.is_staff)
        self.assertFalse(hasattr(user, "username") and user.username)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email="admin@example.com", password=STRONG_PASSWORD, full_name="Admin"
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_email_is_saved_lowercased(self):
        user = User.objects.create_user(
            email="Aditya.R@Example.COM", password=STRONG_PASSWORD, full_name="Aditya"
        )
        self.assertEqual(user.email, "aditya.r@example.com")

    def test_duplicate_email_in_different_case_is_rejected(self):
        User.objects.create_user(email="aditya@example.com", password=STRONG_PASSWORD, full_name="A")
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email="ADITYA@example.com", password=STRONG_PASSWORD, full_name="B"
            )

    def test_initials(self):
        self.assertEqual(User(full_name="Aditya Ramadhan", email="a@x.com").initials, "AR")
        self.assertEqual(User(full_name="Sari", email="s@x.com").initials, "SA")
        self.assertEqual(User(full_name="Budi Santoso Putra", email="b@x.com").initials, "BP")


class RegistrationTests(TestCase):
    url = reverse("accounts:register")

    def post(self, **overrides):
        data = {
            "full_name": "Aditya Ramadhan",
            "email": "aditya@example.com",
            "password1": STRONG_PASSWORD,
            "password2": STRONG_PASSWORD,
        }
        data.update(overrides)
        return self.client.post(self.url, data)

    def test_success_creates_account_and_signs_in(self):
        response = self.post()
        # Don't fetch the target here: that would consume the one-time toast message.
        self.assertRedirects(response, reverse("core:dashboard"), fetch_redirect_response=False)
        self.assertTrue(User.objects.filter(email="aditya@example.com").exists())
        page = self.client.get(reverse("core:dashboard"))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Account created")

    def test_duplicate_email_any_case(self):
        User.objects.create_user(email="aditya@example.com", password=STRONG_PASSWORD, full_name="A")
        response = self.post(email="Aditya@Example.com")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "An account with this email already exists.")
        self.assertEqual(User.objects.count(), 1)

    def test_mismatched_passwords_keep_name_and_email(self):
        response = self.post(password2="something-else-2026")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.exists())
        self.assertIn("password2", response.context["form"].errors)
        self.assertContains(response, 'value="Aditya Ramadhan"')
        self.assertContains(response, 'value="aditya@example.com"')

    def test_weak_password(self):
        response = self.post(password1="password", password2="password")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.exists())
        self.assertIn("password2", response.context["form"].errors)


class SignInTests(TestCase):
    url = reverse("accounts:login")

    def setUp(self):
        User.objects.create_user(
            email="aditya@example.com", password=STRONG_PASSWORD, full_name="Aditya Ramadhan"
        )

    def test_valid_credentials_any_email_case(self):
        response = self.client.post(
            self.url, {"username": "ADITYA@Example.com", "password": STRONG_PASSWORD}
        )
        self.assertRedirects(response, reverse("core:dashboard"))

    def test_wrong_password_shows_generic_error(self):
        response = self.client.post(
            self.url, {"username": "aditya@example.com", "password": "wrong-password"}
        )
        self.assertContains(response, "Email or password is incorrect.")

    def test_unknown_email_shows_same_generic_error(self):
        response = self.client.post(
            self.url, {"username": "nobody@example.com", "password": STRONG_PASSWORD}
        )
        self.assertContains(response, "Email or password is incorrect.")

    def test_external_next_address_is_ignored(self):
        response = self.client.post(
            f"{self.url}?next=https://evil.example.com/",
            {
                "username": "aditya@example.com",
                "password": STRONG_PASSWORD,
                "next": "https://evil.example.com/",
            },
        )
        self.assertRedirects(response, reverse("core:dashboard"))


class AccessTests(TestCase):
    section_urls = [
        "core:dashboard",
        "core:transactions",
        "finance:wallets",
        "core:budget",
        "core:savings",
        "core:assistant",
    ]

    def setUp(self):
        self.user = User.objects.create_user(
            email="aditya@example.com", password=STRONG_PASSWORD, full_name="Aditya Ramadhan"
        )

    def test_visitors_are_sent_to_sign_in(self):
        for name in self.section_urls:
            with self.subTest(page=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}")

    def test_returns_to_requested_page_after_sign_in(self):
        budget = reverse("core:budget")
        response = self.client.post(
            f"{reverse('accounts:login')}?next={budget}",
            {"username": "aditya@example.com", "password": STRONG_PASSWORD, "next": budget},
        )
        self.assertRedirects(response, budget)

    def test_signed_in_user_skips_sign_in_and_register(self):
        self.client.force_login(self.user)
        for name in ["accounts:login", "accounts:register"]:
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertRedirects(response, reverse("core:dashboard"))


class SignOutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="aditya@example.com", password=STRONG_PASSWORD, full_name="Aditya Ramadhan"
        )
        self.client.force_login(self.user)

    def test_get_does_not_sign_out(self):
        response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 405)
        self.assertEqual(self.client.get(reverse("core:dashboard")).status_code, 200)

    def test_post_signs_out(self):
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))
        dashboard = reverse("core:dashboard")
        self.assertRedirects(
            self.client.get(dashboard), f"{reverse('accounts:login')}?next={dashboard}"
        )
