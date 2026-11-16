# Per-Commit Records

**Created:** 2026-11-16
**Last edited:** 2026-11-16
**Status:** Implemented
**Commit:** `3f2dae8` feat: add per-commit openspec records for mvp 0
**Branch:** `main`, parent `437f30d`
**OpenSpec change:** `setup-foundation` (MVP 0)
**Trigger:** request for one detailed OpenSpec-style Markdown record per commit, in the format of an existing team record (header, Why, Context, What is built, Requirements, Files changed, Verification, Known gaps).

## Why this is recorded here

It sets a documentation rule for every later commit and adds a new folder, `openspec/commits/`.

## Context

- **Records live in `openspec/commits/`,** not in `openspec/changes/`. The OpenSpec CLI treats every entry in `changes/` as a change with proposal, specs and tasks, so loose files there would be misread.
- **A change's `changes.md` stays.** It summarizes a whole MVP; commit records describe one commit each. The `config.yaml` rule now asks for both.
- **A record can't contain its own hash,** because the hash depends on the content. Records give the parent commit instead, and the index in `README.md` is updated with the hash in the following commit.

## What is built

| File | Job |
|---|---|
| `openspec/commits/README.md` | Purpose, index of all records, rules, and the template |
| `openspec/commits/django-project-env-settings.md` | Record for `48cc247` |
| `openspec/commits/tailwind-build-and-assets.md` | Record for `4097ca1` |
| `openspec/commits/email-auth-and-app-shell.md` | Record for `2f886ac` |
| `openspec/commits/setup-foundation-spec-and-readme.md` | Record for `5b725ca` |
| `openspec/commits/setup-foundation-implementation-log.md` | Record for `437f30d` |
| `openspec/commits/per-commit-records.md` | This record |

`openspec/config.yaml` gains the rule: every commit adds a record in `openspec/commits/` following the template in its README, in the same commit.

## Requirements this establishes

1. **Every commit adds its own record** in `openspec/commits/`, in the same commit.
2. **Records follow the template** in `openspec/commits/README.md`, with every section present.
3. **The index is kept current;** the previous commit's hash is filled in by the next commit.

## Files changed

| File | Change |
|---|---|
| `openspec/commits/` (7 files) | new |
| `openspec/config.yaml` | per-commit record rule added |

## Verification

**Executed:**

- `openspec validate setup-foundation --strict`: valid; the new folder does not affect the CLI.
- Each record's file list was checked against `git show --stat` for its commit.

**Not executed:**

- None.

## Known gaps

- None.
