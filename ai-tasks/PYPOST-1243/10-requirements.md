# PYPOST-1243: Reusable variable autocomplete editing capability

## Goals

PyPost users enter request data in several editing contexts, including query parameters,
headers, and request bodies. These contexts need a consistent way to reference variables from
the active environment while preserving the user's surrounding text.

The current variable-aware editing experience is tied to one header-editing context. This
coupling makes the experience harder to share and increases the risk that users see different
completion and validation behavior in different editors.

**Business goal:** provide one consistent, reusable variable autocomplete experience across
supported request-editing contexts. Users should be able to discover and insert active
environment variables quickly, reduce spelling and formatting errors, and receive consistent
feedback when a reference is incomplete or unavailable.

## User Stories

- As a PyPost user editing query parameters, I want suggestions for variables from my active
  environment so that I can construct requests without memorizing variable names.
- As a PyPost user editing headers, I want the same variable reference behavior available in
  other request editors so that switching contexts does not change how I work.
- As a PyPost user editing a request body, I want to insert a variable at the current text
  position while retaining the surrounding content.
- As a PyPost user, I want suggestions to reflect the currently selected environment so that I
  do not accidentally choose a variable from a different environment.
- As a PyPost user reviewing a request, I want incomplete or unavailable variable references to
  be visibly identified so that I can correct them before sending the request.
- As a PyPost user working with sensitive variables, I want existing masking and disclosure
  expectations to remain unchanged while using autocomplete.

## Definition of Done

- Variable autocomplete is available as a shared user-facing capability for query parameters,
  headers, and request body editing contexts that support variable references.
- Typing the opening `{{` of a variable reference presents matching variable names from the
  active environment. A complete reference uses the user-visible `{{ VAR }}` syntax, including
  the variable name between the opening `{{` and closing `}}` delimiters.
- Suggestions are filtered as the user types and can be selected with the mouse or keyboard.
- Selecting a suggestion inserts a complete, consistently formatted `{{ VAR }}` reference at
  the current cursor position without losing unrelated text.
- The autocomplete experience supports multiple variable references within one field.
- Changing the active environment refreshes available suggestions and the status of existing
  variable references.
- An empty reference such as `{{ }}` is visibly identified as missing a variable name, and an
  incomplete reference such as `{{ VAR` or `{{ VAR }` is visibly identified as unfinished until
  its closing `}}` is present.
- A reference to a name unavailable in the active environment, such as `{{ MISSING }}`, is
  visibly identified as unavailable; feedback names the problem but does not display a value.
- In query parameters, headers, and request bodies, existing valid text and variable references
  remain unchanged after suggestions are shown, filtered, or inserted.
- Existing header editing behavior, request construction, and environment-variable handling
  remain observable to users as they were before this capability was shared: valid header
  content is retained, references keep their existing formatting, and requests continue to use
  the same resolved values.
- Users never see sensitive variable values in autocomplete suggestions, inserted reference
  text, or feedback for empty, incomplete, unavailable, or environment-switched references.
- Query parameters, headers, and request bodies present the same user-facing suggestion,
  insertion, and reference-feedback behavior wherever variable references are supported.

## Task Description

This task addresses a maintainability and consistency problem in PyPost's request editors. A
variable-aware text editor currently belongs to the MCP server headers editing context, although
query parameters, general headers, and request body editors have the same user need. The task is
to make that capability available for shared use while keeping the behavior users already rely
on for header editing.

### In scope

- Variable suggestion, filtering, insertion, and feedback behavior for query parameters,
  headers, and request body editors.
- Synchronization with the active environment and its available variable names.
- Consistent handling of incomplete or unavailable references.
- Preservation of sensitive-value masking expectations.
- Compatibility with existing request editing and header configuration workflows.

### Out of scope

- Creating, renaming, deleting, or editing environment variables.
- Changing variable resolution rules or request transport behavior.
- Redesigning unrelated editor controls or validation rules.
- Performance work for exceptionally large environments; this is tracked separately in
  PYPOST-1244.
- Theme and popup styling centralization; this is tracked separately in PYPOST-1245.
- Additional platform and focus/IME integration coverage; this is tracked separately in
  PYPOST-1246.

### Main business entities and interactions

- **User**: edits request-related fields and chooses variable suggestions.
- **Request editor**: presents query parameters, headers, or request body content and accepts
  variable references.
- **Active environment**: supplies the variable names available for the current editing
  context.
- **Variable reference**: a placeholder in user-authored request content that identifies an
  environment variable.
- **Request configuration**: retains the edited content for later preview, saving, or sending.

The user works in a request editor, the editor consults the active environment for available
variable names, and the resulting variable references remain part of the request configuration
until they are resolved by the existing request workflow.

## Q&A

### Why is this needed?

The same user-facing variable editing need exists in multiple request contexts, but the current
experience is coupled to one context. Sharing it reduces inconsistent behavior, lowers entry
errors, and makes environment-based request authoring faster.

### Which language is required?

Python, as mandated by the existing PyPost application.

### What behavior must remain compatible?

Existing header editing, variable-reference formatting, environment switching, request content,
and sensitive-value handling must continue to behave as users expect.

### What is the acceptance gate for this step?

The user reviews this requirements artifact and confirms that the business goal, functional
scope, boundaries, and acceptance criteria are complete. Step 1 remains in progress until that
review is approved.

### Related context

- Jira: PYPOST-1243
- Related technical-debt record: `ai-tasks/PYPOST-1104/60-tech-debt.md`
