# Proposal

## Why

Walleto has a work plan, a style guide and a Figma design, but no running application yet. Every later MVP (wallets, transactions, budget, savings goals, dashboard, AI features) needs the same base: a Django project, user accounts, a page layout that matches the design, and shared UI components. Building this base first keeps every later page consistent and lets each MVP focus on its own feature.

## What Changes

- Create the Django project with settings loaded from environment variables.
- Add a custom user model that signs in with email instead of username, created before the first migration.
- Add registration, login and logout pages styled after the Figma design.
- Require login for every page except login and registration.
- Add the application shell: collapsible sidebar with the six main sections, topbar with breadcrumb and today's date, profile menu, and a mobile bottom navigation.
- Add placeholder pages for the six sections so navigation works before the features exist.
- Add shared UI components (buttons, inputs, panel, category chip, progress bar, modal, empty state, toast) as reusable templates, using the tokens from docs/STYLE.md.
- Add the Rupiah display format used by every page.
- Add a style guide page, available only in development, that shows every component.

Out of scope for this MVP:
- Any finance data (wallets, categories, transactions); these start in `add-wallets`.
- The "Try demo account" behavior; the button is shown but the demo account is created in `add-transactions`.
- Password reset by email, social login, and email verification.
- Deployment and production settings.

## Capabilities

### New Capabilities
- `user-auth`: registering, signing in and out with email and password, and restricting pages to signed-in users.
- `app-shell`: the shared page frame (sidebar, topbar, profile menu, mobile navigation, toast messages) and the placeholder pages for each section.
- `money-format`: how Rupiah amounts are displayed across the application.

### Modified Capabilities
- None.

## Impact

- New Django project (`config/`) and app (`accounts/`), base templates and component templates, static assets (Tailwind build, fonts, HTMX, Alpine.js).
- New dependencies: Tailwind CSS v4 CLI through npm (development only). No new Python packages beyond Django and python-dotenv.
- `.env` and `.env.example` for secrets and settings.
- The custom user model is permanent: it cannot be introduced later without resetting the database, which is why it is part of this change.
