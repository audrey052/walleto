# Changes: polish-and-deploy (MVP 8)

This is the implementation log for this change. It lists what was created or modified, and where the result differs from `proposal.md`, `design.md` and `tasks.md`. Per-commit detail is in `openspec/commits/`.

- **Status:** implemented and not yet archived. The developer deploys by hand with `docs/DEPLOY.md`.
- **Date:** 2026-11-25
- **Tests:** 512 passing, up from 486. The 26 new tests cover settings, the health check, the build script, error pages, the HTMX sign-in redirect and the demo data.
- **Validation:** `openspec validate polish-and-deploy --strict` passes. `makemigrations --check` is clean, and `check --deploy` reports no issues with production values.

## Commits

| Commit | Message | Record |
|---|---|---|
| this commit | feat: production settings, error handling, README and deploy guide | `polish-and-deploy.md` |

## Routes

| Method | URL | Name | Purpose |
|---|---|---|---|
| GET | `/healthz` | `healthz` | Render's health check: "ok", with no sign-in and no database query. Exempt from the HTTPS redirect. |

## Files

| File | Change |
|---|---|
| `config/settings.py` | Reads hosts, trusted origins and `DATABASE_URL` from the environment. An empty `DATABASE_URL` means SQLite. Adds `conn_health_checks` for Neon, WhiteNoise, `STATIC_ROOT`, the HTTPS/HSTS block when `DEBUG` is off, console logging, and an error for an empty `SECRET_KEY`. |
| `config/staticfiles.py` (new) | The staticfiles app without `static/src/` |
| `config/urls.py` | `/healthz` |
| `core/middleware.py` (new) | `HtmxLoginRedirect` |
| `templates/layouts/error.html`, `404.html`, `500.html`, `403_csrf.html` (new) | Error pages |
| `static/js/app.js`, `static/src/app.css`, `templates/base.html` | Error and offline toasts in a popover above modals, and the delayed loading bar. Plan card amounts now show thousands dots (`70.000`) and are tidied again on blur. |
| `core/templatetags/money.py`, `templates/assistant/_card_plan.html` | Adds the `thousands` filter for the plan amounts. |
| `build.sh`, `.python-version` (new) | The Render build: pip, `npm ci`, `css:build`, `collectstatic`, `migrate` |
| `requirements.txt`, `.env.example` | Adds gunicorn, whitenoise, dj-database-url and psycopg; documents every environment value. |
| `.gitignore` | Grouped into sections, and adds `.codeduck/`. |
| `core/tests/` (moved and new) | `tests.py` becomes `tests/test_shell.py` and `test_forms.py` moves into the package. New: `test_settings.py`, `test_deploy.py`, `test_errors.py`. |
| `finance/tests/test_demo.py`, `assistant/tests/test_views.py` | Adds a test that a visitor's changes stay. The signed-out Assistant question from the page now expects the `HX-Redirect`. |
| `accounts/forms.py`, `finance/forms.py`, `core/sections.py`, `static/src/app.css`, `templates/components/progress.html`, `templates/core/styleguide.html`, `templates/finance/wallets.html` | Comments and one style-guide subtitle no longer point at `docs/STYLE.md`, which is not in git. |
| `README.md` | Rewritten in English, for the public. |
| `docs/DEPLOY.md` (new) | The manual Render + Neon guide |
| `docs/screenshots/` (new) | Home, Transactions, Budget, Savings goals, Assistant and the phone view, taken from a copy of the local database |

## Differences from the plan

- **Scope was trimmed partway, at the developer's request.** The developer asked for a manual deploy guide and a focus on the repository and the README. So:
  - `render.yaml` was written and then removed;
  - the demo assistant limits, per-visitor demo conversations and the 390px empty-account pass were moved to a later change.

  The proposal, design, specs and tasks were updated before continuing.
- **Render's free plan has no shell.** Rerunning `seed_demo` therefore happens from the developer's machine against the Neon URL.
- **Found while testing, and not planned:**
  - `collectstatic` failed on the Tailwind source, fixed by `config/staticfiles.py`;
  - an empty `DATABASE_URL` copied from `.env.example` broke a fresh setup, fixed in settings and covered by a test;
  - the error toast was hidden behind modals, because native `<dialog>` sits in the top layer; fixed with a popover container;
  - the plan card showed raw `70000`.
- **`npm ci` was not run inside the working copy.** It failed with EPERM, because the developer's `css:watch` process held a native module open, and it partly emptied `node_modules`. That was restored with `npm install`; the lockfile is unchanged. Instead, `npm ci` was verified on a copy of `package.json` and the lockfile, and a fresh copy of the repository was set up by following the README.
