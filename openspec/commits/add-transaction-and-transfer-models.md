# Transaction and Transfer Models with Computed Wallet Balances

**Created:** 2026-11-17
**Last edited:** 2026-11-17
**Status:** Implemented
**Commit:** this commit
**Branch:** `main`, parent `e9d43b7`
**OpenSpec change:** `add-transactions` (MVP 2), tasks 1.1–1.7
**Trigger:** specs `transactions`, `transfers` and the `wallets` delta (balance from activity).

## Why this is recorded here

- **Two new tables** (migration `finance.0003`) that hold the core financial history.
- **Wallet balances stop being the starting balance.** Every page that shows a balance changes meaning with this commit.
- **A test-settings change** that affects every test run.

## Context

- **Balances are four correlated subqueries** (income, expenses, transfers in, transfers out), each `Coalesce(Sum, 0)`. Summing over joins would multiply rows when a wallet has several transactions and several transfers; a test reproduces that case. Design decision 3.
- **`kind` is copied from the category in `save()`** and is not editable, so it can't disagree with the category. Design decision 2.
- **`PROTECT` on every wallet and category foreign key.** A wallet with history can't be deleted even from the admin; archiving stays the only way to retire it.
- **Fast hasher in tests.** Tests create a user in almost every `setUp`; PBKDF2 made the suite take about 70 s. With MD5 under `manage.py test` only, it takes about 1.3 s. Production hashing is unchanged.

## What is built

### `Transaction`

| Field | Type | Notes |
|---|---|---|
| `user` | FK, `CASCADE` | owner |
| `wallet` | FK `Wallet`, `PROTECT` | |
| `category` | FK `Category`, `PROTECT` | |
| `kind` | `expense` / `income` | copied from the category, not editable |
| `amount` | `BigIntegerField` | DB check `> 0` |
| `date` | `DateField` | |
| `description` | `CharField(80)` | trimmed |
| `note` | `CharField(120)`, blank | |
| `source` | `manual` / `ai` | AI quick add arrives in MVP 6 |
| `created_at`, `updated_at` | | |

Indexes `(user, date)` and `(wallet, kind)`. Ordering newest first. `TransactionQuerySet`: `for_user`, `in_month(year, month)`, `search(text)` (description or note, case-insensitive), `income`, `expense`, `totals()` (income, expense, net in one aggregate).

### `Transfer`

| Field | Type | Notes |
|---|---|---|
| `user` | FK, `CASCADE` | |
| `from_wallet`, `to_wallet` | FK `Wallet`, `PROTECT` | DB check: different |
| `amount` | `BigIntegerField` | DB check `> 0` |
| `date`, `note`, timestamps | | |

`TransferQuerySet`: `for_user`, `in_month`, `touching(wallet)`, `search(text)` (note).

### Balance

`WalletQuerySet.with_balance()` → `initial_balance + income − expense + transfers_in − transfers_out`. `total_balance()` sums it unchanged. `month_bounds(year, month)` helper handles December → January.

## Requirements this establishes

1. **A wallet or category that has transactions or transfers can't be deleted.**
2. **Transaction and transfer amounts are always positive;** direction comes from `kind` or from the two wallets.
3. **Balances may be negative.**

## Files changed

| File | Change |
|---|---|
| `finance/models.py` | `Transaction`, `Transfer`, their querysets, `month_bounds`, new `with_balance()` |
| `finance/migrations/0003_transactions_and_transfers.py` | new |
| `finance/admin.py` | admin for both |
| `finance/tests/test_balances.py` | new: 14 tests |
| `config/settings.py` | `import sys`; MD5 hasher when running tests |
| `openspec/commits/README.md` | index: `e9d43b7` filled in, this record added |
| `openspec/commits/add-transactions-proposal.md` | its own hash filled in |

## Verification

**Executed:**

- `migrate` applied `finance.0003`.
- 104 tests pass in 1.3 s. New ones: the spec's balance example (1.000.000 → 1.050.000), several transactions and transfers on one wallet not multiplying, transfers keeping the total, negative balance, edit and delete updating the balance, wallet without activity; kind from category, trimming, amount > 0, `PROTECT` on a wallet with history, month filter and totals, December bounds, search; same-wallet transfer rejected by the database.

**Not executed:**

- None.

## Known gaps

- **No UI yet** for transactions and transfers; next commit.
