# Wallet and Category Models with Default Categories

**Created:** 2026-11-16
**Last edited:** 2026-11-16
**Status:** Implemented
**Commit:** this commit
**Branch:** `main`, parent `5c5521c`
**OpenSpec change:** `add-wallets` (MVP 1), tasks 1.1–1.8, 5.1–5.2
**Trigger:** specs `wallets` and `categories`; every later money feature needs a wallet and a category.

## Why this is recorded here

- **A new app** (`finance`) that will hold all money data.
- **Two new tables and two migrations,** one of them a data migration that seeds shared rows.
- **Database-level rules** (partial unique indexes, a check constraint) that later code relies on.

## Context

- **Integer Rupiah.** `initial_balance` is a `BigIntegerField`; design decision 2.
- **Uniqueness lives in the database.** Active wallet names are unique per user ignoring case through a partial unique index on `(user, LOWER(name)) WHERE NOT is_archived`. Archived wallets don't block a name. Design decision 4.
- **Balance is never stored.** `with_balance()` annotates it; for now it equals `initial_balance`. Design decision 5.
- **Defaults are shared rows** with `user = NULL`, not copies per user. Design decision 7.
- **Category colors repeat.** There are seven expense categories and five chart colors, so Health and Others reuse the first two colors, as STYLE.md allows ("use in sequence").

## What is built

### `Wallet`

| Field | Type | Notes |
|---|---|---|
| `user` | FK `accounts.User`, `CASCADE` | owner |
| `name` | `CharField(40)` | trimmed on save |
| `type` | `cash` / `bank` / `ewallet` | labels "Cash", "Bank account", "E-wallet" |
| `initial_balance` | `BigIntegerField`, default 0 | DB check `>= 0` |
| `color` | `CharField(7)` | assigned on create, cycling `#426050`, `#597D73`, `#8D826E`, `#A39C87`, `#1F5C4A` |
| `is_archived`, `archived_at` | bool, datetime | set by `archive()`, cleared by `restore()` |
| `created_at`, `updated_at` | datetimes | default ordering by `created_at` |

Constraints: `unique_active_wallet_name_per_user`, `wallet_initial_balance_not_negative`.

`monogram` property: "Rp" for cash; initials of the first two words; a single word of up to four letters in capitals; otherwise the first two letters ("Go").

`WalletQuerySet`: `for_user(user)`, `active()`, `archived()`, `with_balance()`, `total_balance()` (one `SUM` query, 0 when empty).

### `Category`

| Field | Type | Notes |
|---|---|---|
| `user` | FK, nullable | `NULL` = default |
| `name` | `CharField(40)` | |
| `kind` | `expense` / `income` | |
| `color`, `icon`, `order` | | display |

Constraints: `unique_default_category_name` on `(LOWER(name), kind) WHERE user IS NULL`; `unique_user_category_name` on `(user, LOWER(name), kind) WHERE user IS NOT NULL`.

`CategoryQuerySet`: `for_user(user)` (defaults + own), `expense()`, `income()`.

### Default categories (migration `0002_default_categories`)

| Kind | Name | Color | Icon |
|---|---|---|---|
| expense | Food & drinks | #1F5C4A | food |
| expense | Shopping | #688373 | bag |
| expense | Transport | #99AA99 | car |
| expense | Bills & utilities | #B8AD92 | home |
| expense | Entertainment | #D2CDBF | ticket |
| expense | Health | #1F5C4A | heart |
| expense | Others | #688373 | other |
| income | Salary | #1F5C4A | briefcase |
| income | Other income | #688373 | gift |

The migration is reversible and uses `update_or_create`, so running it twice changes nothing.

### Icons

Seven icons added to `{% icon %}` in the Figma line style: `heart`, `ticket`, `briefcase`, `gift` (categories) and `archive`, `edit`, `restore` (wallet actions in the next commit).

## Requirements this establishes

1. **Every money amount is an integer number of Rupiah.**
2. **A user can't have two active wallets with the same name,** whatever the letter case.
3. **A starting balance is never negative.**
4. **Wallet balances are read through `with_balance()`;** no code reads `initial_balance` as the balance.
5. **Categories are listed through `Category.objects.for_user(user)`,** so users never see each other's categories.

## Files changed

| File | Change |
|---|---|
| `finance/__init__.py`, `finance/apps.py`, `finance/views.py` | new (generated) |
| `finance/models.py` | `Wallet`, `Category`, their querysets |
| `finance/migrations/0001_initial.py` | tables and constraints |
| `finance/migrations/0002_default_categories.py` | nine default categories |
| `finance/admin.py` | admin for both models |
| `finance/tests/__init__.py`, `finance/tests/test_models.py` | 17 tests |
| `config/settings.py` | `finance` in `INSTALLED_APPS` |
| `core/templatetags/icons.py` | seven icons |
| `openspec/commits/README.md` | index: `5c5521c` filled in, this record added |
| `openspec/commits/add-wallets-proposal.md` | its own hash filled in |

## Verification

**Executed:**

- `migrate` applied `finance.0001` and `0002` on the development database; the nine categories are present in order.
- 17 tests pass (`manage.py test finance`): monograms, color cycling, trimming, case-insensitive active-name uniqueness, same name across users, archived name reuse, negative balance rejected by the database, archive and restore, balance and total (archived and other users' wallets excluded), empty total; nine defaults, order, colors and icons valid, `for_user` isolation, unique names per user and kind.

**Not executed:**

- The constraints on PostgreSQL (planned for MVP 8). Both are partial unique indexes and a check constraint, which PostgreSQL supports.

## Known gaps

- **No user-created categories yet.** The model and constraints support them; there is no UI.
- **Color assignment counts all of a user's wallets,** archived ones included, so colors keep cycling after archiving. Harmless.
