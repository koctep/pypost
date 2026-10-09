# Example Collection Library, collections, and environments

This directory functions as a self-contained **Collection Library** (configured via [`pypost-library.yaml`](pypost-library.yaml)) as well as providing standalone importable fixtures you can load into PyPost, fill with your own values, and adapt.

## Git Collection Library

You can clone or connect this repository directly into PyPost via the **Library Manager** (`Ctrl+Shift+L` or **File → Library Manager...**).

The library manifest [`pypost-library.yaml`](pypost-library.yaml) declares:
- Metadata (`id`, `name`, `version`, `description`)
- Bundled collections ([`collections/jira_mcp.json`](collections/jira_mcp.json), [`collections/gitlab_mcp.json`](collections/gitlab_mcp.json), [`collections/github_mcp.json`](collections/github_mcp.json), [`collections/mcp.json`](collections/mcp.json))
- Default variable schemas with secrets isolation
- Profile presets (`jira_cloud`, `gitlab_com`, `github_com`); presets never carry tokens

## Standalone Inventory

- [`collections/jira_mcp.json`](collections/jira_mcp.json) — **End users.**
  Curated Jira Cloud MCP collection (22 REST tools): issue search/CRUD,
  transitions, worklog, fields, comments, assign, epic/parent link, boards,
  sprints (list/create/update/delete/membership), backlog, and
  assignable-user search.
- [`collections/jira_mcp_critical_rest_paths.json`](collections/jira_mcp_critical_rest_paths.json)
  — **Contributors.** Locked critical REST path catalog for offline freshness
  checks (`make check-jira-mcp-path-freshness`; see
  [doc/dev/jira_mcp_path_freshness.md](../doc/dev/jira_mcp_path_freshness.md)).
  Not an importable collection.
- [`environments/jira_cloud.json`](environments/jira_cloud.json) — **End users.**
  Companion environment: `jira_base_url`, visible `jira_project_key`, hidden `jira_credentials`.
  Its retained `enable_mcp: true` field is legacy migration input.
- [`collections/gitlab_mcp.json`](collections/gitlab_mcp.json) — **End users.**
  Curated GitLab MCP collection (25 REST tools) for GitLab.com and self-managed
  GitLab: current user, projects, branches, repository files and tree, commits,
  issues, merge requests, issue and merge request comments, pipelines, and jobs.
- [`collections/gitlab_mcp_rest_paths.json`](collections/gitlab_mcp_rest_paths.json)
  — **Contributors.** Locked REST method and path catalog for all 25 GitLab tools,
  checked offline by `make check-gitlab-mcp-path-freshness`. Not an importable
  collection.
- [`environments/gitlab.json`](environments/gitlab.json) — **End users.**
  Companion environment: `gitlab_base_url`, visible MCP-overridable `gitlab_project`,
  hidden `gitlab_token`. Its retained `enable_mcp: true` field is legacy migration input.
- [`collections/github_mcp.json`](collections/github_mcp.json) — **End users.**
  Curated GitHub MCP collection (30 REST tools) for github.com and GitHub Enterprise
  Server: authenticated user, repository, Actions workflows, runs and jobs (dispatch,
  re-run, cancel), pull requests (files, commits, review comments, conversation
  comments, reviews), issues, and issue comments.
- [`collections/github_mcp_rest_paths.json`](collections/github_mcp_rest_paths.json)
  — **Contributors.** Locked REST method, path and API version catalog for all 30 GitHub
  tools, checked offline by `make check-github-mcp-path-freshness`. Not an importable
  collection.
- [`environments/github.json`](environments/github.json) — **End users.**
  Companion environment: `github_api_url`, visible MCP-overridable `github_owner` and
  `github_repo`, hidden `github_token`. Its retained `enable_mcp: true` field is legacy
  migration input.
- [`collections/mcp.json`](collections/mcp.json) — **Contributors / local
  probing.** Local MCP/SSE probe against PyPost ports (`127.0.0.1:1080` /
  `9080`); used by test helpers. Not the primary “learn Jira + MCP” starter.
- [`collections/google_drive.json`](collections/google_drive.json) — **End users.**
  Curated Google Drive API v3 collection demonstrating file listing, metadata retrieval,
  binary content download, file creation, multipart and resumable uploads, and file sharing
  permissions.

### Google Drive resumable uploads

The Google Drive collection includes a two-stage resumable-upload example for large files:

1. Run **Start Resumable File Upload**. It sends JSON metadata to the Google Drive v3 upload
   endpoint and returns a short-lived session URL in the response `Location` header.
2. Copy that opaque `Location` value into `google_drive_upload_session_url`, replace the example
   chunk body with file content, and run **Upload File Chunk (Resumable)**.
3. Update `google_drive_chunk_start`, `google_drive_chunk_end`, `google_drive_chunk_length`, and
   `google_drive_file_size` for each subsequent chunk. A `308 Resume Incomplete` response means
   more content is needed; `200 OK` or `201 Created` indicates completion.

The fixture is a request reference, so it does not perform automatic chunking, retries, or live
credential setup. Keep the access token private and treat the returned session URL as sensitive.


## Recommended import order (Jira Cloud pair)

1. **Import the environment** — **Manage Environments → Import…** and choose
   `examples/environments/jira_cloud.json`.
2. **Replace placeholders locally** (do not commit real secrets):
   - `jira_base_url` — your site, for example
     `https://your-company.atlassian.net`
   - `jira_project_key` — set this to the Jira project key, ID, or comma-separated
     project list (e.g. `PROJ1, PROJ2`) that should guide normal issue search,
     issue creation, and board discovery
   - `jira_credentials` — `email:api_token` (Atlassian account email and an
     API token from Atlassian account settings); keep the key **Hidden**
3. **Import the collection** — **Import Collection…** and choose
   `examples/collections/jira_mcp.json`.
4. **Select** the **Jira Cloud MCP** environment in the top dropdown for manual GUI sends.
5. **Create and start an endpoint** — open **MCP Servers…**, add a row selecting the Jira
   collection and Jira Cloud MCP environment, choose a unique host/port, then click **Start**.
   Point the agent at that row's `/mcp` URL. The example's `enable_mcp: true` is migration
   input only.

Auth in the collection matches Atlassian Cloud basic auth for REST APIs:
`Authorization: Basic {{ base64(jira_credentials) }}`.

`jira_project_key` is a soft default for normal work. It is not an authorization
and not a security boundary or permission control. A user may deliberately work
in a different project when their Jira permissions allow it. Board discovery uses
the project-aware Jira parameter; board and sprint follow-up tools keep the
scope of the selected board or sprint rather than simulating a project lock.

## Board and sprint identifier input (PYPOST-1038)

The Jira MCP tools below accept their board or sprint ID in either normal JSON
form: a native integer such as `42` or a decimal string such as `"42"`. This
helps agents and clients that naturally serialize numeric identifiers as
strings, without changing existing native-number clients.

| MCP tool | Argument |
| --- | --- |
| `jira_list_board_sprints` | `board_id` |
| `jira_get_sprint` | `sprint_id` |
| `jira_update_sprint` | `sprint_id` |
| `jira_delete_sprint` | `sprint_id` |
| `jira_add_issues_to_sprint` | `sprint_id` |
| `jira_get_sprint_issues` | `sprint_id` |

Use only a decimal integer representation. Booleans, floats, whitespace-padded
or exponent-form values, and nonnumeric strings are invalid and are rejected
before a Jira HTTP request is sent. This applies only to the listed path IDs;
JSON payload arguments such as `issues_payload` remain serialized JSON strings.

## Coverage vs gaps

This collection is a **practical analog** of the Atlassian MCP Jira surface
used by in-repo agent skills and workflows — not a full dump of every Jira
Cloud or Atlassian MCP tool.

**Included (MCP-exposed requests):**

| Area | Request ids |
| ---- | ----------- |
| Search / fields | `jira-search-issues-jql`, `jira-search-fields` |
| Issue lifecycle | `jira-get-issue`, `jira-create-issue`, `jira-update-issue` |
| Workflow | `jira-get-transitions`, `jira-transition-issue` |
| Comments / assign | `jira-add-comment`, `jira-assign-issue` |
| Assignable users | `jira-search-assignable-users` |
| Worklog | `jira-add-worklog`, `jira-get-worklog` |
| Epic / parent | `jira-link-issue-parent` (uses `fields.parent`) |
| Boards / sprint read | `jira-list-boards`, `jira-list-board-sprints`, `jira-get-sprint` |
| Sprint write | `jira-create-sprint`, `jira-update-sprint`, `jira-delete-sprint` |
| Sprint issues | `jira-get-sprint-issues` |
| Sprint membership | `jira-add-issues-to-sprint`, `jira-move-issues-to-backlog` |

`jira-move-issues-to-backlog` is the supported remove-from-sprint path (capped at ≤50 issues
per batch by Jira Agile).

**Explicit gaps** (out of scope unless added later):

- Service Desk / JSM (queues, request types, customer requests)
- ProForma forms and answers
- Watchers, attachments/images, delete issue
- Remote/issue-link CRUD beyond epic-parent linking
- Versions/components batch APIs, SLA, development info
- Cross-project dependencies and customer-facing comment flags
- `jira_batch_create_issues` (skills deliberately avoid batch create)

External Atlassian MCP may remain configured for agents; these fixtures do not
replace that server — they ship a PyPost-native analog for the in-scope set.

## Recommended import order (GitLab pair)

1. **Import the environment** — **Manage Environments → Import…** and choose
   `examples/environments/gitlab.json`.
2. **Replace placeholders locally** (do not commit real secrets):
   - `gitlab_base_url` — `https://gitlab.com` or your self-managed instance URL
   - `gitlab_project` — the default project as a numeric ID (for example `42`) or a
     full path (for example `your-group/your-project`)
   - `gitlab_token` — your access token in place of `your-gitlab-access-token`;
     keep the key **Hidden**
3. **Import the collection** — **Import Collection…** and choose
   `examples/collections/gitlab_mcp.json`.
4. **Select** the **GitLab MCP** environment in the top dropdown for manual GUI sends.
5. **Create and start an endpoint** — open **MCP Servers…**, add a row selecting the GitLab
   collection and GitLab MCP environment, choose a unique host/port, then click **Start**.
   Point the agent at that row's `/mcp` URL. The example's `enable_mcp: true` is migration
   input only.

When you attach the library instead, apply the `gitlab_com` preset and enter the token
in the secret `gitlab_token` variable.

## GitLab authentication

- Use a personal, project or group access token. Choose the `read_api` scope for
  read-only tools and the `api` scope when the agent must create or update issues,
  merge requests or comments.
- Enter the token only in the hidden key `gitlab_token`. It is never published in
  an MCP tool schema and cannot be overridden by the agent.
- Every request sends `Authorization: Bearer {{ gitlab_token }}`, which GitLab accepts for
  personal, project and group access tokens. PyPost redacts `Authorization` headers and
  `Bearer` values in logs and MCP results.
- GitLab also accepts the `PRIVATE-TOKEN: <token>` header. If you prefer it, edit the
  header in your imported copy; note that PyPost then masks the token only by its hidden
  value, not by header name.

## GitLab.com vs self-managed

- GitLab.com: keep `gitlab_base_url` set to `https://gitlab.com`.
- Self-managed GitLab: set `gitlab_base_url` to your instance URL, including any
  sub-path (for example `https://git.example.com/gitlab`), with no trailing slash.
  Every tool appends `/api/v4/...` to it.
- Both expose the same REST API v4 and token headers, so one environment covers both.
  TLS certificates, proxies and network access to the instance are your concern.

## GitLab default project and identifiers

- `gitlab_project` is a soft default for normal work. It is not a security boundary
  or permission control. Every project-scoped tool publishes an optional
  `gitlab_project` argument, so the agent can target any other project the token can
  access. A blank default is not supported for project-scoped tools: keep a value
  configured or pass `gitlab_project` on every call.
- A project is identified by its numeric ID (`42`) or its full path
  (`group/subgroup/project`). The path is URL-encoded automatically
  (`group%2Fsubgroup%2Fproject`).
- Issues and merge requests use the project-scoped **IID** (`issue_iid`,
  `merge_request_iid`), the number shown in the UI. Pipelines and jobs use their
  global numeric ID (`pipeline_id`, `job_id`). These arguments accept a native integer
  or a decimal string; any other value is rejected before an HTTP request is sent.
- File paths, branch names and commit references in the URL path are encoded as one
  path segment (`src/app/main.py` → `src%2Fapp%2Fmain.py`, `feature/x` → `feature%2Fx`).
  Query values such as `ref` and `search` are sent as raw values and encoded once by
  the HTTP client.
- Limitation: a file path, branch or SHA that is exactly `.` or `..` is not supported,
  because dots are not encoded and such a dot segment may be normalised away. Git does
  not allow these names, so valid input does not reach this case.

## GitLab coverage vs gaps

The GitLab collection is a practical subset of GitLab REST API v4 for agent workflows,
not a full dump of the API.

**Included (25 MCP tools):**

| Area | MCP tools |
| ---- | --------- |
| Identity | `gitlab_get_current_user` |
| Projects | `gitlab_list_projects`, `gitlab_get_project` |
| Branches | `gitlab_list_branches`, `gitlab_get_branch` |
| Files | `gitlab_get_file`, `gitlab_list_repository_tree` |
| Commits | `gitlab_list_commits`, `gitlab_get_commit` |
| Issues | `gitlab_list_issues`, `gitlab_get_issue`, `gitlab_create_issue`, `gitlab_update_issue` |
| Merge requests | `gitlab_list_merge_requests`, `gitlab_get_merge_request`, `gitlab_create_merge_request`, `gitlab_update_merge_request` |
| Comments | `gitlab_list_issue_notes`, `gitlab_create_issue_note`, `gitlab_list_merge_request_notes`, `gitlab_create_merge_request_note` |
| CI/CD | `gitlab_list_pipelines`, `gitlab_get_pipeline`, `gitlab_list_pipeline_jobs`, `gitlab_get_job` |

List tools accept `page` (default `1`) and `per_page` (default `20`). `gitlab_get_file`
returns the raw file content as decoded text, so binary or very large files are not
suitable (responses are also subject to the existing `max_response_bytes` size cap).

**Explicit gaps** (out of scope unless added later):

- Delete operations of any kind
- Merging or approving merge requests, diffs and discussions (threaded review comments)
- Writing repository files, commits, branches or tags
- Triggering, retrying or cancelling pipelines and jobs; job logs and artifacts
- Groups, users and members administration, wikis, releases, packages and registries
- Webhooks, project settings and access token management

## Recommended import order (GitHub pair)

1. **Import the environment** — **Manage Environments → Import…** and choose
   `examples/environments/github.json`.
2. **Replace placeholders locally** (do not commit real secrets):
   - `github_api_url` — `https://api.github.com` for github.com, or
     `https://<host>/api/v3` for GitHub Enterprise Server
   - `github_owner` and `github_repo` — the default repository (for example `octo-org`
     and `hello-world`) in place of `your-org` and `your-repo`
   - `github_token` — your personal access token in place of `your-github-token`;
     keep the key **Hidden**
3. **Import the collection** — **Import Collection…** and choose
   `examples/collections/github_mcp.json`.
4. **Select** the **GitHub MCP** environment in the top dropdown for manual GUI sends.
5. **Create and start an endpoint** — open **MCP Servers…**, add a row selecting the GitHub
   collection and GitHub MCP environment, choose a unique host/port, then click **Start**.
   Point the agent at that row's `/mcp` URL. The example's `enable_mcp: true` is migration
   input only.

When you attach the library instead, apply the `github_com` preset and enter the token
in the secret `github_token` variable.

## GitHub authentication

- Prefer a **fine-grained** personal access token limited to the repositories the agent
  needs. Minimum repository permissions per tool group:
  - Repository and identity: Metadata read (always granted) for the repository lookup;
    the authenticated-user lookup (`GET /user`) needs no repository permission
  - Actions: Actions read for workflows, runs and jobs; Actions write to dispatch,
    re-run or cancel runs
  - Pull requests: Pull requests read; Pull requests write to create or update pull
    requests, review comments, replies and reviews
  - Issues and conversation comments: Issues read; Issues write to create or update
    issues and comments (conversation comments on a pull request accept Issues or Pull
    requests write)
- A **classic** personal access token needs the `repo` scope. `github_dispatch_workflow`,
  `github_rerun_workflow_run` and `github_cancel_workflow_run` require `repo` even on public
  repositories. For every other tool, `public_repo` is enough on public repositories only
  (the Actions read tools need `repo` only for private repositories).
- Merging pull requests is not part of the collection; it would also need Contents write.
- Enter the token only in the hidden key `github_token`. It is never published in an MCP
  tool schema and cannot be overridden by the agent.
- Every request sends `Authorization: Bearer {{ github_token }}`,
  `Accept: application/vnd.github+json` and the pinned `X-GitHub-Api-Version: 2022-11-28`.
  PyPost redacts `Authorization` headers and `Bearer` values in logs and MCP results.
- GitHub also accepts the `Authorization: token <token>` form. If you prefer it, edit the
  header in your imported copy.

## GitHub.com vs GitHub Enterprise Server

- github.com: keep `github_api_url` set to `https://api.github.com`.
- GitHub Enterprise Server: set `github_api_url` to `https://<host>/api/v3` (the REST API
  base, not the web URL), with no trailing slash.
- Both use the same REST paths and headers, so one environment covers both. API version
  `2022-11-28` is the one version supported by github.com and every supported GitHub
  Enterprise Server release. TLS certificates, proxies and network access to the server
  are your concern.

## GitHub default repository and identifiers

- `github_owner` and `github_repo` are a soft default for normal work. They are not a
  security boundary or permission control. Every repository-scoped tool publishes
  optional `github_owner` and `github_repo` arguments, so the agent can target any other
  repository the token can access. A blank default is not supported: keep values
  configured or pass both arguments on every call.
- Owner and repository are URL-encoded as one path segment each, so a value cannot add
  or split path segments.
- Pull requests and issues use the repository-scoped **number** shown in the UI
  (`pull_number`, `issue_number`), not a global ID. Runs, jobs and comments use their
  numeric ID (`run_id`, `job_id`, `comment_id`). These arguments accept a native integer
  or a decimal string; any other value is rejected before an HTTP request is sent.
- `workflow_id` accepts the numeric workflow ID as a decimal string or the workflow file
  name (`ci.yml`); it is encoded as one path segment.
- Query values such as `branch`, `head` (`user:branch`) and `labels` are sent as raw
  values and encoded once by the HTTP client. `labels` is a comma-separated string when
  listing issues, but a JSON array of strings when creating or updating an issue (an
  empty array clears all labels).
- Limitation: an owner, repository or workflow file name that is exactly `.` or `..` is
  not supported, because dots are not encoded. GitHub does not allow these names.

## GitHub coverage vs gaps

The GitHub collection is a practical subset of the GitHub REST API for agent workflows,
not a full dump of the API.

**Included (30 MCP tools):**

| Area | MCP tools |
| ---- | --------- |
| Identity | `github_get_authenticated_user` |
| Repository | `github_get_repository` |
| Actions workflows | `github_list_workflows`, `github_dispatch_workflow` |
| Actions runs | `github_list_workflow_runs`, `github_list_workflow_runs_for_workflow`, `github_get_workflow_run`, `github_rerun_workflow_run`, `github_cancel_workflow_run` |
| Actions jobs | `github_list_workflow_run_jobs`, `github_get_workflow_job` |
| Pull requests | `github_list_pull_requests`, `github_get_pull_request`, `github_create_pull_request`, `github_update_pull_request` |
| Pull request contents | `github_list_pull_request_files`, `github_list_pull_request_commits` |
| Pull request review comments | `github_list_pull_request_review_comments`, `github_create_pull_request_review_comment`, `github_reply_to_pull_request_review_comment` |
| Pull request conversation comments | `github_list_pull_request_comments`, `github_create_pull_request_comment` |
| Pull request reviews | `github_list_pull_request_reviews`, `github_create_pull_request_review` |
| Issues | `github_list_issues`, `github_get_issue`, `github_create_issue`, `github_update_issue` |
| Issue comments | `github_list_issue_comments`, `github_create_issue_comment` |

List tools accept `page` (default `1`) and `per_page` (default `30`, GitHub max `100`).
Closing and reopening use the update tools with `state`. For
`github_create_pull_request_review`, `event` is required and must be `APPROVE`,
`REQUEST_CHANGES` or `COMMENT`; the review is submitted on create. Issue listing also
returns pull requests (GitHub behaviour).

**Explicit gaps** (out of scope unless added later):

- Delete operations of any kind
- Merging pull requests (irreversible; add
  `PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge` to your imported copy if needed)
- Pending (draft) reviews and submitting a pending review
  (`POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews/{review_id}/events`); reading
  one review by ID
- Workflow run details from dispatch (`return_run_details`); find the run with the run
  listing tools instead
- Job logs, artifacts, caches, secrets and variables of GitHub Actions
- Writing repository files, commits, branches, tags or releases
- Organization, team, member, webhook and repository settings administration

## Secret handling

- Committed fixtures contain **placeholders only** (sample site URL and
  `you@example.com:your-api-token`; for GitLab, `your-gitlab-access-token`; for GitHub,
  `your-github-token`). Never put real API tokens or passwords in git, such as GitHub
  `ghp_…` or `github_pat_…` tokens.
- After import, substitute your own values in PyPost (or in a private copy of the
  JSON). Keep credential keys in `hidden_keys`.
- Local runtime data under `collections/` and `environments.json` stays
  gitignored; only the tracked files under
  `examples/{collections,environments}/` are source-controlled fixtures.

## Role of `mcp.json`

Use `collections/mcp.json` when you are developing or probing PyPost’s own
MCP/SSE endpoints locally. For a ready-to-adapt Jira Cloud + MCP workflow, use
the `jira_mcp.json` + `jira_cloud.json` pair instead; for GitLab, use the
`gitlab_mcp.json` + `gitlab.json` pair; for GitHub, use the `github_mcp.json` +
`github.json` pair.
