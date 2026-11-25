"""deployment spec: configuration from the environment and production security.

Settings are read once at import, so each case loads them in a fresh Python process.
"""

import json
import os
import subprocess
import sys

from django.conf import settings
from django.test import SimpleTestCase

PRINT = """
import json, django
django.setup()
from django.conf import settings as s
db = s.DATABASES["default"]
print(json.dumps({
    "hosts": s.ALLOWED_HOSTS, "origins": s.CSRF_TRUSTED_ORIGINS,
    "engine": db["ENGINE"], "name": str(db["NAME"]), "options": db.get("OPTIONS", {}),
    "health": db.get("CONN_HEALTH_CHECKS"), "age": db.get("CONN_MAX_AGE"),
    "ssl_redirect": getattr(s, "SECURE_SSL_REDIRECT", False), "hsts": getattr(s, "SECURE_HSTS_SECONDS", 0),
    "secure_cookies": [s.SESSION_COOKIE_SECURE, s.CSRF_COOKIE_SECURE],
    "storage": s.STORAGES["staticfiles"]["BACKEND"],
}))
"""

SECRET = "x" * 50


def load(**env):
    """Settings as seen by a process started with exactly these deployment values."""
    base = {k: v for k, v in os.environ.items() if k not in {
        "ALLOWED_HOSTS", "DATABASE_URL", "RENDER_EXTERNAL_HOSTNAME", "DEBUG", "SECRET_KEY"}}
    base.update({"DJANGO_SETTINGS_MODULE": "config.settings", "SECRET_KEY": SECRET, "DEBUG": "False"})
    base.update(env)
    result = subprocess.run([sys.executable, "-c", PRINT], env=base, cwd=settings.BASE_DIR,
                            capture_output=True, text=True, timeout=60)
    if result.returncode:
        return {"error": result.stderr}
    return json.loads(result.stdout.strip().splitlines()[-1])


class EnvironmentSettingsTests(SimpleTestCase):
    def test_hosts_and_trusted_origins(self):
        s = load(ALLOWED_HOSTS="walleto.example.com, www.walleto.example.com", RENDER_EXTERNAL_HOSTNAME="walleto.onrender.com")
        self.assertEqual(s["hosts"], ["walleto.example.com", "www.walleto.example.com", "walleto.onrender.com"])
        self.assertEqual(s["origins"], ["https://walleto.example.com", "https://www.walleto.example.com", "https://walleto.onrender.com"])

    def test_neon_database_url(self):
        s = load(DATABASE_URL="postgresql://u:p@ep-x.ap-southeast-1.aws.neon.tech/walleto?sslmode=require")
        self.assertEqual(s["engine"], "django.db.backends.postgresql")
        self.assertEqual(s["name"], "walleto")
        self.assertEqual(s["options"], {"sslmode": "require"})
        self.assertTrue(s["health"])
        self.assertEqual(s["age"], 600)

    def test_sqlite_by_default(self):
        s = load()
        self.assertEqual(s["engine"], "django.db.backends.sqlite3")
        self.assertTrue(s["name"].endswith("db.sqlite3"))

    def test_empty_database_url_means_sqlite(self):
        # .env.example ships `DATABASE_URL=` empty; copying it must still give a working local setup.
        s = load(DATABASE_URL="")
        self.assertEqual(s["engine"], "django.db.backends.sqlite3")

    def test_production_security(self):
        s = load(ALLOWED_HOSTS="walleto.example.com")
        self.assertTrue(s["ssl_redirect"])
        self.assertEqual(s["hsts"], 3600)
        self.assertEqual(s["secure_cookies"], [True, True])
        self.assertEqual(s["storage"], "whitenoise.storage.CompressedManifestStaticFilesStorage")

    def test_local_debug(self):
        s = load(DEBUG="True")
        self.assertIn("localhost", s["hosts"])
        self.assertEqual(s["origins"], [])
        self.assertFalse(s["ssl_redirect"])

    def test_missing_secret(self):
        s = load(SECRET_KEY="")
        # An empty SECRET_KEY is refused by Django as soon as settings are used.
        self.assertIn("SECRET_KEY", s.get("error", ""))

    def test_deploy_check_is_clean(self):
        env = {k: v for k, v in os.environ.items() if k not in {"DATABASE_URL", "DEBUG"}}
        env.update({"SECRET_KEY": "k3$" + "a9Zq" * 15, "DEBUG": "False", "ALLOWED_HOSTS": "walleto.example.com"})
        result = subprocess.run([sys.executable, "manage.py", "check", "--deploy", "--fail-level", "WARNING"],
                                env=env, cwd=settings.BASE_DIR, capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
