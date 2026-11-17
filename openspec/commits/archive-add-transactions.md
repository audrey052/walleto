# Archive the add-transactions Change

**Created:** 2026-11-17
**Last edited:** 2026-11-17
**Status:** Implemented
**Commit:** this commit
**Branch:** `main`, parent `511cfd4`
**OpenSpec change:** `add-transactions` (MVP 2), closing
**Trigger:** MVP 2 accepted and archived by the developer with `openspec archive add-transactions`.

## Why this is recorded here

Archiving makes `transactions`, `transfers` and `demo-account` part of the official behavior in `openspec/specs/`, and applies the `wallets` delta (balances computed from transactions and transfers). MVP 3 (`add-budgets`) adds requirements to `transactions` and `demo-account` on top of these specs.

## Context

- The developer ran `openspec archive add-transactions`, which moved the change to `openspec/changes/archive/2026-11-17-add-transactions/` and merged its specs.
- Task 6.1 (real-browser pass) was still unticked in the archived copy; archiving was taken as the developer's confirmation, and it is ticked here, as was done for `add-wallets`.

## What is built

| Spec | Requirements now in `openspec/specs/` |
|---|---|
| `transactions` | record, one month at a time, summary line, table, filter and search, pagination, CSV export (amounts, transfers, safe text), edit and delete, privacy |
| `transfers` | moving money between the user's own wallets |
| `demo-account` | demo data, try the demo account |
| `wallets` | balance and total now include transactions and transfers; cards link to their activity |

## Requirements this establishes

1. **MVP 3 extends `transactions` and `demo-account` with `ADDED` requirements** (budget warning toast, demo budgets) rather than rewriting the archived ones.

## Files changed

| File | Change |
|---|---|
| `openspec/changes/add-transactions/` | moved to `openspec/changes/archive/2026-11-17-add-transactions/` |
| `openspec/specs/transactions/`, `transfers/`, `demo-account/` | new (merged) |
| `openspec/specs/wallets/spec.md` | delta merged |
| `openspec/changes/archive/2026-11-17-add-transactions/tasks.md` | task 6.1 ticked |
| `openspec/changes/archive/2026-11-17-add-transactions/changes.md` | status archived, last commit hash, open items cleared |
| `openspec/commits/README.md` | index: `511cfd4` filled in, this record added |
| `openspec/commits/restore-transactions-template.md` | its own hash filled in |

## Verification

**Executed:**

- `openspec validate --all`: 9 of 9 valid.

**Not executed:**

- None.

## Known gaps

- **`openspec validate --all --strict` fails on the `wallets` spec.** Requirement 6 ("Wallets page and total balance", merged from the MVP 2 delta) is longer than 500 characters, which strict mode reports. It is left as merged; splitting it is a separate spec-only change.
