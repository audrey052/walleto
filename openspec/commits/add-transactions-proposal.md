# Plan the add-transactions Change (MVP 2)

**Created:** 2026-11-16
**Last edited:** 2026-11-16
**Status:** Implemented
**Commit:** `e9d43b7` feat: plan the add-transactions change for transactions, transfers and the demo account
**Branch:** `main`, parent `8e2ebf5`
**OpenSpec change:** `add-transactions` (MVP 2), planning
**Trigger:** WORKPLAN MVP 2 (transactions and transfers), and the question whether money can be moved between wallets: yes, as transfers.

## Why this is recorded here

It adds three capabilities (`transactions`, `transfers`, `demo-account`) and the first `MODIFIED` delta to an archived spec (`wallets`), since balances stop being equal to the starting balance.

## Context

- **Transfers are their own records,** not a pair of income and expense transactions, so reports never have to exclude them. Design decision 1.
- **Income or expense follows from the category,** so the form can't contradict itself. Design decision 2.
- **Balances come from correlated subqueries,** because summing over joined transactions and transfers would multiply rows. Design decision 3.
- **The demo account is a fixed user signed in by a POST,** with no password in the repository. Design decision 9.

## What is built

| File | Content |
|---|---|
| `proposal.md` | Why, what changes, out of scope (budgets, CSV export, quick add, recurring) |
| `specs/transactions/spec.md` | 6 requirements, 17 scenarios |
| `specs/transfers/spec.md` | 4 requirements, 6 scenarios |
| `specs/demo-account/spec.md` | 2 requirements, 5 scenarios |
| `specs/wallets/spec.md` | `MODIFIED`: balance from activity (may be negative), "View activity", "Transfer" action; archived wallets excluded from new records but history kept |
| `design.md` | 9 decisions, 3 risks |
| `tasks.md` | 31 tasks in 6 groups |

## Requirements this establishes

1. **Transfers never count as income or expenses.**
2. **Forms only accept the user's own active wallets and visible categories.**
3. **No date in the future,** measured in Jakarta time.

## Files changed

| File | Change |
|---|---|
| `openspec/changes/add-transactions/` (`.openspec.yaml`, `proposal.md`, `design.md`, `tasks.md`, four spec deltas) | new |
| `openspec/commits/README.md` | index: `8e2ebf5` filled in, this record added |
| `openspec/commits/archive-add-wallets.md` | its own hash filled in |

## Verification

**Executed:**

- `openspec validate add-transactions --strict`: valid.

**Not executed:**

- None; planning only.

## Known gaps

- None.
