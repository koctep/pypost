# PYPOST-1213: Root-Cause Diagnosis for Large-Batch GUI Segfault

## Goals

Provide a durable, evidence-based diagnosis of the large-batch GUI test segmentation
fault so the mitigation task can choose a safe containment strategy without reopening
the defect classification.

## User Stories

- As a maintainer, I need to know whether this crash is the same class as the known
  SettingsDialog teardown failure or a distinct failure mode.
- As the mitigation owner, I need a clear conclusion tied to observed crash sites and
  execution triggers.
- As a future investigator, I need the diagnosis and evidence recorded in developer
  documentation.

## Definition of Done

- A written diagnosis classifies the crash as shared Shiboken/Qt object-lifetime behavior,
  distinct QStyle/QPalette accumulation, or another evidence-supported class.
- The site and trigger are explicitly contrasted with PYPOST-1040/PYPOST-1115.
- The evidence is sufficient for PYPOST-1214 to select a mitigation strategy.
- The conclusion is available to future maintainers in `doc/dev`.

## Task Description

The PYPOST-1212 baseline shows a native SIGSEGV during sustained large-batch GUI test
execution, associated with `StyleManager.apply_theme` and `QStyleFactory.create("Fusion")`.
This task diagnoses the failure class. It does not implement bounded batching, process
isolation, or the separate SettingsDialog teardown mitigation.

The implementation language is Python. The diagnosis may be documentation-only because
the reproducible behavior and baseline harness already exist in PYPOST-1212.

## Scope and Boundaries

In scope: compare crash site, trigger topology, workload shape, and prior-art signatures;
record the root-cause conclusion and mitigation handoff criteria.

Out of scope: changing application behavior, changing the baseline repro, guaranteeing
an upstream PySide6 fix, or implementing CI ownership and batching policy.

## Q&A

- **Why is this needed?** PYPOST-1214 must select a safe mitigation based on a stable
  defect classification.
- **What is the source of baseline evidence?** PYPOST-1212 artifacts and
  `doc/dev/gui_batch_segfault.md`.
