# Production Settings, Error Handling, README and Deploy Guide

**Created:** 2026-11-25
**Last edited:** 2026-11-25
**Status:** Implemented
**Commit:** this commit
**Branch:** `main`, parent `eedb4f7`
**OpenSpec change:** `polish-and-deploy` (MVP 8)
**Trigger:** The developer asked to continue with MVP 8 in one change: Render with a Neon database instead of Render's PostgreSQL, and demo data that is not reset. Partway through, the developer asked for a manual deploy guide and a focus on preparing and tidying the repository and the README.

## Why this is recorded here

This is the last milestone before the project goes public. The record says what is ready, what the developer does by hand, and what was deferred.

## What is built

| Area | Change |
|---|---|
| Production settings | Everything comes from the environment. `DATABASE_URL` points to Neon in production; when it is missing or empty, SQLite is used. With `DEBUG` off: HTTPS redirect, secure cookies, HSTS for 1 hour, and WhiteNoise serving fingerprinted static files. `check --deploy` is clean. |
| Health check | `/healthz` returns "ok" without sign-in or database access. |
| Build | `build.sh`: pip, `npm ci`, `css:build`, `collectstatic`, `migrate`. `.python-version` pins 3.11.9. |
| Deploy guide | `docs/DEPLOY.md` covers Neon in Singapore with the direct connection string, and the Render web service by hand, with a table of every environment value. It also has a first-deploy checklist, how to update and roll back, how to refresh the demo data from the developer's machine, the free-plan limits and troubleshooting. |
| Error pages | "Page not found", "Something went wrong" and "This form has expired", with no app shell and no database use. |
| Failed requests | A toast says "Something went wrong. Try again." on a server error and "You're offline…" when the connection is lost. Modals keep what was typed, and the toast shows above `<dialog>` modals. |
| Expired session | An HTMX request goes to the sign-in page as a full page, then returns to the page the user was on. |
| Loading | A 2px bar at the top appears after 300ms. |
| Plan card | Amounts show thousands dots. |
| Repository | `.gitignore` regrouped; `core` tests moved to `core/tests/`; no comments pointing at local-only files; README in English with screenshots, Mermaid diagrams (tool flow, data model), the evaluation result, local setup, deploy link and project structure. |

## Requirements this establishes

1. **Configuration from the environment, Secure when debugging is off, Static files in production, Health check and Repeatable deploy**, in the new `deployment` spec.
2. **Error pages, Failed requests in place, Expired session during an action and Loading indicator**, in `app-shell`.
3. **Demo data is created once**, in `demo-account`.

## Files changed

See `openspec/changes/polish-and-deploy/changes.md` for the full table. In short:
- **Configuration:** `config/` (settings, staticfiles, urls).
- **Backend:** `core/middleware.py`, `core/templatetags/money.py`.
- **Templates:** the error templates, `base.html` and the plan card.
- **Frontend:** `static/js/app.js` and `static/src/app.css`.
- **Build and settings files:** `build.sh`, `.python-version`, `requirements.txt`, `.env.example` and `.gitignore`.
- **Tests:** `core/tests/` (moved and new), `finance/tests/test_demo.py` and `assistant/tests/test_views.py`.
- **Documentation:** `README.md`, `docs/DEPLOY.md` and `docs/screenshots/`.
- **Records:** `openspec/commits/README.md`, plus `sign-in-footer-and-password-eye.md` with `eedb4f7` filled in.

## Verification

**Executed:**

- `python manage.py test`: 512 tests OK. `makemigrations --check`: no changes. `openspec validate polish-and-deploy --strict`: valid.
- With production values, `check --deploy` reports no issues.
- With `DEBUG=False`, `collectstatic` copies 136 files and post-processes 406, giving fingerprinted `app.<hash>.css`, with the fonts rewritten inside it.
- `build.sh` runs to the end against SQLite, with `npm install` in place of `npm ci`. `npm ci` itself was verified on a copy of the package files, and `config.wsgi` imports.
- A fresh copy of the repository, set up by following the README: a new venv, `pip install`, `.env` copied from the example, `migrate`, `seed_demo`, `npm install`, `css:build` and all tests pass. `/sign-in/` and the CSS both return 200.
- Edge headless, with a temporary QA user that was deleted afterwards:
  - **Forced 500 on saving a transaction:** the toast shows above the modal, and the modal keeps "Kopi Kenangan".
  - **Offline filter change:** the offline toast shows, and the list is unchanged.
  - **Loading bar:** opacity 0 at 120ms on a fast request, and 1 at 700ms on a 1-second request.
  - **Expired session:** after signing out elsewhere, a filter change lands on `/sign-in/?next=/transactions/?month=2026-11`, and signing in returns there.
- The screenshots were taken on a copy of the database, with the demo reseeded for today and one real Assistant question asked, so the real demo is untouched.

**Not executed:**

- **The real deploy on Render and Neon.** The developer does this following `docs/DEPLOY.md`.
- **`gunicorn` running for real.** It does not run on Windows; Render runs it.

## Known gaps

- **Deferred to a later change:**
  - demo assistant limits per visitor and in total (the shared demo user currently has 30 questions a day);
  - per-visitor demo conversations (demo visitors share the demo's History);
  - the 390px pass with an empty account.
- **Demo data is not reset automatically**, so it ages. The developer reruns `seed_demo` against Neon.
- **The live demo link in the README is a placeholder** until the first deploy.
