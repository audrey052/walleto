# Update setup-foundation Spec and Add Local Run Instructions

**Created:** 2026-11-16
**Last edited:** 2026-11-16
**Status:** Implemented
**Commit:** `5b725ca` feat: update setup-foundation spec and add local run instructions
**Branch:** `main`, parent `2f886ac`
**OpenSpec change:** `setup-foundation` (MVP 0), tasks 10.2–10.4
**Trigger:** the implementation in `2f886ac` departed from parts of the plan; the change documents must describe what was actually built.

## Why this is recorded here

Documentation only, but it changes the record of decisions in `design.md` and the completion state in `tasks.md`, which reviewers and later MVPs rely on.

## What is built

### `openspec/changes/setup-foundation/design.md`

| Decision | Update |
|---|---|
| 4. Built-in auth views | Added `LoginRequiredMiddleware`, with `@login_required` on every view as the rejected alternative |
| 7. Components | Rewritten: CSS classes for simple components, includes for structured ones, `{% icon %}` tag, money helpers; why `eyebrow` instead of `overline` |
| 8. Alpine.js | Components live in `static/js/app.js`; modals use native `<dialog>`; sidebar widths are CSS-driven |
| Risks | Sidebar flash described precisely, with the inline-script fix |

### `openspec/changes/setup-foundation/tasks.md`

- All tasks ticked except 2.4 (superuser, needs the developer's password) and 10.1 (real-browser check).
- Task wording aligned with what was built (pinned versions, class names, middleware), and task 9.7 added for the app shell tests.

### `README.md`

New section "Menjalankan secara lokal": create the venv, `pip install -r requirements.txt`, copy `.env.example` to `.env`, `migrate`, `createsuperuser`, `npm install` + `npm run css:watch`, `runserver`; plus how to run the tests.

## Files changed

| File | Change |
|---|---|
| `openspec/changes/setup-foundation/design.md` | decisions 4, 7, 8 and risks updated |
| `openspec/changes/setup-foundation/tasks.md` | ticked and reworded |
| `README.md` | local run and test instructions |

`docs/decisions.md` also gained six rows, but `docs/` is git-ignored, so it is not part of this commit.

## Verification

**Executed:**

- `openspec validate setup-foundation --strict`: valid.
- `python manage.py test`: 34 pass.

## Known gaps

- The README is still in Indonesian and internal; the public version is planned for MVP 8.
