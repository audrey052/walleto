# Changes: add-assistant (MVP 7, part 1)

This is the implementation log for this change. It lists what was created or modified, and where the result differs from `proposal.md`, `design.md` and `tasks.md`. Per-commit detail is in `openspec/commits/`.

- **Status:** archived on 2026-11-25, with the `assistant` spec synced to `openspec/specs/assistant/spec.md`. Saving a draft card in a real browser with the real model was still not checked.
- **Date:** 2026-11-25
- **Tests:** 451 passing; 55 new in `assistant/tests/`: models, tools, agent, views, evaluation.
- **Validation:** `openspec validate add-assistant --strict` passes; `makemigrations --check` is clean.
- **Evaluation:** `gpt-6-luna`, 21 of 24 on the first run, then 23 of 24 (`docs/eval_results.md`).

## Commits

| Commit | Message | Record |
|---|---|---|
| this commit | feat: add the assistant | `add-assistant.md` |

## Routes

| Method | URL | Name | Purpose |
|---|---|---|---|
| GET | `/assistant/` | `core:assistant` | the page; now `assistant.views.assistant` (the placeholder is gone) |
| POST | `/assistant/ask/` | `assistant:ask` | one question; HTMX gets the new turn, no-JS gets a redirect |
| GET | `/assistant/?chat=<id>` | `core:assistant` | an earlier conversation from History |
| POST | `/assistant/new/` | `assistant:new` | a new, empty conversation |
| POST | `/assistant/drafts/<id>/save/` | `assistant:save_draft` | save a confirmation card as a transaction (source AI) |
| POST | `/assistant/drafts/<id>/cancel/` | `assistant:cancel_draft` | discard it |

## Files

| File | Change |
|---|---|
| `assistant/` (new app) | `models.py` (`Conversation`, `Message`) and migration `0001`; `tools.py`; `llm.py`; `agent.py`; `views.py`; `urls.py`; `evaluation.py`; `management/commands/eval_assistant.py` |
| `templates/assistant/` | `assistant.html`, `_turns.html`, `_turn.html`, `_input.html`, `_limit.html`, `_card_figures.html`, `_card_draft.html` |
| `static/src/app.css`, `templates/layouts/app.html` | `.assistant-*` styles: prompts, messages, one-screen layout, input; `main_padding` block |
| `config/settings.py`, `config/urls.py` | `assistant` app; `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_REASONING_EFFORT`, `ASSISTANT_DAILY_LIMIT`, `ASSISTANT_MAX_TOOL_ROUNDS`; assistant URLs |
| `core/urls.py`, `core/views.py`, `core/tests.py`, `templates/core/placeholder.html` | route moved; placeholder view, template and test removed |
| `templates/finance/transactions.html` | an "AI" label on transactions recorded by the assistant |
| `requirements.txt`, `.env.example` | `openai` 3.58.0 and its dependencies; `OPENAI_MODEL`, `OPENAI_REASONING_EFFORT` |
| `evals/assistant.jsonl` | 20 lookups and drafts, 4 refusals |
| `docs/eval_results.md` | two runs |

## Differences from the plan

- **`reasoning_effort` setting.** `gpt-6-luna` rejects function tools on Chat Completions unless `reasoning_effort` is `none` (it points to the Responses API otherwise).
  - `OPENAI_REASONING_EFFORT` is sent when set; `.env` has `none`.
  - Moving `llm.py` to the Responses API is the alternative if answers need reasoning.
- **One-screen layout with a growing input.** At the developer's request after the first look:
  - the question box is a textarea that wraps and grows to about six lines (Enter sends, Shift+Enter is a new line);
  - the page is exactly one screen high (`.assistant-screen`, no page scroll);
  - the conversation scrolls inside it and opens at the latest message;
  - the box sits right above the page footer (and on phones above the bottom bar);
  - `layouts/app.html` gains a `main_padding` block so the page can drop the bottom padding;
  - the chat icon above the suggestions and in the not-set-up state is gone.
- **Chat-app look, wider column.** At the developer's request:
  - the column is 860px (Figma had 710px);
  - the question is a grey bubble on the right with no "You" label;
  - the answer is plain text with its cards, with no green box and no "Walleto" label.
- **Chat behaviour on send.** The question shows at once as a bubble, followed by a "thinking" bubble with three pulsing dots (`window.walletoChat` in `static/js/app.js`). The server's turn replaces both. If the request fails, the question stays with the error note. The textarea empties as soon as the question is sent, and the "Thinking…" line under the chat is gone.
- **History.** The developer asked for it after "New chat" left earlier chats out of reach. It was out of scope in the proposal; the spec, proposal and design are updated.
  - History and New chat are icon-only buttons (a clock and a plus), with "History" and "New chat" as their accessible names and hover titles.
  - The History button lists up to 30 conversations, titled by their first question, newest activity first.
  - Choosing one opens `/assistant/?chat=<id>`, and questions asked there continue it.
  - Another user's ID gives 404.
- **No disclaimer line.** "Based on the data you've recorded. Not professional financial advice." was removed at the developer's request; the spec no longer asks for it. The system prompt still declines investment advice.
- **"AI" label on Transactions.** Task 4.2 checks that a saved draft shows as AI there; nothing displayed `source` before.
- **No "On track" chip in goal cards**, the same as the Savings goals page (`bd904d9`).
- **Message fields.** `tool_calls`, `cards` and `counted_transactions` sit beside the design's fields:
  - a draft card lives on its tool row, so its state has one home;
  - the answer row holds the count.
- **Evaluation fix after run 1:**
  - tool descriptions now say which tool answers "how much did I spend" (`query_transactions`) and which gives a month overview;
  - the prompt defines "this past week" and "the last 7/30 days" as including today.

## Verification

- `python manage.py test`: 451 tests OK. The fake client means no network or key.
- One direct call with the demo data: "How much did I spend on food this month?" chose `query_transactions` with Food & drinks.
- The developer's own session on the demo account (three questions, in English and Indonesian) answered with figure cards and "Calculated from 68 transactions".
- Edge headless, demo account:
  - the textarea grows from 36 to 56px (1440px) and 76px (390px) with a long question;
  - the input's bottom is at the screen's bottom (803 of 803px at 1440px) and at the bottom bar's top (639 of 640px at 390px);
  - only the conversation scrolls, and it opens at the end;
  - History opens a list inside the screen (1000–1320px at 1440px; 16–336px at 390px);
  - with the send request held by the browser (no server call), the question bubble and the dots appear and the textarea is empty; failing that request leaves the question with "The assistant couldn't answer right now. Try again." and nothing is stored;
  - no horizontal scroll.
- `python manage.py eval_assistant`: run 1, 21 of 24; run 2, 23 of 24. The miss: "How much did I spend this month?" without `kind: expense`, whose result still includes the expenses.

**Not executed:** saving a draft card through the browser with the real model. A headless run as a temporary user was stopped. The save path is covered by the view tests (`DraftTests`), and the temporary user was deleted.

## Open before archiving

- The developer restarts their dev server (port 8000) so it reads `OPENAI_MODEL` and `OPENAI_REASONING_EFFORT` from `.env`, records and saves a transaction from the chat, then runs `/opsx:archive add-assistant` (sync: new `assistant` spec).
- `docs/STYLE.md`, `docs/decisions.md` and `WORKPLAN.md` are updated locally only (`.gitignore`).
