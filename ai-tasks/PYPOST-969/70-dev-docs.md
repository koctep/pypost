# PYPOST-969: Developer Documentation

## Updates

- `doc/dev/agent_e2e_send_settle.md`: added seed POST convention membership,
  guard behavior, a focused command, and troubleshooting.
- `ai-tasks/PYPOST-969/00-roadmap.md`: marked Step 8 in progress pending
  review.

## Documentation Decisions

- Updated the existing Send-settle guide because it is the canonical developer
  page for the helper and convention inventory.
- Did not create a second focused `doc/dev` page; that would duplicate the
  authoritative module list and troubleshooting guidance.
- Did not change `doc/dev/testing.md`; PYPOST-969 introduces no test marker,
  timeout policy, Makefile target, or `PYTEST_ARGS` behavior.
- Did not change the response-panel helper guide; it already links to the
  Send-settle guide, and snapshot helper behavior is unchanged.
- This workflow artifact records delivery evidence only. It is not application
  API documentation and is not exposed as a public product contract.

## Template Coverage

- **Overview:** The existing guide explains Send-to-response readiness and now
  identifies seed POST as a guarded module.
- **Architecture:** The authoritative inventory and parameterized source guard
  behavior are documented, including accepted and rejected patterns.
- **API / Usage:** Existing `wait_response_after_send` usage remains current;
  no helper signature changed.
- **Configuration:** No new configuration exists; the guide retains shared
  timeout and import information.
- **Running:** A focused seed POST convention command is provided.
- **Troubleshooting:** Missing parameter collection and tree-open edit guidance
  are provided.

## Validation

- New and modified developer and task Markdown lines obey the 100-character
  limit.
- Whitespace, ATX heading, and merge-conflict marker checks pass.
- All linked existing developer pages remain present.
- The final product/test code diff remains one inventory entry.
- The standard task artifact set now includes `70-dev-docs.md`, so PYPOST-969
  has all files required by the artifact scanner when Step 8 is approved.
- No broad test suite was run for this documentation-only step.

## Review Status

Documentation is ready for review. Step 8 remains `[/]` until approval.
