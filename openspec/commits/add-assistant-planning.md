# Assistant Planning and Monthly PDF Reports

**Created:** 2026-11-25
**Last edited:** 2026-11-25
**Status:** Implemented
**Commit:** `367b8b5`
**Branch:** `main`, parent `742413c`
**OpenSpec change:** `add-assistant-planning` (MVP 7, part 2), archived to `openspec/changes/archive/2026-11-25-add-assistant-planning/`
**Trigger:** The developer asked to "continue MVP 7 part 2". They chose to base the plan on what is left of the monthly plan, and chose a full one-page report.

## Why this is recorded here

The Assistant can now change the user's data in a second place, Budget, so this record states how that change is confirmed and checked.

## Context

- Part 1 (`add-assistant`, archived) built the tool registry, the agent loop and the transaction draft cards.
- Budget limits are per category per month, and the monthly plan is their sum (`finance/budgets.month_budget`).

## What is built

| Area | Change |
|---|---|
| Plan facts | `plan_rest_of_month`: code computes what is left of this month's plan, the days left, and each limited category's limit, spent, left and daily average so far. |
| Proposal | `propose_budget_plan(amounts, note)`: the model proposes an amount per category, and code checks it. The check rejects unknown, duplicate or missing categories, non-whole and negative amounts, and limits below Rp1.000. The amounts must add up exactly to what is left. A failed check goes back to the model as an error naming the difference, and only a valid proposal becomes a card. |
| Plan card | A table of Category, Left now, Suggested and Per day. **Edit** unlocks the amounts, and the per-day values and the total follow as the user types, with an over or under warning. **Apply to Budget** stays disabled until the amounts add up. Applying sets each limit to spent + amount in one transaction, so the plan total does not change. The card can be applied once, and it shows "expired" after its month has ended. |
| Report | `generate_report(month)` gathers income, expenses, plan, remaining, a category table, the 10 largest expenses and goal progress. The model writes one summary paragraph, then code checks every Rp amount and percent in it against these figures. If a figure doesn't match, or the model fails, the code's own summary is used. Months that have not started are refused. |
| Report card | Shows the month, income and expenses, the summary and **Download PDF**. The PDF (A4, xhtml2pdf) is rendered from the stored figures when downloaded. |
| Chat | A fourth suggestion, "Help me plan the rest of the month". The "thinking" bubble no longer stays after the answer, because it is now removed on `htmx:beforeSwap` of `#conversation`. |
| Prompt | Per-day questions stay with `check_budget`. Replies follow the language of the latest question, in plain text without Markdown. |

## Requirements this establishes

1. **Rest-of-month plan from computed facts** (assistant spec).
2. **Plan card and Apply to Budget.**
3. **Monthly report.**
4. **Planning and report privacy.**

## Files changed

| File | Change |
|---|---|
| `assistant/planning.py`, `assistant/report.py`, `templates/assistant/report.html` (new) | Facts, checks, apply, report figures, summary check, PDF |
| `assistant/tools.py`, `assistant/agent.py` | The three tools and the prompt rules |
| `assistant/views.py`, `assistant/urls.py` | `apply_plan` and `report_pdf` |
| `templates/assistant/_card_plan.html`, `_card_report.html` (new), `_turn.html`, `_input.html`, `assistant.html` | The two cards; `hx-on::before-swap` removed |
| `static/js/app.js`, `static/src/app.css` | `planCard`, the `.plan-amount` style and the pending-turn fix |
| `assistant/tests/test_planning.py`, `test_planning_tools.py`, `test_planning_views.py` (new) | 34 tests |
| `evals/assistant.jsonl`, `docs/eval_results.md` | 4 cases, Runs 3 and 4 |
| `requirements.txt` | Adds `xhtml2pdf` and its dependencies. It also fixes `4c057fa`, which committed the global Python's 212 packages; the file now holds the venv's 32. |
| `openspec/changes/archive/2026-11-25-add-assistant-planning/` | Proposal, spec delta, design, tasks and `changes.md`, archived |
| `openspec/specs/assistant/spec.md` | 9 requirements added by the sync (20 in total) |
| `openspec/commits/README.md`, `transactions-grouped-by-day.md` | `742413c` filled in; this record added |

## Verification

**Executed:**

- `python manage.py test`: 486 tests OK.
- `openspec validate add-assistant-planning --strict`: valid. After the sync, `openspec validate assistant --type spec --strict` is also valid.
- `python manage.py eval_assistant` with `gpt-6-luna`:
  - Run 3: 26 of 28 passed. The new `per-day` miss went to `plan_rest_of_month`.
  - After the prompt fix, Run 4: 27 of 28 passed. The only miss is `spend-month`, as in Run 2.
- Edge headless, using a temporary QA user (deleted afterwards) so the demo account's budgets stayed untouched, with the real model:
  - "Help me plan the rest of the month" gives a plan card: "Adds up to Rp1.790.000 of Rp1.790.000 left."
  - Edit +Rp50.000 shows "Rp1.840.000: Rp50.000 over the Rp1.790.000 left." and disables Apply; the per-day value follows.
  - Restoring the amount and pressing Apply turns the card into "Applied to Budget". Budget keeps its Rp5.000.000 plan.
  - "Make a report for October" gives a report card. The download is `application/pdf`, named `walleto-report-2026-10.pdf`, and the PDF's contents were read and checked.
  - After the fix, no question bubble or "thinking" dots are left behind.
  - No horizontal scroll at 1440px or 390px.

**Not executed:**

- In the browser, the model proposed each category's current remaining amount, so Apply left the limits unchanged. The view tests cover limits that do change.

## Known gaps

- **Per-day values use the floor of amount ÷ days left.** Their sum can be a few Rupiah below the amount; the amount itself is what is applied.
- **xhtml2pdf ignores `border-collapse`.** The tables still render cleanly.
