# Reorder Goals by Drag and Drop

**Created:** 2026-11-24
**Last edited:** 2026-11-24
**Status:** Implemented
**Commit:** this commit
**Branch:** `main`, parent `7b04a3a`
**OpenSpec change:** `add-savings-goals` (MVP 4), revision after the first review (design decision 11)
**Trigger:** The developer asked to:
- remove "Make main goal" and the "Other goals" heading;
- order goals by drag and drop instead;
- remove the modal close icon, which duplicates Cancel.

## Why this is recorded here

A model change (`is_main` becomes `position`) with a data migration, a new route, a new vendored library, and a change to every modal.

## Context

- The main goal is now simply the first goal in the user's order.

## What is built

| Area | Change |
|---|---|
| `SavingsGoal.position` | replaces `is_main`. Migration `0006` keeps the existing order (chosen main, then nearest deadline, then oldest). New and reopened goals go last. |
| `POST /savings-goals/order/` | saves the order; ignores ids that aren't the user's active goals; unlisted goals keep their place after the listed ones |
| `templates/finance/goals.html` | the main card and the other goals form one sortable list with grip handles (only with two or more goals); "Other goals" heading and "Make main goal" removed |
| `templates/finance/goal_detail.html` | "Make main goal" removed |
| `static/js/app.js` `goalOrder`, `static/vendor/sortable.min.js` | drag with mouse or touch; arrow keys on the handle; reload when the first goal changes |
| `templates/components/modal_form.html`, `modal.html` | no ✕ icon |

## Requirements this establishes

1. **The first goal in the user's order is the main goal.**
2. **Modals close with Cancel, Escape or a click outside;** there is no close icon.

## Files changed

| File | Change |
|---|---|
| `finance/models.py`, `finance/migrations/0006_goal_position.py`, `finance/admin.py` | `position` |
| `finance/goals.py`, `finance/forms.py`, `finance/views_goals.py`, `finance/urls.py`, `finance/demo.py` | order rule, append on create and reopen, reorder view, demo order |
| `templates/finance/goals.html`, `goal_detail.html`, `templates/components/modal_form.html`, `modal.html` | layout and buttons |
| `core/templatetags/icons.py` | `grip` icon |
| `static/js/app.js`, `static/vendor/sortable.min.js` | ordering |
| `finance/tests/test_goals.py` | order rule, reorder, new and reopened goals last, handles, privacy |
| `openspec/changes/add-savings-goals/` | proposal, spec "Main goal", design decision 11, changes |
| `openspec/commits/README.md`, `simplify-wallets-and-transactions.md` | `7b04a3a` filled in, this record |

## Verification

**Executed:**

- `python manage.py test`: 319 tests OK.
- `migrate finance 0005` and forward again run cleanly. On the dev database the existing order was kept.
- `openspec validate add-savings-goals --strict`: valid.
- Edge with the demo account:
  - Sortable attached;
  - ArrowUp on the second goal made it main after the reload;
  - ArrowDown restored the order;
  - the edit modal has no close icon, and Escape closes it.

**Not executed:**

- Dragging with a real mouse or finger. The headless test drove the same save path through the keyboard handler.

## Known gaps

- **`docs/STYLE.md` and `docs/decisions.md` updates are local only** (`.gitignore`).
