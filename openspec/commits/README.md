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
| 10 | `605f480` | [add-wallets-page.md](add-wallets-page.md) | 1 |
| 11 | `bdb1803` | [add-wallets-wrap-up.md](add-wallets-wrap-up.md) | 1 |
| 12 | `8e2ebf5` | [archive-add-wallets.md](archive-add-wallets.md) | 1 |
| 13 | `e9d43b7` | [add-transactions-proposal.md](add-transactions-proposal.md) | 2 |
| 14 | `a6fbdf7` | [add-transaction-and-transfer-models.md](add-transaction-and-transfer-models.md) | 2 |
| 15 | `f8ff966` | [add-transactions-page.md](add-transactions-page.md) | 2 |
| 16 | `9e1ba0b` | [add-demo-account.md](add-demo-account.md) | 2 |
| 17 | `05a739d` | [add-transactions-wrap-up.md](add-transactions-wrap-up.md) | 2 |
| 18 | `90c528b` | [transactions-figma-table-and-csv.md](transactions-figma-table-and-csv.md) | 2 |
| 19 | `00e39c5` | [transactions-summary-income-expenses.md](transactions-summary-income-expenses.md) | 2 |
| 20 | `511cfd4` | [restore-transactions-template.md](restore-transactions-template.md) | 2 |
| 21 | `fc953ab` | [archive-add-transactions.md](archive-add-transactions.md) | 2 |
| 22 | `bb06f5c` | [add-budgets.md](add-budgets.md) | 3 |
| 23 | `e3e407f` | [redesign-wallets-page.md](redesign-wallets-page.md) | 1 (redesign) |
| 24 | `56e9972` | [archive-add-budgets.md](archive-add-budgets.md) | 3 |
| 25 | `99af433` | [fix-budget-modal-root.md](fix-budget-modal-root.md) | 3 (fix) |
| 26 | `b8ac963` | [add-savings-goals.md](add-savings-goals.md) | 4 |
| 27 | `680acc6` | [goals-single-create-button.md](goals-single-create-button.md) | 4 (fix) |
| 28 | `c699a64` | [placeholders-without-eg.md](placeholders-without-eg.md) | all (copy) |
| 29 | `5cec7fa` | [money-input-separators.md](money-input-separators.md) | all (input) |
| 30 | `2b48268` | [styleguide-money-inputs.md](styleguide-money-inputs.md) | 0 (style guide) |
| 31 | `89bd29e` | [versioned-static-assets.md](versioned-static-assets.md) | 0 (assets) |
| 32 | `7b04a3a` | [simplify-wallets-and-transactions.md](simplify-wallets-and-transactions.md) | 1, 2 (UI) |
| 33 | `352fe67` | [goal-drag-and-drop.md](goal-drag-and-drop.md) | 4 |
| 34 | `f3a84a3` | [add-dashboard.md](add-dashboard.md) | 5 |
| 35 | `d4284f7` | [smiling-wallet-logo.md](smiling-wallet-logo.md) | 0 (brand, top bar, sidebar, Home) |
| 36 | this commit | [transfer-from-wallets-only.md](transfer-from-wallets-only.md) | 2 (UI) |

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
