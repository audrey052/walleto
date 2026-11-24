# No "On track" Label, Smaller Main Goal Card

**Created:** 2026-11-25
**Last edited:** 2026-11-25
**Status:** Implemented
**Commit:** `bd904d9` fix: no on track label, smaller main goal card
**Branch:** `main`, parent `fc086f2`
**OpenSpec change:** `add-savings-goals` (MVP 4), revision
**Trigger:** The developer asked to remove the "On track" label from Savings goals, then to make the main goal card a little smaller.

## Why this is recorded here

A goal's status chip now appears only when something needs attention, and the main card moves away from the Figma size.

## What is built

| Area | Change |
|---|---|
| Goal status chip | shown for "Behind" (amber) and "Past deadline" (clay) only; an on-track goal shows none, on the goals page and the detail page |
| Status logic | unchanged: `finance/goals.py` still computes `on_track` |
| Main goal card | 32px padding (was 40), 40px column gap (was 50), name 22px (was 25), saved amount 36px (was 40), percent 46px (was 57), ledger lines 80px high and 11px wide (were 100 and 13), tighter spacing; 327px tall at 1440px (was about 380) |

## Requirements this establishes

1. **An on-track goal carries no status label.**

## Files changed

| File | Change |
|---|---|
| `templates/finance/_goal_status.html` | skips `on_track` |
| `templates/finance/goals.html` | smaller main card |
| `finance/tests/test_goals.py` | the main card's goal is on track and the page has no "On track" |
| `openspec/changes/add-savings-goals/specs/savings-goals/spec.md`, `changes.md` | "Goal status" shows only Behind and Past deadline |
| `openspec/changes/add-date-range/changes.md`, `openspec/commits/README.md`, `add-date-range.md` | `fc086f2` filled in, this record |

## Verification

**Executed:**

- `python manage.py test`: 397 tests OK.
- `openspec validate add-savings-goals --strict`: valid.
- Edge headless, demo account, 1440px: the main card is 327px tall, the amount is 36px, "Add to this goal" and the drag handle are still on top of the card link, and the card still opens the goal.

**Not executed:**

- The "On track" chip was not checked in a browser (the demo's main goal is behind).

## Known gaps

- None.
