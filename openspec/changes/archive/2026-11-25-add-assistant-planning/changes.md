# Changes: add-assistant-planning (MVP 7, part 2)

This is the implementation log for this change. It lists what was created or modified, and where the result differs from `proposal.md`, `design.md` and `tasks.md`. Per-commit detail is in `openspec/commits/`.

- **Status:** archived on 2026-11-25. The `assistant` spec is synced to `openspec/specs/assistant/spec.md`, which now has 20 requirements.
- **Date:** 2026-11-25
- **Tests:** 486 passing. 34 are new: 15 in `test_planning.py`, 9 in `test_planning_tools.py` and 10 in `test_planning_views.py`.
- **Validation:** `openspec validate add-assistant-planning --strict` passes.
- **Evaluation:** `gpt-6-luna` passed 26 of 28 in Run 3. After a prompt fix it passed 27 of 28 in Run 4. The one miss is still `spend-month`, the same as in Run 2 (`docs/eval_results.md`).

## Commits

| Commit | Message | Record |
|---|---|---|
| this commit | feat: plan the rest of the month and monthly PDF reports | `add-assistant-planning.md` |

## Routes

| Method | URL | Name | Purpose |
|---|---|---|---|
| POST | `/assistant/plans/<id>/apply/` | `assistant:apply_plan` | Applies a plan card to this month's Budget. Fields are `amount_<category_id>`, edited or as proposed. HTMX gets the card back; a request without JavaScript gets a redirect. |
| GET | `/assistant/reports/<id>.pdf` | `assistant:report_pdf` | Downloads the report card's PDF as `walleto-report-YYYY-MM.pdf`, rendered at download time. |

Both routes return 404 for another user's message and for a message whose card is of a different type.

## Files

| File | Change |
|---|---|
| `assistant/planning.py` (new) | `plan_facts`, `check_plan`, `apply_plan`, `report_figures`, `figures_text`, `check_summary`, `code_summary` |
| `assistant/report.py` (new), `templates/assistant/report.html` (new) | Builds the one-page A4 PDF with xhtml2pdf. |
| `assistant/tools.py` | Adds the `plan_rest_of_month`, `propose_budget_plan` and `generate_report` tools and their schemas. Tools listed in `NEEDS_CLIENT` get the model client so they can write the summary. |
| `assistant/agent.py` | Adds the planning and report rules to the system prompt. The prompt also gains two rules: per-day questions stay with `check_budget`, and replies follow the language of the question in plain text. |
| `assistant/views.py`, `assistant/urls.py` | Adds the `apply_plan` and `report_pdf` views and the fourth suggestion. |
| `templates/assistant/_card_plan.html` (new), `_card_report.html` (new), `_turn.html` | Adds the plan card and the report card. |
| `static/js/app.js`, `static/src/app.css` | Adds the Alpine `planCard` component and the `.plan-amount` style. The chat's "thinking" bubble is now removed on `htmx:beforeSwap` of `#conversation`. |
| `templates/assistant/_input.html`, `assistant.html` | Removes `hx-on::before-swap`, which never fired on the form. |
| `evals/assistant.jsonl`, `docs/eval_results.md` | Adds 4 cases, plus Runs 3 and 4. |
| `requirements.txt` | Pins `xhtml2pdf` and its dependencies. The file is rebuilt from the venv because `4c057fa` had committed the global Python's 212 packages. |

## Differences from the plan

- **The plan's total must equal what is left, not just stay at or below it.** This keeps the monthly plan total unchanged, which design decision 2 already states.
- **There are no upcoming bills in the plan facts,** because the data model has no recurring bills. The proposal lists this as out of scope.
- **The chat "thinking" bubble fix was not planned.** QA found the optimistic question and the dots stayed on screen after the answer, because htmx 2 fires `beforeSwap` on the target, not on the form. This bug came from part 1.
- **The language and Markdown rule in the system prompt was not planned.** In QA the model answered an English question in Indonesian and wrote `**Apply to Budget**` literally.
- **The PDF footer has no "Not professional financial advice".** This matches the developer's earlier request to remove that line from the Assistant.
