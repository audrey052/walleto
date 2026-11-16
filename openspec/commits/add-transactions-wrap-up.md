# Complete the add-transactions Change Log

**Created:** 2026-11-17
**Last edited:** 2026-11-17
**Status:** Implemented, with the real-browser check (task 6.1) outstanding
**Commit:** `05a739d` feat: complete the add-transactions change log
**Branch:** `main`, parent `9e1ba0b`
**OpenSpec change:** `add-transactions` (MVP 2), tasks 6.2–6.4
**Trigger:** `openspec/config.yaml` asks for a `changes.md` after a change is implemented.

## Why this is recorded here

It closes MVP 2's implementation on the OpenSpec side and documents how to load demo data.

## What is built

- **`openspec/changes/add-transactions/changes.md`:** status, commits, routes, data, every file, test counts, differences from the plan, verification, open items.
- **`openspec/changes/add-transactions/tasks.md`:** all tasks ticked except 6.1.
- **`README.md`:** how to load or reset demo data (`seed_demo` or the Try demo account button).
- **`docs/decisions.md`** and **`WORKPLAN.md`** (local, git-ignored): seven decisions; MVP 2 ticked.

## Requirements this establishes

None.

## Files changed

| File | Change |
|---|---|
| `openspec/changes/add-transactions/changes.md` | new |
| `openspec/changes/add-transactions/tasks.md` | ticked |
| `README.md` | demo data instructions |
| `openspec/commits/README.md` | index: `9e1ba0b` filled in, this record added |
| `openspec/commits/add-demo-account.md` | its own hash filled in |

## Verification

**Executed:**

- `openspec validate add-transactions --strict`: valid.
- `python manage.py test`: 150 pass.

**Not executed:**

- None.

## Known gaps

- **Task 6.1** (real-browser pass) remains before `openspec archive add-transactions`.
