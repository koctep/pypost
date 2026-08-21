# PYPOST-1064: Test source item overrides distant active selection on collection export

## Programming language

Python

## Goals

When managing multiple collections in the application, a user may right-click on a specific collection (or an individual request inside it) to export it while a different collection is currently highlighted or active elsewhere in the collections tree.

From a business and data integrity perspective, it is critical that the export operation strictly targets the collection associated with the user's explicit action (the item clicked in the context menu) rather than the distant active selection. Exporting the wrong collection could lead to serious data leaks, sharing unintended or confidential requests, or exporting incorrect API collections.

While individual menu dispatch and export orchestration components exist, automated integration and unit test coverage is needed to guarantee end-to-end that an explicit source target takes complete precedence over any distant tree selection during single-collection export, ensuring the correct collection is always serialized and saved.

## User Stories

- As a **user** managing multiple collections, I want exporting a collection from its context menu to export that specific collection even when another collection is active in the tree, so that I never accidentally export or share the wrong data.
- As a **user**, I want exporting a request via its context menu to export its parent collection even if a different collection is currently active elsewhere, so that the context menu always operates on the item under my pointer.
- As a **maintainer**, I want automated integration and unit tests that verify explicit source targeting takes precedence over tree selection during collection export, so that regressions in export target resolution are immediately caught in CI.

## Definition of Done

- [ ] Automated tests verify that when export is triggered with an explicit target collection, the serialization and saved export file contain that target collection even when a different collection is currently selected/active in the tree.
- [ ] Automated tests verify that when export is triggered with an explicit target request row, the serialization and saved export file contain the target request's parent collection even when a different collection is currently selected/active in the tree.
- [ ] Automated tests verify that when export is triggered without an explicit target (e.g., via the below-tree action button), export continues to resolve and export the currently selected collection as expected.
- [ ] All new and touched test suites enforce explicit test timeout markers per testing standards.
- [ ] All tests execute deterministically with zero side effects or leaks across test cases.

## Task Description

**Problem:** In PYPOST-1013, context-menu export was introduced to allow users to export collections directly from the item's context menu. Dispatch tests verified that the menu passes the clicked item index to the export handler. However, an end-to-end verification gap remains: ensuring that when a specific source item is provided, the export serialization and file writing target that specific item and completely override any distant active selection in the tree.

**Goal:** Establish comprehensive integration and unit test coverage in the test suite demonstrating that explicit source item export overrides distant active tree selection across single-collection export flows.

### Scope (in)

- Unit and integration tests verifying export targeting when active tree selection differs from explicit source target:
  - Scenario 1: Active selection on Collection A, export target on Collection B -> Export serializes and saves Collection B.
  - Scenario 2: Active selection on Collection A, export target on Request inside Collection B -> Export serializes and saves Collection B.
  - Scenario 3: Active selection on Collection A, export invoked with no explicit source target -> Export serializes and saves Collection A.
- Verification that serialization and file write receive the correct collection data payload and filename suggestions.
- Strict adherence to test timeout markers and PySide/Qt test fixture conventions.

### Scope (out)

- Altering the business logic or format of collection export.
- Export-all functionality (PYPOST-1012).
- Import functionality or changes to other tree context menu actions (rename, delete).
- UI redesign or layout modifications.

## Assumptions

- Single-collection export and multi-collection tree structures are fully functional.
- The UI presentation and export actions support passing an explicit source item or falling back to the active selection.
- Test suites can mock filesystem and dialog interactions while exercising real tree model resolution and export action orchestration.

## Main Entities and Interactions

- **Collection**: A named grouping of API requests within the sidebar tree.
- **Request**: An individual API request item belonging to a parent collection.
- **Active Selection**: The currently highlighted or focused item in the collections tree.
- **Target Item / Source Target**: The specific collection or request row targeted by a user action (such as a context-menu click).
- **Export Action**: The operation that serializes the resolved collection and saves it to a JSON file.
- **Export File**: The resulting JSON document containing the serialized collection data.

**Interaction Flow:**
1. A tree contains multiple collections (e.g., Collection A and Collection B).
2. Collection A is selected as the active tree item.
3. An export operation is initiated targeting Collection B (or a request within Collection B).
4. The system resolves the export target to Collection B, ignoring the active selection on Collection A.
5. Collection B is serialized and written to the export destination.

## Non-Functional Requirements

- **Correctness & Data Integrity:** Export target resolution must be 100% deterministic and never default to active selection when a source target is provided.
- **Test Execution & Performance:** Tests must run quickly within standard CI limits and declare explicit test timeouts.
- **Isolation:** Tests must not leave temporary files or mutate global state across test runs.

## Q&A

**Q:** Why is this test necessary if menu dispatch tests already exist?  
**A:** Menu dispatch tests only verify that the clicked index is forwarded to the export callback. They do not verify that the export orchestration actually uses that index to resolve the collection and serialize/save the correct data rather than falling back to the tree's current selection. This test closes that gap.

**Q:** What scenarios should be covered?  
**A:** The primary scenario is having two collections (A and B) in the tree, setting active selection to A, initiating export on B, and asserting that B (and only B) is serialized and written. Related scenarios include targeting a child request of B while A is selected, and verifying fallback to A when no explicit target is supplied.

**Q:** Does this task modify production behavior?  
**A:** No production behavior changes are planned unless test development uncovers a bug or regression in existing target resolution logic.
