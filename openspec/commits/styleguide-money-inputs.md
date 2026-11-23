# Format the Style Guide's Sample Money Inputs

**Created:** 2026-11-23
**Last edited:** 2026-11-23
**Status:** Implemented
**Commit:** `2b48268` fix: format the style guide's sample money inputs
**Branch:** `main`, parent `5cec7fa`
**OpenSpec change:** none (development-only page)
**Trigger:** An audit after `5cec7fa`, when the developer asked whether every money field gets the dot separators.

## Why this is recorded here

This completes the money-input change. The audit result is recorded so it doesn't have to be repeated.

## Context

- Every app form was rendered and checked: all 12 money inputs carry `data-money`. Those are:
  - wallet create and edit;
  - transaction create and edit;
  - transfer create and edit;
  - budget plan and category limit;
  - goal create and edit;
  - goal deposit and withdrawal.
- The account forms have no money fields.
- The only inputs without the formatter were two hand-written samples on `/styleguide/`, which is a DEBUG-only page.

## What is built

| Area | Change |
|---|---|
| `templates/core/styleguide.html`, `_styleguide_modal_body.html` | sample Amount and Monthly limit inputs get `inputmode="numeric"` and `data-money` |

## Requirements this establishes

None.

## Files changed

| File | Change |
|---|---|
| `templates/core/styleguide.html`, `templates/core/_styleguide_modal_body.html` | attributes |
| `openspec/commits/README.md`, `money-input-separators.md` | `5cec7fa` filled in, this record |

## Verification

**Executed:**

- A script rendered every form modal as the demo user and found `data-money` on each money input.

**Not executed:**

- None.

## Known gaps

- None.
