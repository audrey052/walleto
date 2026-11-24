# The Main Goal Card Opens the Goal

**Created:** 2026-11-24
**Last edited:** 2026-11-24
**Status:** Implemented
**Commit:** `9c72adc` fix: open a goal from its card
**Branch:** `main`, parent `9ed75f9`
**OpenSpec change:** `add-savings-goals` (MVP 4), revision
**Trigger:** The developer asked to remove "Edit goal" and "View history" from the main goal card: clicking the card opens the history, and editing happens there.

## Why this is recorded here

The main card now behaves like the other goal rows, and editing has one entry point.

## What is built

| Area | Change |
|---|---|
| Main goal card | the whole card links to the goal's detail page, with the same light hover as the other rows; the name is plain text |
| Card actions | only "Add to this goal" (or "Mark as complete") and the drag handle, both above the card link |
| Edit | only from the detail page's Edit button |

## Requirements this establishes

1. **A goal is edited from its detail page.** The Savings goals page does not link to `finance:goal_edit`.

## Files changed

| File | Change |
|---|---|
| `templates/finance/goals.html` | card link, two links removed, actions above the link |
| `finance/tests/test_goals.py` | card opens the goal; no Edit goal or View history |
| `openspec/changes/add-savings-goals/` spec, proposal, tasks, changes | the card's actions |
| `openspec/commits/README.md`, `transfer-from-wallets-only.md` | `9ed75f9` filled in, this record |

## Verification

**Executed:**

- Edge headless, demo account, 1440px: "Add to this goal" and the drag handle are on top (not covered by the card link); clicking the goal name opens `/savings-goals/9/`, which has Edit; the page has no "Edit goal" or "View history".
- `python manage.py test`: 354 tests OK.

**Not executed:**

- Dragging the main card was not re-tested; the handle is reachable and its code is unchanged.

## Known gaps

- None.
