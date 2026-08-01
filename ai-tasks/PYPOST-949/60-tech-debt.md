# PYPOST-949: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

`AgentAppSession.wait_for_text`, `wait_for_widget`, and `wait_for_enabled` accept
optional `in_current_tab=False`; tab-scoped routing reuses `_action_root`.
Multi-tab Send proof in `test_ui_wait.py` demonstrates window-first mismatch and
tab-scoped success. Helper `wait_response_after_send` delegates to session API.
Developer docs updated. No user-facing changes.

## Shortcuts Taken

- **Golden e2e not migrated** to `session.wait_for_text(..., in_current_tab=True)`.
  Inline tab-root free function remains valid and unchanged.
- **Full `make check` not re-run.** Step 5 validated lint + scoped tests (12 passed).
- **`wait_for_snapshot` stays window-only.** Multi-tab proofs use per-tab widget ids.

## Code Quality Issues

None blocking. Implementation mirrors PYPOST-851 action scoping pattern.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Multi-tab Send: window-scoped status wait fails | Covered |
| Multi-tab Send: tab-scoped status/body wait succeeds | Covered |
| Default `in_current_tab=False` regression (single-tab fill wait) | Covered (`test_session_wait_for_text_after_fill`) |
| Tab-scoped `wait_for_widget` / `wait_for_enabled` | Not explicitly covered — low risk (same root routing) |
| Golden rewritten to session tab-scoped waits | Not required |

## Performance Concerns

None. Same poll loop; narrower search subtree when `in_current_tab=True` may
slightly reduce findChild walk cost.

## Follow-up Tasks

| ID | Priority | Task | Acceptance | Jira |
| -- | -------- | ---- | ------------ | ---- |
| TD-1 | Low | Optional golden migration to `session.wait_for_text(..., in_current_tab=True)` | Golden behaviour unchanged; fewer free-function imports | [PYPOST-978](https://pypost.atlassian.net/browse/PYPOST-978) |
| TD-2 | Low | Explicit tests for tab-scoped `wait_for_widget` / `wait_for_enabled` | Multi-tab fixture proves widget/enabled under active tab only | [PYPOST-979](https://pypost.atlassian.net/browse/PYPOST-979) |
| TD-3 | Low | PYPOST-950: align golden timeout-diagnostics lock with text-wait settle | Force text-wait miss with `step` + `response_excerpt` | [PYPOST-950](https://pypost.atlassian.net/browse/PYPOST-950) |

### Ticketed follow-ups

1. **TD-1** — Golden session API migration (cosmetic DRY).
   Priority: Low. Jira: [PYPOST-978](https://pypost.atlassian.net/browse/PYPOST-978)
2. **TD-2** — Tab-scoped widget/enabled integration tests.
   Priority: Low. Jira: [PYPOST-979](https://pypost.atlassian.net/browse/PYPOST-979)

## User documentation

N/A — developer docs only (`doc/dev/ui_wait.md`, `agent_e2e_send_settle.md`).

## Blocker Review

**SAFE TO CLOSE** — Acceptance criteria met: tab-scoped `wait_for_text` API on
session, tested multi-tab Send proof, related waits aligned, docs updated.
Listed gaps are non-blocking follow-ups.

## Worklog

```
tokens_used: 8000
role: execution
step: 7
step_name: Review
```
