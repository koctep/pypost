# PYPOST-1222: Observability Implementation

## Logging Implementation

Structured, syslog-compatible logging was implemented across `pypost/core/git_auth.py` and `pypost/core/git_service.py` to provide visibility into Git repository lifecycle events, authentication setup, and safety guard executions without leaking sensitive credentials.

### Added Logs

- **ERR**:
  - `pypost/core/git_service.py:_run_git` — `git_binary_not_found`: Logged when the git executable is missing from system PATH (`binary=%s error=%s`).
  - `pypost/core/git_service.py:_run_git` — `git_command_timeout`: Logged when a git subprocess times out (`subcommand=%s timeout=%s`).
  - `pypost/core/git_service.py:clone` — `git_clone_failed`: Logged when repository clone fails (`url=%s code=%s stderr=%s`, with URL credentials masked).
  - `pypost/core/git_service.py:fetch` — `git_fetch_failed`: Logged when remote reference fetch fails (`library_id=%s code=%s stderr=%s`).
  - `pypost/core/git_service.py:pull` — `git_pull_failed`: Logged when remote pull fails (`library_id=%s code=%s stderr=%s`).
  - `pypost/core/git_service.py:checkout` — `git_checkout_failed`: Logged when branch switch/creation fails (`library_id=%s branch=%s code=%s stderr=%s`).

- **WARNING**:
  - `pypost/core/git_auth.py:build_env` — `git_auth_cleanup_failed`: Logged when askpass temporary directory removal fails (`error=%s`).
  - `pypost/core/git_service.py:check_dirty` — `git_status_check_failed`: Logged when porcelain status check returns non-zero (`repo=%s stderr=%s`).
  - `pypost/core/git_service.py:clone` — `git_clone_destination_not_empty`: Logged when destination directory exists and is not empty (`path=%s`).
  - `pypost/core/git_service.py:pull` — `git_pull_blocked_dirty_tree`: Logged when pull is prevented due to uncommitted local edits (`library_id=%s files=%s`).
  - `pypost/core/git_service.py:checkout` — `git_checkout_blocked_dirty_tree`: Logged when branch checkout is prevented due to dirty tree (`library_id=%s files=%s`).
  - `pypost/core/git_service.py:list_branches` — `git_list_branches_failed`: Logged when branch enumeration command fails (`library_id=%s stderr=%s`).

- **INFO**:
  - `pypost/core/git_service.py:clone` — `git_clone_started`: Logged when clone initiates (`library_id=%s url=%s branch=%s force=%s`, with masked credentials in URL).
  - `pypost/core/git_service.py:clone` — `git_clone_force_clearing_destination`: Logged when force clone cleans existing destination directory (`path=%s`).
  - `pypost/core/git_service.py:clone` — `git_clone_success`: Logged upon successful clone completion (`library_id=%s path=%s manifest=%s`).
  - `pypost/core/git_service.py:fetch` — `git_fetch_started`: Logged when remote fetch initiates (`library_id=%s remote=%s`).
  - `pypost/core/git_service.py:fetch` — `git_fetch_success`: Logged upon successful fetch completion (`library_id=%s remote=%s`).
  - `pypost/core/git_service.py:pull` — `git_pull_started`: Logged when pull initiates (`library_id=%s remote=%s branch=%s force=%s`).
  - `pypost/core/git_service.py:pull` — `git_pull_success`: Logged upon successful pull completion (`library_id=%s remote=%s`).
  - `pypost/core/git_service.py:checkout` — `git_checkout_started`: Logged when checkout initiates (`library_id=%s branch=%s create=%s force=%s`).
  - `pypost/core/git_service.py:checkout` — `git_checkout_success`: Logged upon successful checkout (`library_id=%s branch=%s`).
  - `pypost/core/git_service.py:delete_library` — `git_library_deleted`: Logged when library storage directory is deleted (`library_id=%s path=%s`).

- **DEBUG**:
  - `pypost/core/git_auth.py:build_env` — `git_auth_mode_configured`: Logged when auth environment is constructed (`mode=%s username=%s has_token=%s` or `key_path=%s strict_host_checking=%s has_passphrase=%s`).
  - `pypost/core/git_auth.py:build_env` — `git_auth_askpass_created`: Logged when ephemeral askpass helper script is generated (`mode=%s path=%s`).
  - `pypost/core/git_auth.py:build_env` — `git_auth_askpass_cleaned`: Logged when ephemeral askpass script and directory are deleted (`mode=%s path=%s`).
  - `pypost/core/git_auth.py:transient_git_auth_env` — `transient_git_auth_env_entered` / `transient_git_auth_env_exited`: Logged upon entering/exiting transient environment scope (`mode=%s`).
  - `pypost/core/git_service.py:check_dirty` — `git_check_dirty_started`, `git_check_dirty_skipped_no_repo`, `git_dirty_tree_detected`, `git_dirty_tree_clean`: Logged during working tree dirty checks.
  - `pypost/core/git_service.py:discover_manifest` — `git_manifest_discovery_started`, `git_manifest_discovered`, `git_manifest_not_found`: Logged during collection library manifest discovery.
  - `pypost/core/git_service.py:status` — `git_status_started`, `git_status_completed`: Logged with branch, clean flag, ahead/behind counts, and file modification counts.
  - `pypost/core/git_list_branches` — `git_list_branches_started`, `git_list_branches_completed`: Logged with branch count.
  - `pypost/core/git_service.py:delete_library` — `git_library_delete_skipped_not_found`: Logged when requested directory for deletion does not exist.

### Log Structure

Log format used:
- Structured logs: yes (key=value formatting with standardized event prefixes)
- Includes context: yes (library ID, branch, path, sanitized URL, exit codes, modification counts)
- Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`

### Credential Protection & Redaction

- Personal Access Tokens (`PAT`), SSH key passphrases, and raw private key contents are **never written to log records**.
- Only boolean indicator flags (`has_token=True/False`, `has_passphrase=True/False`), usernames, and filepaths are logged.
- `sanitize_git_url` strips embedded basic auth (`https://***:***@host/...`) from URLs before writing to logs or error diagnostics.
- Subprocess command logging avoids printing full argument vectors that might contain secrets, logging subcommand names and timeouts only.

## Metrics Implementation (if applicable)

### Performance Metrics

- **Subprocess timeout boundaries**: Configurable bounded timeout per command execution (`default_timeout=30.0s`, status/branch inspect `5.0s`, checkout `10.0s`).
- Git operations run as subprocesses isolated from the main event loop.

### Business Metrics

- **Git operation outcomes**: Structured `GitOperationResult` returned with `success`, `operation`, `library_id`, `repo_path`, and `manifest_path`.
- **Diagnostic classifications**: Structured error mapping (`GitDiagnosticErrorCode`: `AUTH_FAILED`, `REPO_NOT_FOUND`, `BRANCH_NOT_FOUND`, `MERGE_CONFLICT`, `DIRTY_WORKING_TREE`, `DESTINATION_NOT_EMPTY`, `TIMEOUT`, `GIT_NOT_INSTALLED`, `COMMAND_FAILED`).

### System Health Metrics

- **Working tree clean status**: `GitRepoStatus.is_clean`, `ahead_count`, `behind_count`, `dirty_files`, `untracked_files`.
- **Ephemeral credential lifecycle**: Guaranteed cleanup via `transient_git_auth_env` context managers and callback chains.

## Monitoring Integration

- [x] Structured logger integration compatible with Python `logging` handlers and standard syslog/ELK log shippers
- [x] Diagnostic error model with structured codes for programmatic alerting and UI display

## Validation Results

- [x] Logs are correctly formatted with key=value structured event identifiers
- [x] Logging works in error scenarios (auth failures, timeout, dirty working tree, missing executable)
- [x] Large data structures are not logged (counts and file paths only)
- [x] Sensitive credentials (PAT tokens, passphrases) are never leaked in logs
- [x] Automated unit tests verify structured logging events and URL credential masking (`tests/test_git_library_service_repro.py`)

## Notes

- All Git authentication operations use non-interactive guards (`GIT_TERMINAL_PROMPT=0`, `GIT_FLUSH=1`) and ephemeral credential helpers created with restrictive permissions (`0o700`).
