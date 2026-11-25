# Archive the Date Range Picker and MVP 4 (Savings Goals), and Sync Their Specs

**Created:** 2026-11-25
**Last edited:** 2026-11-25
**Status:** Implemented
**Commit:** `ec883a6` chore: archive add-date-range and add-savings-goals
**Branch:** `main`, parent `4c057fa`
**OpenSpec changes:** `add-date-range` and `add-savings-goals` (MVP 4), closing both
**Trigger:** `/opsx:archive add-date-range`, then `/opsx:archive add-savings-goals`; the developer chose to sync both times, then asked to merge the two small commits into one.

## Why this is recorded here

- Home and Transactions specs now describe periods instead of single months, and the period picker becomes its own spec.
- MVP 4 is closed, and savings goals become an official spec.

## What is built

| Area | Change |
|---|---|
| `openspec/specs/dashboard/spec.md` | six requirements replaced by the delta's period versions. "Remaining this month", "Income and expenses" and "Where it goes" are reworded under 500 characters for strict validation, with no change in meaning |
| `openspec/specs/transactions/spec.md` | five requirements replaced: one period at a time, summary, filters, pagination, export |
| `openspec/specs/period-picker/spec.md` | new, six requirements |
| `openspec/changes/add-date-range/` | moved to `openspec/changes/archive/2026-11-25-add-date-range/`; `changes.md` status closed |
| `openspec/specs/savings-goals/spec.md` | new, 14 requirements |
| `openspec/specs/demo-account/spec.md` | adds "Demo savings goals" |
| `openspec/specs/transactions/spec.md` | adds "Goal movements in the Transactions list" and "Goal movements in the CSV export" |
| `openspec/specs/wallets/spec.md` | "Wallets page and total balance" replaced; adds "Money set aside in goals" |
| `openspec/changes/add-savings-goals/` | moved to `openspec/changes/archive/2026-11-25-add-savings-goals/`; `changes.md` status closed |

## Requirements this establishes

1. **The period picker is a spec of its own**, shared by Home and Transactions.
2. **MVP 4 is closed.**

## Files changed

| File | Change |
|---|---|
| `openspec/specs/dashboard/`, `transactions/`, `period-picker/`, `savings-goals/`, `demo-account/`, `wallets/` | sync |
| `openspec/changes/archive/2026-11-25-add-date-range/`, `2026-11-25-add-savings-goals/` | the archived changes |
| `openspec/commits/README.md`, `add-assistant.md` | `4c057fa` filled in, this record |

## Verification

**Executed:**

- `openspec validate dashboard|transactions|period-picker|savings-goals|demo-account --type spec --strict`: all valid.
- `openspec list --json`: only `monthly-wallet-balances` is still active.

**Not executed:**

- None; no code changed.

## Known gaps

- **`wallets` strict validation still warns** about two requirements over 500 characters, as it did before this sync.
