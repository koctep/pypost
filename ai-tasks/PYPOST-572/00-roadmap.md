# Roadmap: PYPOST-572

Implement CI log allowlist and post-run verifier (Phase 1 of PYPOST-571 guardrails).

Recommended branch: `feature/PYPOST-572-log-guardrails`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] `tests/expected_log_allowlist.yaml`
  - [x] `scripts/verify_test_log_guardrails.py`
  - [x] `tests/test_verify_test_log_guardrails.py`
  - [x] `.github/workflows/test.yml` CI wiring
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Artifacts

| Step | File |
| --- | --- |
| 1 | `ai-tasks/PYPOST-572/10-requirements.md` |
| 2 | `ai-tasks/PYPOST-572/20-architecture.md` |
| 3 | allowlist, verifier script, unit tests, workflow |
| 4 | `ai-tasks/PYPOST-572/40-code-cleanup.md` |
| 5 | `ai-tasks/PYPOST-572/50-observability.md` |
| 6 | `ai-tasks/PYPOST-572/60-tech-debt.md` |
| 7 | `ai-tasks/PYPOST-572/70-dev-docs.md`, `doc/dev/testing.md` |

## Related Work

- Parent proposal: [PYPOST-571](../PYPOST-571/ci-guardrails-proposal.md)
- Baseline inventory: [PYPOST-567](../PYPOST-567/inventory.md)
- Follow-ups: PYPOST-573 (duration), PYPOST-574 (caplog contract)
