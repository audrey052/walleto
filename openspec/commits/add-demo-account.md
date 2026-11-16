# Demo Account with seed_demo and "Try demo account"

**Created:** 2026-11-17
**Last edited:** 2026-11-17
**Status:** Implemented
**Commit:** `9e1ba0b` feat: add the demo account with seed_demo and a working try demo button
**Branch:** `main`, parent `f8ff966`
**OpenSpec change:** `add-transactions` (MVP 2), tasks 5.1–5.3
**Trigger:** spec `demo-account`; the sign-in page showed a disabled "Try demo account" button since MVP 0.

## Why this is recorded here

- **A new public action** (`POST /demo/`) that signs a visitor in without credentials.
- **A management command** that deletes and rebuilds one user's data, which has to stay strictly limited to that user.

## Context

- **Fixed user, no password.** `demo@walleto.app` with an unusable password; the only way in is the demo button. No password lives in the repository. Design decision 9.
- **Deterministic per day.** The generator is `random.Random("walleto-demo-<date>")`, so two runs on the same day give identical data and tests can compare snapshots.
- **No overdraft.** The generator keeps a running balance per wallet and skips any expense or transfer the wallet can't cover, so every demo balance stays ≥ 0.
- **Order inside a day:** monthly income and bills, then transfers, then weekly and everyday spending, so salary lands before the day's spending.
- **`bulk_create`** inserts about 260 rows at once. It skips `Transaction.save()`, so `kind` is set explicitly from the category.
- **Shared demo user:** visitors can change its data. `seed_demo` restores it; scheduling it is part of deployment (MVP 8).

## What is built

### Data (`finance/demo.py`, `build_demo(today)`)

| Part | Content |
|---|---|
| Wallets | BCA (4.250.000), GoPay (85.000), OVO (42.500), Bank Jago (1.500.000), Cash (350.000) |
| Monthly | Salary 12.500.000 on the 1st (BCA); IndiHome, Spotify, Telkomsel, PAM Jaya, PLN token; freelance income on the 18th (Bank Jago) |
| Weekly | Superindo groceries (Sat), Pertamina fuel (Sun), LaundryKlin (Wed) |
| Everyday | GoFood, Kopi Kenangan, Fore, Warung Bu Kris, Bakmi GM, Grab, Gojek, Indomaret, Tokopedia, Shopee, Cinema XXI, Kimia Farma, each with a daily chance and an amount range |
| Transfers | BCA → Bank Jago savings (2nd), BCA → Cash (1st and 15th), BCA → GoPay (Mondays), BCA → OVO (Thursdays) |
| Range | first day of the month two months back, up to `today` |

Amounts are random within each range and rounded to Rp500, so most are irregular (Rp67.500, not Rp70.000).

On the development database on 17 Nov 2026: 229 transactions, 31 transfers; BCA Rp15.207.030, GoPay Rp249.500, OVO Rp764.500, Bank Jago Rp10.058.000, Cash Rp1.084.000.

### Command

`python manage.py seed_demo` rebuilds the demo data for today and prints counts and balances.

### Sign-in

| Method | URL | Name | Access | Purpose |
|---|---|---|---|---|
| POST | `/demo/` | `accounts:demo` | public (`@login_not_required`, `@require_POST`) | Create the demo data if the demo user has no wallets, sign in, toast "You're using the demo account.", go to the Dashboard |

`templates/accounts/login.html`: the button is now a POST form, with "Three months of sample data. No sign-up needed." under it.

## Requirements this establishes

1. **Rebuilding demo data touches only `demo@walleto.app`.**
2. **The demo user can only be entered through the POST button.**

## Files changed

| File | Change |
|---|---|
| `finance/demo.py` | new: generator, `get_demo_user`, `build_demo` |
| `finance/management/__init__.py`, `finance/management/commands/__init__.py`, `finance/management/commands/seed_demo.py` | new |
| `finance/tests/test_demo.py` | new: 10 tests |
| `accounts/views.py`, `accounts/urls.py` | `demo_sign_in`, `/demo/` |
| `templates/accounts/login.html` | enabled demo button |
| `openspec/commits/README.md` | index: `f8ff966` filled in, this record added |
| `openspec/commits/add-transactions-page.md` | its own hash filled in |

## Verification

**Executed:**

- `seed_demo` on the development database (output above).
- **150 tests pass.** New ones: five wallets in order, unusable password, salaries on 1 Sep, 1 Oct and 1 Nov, first and last dates, no future transfers, expenses on more than 80% of days, irregular amounts, every balance ≥ 0, identical data for the same date, reset removes leftovers and keeps other users, command output; demo sign-in creates data when missing and shows the toast, reuses existing data, GET is 405 and creates nothing, sign-in page posts to `/demo/` with the button enabled.

**Not executed:**

- The demo account in a real browser.

## Known gaps

- **Shared state:** one visitor's edits are visible to the next until `seed_demo` runs again. A schedule comes with deployment (MVP 8).
- **Data stops at the day it was generated;** if not reseeded, the current month gradually empties as days pass.
