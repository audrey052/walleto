# No Top Bar on Desktop, No Date, Clean Collapsed Profile

**Created:** 2026-11-25
**Last edited:** 2026-11-25
**Status:** Implemented
**Commit:** `8b5a864` fix: no top bar or date on desktop, clean collapsed profile
**Branch:** `main`, parent `bd904d9`
**OpenSpec change:** none; `openspec/specs/app-shell/spec.md` "Topbar" edited directly
**Trigger:** The developer found the header awkward. Since `d4284f7` removed the breadcrumb and the sidebar button, the desktop top bar held only the date: a 64px empty band between the sidebar logo and the page title. They agreed to remove it. With the date then shown above the page title, they found that odd too, and chose to drop the date. Last, the collapsed sidebar showed a cut-off name and email next to the avatar.

## Why this is recorded here

Every signed-in page changes its frame, and the app-shell spec changes with it.

## What is built

| Area | Change |
|---|---|
| Desktop (768px and up) | no top bar and no date; the page title starts 32px from the top, level with the sidebar logo |
| Phone | top bar with the logo and the account menu; the date is gone |
| Collapsed sidebar | the profile shows only the initials circle, centred; the name and email are hidden like the other labels (their `flex` class had beaten the collapsed rule) |

## Requirements this establishes

1. **No top bar on desktop, and no date in the shell.** "Today" is still Jakarta time for every calculation.

## Files changed

| File | Change |
|---|---|
| `templates/layouts/app.html` | `<header>` is phone-only and has no date; main padding 32px on desktop |
| `templates/layouts/app.html` (profile) | `flex` moved to an inner span so `.is-collapsed .sidebar-label` can hide it |
| `core/tests.py` | Jakarta "today" checked in the context; the date is not printed |
| `openspec/specs/app-shell/spec.md` | "Topbar": no desktop top bar, no date, phone top bar with logo and account menu; Jakarta "today" kept as a scenario |
| `openspec/commits/README.md`, `goal-no-on-track-label.md` | `bd904d9` filled in, this record |

## Verification

**Executed:**

- Edge headless, demo account, on Savings goals, Home and Transactions:
  - at 1440px the header is hidden and the title is the first line (an earlier version with the date above it was checked the same way);
  - at 520px the phone top bar shows;
  - with the sidebar collapsed (76px), the profile button shows only "AR", 51px wide;
  - no horizontal scroll at either width.
- `python manage.py test`: 397 tests OK.
- `openspec validate app-shell --type spec --strict`: valid.

**Not executed:**

- None.

## Known gaps

- None.
