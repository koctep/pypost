# PYPOST-1010: Consistent JSON root shape for exported records

## Programming Language

Python

## Goals

PyPost lets users export one or more saved records as JSON. A file containing one record
should be easy to consume as one JSON object, while a file containing several records should
remain an array. This root-shape decision now matters in a third export-related use case.
The product needs one consistent rule so users and integrations can rely on the same JSON
shape everywhere and do not encounter incompatible files for equivalent export choices.

## User Stories

- As a **PyPost user**, I want every relevant export to use the same root shape for one versus
  many records, so I can reliably use the files in scripts, backups, and sharing workflows.
- As an **integration user**, I want a one-record export to be a JSON object and a multi-record
  export to be a JSON array, so the file shape communicates the number of exported records.
- As a **maintainer**, I want that user-visible rule to stay consistent when another export
  workflow uses it, so a future change does not make equivalent exports disagree.

## Definition of Done

- [ ] Relevant JSON export workflows apply one consistent root-shape rule.
- [ ] An export containing exactly one record produces a JSON object at the file root.
- [ ] An export containing more than one record produces a JSON array at the file root.
- [ ] Each export preserves the existing contents and meaning of its records.
- [ ] Automated coverage verifies the root shape for the newly covered use case and guards
      against inconsistent behavior.
- [ ] Existing supported import and export behavior remains compatible with its documented
      expectations.

## Task Description

**Problem:** PyPost already has a user-visible convention for the JSON root of exported
records: a single record is represented directly, and multiple records are represented as a
list. As a third export-related caller requires this convention, separate decisions could
drift and leave users with different file shapes for the same number of records.

**Goal:** Preserve one predictable JSON root-shape contract across the relevant export
workflows: one record is a JSON object; multiple records are a JSON array.

**Scope (in):**

- Apply the established root-shape contract to the newly relevant export use case.
- Preserve the existing record data and export outcomes apart from ensuring the consistent
  root shape.
- Add focused automated verification of the user-visible root-shape contract.

**Scope (out):**

- Changing the fields, values, or meaning of exported records.
- Introducing new export formats or altering user export choices.
- Changing import conflict behavior, encryption behavior, or collection and environment
  business rules.

## Main Entities and Interactions

| Entity | Business role |
| --- | --- |
| Exported record | A saved PyPost item represented in a JSON export file. |
| Export request | A user or product workflow that produces a file containing one or more records. |
| JSON root shape | The top-level form of the file: one object for one record or an array for several. |
| Consumer | A user, script, or import workflow that relies on the exported file's shape. |

Interaction: an export request identifies the records to include → PyPost produces the
corresponding JSON root shape based on the record count → the consumer receives a predictable
file without changing the underlying record content.

## Non-Functional Requirements

- **Compatibility:** preserve established JSON root-shape expectations for existing exports and
  supported consumers.
- **Reliability:** equivalent export choices must not produce different root shapes based solely
  on which workflow initiated them.
- **Data fidelity:** the change must not omit, alter, or expose record data beyond existing
  export behavior.
- **Maintainability:** the root-shape contract must be clearly verified so future export work
  continues to follow it.

## Constraints and Assumptions

- This task follows the technical-debt item recorded in
  `ai-tasks/PYPOST-988/60-tech-debt.md`.
- The existing product convention is one record as a JSON object and multiple records as a JSON
  array.
- The task addresses consistency of the JSON root only; it does not redefine any record format.

## Q&A

**Q: Why is this work needed now?**

**A:** A third export-related use case needs the same root-shape decision. Formalizing the
contract prevents equivalent exports from gradually producing incompatible files.

**Q: Does this change what data users export?**

**A:** No. The requirement concerns only the top-level JSON form used to hold the selected
records; the records retain their existing content and meaning.

**Q: Does this add a new export format?**

**A:** No. It keeps the established JSON convention consistent across the relevant workflows.
