# period-picker Specification

## Purpose
The control at the top of Home and Transactions that picks which days a page covers: a whole calendar month, or any range of days up to today.

## Requirements

### Requirement: Period in the address
The selected period SHALL be part of the address. A whole calendar month SHALL use `?month=YYYY-MM`. Any other range SHALL use `?from=YYYY-MM-DD&to=YYYY-MM-DD`, with both dates included. Without a period in the address, the page SHALL show the current month.

#### Scenario: Old month link
- **WHEN** a user opens a link ending in `?month=2026-10`
- **THEN** the page covers 1 to 31 October 2026

#### Scenario: Range link
- **WHEN** a user opens a link ending in `?from=2026-11-10&to=2026-11-24`
- **THEN** the page covers 10 to 24 November 2026, both days included

#### Scenario: A range that is a whole month
- **WHEN** a user picks 1 to 30 November 2026 in the calendar
- **THEN** the address uses `?month=2026-11`

### Requirement: Valid periods
A period SHALL NOT include days after today; an end date after today SHALL become today. A start date after the end date SHALL be swapped with it. A range longer than 92 days SHALL be shortened to 92 days from its start. Dates that cannot be read SHALL fall back to the current month.

#### Scenario: Future end date
- **WHEN** today is 24 November 2026 and the address asks for 10 November to 10 December
- **THEN** the page covers 10 to 24 November

#### Scenario: Reversed range
- **WHEN** the address asks for 24 November to 10 November
- **THEN** the page covers 10 to 24 November

#### Scenario: Too long
- **WHEN** the address asks for 1 January to 24 November 2026
- **THEN** the page covers 92 days starting 1 January 2026

#### Scenario: Unreadable dates
- **WHEN** the address asks for `?from=yesterday`
- **THEN** the page shows the current month

### Requirement: Period label
The picker SHALL name the period: a whole month as "November 2026"; another range as "10 Nov – 24 Nov 2026"; and a range across two years as "28 Dec 2025 – 3 Jan 2026". A single day SHALL read "24 Nov 2026".

#### Scenario: Range label
- **WHEN** the period is 10 to 24 November 2026
- **THEN** the picker reads "10 Nov – 24 Nov 2026"

### Requirement: Range calendar
Choosing the picker's calendar button SHALL open a popover with a calendar of the period's month, which can move to earlier months and up to the current month. The first chosen day SHALL be the start and the second the end, with the days between highlighted. Days after today SHALL NOT be selectable. Choosing the end day SHALL apply the period and close the popover; Escape or a click outside SHALL close it without a change.

#### Scenario: Pick a range
- **WHEN** a user opens the popover, chooses 10 November and then 24 November
- **THEN** the page shows 10 to 24 November and the address ends with `?from=2026-11-10&to=2026-11-24`

#### Scenario: Future days
- **WHEN** the popover shows November 2026 and today is 24 November
- **THEN** 25 to 30 November cannot be chosen and there is no later month

### Requirement: Month arrows
On Home, previous and next arrows SHALL move by whole calendar month; the Transactions filter bar SHALL offer only the calendar, without arrows. From a whole month they SHALL move to the month before or after it. From another range, previous SHALL open the month before the range's start month and next SHALL open the month after the range's end month. There SHALL be no next arrow when that month starts after today.

#### Scenario: Previous from a range
- **WHEN** the period is 10 to 24 November and the user chooses the previous arrow
- **THEN** the page shows October 2026

#### Scenario: Next from a range in an earlier month
- **WHEN** the period is 5 to 12 October 2026 and today is 24 November
- **THEN** the next arrow opens November 2026

### Requirement: Changing the period without a reload
Choosing an arrow or a range SHALL replace the page content without a full page reload and SHALL update the address. Without JavaScript, the popover SHALL offer "From" and "To" date fields and an "Apply" button that load the page for that range, and the arrows SHALL be ordinary links.

#### Scenario: Without JavaScript
- **WHEN** JavaScript is off and a user enters 10 November and 24 November and chooses Apply
- **THEN** the page loads for 10 to 24 November
