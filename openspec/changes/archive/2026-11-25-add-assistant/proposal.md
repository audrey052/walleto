# Proposal: add-assistant

## Why

The Assistant page is still a "Coming soon" placeholder. It is the AI part of the portfolio. People ask about their money in plain language ("How much did I spend on food this month?"), and the answer must come from the numbers the app already computes, never from the model's arithmetic. This is MVP 7, part 1 of 2. MVP 6 (Quick add) is skipped for now.

## What Changes

- **Assistant page.** It replaces the placeholder:
  - the heading and subtitle;
  - the conversation in the middle;
  - an input at the bottom;
  - three numbered suggestion prompts while the conversation is empty;
  - a "New chat" action that starts an empty conversation.
- **Chat history.** Each user's conversations and messages are stored. The page shows the latest conversation, so it survives a reload, and a "History" list reopens earlier ones (added after the first build, at the developer's request).
- **Tool calling with the OpenAI SDK** (no LangChain). The model picks tools, and Python functions compute every number. The system prompt says:
  - answer only from tool results;
  - never calculate;
  - refuse questions about specific investments or stocks.
- **Read-only tools.** Plain functions, tested without a model, all limited to the signed-in user:
  - `query_transactions`: a period, with optional category, wallet, keyword and kind. Returns the total, the count, and the change against the previous period of the same length;
  - `get_monthly_summary`: a month's income, expenses, plan, remaining, the meal-days line and top categories;
  - `check_budget`: a month's plan or one category's limit, spent, remaining and per-day amount;
  - `get_goal_progress`: one goal or all active goals. Returns saved, target, to go, status and the monthly amount.
- **Recording a transaction from chat.** `add_transaction` takes a description, amount, category, wallet, date and note, choosing only from the user's own categories and wallets. Code validates it with the same rules as the Transactions form.
  - The chat shows a **confirmation card**.
  - Nothing is saved until the user chooses **Save**, which records the transaction with source "AI".
  - **Cancel** discards it.
- **Answers carry data cards** built by code from tool results:
  - a figure card (totals, budget, goal);
  - the confirmation card;
  - the line "Calculated from N transactions" under answers that used transaction data.
- **Cost limits:**
  - at most 4 tool rounds per question;
  - at most 30 questions per user per day (Asia/Jakarta);
  - a clear message when the limit is reached.
- **Configuration and failures:**
  - `OPENAI_API_KEY` and `OPENAI_MODEL` come from `.env`, which is never committed. `.env.example` lists them.
  - Without them, the page says the assistant is not set up.
  - When the API fails or times out, the user sees a short error message and can ask again.
- **Evaluation:**
  - `evals/assistant.jsonl` holds about 20 questions with the expected tool and arguments, plus a few that must be refused;
  - a management command scores tool choice, arguments and refusals against the real API;
  - the first results go to `docs/eval_results.md`.

### Out of scope

- `plan_rest_of_month`, the plan card and "Apply to Budget" (part 2).
- The monthly PDF report (part 2).
- Streaming answers, and "Help me plan" buttons on Budget and Savings goals.
- Natural-language Quick add on Transactions (MVP 6).
- Rate limits specific to the demo account (MVP 8).

## Capabilities

### New Capabilities

- `assistant`: the Assistant page, conversations and their history, the tools and what they return, confirmation before saving, cards, limits, configuration and failure messages, refusals, and privacy.

### Modified Capabilities

- None. The app-shell rule "Placeholder section pages" stays as written; the Assistant simply stops being a placeholder.

## Impact

- **New Django app `assistant`:**
  - models `Conversation` and `Message`, with a migration;
  - `tools.py` (functions and their JSON schemas);
  - `llm.py` (the OpenAI client and a fake client for tests);
  - `agent.py` (the tool loop);
  - views, URLs and templates.
- **Reused code:** `finance/periods.py`, `finance/summary.py`, `finance/budgets.py`, `finance/goals.py`, and `finance/forms.py::TransactionForm`, which validates drafts.
- **Routing:** `core:assistant` moves from the placeholder view to `assistant/views.py`, keeping its name and address.
- **Dependency:** `openai`, pinned in `requirements.txt`.
- **Settings:** `ASSISTANT_DAILY_LIMIT` and `ASSISTANT_MAX_TOOL_ROUNDS`, with defaults 30 and 4.
- **Files:**
  - new `evals/assistant.jsonl` and the `eval_assistant` management command;
  - `docs/eval_results.md` (local, like the other docs).
- **Tests:** a fake client, so tests never call the network or need a key.
