# PYPOST-1049: Architecture Design

## Artifact Verification Baseline Architecture

1. **Required Artifacts Specification**:
   - Standard tasks require 6 artifacts: `00-roadmap.md`, `10-requirements.md`, `20-architecture.md`, `40-code-cleanup.md`, `50-observability.md`, `60-tech-debt.md`.
   - Code audit tasks (PYPOST-684..689) require `30-audit-report.md`.
   - `70-dev-docs.md` was retired in PYPOST-1071 in favor of reviewed documentation under `doc/dev/`.

2. **Grandfathered Baseline (`ai-tasks-artifacts-baseline.json`)**:
   - Records legacy tasks created before mandatory Top-Down artifact enforcement.
   - Any new or modified tasks must comply with the current standard.
   - `tests/test_verify_ai_task_artifacts.py` guards against both positive and negative baseline drift.
