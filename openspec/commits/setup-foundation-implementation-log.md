# Implementation Log for the setup-foundation Change

**Created:** 2026-11-16
**Last edited:** 2026-11-16
**Status:** Implemented. Superseded in format by the per-commit records in `openspec/commits/`
**Commit:** `437f30d` feat: add implementation log for the setup-foundation change
**Branch:** `main`, parent `5b725ca`
**OpenSpec change:** `setup-foundation` (MVP 0)
**Trigger:** a request for one document listing everything MVP 0 created and changed.

## Why this is recorded here

It added a rule to `openspec/config.yaml` that applies to every later change.

## What is built

- **`openspec/changes/setup-foundation/changes.md`:** one summary of MVP 0: status, commits, route table, every file in `config/`, `accounts/`, `core/`, `static/` and `templates/` with its job, the CSS class list, differences from the plan, verification, and open items before archiving.
- **`openspec/config.yaml`:**
  - added: after a change is implemented, write a `changes.md` next to its proposal
  - removed: "the developer writes the code by hand", since implementation is now delegated

## Files changed

| File | Change |
|---|---|
| `openspec/changes/setup-foundation/changes.md` | new |
| `openspec/config.yaml` | one rule added, one removed |

## Verification

**Executed:**

- `openspec validate setup-foundation --strict`: valid.

## Known gaps

- The per-change summary was followed by a per-commit format (this folder). The `config.yaml` rule is updated in the commit that adds these records.
