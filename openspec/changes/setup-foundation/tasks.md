# Tasks

## 1. Django project and settings

- [x] 1.1 Run `django-admin startproject config .` in the repository root and confirm `python manage.py runserver` shows the Django welcome page (do NOT run `migrate` yet)
- [x] 1.2 Load `SECRET_KEY`, `DEBUG` and `OPENAI_API_KEY` from `.env` with python-dotenv; create `.env` (git-ignored) and `.env.example` (committed, no values)
- [x] 1.3 Set `LANGUAGE_CODE = "en-us"`, `TIME_ZONE = "Asia/Jakarta"`, `USE_TZ = True`; configure `templates/` and `static/` folders at the repository root
- [x] 1.4 Create the `core` app (shared template tags, placeholder pages, style guide) and add it to `INSTALLED_APPS`

## 2. Custom user model (before the first migration)

- [x] 2.1 Create the `accounts` app and an `accounts.User` model: extends `AbstractUser`, no `username`, unique `email` as `USERNAME_FIELD`, `full_name` field, email saved lowercased
- [x] 2.2 Write the user manager with `create_user` and `create_superuser` that work without a username
- [x] 2.3 Set `AUTH_USER_MODEL = "accounts.User"`, then run `makemigrations` and the first `migrate`
- [ ] 2.4 Register the user model in the admin (done), create a superuser with `python manage.py createsuperuser`, and sign in to `/admin` with an email address (developer, needs a personal password)

## 3. Tailwind, static assets and tokens

- [x] 3.1 Create `package.json` with `tailwindcss` and `@tailwindcss/cli` (pinned 4.1.11) as dev dependencies and npm scripts `css:watch` and `css:build`
- [x] 3.2 Write `static/src/app.css`: import Tailwind, `@source` the template and app folders, declare the color, font, radius, shadow and type-scale tokens from docs/STYLE.md in `@theme`, and the shared component classes in `@layer components`
- [x] 3.3 Add `static/css/` (the build output) to `.gitignore`
- [x] 3.4 Copy Plus Jakarta Sans and its OFL license from the Figma Make project into `static/fonts/` and declare it with `@font-face`
- [x] 3.5 Download pinned versions of HTMX (2.0.4) and Alpine.js (3.14.9) into `static/vendor/` and note the versions in docs/decisions.md

## 4. Shared components

- [x] 4.1 `{% icon %}` template tag (`core/templatetags/icons.py`): SVG icons by name, using the icon set from the Figma Make project
- [x] 4.2 Button classes (`btn`, `btn-primary`, `btn-danger`, `btn-text`, `btn-icon`) and `components/field.html` (label, input or select, help text, error message)
- [x] 4.3 `panel` classes, `components/category_chip.html`, `components/progress.html` (normal, warning, over)
- [x] 4.4 `components/modal.html` (native `<dialog>`, title, description, close button, footer actions), `components/empty_state.html` and `components/page_heading.html`
- [x] 4.5 Toast rendering for Django messages in the base template, auto-closing after about four seconds and closable by hand

## 5. Money format

- [x] 5.1 In the `core` app, add the `rupiah` filter, the `rupiah_signed` filter and the `{% amount %}` tag, matching the `money-format` spec (dot separators, U+2212 minus, tabular digits)
- [x] 5.2 Unit tests covering every scenario in the `money-format` spec

## 6. Application shell

- [x] 6.1 `templates/base.html` and `templates/layouts/app.html`: sidebar (logo, six sections, active state), topbar (toggle, breadcrumb, Jakarta date), content area, toast area
- [x] 6.2 Profile menu at the bottom of the sidebar with initials, name, email and a POST "Sign out" form
- [x] 6.3 Sidebar collapse with Alpine.js, remembered in `localStorage`, with section names shown on hover when collapsed
- [x] 6.4 Mobile layout below 768px: hide the sidebar, show a bottom navigation with all six sections and the profile menu in the topbar, no horizontal scroll
- [x] 6.5 Placeholder pages for Dashboard (also served at `/`), Transactions, Wallets, Budget, Savings goals and Assistant, with titles and subtitles from docs/STYLE.md and a "coming soon" empty state

## 7. Authentication pages

- [x] 7.1 Registration form and view: full name, email, password twice, case-insensitive duplicate check, Django password validators, sign in after success, success toast
- [x] 7.2 Sign-in page using Django's `LoginView` with an email field, `redirect_authenticated_user=True`, and the generic error "Email or password is incorrect."
- [x] 7.3 Split layout for sign-in and registration as in the design, including a "Try demo account" button that is visible but disabled until MVP 2
- [x] 7.4 Sign-out through Django's `LogoutView` (POST only), redirecting to the sign-in page
- [x] 7.5 Require sign-in on every view through `LoginRequiredMiddleware` (`@login_not_required` on registration), with `LOGIN_URL`, `LOGIN_REDIRECT_URL` and `LOGOUT_REDIRECT_URL` set

## 8. Style guide page

- [x] 8.1 `/styleguide/` showing every component with sample content, returning 404 when `DEBUG` is off

## 9. Tests

- [x] 9.1 User model tests: create user and superuser without username, email lowercased, duplicate email in different case rejected
- [x] 9.2 Registration tests: success signs in, duplicate email, mismatched passwords, weak password
- [x] 9.3 Sign-in tests: valid credentials in any email case, invalid credentials show the generic error, external `next` address is ignored
- [x] 9.4 Access tests: each section page redirects visitors to sign-in and returns to the requested page after sign-in; signed-in users are redirected away from sign-in and registration
- [x] 9.5 Sign-out test: a GET request does not sign the user out, a POST does
- [x] 9.6 Style guide test: 200 with `DEBUG` on, 404 with `DEBUG` off
- [x] 9.7 App shell tests: six sections with one active item, placeholder content, profile initials, topbar date in Jakarta time

## 10. Wrap-up

- [ ] 10.1 Check every page at 1440px and 390px against docs/STYLE.md and the Figma design (sign-in, dashboard placeholder and style guide checked by headless screenshots; developer to do a final pass in a real browser)
- [x] 10.2 Add "how to run locally" (venv, `npm install`, `npm run css:watch`, `runserver`) to README.md
- [x] 10.3 Update docs/decisions.md with the decisions from design.md that are not there yet
- [x] 10.4 Run `openspec validate setup-foundation --strict` and fix any errors
