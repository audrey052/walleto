# Design: add-assistant

## Context

See proposal.md for why.

- **Placeholder.** `/assistant/` (`core:assistant`) renders `core.views._placeholder`, and `core/tests.py` checks its "Coming soon" text.
- **Figures already exist as services:**
  - `finance/periods.py` (`Period`, `parse_period`) and `finance/summary.py::period_summary` (Home);
  - `finance/budgets.py::month_budget` (Budget, with rows per category, `per_day`, `days_left`);
  - `finance/goals.py::summarize` (Savings goals);
  - `Transaction.objects.for_user().in_period().totals()` (Transactions).
- **Saving a transaction.** `finance/forms.py::TransactionForm` validates a transaction for a user: active wallets only, the user's categories, positive amount, no future date. `Transaction.Source.AI` ("AI quick add") already exists.
- **Configuration.** `.env` is loaded in `config/settings.py` and ignored by git. `.env.example` already lists `OPENAI_API_KEY`. No AI dependency is installed yet.
- **Figma Make "Assistant" page:** intro, three numbered prompts (`.assistant-prompts`), conversation, rounded input with an arrow button, disclaimer.
- **STYLE.md copy rules:** no poetic eyebrow ("A LITTLE PERSPECTIVE"), no poetic headline. The heading is "Assistant" with its subtitle.

## Goals / Non-Goals

**Goals:**
- The model never produces a number the user sees in a card. Cards are rendered from tool results.
- Every tool can be tested without a model, and the whole loop can be tested with a fake client.
- A fixed, small cost per question (4 tool rounds) and per user per day (30 questions).

**Non-Goals:**
- A conversation list, streaming, the rest-of-month plan, or PDF reports (part 2).
- Choosing or tuning a model. The developer sets `OPENAI_MODEL`.

## Decisions

### 1. A separate `assistant` app with two models

- `Conversation(user, created_at)` and `Message(conversation, role, text, tool_name, tool_args, tool_result, card, counted, created_at)`.
  - `counted` marks a question that uses up the daily limit (decision 6).
  - `role` is `user`, `assistant` or `tool`.
  - `card` is a small JSON value the template renders: `{"type": "figures" | "draft", …}`.
  - Tool rows keep the call and the result, so a later turn can send the history back to the model.
- The page shows the user's latest conversation, or the one in `?chat=<id>` (looked up in the user's own conversations, so any other ID is 404). "New chat" creates a new, empty one. Questions carry the conversation's ID in a hidden `chat` field.
- "History" lists up to 30 conversations that have a question, newest activity first, titled by their first question, in one query with a subquery and `Max`.
- A draft transaction lives in a `Message` with `card.type = "draft"` and `card.state` = `pending`, `saved` or `cancelled`. Saving re-validates and changes the state in one transaction.

*Rejected: storing the draft in the session.* It would be lost on logout, and the card's state would not survive a reload.

### 2. Tools are plain functions with JSON schemas (`assistant/tools.py`)

- Each tool is `fn(user, today, **args) -> ToolResult(data, card, counted)`:
  - `data` is the JSON sent back to the model;
  - `card` is what the page shows;
  - `counted` is the number of transactions used, for "Calculated from N transactions".
- A registry maps names to the function and its JSON schema.
- **The user is never an argument.** It comes from the request.
- Categories and wallets are passed **by name** and resolved case-insensitively inside the user's own querysets.
- The schema's `enum` lists the user's names for that request, so the model can only pick real ones.
- Bad arguments return `{"error": "..."}` to the model instead of raising.

| Tool | Arguments | Reuses |
|---|---|---|
| `query_transactions` | `month` or `from`/`to`, `category`, `wallet`, `keyword`, `kind` | `parse_period`, `in_period`, `search`, `totals`, `Period.previous()` |
| `get_monthly_summary` | `month` | `period_summary` (plan fields only for a whole month) |
| `check_budget` | `month`, `category` | `month_budget` rows, `per_day` |
| `get_goal_progress` | `goal` (name, optional) | `SavingsGoal…with_saved()`, `goals.summarize` |
| `add_transaction` | `description`, `amount`, `category`, `wallet`, `date`, `note` | `TransactionForm(data, user=…)`, **not saved** |

- `add_transaction` returns the cleaned fields and a `draft` card when the form is valid, or the form's error messages when it is not.
- The draft is saved by a separate POST (decision 5), never by the loop.

*Rejected: passing IDs to the model.* Names are what people say, and resolving them inside the user's queryset makes guessing another user's ID pointless.

### 3. The loop (`assistant/agent.py`)

```
ask(conversation, text):
  messages = system prompt + today + last 20 stored messages + the new question
  for round in 1..4:
      reply = client.chat(messages, tools)
      if reply has no tool calls: store the answer and stop
      for each call: run the tool, store a tool message (args, result, card), append the result
  after round 4: one last call with tools disabled, so there is always an answer
```

- Uses OpenAI **Chat Completions with `tools`** from the official `openai` SDK.
  - Timeout 30 s, at most 1 retry.
  - Temperature low.
  - `parallel_tool_calls` allowed.
- **System prompt:**
  - answer only from tool results, in the user's language;
  - never calculate or estimate amounts;
  - say when a tool returns no data;
  - decline specific investment or stock advice;
  - give amounts the way STYLE.md writes them (Rp1.405.500).
- **The answer message carries the cards** of every tool result in its turn, in order. "Calculated from N transactions" is the sum of `counted` for that turn. It is shown only when the sum is above 0.

*Rejected: LangChain or the Assistants/Agents frameworks.* WORKPLAN asks for the SDK directly, to show the tool-calling flow.

*Rejected: letting the model write figures into cards.* Cards would then depend on the model's arithmetic.

### 4. The client and the fake (`assistant/llm.py`)

- `get_client()` returns a small wrapper around `openai.OpenAI(api_key=…, timeout=30, max_retries=1)` with one method:
  - `chat(messages, tools, tool_choice)` returns `Reply(text, tool_calls)`.
- **Configuration:**
  - `OPENAI_API_KEY` and `OPENAI_MODEL` are read from settings (via `.env`). If either is empty, `is_configured()` is false.
  - `.env.example` gains `OPENAI_MODEL=`.
- **`FakeClient(script)`** replays a list of replies (tool calls, then text). Tests set it with `override_settings(ASSISTANT_CLIENT=...)` or by patching `get_client`. No test needs a key or the network.
- API errors (`openai.APIError`, timeouts) become one `AssistantUnavailable` exception, and the view shows the spec's error message.

### 5. Views and the page

- `GET /assistant/`: the page with the latest conversation.
- `POST /assistant/ask`, with HTMX:
  1. checks the limit and the configuration;
  2. stores the question;
  3. runs the loop;
  4. returns the two new message rows, which are appended to `#conversation` (`hx-swap="beforeend"`).

  Without JavaScript the form posts and redirects back.
- `POST /assistant/new`: a new conversation.
- `POST /assistant/drafts/<message_id>/save` and `/cancel`:
  - look up the message through `Message.objects.filter(conversation__user=request.user)`, so another user's ID gives 404;
  - saving runs `TransactionForm` again, inside `select_for_update` on the message, and checks `state == pending` first;
  - each returns the card in its new state.
- **Template (`templates/assistant/assistant.html`):**
  - heading and subtitle;
  - while empty, three numbered prompts (Figma `.assistant-prompts`). Each is a small form posting its text:
    - "How much did I spend this month?"
    - "Am I within my budget?"
    - "How are my savings goals going?"
  - `#conversation`, a list of message rows:
    - the user's question on the right;
    - the answer's text, its cards and the "Calculated from N transactions" line on the left;
  - the input form at the bottom: placeholder "Ask about your spending, budget or goals", an arrow button, and an `hx-indicator` "Thinking…";
- Cards are partials: `_card_figures.html` (label and amount rows) and `_card_draft.html` (fields, Save and Cancel, or the "Saved"/"Cancelled" state).

### 6. Limits

- `ASSISTANT_DAILY_LIMIT = 30` and `ASSISTANT_MAX_TOOL_ROUNDS = 4` in settings.
- The day count is the user's `role=user` messages with `counted=True`, since Jakarta midnight.
- A question that failed with `AssistantUnavailable` is stored with `counted=False`, so it does not use up the limit.

### 7. Evaluation

- `evals/assistant.jsonl`: one line per case, `{"question", "expect": {"tool", "args"} | {"refuse": true}}`. About 20 lookups and drafts, and 4 refusals.
- `python manage.py eval_assistant`:
  - runs only the first model turn of each question against the demo user's data, with the real client;
  - compares the chosen tool and the given arguments with the expected ones (exact for names, normalised for dates and amounts);
  - prints a table and writes `docs/eval_results.md`;
  - is never run by the test suite.

## Risks / Trade-offs

- **[The model restates a number wrongly in its text]** The card next to it is always right, the prompt forbids computing, and the eval checks arguments. A text-versus-card mismatch check is a part-2 candidate.
- **[Cost]** 4 rounds and 30 questions a day per user, and only the last 20 messages are sent back.
- **[Prompt injection through transaction descriptions]** Tools only read the user's own data and cannot save. Saving needs a click on a card.
- **[Category and wallet names change between turns]** The draft stores IDs resolved at draft time, and Save re-validates against the current lists.
- **[`openai` SDK changes]** It is pinned in `requirements.txt`, and only `llm.py` touches it.

## Migration Plan

- New migration for the `assistant` app. No change to existing data.
- Rollback: revert, then `migrate assistant zero`.
