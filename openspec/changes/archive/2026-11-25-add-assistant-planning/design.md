# Design: add-assistant-planning

## Context

See proposal.md for why. Part 1 (`add-assistant`, archived) gives:

- **`assistant/tools.py`:** a registry of `fn(user, today, **args) -> ToolResult(data, cards, counted)`. Per-user JSON schemas list category, wallet and goal names as `enum`s. `run_tool()` turns bad arguments into `{"error": …}`.
- **`assistant/agent.py`:** at most 4 tool rounds. Tool rows store their `cards`, and the answer row shows the cards of its turn.
- **`assistant/views.py`:** draft cards live on their tool `Message` (`cards[0]`). They are saved by `POST …/drafts/<id>/save` through `Message.objects.for_user()` with `select_for_update`, and a `state` field makes them single-use.
- **`assistant/llm.py`:** a `chat(messages, tools)` client, a `FakeClient`, and `OPENAI_REASONING_EFFORT` for `gpt-6-luna`.
- **Budget data:**
  - `finance/budgets.month_budget()` gives the plan rows (`BudgetRow(category, limit, spent)`), `days_left()`, `per_day()` and the plan total.
  - `Budget(user, category, month, limit)` has `MIN_CATEGORY_LIMIT` (Rp1.000) and a unique (user, category, month) constraint.
  - The monthly plan is the sum of the limits and is never stored.
- **Report figures:** `finance/summary.period_summary()` and `finance/goals.summarize()` already compute them for Home and Savings goals.

## Goals / Non-Goals

**Goals:**
- The model never writes an amount into a card or the PDF table. A summary sentence that does is replaced.
- Applying a plan changes only the current month's limits of limited categories, keeps the plan total, and happens once.
- Every new rule is a pure function tested without a model.

**Non-Goals:**
- A recurring-bills model, plans for other months, or new limits for unlimited categories.
- Storing PDF files. A report is rendered when it is downloaded, from figures frozen in its card.

## Decisions

### 1. Two tools for a plan: facts, then a proposal

- `plan_rest_of_month()` takes no arguments and returns the facts for the current month:
  - `plan`, `left` (the sum of `limit - spent` over the limited rows), `days_left`;
  - per row: `category`, `limit`, `spent`, `left`, `daily_average` (`spent // today.day`).
  - Without a plan, or with `left <= 0`, it returns a note and no plan can follow.
- `propose_budget_plan(amounts: [{category, amount}], note)` takes the model's proposal. Code validates it (decision 2) and returns either an error for the model to fix, or a **plan card** with `cards[0] = {"type": "plan", "state": "pending", "month": "2026-11", "left": …, "rows": [{category_id, name, spent, left_now, amount, per_day}]}`.
- The tool descriptions and system prompt say to call the facts tool first and to make the amounts add up to `left`.

*Rejected: one tool where code splits the money.* WORKPLAN wants the model to plan from the facts, with code checking the result.

*Rejected: Chat Completions `response_format`.* A tool call with a JSON schema gives the same structured output inside the existing loop, and its errors go back to the model like any other tool's.

### 2. Validation (`assistant/planning.py`)

`check_plan(facts, amounts) -> (rows, error)`. The checks, in order:

1. Every limited category appears exactly once, and only those (matched by name, case-insensitive).
2. Each amount is an integer ≥ 0.
3. `sum(amounts) == facts.left`. The error names the difference.
4. `spent + amount >= MIN_CATEGORY_LIMIT` for each row.

The same function runs again when Apply is posted, with the edited amounts and fresh facts. Spending may have changed since the card was made, so Apply always re-reads `month_budget`.

*Rejected: allowing a total below `left` and lowering the plan.* The developer chose "remaining of the monthly plan" as the money to divide, so Apply keeps the plan total.

### 3. Apply to Budget

`POST /assistant/plans/<message_id>/apply` with `amount_<category_id>` fields from the card (the Edit inputs). It:

- finds the message through `Message.objects.for_user(request.user)` with `select_for_update`, and returns 404 for others;
- refuses unless `state == "pending"` and the card's month is the current month (Asia/Jakarta);
- runs `check_plan` with fresh facts;
- in one transaction, updates each row's `Budget.limit = spent + amount` and sets `state = "applied"` with the new plan total.

When invalid, it returns the card with the error and changes nothing. HTMX swaps the card; without JavaScript it redirects back.

### 4. Plan card and Edit

- `_card_plan.html` is a small form, Alpine `planCard`. It has one row per category: name, left now, a number input for the suggested amount (read-only until **Edit**), and the per-day value (`amount // days_left`, recomputed in the browser).
- The footer shows "Adds up to Rp… of Rp…" and turns red with "Rp… over/under" when the amounts differ. Apply is disabled until they add up, and the server checks again.
- Once applied, the card shows "Applied to Budget" and a link to Budget.

### 5. Report figures, summary and PDF

- `report_figures(user, month, today)` in `planning.py` returns a frozen dict:
  - income, expenses, plan, remaining (`period_summary`);
  - category rows (spent, limit or `None`, percent; from `month_budget`);
  - the 10 largest expenses (`Transaction…expense().order_by("-amount", "-date")[:10]`);
  - active goals (`goals.summarize`).
- `generate_report(month)`:
  1. computes the figures;
  2. asks the model for a 2–3 sentence summary in one extra `chat()` call without tools, with the figures as text and the rule "use only these numbers";
  3. runs `check_summary(text, figures)`, which extracts every `Rp…` amount and `…%` in the text and requires each to be in the figures' formatted values;
  4. on failure, or on `AssistantUnavailable`, uses `code_summary(figures)` ("In October you spent Rp… of a Rp… plan; Food & drinks was the largest category.").
  The card is `{"type": "report", "month": "2026-10", "figures": …, "summary": …}`.
- `GET /assistant/reports/<message_id>.pdf` (user-scoped, 404 otherwise) renders `templates/assistant/report.html` with **xhtml2pdf** into `walleto-report-2026-10.pdf`.
- The extra model call is part of the tool's cost. It counts as one more call, still within the question's limits.

*Rejected: WeasyPrint.* It needs Pango and GTK installed on Windows, outside pip. xhtml2pdf is pure Python (ReportLab underneath) and handles a one-page table layout. Its limited CSS (no flex or grid) is fine for tables.

*Rejected: storing the PDF bytes.* Rendering from the frozen figures gives the same file every time and needs no file storage.

### 6. Prompt, suggestions and evaluation

- **System prompt additions:**
  - for planning, call `plan_rest_of_month` and then `propose_budget_plan` with amounts that add up to `left`, keeping categories with a high daily average realistic;
  - for a report, call `generate_report`;
  - never state amounts that are not in tool results.
- `SUGGESTIONS` gains "Help me plan the rest of the month".
- `evals/assistant.jsonl` gains cases for:
  - "Help me plan the rest of the month" → `plan_rest_of_month`;
  - "Make a report for October" → `generate_report{month: last month}`;
  - "Bikin laporan bulan ini" → `generate_report{}`.

## Risks / Trade-offs

- **[The model's amounts rarely add up exactly the first time]** The error states the exact difference, so the model can fix it; 4 rounds leave room for facts + proposal + one retry.
- **[Spending changes between the card and Apply]** Apply re-checks with fresh facts. If `left` changed, the card says so and asks for a new plan.
- **[xhtml2pdf layout limits]** The report uses tables and fixed widths only. A test checks the PDF starts with `%PDF` and contains the month name.
- **[Summary check too strict, e.g. "Rp1,9 juta"]** The fallback summary is always correct, and the prompt asks for the exact Rp format.

## Migration Plan

- No migration: cards live in the existing `Message.cards` JSON.
- New dependency `xhtml2pdf`, pinned.
- Rollback: revert; existing plan and report cards render as plain messages.
