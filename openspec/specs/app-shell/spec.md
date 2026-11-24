# app-shell Specification

## Purpose
Defines the shared frame around every signed-in page (navigation, topbar, profile menu, messages) so that all Walleto sections look and behave the same on desktop and mobile.

## Requirements

### Requirement: Sidebar navigation
Every signed-in page SHALL show a sidebar with the Walleto logo and six sections in this order: Home, Transactions, Wallets, Budget, Savings goals, Assistant. The section of the current page SHALL be visibly marked as active.

#### Scenario: Navigate between sections
- **WHEN** a signed-in user selects "Wallets" in the sidebar
- **THEN** the Wallets page is shown and "Wallets" is marked as the active section

#### Scenario: Only one active section
- **WHEN** any section page is shown
- **THEN** exactly one sidebar item is marked active

### Requirement: Collapsible sidebar
The user SHALL be able to collapse the sidebar to icons only and expand it again with a round handle on the sidebar's right edge, which appears while the pointer is over the sidebar or the handle has keyboard focus, and is always shown on touch screens. The chosen state SHALL be kept when moving to another page in the same browser.

#### Scenario: Collapse persists across pages
- **WHEN** the user collapses the sidebar and then opens another section
- **THEN** the sidebar is still collapsed, and each icon shows its section name on hover

### Requirement: Topbar
On screens 768 pixels and wider there SHALL be no top bar; the page title SHALL be the first thing in the content area. On narrower screens a top bar SHALL show the logo and the account menu. Neither SHALL show a breadcrumb or today's date. "Today" for every page SHALL be the date in the Asia/Jakarta time zone.

#### Scenario: Today follows Jakarta time
- **WHEN** a page is opened at 23:30 UTC on 14 November 2026
- **THEN** the app treats 15 November 2026 as today

#### Scenario: Desktop has no top bar
- **WHEN** a signed-in page is shown 1440 pixels wide
- **THEN** there is no top bar and no date, and the page title is level with the logo in the sidebar

### Requirement: Profile menu
The bottom of the sidebar SHALL show the user's initials, full name and email. Opening it SHALL show a menu with a "Sign out" action.

#### Scenario: Profile shows the signed-in user
- **WHEN** a user named "Aditya Ramadhan" is signed in
- **THEN** the sidebar shows "AR", "Aditya Ramadhan" and that user's email

### Requirement: Placeholder section pages
Until a section's feature is built, its page SHALL exist, carry the section title and subtitle from docs/STYLE.md, and show an empty state saying the section is coming soon. The home address SHALL show the Home page.

#### Scenario: Unbuilt section
- **WHEN** a signed-in user opens Savings goals before that feature exists
- **THEN** the page shows the title "Savings goals", its subtitle, and a "coming soon" empty state instead of an error

### Requirement: Toast messages
After an action that changes something (for example signing in or registering), the next page SHALL show a short confirmation toast. A toast SHALL close by itself after about four seconds and SHALL also be closable by the user.

#### Scenario: Toast after registration
- **WHEN** a user finishes registration
- **THEN** the home page shows a toast confirming the account was created, and it disappears after about four seconds

### Requirement: Mobile layout
On screens narrower than 768 pixels the sidebar SHALL be replaced by a bottom navigation bar that gives access to all six sections, and no page SHALL scroll horizontally.

#### Scenario: Phone-width screen
- **WHEN** a signed-in page is shown at 390 pixels wide
- **THEN** the sidebar is hidden, a bottom navigation is shown, and the page fits the screen width

### Requirement: Development style guide
The system SHALL provide a style guide page that shows every shared component with sample content. The page SHALL be available only when the application runs in development mode.

#### Scenario: Style guide in development
- **WHEN** a developer opens the style guide address while running in development mode
- **THEN** buttons, inputs, panel, category chips, progress bars, modal, empty state and toast are all shown

#### Scenario: Style guide in production
- **WHEN** anyone opens the style guide address while running in production mode
- **THEN** a "page not found" response is returned
