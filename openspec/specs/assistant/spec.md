# assistant Specification

## Purpose
Lets a signed-in user ask about their own money in plain language and get answers built only from figures the app computes, and record a transaction from the chat after confirming it.

## Requirements

### Requirement: Assistant page
The Assistant page SHALL show the section title and subtitle, the latest conversation, a message input at the bottom While the conversation is empty, it SHALL offer three numbered suggestions that send their text as a question when chosen. A "New chat" action SHALL start an empty conversation.

#### Scenario: Empty conversation
- **WHEN** a user opens the Assistant for the first time
- **THEN** the page shows the three suggestions and the input, and no "Coming soon" state

#### Scenario: Suggestion
- **WHEN** the user chooses "How much did I spend this month?"
- **THEN** that text appears as the user's message and an answer follows

### Requirement: Conversation history
Each question and answer SHALL be stored, so that reloading the page shows the same conversation. Starting a new chat SHALL keep the old conversation. A "History" list SHALL show the user's earlier conversations, newest activity first, each titled by its first question, and choosing one SHALL open it so the user can read and continue it. Sending a question SHALL add the question and the answer to the page without a full page reload.

#### Scenario: Reload
- **WHEN** a user asks a question, gets an answer and reloads the page
- **THEN** both messages are still shown in order

#### Scenario: Reopen an earlier conversation
- **WHEN** a user asked "How much on food?", started a new chat, and then chooses that question in History
- **THEN** that conversation is shown, and a new question is added to it

### Requirement: Answers come from tools
Every figure in an answer SHALL come from a tool result computed by the app, and SHALL equal what the Home, Transactions, Budget and Savings goals pages show for the same data.

#### Scenario: Spending in a category
- **WHEN** November has Food & drinks expenses of Rp1.405.500 and the user asks "How much did I spend on food this month?"
- **THEN** the answer states Rp1.405.500, the same figure the Transactions page shows for November filtered to Food & drinks

#### Scenario: Budget question
- **WHEN** November's plan is Rp7.700.000 and its expenses are Rp5.808.490, and the user asks "How much budget do I have left?"
- **THEN** the answer states Rp1.891.510

### Requirement: What the assistant can look up
The assistant SHALL be able to look up: transactions for a period (optionally by category, wallet, keyword or kind) with their total, count and the change against the previous period of the same length; a month's summary; a month's budget or one category's limit, spent, remaining and amount per day; and one savings goal or all active goals with saved, target, to go, status and monthly amount.

#### Scenario: Compared with the previous period
- **WHEN** the user asks "Did I spend more on transport in the last two weeks than before?"
- **THEN** the answer gives both totals and the change, all from one tool result

#### Scenario: Goal progress
- **WHEN** the user asks "How is my laptop goal going?"
- **THEN** the answer gives the saved amount, the target, the amount to go and its status, as the Savings goals page does

### Requirement: Data cards
An answer that used a tool SHALL show the figures in a card built by the app from the tool result, next to the text. An answer based on transactions SHALL end with the line "Calculated from N transactions", where N is the number of transactions the tool counted.

#### Scenario: Card and count
- **WHEN** the answer about Food & drinks used 23 transactions
- **THEN** a card shows Rp1.405.500 and the answer ends with "Calculated from 23 transactions"

### Requirement: Record a transaction after confirming
When the user asks to record a transaction, the assistant SHALL show a confirmation card with its description, amount, category, wallet and date, choosing only from the user's own active wallets and categories and checked with the same rules as the Transactions form. Nothing SHALL be saved until the user chooses "Save"; then the transaction SHALL be saved as recorded by AI. "Cancel" SHALL discard it.

#### Scenario: Confirm and save
- **WHEN** the user writes "Lunch at Bakmi GM 45rb from GoPay today" and chooses Save on the card
- **THEN** a Food & drinks expense of Rp45.000 from GoPay dated today exists, marked as recorded by AI, and the card shows it was saved

#### Scenario: Nothing saved before confirming
- **WHEN** the confirmation card is shown and the user leaves the page
- **THEN** no transaction was saved

#### Scenario: Invalid draft
- **WHEN** the requested wallet does not exist or the amount is not a positive whole number of Rupiah
- **THEN** no card offers Save, and the answer says what is missing

### Requirement: A confirmation card is used once
A confirmation card that has been saved or cancelled SHALL show that state and SHALL NOT save again, also after a reload or a second request.

#### Scenario: Double save
- **WHEN** the user chooses Save twice on the same card
- **THEN** exactly one transaction is saved

### Requirement: Refusals
The assistant SHALL decline to recommend specific investments, stocks or other securities, and SHALL say that it only answers from the data the user has recorded. It SHALL NOT invent figures when a tool returns nothing; it SHALL say there is no data instead.

#### Scenario: Stock tip
- **WHEN** the user asks "Which stock should I buy?"
- **THEN** the assistant declines and no tool is called

#### Scenario: No data
- **WHEN** the user asks about spending in a month with no transactions
- **THEN** the answer says there are no transactions for that period and states no amount

### Requirement: Usage limits
A question SHALL use at most 4 rounds of tool calls before an answer is given. A user SHALL be able to ask at most 30 questions per day (Asia/Jakarta). When the daily limit is reached, the input SHALL say so and no question SHALL be sent to the model until the next day.

#### Scenario: Daily limit
- **WHEN** a user has asked 30 questions today and asks another
- **THEN** the page says the daily limit is reached and the question is not answered

### Requirement: Not set up and failures
When the assistant has no API key or model configured, the page SHALL say that the assistant is not set up, and the input SHALL be disabled. When the model cannot be reached or fails, the user SHALL see "The assistant couldn't answer right now. Try again." and the question SHALL NOT count toward the daily limit.

#### Scenario: Missing configuration
- **WHEN** no API key is configured
- **THEN** the page says the assistant is not set up yet and offers no input

#### Scenario: Timeout
- **WHEN** the model does not answer in time
- **THEN** the error message is shown and the user can ask again

### Requirement: Assistant is private
Conversations, tool results and confirmation cards SHALL only ever cover the signed-in user's own data. A user SHALL NOT be able to read or continue another user's conversation or save another user's confirmation card, including by changing an ID in the address.

#### Scenario: Another user's card
- **WHEN** a user sends Save for a confirmation card that belongs to another user
- **THEN** the response is "not found" and no transaction is saved

#### Scenario: Another user's data
- **WHEN** another user has Rp9.000.000 of Food & drinks expenses in November and the signed-in user asks about food spending in November
- **THEN** the answer covers only the signed-in user's transactions

### Requirement: Rest-of-month plan facts
When asked to plan the rest of the month, the assistant SHALL use facts computed by the app for the current month: the plan total, what is left of the category limits (their limits minus their spending), the days left including today, and for each limited expense category its limit, spent, what is left and its average daily spending so far. Without a plan, or with nothing left of the limits, it SHALL say so and point to the Budget page instead of showing a plan card.

#### Scenario: Facts
- **WHEN** on 25 November the plan is Rp7.700.000 with Food & drinks Rp1.405.500 spent of Rp1.600.000
- **THEN** the facts list Food & drinks with Rp194.500 left and 6 days left

#### Scenario: No plan
- **WHEN** the current month has no category limits
- **THEN** the answer says there is no monthly plan yet and links to Budget, and no plan card is shown

### Requirement: Plan proposals are checked
A plan proposed by the assistant SHALL only be shown as a plan card when it gives an amount for each limited expense category of the user, every amount is a whole, non-negative number of Rupiah, the amounts add up exactly to what is left of the limits, and every resulting limit (spent plus amount) is at least Rp1.000. Otherwise the assistant SHALL be told what is wrong and no card SHALL be shown.

#### Scenario: Amounts do not add up
- **WHEN** Rp1.000.000 is left and the proposal adds up to Rp1.200.000
- **THEN** no plan card is shown and the assistant is told the amounts must add up to Rp1.000.000

#### Scenario: Unknown category
- **WHEN** the proposal names a category the user has no limit for
- **THEN** no plan card is shown

### Requirement: Plan card and Apply to Budget
A plan card SHALL list each limited category with what is left now, the suggested amount and the amount per day, and SHALL offer "Edit" and "Apply to Budget". "Apply to Budget" SHALL check the amounts again with the same rules and set each category's limit for the current month to its spending plus the amount, so the monthly plan total does not change. Nothing SHALL change before Apply.

#### Scenario: Apply
- **WHEN** a user chooses Apply to Budget on a card suggesting Food & drinks Rp150.000 and Transport Rp44.500
- **THEN** November's Food & drinks limit becomes its spending plus Rp150.000, Transport's its spending plus Rp44.500, and the plan total on Budget is unchanged

#### Scenario: Edited amounts that do not add up
- **WHEN** the user edits the amounts so they add up to more than what is left and chooses Apply
- **THEN** no limit changes and the card says by how much the amounts are off

### Requirement: Editing a plan card
"Edit" SHALL let the user change the amounts in the card before applying, and the card SHALL show whether they still add up to what is left of the limits.

#### Scenario: Live total
- **WHEN** the user raises one amount by Rp50.000 in Edit
- **THEN** the card shows the amounts are Rp50.000 over what is left

### Requirement: A plan card is applied once
A plan card that has been applied SHALL show that it was applied and SHALL NOT apply again. A card for a month that is no longer the current month SHALL NOT be applied.

#### Scenario: Applied twice
- **WHEN** the user chooses Apply to Budget twice on the same card
- **THEN** the limits change once

#### Scenario: Month has passed
- **WHEN** a November card is applied on 1 December
- **THEN** no limit changes and the card says the month has ended

### Requirement: Monthly report
When asked for a monthly report, the assistant SHALL show a file card with a "Download PDF" action for that month. The one-page PDF SHALL show the month's income, expenses, plan and remaining; a table of expense categories with spent, limit and percent used; the 10 largest expenses; the progress of active savings goals; and one short summary paragraph. Every figure SHALL be computed by the app and SHALL match the Home, Budget and Savings goals pages for that month.

#### Scenario: Report for a month
- **WHEN** a user asks "Make a report for October"
- **THEN** a file card for October 2026 appears, and its PDF shows October's income, expenses and category table, with the same numbers as Home and Budget for October

#### Scenario: Future month
- **WHEN** a user asks for a report of a month that has not started
- **THEN** no file card is shown and the answer says there is no data yet

### Requirement: Report summary uses only the figures
The report's summary paragraph SHALL be written by the model from the report's figures only. If it mentions an amount or percent that is not among the figures, the app SHALL replace it with a short summary written by code.

#### Scenario: Invented number
- **WHEN** the model's summary mentions Rp999.999, which is not in the figures
- **THEN** the PDF uses the code-written summary instead

### Requirement: Planning suggestion
While the conversation is empty, the suggestions SHALL include "Help me plan the rest of the month".

#### Scenario: Suggestion shown
- **WHEN** a user opens an empty conversation
- **THEN** "Help me plan the rest of the month" is one of the suggestions

### Requirement: Plans and reports are private
A user SHALL NOT be able to apply another user's plan card or download another user's report, including by changing an ID in the address.

#### Scenario: Another user's report
- **WHEN** a user opens the download address of another user's report
- **THEN** the response is "not found"

#### Scenario: Another user's plan
- **WHEN** a user sends Apply for another user's plan card
- **THEN** the response is "not found" and no limit changes
