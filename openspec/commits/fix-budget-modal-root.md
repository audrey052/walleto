# Fix the Budget Modals That Never Opened

**Created:** 2026-11-18
**Last edited:** 2026-11-18
**Status:** Implemented
**Commit:** this commit
**Branch:** `main`, parent `56e9972`
**OpenSpec change:** none (fix to the archived `add-budgets`, budgets spec "Budget modals")
**Trigger:** The developer reported that "Set monthly plan" did nothing in the browser.

## Why this is recorded here

Every Budget modal was broken in a real browser: Set and Edit monthly plan, editing a category row, and Set limit.

## Context

- The Budget links load their modal with `hx-target="#modal-root"`, but `budget.html` had no `#modal-root` element. Wallets and Transactions each place it at the end of their template. HTMX logged `htmx:targetError` and loaded nothing.
- Tests requested the modal URLs directly, and the headless screenshots injected the modal into the page, so neither caught it.

## What is built

| Area | Change |
|---|---|
| `templates/finance/budget.html` | `<div id="modal-root"></div>` at the end of the content block |
| `finance/tests/test_budget_views.py` | the page renders `#modal-root` with and without a plan |

## Requirements this establishes

1. **A page with `hx-target="#modal-root"` links renders `#modal-root` itself.**

## Files changed

| File | Change |
|---|---|
| `templates/finance/budget.html` | modal root added |
| `finance/tests/test_budget_views.py` | regression test |
| `openspec/commits/README.md`, `archive-add-budgets.md` | `56e9972` filled in, this record |

## Verification

**Executed:**

- `python manage.py test`: 236 tests OK (1 new).
- Edge driven over the DevTools protocol with the demo account: before the fix, clicking "Set monthly plan" logged `htmx:targetError` and opened nothing. After it, the modal opened, Rp8.000.000 was saved (204 with HX-Redirect), the page showed the split limits and the success toast. The test plan was then deleted from the demo data.

**Not executed:**

- None.

## Known gaps

- None.
