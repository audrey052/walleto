# Design

## Context

The repository contains only documentation: WORKPLAN.md, docs/STYLE.md, docs/decisions.md and the Figma Make reference code in docs/design/figma-make-source/. A `.venv` with Django 5.2 LTS and python-dotenv exists. Node.js v24 is installed globally. No migration has been run yet, which matters for the user model decision below.

## Goals / Non-Goals

**Goals:**
- A Django project structure that later MVPs extend by adding apps, not by reorganizing.
- Authentication by email that will not need to change later.
- One set of design tokens and components that every page reuses.
- Everything works offline in development (no runtime CDN dependency).

**Non-Goals:**
- Production settings, static file serving in production, PostgreSQL (MVP 8).
- Demo account (MVP 2).
- Password reset and email sending.

## Decisions

### 1. Project layout: `config/` package plus apps at the repository root
`django-admin startproject config .` puts settings in `config/`. Feature apps live at the root (`accounts/`, `core/`, later `finance/` and others). Project-wide templates live in `templates/`, static sources in `static/`.
- Rejected: an `apps/` folder. It adds import path configuration for little benefit at this size.

### 2. Custom user model with email as the login field, created before the first migration
An `accounts.User` model extends `AbstractUser`, removes `username`, uses `email` as `USERNAME_FIELD`, and needs a custom manager for `create_user` and `create_superuser`. Emails are stored lowercased so uniqueness and sign-in are case-insensitive. `AUTH_USER_MODEL` is set before running `migrate` for the first time.
- Rejected: Django's default `User` with username. The design signs in by email, and switching the user model after the first migration requires resetting the database.

### 3. A `core` app for shared, non-feature pieces
`core` holds the placeholder section pages, the style guide page, and the template tags (for example the Rupiah filter). Feature apps stay focused on their own data.
- Rejected: putting shared template tags in `accounts`. They have nothing to do with accounts.

### 4. Use Django's built-in auth views
`LoginView` (with `redirect_authenticated_user=True`) and `LogoutView` are reused with Walleto templates and an email-based form. `LogoutView` accepts only POST in Django 5, which satisfies the sign-out requirement. `LoginView` already rejects unsafe `next` addresses. Registration is a small custom view because Django does not ship one.
- Rejected: django-allauth. Powerful, but far more than email and password sign-in needs, and it hides the parts worth learning.

### 5. Tailwind CSS v4 through its npm CLI
`package.json` lists `tailwindcss` and `@tailwindcss/cli` as dev dependencies. `static/src/app.css` imports Tailwind, declares the STYLE.md tokens in `@theme`, and points `@source` at the template folders. The CLI builds `static/css/app.css`; during development it runs in watch mode next to `runserver`. The built file is git-ignored and rebuilt at deploy time.
- Rejected: the Tailwind CDN script (not meant for production, no custom build), and the `django-tailwind` package (an extra layer over a CLI that is already simple to run).

### 6. HTMX, Alpine.js and fonts are vendored into `static/vendor/` and `static/fonts/`
Pinned versions are downloaded once and committed. Plus Jakarta Sans comes from the Figma Make project (OFL license, license file kept next to it).
- Rejected: loading from a CDN at runtime. Development should work offline and versions must not change underneath the app.

### 7. Components as template partials
Each component in STYLE.md section 5 is a file under `templates/components/` used with `{% include "components/button.html" with variant="primary" label="Save" %}`. Icons are one `components/icon.html` partial that picks an SVG by name, using the icon set from the Figma Make project (`src/components/ui.tsx`).
- Rejected: django-cotton or django-components. Nicer syntax, but plain includes are enough for this number of components and keep the project on built-in Django.

### 8. Small client-side state with Alpine.js
Sidebar collapse, profile menu, modals and toast dismissal use Alpine.js. The sidebar's collapsed state is saved in `localStorage` so it survives page loads.
- Rejected: storing the sidebar state on the server. It is a per-browser preference and not worth a database field.

### 9. Toasts from Django's messages framework
Views add messages with `messages.success(...)`; `base.html` renders them as toasts.
- Rejected: a custom notification system. The messages framework already survives redirects.

### 10. Settings from `.env`
`config/settings.py` reads `SECRET_KEY`, `DEBUG` and `OPENAI_API_KEY` through python-dotenv. `.env.example` lists the keys without values. `TIME_ZONE = "Asia/Jakarta"`, `USE_TZ = True`, `LANGUAGE_CODE = "en-us"`.

## Risks / Trade-offs

- **Running `migrate` too early** → If `migrate` runs before the custom user model exists, the database must be deleted and recreated. Mitigation: the tasks create the user model before the first `migrate`.
- **Two processes in development** (Django and the Tailwind watcher) → Easy to forget the watcher and see unstyled pages. Mitigation: document both commands in the README.
- **Template includes have no type checking** → A wrong parameter name fails silently. Mitigation: the style guide page shows every component, so breakage is visible.
- **Sidebar flashes expanded before Alpine loads** → Minor visual jump on page load. Acceptable for now; can be fixed later with a small inline script.
