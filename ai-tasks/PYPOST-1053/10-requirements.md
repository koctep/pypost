# PYPOST-1053: CI-safe Jira MCP collection e2e

## Programming Language

Python is the primary implementation language. The delivered developer
workflow also includes Makefile and Markdown changes.

## Goals

Curated Jira MCP tools are a user-facing capability: a caller expects each
tool to complete a collection request and return a usable Jira result. Current
routine checks do not give maintainers one deterministic,
credential-free signal that this end-to-end capability continues to work for
the representative read-only Jira workflows.

**Business goal:** give contributors and release stewards dependable,
secret-free CI confidence that the critical Jira MCP collection workflows
remain usable end to end, while retaining protected live Jira validation as a
separate complementary check.

This implements the follow-up scoped by
[PYPOST-1045 architecture](../PYPOST-1045/20-architecture.md) and resolves
its High-priority TD-1 follow-up.

## User Stories

- As a contributor, I want routine CI to validate representative Jira MCP
  collection workflows without credentials or a Jira tenant, so regressions
  are caught before merge.
- As a collection user, I want the current-user, issue-search, issue-detail,
  and board-listing tools to keep returning usable results, so common Jira
  read workflows remain trustworthy.
- As a release steward, I want a clearly named, repeatable test workflow for
  this coverage, so the CI signal can be run locally and in pull requests.
- As a maintainer, I want the offline collection-e2e scope documented against
  the protected live smoke, so each check's coverage and limitations are
  clear.

## Definition of Done

- [ ] An automated, CI-safe collection-e2e pack validates the curated Jira
      collection's end-to-end read-only workflows using deterministic,
      credential-free validation conditions.
- [ ] The pack demonstrates that each selected workflow completes with a
      usable result from the shipped collection, rather than only verifying an
      isolated interaction or contract.
- [ ] The following Jira MCP tools are covered: `jira_get_current_user`,
      `jira_search_issues_jql`, `jira_get_issue`, and `jira_list_boards`.
- [ ] Issue search produces an issue identifier that the issue-detail
      workflow can consume, proving the representative workflow is coherent.
- [ ] The collection e2e pack is available through
      `make test-mcp-collection-e2e` and is included in the standard CI-safe
      test workflow.
- [ ] The default path requires no real Jira credentials, tenant data, or
      external SaaS network access, and it does not reveal sensitive values in
      test output.
- [ ] Developer documentation explains the workflow, the covered four-tool
      slice, and how it differs from the opt-in live Jira smoke.
- [ ] Existing protected live Jira smoke remains an opt-in complementary
      validation and keeps its current secrecy protections.

## Task Description

### Problem

The curated Jira MCP collection exposes Jira read tools, but default CI lacks
a shared, deterministic end-to-end proof for the representative collection
workflows. Existing isolated checks cover useful individual behavior but do
not demonstrate those workflows as a whole. The live Jira smoke remains
valuable but is unsuitable as the primary PR signal because it depends on
protected credentials and external tenant state.

### Functional Requirements

1. Provide deterministic, credential-free validation conditions for automated
   collection e2e validation.
2. Validate successful end-to-end execution of these four read-only
   collection workflows:
   - Current-user lookup.
   - Issue search by JQL.
   - Issue lookup by an identifier returned from the search workflow.
   - Board listing.
3. Ensure the validation uses the shipped curated Jira collection and invokes
   the exposed MCP tools, so it represents the user-visible collection
   contract.
4. Provide a project-standard command, `make test-mcp-collection-e2e`, for
   contributors and CI to run the pack.
5. Document the intended use of the new offline e2e pack and its boundary
   relative to the optional live Jira smoke.

### Non-Functional Requirements

- **Determinism:** runs must not depend on a real Jira tenant or mutable
  external data.
- **Security:** default CI and local use must need no Jira secret; diagnostics
  must not disclose credentials or sensitive tenant data.
- **Reliability:** the pack must be suitable for the normal CI-safe test
  workflow and remain isolated from external network availability.
- **Maintainability:** the covered workflow and test command must be
  discoverable in developer documentation.
- **Compatibility:** the existing optional live Jira smoke remains supported
  and separate from the offline pack.

### Scope and Boundaries

**In scope**

- Offline e2e confidence for the four specified read-only Jira MCP tools.
- Deterministic, credential-free validation conditions for those workflows.
- A repeatable Makefile test command and its inclusion in CI-safe validation.
- Developer documentation for coverage, operation, and the boundary with live
  smoke testing.

**Out of scope**

- Write, delete, or state-changing Jira tool coverage.
- Full Jira API or full curated-collection emulation.
- Replacing or weakening the protected live Jira smoke.
- Validation of separate user-interface interactions.
- Real credentials, tenant data, or live Jira calls in the default pack.

### Constraints and Assumptions

- The workflow must remain usable in routine CI without access to protected
  Jira services.
- The four-tool slice is the minimum smoke-critical representative scope;
  broader Jira collection coverage is deferred.
- The repository's existing curated Jira collection remains the source of the
  MCP tool contract.
- Protected live smoke continues to provide authorized, external-service
  confidence outside routine CI.

## Main Entities and Interactions

- **Curated Jira collection** — the shipped user-facing set of Jira MCP tool
  definitions.
- **MCP caller** — a test client representing an agent or other collection
  user invoking a tool.
- **Jira read workflow** — current user, issue search, issue detail, or board
  listing behavior requested by the caller.
- **Collection e2e pack** — automated verification that records whether the
  workflow succeeds without live service access.
- **Contributor and CI steward** — consumers of the local command and CI
  result.
- **Live Jira smoke** — separate, protected complementary validation against
  an authorized Jira service.

## Q&A

**Q: Why is this needed if a live Jira smoke already exists?**

**A:** The live smoke is protected and opt-in because it relies on real
credentials and tenant state. It cannot provide routine, repeatable PR CI
coverage.

**Q: Why are existing isolated checks not the primary answer?**

**A:** They validate individual interactions or contracts, not the
user-visible curated Jira MCP collection workflow as a whole. This task needs
confidence in the complete representative workflows.

**Q: Why only four Jira tools?**

**A:** They form the previously approved smoke-critical representative
read-only slice: a user lookup, search, result-following issue lookup, and a
list operation. Full collection coverage is not required for this delivery.

**Q: Does this make live Jira validation unnecessary?**

**A:** No. The offline pack supplies deterministic default-CI confidence; the
protected live smoke remains the complementary authorized-service check.
