# Match the Budget Rows to the Figma Spacing and Archive MVP 3

**Created:** 2026-11-18
**Last edited:** 2026-11-18
**Status:** Implemented
**Commit:** this commit
**Branch:** `main`, parent `e3e407f`
**OpenSpec change:** `add-budgets` (MVP 3) and `redesign-wallets-page`, closing both
**Trigger:** The developer asked to close MVP 3 and refine the Budget page to the Figma Make Budget section (`SqCtFlkW2pwTXgwnAeHSdb`), and archived `redesign-wallets-page` with `/opsx:archive`.

## Why this is recorded here

Archiving makes `budgets` an official spec and adds requirements to `transactions`, `demo-account`, `wallets` and `transfers` in `openspec/specs/`. The Budget template's row spacing changes.

## Context

- The Budget page already had the Figma structure (plan panel, "A place for every Rupiah" list). Only spacing and column widths differed.
- Task 7.2 of `add-budgets` and the real-browser check of `redesign-wallets-page` were closed at the developer's request; the developer does the real-browser pass.

## What is built

| Area | Change |
|---|---|
| Budget rows | 25px padding, 180px name column, 120px amounts, 35px percent, 6px between name and status (Figma `.budget-detail-row`); on phones the bar starts under the name |
| `openspec/specs/budgets/` | new, from the `add-budgets` delta |
| `openspec/specs/transactions/`, `demo-account/` | budget warning toast, demo budgets added |
| `openspec/specs/wallets/`, `transfers/` | `redesign-wallets-page` delta merged: breakdown, trend, row actions, recent transfers, overdraft rule, transfer preview; monogram removed |

## Requirements this establishes

1. **MVP 3 is closed.** The next change is MVP 4 (Savings goals).

## Files changed

| File | Change |
|---|---|
| `templates/finance/budget.html` | Figma row spacing |
| `openspec/changes/add-budgets/` | moved to `openspec/changes/archive/2026-11-18-add-budgets/`; task 7.2 ticked; changes.md closed |
| `openspec/changes/redesign-wallets-page/` | moved to `openspec/changes/archive/2026-11-18-redesign-wallets-page/`; changes.md closed with `e3e407f` |
| `openspec/specs/budgets/spec.md` | new |
| `openspec/specs/transactions/spec.md`, `demo-account/spec.md`, `wallets/spec.md`, `transfers/spec.md` | deltas merged |
| `openspec/commits/README.md`, `redesign-wallets-page.md`, `add-budgets.md` | `e3e407f` filled in, statuses, this record |

## Verification

**Executed:**

- `python manage.py test`: 235 tests OK.
- `openspec validate` on `budgets`, `transactions`, `demo-account`, `wallets` and `transfers`: valid.
- Headless Edge: Budget at 1440px and 390px compared with the local Figma Make build; bars run from x 554 to 1167 (Figma 552 to 1169).

**Not executed:**

- Real-browser pass of Budget and Wallets.

## Known gaps

- **`openspec validate --all --strict` still warns on two long `wallets` requirements,** as recorded in `archive-add-transactions.md`.
