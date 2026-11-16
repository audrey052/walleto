# Email Sign-in, Registration and the App Shell with Placeholder Pages

**Created:** 2026-11-16
**Last edited:** 2026-11-16
**Status:** Implemented. Superuser creation and a real-browser check are outstanding; see *Known gaps*
**Commit:** `2f886ac` feat: add email sign-in, registration and the app shell with placeholder pages
**Branch:** `main`, parent `4097ca1`
**OpenSpec change:** `setup-foundation` (MVP 0), tasks 1.4, 2.1–2.3, 4.1–4.5, 5.1–5.2, 6.1–6.5, 7.1–7.5, 8.1, 9.1–9.7
**Trigger:** specs `user-auth`, `app-shell` and `money-format`. People need accounts before any finance data exists, and every later page needs the same frame.

## Why this is recorded here

- **A new user model and the project's first migration** (`accounts.0001_initial`). The user model can't be swapped later without resetting the database.
- **Two new apps** (`accounts`, `core`) and all public routes.
- **A global access rule:** every view now requires sign-in by default.

## Context

- **Custom user model before the first `migrate`.** The design signs in by email; Django's default `User` signs in by username. `AUTH_USER_MODEL` was set, then `makemigrations accounts` and the first `migrate` ran on an empty database. See `design.md` decision 2.
- **`LoginRequiredMiddleware` (Django 5.1+) instead of decorators.** A forgotten `@login_required` would silently expose user data; with the middleware, a view is private unless marked `@login_not_required`. `LoginView` and the admin login are already marked. This departs from task 7.5's original wording; recorded in `design.md` decision 4.
- **Built-in auth views.** `LoginView` (rejects unsafe `next` addresses) and `LogoutView` (POST only in Django 5). Registration is a small custom view.
- **`core` holds shared pieces:** section list, placeholder pages, style guide, context processor and template tags.
- **Simple components are CSS classes; structured ones are includes.** Icons are a template tag, not a partial. This departs from tasks 4.1–4.3's original wording; recorded in `design.md` decision 7.

## What is built

### User model: `accounts/models.py`, migration `0001_initial`

| Field / member | Notes |
|---|---|
| `email` | `EmailField`, unique, `USERNAME_FIELD`; lowercased and stripped on save |
| `full_name` | `CharField(150)`, required (`REQUIRED_FIELDS`) |
| `username`, `first_name`, `last_name` | removed (`= None`) |
| `UserManager.create_user` / `create_superuser` | no username; superuser must have `is_staff` and `is_superuser` |
| `UserManager.get_by_natural_key` | `email__iexact`, so sign-in ignores letter case |
| `initials` | "AR" for "Aditya Ramadhan", "SA" for a single name, first two letters of the email when the name is empty |
| `get_full_name`, `get_short_name` | full name; first word of the name |

### Forms: `accounts/forms.py`

| Form | Behavior |
|---|---|
| `RegistrationForm` (`BaseUserCreationForm`) | Full name, email, password ×2; duplicate check with `email__iexact` → "An account with this email already exists."; Django's four password validators |
| `EmailAuthenticationForm` (`AuthenticationForm`) | Label "Email"; both `invalid_login` and `inactive` show "Email or password is incorrect.", so the form never reveals whether an email is registered |
| `AdminUserCreationForm`, `AdminUserChangeForm` | Admin forms for the email-based model |

Every widget gets the `.input` class.

### Routes

| Method | URL | Name | Access | Purpose |
|---|---|---|---|---|
| GET/POST | `/sign-in/` | `accounts:login` | public | Sign in; signed-in users are redirected to `/`; "Welcome back, {first name}." toast |
| GET/POST | `/register/` | `accounts:register` | public | Create account, sign in, "Account created. Welcome to Walleto." toast |
| POST | `/sign-out/` | `accounts:logout` | signed in | Sign out → `/sign-in/`; GET returns 405 |
| GET | `/` | `core:dashboard` | signed in | Placeholder |
| GET | `/transactions/`, `/wallets/`, `/budget/`, `/savings-goals/`, `/assistant/` | `core:*` | signed in | Placeholders |
| GET | `/styleguide/` | `core:styleguide` | signed in | All components; 404 unless `DEBUG` |

Settings added: `INSTALLED_APPS += accounts, core`, `LoginRequiredMiddleware`, `core.context_processors.app_shell`, `AUTH_USER_MODEL`, `LOGIN_URL = "accounts:login"`, `LOGIN_REDIRECT_URL = "core:dashboard"`, `LOGOUT_REDIRECT_URL = "accounts:login"`.

### Shared code: `core/`

| Module | Job |
|---|---|
| `sections.py` | Six sections in sidebar order: key, short mobile label, title, subtitle, icon, URL name |
| `context_processors.py` | `nav_sections`, `active_section` (from the URL name in the `core` namespace) and `today` (`timezone.localdate()`) on every page |
| `templatetags/money.py` | `rupiah`, `rupiah_signed:"income"/"expense"`, `{% amount %}`; whole Rupiah (round half up), dot separators, U+2212 minus, `+` and accent color for income |
| `templatetags/icons.py` | `{% icon name size css_class %}` with the 30 Figma line icons; unknown names raise `TemplateSyntaxError` |
| `views.py` | Placeholder views and the style guide |

### Templates

| Template | Job |
|---|---|
| `base.html` | Skeleton: font preload, CSS, `app.js`, HTMX, Alpine, CSRF header for HTMX, toasts |
| `layouts/app.html` | Shell: collapsible sidebar (logo, six sections, active marker, profile menu), topbar (toggle, breadcrumb, date as "Monday, 16 Nov 2026"), content area; below 768px a topbar logo, avatar menu and a six-item bottom navigation |
| `layouts/auth.html` | Split layout; right side is a static dashboard preview, hidden below 1024px |
| `accounts/login.html`, `accounts/register.html` | Forms; "Try demo account" is shown disabled until MVP 2 |
| `core/placeholder.html` | Title, subtitle, "Coming soon" empty state |
| `core/styleguide.html`, `core/_styleguide_modal_body.html` | Every component with sample content |
| `components/` | `page_heading`, `field`, `empty_state`, `category_chip`, `progress` (forest < 90, amber 90–100, clay > 100), `modal` (`<dialog>`), `profile_menu` (POST sign-out), `toasts` |

## Requirements this establishes

1. **Every page requires sign-in** unless its view is marked `@login_not_required`.
2. **Emails are unique and case-insensitive** for registration and sign-in.
3. **A failed sign-in never reveals whether the email exists.**
4. **Sign-out happens only through POST.**
5. **After sign-in the user returns to the page they asked for,** but never to another site.
6. **Every amount is shown through the money helpers,** never formatted by hand.
7. **The style guide is unreachable in production.**

## Files changed

| File | Change |
|---|---|
| `accounts/models.py`, `accounts/migrations/0001_initial.py` | new `User` model and table |
| `accounts/forms.py`, `accounts/views.py`, `accounts/urls.py`, `accounts/admin.py`, `accounts/apps.py`, `accounts/__init__.py` | new |
| `accounts/tests.py` | 19 tests |
| `core/sections.py`, `core/context_processors.py`, `core/views.py`, `core/urls.py`, `core/templatetags/money.py`, `core/templatetags/icons.py` | new |
| `core/admin.py`, `core/apps.py`, `core/models.py`, `core/__init__.py`, `core/migrations/__init__.py`, `core/templatetags/__init__.py` | new (generated or empty) |
| `core/tests.py` | 15 tests |
| `config/settings.py` | apps, middleware, context processor, auth settings |
| `config/urls.py` | includes `accounts.urls` and `core.urls` |
| `templates/` (19 files) | see the table above |

## Verification

**Executed:**

- **34 tests pass** (`python manage.py test`), covering:
  - user model: create without username, superuser, email lowercased, case-insensitive duplicate rejected, initials
  - registration: success signs in with toast, duplicate in any case, mismatched passwords keep name and email, weak password
  - sign-in: any email case, wrong password and unknown email give the same error, external `next` ignored
  - access: all six sections redirect visitors with `?next=`, return to Budget after sign-in, signed-in users skip sign-in and registration
  - sign-out: GET returns 405 and the user stays signed in; POST signs out
  - money: every `money-format` scenario, Decimal and string inputs, `{% amount %}` markup
  - shell: six sections with exactly one current item per navigation, placeholder text, initials "AR", 23:30 UTC on 14 Nov shows "Sunday, 15 Nov 2026"
  - style guide: 200 with `DEBUG`, 404 without
- **Migration:** `makemigrations accounts` then the first `migrate` on an empty database; all built-in apps applied after `accounts.0001`.
- **`manage.py check`:** no issues.
- **Headless Edge screenshots:** sign-in at 1440px; dashboard placeholder at 1440px and at 390px inside an iframe (no horizontal scroll; all six bottom-navigation items fit); style guide at 1440px.

**Fixed during implementation:**

- `{{ active_section.title|default:page_title }}` raised `VariableDoesNotExist` when `page_title` was absent (filter arguments must exist). Replaced with `{% if %}`.
- Views passed `active_section` as a string, overriding the context processor's dict. Removed from the views.
- A registration test used `assertRedirects`, which fetched the dashboard and consumed the one-time toast before the test looked for it. It now uses `fetch_redirect_response=False`.

**Not executed:**

- A pass in a real browser: sidebar collapse persistence, profile menu, toast timing, the style guide modal.
- Sign-in to `/admin/` with a real superuser.

## Known gaps

- **No superuser yet** (task 2.4); it needs the developer's own password.
- **Real-browser check outstanding** (task 10.1).
- **"Try demo account" is disabled** until the demo account exists (MVP 2).
- **No password reset**; out of scope for MVP 0.
- **Bottom navigation labels are short forms** ("Home", "Activity", "Goals") to fit six items at 390px; the sidebar uses the full titles.
