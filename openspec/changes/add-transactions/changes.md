# Changes: add-transactions (MVP 2)

Implementation log for this change: what was created or modified, and where the result differs from `proposal.md`, `design.md` and `tasks.md`. Per-commit detail is in `openspec/commits/`.

- **Status:** implemented, not archived yet (open: task 6.1 real-browser check)
- **Date:** 2026-11-17
- **Tests:** 155 passing in about 3 s; 65 of them new (14 balance and model, 41 activity, 10 demo)
- **Validation:** `openspec validate add-transactions --strict` passes

## Commits

| Commit | Message | Record |
|---|---|---|
| `e9d43b7` | feat: plan the add-transactions change for transactions, transfers and the demo account | `add-transactions-proposal.md` |
| `a6fbdf7` | feat: add transaction and transfer models with computed wallet balances | `add-transaction-and-transfer-models.md` |
| `f8ff966` | feat: add transactions page with add, edit and delete for transactions and transfers | `add-transactions-page.md` |
| `9e1ba0b` | feat: add the demo account with seed_demo and a working try demo button | `add-demo-account.md` |
| `05a739d` | feat: complete the add-transactions change log | `add-transactions-wrap-up.md` |
| this commit | feat: match the transactions page to the figma table and add csv export | `transactions-figma-table-and-csv.md` |

## Routes

| Method | URL | Name | Purpose |
|---|---|---|---|
| GET | `/transactions/` | `finance:transactions` | Month page: month picker, filters, summary line, table, pagination |
| GET | `/transactions/export/` | `finance:transactions_export` | CSV of the filtered month (all pages) |
| GET/POST | `/transactions/new/` | `finance:transaction_create` | Add transaction |
| GET/POST | `/transactions/<id>/edit/` | `finance:transaction_edit` | Edit transaction |
| GET/POST | `/transactions/<id>/delete/` | `finance:transaction_delete` | Confirm / delete |
| GET/POST | `/transfers/new/` | `finance:transfer_create` | Add transfer |
| GET/POST | `/transfers/<id>/edit/` | `finance:transfer_edit` | Edit transfer |
| GET/POST | `/transfers/<id>/delete/` | `finance:transfer_delete` | Confirm / delete |
| POST | `/demo/` | `accounts:demo` | Sign in as the demo user |

Removed: `core:transactions` placeholder.

## Data

| Table | Notes |
|---|---|
| `finance_transaction` | `user`, `wallet` (PROTECT), `category` (PROTECT), `kind` (from category), `amount` (bigint, > 0), `date`, `description`, `note`, `source`, timestamps; indexes `(user, date)`, `(wallet, kind)` |
| `finance_transfer` | `user`, `from_wallet`, `to_wallet` (PROTECT, must differ), `amount` (> 0), `date`, `note`, timestamps; index `(user, date)` |

Migration: `finance.0003_transactions_and_transfers`. Wallet balance is now `initial + income − expense + transfers in − transfers out`, computed with four correlated subqueries.

## Files

### Backend

| File | What |
|---|---|
| `finance/models.py` | `Transaction`, `Transfer`, their querysets (`in_month`, `search`, `totals`, `touching`), `month_bounds`, new `with_balance()` |
| `finance/forms.py` | `TransactionForm`, `TransferForm` |
| `finance/views_activity.py` | Transactions page; create/edit/delete for transactions and transfers |
| `finance/urls.py` | seven routes |
| `finance/admin.py` | admin for both models |
| `finance/demo.py`, `finance/management/commands/seed_demo.py` | demo data generator and command |
| `accounts/views.py`, `accounts/urls.py` | `demo_sign_in` |
| `core/htmx.py` | `safe_next` |
| `core/sections.py`, `core/views.py`, `core/urls.py` | Transactions section in `finance`; placeholder removed |
| `config/settings.py` | MD5 password hasher during tests |

### Frontend

| File | What |
|---|---|
| `templates/finance/transactions.html` | month page |
| `templates/finance/_transaction_fields.html`, `_transfer_fields.html`, `_transaction_delete_body.html`, `_transfer_delete_body.html` | form and confirmation bodies |
| `templates/finance/wallets.html` | Transfer button, View activity, icon actions, negative balances in clay |
| `templates/components/modal_form.html`, `form_page.html` | Delete action, `next`, no-submit mode |
| `templates/accounts/login.html` | working demo button |

### Tests

| File | Tests |
|---|---|
| `finance/tests/test_balances.py` | 14 |
| `finance/tests/test_activity.py` | 36 |
| `finance/tests/test_demo.py` | 10 |

### Documentation

`README.md` (demo data), `docs/decisions.md` (seven rows, local), `WORKPLAN.md` (MVP 2 ticked, local).

## Differences from the plan

- **Transactions page follows the Figma table** instead of day groups with subtotals: month picker in the heading, Export CSV in the toolbar, a one-line summary (count, income, expenses, net), columns Transaction / Category / Wallet / Date / Amount, neutral row icons, sideways scroll on phones. Font sizes stay on the docs/STYLE.md scale. The `transactions` and `transfers` spec deltas were updated (daily subtotals removed; table, summary line and CSV requirements added).
- **CSV export added** (planned as out of scope), with formula protection for text cells.
- **Fast password hasher in tests** was not planned. It cut the suite from about 70 s to about 3 s.
- **Wallet card actions became icon buttons** (Edit, Archive) to fit "View activity" on phones.
- **Category icons are darkened** (75% category color, 25% ink) because the lighter palette colors were too faint on the tile.
- **The demo user is "Aditya Ramadhan"** (as in the Figma design) with the email `demo@walleto.app`.
- **Filter selects include archived wallets,** labelled "(archived)", so their history stays reachable from the filter, as the `wallets` delta requires.

## Verification

- **Automated:** 150 tests pass; `manage.py check` reports no issues.
- **Visual (headless Edge):** Transactions at 1440px and 390px, add-transaction modal, Wallets with real balances; balances match a hand calculation.
- **Demo data:** `seed_demo` on the development database produced 229 transactions and 31 transfers, all balances positive.
- **Not yet done:** a real-browser pass (task 6.1).

## Open items before archiving

1. Task 6.1: in a real browser, try the demo account; on Transactions, change month, filter by wallet and category, search, page through, add/edit/delete a transaction and a transfer; on Wallets, use Transfer and View activity; check at phone width.
2. Then run `openspec archive add-transactions`.
