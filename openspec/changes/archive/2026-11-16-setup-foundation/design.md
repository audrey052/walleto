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

Sign-in is required globally with Django's `LoginRequiredMiddleware` (added in Django 5.1). Views that must stay public opt out with `@login_not_required`; `LoginView` and the admin login already do.
- Rejected: `@login_required` on every view. Easy to forget on a new view, which would silently expose user data; the middleware makes "private" the default.

### 5. Tailwind CSS v4 through its npm CLI
`package.json` lists `tailwindcss` and `@tailwindcss/cli` as dev dependencies. `static/src/app.css` imports Tailwind, declares the STYLE.md tokens in `@theme`, and points `@source` at the template folders. The CLI builds `static/css/app.css`; during development it runs in watch mode next to `runserver`. The built file is git-ignored and rebuilt at deploy time.
- Rejected: the Tailwind CDN script (not meant for production, no custom build), and the `django-tailwind` package (an extra layer over a CLI that is already simple to run).

### 6. HTMX, Alpine.js and fonts are vendored into `static/vendor/` and `static/fonts/`
Pinned versions are downloaded once and committed. Plus Jakarta Sans comes from the Figma Make project (OFL license, license file kept next to it).
- Rejected: loading from a CDN at runtime. Development should work offline and versions must not change underneath the app.

### 7. Components: CSS classes for simple ones, template partials for structured ones
Simple components (buttons, inputs, panel, eyebrow label, toast, nav item) are CSS classes in `@layer components` of `static/src/app.css`, built with `@apply` from the STYLE.md tokens, so templates write `class="btn btn-primary"`. Components with structure (field with label and errors, modal, empty state, category chip, progress bar, page heading) are partials under `templates/components/` used with `{% include ... with ... %}`. Icons are an `{% icon "name" %}` template tag holding the SVG paths from the Figma Make icon set. Money uses the `rupiah` filters and `{% amount %}` tag.
- Rejected: one include per button. Buttons appear everywhere with varying content (icons, labels, `hx-*` attributes); a class is shorter and more flexible.
- Rejected: an icon partial with a long `{% if %}` chain. A Python dict is easier to read and raises an error for an unknown icon name.
- Rejected: django-cotton or django-components. Nicer syntax, but plain includes are enough for this number of components and keep the project on built-in Django.
- Note: the label style is called `eyebrow`, not `overline`, because Tailwind already has an `overline` (text-decoration) utility.

### 8. Small client-side state with Alpine.js
Sidebar collapse, profile menu and toast dismissal use Alpine.js components registered in `static/js/app.js`. Modals use the native `<dialog>` element. The sidebar's collapsed state is saved in `localStorage` so it survives page loads; widths are set in CSS (`.is-collapsed`) so the layout is correct even before Alpine starts.
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
- **Sidebar flashes expanded before Alpine loads** → For users who collapsed it, the sidebar is briefly expanded on page load. Acceptable for now; can be fixed later with a small inline script that sets `.is-collapsed` before first paint.
