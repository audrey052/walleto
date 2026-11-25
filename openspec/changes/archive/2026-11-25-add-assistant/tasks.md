# Tasks

## 1. Setup

- [x] 1.1 Install `openai` and pin it in `requirements.txt`. Add `OPENAI_MODEL=` to `.env.example`, and `ASSISTANT_DAILY_LIMIT` (30) and `ASSISTANT_MAX_TOOL_ROUNDS` (4) to settings. Verify `pip install -r requirements.txt` and `python manage.py check` pass.
- [x] 1.2 Create the `assistant` app with `Conversation` and `Message` (design decision 1) and its migration. Verify model tests:
  - a conversation belongs to one user;
  - messages come back in order;
  - a draft card's state is stored;
  - `makemigrations --check` is clean.

## 2. Tools (no model involved)

- [x] 2.1 `assistant/tools.py`: the registry, the JSON schemas with per-user `enum` lists, name resolution inside the user's querysets, and error results. Verify tests that unknown names and bad periods return an error, never an exception.
- [x] 2.2 `query_transactions`; verify tests for:
  - "Spending in a category" (same total as the Transactions page for the same period and filter);
  - "Compared with the previous period";
  - the keyword and kind filters;
  - `counted`;
  - "No data".
- [x] 2.3 `get_monthly_summary` and `check_budget`; verify tests for "Budget question" (the same remaining as Budget), one category's limit, spent and per day, and a month without a plan.
- [x] 2.4 `get_goal_progress`; verify tests for "Goal progress" (the same figures as `goals.summarize`), all active goals, and an unknown goal name.
- [x] 2.5 `add_transaction` as a draft with `TransactionForm`; verify tests for:
  - a valid draft (card fields, nothing saved);
  - "Invalid draft" (unknown wallet, zero amount, future date);
  - an archived wallet refused.
- [x] 2.6 Privacy of the tools; verify tests that another user's transactions, budgets, goals, wallets and categories are never counted, found or offered (the scenario "Another user's data").

## 3. Model loop

- [x] 3.1 `assistant/llm.py`: the client wrapper, `is_configured()`, `AssistantUnavailable`, and `FakeClient`. Verify tests that a missing key or model makes it unconfigured, and that an SDK error becomes `AssistantUnavailable`.
- [x] 3.2 `assistant/agent.py`: the system prompt, history (last 20), tool rounds capped at 4 with a final call without tools, stored tool messages, the answer's cards and transaction count. Verify `FakeClient` tests for:
  - one tool then an answer;
  - two tools in one turn;
  - the 4-round cap;
  - "Stock tip" (no tool call);
  - "Card and count".

## 4. Page

- [x] 4.1 Views and URLs:
  - `core:assistant` (moved from the placeholder), `ask`, `new`, and draft `save`/`cancel`;
  - the daily limit, the not-set-up state, and the error message.

  Remove the placeholder test in `core/tests.py` and add page tests for:
  - "Empty conversation", "Suggestion", "Reload";
  - "Daily limit", "Missing configuration", "Timeout";
  - "Confirm and save", "Nothing saved before confirming", "Double save";
  - "Another user's card".
- [x] 4.2 Templates and styles after the Figma Make Assistant page, with STYLE.md copy:
  - heading and subtitle, numbered prompts, conversation rows;
  - figures card, draft card with Save and Cancel, "Calculated from N transactions";
  - input with the "Thinking…" indicator, disclaimer, "New chat".

  Then `npm run css:build`. Verify in Edge (demo account, with the developer's key) at 1440px and 520px:
  - ask a spending question;
  - record a transaction and save it;
  - check the Transactions page shows it as AI;
  - reload and see the conversation;
  - no horizontal scroll.

## 5. Evaluation

- [x] 5.1 Write `evals/assistant.jsonl` (about 20 lookups and drafts, plus 4 refusals) and the `eval_assistant` management command (design decision 7). Verify a unit test of its scoring on two fake replies.
- [x] 5.2 Run `python manage.py eval_assistant` with the developer's key. Write the first results to `docs/eval_results.md`. Fix the prompt or tool descriptions for the most common miss and run it again. Verify the file has both runs.

## 6. Wrap-up

- [x] 6.1 Update `docs/STYLE.md` (Assistant page row), `WORKPLAN.md` (MVP 7 part 1 ticked, MVP 6 marked skipped for now) and `docs/decisions.md` (SDK without LangChain, cards from tool results, names instead of IDs, limits). Verify that `python manage.py test` and `openspec validate add-assistant --strict` pass.
- [x] 6.2 Write `changes.md` and the commit record in `openspec/commits/`; verify the index lists it.

## Workflow follow-up

- The developer tries the Assistant with their key in a real browser, then archives with `/opsx:archive add-assistant`.
- Part 2 (`plan_rest_of_month`, Apply to Budget, the PDF report) is a separate change.
