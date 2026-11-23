# Drop "e.g." from Input Placeholders

**Created:** 2026-11-23
**Last edited:** 2026-11-23
**Status:** Implemented
**Commit:** `c699a64` fix: show examples in placeholders without e.g.
**Branch:** `main`, parent `680acc6`
**OpenSpec change:** none (copy change across existing forms)
**Trigger:** The developer asked for placeholders to show the example directly, without "e.g.".

## Why this is recorded here

A copy change on every form in the app, and a new copy rule in docs/STYLE.md.

## Context

- Placeholders already use the light placeholder color (`#A5A699`), so a bare example reads as a hint, not a value.

## What is built

| Area | Change |
|---|---|
| Sign-up name, wallet, transaction, transfer, budget plan and limit, goal, and goal movement forms | `"e.g. 2.500.000"` becomes `"2.500.000"`, `"e.g. BCA, GoPay, Cash"` becomes `"BCA, GoPay, Cash"`, and so on (12 placeholders) |
| Style guide sample input | same |

## Requirements this establishes

1. **Placeholders show the example directly, without "e.g."** (docs/STYLE.md section 6, local only).

## Files changed

| File | Change |
|---|---|
| `accounts/forms.py`, `finance/forms.py` | placeholders |
| `templates/core/styleguide.html` | sample placeholder |
| `openspec/commits/README.md`, `goals-single-create-button.md`, `openspec/changes/add-savings-goals/changes.md` | `680acc6` filled in, this record |

## Verification

**Executed:**

- `grep "e.g."` over the forms and templates finds nothing.
- `python manage.py test`: 310 tests OK.

**Not executed:**

- None.

## Known gaps

- **The docs/STYLE.md rule is local only** (`.gitignore`).
