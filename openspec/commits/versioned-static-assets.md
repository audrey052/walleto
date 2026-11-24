# Version the App CSS and JavaScript URLs

**Created:** 2026-11-23
**Last edited:** 2026-11-23
**Status:** Implemented
**Commit:** `89bd29e` fix: version the app css and js urls so browsers load the latest files
**Branch:** `main`, parent `2b48268`
**OpenSpec change:** none (asset delivery)
**Trigger:** After `5cec7fa`, the developer saw no dot separators in money fields.

## Why this is recorded here

A change to how every page loads its stylesheet and script, and the cause of a "not working" report.

## Context

- The running server (port 8000) already served the new `app.js` and rendered `data-money` on every money input. The developer's browser kept the cached `/static/js/app.js` from before the change, because the URL never changes.
- Earlier CSS changes needed Ctrl+Shift+R for the same reason.

## What is built

| Area | Change |
|---|---|
| `core/templatetags/assets.py` | `{% asset "path" %}` returns the static URL with `?v=<file modification time>` |
| `templates/base.html` | `css/app.css` and `js/app.js` load through `{% asset %}`; vendor files keep plain URLs (their names don't change between versions we pin) |

## Requirements this establishes

1. **Edited CSS and JavaScript reach the browser on a normal reload.**

## Files changed

| File | Change |
|---|---|
| `core/templatetags/assets.py`, `templates/base.html` | versioned URLs |
| `core/test_forms.py` | tag test |
| `openspec/commits/README.md`, `styleguide-money-inputs.md` | `2b48268` filled in, this record |

## Verification

**Executed:**

- The developer's running server (port 8000), signed in as demo:
  - the four sampled modals each had `data-money`;
  - after the change, `/wallets/` loads `app.css?v=…` and `app.js?v=…`.
- `python manage.py test`: all tests OK.

**Not executed:**

- None.

## Known gaps

- **Production should use `ManifestStaticFilesStorage`** (hashed file names) when deploying in MVP 8; `?v=` covers development.
