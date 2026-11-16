# Archive the setup-foundation Change

**Created:** 2026-11-16
**Last edited:** 2026-11-16
**Status:** Implemented
**Commit:** `28d1f2f` feat: archive the setup-foundation change
**Branch:** `main`, parent `3f2dae8`
**OpenSpec change:** `setup-foundation` (MVP 0), closing
**Trigger:** MVP 0 accepted by the developer after the superuser sign-in (task 2.4) and the real-browser check (task 10.1).

## Why this is recorded here

Archiving moves the MVP 0 specs into `openspec/specs/`, which from now on is the official description of how Walleto behaves. Later changes modify these specs through deltas instead of adding new ones.

## Context

- `openspec archive setup-foundation` was run by the developer. It moved the change to `openspec/changes/archive/2026-11-16-setup-foundation/` and merged its three delta specs into `openspec/specs/`.
- The archived `changes.md` still said "not archived yet"; it is corrected here.

## What is built

| Spec | Requirements now in `openspec/specs/` |
|---|---|
| `user-auth` | registration, sign-in, sign-out, pages require sign-in, signed-in users skip the sign-in pages |
| `app-shell` | sidebar navigation, collapsible sidebar, topbar, profile menu, placeholder pages, toasts, mobile layout, development style guide |
| `money-format` | Rupiah display format, income and expense signs |

## Requirements this establishes

1. **`openspec/specs/` is the source of truth** for current behavior. A later change that alters these behaviors must use `MODIFIED Requirements` deltas against these files.

## Files changed

| File | Change |
|---|---|
| `openspec/changes/setup-foundation/` | moved to `openspec/changes/archive/2026-11-16-setup-foundation/` |
| `openspec/specs/user-auth/spec.md`, `app-shell/spec.md`, `money-format/spec.md` | new (merged from the change) |
| `openspec/changes/archive/2026-11-16-setup-foundation/changes.md` | status set to archived; open items cleared |
| `openspec/commits/README.md` | index: hash `3f2dae8` filled in, this record added |
| `openspec/commits/per-commit-records.md` | its own hash filled in |

## Verification

**Executed:**

- All 42 tasks in the archived `tasks.md` are ticked.
- `openspec/specs/` contains the three specs with their purpose and requirements.

**Not executed:**

- None.

## Known gaps

- None.
