# Spec Delta

## ADDED Requirements

### Requirement: Demo savings goals
The demo data SHALL include at least two active savings goals with deadlines and deposits from the demo wallets spread over its three months, so the Savings goals page has content as soon as a visitor opens it. One goal SHALL be on track and one behind. Every demo wallet SHALL still end with a balance of zero or more. Resetting the demo data SHALL replace the demo goals and leave other users' goals untouched.

#### Scenario: Goals with history
- **WHEN** the demo data is created on 18 November 2026
- **THEN** the demo user has at least two active goals, each with deposits dated between 1 September and 18 November 2026

#### Scenario: Something to notice
- **WHEN** a visitor opens Savings goals in the demo account
- **THEN** at least one goal shows "On track" and at least one shows "Behind"

#### Scenario: Reset keeps others' goals
- **WHEN** the demo data is reset
- **THEN** other users' goals and their deposits are unchanged
