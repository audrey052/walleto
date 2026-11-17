# Spec Delta

## ADDED Requirements

### Requirement: Demo budgets
The demo data SHALL include category limits for each of its three months, so the Budget page has content as soon as a visitor opens it. In the current month, at least one category SHALL be in warning or over. Resetting the demo data SHALL replace the demo plans and leave other users' plans untouched.

#### Scenario: Plans for every demo month
- **WHEN** the demo data is created on 17 November 2026
- **THEN** the demo user has a plan for September, October and November 2026

#### Scenario: Something to notice
- **WHEN** a visitor opens the Budget page in the demo account
- **THEN** at least one category in the current month shows the warning or over status

#### Scenario: Reset keeps others' plans
- **WHEN** the demo data is reset
- **THEN** other users' plans are unchanged
