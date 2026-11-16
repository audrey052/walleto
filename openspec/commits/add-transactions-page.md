# Transactions Page with Add, Edit and Delete for Transactions and Transfers

**Created:** 2026-11-17
**Last edited:** 2026-11-17
**Status:** Implemented
**Commit:** this commit
**Branch:** `main`, parent `a6fbdf7`
**OpenSpec change:** `add-transactions` (MVP 2), tasks 2.1–2.3, 3.1–3.7, 4.1–4.5
**Trigger:** specs `transactions`, `transfers` and the `wallets` delta.

## Why this is recorded here

- **Seven new routes,** six of them changing data.
- **The Transactions section stops being a placeholder,** and the Wallets page gains "Transfer" and "View activity".
- **Shared form plumbing grows:** modals can carry a Delete action, a `next` address and a no-submit mode, used by every later form.

## Context

- **One month per page, transfers merged in Python.** Transactions and transfers for the month are two queries, merged and sorted newest first, then paginated at 50. A month holds a few hundred entries at most. Design decision 4.
- **Day subtotals come from the database,** one `GROUP BY date` over the filtered transactions, so a day split across two pages still shows its whole subtotal.
- **Filters are a GET form upgraded by HTMX** (`hx-get`, `hx-select="#results"`, `hx-push-url`, 300 ms debounce on search). The address always holds the filters; without JavaScript the form still submits. Design decision 5.
- **Filter IDs are looked up within the user's own wallets and categories,** so another user's ID is ignored rather than erroring or leaking.
- **`next` is only followed when it points to this site** (`url_has_allowed_host_and_scheme`). After saving, the default is the record's own month.
- **Income or expense follows the category.** The category select is grouped into Expense and Income.

## What is built

### Routes

| Method | URL | Name | Purpose |
|---|---|---|---|
| GET | `/transactions/` | `finance:transactions` | Month page; `?month=YYYY-MM&wallet=&category=&q=&page=` |
| GET/POST | `/transactions/new/` | `finance:transaction_create` | "Transaction added." |
| GET/POST | `/transactions/<id>/edit/` | `finance:transaction_edit` | "Transaction updated."; modal has Delete |
| GET/POST | `/transactions/<id>/delete/` | `finance:transaction_delete` | GET confirms; POST deletes; "Transaction deleted." |
| GET/POST | `/transfers/new/` | `finance:transfer_create` | "Transfer recorded."; explains when fewer than two wallets |
| GET/POST | `/transfers/<id>/edit/` | `finance:transfer_edit` | "Transfer updated." |
| GET/POST | `/transfers/<id>/delete/` | `finance:transfer_delete` | "Transfer deleted." |

The `core` Transactions placeholder was removed. The Transactions section matches both `finance:transaction*` and `finance:transfer*` view names.

### Forms (`finance/forms.py`)

| Form | Rules |
|---|---|
| `TransactionForm` | description required ("Enter a description, for example GoFood."); amount > 0 ("Amount must be greater than 0.", also when empty); date defaults to today in Jakarta and can't be in the future ("Date can't be in the future."); category from `Category.objects.for_user`, grouped; wallet from the user's active wallets plus the record's current one (labelled "(archived)"); a single active wallet is preselected |
| `TransferForm` | from and to from the same wallet set; "Choose two different wallets."; amount and date as above; `has_enough_wallets` |
| `WalletForm` | unchanged except the starting-balance help text now says it is the amount before using Walleto |

### Page (`templates/finance/transactions.html`)

- Heading with Transfer (when two or more active wallets) and Add transaction.
- Month navigator; no next link beyond the current month.
- Panel with search, wallet and category filters.
- `#results`: the month's income, expenses and net (stacked on phones); "N results … Clear filters" when filtering; column headings; day groups (date, signed subtotal); transaction rows (category icon tile, description, note, chip, wallet, signed amount); neutral transfer rows ("BCA → GoPay", Transfer chip, unsigned amount); pagination.
- Rows open their edit modal.
- Three empty states: no wallets, no transactions this month, no matches.

### Wallets page

"Transfer" button (two or more active wallets), "View activity" link per card (`/transactions/?wallet=<id>`), Edit and Archive as icon buttons, negative balances in clay.

### Shared

- `core/htmx.py`: `safe_next(request, default)`.
- `components/modal_form.html` and `form_page.html`: optional `delete_url`, `next`, `hide_submit`.

## Requirements this establishes

1. **Every list filter is scoped to the user's own objects.**
2. **A `next` address is only followed when it is on this site.**
3. **Delete always goes through a confirmation and a POST.**

## Files changed

| File | Change |
|---|---|
| `finance/forms.py` | `TransactionForm`, `TransferForm`, shared helpers |
| `finance/views_activity.py` | new: page and six create/edit/delete views |
| `finance/urls.py` | seven routes |
| `finance/tests/test_activity.py` | new: 36 tests |
| `core/htmx.py` | `safe_next` |
| `core/sections.py`, `core/views.py`, `core/urls.py` | Transactions moved to `finance`; placeholder removed |
| `accounts/tests.py`, `core/tests.py` | `core:transactions` → `finance:transactions` |
| `templates/finance/transactions.html` | new |
| `templates/finance/_transaction_fields.html`, `_transfer_fields.html`, `_transaction_delete_body.html`, `_transfer_delete_body.html` | new |
| `templates/finance/wallets.html` | Transfer, View activity, icon actions, negative balance color |
| `templates/components/modal_form.html`, `form_page.html` | Delete, next, hide-submit |
| `openspec/commits/README.md` | index: `a6fbdf7` filled in, this record added |
| `openspec/commits/add-transaction-and-transfer-models.md` | its own hash filled in |

## Verification

**Executed:**

- **140 tests pass** (about 3 s). New ones, with "today" frozen at 16 Nov 2026 in Jakarta:
  - forms: kind from category, today's default, zero and empty amount, future date, only own active wallets, archived wallet kept when editing, another user's category, grouped categories; transfer valid, same wallet, two-wallet rule, another user's wallet
  - page: current month by default with the spec's summary (12.500.000 / 5.847.500 / 6.652.500), previous month, invalid and future months, day groups with subtotal −99.500 excluding transfers, newest day first, case-insensitive search across notes, wallet filter keeps transfers, category filter hides them, foreign filter IDs ignored, no-results state, 60 entries → two pages with the full-day subtotal on page 2, other users' rows hidden, Transactions active on its pages
  - CRUD: create redirects to its month with toast, safe vs external `next`, error keeps the modal, edit and delete update balances, delete confirms first, no-wallet message; transfer keeps the total, one-wallet refusal, edit and delete restore balances
  - wallets page: real balances (including negative), activity link, archived wallet's history still listed
  - privacy: edit and delete of another user's transaction or transfer are 404 for GET and POST, records unchanged
- **Headless Edge screenshots** at 1440px (list, add modal, wallets) and 390px (list). The balances shown match a hand calculation.

**Fixed during implementation:**

- The month summary's three columns overflowed at 390px; it now stacks on phones.
- Light category colors made icons too faint; tiles now use the category color mixed 75% with ink.
- A positive day subtotal had no sign; it now shows "+" in the accent color.

**Not executed:**

- A real-browser pass of filtering without reload, the modal Delete flow and pagination links.

## Known gaps

- **No CSV export** (in the Figma design; later).
- **Filter selects list archived wallets too,** labelled "(archived)", so their history stays reachable.
