# Tasks

## 1. Plan logic (no model)

- [x] 1.1 `assistant/planning.py`: `plan_facts(user, today)` (plan, left, days left, rows with limit, spent, left, daily average) and `check_plan(facts, amounts)` (design decision 2). Verify unit tests for:
  - "Facts" and "No plan" (and nothing left);
  - "Amounts do not add up" (the error names the difference);
  - "Unknown category" and a missing category;
  - a negative amount, a non-integer, and a resulting limit under Rp1.000;
  - another user's limits never counted.
- [x] 1.2 `apply_plan(user, rows, today)`: sets each limit to spent + amount in one transaction. Verify tests that the plan total is unchanged, other months and unlimited categories are untouched, and a failure in the middle changes nothing.

## 2. Report logic (no model)

- [x] 2.1 `report_figures(user, year, month, today)`, `check_summary(text, figures)` and `code_summary(figures)` (design decision 5). Verify tests for:
  - the figures matching Home and Budget for October (income, expenses, plan, remaining, category percents);
  - the 10 largest expenses in order;
  - goal progress;
  - "Invented number" (rejected), and a summary that only uses the figures (kept);
  - another user's data never included.
- [x] 2.2 Install `xhtml2pdf` and pin it; write `assistant/report.py` and `templates/assistant/report.html` (one page: summary, figures, category table, largest expenses, goals). Verify a test that the bytes start with `%PDF` and the rendered HTML contains the month and the figures.

## 3. Tools and loop

- [x] 3.1 Tools `plan_rest_of_month`, `propose_budget_plan` and `generate_report` with schemas and descriptions, plus the system-prompt additions (design decisions 1, 5, 6). Verify tests:
  - each tool's result and card;
  - `propose_budget_plan` errors returned to the model;
  - `generate_report` for a future month refused;
  - the summary call made with the `FakeClient`, and the fallback when it fails or invents a number;
  - a `FakeClient` loop of facts → bad proposal → fixed proposal → answer, which shows one plan card.

## 4. Page

- [x] 4.1 Views and URLs: `POST /assistant/plans/<id>/apply` and `GET /assistant/reports/<id>.pdf` (design decisions 3 and 5). Verify page tests for:
  - "Apply" (limits changed, plan total unchanged, card applied);
  - "Edited amounts that do not add up";
  - "Applied twice";
  - "Month has passed";
  - "Report for a month" (download is a PDF named `walleto-report-2026-10.pdf`);
  - "Another user's report" and "Another user's plan" (404, nothing changed);
  - "Suggestion shown".
- [x] 4.2 `_card_plan.html` (Alpine `planCard`: Edit, live per day and total, Apply disabled until it adds up) and `_card_report.html` (month, summary, Download PDF), with styles; then `npm run css:build`. Verify in Edge (demo account, with the developer's key):
  - ask for a plan, edit one amount, and see the total warning;
  - fix it, apply, and see Budget's limits changed with the same plan total;
  - ask for October's report and download the PDF;
  - no horizontal scroll at 1440px and on a phone.

## 5. Evaluation

- [x] 5.1 Add the planning and report cases to `evals/assistant.jsonl` (design decision 6); run `python manage.py eval_assistant --label "Run 3: planning and reports"`. Verify `docs/eval_results.md` has the new run, and fix the prompt for any new miss.

## 6. Wrap-up

- [x] 6.1 Update `docs/STYLE.md` (Assistant row: plan and report cards), `WORKPLAN.md` (MVP 7 part 2 ticked) and `docs/decisions.md` (two-step plan tools, xhtml2pdf over WeasyPrint, summary check, reports rendered on download). Verify that `python manage.py test` and `openspec validate add-assistant-planning --strict` pass.
- [x] 6.2 Write `changes.md` and the commit record in `openspec/commits/`; verify the index lists it.

## Workflow follow-up

- The developer tries a plan and a report in a real browser, then archives with `/opsx:archive add-assistant-planning`.
