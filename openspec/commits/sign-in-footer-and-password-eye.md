# Sign-in Page: Footer and Show Password

**Created:** 2026-11-25
**Last edited:** 2026-11-25
**Status:** Implemented
**Commit:** `eedb4f7`
**Branch:** `main`, parent `367b8b5`
**OpenSpec change:** none (layout only)
**Trigger:** Before MVP 8 the developer asked to fix the sign-in pages. A first version redesigned the preview panel; the developer asked to keep the panel as it was, remove the tagline, and add an eye button to see the password.

## What is built

| Area | Change |
|---|---|
| Footer | "Personal finance for everyday life." removed. Only the centred copyright stays under the form column. |
| Show password | Every password field (`components/field.html`, when the widget is a password) gets an eye button on the right of the input. It switches the input between hidden and visible, with "Show password" or "Hide password" as its label and `aria-pressed`. Without JavaScript the button stays hidden and the field works as before. On Create account, each of the two fields has its own button. |
| Icons | `eye` and `eye-off` |
| Full name example | The Create account placeholder is "Admin" instead of "Aditya Ramadhan", at the developer's request. |
| Preview panel | Unchanged. |

## Files changed

| File | Change |
|---|---|
| `templates/layouts/auth.html` | Tagline removed |
| `templates/components/field.html` | Eye button for password fields |
| `core/templatetags/icons.py` | `eye` and `eye-off` icons |
| `accounts/forms.py` | Full name placeholder "Admin" |
| `static/src/app.css` | `.password-toggle` style and right padding on its input |
| `openspec/commits/README.md`, `add-assistant-planning.md` | `367b8b5` filled in; this record |

## Verification

**Executed:**

- `python manage.py test`: 486 tests OK.
- Edge headless, Sign in and Create account at 1440px and 390px: pressing the eye shows the typed password (`type=text`, label "Hide password"). On Create account the other field stays hidden. No horizontal scroll.

**Not executed:**

- None.
