"""deployment spec: the health check."""

from django.test import TestCase, override_settings


class HealthCheckTests(TestCase):
    def test_signed_out_and_no_database(self):
        with self.assertNumQueries(0):
            response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")
        self.assertEqual(response["Content-Type"], "text/plain")

    @override_settings(SECURE_SSL_REDIRECT=True, SECURE_REDIRECT_EXEMPT=[r"^healthz$"], DEBUG=False)
    def test_plain_http_probe_with_production_security(self):
        self.assertEqual(self.client.get("/healthz").status_code, 200)
        # Everything else is redirected to HTTPS.
        response = self.client.get("/sign-in/")
        self.assertEqual(response.status_code, 301)
        self.assertTrue(response["Location"].startswith("https://"))

    @override_settings(ALLOWED_HOSTS=["walleto.example.com"], DEBUG=False)
    def test_unknown_host(self):
        self.assertEqual(self.client.get("/sign-in/", HTTP_HOST="evil.example.com").status_code, 400)


class DeployFilesTests(TestCase):
    """deployment spec, "Repeatable deploy": the build script and example settings."""

    def read(self, name):
        from django.conf import settings

        return (settings.BASE_DIR / name).read_text(encoding="utf-8")

    def test_build_steps_in_order(self):
        text = self.read("build.sh")
        steps = ["pip install -r requirements.txt", "npm ci", "npm run css:build",
                 "manage.py collectstatic --no-input", "manage.py migrate --no-input"]
        positions = [text.index(step) for step in steps]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("set -o errexit", text)

    def test_demo_is_never_seeded_by_a_deploy(self):
        # demo-account spec, "Demo data is created once".
        self.assertNotIn("seed_demo", self.read("build.sh"))

    def test_example_env_has_no_real_connection_string(self):
        text = self.read(".env.example")
        self.assertIn("DATABASE_URL=\n", text)
        self.assertNotRegex(text, r"postgresql://[^<]")


class HtmxSignInRedirectTests(TestCase):
    """app-shell spec, "Expired session during an action"."""

    def test_htmx_request_after_sign_out(self):
        response = self.client.get("/transactions/?wallet=3", HTTP_HX_REQUEST="true",
                                   HTTP_HX_CURRENT_URL="http://testserver/transactions/?month=2026-11")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response["HX-Redirect"], "/sign-in/?next=%2Ftransactions%2F%3Fmonth%3D2026-11")

    def test_without_current_url(self):
        response = self.client.post("/transactions/new/", HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response["HX-Redirect"], "/sign-in/?next=%2F")

    def test_normal_request_still_redirects(self):
        response = self.client.get("/transactions/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/sign-in/?next=/transactions/")

    def test_other_htmx_redirects_untouched(self):
        from finance.tests.test_views import make_user

        self.client.force_login(make_user())
        # Signing in again while signed in redirects to Home, not to sign-in: left alone.
        response = self.client.get("/sign-in/", HTTP_HX_REQUEST="true")
        self.assertNotIn("HX-Redirect", response)
        self.assertEqual(response.status_code, 302)

    def test_signing_in_returns_to_the_page(self):
        from finance.tests.test_views import make_user

        make_user()
        response = self.client.post("/sign-in/?next=%2Ftransactions%2F%3Fmonth%3D2026-11", {
            "username": "aditya@example.com", "password": "quiet-ledger-2026", "next": "/transactions/?month=2026-11"})
        self.assertEqual(response["Location"], "/transactions/?month=2026-11")
