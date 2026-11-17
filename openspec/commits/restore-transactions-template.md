# Restore the Transactions Template Broken by HTML Formatting

**Created:** 2026-11-17
**Last edited:** 2026-11-17
**Status:** Implemented
**Commit:** `511cfd4` fix: restore the transactions template broken by html formatting
**Branch:** `main`, parent `00e39c5`
**OpenSpec change:** `add-transactions` (MVP 2), task 3.8
**Trigger:** commit `00e39c5` was made while the test suite was failing (18 errors), because the commit step did not wait for the test result.

## Why this is recorded here

`00e39c5` contains a template that Django can't parse, so `/transactions/` raised `TemplateSyntaxError`. This commit fixes it and adds a guard so it doesn't happen again.

## Context

- **Cause:** the editor reformatted `templates/finance/transactions.html` with Prettier on save. Prettier's HTML formatter wraps long lines, which split Django tags across lines (`{% block title` / `%}`, `{{` / `month_start|date:"F Y" }}`). Django requires every `{% %}` and `{{ }}` tag to be on one line.
- **Fix:** the template was restored from `90c528b` with `git checkout`, and the summary change from `00e39c5` (Income and Expenses only, no Net) was applied again.
- **Guard:** `.prettierignore` excludes `templates/`, built CSS, vendored scripts and `node_modules/`.
- **Process fix:** commits are only made after the test run has passed, not chained after it.

## What is built

| File | Change |
|---|---|
| `templates/finance/transactions.html` | the `90c528b` version, plus the summary showing only "Income" and "Expenses" |
| `.prettierignore` | new |

## Requirements this establishes

1. **Django templates are not auto-formatted by Prettier.**
2. **No commit is made while tests fail.**

## Files changed

| File | Change |
|---|---|
| `templates/finance/transactions.html` | restored and re-edited |
| `.prettierignore` | new |
| `openspec/changes/add-transactions/changes.md` | commit table |
| `openspec/commits/README.md` | index: `00e39c5` filled in, this record added |
| `openspec/commits/transactions-summary-income-expenses.md` | its own hash filled in; status notes the broken template |

## Verification

**Executed:**

- `python manage.py test`: 155 pass.
- Scan of every template for `{% %}` or `{{ }}` tags split across lines: none (one false positive in comment lines of `components/modal.html`, which is unchanged).

**Not executed:**

- None.

## Known gaps

- **`00e39c5` stays in the history** as a broken commit. It was not rewritten, since history is only rewritten on request.
