# PYPOST-1316: Create a GitLab collection for MCP in PyPost

## Goals

PyPost users and AI agents already get a ready-to-import Jira Cloud MCP pair
(`examples/collections/jira_mcp.json` + `examples/environments/jira_cloud.json`) that turns
PyPost into an MCP endpoint without writing requests by hand. Teams that host code in GitLab
have no equivalent: they must hand-build requests, guess encoding rules for project and file
paths, and risk committing tokens.

Business goal: ship a curated, ready-to-import **GitLab MCP collection** and companion
**environment** in the example library so that a user can, in minutes and without code, expose
the everyday GitLab workflow (find a project, read code and history, work on issues and merge
requests, comment, inspect CI) to an AI agent through a PyPost MCP endpoint — for both
GitLab.com and self-hosted GitLab — while keeping secrets out of git and keeping the fixture
protected by offline checks that never contact GitLab.

**Implementation language**: JSON/YAML example fixtures under `examples/` plus Python (pytest)
offline contract tests under `tests/`, executed only through `make` targets.

## User Stories

- **US1 (end user, GitLab.com)**: As a developer using GitLab.com, I want to import a GitLab
  collection and environment, enter my token and default project, and start an MCP endpoint, so
  that my AI agent can work with my GitLab project.
- **US2 (end user, self-hosted)**: As a developer at a company with a self-hosted GitLab, I want
  to point the same collection at my instance URL, so that I do not need a separate fixture.
- **US3 (AI agent)**: As an AI agent connected to the PyPost MCP endpoint, I want clearly named
  tools with descriptions and argument schemas, so that I can choose the right tool and supply
  valid arguments without guessing GitLab API details.
- **US4 (library user)**: As a user of the Library Manager, I want the GitLab collection to
  appear in the official example library with its variables and a preset, so that I can attach
  it the same way as the Jira collection.
- **US5 (security-conscious maintainer)**: As a maintainer, I want the token to be marked
  secret and only placeholders to be tracked, so that no credential leaks through the repo or
  environment exports.
- **US6 (contributor)**: As a contributor, I want offline checks run through `make` that fail
  when the fixture drifts (format, variables, MCP schemas, HTTP contracts), so that regressions
  are caught without credentials or network access.

## Definition of Done

Each criterion below must be verifiable by an offline automated check run through a `make`
target, or (for documentation) by inspection of the tracked files.

### AC1 — Import and MCP availability (refines Jira AC1)

1. A new collection `examples/collections/gitlab_mcp.json` loads through the same native
   collection loader used for `jira_mcp.json` without errors or migration warnings beyond those
   accepted for existing examples.
2. A new environment `examples/environments/gitlab.json` (final name may be adjusted in Step 2,
   but must live under `examples/environments/`) imports through the same path as
   `jira_cloud.json`.
3. Every request intended as a tool is marked as exposed via MCP and has a non-empty MCP
   description; tool names are unique, stable, and share a common GitLab prefix (analogous to
   the `jira_` prefix).
4. With the collection + environment selected for an MCP endpoint, the published tool list
   equals the documented tool set (no missing, no undocumented extra tools), and each tool's
   published input schema matches its declared arguments (names, types, required flags).

### AC2 — Tool coverage and HTTP contracts (refines Jira AC2)

The collection must cover at least the following capabilities. Tool names, exact count, and
JSON shape are decided in Step 2; the capability list is the contract.

| Area | Required capabilities |
| ---- | --------------------- |
| Identity | Get the authenticated user (connectivity / token sanity check) |
| Projects | Search/list projects visible to the user; get one project (by numeric ID or full path) |
| Repository — branches | List branches of a project; get one branch |
| Repository — files | Read a file's content at a ref (branch, tag, or commit); list a repository tree (directory listing) at a ref |
| Repository — commits | List commits (optionally filtered by ref and path); get one commit |
| Issues | List issues of a project (with filters such as state, labels, search text, pagination); get one issue; create an issue; update an issue (including close/reopen) |
| Merge requests | List merge requests of a project (with filters such as state, pagination); get one merge request; create a merge request; update a merge request (including close/reopen) |
| Comments | List and add comments (notes) on an issue; list and add comments (notes) on a merge request |
| CI/CD | List pipelines of a project (filters such as ref, status); get one pipeline; list jobs of a pipeline; get one job |

For every tool, an offline check verifies:

- the HTTP method matches the documented GitLab REST API v4 operation (read = `GET`,
  create = `POST`, update = `PUT`);
- the URL is `<configured base URL>` + the GitLab REST API v4 path for that operation;
- query parameters and request body fields used by the tool are the ones GitLab documents for
  that operation (create/update tools send a JSON body; read tools send no body);
- every placeholder the request references is either a declared MCP argument or a variable
  provided by the companion environment (no dangling references);
- every declared MCP argument is actually used by the request (no dead arguments).

A locked, offline catalog of the expected method + path per tool (analogous to
`jira_mcp_critical_rest_paths.json`) is in scope if Step 2 chooses that mechanism; the
requirement is only that path/method drift is detected offline.

Explicitly **not** required (documented as gaps): delete operations of any kind, approvals,
MR merge/rebase action, pipeline trigger/retry/cancel, job logs/artifacts download, file
create/update/delete (commits via API), wikis, snippets, releases, tags/protected branches
management, groups/namespaces administration, users/members management, labels/milestones CRUD,
webhooks, GraphQL API.

### AC3 — Configuration, encoding, and secrets (refines Jira AC3)

1. **Configurable instance URL**: one environment variable holds the GitLab base URL (default
   placeholder `https://gitlab.com`); all tool URLs derive from it. Pointing it at a
   self-hosted URL (including one served under a sub-path such as
   `https://git.example.com/gitlab`) changes every tool's target without editing the collection.
2. **Default project**: one visible environment variable holds the default project
   (numeric ID or full `namespace/project` path). Project-scoped tools use it when the agent
   does not provide a project, and allow the agent to supply another project explicitly.
   As with `jira_project_key`, it is a soft default, not a security boundary. Whether it is
   MCP-overridable follows the Jira environment convention unless Step 2 justifies otherwise.
3. **Encoding rules** (each verified by an offline substitution check with concrete sample
   values):
   - A project identified by full path (e.g. `group/subgroup/my-project`) is URL-encoded as a
     single path segment (`group%2Fsubgroup%2Fmy-project`); a numeric project ID
     (e.g. `42`) is passed unchanged.
   - A repository file path (e.g. `src/app/main.py`) is URL-encoded as a single path segment
     (`src%2Fapp%2Fmain.py`), including characters such as spaces, `#`, `?`, `%` and `+`.
   - Branch names used in a path segment (e.g. `feature/x`) are URL-encoded the same way.
   - Refs, paths, and free-text search values passed as query parameters are encoded so that
     reserved characters cannot alter the query string.
   - Issue and merge request **IIDs** (project-scoped), pipeline IDs, and job IDs are numeric
     path identifiers; they accept a native integer or a decimal string, and reject
     non-decimal input before any HTTP request (same contract as the Jira board/sprint IDs,
     PYPOST-1038). Commit SHAs are accepted as strings.
   - Tool descriptions state whether an argument is a project-scoped IID or a global ID, and
     whether a project accepts an ID or a path.
4. **Secret token**: authentication uses a GitLab personal/project/group access token sent in
   a GitLab-supported header on every tool request, using one consistent convention across the
   collection (verified offline). The token variable is marked `secret: true` in the collection
   and library manifest and listed in the environment's hidden keys.
5. **No secrets in git**: tracked files contain only obvious placeholders for the token (no
   value matching a GitLab token pattern such as `glpat-` followed by a realistic secret); an
   offline check enforces this.

### AC4 — Library and documentation (refines Jira AC4)

1. `examples/pypost-library.yaml` lists the GitLab collection, declares the GitLab variables
   (base URL, default project, token with `secret: true`) and adds a GitLab preset, without
   breaking the existing Jira entries or existing library tests.
2. `examples/README.md` documents, for the GitLab pair:
   - inventory entry (audience, purpose, tool count);
   - recommended import order (environment, placeholders, collection, environment selection,
     MCP endpoint creation and start, pointing the agent at the `/mcp` URL);
   - authentication: how to create a token, minimum scopes for read-only use and for
     read/write use, and where to enter it (hidden key);
   - setup for **GitLab.com** and for **self-hosted GitLab** (base URL form, sub-path
     installs, note that self-signed TLS/network access is the user's environment concern);
   - default project semantics and the encoding rules users/agents should know (ID vs path,
     IID vs ID);
   - coverage table and explicit gaps;
   - secret handling (placeholders only, never commit real tokens).
3. Documentation passes the repo doc linters (`make lint` / `make lint-docs`, `make
   check-docs-links`).

### AC5 — Offline checks via make (refines Jira AC5)

1. New offline tests cover: collection format/loading, environment loading, library manifest
   entry, variable substitution (including encoding cases above), published MCP tool schemas,
   HTTP contracts (method, path, params, body) for every tool, auth convention, secret marking
   and placeholder-only enforcement, and documented-tool-set parity.
2. HTTP contract checks run against no network or a loopback-only stub; no test contacts
   gitlab.com or any external host, and none requires real credentials.
3. The checks run as part of `make test` / `make check`; Step 2 may additionally add a focused
   make target (analogous to `check-jira-mcp-path-freshness`).
4. Existing example/library tests (`tests/test_example_fixtures.py`,
   `tests/test_examples_modernization.py`, library manifest tests, MCP collection e2e) keep
   passing; any count/inventory assertions affected by adding the collection are updated
   consciously, not weakened.
5. `make check` passes.

## Task Description

### Problem

There is no GitLab counterpart to the Jira MCP example pair, so GitLab users cannot quickly
expose GitLab to agents via PyPost, and there is no tested guidance on GitLab-specific
encoding (path-encoded project IDs and file paths, IID vs ID) or token handling.

### Main business entities

- **GitLab instance** — GitLab.com or self-hosted; identified by base URL.
- **Access token** — secret credential with scopes; never tracked.
- **Project** — identified by numeric ID or full namespace path; may be a default.
- **Repository objects** — branch, ref, file, tree entry, commit.
- **Work items** — issue and merge request (project-scoped IID), note (comment).
- **CI objects** — pipeline, job.
- **PyPost artifacts** — collection (requests exposed as MCP tools), environment
  (variables, hidden keys), example library manifest (collections, variables, presets),
  MCP endpoint (collection + environment served at `/mcp`).

### Scope

In scope:

- New collection and environment example fixtures, library manifest update, README docs.
- Offline Python tests (and optionally a make target) validating the fixtures.

Out of scope:

- Any live call to GitLab, live smoke tests, or tests requiring credentials (a live opt-in
  smoke like `test-jira-mcp-live` is not part of this task).
- New PyPost runtime features (template functions, auth types, MCP server changes). Existing
  capabilities (e.g. the `urlencode` template function, `to_int`, `integer_or_string` MCP
  params, hidden keys) are expected to suffice. If Step 2 finds a genuine gap, it must be
  justified and kept minimal, or recorded as a follow-up instead of being built here.
- GitLab GraphQL API, OAuth flows, and the operations listed as explicit gaps in AC2.
- Changes to the Jira collection/environment other than shared-library/README edits.
- Replacing any external GitLab MCP server; this is a PyPost-native analog for the in-scope set.

### Constraints and assumptions

- Target API: GitLab REST API v4 (`/api/v4`), same paths on GitLab.com and self-hosted.
- Format must match what the current PyPost collection/environment/library loaders accept
  (same structure as the Jira examples).
- All repository operations go through `make` targets (AGENTS.md).
- Pagination is exposed via GitLab's documented `page`/`per_page` query parameters where
  listing is involved; full auto-pagination is not required.

## Q&A

- **Q: Why a fixture rather than a runtime integration?** A: The business need is a
  zero-code, importable starting point, consistent with the Jira example; PyPost's MCP
  endpoint already turns collections into tools.
- **Q: Environment file name?** A: Proposed `examples/environments/gitlab.json`; Step 2 may
  rename it (e.g. `gitlab_com.json`) as long as docs and tests agree.
- **Q: Which auth header?** A: Any GitLab-documented token header (`PRIVATE-TOKEN` or
  `Authorization: Bearer`) is acceptable; Step 2 picks one and the checks enforce consistency.
- **Q: Default project behavior when unset?** Open — Step 2 decides whether project-scoped
  tools require an explicit project when the default is empty or rely on the placeholder.
- **Q: Exact tool count?** Open — fixed in Step 2 from the capability table in AC2; the docs
  and parity test must match it.
- References: `examples/collections/jira_mcp.json`, `examples/environments/jira_cloud.json`,
  `examples/pypost-library.yaml`, `examples/README.md`, `tests/test_example_fixtures.py`,
  `tests/test_examples_modernization.py`, `tests/test_mcp_collection_e2e.py`,
  `pypost/core/function_registry.py` (`urlencode`), `pypost/core/mcp_tool_contract.py`
  (`integer_or_string`).
