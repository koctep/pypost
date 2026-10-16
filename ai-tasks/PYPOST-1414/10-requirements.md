# PYPOST-1414: Per-variable conflict strategy and side-by-side diff inspector in collection variable import

## Goals

When synchronizing collection-scoped variables into active workspace environments in PyPost, users frequently encounter variable name collisions where a variable declared in the collection already exists in the target environment.

While previous iterations introduced an import dialog with global conflict resolution ("Skip existing" vs. "Overwrite existing"), this all-or-nothing approach introduced critical business and operational challenges:
1. **Lack of Granular Control (All-or-Nothing Dilemma)**: In real-world API workflows, environments often contain a mix of variables. Users frequently need to overwrite specific outdated base URLs or configuration keys from the collection while preserving customized local values (such as locally overridden ports, personal API tokens, or custom session credentials). Under a global policy, users are forced to choose between overwriting all collisions (risking data loss) or skipping all collisions (failing to update desired keys), unless they manually uncheck rows or re-edit variables after the import.
2. **Blind Overwrite Risk**: In the previous interface, users were shown only the candidate incoming value from the collection. They could not see what value currently resided in their target environment for colliding keys. Deciding whether to overwrite required users to cancel the dialog, inspect their environment variables table, memorize or copy existing values, and re-open the dialog.
3. **Sensitive Credential Exposure Risks**: Variables in environments and collections may contain sensitive secrets (e.g., authentication tokens, client secrets, private keys). When previewing or comparing values, sensitive credentials must remain masked to prevent visual leaks to unauthorized onlookers, screen shares, or video recordings.
4. **Efficiency in Large Imports**: When importing large collections containing dozens of variables with multiple collisions, manually configuring conflict resolution row-by-row would be tedious without bulk controls to quickly set strategies across all colliding rows.

The business goal of this task is to empower users with an informed, granular, and safe variable import process. Users will be able to inspect current environment values side-by-side against candidate collection values for colliding variables, selectively choose the conflict resolution strategy (Keep Current vs. Overwrite) on a per-variable basis, apply bulk conflict strategy presets, and safely review changes while maintaining secret confidentiality.

## Implementation Language

- **Implementation language**: Python

## User Stories

- As an **API developer**, I want to see my existing environment value side-by-side with the candidate collection value for any colliding variable, so that I can immediately understand what will change before deciding whether to import or overwrite it.
- As a **team member collaborating on shared collections**, I want to choose a conflict strategy on a per-variable basis (Keep Current vs. Overwrite), so that I can adopt updated endpoint URLs from the collection without wiping out my custom local test credentials.
- As a **security-conscious engineer**, I want secret values in the side-by-side comparison to be masked by default, so that sensitive tokens are never exposed in plaintext during a screen share or team review.
- As an **operator importing large collections**, I want bulk action controls to set the conflict strategy for all colliding rows at once (e.g., "Keep All Current" or "Overwrite All"), so that I can quickly configure a baseline strategy and only fine-tune the specific variables I care about.
- As an **environment administrator**, I want the import preview summary to dynamically reflect both additions and granular overwrites/preservations, so that I have complete confidence in the final state of my environment before confirming the import.

## Definition of Done

This task is considered complete when:
1. When inspecting collection variables in the import workflow, colliding variables (keys that already exist in the target environment) display both the current environment value and the incoming candidate collection value side-by-side.
2. For every colliding variable, users can independently choose between two conflict resolution strategies:
   - **Keep Current**: Retains the existing environment variable value.
   - **Overwrite**: Replaces the current environment variable value with the candidate collection value.
3. Non-colliding (new) variables are clearly indicated and are not burdened with conflict strategy choices.
4. A safe default conflict strategy ("Keep Current") is automatically assigned to colliding variables upon initial display.
5. Bulk controls are available to quickly set or reset the conflict strategy across all colliding variables simultaneously.
6. Secret masking is enforced across both current and candidate values in the comparison view when either value is designated as secret/hidden.
7. The import preview summary accurately reflects the count of new variables to add, existing variables to keep, and existing variables to overwrite based on active per-variable selections.
8. Confirming the import applies the exact per-variable conflict decisions to the target environment, preserving existing values where "Keep Current" was chosen and updating values where "Overwrite" was chosen.
9. All business rules, edge cases (such as empty values, identical values, and preset profile switching), and user interface interactions are verified through automated tests and quality gates.

## Task Description

### Problem Statement

During collection variable import, variable name collisions occur when a collection defines keys that already exist in the user's active workspace environment. Without side-by-side comparison and granular per-variable conflict resolution, users face an all-or-nothing choice that leads to configuration errors, accidental loss of customized local values, or cumbersome workarounds.

### Scope

- **Side-by-Side Diff Inspector**: Display current environment values alongside candidate collection values for colliding variables within the import preview.
- **Granular Per-Variable Conflict Strategy**: Provide a per-row selection mechanism (e.g., Keep Current vs. Overwrite) for each colliding variable.
- **Safe Baseline Strategy Defaults**: Ensure that colliding variables default to a safe, non-destructive strategy ("Keep Current") to prevent accidental overwrites.
- **Bulk Strategy Controls**: Provide one-click actions to set conflict strategies across all colliding variables (e.g., "Set All Collisions to Keep Current", "Set All Collisions to Overwrite").
- **Secret Masking & Privacy**: Ensure that secret variables (whether hidden in the environment or flagged secret in the collection) are masked in both the current and candidate value views.
- **Dynamic Preview Summary**: Update real-time summary statistics reflecting how many new variables will be added, how many colliding variables will be kept unchanged, and how many colliding variables will be overwritten.
- **Accurate Domain Application**: Apply the per-variable resolution choices faithfully when committing the import to the target environment.

### Out of Scope

- Arbitrary text line-by-line diff editors or syntax-highlighted three-way merge tools (values are evaluated as configuration entities/strings).
- Background automatic two-way synchronization between environments and collections.
- Modifying underlying encryption vault storage engines.
- Re-architecting unrelated environment management dialogs or workspace persistence layers.

### Functional Requirements

- **FR1 (Side-by-Side Comparison for Collisions)**:
  - For any variable whose name exists in both the target environment and the candidate collection, the import interface must present both the current environment value and the incoming collection candidate value.
  - New variables (not present in the target environment) must clearly show their candidate value and indicate that no prior value exists in the target environment.

- **FR2 (Per-Variable Conflict Strategy Selection)**:
  - For each colliding variable row, the user must be able to choose between:
    - **Keep Current**: Keep the target environment's existing value; do not overwrite.
    - **Overwrite**: Overwrite the target environment's value with the incoming candidate value.
  - The conflict strategy selection must be independent for each colliding variable. Changing the strategy for one variable must not alter other variables unless a bulk action is explicitly triggered.

- **FR3 (Default Conflict Strategy Policy)**:
  - By default, all colliding variables must initialize to the safe, non-destructive strategy: **Keep Current**.
  - New variables must default to being selected for addition.

- **FR4 (Bulk Conflict Strategy Controls)**:
  - The interface must provide convenient bulk controls (e.g., quick toggle buttons or global preset selectors) that allow users to:
    - Set all colliding variables to **Keep Current**.
    - Set all colliding variables to **Overwrite**.
  - Triggering a bulk control updates all colliding rows immediately while allowing subsequent individual adjustments.

- **FR5 (Secret Value Masking in Diff Inspector)**:
  - If a variable is marked as secret in the candidate collection OR is currently marked as hidden/secret in the target environment, its value must be visually masked (e.g., `********`) in the side-by-side view.
  - Masking must apply to both the current environment value column and the candidate collection value column whenever secrecy applies.
  - Secret status must be clearly indicated so the user understands why the value is masked.

- **FR6 (Dynamic Preview Summary)**:
  - The import preview summary must provide immediate feedback on the impact of the pending import:
    - Total new variables to add.
    - Total colliding variables to overwrite.
    - Total colliding variables to keep unchanged.
    - Total deselected/skipped variables.
  - Modifying any row's checkbox (included/excluded) or conflict strategy (Keep Current vs. Overwrite) must update this summary in real time.

- **FR7 (Preset Profile Interactivity)**:
  - When the user switches the selected collection preset profile, the candidate values in the preview table must update immediately to reflect the chosen preset.
  - If candidate values change due to preset switching, the collision status, side-by-side comparisons, and summary counts must refresh automatically while preserving user-selected conflict strategies where applicable.

- **FR8 (Selective Row Inclusion with Conflict Strategy)**:
  - Users must retain the ability to include or exclude any variable via a row selection checkbox.
  - If a colliding row is unchecked (deselected), it must be excluded from the import entirely (no value change occurs in the environment, and it is excluded from the overwrite/add counts).

- **FR9 (Import Execution & Commitment)**:
  - When the user confirms the import:
    - Variables marked as new and checked must be added to the environment.
    - Colliding variables marked as **Overwrite** and checked must update the environment value with the candidate value.
    - Colliding variables marked as **Keep Current** must remain unchanged in value in the environment.
    - Secret flags must be correctly applied to any added or updated variables that are declared secret in the collection.

### Non-Functional Requirements

- **NFR1 (Data Safety and Non-Destructiveness)**: The default behavior must prevent accidental overwrites. Unless the user explicitly selects "Overwrite" individually or via bulk controls, existing environment values must be preserved.
- **NFR2 (Security & Confidentiality)**: Sensitive credentials must never be rendered in plaintext in the comparison interface without explicit masking.
- **NFR3 (Clarity & Visual Differentiation)**: The side-by-side comparison must clearly distinguish between the current value, candidate value, and collision status so users can understand differences at a glance without visual ambiguity.
- **NFR4 (Performance & Responsiveness)**: Updating conflict strategies, toggling bulk actions, and recalculating summary statistics must happen instantaneously without perceptible UI lag (< 50ms for collections up to 200 variables).

### Constraints and Assumptions

- **Target Environment Available**: The user is performing the import against an existing, selected workspace environment.
- **Point-in-Time Operation**: The conflict resolution decisions are evaluated and applied at the moment the import is confirmed; no permanent synchronization link is created.
- **Variable Identifiers**: Variable matching between the environment and collection is determined by exact variable name (case-sensitive identifier matching).

### Main Business Entities

| Business Entity | Description | Attributes (Business Perspective) |
| --- | --- | --- |
| **Workspace Environment** | The destination container holding existing variable configurations. | Environment name, existing variable definitions (name, current value, secret/hidden flag). |
| **Source Collection** | The source defining declared variables and optional preset profiles. | Collection name, declared variables (name, candidate value, type, secret flag), presets. |
| **Collision Item** | A variable whose name exists in both the target environment and the source collection. | Variable name, current environment value, candidate collection value, current secret flag, candidate secret flag, selected conflict strategy. |
| **Conflict Strategy** | The policy applied to resolve a collision for a specific variable. | `Keep Current` (retain environment value), `Overwrite` (apply candidate collection value). |
| **Bulk Strategy Action** | A convenient operation that applies a uniform conflict strategy to all colliding items. | Action type (e.g., "Keep All Current", "Overwrite All"). |
| **Import Plan / Specification** | The complete user-configured set of decisions for the import operation. | Target environment, source collection, selected preset, per-variable inclusion flags, per-variable conflict strategies. |
| **Import Execution Result** | The summary of actual modifications made to the environment. | Added count, updated count, kept/skipped count, newly masked keys. |

### User Scenarios

#### Scenario 1: Preserving Custom Token While Updating Service Base URL
A developer is configuring their "Local Dev" environment from a team "Payments API" collection. The environment already contains:
- `BASE_URL = "http://old-api.internal"`
- `AUTH_TOKEN = "my-personal-dev-jwt-123"`

The team collection defines:
- `BASE_URL = "https://api.payments.dev"`
- `AUTH_TOKEN = "sample-sandbox-token"` (secret)
- `RETRY_COUNT = "3"` (new variable)

When the developer opens the import dialog:
1. Both `BASE_URL` and `AUTH_TOKEN` are flagged as collisions.
2. The side-by-side view displays:
   - For `BASE_URL`: Current value `"http://old-api.internal"`, Candidate value `"https://api.payments.dev"`.
   - For `AUTH_TOKEN`: Current value `"my-personal-dev-jwt-123"`, Candidate value `"********"` (masked because secret is enabled in the collection).
3. The developer sets the conflict strategy for `BASE_URL` to **Overwrite**, but leaves `AUTH_TOKEN` set to **Keep Current**.
4. `RETRY_COUNT` is marked as a new variable.
5. The developer confirms the import.
6. Result: `BASE_URL` is updated to `"https://api.payments.dev"`, `AUTH_TOKEN` remains `"my-personal-dev-jwt-123"`, and `RETRY_COUNT = "3"` is added.

#### Scenario 2: Quick Bulk Overwrite for Staging Environment Refresh
A QA engineer wants to update their "Staging" environment with all the latest default settings from an updated collection. The collection has 25 variables, of which 10 already exist in the environment.
1. The engineer opens the import dialog.
2. Rather than selecting "Overwrite" on 10 separate rows, the engineer clicks the bulk action **"Overwrite All Collisions"**.
3. All 10 colliding rows immediately update their strategy selector to **Overwrite**.
4. The preview summary updates to: `"15 new to add, 10 existing to overwrite, 0 existing to keep"`.
5. The engineer confirms the import, cleanly updating all 10 colliding variables and adding the 15 new ones.

#### Scenario 3: Secret Protection During Visual Diff Inspection
An engineer is presenting an environment setup during a recorded video conference.
1. The engineer opens the import dialog to pull variables from a partner collection.
2. The collection defines a secret API key `PARTNER_SECRET` which already exists in the engineer's environment.
3. Because the variable is designated as a secret, both the Current Value and Candidate Value columns render masked values (`********`).
4. The engineer safely reviews the conflict strategy without exposing private keys to meeting attendees or the video recording.

#### Scenario 4: Deselecting a Colliding Variable Entirely
A developer imports variables from a collection that contains a colliding variable `PORT = "8080"`. In the developer's environment, `PORT = "3000"` is used.
1. The developer does not want the collection import to touch `PORT` at all, nor does the developer want it recorded as an imported key.
2. The developer unchecks the selection box for the `PORT` row.
3. The row is excluded from the import operation.
4. When import is confirmed, the environment retains `PORT = "3000"` completely untouched.

## Q&A

**Q: Why is per-variable conflict strategy needed instead of just keeping the global dialog-wide radio buttons?**  
A: A global strategy forces an all-or-nothing trade-off. Users often want to accept new defaults for some configuration parameters (such as hostnames or timeout limits) while retaining custom local overrides for others (such as local ports or personal tokens). Per-variable strategy gives users the exact granularity required without manual post-import cleanups.

**Q: What should the default conflict strategy be for colliding variables?**  
A: The default strategy must be **Keep Current**. This ensures safety by preventing accidental data loss if a user quickly accepts the dialog without inspecting every row.

**Q: How does the side-by-side diff inspector handle secret or hidden variables?**  
A: If a variable is marked as secret in the collection, or is currently designated as a hidden/secret variable in the target environment, its value must be masked (e.g. `********`) in both the current and candidate value displays. This prevents visual leakage of sensitive credentials.

**Q: Do non-colliding (new) variables have a conflict strategy selector?**  
A: No. Non-colliding variables do not exist in the environment, so there is no conflict to resolve. They simply have an inclusion checkbox indicating whether they will be added.

**Q: How do bulk controls interact with individual row strategies?**  
A: Bulk controls act as convenient presets: clicking a bulk control (e.g., "Keep All Current" or "Overwrite All") updates the strategy for all colliding rows. Users can subsequently adjust individual rows as needed before confirming the import.

**Q: What happens if a user deselects (unchecks) a colliding variable row?**  
A: Deselecting a row excludes that variable from the import entirely. The target environment's existing variable remains unaltered, regardless of what conflict strategy was selected on that row.
