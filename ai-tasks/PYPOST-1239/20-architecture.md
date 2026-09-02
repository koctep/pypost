# PYPOST-1239: Make intentional assertion repetition discoverable

## Research

The authoritative requirements are in
[`10-requirements.md`](10-requirements.md). The current ownership suite,
[`tests/test_display_role_scan_ownership.py`](../../tests/test_display_role_scan_ownership.py),
parses Python source with `ast`, checks delegation and inline
`ItemDataRole.DisplayRole` ownership, and already has a deterministic aggregate
validation seam. The existing developer reference is
[`doc/dev/display_role_ownership_verification.md`](
../../doc/dev/display_role_ownership_verification.md).

Python's `ast` deliberately represents the executable structure, not ordinary
comments. Therefore the new discoverability check must retain source text and
line locations alongside AST inspection; it must not infer a comment from an
AST-only walk. This keeps the check hermetic and consistent with the suite's
existing source-inspection pattern. See the
[Python AST documentation](https://docs.python.org/3.12/library/ast.html).

## Architecture

This is a test/documentation contract, not a production feature. The selected
architectural pattern is a **layered, table-driven validation pipeline**. Source
loading, source/AST location, target rules, contract evaluation, and diagnostic
reporting remain separate layers. A fixed target-specification table gives all
three assertion groups the same validation path while retaining target-specific
messages. This pattern is appropriate because the contract is static, bounded,
and deterministic; it also prevents a new target from silently receiving weaker
rules.

```text
UTF-8 ownership source
        |
        v
source/AST location layer --> fixed target-specification table
        |                                  |
        +--------------> contract validator
                                  |
                                  v
                    validation result + stable diagnostics
                                  ^
                                  |
              focused offline discoverability tests and real-source check

doc/dev/display_role_ownership_verification.md
        |
        +--> durable maintainer guidance (updated in Step 8)
```

### Components and responsibilities

- **Source adapter:** Provides the complete UTF-8 text of
  `tests/test_display_role_scan_ownership.py`. It performs no imports, Qt
  setup, network access, or source mutation.
- **Source/AST location layer:** Parses the supplied text and retains source
  line spans for comments/docstrings and the two assertion nodes in each target
  group. AST inspection continues to identify executable assertion structure;
  source text is authoritative for rationale content.
- **Target specification:** Defines the fixed target order and maps the
  user-facing labels to the source functions: `find_child` maps to
  `find_child_index_by_display_text`, `find_tree` maps to
  `find_tree_index_by_display_text`, and `_select_item_view` maps to the
  identically named function. It also defines the two required assertion
  predicates for each target.
- **Contract validator:** Applies the target rules and returns a complete,
  deterministic result rather than changing ownership behavior.
- **Focused test harness:** Exercises the validator with the real source and
  bounded synthetic mutations, without requiring a display server or external
  service.

### Validator interface and result contract

The validator's concrete test-side API is:

```text
validate_display_role_discoverability(source_text: str)
    -> DiscoverabilityValidationResult
```

This is an architectural interface, not an implementation instruction. Its
input is the complete, decoded UTF-8 contents of the ownership test module.
The validator receives source text directly so focused tests can supply
synthetic variants; it does not accept a path, read other files, or execute the
source. The production ownership checks continue to receive and inspect their
existing source paths independently.

`DiscoverabilityValidationResult` contains:

- `valid: bool`, true only when all three target groups satisfy the contract;
- `checked_targets`, the fixed ordered labels `find_child`, `find_tree`, and
  `_select_item_view`; and
- `diagnostics`, an ordered tuple of zero or more diagnostic records. Each
  record contains a target label, a stable code, and a stable human-readable
  message. Contract violations are represented in the result and do not rely
  on incidental exceptions.

The stable diagnostic contract is target-first and source-location-independent:
diagnostics are emitted in the order `find_child`, `find_tree`,
`_select_item_view`, with at most one diagnostic per invalid target. Diagnostic
records do not include absolute paths, object representations, or line numbers.
The fixed codes and message meanings are:

| Code | Meaning |
| --- | --- |
| `MISSING_ASSERTION_PAIR` | One or both required assertions are absent. |
| `MISSING_EXPLANATION` | The target has its pair but no local rationale. |
| `MISSING_INTENTIONALITY` | The rationale does not explicitly say the repetition is intentional. |
| `INCOMPLETE_RATIONALE` | The rationale omits delegation, no inline ownership, or regression risk. |
| `WRONG_TARGET_EXPLANATION` | A local rationale names a different target. |
| `DETACHED_EXPLANATION` | The correct rationale exists only outside the target's local boundary. |

The message for every record starts with `PYPOST-1239`, the target label, and
the code, followed by the fixed requirement meaning. This makes missing and
detached explanations identifiable as discoverability failures while allowing
wording to remain readable. If the supplied text cannot be parsed as Python,
the result is invalid with one `INVALID_SOURCE` diagnostic for `module`; this
is the only non-target diagnostic and is also stable.

### Assertion-pair association and proximity boundaries

The validator uses a target-region rule for each target independently. The
matching pair is the target's two assertion predicates: an assertion that the
mapped function calls the shared lookup helper (`_calls_name`) and an assertion
that the mapped function has no inline `ItemDataRole.DisplayRole` reference
(`_has_display_role_attr`, with the existing negative assertion meaning). Both
assertion nodes must occur in the same target-specific region, but they do not
need to occur in the same containing function.

The regions are bounded by explicit source names and target markers. The
`find_child` region is the inclusive source span beginning at
`_assert_flat_shared_ownership` and ending at
`_assert_flat_no_duplicate_ownership`; it is explicitly allowed to cross the
boundary between those two helper definitions. The `find_tree` region is the
`_assert_tree_shared_ownership` helper span. The `_select_item_view` region is
the `_select_item_view` assertion cluster inside
`test_flat_and_tree_share_display_role_match_helper`, bounded by its
target-specific marker and the surrounding named function. If a function
contains assertions for more than one target, target markers subdivide the
function into separate regions. A region ends at its closing named function or
at the next target marker; it may not consume an unrelated helper or target.

Each required assertion must have an adjacent target-specific rationale/marker
within twelve nonblank source lines. The marker names the target and either
contains or points to the local explanation; the explanation must be in the
same bounded region. Thus the validator requires both assertions and local
rationale for the target, including when the `find_child` pair spans two
helpers. A marker adjacent to only one assertion, a marker for another target,
or an explanation outside the bounded region is insufficient. A module
docstring, a developer-guide paragraph, or a remote summary is not associated
with the pair.

For all three targets, the local rationale must state four linked facts: the
two assertions are intentionally repeated, the target delegates to the named
shared/flat lookup as applicable, the target has no inline DisplayRole
ownership, and simplifying or combining the pair risks weakening ownership
regression protection. The validator checks the intentionality statement as a
separate AC-2 condition; it must not infer intentional repetition merely from
the presence of two assertions.

Add a small validator at the ownership suite's maintenance boundary. It reads
the UTF-8 source text, identifies the three named assertion groups, and checks
that each group contains both `_calls_name` and `_has_display_role_attr`
assertions plus a clearly marked rationale in the same local maintenance
region. The target specification and the association/proximity boundaries above
are the validator's complete contract. The rationale marker must also state
that the repetition is intentional; describing duplication without that
statement fails AC-2.

Association is deliberately local and target-specific: a comment or docstring
that occurs only in a remote summary, names another target, or sits beside only
one assertion fails. The validator uses the source line spans and the bounded
target block defined above, while the existing AST helpers remain responsible
for behavior/ownership checks. It must not replace, combine, or weaken
`_calls_name` or `_has_display_role_attr`.

### File responsibilities and mapping

| Requirement | File/component | Responsibility |
| --- | --- | --- |
| AC-1, AC-2, AC-5 | `tests/test_display_role_scan_ownership.py` | Keep the three explicit pairs and their target-specific local explanations. |
| AC-4, AC-5, AC-6 | Validator and focused discoverability tests | Reject missing/detached rationale, accept compliant source, and emit stable target diagnostics. |
| AC-3 | `doc/dev/display_role_ownership_verification.md` | Explain load-bearing repetition and the review constraint; update in Step 8. |
| AC-7 | Existing AST ownership helpers and ownership test | Preserve delegation and no-inline-DisplayRole assertions, lookup results, user-facing selection behavior, exports, and unrelated validation rules; the discoverability check observes source text without changing those contracts. |
| AC-8 | Task artifact and bounded file set above | Prevent unrelated refactoring, dependencies, runtime changes, or gate changes. |

### Validation flow

1. The source adapter supplies the real test source to
   `validate_display_role_discoverability` and validates the three named local
   groups.
2. Run the existing ownership assertions unchanged.
3. In focused tests, call the same text-based API with bounded synthetic source
   variants: remove a rationale, move it outside the target block or beyond
   the proximity limit, associate it with the wrong target, omit the explicit
   intentionality statement, and provide a compliant control.
4. Assert one focused diagnostic per invalid target, with deterministic target
   ordering and the stable code/message prefix. Run through the repository
   Makefile target in the later test step.

The check uses only local files and standard-library parsing/text operations.
It has no application imports, Qt initialization, sleeps, retries, network, or
new dependency. Existing tests remain the behavior-preservation gate.

### Risks and mitigations

- **False acceptance from a generic comment:** require target-specific markers
  and proximity to both assertion nodes; cover this with a wrong-target and
  detached mutation.
- **False rejection after harmless formatting:** recognize the stable marker
  and source spans rather than exact whitespace or line numbers.
- **Validator drift from the assertions:** keep target definitions in one small
  table/helper and test the compliant real source plus independent mutations.
- **Diagnostic instability:** validate targets in a fixed order and use stable,
  target-named messages.
- **Scope creep into behavior:** preserve the current ownership helpers and
  add only test/documentation-contract logic.

## Implementation Plan

Step 3 must create the red automated repro before any production or final test
implementation. Its initial entry point is the self-contained
`tests/test_display_role_scan_ownership_discoverability.py::test_real_source_has_display_role_explanations`.
That test reads
`tests/test_display_role_scan_ownership.py` with
`Path.read_text(encoding="utf-8")`, uses a fixed table of the three target
labels, named assertion forms, and required target markers, and evaluates the
source directly. It does not import or call the future validator, so the red
run cannot fail through a missing symbol, undefined parser, or import seam.

When a target's two assertion forms are present but its required adjacent
target-specific rationale/marker is absent, the test appends the stable
diagnostic `PYPOST-1239/<target>/MISSING_EXPLANATION: local rationale is
required for both repeated DisplayRole assertions`. It raises one
`AssertionError` containing diagnostics in the fixed target order. The current
source is expected to fail directly with that diagnostic for `find_child`,
`find_tree`, and `_select_item_view`. The red test also asserts that both
assertion forms are present, so it cannot pass merely because a free-floating
comment was added.

After the red repro is independently reviewed, Step 4 introduces
`validate_display_role_discoverability(source_text)` and the structured result
contract above. The direct source contract becomes the validator's real-source
control, and focused bounded mutations then cover
`DETACHED_EXPLANATION`, `WRONG_TARGET_EXPLANATION`, and
`MISSING_INTENTIONALITY` without replacing the initial stable red mechanism.
Step 4 adds the local explanations and validator behavior until the repro is
green; Step 8 then updates the developer guide.

## Q&A

**Q: Does this change the DisplayRole ownership rule?**

A: No. It protects discoverability of the existing repeated assertions and
leaves lookup behavior and ownership checks unchanged.

**Q: Why not validate comments with AST alone?**

A: Ordinary comments are not represented in the AST, so source text and AST
line spans are both required to prove local association.

**Q: What is the validation boundary?**

A: The existing fast Makefile test gate plus the focused, offline discoverability
tests; no display server, network service, or external data is required.
