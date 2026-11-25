# Proposal

## Why

Walleto runs only on the developer's machine, so nobody else can try it. MVP 8 makes the code ready for a public server and gives the developer a manual guide to deploy it. Before that, it closes the rough edges a stranger would hit first: error pages, failed requests, slow requests and expired sessions. The repository and its README are also tidied, so the project reads well on GitHub.

## What Changes

- **Production settings.** The secret, allowed hosts, trusted origins and database come from environment variables. In production `DEBUG` is off and HTTPS is enforced with secure cookies and HSTS. WhiteNoise serves the static files, gunicorn runs the app, and `python manage.py check --deploy` passes.
- **PostgreSQL in production on Neon's free plan** through `DATABASE_URL`, which requires SSL. SQLite stays the local default.
- **A build script and a manual deploy guide.** There is no blueprint file.
  - `build.sh` installs the Python packages, builds the CSS with `npm ci` and `npm run css:build` (because `static/css/` is not in git), then runs `collectstatic` and `migrate`.
  - `docs/DEPLOY.md` walks the developer through creating the Neon database and the Render web service by hand in their dashboards: commands, region, environment values, first checks, and how to update and roll back.
  - A `/healthz` address answers Render's health check.
- **Demo data is created once.** "Try demo account" already creates the demo data when it is missing. The data is not reset every day, and the developer can rerun `seed_demo` by hand.
- **Error pages:** "Page not found" (404), "Something went wrong" (500) and "This form has expired" (CSRF 403). They are in Walleto's style and do not depend on the database.
- **Failed and slow requests:**
  - A failed HTMX request shows an error toast instead of doing nothing, and a lost connection shows its own message.
  - If the session has expired, an HTMX request takes the user to the sign-in page as a full page, instead of drawing the sign-in page inside a card.
  - While a request is running, a thin bar at the top of the page shows activity.
- **Tidier repository:**
  - a grouped `.gitignore` that also covers local tool folders;
  - `core` tests moved into a `tests/` package, like the other apps;
  - no dead files or links to files that are not in git.
- **A public README in English:** what Walleto is, screenshots, the architecture ("the LLM picks tools, code computes"), evaluation results, how to run it locally, and a link to the deploy guide.

## Capabilities

### New Capabilities

- `deployment`: how Walleto runs in production. It covers settings from the environment, HTTPS and cookie security, static files, the database URL, the health check, the build script and the deploy guide.

### Modified Capabilities

- `app-shell`: adds requirements for the error pages, failed and expired-session HTMX requests, and the loading bar.
- `demo-account`: demo data is created once and not reset automatically.

## Out of scope

- **Deferred to a later change, as the developer chose:**
  - demo assistant limits per visitor and in total;
  - demo conversations visible only to the visitor who started them;
  - checking every page at 390px with an empty account.

  Until then the shared demo user has the normal limit of 30 questions a day, which already caps the API cost. Demo visitors can see each other's assistant History, which shows only the shared sample data.
- **Deploy tooling:** a Render blueprint (`render.yaml`), Docker and CI. The developer deploys by hand from the guide.
- **Demo data:** resetting it every day, and a separate demo user per visitor.
- **Other services:** a custom domain, email (password reset, verification), and monitoring or error tracking (Sentry).
- **Features:** MVP 6 quick add, streaming answers, and the "Help me plan" buttons on Budget and Savings goals.
- **Things the developer does:** pushing, deploying, and recording the demo video.

## Impact

- **Code:**
  - `config/settings.py`: environment-driven settings, WhiteNoise, database URL, security settings.
  - `config/urls.py`: `/healthz`.
  - `config/staticfiles.py`: leaves the Tailwind source out of `collectstatic`.
  - `core/middleware.py`: turns an HTMX redirect to sign-in into `HX-Redirect`.
  - `static/js/app.js`, `static/src/app.css` and `templates/base.html`: error toasts and the loading bar.
- **New files:**
  - `build.sh` and `.python-version`;
  - `templates/layouts/error.html`, `404.html`, `500.html` and `403_csrf.html`;
  - `docs/DEPLOY.md` and `docs/screenshots/`.
- **Changed files:** a rewritten `README.md`, a regrouped `.gitignore`, and an updated `.env.example`.
- **Dependencies:** `gunicorn`, `whitenoise`, `dj-database-url` and `psycopg[binary]` are added to `requirements.txt`.
- **Systems, set up by the developer following `docs/DEPLOY.md`:**
  - a Neon project in Singapore (`ap-southeast-1`);
  - a Render web service in Singapore, with `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS` (optional), `OPENAI_API_KEY`, `OPENAI_MODEL` and `OPENAI_REASONING_EFFORT` set in its dashboard.
