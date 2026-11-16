# Tailwind Build with Design Tokens, Fonts and Vendored HTMX and Alpine

**Created:** 2026-11-16
**Last edited:** 2026-11-16
**Status:** Implemented
**Commit:** `4097ca1` feat: add tailwind build with design tokens, fonts and vendored htmx and alpine
**Branch:** `main`, parent `48cc247`
**OpenSpec change:** `setup-foundation` (MVP 0), tasks 3.1–3.5, 4.2–4.3 (CSS part), 6.3
**Trigger:** WORKPLAN MVP 0.4 and `docs/STYLE.md`. Every page must use one set of tokens and components taken from the Figma Make design.

## Why this is recorded here

It adds the only non-Python toolchain in the project (Node, for Tailwind) and defines the design system every template uses. Choices here (tokens, class names, vendored versions) are hard to change once many pages depend on them.

## Context

- **Tailwind v4 through its npm CLI**, not the CDN script (not for production) and not `django-tailwind` (an extra layer). Node only compiles CSS; there is no JavaScript app. See `design.md` decision 5.
- **Versions are pinned and not the newest.** `npm view` reported Tailwind 4.3.5, HTMX 2.0.11 and Alpine 3.17.5; the project pins releases that have been out for a while (Tailwind 4.1.11, HTMX 2.0.4, Alpine 3.14.9) to avoid picking up a just-published package.
- **No runtime CDN.** HTMX, Alpine and the font are files in `static/`, so development works offline and versions can't change underneath the app. See `design.md` decision 6.
- **The Figma CSS was not copied.** It used about 190 colors and 30 font sizes, many of them 7–9 px. The tokens come from `docs/STYLE.md`, which consolidates them and raises the type scale.
- **Sidebar width is CSS-driven** (`.is-collapsed` on the shell) so the layout is correct before Alpine starts.

## What is built

### Build (`package.json`)

| Script | Command |
|---|---|
| `css:watch` | `tailwindcss -i static/src/app.css -o static/css/app.css --watch` |
| `css:build` | same with `--minify` |

`static/css/` (the output) is git-ignored and rebuilt at deploy time.

### Tokens (`static/src/app.css`, `@theme`)

| Group | Tokens |
|---|---|
| Neutrals | `paper` #FAFAF7, `sidebar` #F6F6F1, `surface` #FFFFFF, `hover` #F3F3EC, `border` #E7E5DF, `border-strong` #DDDFD4, `track` #EAECE3, `ink` #1C1B18, `secondary` #6B6A64, `muted` #92918A, `placeholder` #A5A699 |
| Accent | `forest` #1F5C4A, `forest-hover` #164C3C, `forest-soft` #E7ECE3, `forest-tint` #F1F3EB, `selection` #DBE9DD |
| Status | `amber` #B7791F, `clay` #B4463A |
| Charts | `chart-1` … `chart-5` (#1F5C4A, #688373, #99AA99, #B8AD92, #D2CDBF) |
| Radius | `chip` 4px, `control` 6px, `panel` 8px |
| Shadows | `popover`, `toast`, `modal` (floating elements only) |
| Type | `display` 40, `title` 28, `modal` 18, `section` 15, `body` 14, `control` 13, `caption` 12, `eyebrow` 11 |

### Component classes (`@layer components`)

Buttons (`btn`, `btn-primary`, `btn-danger`, `btn-text`, `btn-icon`), fields (`field`, `field-label`, `input`, `field-help`, `field-error`, `field-invalid`), `panel` / `panel-header` / `panel-body`, `eyebrow`, amounts (`amount`, `amount-income`, `amount-display`, smaller `.currency`), `chip` (colored by `--chip`), `progress` (+ `-warning`, `-over`), `icon-tile`, `status-dot`, `empty-state`, `modal` (native `<dialog>` + backdrop), `popover`, `toast`, shell (`sidebar`, `workspace`, `is-collapsed`, `sidebar-label`, `nav-item`, `avatar`).

### Scripts and assets

| File | What |
|---|---|
| `static/js/app.js` | Alpine components registered on `alpine:init`: `shell` (sidebar collapse saved in `localStorage` under `walleto.sidebarCollapsed`; falls back to expanded when storage is blocked) and `toast` (hides after 4 s) |
| `static/vendor/htmx.min.js` | HTMX 2.0.4 |
| `static/vendor/alpine.min.js` | Alpine.js 3.14.9 |
| `static/fonts/plus-jakarta-sans-latin.woff2`, `OFL.txt` | Plus Jakarta Sans (variable 400–800) and its SIL OFL license, from the Figma Make project |

## Requirements this establishes

1. **Only STYLE.md tokens are used for color, radius, shadow and type.** New values are added to STYLE.md first.
2. **Light mode only.** `color-scheme: light`; no dark variants.
3. **Panels never have a shadow;** only popovers, toasts and modals do.
4. **Amounts use tabular digits** with a smaller, lighter "Rp".
5. **Built CSS is never committed;** it is produced by `npm run css:build`.

## Files changed

| File | Change |
|---|---|
| `package.json`, `package-lock.json` | new |
| `static/src/app.css` | new: Tailwind entry, `@font-face`, tokens, base styles, component classes |
| `static/js/app.js` | new |
| `static/vendor/htmx.min.js`, `static/vendor/alpine.min.js` | new, downloaded from unpkg at the pinned versions |
| `static/fonts/plus-jakarta-sans-latin.woff2`, `static/fonts/OFL.txt` | new |
| `.gitignore` | `static/css/` added |

## Verification

**Executed:**

- `npm install`: 33 packages added.
- `npm run css:build`: builds `static/css/app.css` (≈30 KB) in about 150 ms.
- The font file starts with the `wOF2` signature (valid WOFF2).
- Headless Edge screenshots after the next commit's templates: tokens, chips, progress states, buttons, toast and icons render as specified on `/styleguide/`.

**Not executed:**

- `css:watch` rebuilding on template edits in a long-running session (expected Tailwind behavior, not exercised).

## Known gaps

- **Sidebar flashes expanded** for users who collapsed it, until Alpine starts. Fixable later with a small inline script that sets `.is-collapsed` before first paint.
- **Two terminals in development** (`css:watch` and `runserver`); documented in the README.
- The label class was first named `overline`, which collided with Tailwind's `overline` text-decoration utility. It was renamed to `eyebrow` before this commit.
