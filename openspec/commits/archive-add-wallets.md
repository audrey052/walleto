# Archive the add-wallets Change

**Created:** 2026-11-16
**Last edited:** 2026-11-16
**Status:** Implemented
**Commit:** this commit
**Branch:** `main`, parent `bdb1803`
**OpenSpec change:** `add-wallets` (MVP 1), closing
**Trigger:** MVP 1 accepted and archived by the developer with `openspec archive add-wallets`.

## Why this is recorded here

Archiving makes `wallets` and `categories` part of the official behavior in `openspec/specs/`. MVP 2 changes wallet balances, so it will modify the `wallets` spec through a delta.

## Context

- The developer ran `openspec archive add-wallets`, which moved the change to `openspec/changes/archive/2026-11-16-add-wallets/` and merged its specs.
- Task 6.1 (real-browser pass) was still unticked in the archived copy; archiving was taken as the developer's confirmation, and it is ticked here.

## What is built

| Spec | Requirements now in `openspec/specs/` |
|---|---|
| `wallets` | create, Rupiah amount input, page and total balance, monogram, edit, archive and restore, privacy, forms open in place |
| `categories` | default categories, category visibility |

## Requirements this establishes

1. **MVP 2 must update the `wallets` spec with a `MODIFIED` delta** where balance stops being equal to the starting balance.

## Files changed

| File | Change |
|---|---|
| `openspec/changes/add-wallets/` | moved to `openspec/changes/archive/2026-11-16-add-wallets/` |
| `openspec/specs/wallets/spec.md`, `openspec/specs/categories/spec.md` | new (merged) |
| `openspec/changes/archive/2026-11-16-add-wallets/tasks.md` | task 6.1 ticked |
| `openspec/changes/archive/2026-11-16-add-wallets/changes.md` | status archived, last commit hash, open items cleared |
| `openspec/commits/README.md` | index: `bdb1803` filled in, this record added |
| `openspec/commits/add-wallets-wrap-up.md` | its own hash filled in |

## Verification

**Executed:**

- `openspec validate --all --strict`: all specs valid.

**Not executed:**

- None.

## Known gaps

- None.
