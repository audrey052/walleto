# Show Only Income and Expenses in the Transactions Summary

**Created:** 2026-11-17
**Last edited:** 2026-11-17
**Status:** Implemented
**Commit:** this commit
**Branch:** `main`, parent `90c528b`
**OpenSpec change:** `add-transactions` (MVP 2), task 3.8
**Trigger:** the developer asked to drop Net from the summary line and to label the totals "Income" and "Expenses" instead of "Monthly income" and "Monthly expenses".

## Why this is recorded here

It changes a spec requirement (`Month summary line`) of the active change.

## Context

- The month picker already says which month is shown, so "Monthly" was redundant.
- Net is still computed by `TransactionQuerySet.totals()` (used by tests and available for the dashboard later); it is only no longer displayed here.

## What is built

The summary line now reads: "N transactions in November 2026 · Income +Rp… · Expenses Rp…".

## Requirements this establishes

1. **The Transactions summary shows income and expenses only,** labelled "Income" and "Expenses".

## Files changed

| File | Change |
|---|---|
| `templates/finance/transactions.html` | Net removed; labels shortened |
| `finance/tests/test_activity.py` | asserts "Expenses" and the absence of "Monthly expenses" and Net |
| `openspec/changes/add-transactions/specs/transactions/spec.md` | `Month summary line`: net removed, labels named |
| `openspec/changes/add-transactions/proposal.md`, `changes.md` | wording; commit table |
| `openspec/commits/README.md` | index: `90c528b` filled in, this record added |
| `openspec/commits/transactions-figma-table-and-csv.md` | its own hash filled in |

## Verification

**Executed:**

- `python manage.py test`: all pass.
- `openspec validate add-transactions --strict`: valid.

**Not executed:**

- None.

## Known gaps

- None.
