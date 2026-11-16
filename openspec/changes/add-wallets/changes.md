# Changes: add-wallets (MVP 1)

Implementation log for this change: what was created or modified, and where the result differs from `proposal.md`, `design.md` and `tasks.md`. Per-commit detail is in `openspec/commits/`.

- **Status:** implemented, not archived yet (open: task 6.1 real-browser check)
- **Date:** 2026-11-16
- **Tests:** 90 passing in the whole suite; 57 of them are new (17 model, 10 amount field, 30 wallet views)
- **Validation:** `openspec validate add-wallets --strict` passes

## Commits

| Commit | Message | Record |
|---|---|---|
| `5c5521c` | feat: plan the add-wallets change for wallets and categories | `add-wallets-proposal.md` |
| `44b0090` | feat: add wallet and category models with default categories | `add-wallet-and-category-models.md` |
| `605f480` | feat: add wallets page with add, edit, archive and restore | `add-wallets-page.md` |
| this commit | feat: complete the add-wallets change log | `add-wallets-wrap-up.md` |

## Routes

| Method | URL | Name | Purpose |
|---|---|---|---|
| GET | `/wallets/` | `finance:wallets` | Wallets page |
| GET/POST | `/wallets/new/` | `finance:wallet_create` | Add wallet |
| GET/POST | `/wallets/<id>/edit/` | `finance:wallet_edit` | Edit wallet |
| GET/POST | `/wallets/<id>/archive/` | `finance:wallet_archive` | Confirm / archive |
| POST | `/wallets/<id>/restore/` | `finance:wallet_restore` | Restore |

Removed: `core:wallets` placeholder.

## Data

| Table | Notes |
|---|---|
| `finance_wallet` | `user`, `name`, `type`, `initial_balance` (bigint, ≥ 0), `color`, `is_archived`, `archived_at`, timestamps; partial unique index on active `(user, LOWER(name))` |
| `finance_category` | `user` (NULL = default), `name`, `kind`, `color`, `icon`, `order`; partial unique indexes for defaults and per user |

Migrations: `finance.0001_initial` (schema), `finance.0002_default_categories` (nine defaults, reversible).

## Files

### Backend

| File | What |
|---|---|
| `finance/models.py` | `Wallet` (monogram, color cycling, archive/restore), `WalletQuerySet` (`for_user`, `active`, `archived`, `with_balance`, `total_balance`), `Category`, `CategoryQuerySet` (`for_user`, `expense`, `income`) |
| `finance/forms.py` | `WalletForm` |
| `finance/views.py`, `finance/urls.py` | five wallet views |
| `finance/admin.py` | admin for wallets and categories |
| `core/forms.py` | `AmountField` |
| `core/htmx.py` | `is_htmx`, `render_form`, `redirect_after_save` |
| `core/sections.py`, `core/context_processors.py` | Wallets section in `finance`, `match` prefix for active state |
| `core/templatetags/icons.py` | `heart`, `ticket`, `briefcase`, `gift`, `archive`, `edit`, `restore` |
| `config/settings.py`, `config/urls.py` | `finance` app and URLs |

### Frontend

| File | What |
|---|---|
| `templates/finance/wallets.html` | total, cards, archived list, empty state, modal root |
| `templates/finance/_wallet_fields.html`, `_wallet_archive_body.html` | form bodies |
| `templates/components/modal_form.html` | self-opening HTMX `<dialog>` form |
| `templates/components/form_page.html` | full-page form fallback |

### Tests

| File | Tests |
|---|---|
| `finance/tests/test_models.py` | 17 |
| `finance/tests/test_views.py` | 30 |
| `core/test_forms.py` | 10 |
| `accounts/tests.py`, `core/tests.py` | references updated to `finance:wallets` |

## Differences from the plan

- **Three extra icons** (`archive`, `edit`, `restore`) for the card actions and the archived list; task 1.7 updated.
- **Restore needs no confirmation,** unlike archive, because it is just as easy to undo. Not specified either way in the spec.
- **`core/htmx.py` was added** as a shared helper rather than keeping the HTMX/page switch inside `finance/views.py`, since transactions and budgets need the same behavior.
- **Restore errors use an error toast** with the wording "You already have an active wallet named {name}. Rename it before restoring this one.", which the spec describes only as "an error toast explains that the name is in use".

## Verification

- **Automated:** 90 tests pass; `manage.py check` reports no issues.
- **Visual (headless Edge):** wallets page with 4 active and 1 archived wallet at 1440px and 390px, add-wallet modal with errors at 1440px, empty state.
- **Not yet done:** a real-browser pass (task 6.1).

## Open items before archiving

1. Task 6.1: in a real browser, add a wallet, trigger an error in the modal, edit, archive, open "Archived wallets", restore; check at phone width.
2. Then run `openspec archive add-wallets`.
