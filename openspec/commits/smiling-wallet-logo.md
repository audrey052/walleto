# Smiling Wallet Logo, No Breadcrumb, Sidebar Handle, Home

**Created:** 2026-11-24
**Last edited:** 2026-11-24
**Status:** Implemented
**Commit:** `d4284f7` feat: new logo, sidebar handle, Home
**Branch:** `main`, parent `f3a84a3`
**OpenSpec change:** none (brand)
**Trigger:** The developer found the plain wallet icon in the logo ugly and asked for a cute one; of three drafts they chose "A: smiling wallet". They then asked to remove the "My workspace › <Page>" breadcrumb from the top bar, and for a more playful way to open and close the sidebar; they chose a handle on the sidebar's edge. Last, they asked to call the Dashboard "Home", as the phone bar already did.

## Why this is recorded here

The logo is on every page, and the site now has a favicon.

## Context

- The logo was the `wallet` line icon in white on a 32px forest square, in two places: the sidebar and the sign-in layout.
- Three drafts were compared in a local render: a smiling wallet with a coin (A), a smiling coin with a sprout (B), a smiling wallet with a yellow clasp (C).

## What is built

| Area | Change |
|---|---|
| Logo | a white wallet with eyes, a smile and pink cheeks, a gold coin peeking out behind it, on the same 32px forest square with 9px corners |
| `templates/components/logo_mark.html` | the logo as inline SVG, used by `layouts/app.html` and `layouts/auth.html` |
| `static/img/logo.svg` | the same drawing as the favicon, linked from `base.html` |
| Top bar | no breadcrumb and no collapse button: only the date on the right; the phone top bar uses the new mark too |
| Home | the sidebar, the page heading and the browser tab say "Home" instead of "Dashboard", the same word as the phone bar |
| Sidebar handle | a 24px round button in the middle of the sidebar's right edge; hidden until the pointer is over the sidebar (always shown on touch screens and on keyboard focus); its chevron turns when the sidebar is closed; same `toggle()` and saved state as before |

## Requirements this establishes

1. **The logo has one source per form:** `logo_mark.html` for pages, `logo.svg` for the favicon. They must show the same drawing.

## Files changed

| File | Change |
|---|---|
| `templates/components/logo_mark.html`, `static/img/logo.svg` | new |
| `templates/layouts/app.html`, `templates/layouts/auth.html` | include the new mark |
| `templates/base.html` | favicon link |
| `templates/layouts/app.html` | breadcrumb, divider and top-bar collapse button removed; sidebar handle added; phone logo uses `logo_mark.html` |
| `static/src/app.css` | `.sidebar-handle` |
| `core/sections.py`, `templates/finance/dashboard.html` | the first section's title is "Home" (sidebar, heading, browser tab), matching its short label; the route stays `core:dashboard` at `/` |
| `core/tests.py`, `finance/tests/test_dashboard.py` | sidebar titles; Home heading and tab title |
| `templates/finance/goal_detail.html` | unused `breadcrumb` block removed |
| `openspec/commits/README.md`, `add-dashboard.md` | `f3a84a3` filled in, this record |

## Verification

**Executed:**

- Edge headless on the developer's server (port 8000), demo account: the sidebar shows the new mark next to "walleto."; the favicon link resolves to `/static/img/logo.svg`; the top bar at 1440px shows only the collapse button and the date, and at 520px the new mark and the avatar. The handle is hidden away from the sidebar, shows on hover, closes the sidebar (224 → 76px, label "Expand sidebar", chevron turned) and opens it again.
- `python manage.py test`: 352 tests OK.

**Not executed:**

- The sign-in page was not screenshotted (the browser was already signed in); it uses the same include.

## Known gaps

- **The SVG is drawn twice** (component and favicon file). A change to one needs the same change to the other.
