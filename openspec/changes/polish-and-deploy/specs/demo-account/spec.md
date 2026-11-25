# Spec Delta

## ADDED Requirements

### Requirement: Demo data is created once
On a server, the demo data SHALL be created the first time someone chooses "Try demo account", or when the developer runs the demo command. It SHALL NOT be reset automatically. Changes made by demo visitors SHALL stay until the developer runs the demo command again.

#### Scenario: First visitor on a new server
- **WHEN** the first visitor on a freshly deployed site chooses "Try demo account"
- **THEN** the demo data is created for the three months up to that day and the visitor is signed in

#### Scenario: Later visitors
- **WHEN** a later visitor chooses "Try demo account"
- **THEN** they see the existing demo data, including earlier visitors' changes, and nothing is recreated
