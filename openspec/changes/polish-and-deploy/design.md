# Design

## Context

- **Settings** (`config/settings.py`):
  - The secret key and the debug flag already come from `.env`. `DEBUG` defaults to False.
  - `ALLOWED_HOSTS` is empty, the database is always SQLite, and nothing serves static files when debugging is off.
- **CSS:** `static/css/` is gitignored. The stylesheet is built from `static/src/app.css` by Tailwind v4 (`npm run css:build`), so every deploy has to run Node.
- **Missing pieces:** there are no 404, 500 or 403 templates. `static/js/app.js` does not handle `htmx:responseError` or `htmx:sendError`.
- **Sign-in:** every view requires sign-in through Django's `LoginRequiredMiddleware`. An HTMX request made after the session ends receives the redirect, follows it, and swaps the sign-in page into its target.
- **Assistant usage:** the usage limit counts the user's counted questions today, with `ASSISTANT_DAILY_LIMIT = 30`. For the shared demo user this already caps model calls at 30 a day.
- **Demo account:** it is one shared user. `accounts.views.demo_sign_in` creates its data when the demo user has no wallets.

## Goals / Non-Goals

**Goals:**
- A developer who has never used Render or Neon can deploy by following `docs/DEPLOY.md` alone.
- `python manage.py check --deploy` is clean with production environment values.
- The repository reads well to a stranger: an English README, no stray files, consistent test layout.

**Non-Goals:**
- A separate settings module per environment.
- Docker, a Render blueprint, background workers, cron jobs and caching.
- The demo limits and per-visitor demo conversations. They are deferred (see proposal, Out of scope).

## Decisions

### 1. One settings file driven by environment variables
`settings.py` keeps a single path:
- `ALLOWED_HOSTS` comes from `ALLOWED_HOSTS`, a comma-separated list. Render's own `RENDER_EXTERNAL_HOSTNAME` is added automatically, and `localhost`/`127.0.0.1` are added when `DEBUG` is on.
- `CSRF_TRUSTED_ORIGINS` is derived as `https://<host>` for each non-local host.
- When `DEBUG` is off, the security block turns on:
  - `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`, because Render ends TLS at its proxy;
  - `SECURE_SSL_REDIRECT`;
  - `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE`;
  - `SECURE_HSTS_SECONDS = 3600`, raised later once the site is known to be stable; no preload;
  - `SECURE_REFERRER_POLICY`.
- `/healthz` is exempt from the SSL redirect, because Render probes over plain HTTP.

*Rejected:* split `settings/base.py`, `dev.py` and `prod.py` modules. They need a `DJANGO_SETTINGS_MODULE` per environment and duplicate most values, while the environment variables already express the difference.

### 2. Neon PostgreSQL through `dj-database-url` and `psycopg`
`DATABASES = {"default": dj_database_url.config(default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}", conn_max_age=600, conn_health_checks=True)}`. `psycopg[binary]` provides the PostgreSQL driver with no system libraries, so it also installs on Windows.

The database is a Neon free project in `ap-southeast-1` (Singapore). The web service runs in Render's Singapore region too, so each query is a short hop.
- **Connection string:** `DATABASE_URL` is Neon's **direct** connection string (host without `-pooler`), which includes `sslmode=require`.
- **No Neon pooler:** with 2 gunicorn workers and persistent connections the app needs at most a handful of connections, well within Neon's limit. The pooler (PgBouncer in transaction mode) would also need `DISABLE_SERVER_SIDE_CURSORS`.
- **Health checks on connections:** `conn_health_checks` replaces a connection that Neon closed while its compute was suspended, instead of failing the first request after a quiet period.

*Rejected:*
- **Render's free PostgreSQL:** it is deleted after 30 days, which would wipe the demo and any registered accounts.
- **Supabase:** it also has a free plan, but it pauses projects after a week without activity and they need a manual restore. Neon only suspends compute and wakes it on the next connection.
- **Parsing the URL by hand:** it is easy to get subtly wrong with special characters in passwords, for one small dependency saved.

### 3. WhiteNoise with fingerprinted file names
WhiteNoise middleware sits right after `SecurityMiddleware`. `STORAGES["staticfiles"]` uses `whitenoise.storage.CompressedManifestStaticFilesStorage`, and `STATIC_ROOT = BASE_DIR / "staticfiles"` (already gitignored). Tests and local debugging use the plain storage, so they do not need a collected manifest. `config/staticfiles.py` replaces `django.contrib.staticfiles` with the same app plus `ignore_patterns` for `static/src/`. Otherwise the manifest storage tries to post-process the Tailwind source and its unresolved `url()` imports, and `collectstatic` fails.

*Rejected:*
- serving static files from a CDN or S3, which means another account and another setup step for a small app;
- Django's `--insecure` static serving, which is not meant for production.

### 4. Manual Render setup from a guide, with one build script
The developer creates the services by hand, following `docs/DEPLOY.md`:
- **Neon:** a project in `ap-southeast-1`; copy the **direct** connection string.
- **Render web service:**
  - from the GitHub repository, runtime Python, region Singapore, free plan;
  - build command `./build.sh`;
  - start command `gunicorn config.wsgi --workers 2 --timeout 60 --access-logfile -`;
  - health check path `/healthz`;
  - environment values:
    - `PYTHON_VERSION=3.11.9` (also in `.python-version`) and `NODE_VERSION=22`;
    - `DEBUG=False`;
    - `SECRET_KEY` (a long random value; the guide shows a one-line generator);
    - `DATABASE_URL` from Neon;
    - `OPENAI_API_KEY`, `OPENAI_MODEL` and `OPENAI_REASONING_EFFORT`;
    - `ALLOWED_HOSTS` only for a custom domain. Render's own host name is added automatically through `RENDER_EXTERNAL_HOSTNAME`.

`build.sh` runs:
```
pip install -r requirements.txt
npm ci
npm run css:build
python manage.py collectstatic --no-input
python manage.py migrate --no-input
```

Migrating in the build keeps everything on the free plan, which has no pre-deploy command. The trade-off is that a failed migration fails the build, so the old version keeps serving.

The gunicorn timeout is 60 seconds because one Assistant question can take several model calls, each with a 30-second timeout.

*Rejected:*
- **A `render.yaml` blueprint:** it was drafted first, but the developer chose a manual guide. The developer wants to understand and control each setting, and a blueprint hides them in a file that is easy to get out of step with the dashboard.
- **A Docker image:** it gives more control but means a Dockerfile with both Python and Node to maintain. Render's native Python runtime already has Node available during the build.
- **Committing the built CSS:** it goes stale and causes merge noise, and the CSS tooling already exists.

### 5. HTMX redirects to sign-in become a full-page redirect
A small middleware, `core.middleware.HtmxLoginRedirect`, runs after authentication. When the request carries `HX-Request` and the response is a redirect to the sign-in URL, it returns status 204 with an `HX-Redirect` header. The header points to the sign-in URL, with `next` set from the request's `HX-Current-URL` path, so the user returns to the page they were on.

*Rejected:* a client-side check on every swap for a sign-in form, which is fragile and depends on markup.

### 6. Error toasts and the loading bar in `app.js`
- **Error toast:** a document listener on `htmx:responseError` shows the error toast "Something went wrong. Try again.", and one on `htmx:sendError` shows the offline message. Both use a small `walletoToast(text)` helper that draws the same markup as the server toasts in `components/toasts.html`. Its container is a `popover="manual"` element, opened again for each toast. Modals are native `<dialog>` elements in the browser's top layer, which no `z-index` can rise above, but a popover opened after the dialog sits on top of it. Because HTMX does not swap responses with status 4xx or 5xx by default, the modal and its typed values stay as they were.
- **Expected form errors are not failures.** Forms with validation errors already respond with status 200 and swap the form back with its messages, so they never raise the toast. This stays as it is.
- **Loading bar:** a fixed 2px bar at the top of the screen gets a class while any request runs, and that class shows the bar only after a 300ms CSS transition delay, so fast requests never flash it. Disabling the control that started the request stays with each form's existing `hx-disabled-elt`.

*Rejected:* a spinner on every button, which means per-template markup in dozens of places.

### 7. Error templates outside the app shell
`templates/404.html`, `500.html` and `403_csrf.html` extend a minimal `layouts/error.html`. It contains only the logo, a heading, one sentence and a "Go to Home" link, with the same compiled stylesheet. It has no sidebar, no user context and no database access, because Django renders 500 errors without context processors, and a 404 can happen for visitors who are not signed in. Django uses `403_csrf.html` automatically for CSRF failures.

### 8. Demo data created on first use only
Nothing in the build or start commands runs `seed_demo`. The existing behaviour of "Try demo account" creates the data on the first click. To refresh it, the developer runs `python manage.py seed_demo` on their own machine with `DATABASE_URL` set to the Neon connection string, because Render's free plan has no shell. This is documented in `docs/DEPLOY.md`.

*Rejected:* `seed_demo` in `build.sh`. It would wipe visitors' changes on every deploy, which goes against the developer's choice not to reset the data.

### 9. Public README in English, and a tidier repository
The README is rewritten in English for recruiters. Its sections:
- what Walleto is;
- screenshots in `docs/screenshots/` (Home, Transactions, Budget, Savings goals, Assistant with a plan card, and a phone view);
- features;
- an architecture diagram in Mermaid ("the LLM picks tools, code computes"), plus the data model;
- the evaluation table from `docs/eval_results.md`;
- the tech stack;
- running locally;
- deploying, as a short paragraph linking to `docs/DEPLOY.md`;
- the project structure, including how OpenSpec is used;
- a placeholder for the live demo link, filled in by the developer after deploy.

The README links only to files that are in git. `docs/STYLE.md` and `docs/decisions.md` stay local, as the developer chose, so the README describes the design rules briefly instead of linking to them.

Repository tidy-up:
- `.gitignore` is regrouped into Python, Django, secrets, Node and local notes and tools, and `.codeduck/` is added.
- `core` tests move into `core/tests/` like the other apps. The test URLconf moves to `core.tests.test_errors`.

*Rejected:* committing `docs/STYLE.md` and `docs/decisions.md` so the README can link them. The developer keeps them local.

## Risks / Trade-offs

- **Neon suspends its compute after about 5 minutes idle, so the first query takes about a second to wake it** → This is small next to Render's own cold start. `conn_health_checks` stops the stale connection from failing that request.
- **Neon's free plan has 0.5 GB of storage and limited compute hours per month** → Walleto's data is a few MB. Suspension when idle keeps the compute hours low, and the README names the limits.
- **The connection string is a secret** → It is only set in the Render dashboard, never in the repository, `.env.example`, the README or the guide, which shows only a placeholder.
- **The free web service sleeps when idle, so the first visit takes about 30 to 60 seconds** → This is accepted for a portfolio project and mentioned in the README.
- **Demo data is not reset, so it ages.** After a month "this month" has few transactions, and visitors' edits stay → The developer reruns `seed_demo`. This was the developer's explicit choice.
- **Node may be missing in Render's Python build image** → The first deploy shows it. `NODE_VERSION` is set in the guide, and the guide's troubleshooting section says what to do if `npm` is not found.
- **Manual setup can drift from what the code expects** → The guide lists every value in one table, and the first-deploy checklist catches a missing one: `/healthz`, sign-in over HTTPS, "Try demo account" and one Assistant question.
- **`SECURE_SSL_REDIRECT` with a misconfigured proxy header causes a redirect loop** → The proxy header is set as above, and `/healthz` is exempt from the redirect. The first deploy is checked over both `http://` and `https://`.
- **Demo visitors share the demo user's assistant History until the deferred per-visitor change** → It only shows the shared sample data and questions asked about it. The README says the demo is shared.

## Migration Plan

1. Merge locally. Run the tests and `check --deploy` with production-like environment values. Optionally run `migrate` once locally against the Neon URL, to prove the connection.
2. The developer creates a Neon project in `ap-southeast-1` and copies the direct connection string.
3. The developer pushes, then creates the Render web service by hand from `docs/DEPLOY.md` and sets the environment values.
4. The first build runs migrate on the empty Neon database. Open `/healthz`, then the sign-in page, then choose "Try demo account".
5. Rollback: Render can redeploy the previous successful deploy with one click. This change adds no migration.

## Open Questions

- Whether to raise `SECURE_HSTS_SECONDS` to a year after a stable week. This can be done later without changing behaviour.
