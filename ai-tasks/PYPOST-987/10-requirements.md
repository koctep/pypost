# PYPOST-987: Import collection

## Programming language

Python

## Goals

PyPost groups saved requests into **collections**, shown as the tree in the left sidebar. Today a
collection can only come into being as a side effect of saving a request: the user types a new
collection name in the Save dialog, and then re-creates every request in it by hand — method, URL,
headers, params, body, post-response script, and MCP tool metadata, one field at a time.

That is a real cost when a user:

- Sets up PyPost on a new machine (or restores a backup) and wants their existing collections back
  without re-entering every request.
- Receives a teammate's collection (shared over chat, a shared drive, or a config repository) and
  wants to start calling the same API endpoints immediately.
- Moves a collection between two PyPost installations, e.g. work laptop and personal machine.

The business goal is to remove that manual re-entry step: let a user bring a collection — with all
of its requests — into PyPost from a file in one action, so sharing or moving a working set of
requests is a click instead of an error-prone transcription exercise.

## User Stories

- As a **user**, I want to import a collection from a file, so that I can reuse a set of requests I
  already built on another machine without recreating each request by hand.
- As a **user**, I want a teammate's shared collection file to load straight into my sidebar, so
  that I can start sending the same requests they use without manual re-entry.
- As a **user**, I want a file that contains several collections to import in one action, so that I
  do not have to repeat the import once per collection.
- As a **user**, I want each imported request to arrive complete — method, URL, headers, query
  params, body, post-response script, and its MCP tool settings — so that I can send or save it
  immediately without fixing up missing fields.
- As a **user**, I want to be warned when an imported collection has the same name as one I already
  have, and to decide what happens to it, so that importing never silently destroys a collection I
  am currently using.
- As a **user**, I want a clear, specific error message if the file I picked is not a valid
  collection file, so that I understand what went wrong and know my existing collections were left
  untouched.
- As a **user**, I want a clear confirmation after a successful import (how many collections and
  requests arrived, and what happened to any conflicts), so that I know the action worked.
- As a **user**, I want the imported collection to appear in the sidebar tree right away, so that I
  do not have to restart the app or hunt for it.
- As a **user**, I want to start the import from near the collections tree, so that the feature is
  easy to discover and consistent with how I already work with collections.

## Definition of Done

- [ ] A user can trigger "Import collection" from a UI entry point near the collections tree and
      pick a file from disk.
- [ ] Importing a file containing one or more valid collections adds them, with their requests, to
      the user's collections, without any manual re-entry.
- [ ] Imported requests preserve every field needed to send and re-save them: method, URL, headers,
      query params, body and body type, post-response script, and MCP tool flags/metadata.
- [ ] When an imported collection's name collides with an existing collection, the documented
      conflict policy (see Q&A) is applied consistently, and existing collections are never lost or
      corrupted as a side effect.
- [ ] Importing a file whose collection or request identifiers already exist locally never
      overwrites or merges into an unrelated existing collection or request by accident.
- [ ] Picking an invalid, corrupted, or unreadable file produces a clear, user-visible error and
      leaves all existing collections unchanged.
- [ ] A successful import gives the user visible confirmation of what was imported, and the
      collections tree shows the result without needing a restart.
- [ ] Automated tests cover: importing a valid file (happy path), importing a file with at least
      one name conflict, and importing an invalid file.
- [ ] `doc/user/collections.md` documents how to import a collection, the expected file format at a
      level a user can act on, and how name conflicts are handled.

## Task Description

**Problem:** Collections in PyPost can only be created inside the running application, and their
requests can only be populated one at a time through the request editor. There is no way to bring
in a collection prepared elsewhere — a previous PyPost installation, a backup, a teammate's copy, a
file kept in version control. Multi-machine setups and team onboarding are therefore slow and
error-prone: every request's URL, headers, body, and script must be retyped, exactly the kind of
values where a typo is hard to spot.

**Goal:** Add an **Import collection** action, reachable from near the collections tree, that loads
one or more collections (with their requests) from a file into the app in a single step.

**Scope (in):**

- A way to pick a file from disk and load one or more collections, with their requests, into the
  app.
- The file format must be one a user (or another PyPost installation) can realistically produce
  today — i.e. compatible with PyPost's own collection data on disk — since PyPost has no matching
  "Export collection" feature to guarantee round-tripping through a brand-new format.
- A single, documented policy for what happens when an imported collection's name already exists
  locally (see Q&A), and a documented rule for identifier collisions (see Q&A).
- Preservation of every request field needed to send and save the request.
- User-visible, specific error feedback for invalid/unreadable files; user-visible success feedback
  and an immediately refreshed sidebar tree for a completed import.
- Automated test coverage for the happy path plus the name-conflict and invalid-file cases.
- A short update to `doc/user/collections.md` describing the new action for end users.

**Scope (out):**

- Converting collections from third-party tools (Postman, Insomnia, OpenAPI).
- **Exporting** a collection to a file — an explicitly separate, future story.
- Importing or exporting **environments** — already delivered separately (PYPOST-986) and not
  changed here.
- Merging at the level of individual requests (e.g. "import only these three requests into that
  existing collection"). The unit of import is the collection.

**Constraints and assumptions:**

- Collections are persisted immediately, per collection, as the user works (unlike environments,
  which are written once when the management dialog closes). An import must therefore write its
  result to disk as part of the action, and must not leave the stored collections in a state that
  contradicts what the sidebar shows.
- Existing collections and requests already stored on disk must never be corrupted, truncated, or
  silently replaced as a result of an import, whether it succeeds, partially succeeds (per the
  conflict policy), or fails outright.
- Collection identifiers, not names, are what the app uses to address a collection on disk and in
  memory; two different collections must never end up sharing one identifier as a result of an
  import.
- Requests exposed as MCP tools are registered from whatever collections are loaded, so an import
  must leave MCP tool registration consistent with the newly imported requests.
- No new persistent user-facing settings are introduced beyond the import action itself and the
  conflict choice made at import time.

## Main Entities and Interactions

- **Collection** — a named group of saved requests, shown as a top-level node in the sidebar tree.
- **Request** — one saved HTTP call inside a collection, with its method, URL, headers, params,
  body, post-response script, and MCP tool settings.
- **Collection file** — the artifact the user picks from disk; it describes one or more collections
  and the requests inside them.
- **User's existing collections** — what is already in the sidebar before the import; the target
  the imported collections are merged into.
- **Import action** — the user-triggered operation of picking a file and bringing its collections
  into the app.
- **Conflict decision** — when an imported collection's name matches an existing one, the
  resolution applied per the documented policy before the collection is added.
- **Import outcome** — the user-visible result: which collections were added, updated, renamed, or
  skipped, how many requests arrived, and any entries that could not be read.

Interaction flow: a user chooses "Import collection" near the collections tree → picks a file → the
app reads and validates the file's collection(s) → for each collection whose name already exists
locally, the documented conflict policy is applied → the resulting collections are stored and shown
in the tree → the user sees a summary of what was imported and any errors, while invalid entries
are reported without touching the user's existing collections.

## Non-Functional Requirements

- **Data integrity**: an error during import (invalid file, one unreadable entry, a failed write)
  must never leave an existing collection corrupted or half-rewritten. Anything the user already
  had must either be untouched or replaced deliberately by an explicit conflict decision.
- **Identity safety**: an imported collection or request must never silently take over the storage
  slot of an unrelated existing one; identifier collisions must be resolved rather than ignored.
- **Fidelity**: a request that arrives via import must behave identically to one saved by hand —
  no field silently dropped, no MCP tool flag lost.
- **Clarity of feedback**: success and failure feedback must be specific enough for a
  non-technical user to know what happened (counts, which names conflicted and how they were
  resolved, which entry was invalid), not a generic "import failed".
- **Consistency**: the action's discoverability and interaction style (file picker, conflict
  prompt, result dialog) should match the Import environments feature users already have, so the
  two behave the same way.

## Q&A

**Q:** What is the conflict policy when an imported collection's name already exists locally?

**A:** Prompt the user at import time, per conflicting name, offering **Overwrite** (replace the
existing collection's requests), **Keep Both** (add the imported one under a disambiguated
`Copy of <name>` name), or **Skip** (leave the existing one alone and drop the imported one). This
is the exact policy already shipped for Import environments (PYPOST-986), so the two features stay
consistent; the dialog mechanics (including an "apply to all remaining conflicts" convenience) are
an implementation detail for the architecture step.

**Q:** Why is the conflict unit the collection name rather than its identifier?

**A:** The name is what the user sees in the sidebar and what the app already treats as the
uniqueness constraint when creating or renaming a collection. Identifiers are internal and a user
cannot reason about them, so a prompt keyed on an identifier would be meaningless.

**Q:** What happens if an imported collection's identifier already belongs to a different local
collection (for example, the file came from this same machine)?

**A:** The imported collection must be given a fresh identifier rather than taking over the
existing one's storage slot. The same rule applies to a request identifier inside it. This is a
data-integrity rule, not a user-facing choice, so it is applied silently without a prompt — the
user's decision is about names, which is what they can see.

**Q:** What happens if two collections inside the same imported file share a name?

**A:** Both are imported; the later one is disambiguated automatically the same way a "Keep Both"
outcome would be, with no prompt. Neither of them is a collection the user already had, so there is
nothing to protect by asking — only the final list's readability to preserve.

**Q:** What does the user see if the file is partly readable — some valid collections, some
malformed entries?

**A:** The valid collections import, and the result summary names the entries that could not be
read and why. One bad entry must not block the rest of the file, mirroring how Import environments
already handles a partly readable file.

**Q:** Are third-party formats (Postman, Insomnia, OpenAPI) in scope?

**A:** No. The Jira ticket explicitly excludes converters. The accepted format is PyPost's own
collection serialization.

**Q:** Is "Export collection" part of this task?

**A:** No, explicitly out of scope. The import is still useful on its own because PyPost's stored
collection files can be copied and shared as-is today.

**Q:** Does the import need to preserve which requests are exposed as MCP tools?

**A:** Yes. `Expose as MCP`, the agent-visible description, and the declared tool parameters are
part of a request's saved definition, and losing them would mean the imported collection does not
behave like the one that was shared. MCP tool registration must reflect the imported requests once
the import completes.

## Worklog
tokens_used: 62000
role: execution
step: 1
step_name: Requirements
