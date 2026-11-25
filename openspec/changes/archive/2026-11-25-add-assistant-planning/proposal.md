# Proposal: add-assistant-planning

## Why

Part 1 of the Assistant answers questions and records transactions. WORKPLAN's MVP 7 also asks it to plan the rest of the month and to write a monthly report. Both must keep the rule of part 1: code computes every number, the model only proposes and explains, and nothing changes without the user's confirmation.

## What Changes

- **Rest-of-month plan.** Asked "Help me plan the rest of the month", the assistant shows a plan card for the current month.
  - Code works out the facts:
    - the plan total;
    - what is left of the category limits;
    - the days left;
    - for each limited category: limit, spent, what is left, and average daily spending so far.
  - The model proposes how much each limited category may still spend.
  - Code checks the proposal:
    - only the user's limited expense categories;
    - whole Rupiah, nothing negative;
    - the proposals add up exactly to what is left;
    - every new limit is at least Rp1.000.
  - The card shows, per category, "now" against "suggested" and the amount per day.
  - **Edit** lets the user change the amounts in the card. **Apply to Budget** updates this month's category limits (new limit = spent + suggested), so the monthly plan total stays the same.
  - Nothing changes before Apply. A card is applied once, and only while its month is the current month.
  - A month with no plan, or with nothing left, gets a short answer pointing to Budget instead of a card.
- **Monthly PDF report.** Asked "Make a report for October", the assistant shows a file card with **Download PDF**. The one-page PDF has:
  - income, expenses, plan and remaining;
  - a category table (spent, limit, percent used);
  - the 10 largest expenses;
  - savings goal progress;
  - one short summary paragraph written by the model from those figures only.
  - Code rejects a paragraph that mentions an amount not in the figures and uses a plain code-written summary instead.
- **New suggestion prompt:** "Help me plan the rest of the month" joins the empty-chat suggestions.
- **Evaluation:** new cases for both tools in `evals/assistant.jsonl`.

### Out of scope

- Streaming answers, and "Help me plan" buttons on Budget and Savings goals.
- Emailing or scheduling reports.
- Upcoming bills: there are no recurring bills in the data.
- Plans for months other than the current one.
- Changing the plan total, or adding limits to categories that have none.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `assistant`: adds the rest-of-month plan (facts, validated proposal, plan card, Edit, Apply to Budget), the monthly PDF report (figures, checked summary, file card, download), the planning suggestion, and privacy for plan and report cards.

## Impact

- **`assistant/tools.py`:**
  - `plan_rest_of_month` (facts);
  - `propose_budget_plan` (the model's amounts, validated into a plan card);
  - `generate_report` (figures, summary, file card).
- **`assistant/planning.py` (new):** plan facts and validation, the report figures, and the summary check. All pure code, tested without a model.
- **`assistant/report.py` (new):** renders the PDF with **xhtml2pdf** from `templates/assistant/report.html`.
- **`assistant/views.py`, `urls.py`:**
  - `POST /assistant/plans/<id>/apply`;
  - `GET /assistant/reports/<id>.pdf`;
  - both through the user's own messages.
- **`finance/budgets.py`:** reused. Limits are written through the `Budget` model in one transaction.
- **Templates:** `_card_plan.html` and `_card_report.html`; styles in `static/src/app.css`.
- **Dependency:** `xhtml2pdf` (pure Python, works on Windows without system libraries), pinned in `requirements.txt`.
- **Tests and evaluation:** tests use the fake client; new cases go in `evals/assistant.jsonl`.
- **No new models or migrations:** plan and report cards are `Message.cards` JSON, like the transaction drafts.
