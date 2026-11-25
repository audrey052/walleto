# Evaluation results

Assistant tool choice, arguments and refusals (`python manage.py eval_assistant`).

## Run 1: first prompt

- **Model:** `gpt-6-luna`
- **Date:** 2026-11-25, demo account
- **Passed:** 21 of 24
- **Tool chosen correctly:** 18 of 20
- **Arguments correct:** 17 of 20
- **Refused correctly:** 4 of 4

| Case | Question | Expected | Got | Result |
|---|---|---|---|---|
| spend-month | How much did I spend this month? | `query_transactions({"kind": "expense"})` | `get_monthly_summary({})` | fail: wrong tool |
| food-month | How much did I spend on food this month? | `query_transactions({"category": "Food & drinks"})` | `query_transactions({"month": "2026-11", "category": "Food & drinks", "kind": "expense"})` | pass |
| food-last-month | What did I spend on Food & drinks last month? | `query_transactions({"category": "Food & drinks", "month": "{last_month}"})` | `query_transactions({"month": "2026-10", "category": "Food & drinks", "kind": "expense"})` | pass |
| transport-id | Berapa pengeluaran transport bulan ini? | `query_transactions({"category": "Transport"})` | `query_transactions({"month": "2026-11", "category": "Transport", "kind": "expense"})` | pass |
| gopay | How much went out of GoPay this month? | `query_transactions({"wallet": "GoPay"})` | `query_transactions({"wallet": "GoPay", "kind": "expense"})` | pass |
| kopi | How much have I spent on kopi this month? | `query_transactions({"keyword": "kopi"})` | `query_transactions({"keyword": "kopi", "kind": "expense"})` | pass |
| income-month | What was my income this month? | `query_transactions({"kind": "income"})` | `get_monthly_summary({})` | fail: wrong tool |
| last-7-days | How much did I spend in the last 7 days? | `query_transactions({"from": "{days_ago_6}", "to": "{today}"})` | `query_transactions({"from": "2026-11-19", "to": "2026-11-25", "kind": "expense"})` | pass |
| shopping-week | Did I spend more on shopping this past week than the week before? | `query_transactions({"category": "Shopping", "from": "{days_ago_6}", "to": "{today}"})` | `query_transactions({"from": "2026-11-18", "to": "2026-11-24", "category": "Shopping", "kind": "expense"})` | fail: from: expected '2026-11-19', got '2026-11-18'; to: expected '2026-11-25', got '2026-11-24' |
| summary | Give me a summary of this month. | `get_monthly_summary({})` | `get_monthly_summary({})` | pass |
| summary-last | How did last month go overall? | `get_monthly_summary({"month": "{last_month}"})` | `get_monthly_summary({"month": "2026-10"})` | pass |
| budget-left | How much budget do I have left? | `check_budget({})` | `check_budget({})` | pass |
| within-budget | Am I within my budget? | `check_budget({})` | `check_budget({})` | pass |
| food-limit | How much is left of my food budget? | `check_budget({"category": "Food & drinks"})` | `check_budget({"category": "Food & drinks"})` | pass |
| per-day | How much can I spend per day for the rest of the month? | `check_budget({})` | `check_budget({})` | pass |
| goals | How are my savings goals going? | `get_goal_progress({})` | `get_goal_progress({})` | pass |
| laptop | How close am I to my laptop goal? | `get_goal_progress({"goal": "New laptop"})` | `get_goal_progress({"goal": "New laptop"})` | pass |
| add-lunch | Lunch at Bakmi GM 45rb from GoPay today | `add_transaction({"amount": 45000, "category": "Food & drinks", "wallet": "GoPay"})` | `add_transaction({"description": "Bakmi GM", "amount": 45000, "category": "Food & drinks", "wallet": "GoPay", "date": "2026-11-25"})` | pass |
| add-grab-id | catat grab 18k kemarin pakai OVO | `add_transaction({"amount": 18000, "category": "Transport", "wallet": "OVO", "date": "{yesterday}"})` | `add_transaction({"description": "Grab", "amount": 18000, "category": "Transport", "wallet": "OVO", "date": "2026-11-24"})` | pass |
| add-salary | Record my salary of 12.5 million into BCA today | `add_transaction({"amount": 12500000, "category": "Salary", "wallet": "BCA"})` | `add_transaction({"description": "Salary", "amount": 12500000, "category": "Salary", "wallet": "BCA", "date": "2026-11-25"})` | pass |
| refuse-stock | Which stock should I buy right now? | `refuse` | `no tool` | pass |
| refuse-crypto | Should I put my savings into Bitcoin? | `refuse` | `no tool` | pass |
| refuse-saham | Saham apa yang bagus buat dibeli bulan ini? | `refuse` | `no tool` | pass |
| refuse-fund | Which mutual fund gives the best return? | `refuse` | `no tool` | pass |

## Run 2: clearer tool descriptions and day ranges

- **Model:** `gpt-6-luna`
- **Date:** 2026-11-25, demo account
- **Passed:** 23 of 24
- **Tool chosen correctly:** 20 of 20
- **Arguments correct:** 19 of 20
- **Refused correctly:** 4 of 4

| Case | Question | Expected | Got | Result |
|---|---|---|---|---|
| spend-month | How much did I spend this month? | `query_transactions({"kind": "expense"})` | `query_transactions({})` | fail: kind: expected 'expense', got None |
| food-month | How much did I spend on food this month? | `query_transactions({"category": "Food & drinks"})` | `query_transactions({"month": "2026-11", "category": "Food & drinks", "kind": "expense"})` | pass |
| food-last-month | What did I spend on Food & drinks last month? | `query_transactions({"category": "Food & drinks", "month": "{last_month}"})` | `query_transactions({"month": "2026-10", "category": "Food & drinks", "kind": "expense"})` | pass |
| transport-id | Berapa pengeluaran transport bulan ini? | `query_transactions({"category": "Transport"})` | `query_transactions({"kind": "expense", "category": "Transport"})` | pass |
| gopay | How much went out of GoPay this month? | `query_transactions({"wallet": "GoPay"})` | `query_transactions({"month": "2026-11", "wallet": "GoPay", "kind": "expense"})` | pass |
| kopi | How much have I spent on kopi this month? | `query_transactions({"keyword": "kopi"})` | `query_transactions({"keyword": "kopi", "kind": "expense"})` | pass |
| income-month | What was my income this month? | `query_transactions({"kind": "income"})` | `query_transactions({"kind": "income"})` | pass |
| last-7-days | How much did I spend in the last 7 days? | `query_transactions({"from": "{days_ago_6}", "to": "{today}"})` | `query_transactions({"from": "2026-11-19", "to": "2026-11-25", "kind": "expense"})` | pass |
| shopping-week | Did I spend more on shopping this past week than the week before? | `query_transactions({"category": "Shopping", "from": "{days_ago_6}", "to": "{today}"})` | `query_transactions({"from": "2026-11-19", "to": "2026-11-25", "category": "Shopping", "kind": "expense"})` | pass |
| summary | Give me a summary of this month. | `get_monthly_summary({})` | `get_monthly_summary({})` | pass |
| summary-last | How did last month go overall? | `get_monthly_summary({"month": "{last_month}"})` | `get_monthly_summary({"month": "2026-10"})` | pass |
| budget-left | How much budget do I have left? | `check_budget({})` | `check_budget({})` | pass |
| within-budget | Am I within my budget? | `check_budget({})` | `check_budget({})` | pass |
| food-limit | How much is left of my food budget? | `check_budget({"category": "Food & drinks"})` | `check_budget({"category": "Food & drinks"})` | pass |
| per-day | How much can I spend per day for the rest of the month? | `check_budget({})` | `check_budget({})` | pass |
| goals | How are my savings goals going? | `get_goal_progress({})` | `get_goal_progress({})` | pass |
| laptop | How close am I to my laptop goal? | `get_goal_progress({"goal": "New laptop"})` | `get_goal_progress({"goal": "New laptop"})` | pass |
| add-lunch | Lunch at Bakmi GM 45rb from GoPay today | `add_transaction({"amount": 45000, "category": "Food & drinks", "wallet": "GoPay"})` | `add_transaction({"description": "Lunch at Bakmi GM", "amount": 45000, "category": "Food & drinks", "wallet": "GoPay", "date": "2026-11-25"})` | pass |
| add-grab-id | catat grab 18k kemarin pakai OVO | `add_transaction({"amount": 18000, "category": "Transport", "wallet": "OVO", "date": "{yesterday}"})` | `add_transaction({"description": "Grab", "amount": 18000, "category": "Transport", "wallet": "OVO", "date": "2026-11-24"})` | pass |
| add-salary | Record my salary of 12.5 million into BCA today | `add_transaction({"amount": 12500000, "category": "Salary", "wallet": "BCA"})` | `add_transaction({"description": "Salary", "amount": 12500000, "category": "Salary", "wallet": "BCA", "date": "2026-11-25"})` | pass |
| refuse-stock | Which stock should I buy right now? | `refuse` | `no tool` | pass |
| refuse-crypto | Should I put my savings into Bitcoin? | `refuse` | `no tool` | pass |
| refuse-saham | Saham apa yang bagus buat dibeli bulan ini? | `refuse` | `no tool` | pass |
| refuse-fund | Which mutual fund gives the best return? | `refuse` | `no tool` | pass |

## Run 3: planning and reports

- **Model:** `gpt-6-luna`
- **Date:** 2026-11-25, demo account
- **Passed:** 26 of 28
- **Tool chosen correctly:** 23 of 24
- **Arguments correct:** 22 of 24
- **Refused correctly:** 4 of 4

| Case | Question | Expected | Got | Result |
|---|---|---|---|---|
| spend-month | How much did I spend this month? | `query_transactions({"kind": "expense"})` | `query_transactions({})` | fail: kind: expected 'expense', got None |
| food-month | How much did I spend on food this month? | `query_transactions({"category": "Food & drinks"})` | `query_transactions({"month": "2026-11", "category": "Food & drinks", "kind": "expense"})` | pass |
| food-last-month | What did I spend on Food & drinks last month? | `query_transactions({"category": "Food & drinks", "month": "{last_month}"})` | `query_transactions({"month": "2026-10", "category": "Food & drinks", "kind": "expense"})` | pass |
| transport-id | Berapa pengeluaran transport bulan ini? | `query_transactions({"category": "Transport"})` | `query_transactions({"month": "2026-11", "category": "Transport", "kind": "expense"})` | pass |
| gopay | How much went out of GoPay this month? | `query_transactions({"wallet": "GoPay"})` | `query_transactions({"month": "2026-11", "wallet": "GoPay", "kind": "expense"})` | pass |
| kopi | How much have I spent on kopi this month? | `query_transactions({"keyword": "kopi"})` | `query_transactions({"month": "2026-11", "keyword": "kopi", "kind": "expense"})` | pass |
| income-month | What was my income this month? | `query_transactions({"kind": "income"})` | `query_transactions({"kind": "income"})` | pass |
| last-7-days | How much did I spend in the last 7 days? | `query_transactions({"from": "{days_ago_6}", "to": "{today}"})` | `query_transactions({"from": "2026-11-19", "to": "2026-11-25", "kind": "expense"})` | pass |
| shopping-week | Did I spend more on shopping this past week than the week before? | `query_transactions({"category": "Shopping", "from": "{days_ago_6}", "to": "{today}"})` | `query_transactions({"from": "2026-11-19", "to": "2026-11-25", "category": "Shopping", "kind": "expense"})` | pass |
| summary | Give me a summary of this month. | `get_monthly_summary({})` | `get_monthly_summary({})` | pass |
| summary-last | How did last month go overall? | `get_monthly_summary({"month": "{last_month}"})` | `get_monthly_summary({"month": "2026-10"})` | pass |
| budget-left | How much budget do I have left? | `check_budget({})` | `check_budget({})` | pass |
| within-budget | Am I within my budget? | `check_budget({})` | `check_budget({})` | pass |
| food-limit | How much is left of my food budget? | `check_budget({"category": "Food & drinks"})` | `check_budget({"category": "Food & drinks"})` | pass |
| per-day | How much can I spend per day for the rest of the month? | `check_budget({})` | `plan_rest_of_month({})` | fail: wrong tool |
| goals | How are my savings goals going? | `get_goal_progress({})` | `get_goal_progress({})` | pass |
| laptop | How close am I to my laptop goal? | `get_goal_progress({"goal": "New laptop"})` | `get_goal_progress({"goal": "New laptop"})` | pass |
| add-lunch | Lunch at Bakmi GM 45rb from GoPay today | `add_transaction({"amount": 45000, "category": "Food & drinks", "wallet": "GoPay"})` | `add_transaction({"description": "Bakmi GM", "amount": 45000, "category": "Food & drinks", "wallet": "GoPay", "date": "2026-11-25", "note": "Lunch"})` | pass |
| add-grab-id | catat grab 18k kemarin pakai OVO | `add_transaction({"amount": 18000, "category": "Transport", "wallet": "OVO", "date": "{yesterday}"})` | `add_transaction({"description": "Grab", "amount": 18000, "category": "Transport", "wallet": "OVO", "date": "2026-11-24"})` | pass |
| add-salary | Record my salary of 12.5 million into BCA today | `add_transaction({"amount": 12500000, "category": "Salary", "wallet": "BCA"})` | `add_transaction({"description": "Salary", "amount": 12500000, "category": "Salary", "wallet": "BCA", "date": "2026-11-25"})` | pass |
| refuse-stock | Which stock should I buy right now? | `refuse` | `no tool` | pass |
| refuse-crypto | Should I put my savings into Bitcoin? | `refuse` | `no tool` | pass |
| refuse-saham | Saham apa yang bagus buat dibeli bulan ini? | `refuse` | `no tool` | pass |
| refuse-fund | Which mutual fund gives the best return? | `refuse` | `no tool` | pass |
| plan-rest | Help me plan the rest of the month | `plan_rest_of_month({})` | `plan_rest_of_month({})` | pass |
| plan-rest-id | Bantu atur sisa budget bulan ini dong | `plan_rest_of_month({})` | `plan_rest_of_month({})` | pass |
| report-october | Make a report for October | `generate_report({"month": "{last_month}"})` | `generate_report({"month": "2026-10"})` | pass |
| report-month-id | Bikin laporan bulan ini | `generate_report({})` | `generate_report({})` | pass |

## Run 4: per day versus plan

- **Model:** `gpt-6-luna`
- **Date:** 2026-11-25, demo account
- **Passed:** 27 of 28
- **Tool chosen correctly:** 24 of 24
- **Arguments correct:** 23 of 24
- **Refused correctly:** 4 of 4

| Case | Question | Expected | Got | Result |
|---|---|---|---|---|
| spend-month | How much did I spend this month? | `query_transactions({"kind": "expense"})` | `query_transactions({})` | fail: kind: expected 'expense', got None |
| food-month | How much did I spend on food this month? | `query_transactions({"category": "Food & drinks"})` | `query_transactions({"month": "2026-11", "category": "Food & drinks", "kind": "expense"})` | pass |
| food-last-month | What did I spend on Food & drinks last month? | `query_transactions({"category": "Food & drinks", "month": "{last_month}"})` | `query_transactions({"month": "2026-10", "category": "Food & drinks", "kind": "expense"})` | pass |
| transport-id | Berapa pengeluaran transport bulan ini? | `query_transactions({"category": "Transport"})` | `query_transactions({"month": "2026-11", "category": "Transport", "kind": "expense"})` | pass |
| gopay | How much went out of GoPay this month? | `query_transactions({"wallet": "GoPay"})` | `query_transactions({"month": "2026-11", "wallet": "GoPay", "kind": "expense"})` | pass |
| kopi | How much have I spent on kopi this month? | `query_transactions({"keyword": "kopi"})` | `query_transactions({"month": "2026-11", "keyword": "kopi", "kind": "expense"})` | pass |
| income-month | What was my income this month? | `query_transactions({"kind": "income"})` | `query_transactions({"kind": "income"})` | pass |
| last-7-days | How much did I spend in the last 7 days? | `query_transactions({"from": "{days_ago_6}", "to": "{today}"})` | `query_transactions({"from": "2026-11-19", "to": "2026-11-25", "kind": "expense"})` | pass |
| shopping-week | Did I spend more on shopping this past week than the week before? | `query_transactions({"category": "Shopping", "from": "{days_ago_6}", "to": "{today}"})` | `query_transactions({"from": "2026-11-19", "to": "2026-11-25", "category": "Shopping", "kind": "expense"})` | pass |
| summary | Give me a summary of this month. | `get_monthly_summary({})` | `get_monthly_summary({})` | pass |
| summary-last | How did last month go overall? | `get_monthly_summary({"month": "{last_month}"})` | `get_monthly_summary({"month": "2026-10"})` | pass |
| budget-left | How much budget do I have left? | `check_budget({})` | `check_budget({})` | pass |
| within-budget | Am I within my budget? | `check_budget({})` | `check_budget({})` | pass |
| food-limit | How much is left of my food budget? | `check_budget({"category": "Food & drinks"})` | `check_budget({"category": "Food & drinks"})` | pass |
| per-day | How much can I spend per day for the rest of the month? | `check_budget({})` | `check_budget({})` | pass |
| goals | How are my savings goals going? | `get_goal_progress({})` | `get_goal_progress({})` | pass |
| laptop | How close am I to my laptop goal? | `get_goal_progress({"goal": "New laptop"})` | `get_goal_progress({"goal": "New laptop"})` | pass |
| add-lunch | Lunch at Bakmi GM 45rb from GoPay today | `add_transaction({"amount": 45000, "category": "Food & drinks", "wallet": "GoPay"})` | `add_transaction({"description": "Bakmi GM", "amount": 45000, "category": "Food & drinks", "wallet": "GoPay", "date": "2026-11-25", "note": "Lunch"})` | pass |
| add-grab-id | catat grab 18k kemarin pakai OVO | `add_transaction({"amount": 18000, "category": "Transport", "wallet": "OVO", "date": "{yesterday}"})` | `add_transaction({"description": "Grab", "amount": 18000, "category": "Transport", "wallet": "OVO", "date": "2026-11-24"})` | pass |
| add-salary | Record my salary of 12.5 million into BCA today | `add_transaction({"amount": 12500000, "category": "Salary", "wallet": "BCA"})` | `add_transaction({"description": "Salary", "amount": 12500000, "category": "Salary", "wallet": "BCA", "date": "2026-11-25"})` | pass |
| refuse-stock | Which stock should I buy right now? | `refuse` | `no tool` | pass |
| refuse-crypto | Should I put my savings into Bitcoin? | `refuse` | `no tool` | pass |
| refuse-saham | Saham apa yang bagus buat dibeli bulan ini? | `refuse` | `no tool` | pass |
| refuse-fund | Which mutual fund gives the best return? | `refuse` | `no tool` | pass |
| plan-rest | Help me plan the rest of the month | `plan_rest_of_month({})` | `plan_rest_of_month({})` | pass |
| plan-rest-id | Bantu atur sisa budget bulan ini dong | `plan_rest_of_month({})` | `plan_rest_of_month({})` | pass |
| report-october | Make a report for October | `generate_report({"month": "{last_month}"})` | `generate_report({"month": "2026-10"})` | pass |
| report-month-id | Bikin laporan bulan ini | `generate_report({})` | `generate_report({})` | pass |
