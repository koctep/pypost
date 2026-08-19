# PYPOST-1083: Stop deep-copying every MCP server row just to log a dialog-open count

## Goals

This task addresses technical debt identified during PYPOST-1071 (follow-up F7, source item
D5 in [ai-tasks/PYPOST-1071/60-tech-debt.md](../PYPOST-1071/60-tech-debt.md)). The business
goals are:

- **Avoid unnecessary work on a user-initiated action**: opening the MCP servers management
  dialog currently performs a full, independent duplication of every configured MCP server
  entry solely to produce a count for a log line. That duplication is pure overhead — the
  same information (the count) is available without copying anything.
- **Keep the codebase's cost model honest**: a call that reads as "fetch the server rows" is
  standing in for "count the server rows," which misleads anyone reading or extending this
  code path about what is actually needed and how expensive it is.
- **Consistency with sibling behavior already in the same component**: the neighboring
  dialog-open actions in the same MCP control bar already log an open count without
  duplicating the underlying data; the multi-server manager should follow the same low-cost
  pattern.
- **Protect future scalability of this code path**: today's server counts are small enough
  that the wasted work is unmeasurable, but the fix removes an inefficiency that would
  otherwise scale linearly with every future MCP endpoint a user configures, rather than
  leaving it to be rediscovered later.

## User Stories

- **As a maintainer**, I want the MCP servers dialog-open log to report its count without
  duplicating every configured server row, so that a routine, user-initiated UI action does
  not perform hidden, unnecessary work.
- **As a maintainer**, I want logging code to only do as much work as producing the logged
  value requires, so that reading a log statement does not misrepresent its actual cost and
  future contributors are not misled into copying that pattern elsewhere.
- **As an application user**, I want opening the MCP servers dialog to remain fast and to
  behave exactly as it does today (same dialog contents, same log line, same server list),
  so that this internal efficiency change is invisible to me.

## Definition of Done

- Opening the MCP servers dialog no longer performs a full duplication of the configured
  server rows for the sole purpose of logging their count.
- The `mcp_servers_dialog_opened` log entry continues to report the correct number of
  configured MCP servers, unchanged in wording, level, and meaning from today's behavior.
- The MCP servers dialog continues to receive and display the full, correct set of
  configured server rows exactly as before — no user-visible behavior changes.
- No other caller or code path that relies on the existing row-fetching behavior is broken or
  altered.
- All existing automated tests continue to pass, and this change is covered by an automated
  test that asserts the log count is correct and that the wasteful duplication no longer
  occurs on this path.

## Task Description

### Problem Statement

When a user opens the MCP servers management dialog, the component responsible for that
dialog currently fetches the full list of configured MCP server entries twice: once purely to
compute how many servers are configured (for an informational log entry), and a second time
to actually supply the dialog with the data it displays. The first of these two fetches
returns independent copies of every configured server entry, even though only a count is
needed. This is unnecessary work performed on every dialog open, and it is out of proportion
to what the log statement requires.

This was identified as low-severity, non-blocking technical debt during the prior extraction
task (PYPOST-1071) that created this dialog-opening code path, and is being addressed now as
a scheduled, standalone follow-up.

### Scope & System Boundaries

- **In Scope**:
  - The way the dialog-open count is obtained for the `mcp_servers_dialog_opened` log entry.
- **Out of Scope**:
  - The MCP servers dialog's displayed contents, layout, or interaction behavior.
  - The log entry's wording, level, or the information it conveys to the user/operator
    (only how the count is computed changes, not what is logged).
  - Any other MCP server configuration, persistence, lifecycle, or activity behavior.
  - Any other item recorded in PYPOST-1071's technical debt analysis (each has its own
    follow-up task).

### Constraints & Assumptions

- **Implementation language**: Python (matches the rest of the affected component).
- **Behavior preservation**: the dialog's contents, the log entry's meaning, and every other
  observable behavior of opening the MCP servers dialog must remain identical from the
  user's and operator's perspective.
- **Low risk, low volume**: this is a user-initiated, single-click action, and the number of
  configured MCP servers is expected to remain in the single digits in practice, so the
  practical performance impact of the current behavior is negligible. The business case is
  code-quality and future-proofing, not a measured performance problem.
- **Assumption**: this task may be delivered together with the related follow-up (PYPOST-1080
  scope) that adds dedicated automated test coverage for this dialog-open action, since that
  coverage is the natural place to also assert this behavior; delivering it independently is
  also acceptable.

### Main Business Entities

- **MCP Server Configuration Row**: one persisted, user-configured MCP endpoint (its settings
  and identity), as displayed in the MCP servers dialog.
- **MCP Servers Dialog**: the UI surface a user opens to view, add, edit, remove, start, and
  stop their configured MCP server endpoints.
- **Dialog-Open Log Event**: the operator-facing log record produced each time a user opens
  the MCP servers dialog, reporting how many servers are currently configured.

## Q&A

### Why does this matter if the row counts are always small?

The business reason is not a measured performance problem today — it is preventing avoidable
technical debt from compounding. The unnecessary duplication scales with every server a user
configures, sets a pattern that could be copied into costlier contexts, and misrepresents the
actual cost of the log statement to anyone reading the code. Source: PYPOST-1071 technical
debt item D5.

### Does this change what gets logged or what the dialog shows?

No. The log entry's meaning (a count of configured MCP servers) and the dialog's displayed
contents are both required to stay exactly as they are today. Only how the count is obtained
changes.

### What programming language is used for implementation?

Python.

### Is this task related to any other open follow-up?

Yes. It is one of several sibling follow-ups (F1–F11) recorded in PYPOST-1071's technical
debt analysis. The analysis suggests pairing this task with the follow-up that adds dedicated
test coverage for the dialog-open action (PYPOST-1080 scope), since that coverage is the
natural place to assert this behavior, but this task's Definition of Done stands on its own
and does not require that other task to be delivered first.
