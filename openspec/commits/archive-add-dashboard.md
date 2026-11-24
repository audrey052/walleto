# Archive MVP 5 (Home) and Sync Its Spec

**Created:** 2026-11-24
**Last edited:** 2026-11-24
**Status:** Implemented
**Commit:** this commit
**Branch:** `main`, parent `9c72adc`
**OpenSpec change:** `add-dashboard` (MVP 5), closing it
**Trigger:** `/opsx:archive add-dashboard`. The developer first chose "Archive without syncing", then asked to sync the spec after all, together with `app-shell`.

## Why this is recorded here

MVP 5 is closed and `dashboard` becomes an official spec, which `add-date-range` modifies. `app-shell` and `demo-account` catch up with the Home rename, the removed breadcrumb and the sidebar handle from `d4284f7`.

## Context

- All artifacts were done and 10 of 10 tasks ticked.
- The delta held nine ADDED requirements (Dashboard month, Remaining this month, Projection line, How a past month ended, Income and expenses, Daily spending chart, Where it goes, Figures match the other pages, Dashboard is private).

## What is built

| Area | Change |
|---|---|
| `openspec/changes/add-dashboard/` | moved to `openspec/changes/archive/2026-11-24-add-dashboard/`; `changes.md` status and commit hash closed |
| `openspec/specs/dashboard/spec.md` | new, from the archived delta's nine ADDED requirements, synced by hand after the archive |
| `openspec/specs/app-shell/spec.md` | sections start with "Home"; the sidebar collapses with the edge handle; the topbar shows the date and no breadcrumb; the home address shows Home |
| `openspec/specs/demo-account/spec.md` | the demo sign-in opens Home |

## Requirements this establishes

1. **MVP 5 is closed.**
2. **The first section is called Home in the specs too.**

## Files changed

| File | Change |
|---|---|
| `openspec/changes/archive/2026-11-24-add-dashboard/` | the archived change |
| `openspec/specs/dashboard/spec.md`, `app-shell/spec.md`, `demo-account/spec.md` | spec sync |
| `openspec/commits/README.md`, `goal-card-opens-goal.md` | `9c72adc` filled in, this record |

## Verification

**Executed:**

- `openspec list --json`: `add-dashboard` is no longer an active change.
- `openspec validate --specs --strict`: `dashboard`, `app-shell` and `demo-account` pass. `wallets` still fails on two long-requirement warnings from before this commit.
- `openspec validate add-date-range --strict`: valid, with no note about a missing `dashboard` spec.

**Not executed:**

- None.

## Known gaps

- **`openspec/specs/wallets/spec.md` has two requirements over 500 characters** (strict validation warnings, from before this commit). Splitting them belongs to the next change that touches Wallets.
