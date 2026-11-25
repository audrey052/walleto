# Spec Delta

## ADDED Requirements

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
