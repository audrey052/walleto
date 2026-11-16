# Spec Delta

## Purpose

Gives every transaction and budget a label for what the money was for, with one consistent color and icon per label, starting from a shared set of defaults.

## ADDED Requirements

### Requirement: Default categories
Every user SHALL have the following categories available without creating them, each marked as expense or income and shown with a fixed color from the chart palette and an icon:
- Expense: Food & drinks, Shopping, Transport, Bills & utilities, Entertainment, Health, Others
- Income: Salary, Other income

#### Scenario: New user
- **WHEN** a user registers
- **THEN** the nine default categories are available to them, seven for expenses and two for income

#### Scenario: Expense categories in display order
- **WHEN** the expense categories are listed
- **THEN** they appear in the order Food & drinks, Shopping, Transport, Bills & utilities, Entertainment, Health, Others

### Requirement: Category visibility
A user SHALL see the default categories and the categories they created themselves, and never categories created by another user. Default categories SHALL NOT be changeable by users.

#### Scenario: Another user's category
- **WHEN** one user has a category named "Pets" and another user lists their categories
- **THEN** "Pets" is not in the second user's list

#### Scenario: Category names are unique per user and kind
- **WHEN** a user already has an expense category named "Pets" and another "pets" expense category is saved for them
- **THEN** the second one is rejected
