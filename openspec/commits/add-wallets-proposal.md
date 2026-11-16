# Plan the add-wallets Change (MVP 1)

**Created:** 2026-11-16
**Last edited:** 2026-11-16
**Status:** Implemented
**Commit:** this commit
**Branch:** `main`, parent `28d1f2f`
**OpenSpec change:** `add-wallets` (MVP 1), planning
**Trigger:** WORKPLAN MVP 1 (Wallets + categories), started after MVP 0 was archived.

## Why this is recorded here

It adds two new capabilities (`wallets`, `categories`) and fixes data-model decisions that transactions, budgets and the dashboard will depend on: integer Rupiah, archive instead of delete, balance as an annotation.

## Context

Four open questions from the work plan were settled with the recommended options, since no other preference was given:

| Question | Decision |
|---|---|
| One app or one per feature | One `finance` app |
| Amount type | `BigIntegerField`, whole Rupiah |
| Delete or archive wallets | Archive (and restore), no delete |
| Custom categories now | No; defaults only, model ready for custom ones |

## What is built

| File | Content |
|---|---|
| `proposal.md` | Why, what changes, out of scope (transactions, custom categories, delete, color choice) |
| `specs/wallets/spec.md` | 8 requirements, 17 scenarios: create, amount input, page and total, monogram, edit, archive and restore, privacy, modals |
| `specs/categories/spec.md` | 2 requirements, 4 scenarios: nine defaults, visibility and uniqueness |
| `design.md` | 10 decisions with rejected alternatives, 3 risks |
| `tasks.md` | 28 tasks in 6 groups |

## Requirements this establishes

1. **Amounts are whole Rupiah integers** in every model from now on.
2. **Money places are archived, never deleted.**
3. **A wallet's balance is always read through `with_balance()`,** never stored.

## Files changed

| File | Change |
|---|---|
| `openspec/changes/add-wallets/` (`.openspec.yaml`, `proposal.md`, `design.md`, `tasks.md`, `specs/wallets/spec.md`, `specs/categories/spec.md`) | new |
| `openspec/commits/README.md` | index: `28d1f2f` filled in, this record added |
| `openspec/commits/archive-setup-foundation.md` | its own hash filled in |

## Verification

**Executed:**

- `openspec validate add-wallets --strict`: valid.

**Not executed:**

- None; planning only.

## Known gaps

- None.
