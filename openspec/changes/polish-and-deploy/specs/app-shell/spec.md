# Spec Delta

## ADDED Requirements

### Requirement: Error pages
A missing page SHALL show "Page not found", a server error SHALL show "Something went wrong", and a rejected form SHALL show "This form has expired". A form is rejected when its security token is missing or stale. Each page SHALL use Walleto's logo and style, give one sentence of explanation and offer a link back to Home. None of them SHALL show technical details. The server error page SHALL render even when the database is unavailable.

#### Scenario: Unknown address
- **WHEN** a visitor opens an address that does not exist
- **THEN** they see "Page not found" with status 404 and a link to Home

#### Scenario: Another user's item
- **WHEN** a signed-in user opens the address of another user's transaction or goal
- **THEN** they see the same "Page not found" page, which does not reveal that the item exists

#### Scenario: Server error
- **WHEN** an unexpected error happens while a page is built
- **THEN** the visitor sees "Something went wrong" with status 500 and no error details

#### Scenario: Stale form
- **WHEN** a visitor submits a form whose security token has expired
- **THEN** they see "This form has expired" with a suggestion to go back and try again

### Requirement: Failed requests in place
When an action that updates part of a page fails, the page SHALL stay as it was and show an error toast. Examples are saving in a modal, filtering a list, or asking the assistant. A server error SHALL show "Something went wrong. Try again." A lost connection SHALL show "You're offline. Check your connection and try again." Every action SHALL have a form fallback that works without JavaScript.

#### Scenario: Server error while saving
- **WHEN** saving a transaction in the modal fails on the server
- **THEN** the modal stays open with what the user typed, and a toast says "Something went wrong. Try again."

#### Scenario: Offline
- **WHEN** the connection is lost and the user changes a filter on Transactions
- **THEN** a toast says "You're offline. Check your connection and try again." and the list is unchanged

### Requirement: Expired session during an action
If the session has ended and the user starts an action that updates part of the page, they SHALL go to the sign-in page as a full page. The sign-in form SHALL NOT appear inside a modal, card or list. After signing in, they SHALL return to the page they were on.

#### Scenario: Signed out in another tab
- **WHEN** the user signs out in another tab and then changes a filter on Transactions
- **THEN** the browser goes to the sign-in page, and after signing in it opens Transactions again

### Requirement: Loading indicator
While an action that updates part of the page is in progress, the control that started it SHALL be disabled. If the action takes longer than a short moment, a thin bar at the top of the screen SHALL show that work is in progress. The bar SHALL disappear when the action finishes or fails.

#### Scenario: Slow filter
- **WHEN** the user changes the wallet filter and the response takes a second
- **THEN** a thin bar appears at the top of the screen until the list updates

#### Scenario: Fast action
- **WHEN** an action finishes almost at once
- **THEN** no bar flashes on the screen
