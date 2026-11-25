"""Static files app that leaves sources out of collectstatic (polish-and-deploy design decision 3)."""

from django.contrib.staticfiles.apps import StaticFilesConfig


class WalletoStaticFilesConfig(StaticFilesConfig):
    # static/src/ holds the Tailwind source; only the built static/css/app.css is served.
    ignore_patterns = [*StaticFilesConfig.ignore_patterns, "src/*", "src"]
