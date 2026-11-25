# Add the Assistant (MVP 7, Part 1) and a Page Footer

**Created:** 2026-11-25
**Last edited:** 2026-11-25
**Status:** Implemented
**Commit:** this commit
**Branch:** `main`, parent `8b5a864`
**OpenSpec change:** `add-assistant`, tasks 1.1–6.2, archived in this commit (`openspec/changes/archive/2026-11-25-add-assistant/`)
**Trigger:** The developer skipped MVP 6 for now and asked for the Assistant. Scope was chosen in two questions: part 1 first; drafts filled by the model and checked by code; the developer's key with `gpt-6-luna`. Then `/opsx:apply add-assistant`, with one commit for the whole change.

## Why this is recorded here

The app's first AI feature, a new Django app, a new dependency (`openai`) and new settings read from `.env`.

## Context

- The model only chooses tools and writes sentences. Every figure comes from code shared with Home, Transactions, Budget and Savings goals, and every card is built from tool results.
- Nothing is saved without the user's Save on a confirmation card.

## What is built

| Area | Change |
|---|---|
| `assistant` app | `Conversation` and `Message`; tools; OpenAI client and a fake for tests; the tool loop; views and URLs; evaluation |
| Tools | `query_transactions`, `get_monthly_summary`, `check_budget`, `get_goal_progress`, `add_transaction` (draft only); names resolved inside the user's own data |
| Page | an 860px chat column with question bubbles on the right and plain-text answers, suggestions, a one-screen layout with a scrolling conversation and the input at the bottom edge, figure and draft cards, "Calculated from N transactions", a growing textarea, the question bubble and "thinking" dots right on send, "New chat" and "History" (reopen and continue earlier conversations), not-set-up and error states, daily limit |
| Transactions | an "AI" label on assistant-recorded rows |
| Page footer | a full-width 44px band (top border, sidebar background) under every signed-in page, the Assistant included (its one-screen chat is 44px shorter): "© <year> Walleto. All rights reserved.", centred; sticky, so it stays at the bottom of the screen while the page scrolls (above the phone's bottom bar); the same line, centred, on the sign-in page. Asked for in the same session (a copyright line, then "a footer", then that it stays) |
| Sidebar | no line above the account button, at the developer's request |
| Font | Nunito (variable 400–800, latin subset, self-hosted as `static/fonts/nunito-latin.woff2` with its OFL notice) replaces Plus Jakarta Sans everywhere; the developer picked it from a side-by-side with Fredoka, Quicksand and Baloo 2 |
| Evaluation | `evals/assistant.jsonl`, `manage.py eval_assistant`, `docs/eval_results.md` (23 of 24 on run 2) |

## Requirements this establishes

1. **The Assistant never shows a figure that code did not compute.**
2. **Saving needs a click on the card.** A card is used once.
3. **Cost is bounded:** at most 4 tool rounds per question and 30 questions per user per day.
4. **Tests never call OpenAI.**

## Files changed

| File | Change |
|---|---|
| `assistant/**`, `templates/assistant/**` | new |
| `config/settings.py`, `config/urls.py`, `core/urls.py`, `core/views.py`, `core/tests.py` | wiring; placeholder removed |
| `templates/core/placeholder.html` | deleted |
| `templates/finance/transactions.html`, `static/src/app.css`, `templates/layouts/app.html`, `templates/layouts/auth.html` | AI label; assistant styles; `main_padding` and `footer` blocks; `.app-footer`; the workspace is a full-height column |
| `static/fonts/nunito-latin.woff2` (new), `static/fonts/plus-jakarta-sans-latin.woff2` (deleted), `static/fonts/OFL.txt`, `templates/base.html` | font |
| `requirements.txt`, `.env.example` | `openai`; model and reasoning settings |
| `evals/assistant.jsonl`, `docs/eval_results.md` | evaluation |
| `openspec/changes/archive/2026-11-25-add-assistant/` | proposal, spec, design, tasks (all ticked), changes; archived |
| `openspec/specs/assistant/spec.md` | new main spec, synced from the delta (11 requirements) |
| `openspec/commits/README.md`, `no-desktop-top-bar.md` | `8b5a864` filled in, this record |

## Verification

**Executed:**

- `python manage.py test`: 452 tests OK (with the copyright test in `core/tests.py`).
- Edge headless, scrolled 300px into Home and Transactions: the footer stays at the screen's bottom (760–803px of 803px at 1440px) and right above the bottom bar (596–639px, bar at 640px, at 390px); on the Assistant the input ends where the footer starts (759px at 1440px, 595px at 390px) and the page does not scroll.
- `openspec validate add-assistant --strict`: valid; after the sync, `openspec validate assistant --type spec --strict`: valid.
- Real model calls (demo data): a direct tool call, the developer's own three-question session, and two evaluation runs (21 and 23 of 24).
- Edge headless at 1440px and 390px: the input sits at the bottom edge (above the phone's bottom bar), the page does not scroll, the conversation scrolls and opens at the end, and the textarea grows with long text.

**Not executed:**

- Saving a draft card through the browser with the real model. The view tests cover it.

## Known gaps

- **Chat Completions with `reasoning_effort=none`.** `gpt-6-luna` needs it for tools there. The Responses API would allow reasoning with tools.
- **Part 2 is open:** the rest-of-month plan with "Apply to Budget", and the PDF report.
