# PYPOST-970: Review and Technical Debt

## Review Verdict

**SAFE TO CLOSE.** The scoped implementation satisfies the PYPOST-970 requirements and follows
the approved architecture. No task-owned blocker or follow-up debt was found. Step 8 still needs
to complete the normal developer-documentation update before the overall task can close.

## Review Scope

The review covered all PYPOST-970 artifacts and the task-owned diff in:

- `tests/test_agent_golden_e2e.py`
- `tests/test_agent_e2e_response_panel.py`
- `ai-tasks/PYPOST-970/`

It also inspected the existing shared settle helper, timeout budget, response-panel excerpt, and
PYPOST-950 forced-timeout companion. Production code and shared-helper behavior are unchanged.

## Requirements and Architecture Review

| Requirement | Evidence | Verdict |
| --- | --- | --- |
| FR1 shared success contract | Named Golden success helper calls `wait_response_after_send` | Met |
| FR2 status/body readiness | Unchanged expected values reach the shared helper | Met |
| FR3 both Golden flows | Both success tests use `_golden_fill_send_and_settle` | Met |
| FR4 actionable wrapper | Golden step, prefix, and excerpt are bound explicitly | Met |
| FR5 inner wait evidence | Helper preserves timeout, condition, diagnostics, and chain | Met |
| FR6 forced companion | Intentional `Status: 999` path remains inline and unchanged | Met |
| FR7 agent e2e gate | `make test-agent-e2e`: 109 passed | Met |
| Bounded execution | Module timeouts remain 10 seconds and 60 seconds | Met |
| Current-tab behavior | Golden passes `in_current_tab=True` | Met |
| Minimal scope | One success settle block, two unused imports, and one convention marker | Met |

No architecture deviation was found. The migration uses the existing interface exactly as
designed and does not change the fixture, request interaction, product assertion, helper API, or
production dependency direction.

## Shortcuts Taken

None.

The forced-timeout companion intentionally remains inline. This is the accepted PYPOST-950
failure-path design, not a temporary workaround or incomplete migration: it must force a status
miss and inspect the resulting evidence directly. Routing it through the ordinary successful
settle path would obscure that purpose.

The new AST marker is also intentional. Runtime tests already passed before this task, so a
source-level convention check is the honest regression test for shared-helper adoption. It is
scoped to the named success helper and syntax nodes rather than formatting or whole-file text.

## Code Quality Issues

None found.

- The deleted inline success block has no duplicate remainder.
- Only the two imports made obsolete by that deletion were removed.
- Imports required by the forced-timeout companion remain live.
- Scoped flake8, pyflakes, syntax, line-length, conflict-marker, debug-call, and whitespace
  checks passed in Step 5.
- No new hardcoded timeout was introduced. Golden uses the shared 15-second default.
- The explicit step and message-prefix strings are stable diagnostic identifiers required by the
  preserved contract.
- The companion's existing 50 ms timeout is a deliberate deterministic test budget, not new
  production policy.

## Missing Tests

No blocker or task-owned missing test was identified.

| Contract | Coverage |
| --- | --- |
| Golden imports and calls the shared helper | New scoped AST convention marker |
| Ordinary Golden request/response flow | Existing ordinary Golden success test |
| No-blank-tab/current-tab flow | Existing plus-tab Golden success test |
| Forced timeout step and excerpt | Existing PYPOST-950 companion |
| Forced timeout inner wait evidence | Companion asserts widget ID and expected value |
| Shared status/body order and wrapping | Existing shared-helper coverage and source contract |
| Complete agent e2e selection | 109 tests passed in Step 4 |

Both changed test modules retain explicit `pytest-timeout` markers. There is therefore no
missing-timeout **BLOCKER** under the review rules.

## Performance Concerns

None found.

- The same two status-then-body waits execute through one shared implementation.
- The successful Golden path remains bounded by the existing 15-second per-wait policy and the
  module's 60-second test timeout.
- Current-tab scoping avoids broader window-tree matching.
- The AST marker has no GUI, socket, or external dependency and completes in milliseconds.

## Observability, Diagnostics, and Privacy

The migration preserves the existing `ui_wait_settled` and `ui_wait_timeout` DEBUG events without
adding production telemetry. On failure, the shared helper retains the original timeout,
condition, wait diagnostics, and exception chain, then adds the Golden step and bounded response
excerpt. The focused forced-timeout check passed and continues to verify `step`, excerpt,
`widget_id`, and expected-value evidence.

No response content is added to DEBUG logs. The excerpt remains failure-only, bounded to 400
content characters plus an optional ellipsis, and uses deterministic fixture data in this test.
No new privacy or security concern was introduced.

## Follow-up Tasks

None.

| Item | Priority | Jira action |
| --- | --- | --- |
| Task-owned blocker | None | Do not create |
| Task-owned follow-up debt | None | Do not create |

The full fast suite's artifact-baseline mismatch (committed 259 versus concurrent scan 264) is
unrelated to PYPOST-970. This incomplete task is ignored by that scanner, and the task does not
touch the scanner or baseline. Per review scope, no Jira issue should be created from PYPOST-970
for that external worktree drift.

## Validation Evidence

| Check | Result |
| --- | --- |
| Helper-adoption marker plus forced-timeout diagnostic test | 2 passed in 0.50s |
| Golden module, carried from Step 4 | 3 passed |
| `make test-agent-e2e`, carried from Step 4 | 109 passed, 1956 deselected, 1 existing warning |
| `make test`, carried from Step 4 | 2043 passed, 1 unrelated baseline failure |

The targeted Step 7 command exercised only the convention marker and the PYPOST-950 timeout
companion. No full suite was rerun because the Step 4 acceptance gate is already green and the
remaining fast-suite failure has a documented, unrelated cause.

## Documentation Review

User documentation is not applicable because the task changes test-harness ownership only. The
mandatory Step 8 developer-documentation pass should record Golden as a consumer of the shared
Send-settle convention; that planned workflow step is not technical debt.
