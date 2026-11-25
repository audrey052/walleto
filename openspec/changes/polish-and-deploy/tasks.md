# Tasks

## 1. Production settings

- [x] 1.1 Add `gunicorn`, `whitenoise`, `dj-database-url` and `psycopg[binary]` to the venv and pin them in `requirements.txt`, using `.venv/Scripts/python -m pip freeze`. In `config/settings.py` (design decisions 1–3):
  - read `ALLOWED_HOSTS` from the environment, and derive `CSRF_TRUSTED_ORIGINS` from it;
  - take the database from `DATABASE_URL`, defaulting to SQLite, with `conn_max_age=600` and `conn_health_checks=True` for Neon;
  - add WhiteNoise and `STATIC_ROOT`, with plain storage under tests;
  - turn on the security block when `DEBUG` is off;
  - update `.env.example`.

  Verify:
  - settings tests for the hosts and trusted origins, a Neon-style URL (`postgresql://u:p@ep-x.ap-southeast-1.aws.neon.tech/walleto?sslmode=require` parses to the PostgreSQL engine with `sslmode=require`) and the SQLite default;
  - `DEBUG=False SECRET_KEY=<50 random chars> ALLOWED_HOSTS=walleto.onrender.com python manage.py check --deploy` reports no issues;
  - `collectstatic` produces fingerprinted `app.css` names.
- [x] 1.2 Add `GET /healthz`, which needs no sign-in, returns 200 "ok" and is exempt from the SSL redirect. Verify tests: status 200 while signed out, no database query, and still 200 with production security settings.
- [x] 1.3 Add an executable `build.sh` and a `.python-version` (design decision 4). Verify:
  - `bash build.sh` runs to the end locally against SQLite, with `pip install`, `npm ci`, `css:build`, `collectstatic` and `migrate` all succeeding;
  - `gunicorn` imports `config.wsgi`. On Windows, where gunicorn does not run, check this with `python -c "import config.wsgi"`.

## 2. Errors, expired sessions and loading

- [x] 2.1 Add `templates/layouts/error.html`, `404.html`, `500.html` and `403_csrf.html` (design decision 7), with copy per docs/STYLE.md. Verify tests with `DEBUG=False`:
  - an unknown address gives 404 with "Page not found" and a Home link;
  - another user's transaction edit address gives the same page;
  - a view that raises gives 500 "Something went wrong" without the traceback; use a test-only URL with `raise_request_exception=False`;
  - a POST without a CSRF token gives 403 "This form has expired";
  - the 500 page renders with the database connection closed.
- [x] 2.2 Add `core.middleware.HtmxLoginRedirect` (design decision 5). Verify tests:
  - a signed-out HTMX GET to Transactions gets 204 with `HX-Redirect: /sign-in/?next=/transactions/`, using `next` from `HX-Current-URL`;
  - the same request without HTMX still gets the normal 302;
  - other redirects in HTMX requests are unchanged, for example the HX-Redirect after saving.
- [x] 2.3 Add the `htmx:responseError` and `htmx:sendError` toasts and the delayed top loading bar to `static/js/app.js` and `static/src/app.css`, then run `npm run css:build` (design decision 6). Verify in Edge headless, with a temporary QA user that is deleted afterwards:
  - a request forced to fail with a 500 response shows the right toast above the modal and keeps the modal and its values;
  - an offline filter change shows the offline toast and leaves the list unchanged;
  - the bar shows on a 1-second request and not on a fast one;
  - signing out elsewhere, then changing a filter, lands on sign-in and returns to Transactions after signing in.

## 3. Demo data

- [x] 3.1 Check the demo data rule: "Try demo account" creates the data only when it is missing, and nothing in `build.sh` seeds it (design decision 8). Verify a test that a second demo sign-in keeps a transaction a visitor added, and a test that `seed_demo` is absent from `build.sh`.

## 4. Repository tidy-up

- [x] 4.1 Remove `render.yaml` and its test, regroup `.gitignore` (Python, Django, secrets, Node, local notes and tools, adding `.codeduck/`), and move the `core` tests into a `core/tests/` package, updating the test URLconf path (design decision 9). Verify:
  - `git status` shows no unintended files;
  - `git check-ignore .codeduck WORKPLAN.md docs/STYLE.md` lists all three;
  - `python manage.py test` finds and passes the same number of tests as before the move.
- [x] 4.2 Search the tracked files for leftovers: TODOs, debug prints, links to gitignored files, the old placeholder name "Aditya Ramadhan" in UI copy, and real secrets or connection strings. Fix or remove each, and list them in `changes.md`. Verify that a `git grep` for each pattern returns only intended matches, such as test fixtures.

## 5. README and deploy guide

- [x] 5.1 Take the README screenshots in Edge headless with the demo account, on a copy of the local database so the real demo stays untouched, and save them as PNGs in `docs/screenshots/`: Home, Transactions, Budget, Savings goals, Assistant, and Home on a phone. Verify that the files exist and are each under 400 KB.
- [x] 5.2 Write `docs/DEPLOY.md` (design decision 4), covering:
  - the accounts needed;
  - Neon: creating the project in `ap-southeast-1` and copying the direct connection string;
  - Render: the web service settings, the commands and a table of environment values with how to get each one, including a one-line `SECRET_KEY` generator;
  - the first-deploy checklist;
  - updating, rolling back, rerunning `seed_demo` from the developer's machine against Neon (the free plan has no Render shell), and the free-plan limits;
  - troubleshooting: build fails on `npm`, `DisallowedHost`, a redirect loop, the database waking up.

  Verify that every command and setting name matches `build.sh` and `config/settings.py`, and that there are no real secrets.
- [x] 5.3 Rewrite `README.md` in English (design decision 9). Its sections:
  - what Walleto is, and features;
  - screenshots;
  - an architecture diagram in Mermaid ("the LLM picks tools, code computes"), plus the data model;
  - the latest evaluation table;
  - the stack;
  - running locally;
  - deploying (a link to `docs/DEPLOY.md`);
  - the project structure, and how OpenSpec is used;
  - a live demo placeholder.

  Verify that every command in "Running locally" works in a fresh shell, and that every image and link path exists in git.

## 6. Wrap-up

- [x] 6.1 Update `docs/STYLE.md` (error pages, error toasts, loading bar), `WORKPLAN.md` (tick MVP 8, leaving deploy and video to the developer, with the deferred items listed) and `docs/decisions.md` (decisions 1–9 with the alternatives that were rejected). Verify that `python manage.py test`, `python manage.py makemigrations --check` and `openspec validate polish-and-deploy --strict` all pass.
- [x] 6.2 Write `changes.md` and the commit record in `openspec/commits/`, then fill in the index. Make one commit without attribution, and do not push. Verify that the index lists the record and `git status` is clean.

## Workflow follow-up

- The developer follows `docs/DEPLOY.md`: Neon project, Render web service, environment values, first-deploy checklist.
- After the first deploy, put the live link in the README.
- The developer records the demo video.
- A later change: demo assistant limits per visitor and in total, per-visitor demo conversations, and the 390px empty-account pass.
- `/opsx:archive polish-and-deploy`.
