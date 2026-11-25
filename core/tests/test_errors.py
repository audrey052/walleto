"""app-shell spec: error pages. Also the test URLconf (a view that raises) used by these tests."""

from datetime import date

from django.db import connection
from django.test import Client, TestCase, override_settings
from django.urls import include, path, reverse

from finance.models import Transaction, Wallet
from finance.tests.test_summary import category
from finance.tests.test_views import make_user


def boom(request):
    raise RuntimeError("secret detail in a traceback")


urlpatterns = [path("boom/", boom), path("", include("config.urls"))]


@override_settings(DEBUG=False)
class ErrorPageTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def test_unknown_address(self):
        response = self.client.get("/no-such-page/")
        self.assertContains(response, "Page not found</h1>", status_code=404)
        self.assertContains(response, 'href="/"', status_code=404)
        self.assertContains(response, "Go to Home", status_code=404)

    def test_unknown_address_signed_out(self):
        self.client.logout()
        # An address that matches no page is "Page not found" for everyone; the Home link then asks to sign in.
        self.assertContains(self.client.get("/no-such-page/"), "Page not found</h1>", status_code=404)

    def test_another_users_item(self):
        other = make_user(email="other@example.com", name="Other")
        wallet = Wallet.objects.create(user=other, name="Other BCA")
        tx = Transaction.objects.create(user=other, wallet=wallet, category=category("Food & drinks"),
                                        amount=10_000, date=date(2026, 11, 1), description="Theirs")
        response = self.client.get(reverse("finance:transaction_edit", args=[tx.pk]))
        self.assertContains(response, "Page not found", status_code=404)
        self.assertNotContains(response, "Theirs", status_code=404)

    @override_settings(ROOT_URLCONF="core.tests.test_errors")
    def test_server_error(self):
        client = Client(raise_request_exception=False)
        client.force_login(self.user)
        response = client.get("/boom/")
        self.assertContains(response, "Something went wrong</h1>", status_code=500)
        self.assertNotContains(response, "secret detail", status_code=500)
        self.assertNotContains(response, "Traceback", status_code=500)

    @override_settings(ROOT_URLCONF="core.tests.test_errors")
    def test_server_error_without_database(self):
        from django.test import RequestFactory
        from django.views.defaults import server_error

        connection.close()
        with self.assertNumQueries(0):
            response = server_error(RequestFactory().get("/boom/"))
        self.assertEqual(response.status_code, 500)
        self.assertIn(b"Something went wrong", response.content)

    def test_stale_form(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post(reverse("finance:transaction_create"), {"description": "x"})
        self.assertContains(response, "This form has expired</h1>", status_code=403)
        self.assertContains(response, "reload the page and try again", status_code=403)
