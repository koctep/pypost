# PYPOST-570: Technical Debt Analysis

## Shortcuts Taken

- Recommendation assumes PYPOST-571 will implement the CI guardrail; CI quiet mode alone
  reduces noise but does not detect new unexpected ERROR lines.

## Code Quality Issues

None.

## Follow-up Tasks

| Priority | Description | Jira / action |
| --- | --- | --- |
| High | CI allowlist / fail on unexpected ERROR | [PYPOST-670](https://pypost.atlassian.net/browse/PYPOST-670) |
| Medium | Add `-o log_cli=false` to `test.yml` | Optional small PR or part of PYPOST-571 | [PYPOST-671](https://pypost.atlassian.net/browse/PYPOST-671) |
| Low | `caplog` on medium-risk presenter test | Defer |
| Low | Review 21 suspicious + 26 unknown inventory lines | Epic follow-up |

## Verdict

**SAFE TO CLOSE** — quantified noise, options compared, hybrid recommendation documented with
migration steps for PYPOST-571 and optional CI workflow change.
