# PYPOST-986: Import environments

## Programming language

Python

## Goals

PyPost already lets a user manage named environments (variable sets such as `Local`, `Dev`,
`Prod`) through the "Manage environments" dialog, and it can protect sensitive values by marking
them **Hidden** (optionally encrypted at rest). However, environments can only be created by hand,
one variable at a time, inside the app that stores them.

This is a real cost when a user:

- Sets up PyPost on a new machine and wants their existing environments back without retyping
  every host, token, and API key.
- Receives a teammate's environment (for example, shared as a file over chat, a shared drive, or
  a repository) and wants to start using it immediately instead of manually re-creating each
  variable.

The business goal of this task is to remove that manual re-entry step: let a user bring one or
more environments into PyPost from a file, so that sharing a working setup across machines or
with teammates is a one-click action instead of a manual, error-prone transcription exercise.

## User Stories

- As a **user**, I want to import environments from a file, so that I can reuse a setup I already
  built on another machine without retyping every variable.
- As a **user**, I want to import an environment file a teammate shared with me, so that I can
  start working against the same configuration they use without manual re-entry.
- As a **user**, I want to import a file that contains several environments at once, so that I do
  not have to repeat the import action once per environment.
- As a **user**, I want to be warned when an imported environment has the same name as one I
  already have, and to decide what happens to it, so that importing never silently destroys an
  environment I am currently using.
- As a **user**, I want variables that were marked **Hidden** in the source file to still be
  **Hidden** after import, and to be encrypted at rest exactly as my current encryption setting
  dictates, so that importing a file never exposes or downgrades the protection of a secret value.
- As a **user**, I want to see a clear, specific error message if the file I picked is not a valid
  environment file (or a hidden value in it cannot be read), so that I understand what went wrong
  and know my existing environments were left untouched.
- As a **user**, I want a clear confirmation after a successful import (for example, how many
  environments were added or updated), so that I know the action worked and what changed.
- As a **user**, I want to start an import from the same place I already manage environments (the
  "Manage environments" screen / environment list actions), so that the feature is easy to
  discover and consistent with how I already add, rename, copy, or delete environments.

## Definition of Done

- [ ] A user can trigger "Import environments" from the environment management UI and pick a file
      from disk.
- [ ] Importing a file containing one or more valid environments adds them to the user's
      environments, without requiring the user to re-enter any variable by hand.
- [ ] When an imported environment's name collides with an existing environment, the single,
      documented conflict policy (see Q&A) is applied consistently, and existing environments are
      never lost or corrupted as a side effect.
- [ ] Variables marked Hidden in the source file remain Hidden after import, and are protected by
      the user's current encryption setting exactly as any other Hidden variable would be.
- [ ] Picking an invalid, corrupted, or unreadable file produces a clear, user-visible error and
      leaves all existing environments unchanged.
- [ ] A successful import gives the user visible confirmation of what was imported.
- [ ] Automated tests cover: importing a valid file (happy path), importing a file with at least
      one name conflict, and importing an invalid file.
- [ ] `doc/user/environments.md` documents how to import environments, the expected file format
      at a level a user can act on, and how name conflicts are handled.

## Task Description

**Problem:** Environments in PyPost can only be created and populated manually, one field at a
time, inside the running application. There is no way to bring in an environment that was
prepared elsewhere (a previous PyPost installation, a teammate's export, a file kept in version
control or a shared drive). This makes multi-machine setups and team onboarding slower and more
error-prone than necessary, since every variable — including hosts, tokens, and other
configuration — must be retyped by hand, with a real risk of typos in exactly the kind of values
(URLs, keys) where a typo is hard to notice.

**Goal:** Add an **Import environments** action, reachable from the same area of the UI where
environments are already managed today (the "Manage environments" screen / environment list
actions), that lets a user load one or more environments from a file into the app in a single
step.

**Scope (in):**

- A way to pick a file from the user's disk and load one or more environments from it into the
  app's list of environments.
- The imported file's format must be one a user (or another PyPost installation) can realistically
  produce today — i.e. compatible with PyPost's own environment data (name, variables, which
  variables are Hidden, and the MCP-enablement flag) — since PyPost does not yet have a matching
  "Export environments" feature to guarantee round-tripping through a brand-new format.
- A single, documented policy for what happens when an imported environment's name already exists
  locally (see Q&A for the chosen policy).
- Hidden/secret variables keep their Hidden status through the import, and are subject to the
  user's current encryption setting afterwards, regardless of whether the source file's values
  were stored in plaintext or encrypted, and regardless of whether an encrypted value in the
  source file can or cannot be decrypted locally.
- User-visible, specific error feedback for invalid/unreadable files (including a file that
  contains an encrypted secret value that cannot be decrypted with the current installation's
  keys), and user-visible success feedback for a completed import.
- Automated test coverage for the happy path plus the name-conflict and invalid-file cases.
- A short update to `doc/user/environments.md` describing the new action for end users.

**Scope (out):**

- Converting environments from third-party tools (Postman, Insomnia, OpenAPI, etc.) — unless it
  turns out to be trivial reuse of the native format, which is not assumed here.
- **Exporting** environments to a file — that is explicitly a separate, future story. This task
  only consumes files; it does not need to produce them (a user's import file is expected to come
  from another PyPost installation's data, a teammate, or a hand-maintained file, not from an
  in-app export button delivered by this task).
- Importing or exporting **collections** (requests) — this task is scoped to environments only.

**Constraints and assumptions:**

- The app already has an established "environment list actions" pattern (add, rename, copy,
  delete) that any new action should sit alongside for discoverability and consistency; this task
  does not need to invent a new area of the UI for it.
- The app already has an established Hidden/secret concept per variable, plus an optional
  at-rest-encryption setting that is a property of the local installation (its configured key
  source), not of any individual environment or file. Importing must respect the *local*
  installation's current encryption setting for how Hidden values end up stored after import; it
  must not import an environment in a way that leaves a Hidden value's encryption inconsistent
  with that setting.
- A source file may contain a Hidden value that was encrypted by a different installation than the
  one performing the import. Such an installation cannot always decrypt that value (it may not
  share the same encryption key). This is treated as an expected, recoverable failure case (see
  Q&A), not a crash or silent data loss.
- Existing environments and the data already stored on disk must never be left corrupted or
  partially written as a result of an import, whether the import succeeds, partially succeeds
  (per the conflict policy), or fails outright.
- No new persistent user-facing settings/preferences are introduced by this task beyond the import
  action itself and its conflict-resolution choice at the time of import.

## Main Entities and Interactions

- **Environment** — a named set of variables (business perspective: a "configuration profile" like
  `Local`/`Dev`/`Prod`), some of whose variables are marked Hidden/secret. This is both what
  already exists in the app and what is contained in the file being imported.
- **Environment file** — the artifact a user picks from disk to import; it describes one or more
  environments, including which of their variables are Hidden.
- **User's existing environments** — the environments already present in the app before the
  import; the target that the imported environments are merged into.
- **Import action** — the user-triggered operation of picking a file and bringing its
  environment(s) into the app.
- **Conflict decision** — when an imported environment's name matches an existing one, the
  resolution applied per the documented policy (see Q&A) before the environment is added.
- **Import outcome** — the user-visible result of the action: which environments were added,
  which were affected by a conflict decision, and any errors encountered (for the whole file or
  for a specific environment within it).

Interaction flow: a user opens environment management → chooses "Import environments" → picks a
file → the app reads and validates the file's environment(s) → for each environment whose name
already exists locally, the documented conflict policy is applied → valid environments (after
conflict resolution) are added to the user's environments → the user sees a summary of what was
imported and any errors, while any invalid entries are reported without touching the user's
existing environments.

## Non-Functional Requirements

- **Data integrity**: an import must be all-or-nothing at the level of "existing data on disk" —
  a failure or error during import (e.g. an invalid file, or one environment failing to decrypt)
  must never leave the existing stored environment data corrupted, truncated, or partially
  rewritten.
- **Security**: importing must never cause a value that was Hidden in the source file to end up
  stored as plaintext, and must never cause a value that fails to decrypt to be silently treated
  as its own (garbled) ciphertext value; both must surface as explicit errors instead.
- **Clarity of feedback**: both success and failure feedback must be specific enough for a
  non-technical user to know what happened (e.g. how many environments were imported, which
  name(s) had conflicts and how they were resolved, and which file/entry was invalid), not just a
  generic "import failed" message.
- **Consistency**: the import action's discoverability and interaction style (dialogs, prompts,
  confirmations) should feel consistent with the existing environment management actions (add,
  rename, copy, delete) already familiar to users.

## Q&A

**Q:** What is the chosen conflict policy when an imported environment's name already exists
locally?

**A:** Prompt the user at import time, per conflicting name, with the choice to **overwrite** the
existing environment's contents, **keep both** (the imported one is added under a
disambiguated/renamed name, mirroring the existing "Copy" action's `Copy of <name>` style naming),
or **skip** that specific environment and continue with the rest of the file. This mirrors the
app's existing pattern of confirming destructive actions (e.g. delete) and disambiguating names
(e.g. duplicate) rather than silently overwriting or silently discarding data. The exact dialog
mechanics (e.g. an "apply to all remaining conflicts" convenience) are an implementation detail
for the architecture/design step, not a requirements decision.

**Q:** Where does the file a user imports come from, given there is no "Export environments"
feature yet?

**A:** Per the Jira scope, export is an explicitly separate, future story. The import feature is
still valuable on its own because a user's existing stored environment data (or a copy from
another PyPost installation) can be shared as-is (e.g. copied to a USB drive, sent over
chat, or committed to a private config repo) even without a dedicated in-app export button. The
import format is therefore expected to be compatible with the shape of data PyPost already
produces for its own storage, not a brand-new format invented for this task alone.

**Q:** What should happen if a Hidden/secret value in the imported file was encrypted by a
different installation (different encryption key) and cannot be decrypted locally?

**A:** That specific value/environment must fail import with a clear, specific error (e.g. naming
the environment and noting it could not be decrypted with this installation's current encryption
configuration) rather than being imported as unreadable ciphertext or silently dropped. Other,
unaffected environments in the same file must still import successfully — a single undecryptable
entry must not block the rest of the file.

**Q:** Does importing change anything about how encryption works?

**A:** No. Whether Hidden values end up encrypted on disk after import continues to depend solely
on the local installation's existing encryption setting, exactly as it does for any Hidden value
entered by hand. Import does not introduce a new encryption mode, key, or per-environment
encryption toggle.

**Q:** Is importing collections (requests) part of this task?

**A:** No — the Jira ticket explicitly scopes this to environments only; collection import/export
is out of scope.

**Q:** Are third-party formats (Postman, Insomnia, OpenAPI) in scope?

**A:** No, unless trivial reuse of the native format is possible — not assumed as part of this
task's baseline scope.
