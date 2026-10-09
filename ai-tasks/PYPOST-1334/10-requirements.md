# PYPOST-1334: Create a GitHub collection for MCP in PyPost (Actions, pull requests, issues)

## Goals

PyPost already ships two ready-to-import MCP example pairs: Jira Cloud
(`examples/collections/jira_mcp.json` + `examples/environments/jira_cloud.json`) and GitLab
(`examples/collections/gitlab_mcp.json` + `examples/environments/gitlab.json`, PYPOST-1316).
Teams that host code on GitHub have no equivalent: to let an AI agent see CI results, work on
pull requests, or triage issues through PyPost, they must hand-build requests, guess GitHub
header and encoding conventions, and risk committing personal access tokens.

Business goal: ship a curated, ready-to-import **GitHub MCP collection** and companion
**environment** in the example library so that a user can, in minutes and without code, expose
the everyday GitHub delivery loop to an AI agent through a PyPost MCP endpoint:

- **Actions** — see which workflows exist, inspect runs and jobs, start a manual run, re-run
  or cancel a run;
- **Pull requests** — find, read, open and update pull requests, read their changes, and take
  part in review (comments and reviews);
- **Issues** — find, read, open, update and comment on issues.

It must work for both **github.com** and **GitHub Enterprise Server**, keep secrets out of git,
and be protected by offline checks (run through `make`) that never contact GitHub.

**Implementation language**: JSON/YAML example fixtures under `examples/` plus Python (pytest)
offline contract tests under `tests/`, executed only through `make` targets (same as
PYPOST-1316).

## User Stories

- **US1 (end user, github.com)**: As a developer using github.com, I want to import a GitHub
  collection and environment, enter my token and default owner/repository, and start an MCP
  endpoint, so that my AI agent can work with my repository.
- **US2 (end user, GitHub Enterprise Server)**: As a developer at a company running GitHub
  Enterprise Server, I want to point the same collection at my instance's API URL, so that I do
  not need a separate fixture.
- **US3 (AI agent, CI)**: As an AI agent, I want to list workflows and runs, inspect a failed
  run's jobs, dispatch a workflow, and re-run or cancel a run, so that I can help diagnose and
  drive CI without the user switching to the browser.
- **US4 (AI agent, code review)**: As an AI agent, I want to list and read pull requests, see
  their files and commits, read and write review comments, conversation comments and reviews,
  and open or update pull requests, so that I can assist with code review and PR hygiene.
- **US5 (AI agent, triage)**: As an AI agent, I want to list, read, create and update issues
  (title, body, labels, assignees, open/closed state) and read or add issue comments, so that I
  can assist with issue triage.
- **US6 (AI agent, tool choice)**: As an AI agent, I want clearly named tools with descriptions
  and argument schemas, so that I can pick the right tool and supply valid arguments without
  guessing GitHub REST API details.
- **US7 (library user)**: As a Library Manager user, I want the GitHub collection to appear in
  the official example library with its variables and a preset, so that I can attach it the
  same way as the Jira and GitLab collections.
- **US8 (security-conscious maintainer)**: As a maintainer, I want the token to be marked
  secret and only placeholders to be tracked, with a check that rejects real-looking GitHub
  tokens, so that no credential leaks through the repository or environment exports.
- **US9 (contributor)**: As a contributor, I want offline checks run through `make` that fail
  when the fixture drifts (format, variables, MCP schemas, HTTP contracts, REST paths), so that
  regressions are caught without credentials or network access.

## Definition of Done

Each criterion must be verifiable by an offline automated check run through a `make` target,
or (for documentation) by inspection of tracked files.

### AC1 — Import and MCP availability (refines Jira AC1)

1. A new collection `examples/collections/github_mcp.json` loads through the same native
   collection loader used for `jira_mcp.json` and `gitlab_mcp.json`, without errors or
   migration warnings beyond those accepted for the existing examples.
2. A new environment under `examples/environments/` (proposed name `github.json`; Step 2 may
   adjust it) imports through the same path as `jira_cloud.json` and `gitlab.json`.
3. Every request intended as a tool is exposed via MCP and has a non-empty MCP description;
   tool names are unique, stable, and share a common `github_` prefix (analogous to `jira_` and
   `gitlab_`).
4. With the collection + environment selected for an MCP endpoint, the published tool list
   equals the documented tool set (no missing, no undocumented extra tools), and each tool's
   published input schema matches its declared arguments (names, types, required flags).

### AC2 — Tool coverage and HTTP contracts (refines Jira AC2)

The collection must cover at least the following capabilities against the GitHub REST API.
Tool names, exact count, and JSON shape are decided in Step 2; the capability list is the
contract.

| Area | Required capabilities |
| ---- | --------------------- |
| Identity | Get the authenticated user (connectivity / token sanity check) |
| Repository | Get one repository (default owner/repo or an explicit one) |
| Actions — workflows | List workflows of a repository |
| Actions — runs | List workflow runs (repository-wide and/or per workflow, with filters such as branch, status, event, pagination); get one run; re-run a run; cancel a run |
| Actions — jobs | List jobs of a run; get one job |
| Actions — dispatch | Trigger a `workflow_dispatch` run of a workflow on a ref, with optional workflow inputs |
| Pull requests | List pull requests (filters such as state, base, head, pagination); get one; create one; update one (title, body, base, state including close/reopen) |
| Pull request contents | List files changed by a pull request; list commits of a pull request |
| Pull request discussion | List and create review comments (line comments on the diff); list and create pull request conversation comments |
| Pull request reviews | List reviews of a pull request; create a review (comment, approve, or request changes) |
| Issues | List issues (filters such as state, labels, assignee, pagination); get one; create one; update one (title, body, labels, assignees, state) |
| Issue comments | List and create comments on an issue |

Merging a pull request is **optional**: Step 2 decides whether to include it. If included, the
tool description must clearly state that it is an irreversible write, and the documentation must
list the extra permission it needs; if excluded, it is listed as a documented gap.

For every tool, an offline check verifies:

- the HTTP method matches the documented GitHub REST API operation (reads use `GET`; creates,
  dispatch, re-run and cancel use `POST`; updates use `PATCH`; merge, if included, uses `PUT`);
- the URL is `<configured API base URL>` + the documented GitHub REST path for that operation;
- query parameters and request body fields used by the tool are the ones GitHub documents for
  that operation (writes send a JSON body; reads send no body);
- every request sends the GitHub-recommended headers `Accept: application/vnd.github+json` and a
  pinned `X-GitHub-Api-Version` (one consistent value across the collection);
- every placeholder a request references is either a declared MCP argument or a variable
  provided by the companion environment (no dangling references);
- every declared MCP argument is actually used by the request (no dead arguments).

A **locked offline REST path catalog** (expected method + path per tool, analogous to
`examples/collections/gitlab_mcp_rest_paths.json`) and a **make freshness target** (analogous to
`check-gitlab-mcp-path-freshness`) are required; they fail when the collection, the catalog, and
the documented tool set drift apart.

Explicitly **not** required (documented as gaps): delete operations of any kind; repository
content reads and writes (files, trees, branches, commits outside a pull request); workflow run
logs and artifacts download; Actions secrets, variables, runners and environments management;
deployments and environments approvals; checks/statuses APIs; releases and tags; labels and
milestones CRUD; projects (classic or v2); discussions; gists; webhooks; organization, team and
member administration; search API; notifications; GraphQL API; GitHub Apps / OAuth flows.

### AC3 — Configuration, encoding, and secrets (refines Jira AC3)

1. **Configurable API base URL**: one environment variable holds the GitHub REST API base URL
   (default placeholder `https://api.github.com`); all tool URLs derive from it. Pointing it at
   a GitHub Enterprise Server API URL (form `https://<host>/api/v3`) changes every tool's
   target without editing the collection.
2. **Default owner and repository**: visible environment variables hold the default repository
   owner (user or organization) and repository name. Repository-scoped tools use them when the
   agent does not provide a repository, and let the agent supply another owner/repository
   explicitly. As with `gitlab_project`, the defaults are a soft convenience, not a security
   boundary; MCP-overridability follows the GitLab environment convention unless Step 2
   justifies otherwise. Non-empty placeholders are tracked consistently in the environment,
   preset, and manifest defaults (see the blank-segment risk tracked in PYPOST-1332).
3. **Encoding rules** (each verified by an offline substitution check with concrete sample
   values):
   - Owner, repository, and workflow identifier (numeric ID or workflow file name such as
     `ci.yml`) are each encoded as a single path segment: a value containing `/`, spaces, `#`,
     `?`, `%`, or `+` cannot add, split, or escape path segments.
   - Branch names and refs (e.g. `feature/x`) used anywhere in the request are encoded so that
     `/` and reserved characters cannot alter the path or the query string; refs sent in a JSON
     body are sent verbatim as JSON strings.
   - Free-text and filter values passed as query parameters (labels, head/base, branch, status)
     are encoded so that reserved characters cannot alter the query string.
   - Pull request numbers, issue numbers, run IDs, job IDs, comment IDs, and review IDs are
     numeric path identifiers: they accept a native integer or a decimal string and reject
     non-decimal input before any HTTP request (same contract as GitLab IIDs and Jira
     board/sprint IDs, PYPOST-1038). Commit SHAs are accepted as strings.
   - Tool descriptions state that pull request and issue numbers are repository-scoped numbers
     (not global IDs) and whether a workflow accepts an ID or a file name.
4. **Secret token**: authentication uses a GitHub personal access token (fine-grained or
   classic) sent in a GitHub-supported authorization header on every tool request, with one
   consistent convention across the collection (verified offline). The token variable is
   marked `secret: true` in the collection and library manifest and listed in the
   environment's hidden keys.
5. **No secrets in git**: tracked files contain only obvious placeholders for the token. An
   offline check rejects any value that looks like a real GitHub token — at least the classic
   `ghp_` and fine-grained `github_pat_` prefixes followed by a realistic secret.

### AC4 — Library and documentation (refines Jira AC4)

1. `examples/pypost-library.yaml` lists the GitHub collection, declares the GitHub variables
   (API base URL, default owner, default repository, token with `secret: true`) and adds a
   github.com preset, without breaking the existing Jira and GitLab entries or library tests.
2. User-facing documentation (`examples/README.md`) covers, for the GitHub pair:
   - inventory entry (audience, purpose, tool count);
   - recommended import order (environment, placeholders, collection, environment selection,
     MCP endpoint creation and start, pointing the agent at the `/mcp` URL);
   - authentication: creating a fine-grained or classic token, and the **minimum permissions
     per tool group** (identity/repository reads, Actions read vs write, pull requests read vs
     write, issues read vs write, and merge if included);
   - setup for **github.com** and for **GitHub Enterprise Server** (API base URL form, note
     that TLS trust and network reachability are the user's environment concern);
   - default owner/repository semantics and the encoding rules users and agents should know
     (path segments, refs, numbers vs IDs, workflow ID vs file name);
   - coverage table and explicit gaps;
   - secret handling (placeholders only, never commit real tokens).
3. Documentation passes the repository doc checks run by `make lint` (and any doc-link check
   target the GitLab docs pass).

### AC5 — Offline checks via make (refines Jira AC5)

1. New offline tests cover: collection format/loading, environment loading, library manifest
   entry, variable substitution (including the encoding cases above), published MCP tool
   schemas, HTTP contracts (method, path, headers, params, body) for every tool, the auth
   convention, secret marking, placeholder-only and token-pattern enforcement, documented
   tool-set parity, and the locked REST path catalog.
2. HTTP contract checks use no network or a loopback-only stub; no test contacts github.com,
   any GitHub Enterprise Server, or any external host, and none requires real credentials.
3. The checks run as part of `make test` / `make check`; the path freshness check is also
   available as its own make target.
4. Existing example and library tests (fixtures, modernization, predefined library inventory,
   MCP collection e2e, GitLab and Jira collection tests) keep passing; inventory assertions
   affected by the new collection are updated consciously, not weakened.
5. `make check` passes.

## Task Description

### Problem

There is no GitHub counterpart to the Jira and GitLab MCP example pairs, so GitHub users cannot
quickly expose GitHub Actions, pull requests, and issues to agents via PyPost, and there is no
tested guidance on GitHub-specific conventions (API base URL for Enterprise Server, required
headers, owner/repo segments, repository-scoped numbers, token permissions).

### Main business entities

- **GitHub instance** — github.com or GitHub Enterprise Server; identified by its REST API
  base URL.
- **Personal access token** — fine-grained or classic secret credential with permissions or
  scopes; never tracked.
- **Repository** — identified by owner + name; may be a default.
- **Actions objects** — workflow (ID or file name), workflow run, job, dispatch inputs.
- **Pull request** — repository-scoped number; changed files, commits, review comments,
  conversation comments, reviews.
- **Issue** — repository-scoped number; title, body, labels, assignees, state, comments.
- **PyPost artifacts** — collection (requests exposed as MCP tools), environment (variables,
  hidden keys, MCP-overridable keys), example library manifest (collections, variables,
  presets), locked REST path catalog, MCP endpoint (collection + environment served at `/mcp`).

### Scope

In scope:

- New GitHub collection and environment example fixtures, locked REST path catalog, library
  manifest update, user documentation.
- Offline Python tests and a make freshness target validating the fixtures.

Out of scope:

- Any live call to GitHub, live smoke tests, or tests requiring credentials.
- New PyPost runtime features (template functions, auth types, MCP server changes). Existing
  capabilities used by the GitLab collection are expected to suffice; a genuine gap found in
  Step 2 must be justified and kept minimal, or recorded as a follow-up.
- Runtime fail-closed handling of blank path segments (PYPOST-1332) and URL sanitizing in
  generic log events (PYPOST-1333); they apply to this collection too but are tracked there.
- The operations listed as explicit gaps in AC2, the GraphQL API, and GitHub App / OAuth
  authentication.
- Changes to the Jira and GitLab collections/environments other than shared library and
  README edits.
- Replacing any external GitHub MCP server; this is a PyPost-native analog for the in-scope set.

### Constraints and assumptions

- Target API: GitHub REST API; the same paths serve github.com (`https://api.github.com`) and
  GitHub Enterprise Server (`https://<host>/api/v3`).
- Format must match what the current PyPost collection, environment, and library loaders accept
  (same structure as the Jira and GitLab examples).
- Listing tools expose GitHub's documented `page` / `per_page` parameters; automatic
  pagination is not required.
- Write operations without a response body (e.g. dispatch, cancel, re-run) are considered
  successful on GitHub's documented success status; the tool must not require a body to report
  success.
- All repository operations go through `make` targets (AGENTS.md).

## Q&A

- **Q: Why a fixture rather than a runtime integration?** A: The business need is a zero-code,
  importable starting point, consistent with the Jira and GitLab examples; PyPost's MCP
  endpoint already turns collections into tools.
- **Q: Merge pull request?** Open — Step 2 decides (Jira brief: "merge PR if confirmed in
  design"). Either way the coverage table and permission docs must reflect the decision.
- **Q: Which authorization header form?** A: Any GitHub-documented form for PATs is
  acceptable; Step 2 picks one and the checks enforce consistency.
- **Q: Which `X-GitHub-Api-Version`?** Open — Step 2 pins one currently supported version;
  the checks enforce it on every request.
- **Q: One default `owner/repo` variable or two?** Open — the requirement is that owner and
  repository are configurable and encoded as separate path segments; Step 2 chooses the
  variable shape.
- **Q: Repository-wide vs per-workflow run listing?** Open — at least one must exist with a
  workflow filter path; Step 2 decides whether to ship both.
- **Q: Environment file name?** A: Proposed `examples/environments/github.json`; Step 2 may
  rename it as long as docs and tests agree.
- **Q: Exact tool count?** Open — fixed in Step 2 from the AC2 capability table; docs, catalog,
  and parity test must match it.
- References: `examples/collections/gitlab_mcp.json`, `examples/environments/gitlab.json`,
  `examples/collections/gitlab_mcp_rest_paths.json`, `examples/collections/jira_mcp.json`,
  `examples/pypost-library.yaml`, `examples/README.md`, `tests/test_gitlab_mcp_collection.py`,
  `tests/test_predefined_library_pypost_1281_repro.py`, `doc/dev/gitlab_mcp_collection.md`,
  `ai-tasks/PYPOST-1316/`; follow-ups PYPOST-1332, PYPOST-1333.
