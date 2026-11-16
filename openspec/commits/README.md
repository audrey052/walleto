# Commit Records

One Markdown record per commit, describing what the commit built, why, which files it touched, and how it was verified. OpenSpec changes (`openspec/changes/<name>/`) hold the plan for an MVP; these records hold what each commit actually did.

## Index

| # | Commit | Record | MVP |
|---|---|---|---|
| 1 | `48cc247` | [django-project-env-settings.md](django-project-env-settings.md) | 0 |
| 2 | `4097ca1` | [tailwind-build-and-assets.md](tailwind-build-and-assets.md) | 0 |
| 3 | `2f886ac` | [email-auth-and-app-shell.md](email-auth-and-app-shell.md) | 0 |
| 4 | `5b725ca` | [setup-foundation-spec-and-readme.md](setup-foundation-spec-and-readme.md) | 0 |
| 5 | `437f30d` | [setup-foundation-implementation-log.md](setup-foundation-implementation-log.md) | 0 |
| 6 | `3f2dae8` | [per-commit-records.md](per-commit-records.md) | 0 |
| 7 | `28d1f2f` | [archive-setup-foundation.md](archive-setup-foundation.md) | 0 |
| 8 | `5c5521c` | [add-wallets-proposal.md](add-wallets-proposal.md) | 1 |
| 9 | `44b0090` | [add-wallet-and-category-models.md](add-wallet-and-category-models.md) | 1 |
| 10 | this commit | [add-wallets-page.md](add-wallets-page.md) | 1 |

Commits made before MVP 0's code (`git init`, `.gitignore`, OpenSpec init) have no record.

## Rules

- **One record per commit,** added in the same commit it describes. A record can't know its own hash, so it gives the branch and parent commit; the index is filled in with the hash in the next commit.
- **File name:** a short kebab-case description of the commit (`add-wallet-model.md`), not the hash.
- **Language:** English.
- **Every section is required.** Write "None." rather than deleting a section. Records for documentation-only commits may be short.

## Template

```markdown
# <Title in Title Case>

**Created:** YYYY-MM-DD
**Last edited:** YYYY-MM-DD
**Status:** Implemented | Implemented, with <outstanding work>
**Commit:** `<hash>` <commit message>   (or: this commit)
**Branch:** `<branch>`, parent `<parent hash>`
**OpenSpec change:** `<change-name>` (MVP n), tasks x.y–x.z
**Trigger:** <spec, task or request that caused this commit>

## Why this is recorded here

<What makes this commit significant: new model or migration, new routes,
new dependency, new rule, or a decision that is hard to reverse.>

## Context

<Decisions and constraints. Where the commit departs from the plan, say how and why.>

## What is built

<Subsections with tables: models (fields), routes (method, URL, access, purpose),
modules (job), templates, settings.>

## Requirements this establishes

1. **<Rule in bold.>** <Explanation.>

## Files changed

| File | Change |
|---|---|

## Verification

**Executed:**

- <tests run and their count, migrations, checks, screenshots>

**Fixed during implementation:**

- <bugs found while building, and the fix>

**Not executed:**

- <what was not checked, and why>

## Known gaps

- **<Gap.>** <Why it is acceptable now, and when it is addressed.>
```
