# PYPOST-1079: Automated Verification of Step 8 Developer Documentation

## Programming Language

Python is the implementation language for the application and tooling. English Markdown records the requirements and workflow artifacts.

## Goals

The repository development workflow follows an 8-step Top-Down process, where Step 8 mandates updating and reviewing developer documentation under `doc/dev/`. PYPOST-1071 retired the obsolete task-local `70-dev-docs.md` requirement, aligning the workflow with living developer documentation. However, currently `scripts/verify_ai_task_artifacts.py` only checks steps 1 through 7 when evaluating roadmap completion (`range(1, 8)` and collapsed `STEP 1–7`), and the script does not verify that Step 8 developer documentation took place.

This leaves an automated enforcement gap: tasks can be marked closed without verified completion of Step 8 developer documentation.

**Business goal:** Establish automated verification for Step 8 (developer documentation) in the AI task artifact validation workflow, ensuring that all completed tasks adhere to the full 8-step quality standard while cleanly distinguishing new non-compliant tasks from grandfathered historical tasks.

## User Stories

- As a **release steward**, I want automated CI verification to ensure all completed tasks have fulfilled their Step 8 developer documentation obligations, so that codebase documentation remains current, accurate, and aligned with architectural changes.
- As a **maintainer**, I want the artifact verification tool to reliably distinguish between historical tasks completed under earlier workflow conventions and newly completed tasks, so that legacy history is grandfathered in baseline records without masking new documentation regressions.
- As a **contributor / workflow operator**, I want deterministic validation feedback during `make check` and artifact verification runs, so that I have clear and unambiguous requirements for when a task is considered fully documented and closed.

## Definition of Done

- [ ] Automated verification in the task artifact validation workflow checks Step 8 (developer documentation) completion for closed tasks.
- [ ] Roadmap completion evaluation rules account for the complete 8-step Top-Down workflow standard.
- [ ] The committed artifact baseline accurately reflects the accepted repository inventory under the updated verification rules, with zero false positives on legacy tasks.
- [ ] Any newly completed task missing Step 8 completion is detected and reported as a verification violation.
- [ ] All unit and integration test suites covering task artifact verification pass with deterministic, repeatable results.
- [ ] No existing workflow compliance protections for Steps 1 through 7 are weakened or bypassed.

## Task Description

**Problem:** Step 8 developer documentation is a mandatory stage of the development workflow, but current automated tooling evaluates roadmap completion using only steps 1 through 7 and performs no validation of Step 8 documentation. This creates a quality blind spot where tasks can be marked closed without verified documentation updates.

**In-Scope:**

- Define business requirements for automated verification of Step 8 (developer documentation) within the task artifact verification process.
- Require validation of Step 8 completion when determining task roadmap completion.
- Account for legacy roadmaps and historical task inventory through baseline management so that historical tasks do not block CI.
- Verify that the workflow suite and baseline tests detect missing Step 8 fulfillment for newly closed tasks.

**Out-of-Scope:**

- Modifying the semantic contents or writing new documentation for historical tasks completed before this standard.
- Altering the definitions or required artifacts of Steps 1 through 7.
- Changing Jira ticketing or board workflows beyond artifact validation.

## Functional Requirements

- **FR-1**: The verification system must include Step 8 (developer documentation) when determining whether an AI task roadmap is completed.
- **FR-2**: The verification system must detect and report any completed task that lacks required workflow documentation fulfillment according to the repository standard.
- **FR-3**: The verification system must support grandfathering existing historical tasks whose roadmaps followed earlier workflow conventions (such as legacy 7-step or collapsed formats) via a committed baseline inventory.
- **FR-4**: The verification system must provide clear, actionable diagnostic output when a new task violates documentation verification requirements.
- **FR-5**: The verification baseline update mechanism must deterministically synchronize the baseline snapshot with current repository task inventory when executed.

## Non-Functional Requirements

- **NFR-1 (Reliability & Determinism):** Verification results must be 100% deterministic across local developer environments and CI runs.
- **NFR-2 (Performance):** The artifact verification scan over the entire repository task inventory must execute in bounded time (under 5 seconds).
- **NFR-3 (Regression Resistance):** The updated verification rules must reliably prevent future tasks from closing without completing Step 8.
- **NFR-4 (Transparency):** Any delta between current repository task state and the committed baseline must be clearly reported with task IDs and specific discrepancies.

## Constraints and Assumptions

- **Constraints:**
  - The repository contains hundreds of historical task folders with heterogeneous roadmap formatting.
  - The verification tool must integrate with `make check` / CI without introducing heavy external dependencies.
  - Changes to completion rules must not break backwards compatibility for grandfathered historical records.
- **Assumptions:**
  - Step 8 deliverable remains developer documentation under `doc/dev/` as established by `td-70-dev-docs`.
  - The roadmap file (`00-roadmap.md`) remains the authoritative progress journal for each task.

## Main Entities and Interactions

- **AI Task Folder**: The dedicated workspace directory (`ai-tasks/<TASK-ID>/`) containing all Top-Down workflow artifacts for a given task.
- **Task Roadmap**: The single progress journal (`00-roadmap.md`) tracking the lifecycle state, step marks, metadata, and recorded deliverables of a task.
- **Developer Documentation**: The repository-wide technical documentation stored under `doc/dev/` updated as part of Step 8.
- **Artifact Verifier**: The automated validation tool that scans task folders, assesses task completion status, and verifies that required artifacts and steps are fulfilled.
- **Artifact Baseline**: The committed snapshot recording accepted legacy gaps and historical task discrepancies.
- **Workflow Operator / Contributor**: The engineer or automated agent executing the Top-Down workflow according to repository standards.

## Q&A

**Q:** Why is automated verification of Step 8 needed if developers already know they should update docs?

**A:** Manual adherence without automated gates inevitably leads to documentation drift and quality gaps. Automated enforcement guarantees that documentation updates cannot be accidentally overlooked before a task is closed.

**Q:** How does this task relate to the retirement of `70-dev-docs.md` in PYPOST-1071?

**A:** PYPOST-1071 correctly retired the obsolete task-local `70-dev-docs.md` artifact file because Step 8's true output is living documentation in `doc/dev/`. However, that retirement left Step 8 with no residual automated check in `scripts/verify_ai_task_artifacts.py`. PYPOST-1079 restores automated Step 8 verification.

**Q:** How should historical task roadmaps with legacy formats be handled?

**A:** Historical tasks that were completed under legacy formats (e.g. explicit 7-step lists or collapsed `STEP 1-7`) are captured and grandfathered in the committed artifact baseline, ensuring clean CI runs while strictly enforcing the full 8-step standard for all new work.
