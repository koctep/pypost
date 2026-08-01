# PYPOST-902: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: Mapping router accepts compound `"{method} {url}"` keys,
documents compound-before-bare precedence, and unit proofs cover same-URL
multi-method routing, precedence, and v1 bare-URL backward compatibility. No
product runtime change.

## Shortcuts Taken

- **Unit proofs only.** No dedicated GUI scenario for compound keys — same
  stub-boundary scope as PYPOST-868’s initial delivery; PYPOST-901 already
  covers GUI Mapping path with distinct URLs.
- **Method as-is from request object.** No normalization (e.g. uppercasing POST);
  authors must match the method string the UI/worker sends.
- **Single-space separator.** Keys must be exactly `"{method} {url}"`; no
  alternate delimiters.

## Code Quality Issues

- **`_resolve_url_router_response` is a small helper.** Acceptable — keeps
  `_send` readable and gives tests a single lookup semantics site if ever needed.
- **Error message still says `url=` only.** Intentional backward compat with
  868 miss messages; compound-only maps list compound keys in `known=`.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Same URL / GET+POST via compound keys | Covered |
| Compound precedence over bare URL | Covered |
| Bare URL only (868 regress) | Covered — existing `test_stub_agent_e2e_http_url_router_map` |
| Miss with compound keys in map | Covered — existing miss test shape unchanged |
| GUI same-URL multi-method | Not covered — optional follow-up |
| Method case normalization | Not covered — out of scope |

## Follow-Up Items

| Item | Priority | Notes | Jira |
| --- | --- | --- | --- |
| GUI scenario: same URL, GET+POST under compound-key map | Lowest | Optional confidence raise; unit proofs satisfy AC | [PYPOST-958](https://pypost.atlassian.net/browse/PYPOST-958) |
| HTTP method case normalization in router | Lowest | Only if scenarios send inconsistent casing | [PYPOST-959](https://pypost.atlassian.net/browse/PYPOST-959) |

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None |
| Missing timeout markers | **None** — module `pytestmark timeout(10)` |
| Deviations from architecture | None |
| Hardcoded values | Test URLs intentional |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE**
