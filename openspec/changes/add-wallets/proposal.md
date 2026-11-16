# Proposal

## Why

Every money feature in Walleto starts from a place where money is kept and a label for what it is spent on. Transactions (MVP 2) need a wallet and a category, budgets (MVP 3) need categories, and the dashboard (MVP 5) totals wallets. This change adds both, and replaces the Wallets placeholder with a working page, so the app is useful before any transaction exists: a user can record where their money is today.

## What Changes

- Add a `finance` app that will hold all money data from now on.
- Add wallets: a name, a type (cash, bank account or e-wallet) and a starting balance, owned by one user.
- Replace the Wallets placeholder with a page that shows the total balance across active wallets and a card per wallet, with add, edit, archive and restore through modals that open without a page reload.
- Archive wallets instead of deleting them, so later transaction history stays intact; archived wallets are listed separately and can be restored.
- Accept amounts typed the way people write Rupiah ("2.500.000", "Rp 2,500,000", "2500000").
- Add default categories (expense and income) that every user can use, with the color and icon each one is shown with.

Out of scope for this MVP:
- Transactions and transfers between wallets, so a wallet's balance equals its starting balance for now (MVP 2).
- Custom categories created by the user; only the defaults exist. The model already supports them.
- Deleting a wallet permanently.
- Choosing a wallet's color; it is assigned automatically.

## Capabilities

### New Capabilities
- `wallets`: creating, listing, editing, archiving and restoring a user's wallets, the total balance, and how amounts are entered.
- `categories`: the default expense and income categories and who can see which categories.

### Modified Capabilities
- None. The Wallets page stops being a placeholder, which `app-shell` already allows ("until a section's feature is built").

## Impact

- New app `finance/` with models `Wallet` and `Category`, two migrations (schema and default categories), admin, forms, views, URLs and tests.
- `core/sections.py` and `core/context_processors.py`: the Wallets section now points at `finance:wallets`, and every wallet page marks Wallets as active.
- New shared form field for Rupiah amounts in `core/forms.py`, reused by transactions and budgets later.
- New templates under `templates/finance/` and a reusable HTMX modal partial.
- No new dependencies.
