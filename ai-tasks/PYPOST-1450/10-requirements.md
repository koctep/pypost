# PYPOST-1450: Dedicated Discovery Status UI Separate from Fetch Loading Chrome

## Goals

When opening the Import Collection Variables dialog, PyPost allows users to import variables from both local workspace collections and remote library collections. Enumerating remote library catalogs (discovery) runs asynchronously in the background so the dialog opens immediately.

Currently, this background discovery process shares the same loading and error UI elements as the active collection-fetch operation. This creates conflicting state machines:
- The progress label, cancel button, error banner, and retry button are toggled by two distinct asynchronous operations.
- User interactions (such as cancelling or retrying) cannot cleanly differentiate between cancelling/retrying remote catalog discovery versus cancelling/retrying an individual collection fetch.
- Discovery state can visually block or interfere with inspecting and importing local workspace collections.

The goal of this task is to establish a dedicated, non-blocking discovery status UI element completely separate from the collection-fetch loading chrome. This guarantees predictable, independent user experiences for background catalog discovery and user-driven collection loading.

## User Stories

1. **Independent Discovery Visibility**: As a user opening the Import Collection Variables dialog, I want to see a dedicated, non-blocking discovery status indicator when remote catalogs are being searched, so that I clearly understand remote sources are being discovered without confusing this with loading a specific collection.
2. **Uninterrupted Workspace Collection Use**: As a user with local workspace collections, I want to select and import variables from workspace collections while catalog discovery is still in progress, without discovery loading indicators obscuring my view or disabling dialog actions.
3. **Dedicated Discovery Error & Retry**: As a user whose remote library discovery encounters a network failure or error, I want a dedicated error notification and retry option for discovery that does not overwrite collection-fetch error messages or prevent me from working with local collections.
4. **Unambiguous Cancellation & State Management**: As a user fetching a remote collection while discovery is running or retrying, I want separate cancel controls for discovery and collection fetching so that cancelling one never inadvertently cancels or resets the other.

## Definition of Done

- **Dedicated Discovery UI**: A distinct discovery status element (e.g., status strip/banner) exists exclusively for catalog discovery feedback.
- **Isolated State Machines**:
  - The collection-fetch loading chrome (loading indicator and cancel control) is used exclusively for fetching selected collection contents and is never manipulated by catalog discovery.
  - The collection-fetch error chrome (error banner and retry control) is used exclusively for collection fetch failures.
  - The discovery status element manages its own states (in-progress, failed, dismissed/hidden) independently.
- **Non-Blocking Operation**:
  - Background discovery does not disable workspace collection selection, variable table interaction, or variable importing.
  - Discovery failure displays within the dedicated discovery status element and allows rediscovery retry without disrupting workspace collection workflows.
- **Verification**:
  - Automated tests verify that discovery progress, errors, and cancellation operate independently from collection-fetch loading and error states.
  - Regression tests verify that existing variable import, preset switching, and collection-fetch workflows continue to operate as expected.

## Task Description

In the Import Collection Variables dialog, background discovery searches configured library connections for remote collections. Previously, discovery reused the collection-fetch loading indicator, cancel button, error container, and retry button.

This task separates the discovery user feedback into a dedicated, non-blocking discovery status UI.

### Scope and Boundaries
- **In Scope**:
  - Providing a dedicated discovery status UI element in the Import Collection Variables dialog.
  - Separating the status lifecycle, cancel action, error display, and retry action of catalog discovery from collection-fetch loading chrome.
  - Ensuring the UI remains responsive and non-blocking for local workspace collections during discovery.
- **Out of Scope**:
  - Modifying the underlying protocol or network transport for library connections.
  - Modifying how variable table conflict resolution or preset selection functions once a collection is loaded.

### Constraints & Assumptions
- The implementation language is Python.
- Existing visual hierarchy and layout ergonomics of the dialog must be preserved.
- Discovery UI must cleanly collapse or hide when discovery completes successfully or when no remote libraries are configured.

## Q&A

- **Q: Why does discovery need its own status UI instead of sharing the existing loading bar?**
  **A:** Catalog discovery is an ambient background scan to find available sources, whereas collection loading is a direct user-requested action on a chosen collection. Sharing UI controls creates state collisions, ambiguous button actions (e.g. which operation is being cancelled or retried), and false blocking indications.
- **Q: How should discovery failure affect the dialog?**
  **A:** Discovery failure should inform the user that some remote collections could not be found and offer a retry option in the discovery strip. It must not block the user from working with local workspace collections or previously discovered collections.
- **Q: What programming language is used for implementation?**
  **A:** Python.
