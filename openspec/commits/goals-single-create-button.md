# Show the New Goal Button Only Once a Goal Exists

**Created:** 2026-11-23
**Last edited:** 2026-11-23
**Status:** Implemented
**Commit:** this commit
**Branch:** `main`, parent `b8ac963`
**OpenSpec change:** `add-savings-goals` (MVP 4), follow-up to the Savings goals page
**Trigger:** The developer found two create buttons on an empty Savings goals page: "New goal" in the heading and "Create a goal" in the empty state.

## Why this is recorded here

A visible change to the Savings goals page, made after the MVP 4 commit.

## Context

- With no active goal, the empty state already offers "Create a goal".
- Once a goal exists, the empty state is gone, so the heading button is the only way to add another goal.

## What is built

| Area | Change |
|---|---|
| `templates/finance/goals.html` | the heading's "New goal" renders only when there is a main (active) goal |

## Requirements this establishes

1. **An empty Savings goals page has one create button,** the empty state's "Create a goal".

## Files changed

| File | Change |
|---|---|
| `templates/finance/goals.html` | condition on the heading button |
| `finance/tests/test_goals.py` | no "New goal" without goals or with only completed goals; shown once a goal exists |
| `openspec/changes/add-savings-goals/changes.md`, `openspec/commits/README.md`, `add-savings-goals.md` | `b8ac963` filled in, this record |

## Verification

**Executed:**

- `python manage.py test finance.tests.test_goals`: 74 tests OK.

**Not executed:**

- None.

## Known gaps

- None.
