# PYPOST-1151: Fix template expression tokenizer whitespace rejection test

## Research

### Background & Issue History
During PYPOST-1149 tech debt tracking, a pre-existing discrepancy was documented regarding `tests/test_template_expression_tokenizer.py::TestPlainVariablePattern::test_plain_pattern_rejects_whitespace_inside`.

In subsequent architecture refactoring (specifically PYPOST-1176):
1. The regex patterns were separated in `pypost/core/template_expression_tokenizer.py`:
   - `PLAIN_VARIABLE_PATTERN = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")`: strictly rejects inner whitespace and only matches exact `{{name}}` tokens.
   - `LOOSE_PLAIN_VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")`: matches loose variable placeholders with optional whitespace inside delimiters for hover resolution.
   - `TEMPLATE_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*(.*?)\s*\}\}")`: general non-greedy template placeholder matching used by `tokenize_template_expressions`.
2. Token helper functions were split:
   - `is_plain_variable_token(token: str) -> bool`: strictly checks against `PLAIN_VARIABLE_PATTERN`.
   - `extract_plain_variable_name(token: str) -> str | None`: strictly extracts the identifier from `PLAIN_VARIABLE_PATTERN`.
   - `is_loose_plain_variable_token(token: str) -> bool`: checks against `LOOSE_PLAIN_VARIABLE_PATTERN`.
   - `extract_loose_plain_variable_name(token: str) -> str | None`: extracts identifier from `LOOSE_PLAIN_VARIABLE_PATTERN`.
3. In `pypost/ui/widgets/mixins.py`, `VariableHoverResolver` uses loose pattern helpers (`is_loose_plain_variable_token`, `extract_loose_plain_variable_name`) for hover text replacement so that templates with internal whitespace (e.g. `{{ SECRET_TOKEN }}`) correctly resolve and mask secret values, while `VariableHoverLocator.VARIABLE_PATTERN` continues referencing `PLAIN_VARIABLE_PATTERN` for the strict unspaced fast-path.
4. The test case `TestPlainVariablePattern::test_plain_pattern_rejects_whitespace_inside` in `tests/test_template_expression_tokenizer.py` is currently fully compliant and passing cleanly with `PLAIN_VARIABLE_PATTERN.fullmatch`.

### Pattern Behavior Matrix
| Pattern / Helper | Input `{{host}}` | Input `{{ host }}` | Input `{{urlencode(db)}}` |
| --- | --- | --- | --- |
| `PLAIN_VARIABLE_PATTERN` (`is_plain_variable_token`) | `True` (group: `"host"`) | `False` (`None`) | `False` (`None`) |
| `LOOSE_PLAIN_VARIABLE_PATTERN` (`is_loose_plain_variable_token`) | `True` (group: `"host"`) | `True` (group: `"host"`) | `False` (`None`) |
| `TEMPLATE_PLACEHOLDER_PATTERN` (`tokenize_template_expressions`) | `["host"]` | `["host"]` | `["urlencode(db)"]` |

## Implementation Plan

### High-Level Plan
1. **Step 3 (Failing Repro Verification)**:
   - Run the automated test suite against `tests/test_template_expression_tokenizer.py` targeting `TestPlainVariablePattern::test_plain_pattern_rejects_whitespace_inside`.
   - Validate and ensure comprehensive assertion coverage for whitespace variations (e.g. `{{ host}}`, `{{host }}`, `{{  host  }}`, `{{\thost\t}}`).
   - If existing assertions already cover the base cases, verify edge-case coverage or record exact test behavior per Step 3 instructions.
2. **Step 4 (Development / Validation)**:
   - Ensure `pypost/core/template_expression_tokenizer.py` and `tests/test_template_expression_tokenizer.py` have exhaustive coverage and 100% passing tests.
   - Run full repository test suite and quality gates (`make check`).
3. **Step 5-8 (Cleanup, Observability, Tech Debt, Dev Docs)**:
   - Complete standard top-down documentation and quality artifacts.

### Mandatory — Failing Repro (Step 3)
- **Target Node**: `tests/test_template_expression_tokenizer.py::TestPlainVariablePattern::test_plain_pattern_rejects_whitespace_inside`
- **Assertion**:
  - `is_plain_variable_token("{{ host }}") is False`
  - `extract_plain_variable_name("{{ host }}") is None`
  - Additional whitespace cases: `{{ host}}`, `{{host }}`, `{{   host   }}`
- **Location**: `tests/test_template_expression_tokenizer.py`
- **Sequencing**: Verify existing test suite state -> Add any missing whitespace edge case assertions if needed -> Confirm green across `make check`.

## Architecture

### System Module Diagram
```mermaid
graph TD
    subgraph Core Tokenization ["pypost.core.template_expression_tokenizer"]
        PVP[PLAIN_VARIABLE_PATTERN<br/>Strict {{name}}]
        LPVP[LOOSE_PLAIN_VARIABLE_PATTERN<br/>Loose {{\s*name\s*}}]
        TPP[TEMPLATE_PLACEHOLDER_PATTERN<br/>General {{\s*expr\s*}}]
        IPVT[is_plain_variable_token]
        EPVN[extract_plain_variable_name]
        ILPVT[is_loose_plain_variable_token]
        ELPVN[extract_loose_plain_variable_name]
        TTE[tokenize_template_expressions]

        PVP --> IPVT
        PVP --> EPVN
        LPVP --> ILPVT
        LPVP --> ELPVN
        TPP --> TTE
    end

    subgraph UI Hover Support ["pypost.ui.widgets.mixins"]
        VHL[VariableHoverLocator]
        VHR[VariableHoverResolver]
        VHM[VariableHoverMixin]

        IPVT -.-> VHR
        ILPVT -.-> VHR
        EPVN -.-> VHR
        ELPVN -.-> VHR
        PVP -.-> VHL
        TPP -.-> VHL
        VHR -.-> VHM
        VHL -.-> VHM
    end

    subgraph Tests ["tests/"]
        T_TET[TestTemplateExpressionTokenizer]
        T_PVP[TestPlainVariablePattern]

        IPVT --> T_PVP
        EPVN --> T_PVP
        TTE --> T_TET
    end
```

### Module Responsibilities and Interfaces

1. **`pypost.core.template_expression_tokenizer`**:
   - `is_plain_variable_token(token: str) -> bool`: Strict fast-path plain variable check. Rejects any whitespace inside delimiters.
   - `extract_plain_variable_name(token: str) -> str | None`: Strict plain variable extractor. Returns `None` if token contains inner whitespace.
   - `is_loose_plain_variable_token(token: str) -> bool`: Loose plain variable check. Allows inner whitespace.
   - `extract_loose_plain_variable_name(token: str) -> str | None`: Loose plain variable extractor. Allows inner whitespace.
   - `tokenize_template_expressions(content: str) -> list[str]`: General template placeholder extraction for runtime template evaluation.

2. **`pypost.ui.widgets.mixins`**:
   - `VariableHoverLocator`: Locates cursor token matches using `PLAIN_VARIABLE_PATTERN` and `TEMPLATE_PLACEHOLDER_PATTERN`.
   - `VariableHoverResolver`: Resolves variable expressions for UI tooltips, utilizing strict and loose helpers as appropriate.

3. **`tests.test_template_expression_tokenizer`**:
   - Unit tests validating strict pattern matching, whitespace rejection, function rejection, and general token extraction.

### Traceability Matrix

| Requirement / Acceptance Criteria | Component / Mechanism | Verification Method |
| --- | --- | --- |
| **AC 1: Strict Token Validation** (`{{host}}` True, `{{ host }}` False / None) | `pypost.core.template_expression_tokenizer` (`PLAIN_VARIABLE_PATTERN`, `is_plain_variable_token`, `extract_plain_variable_name`) | `tests/test_template_expression_tokenizer.py::TestPlainVariablePattern::test_plain_pattern_rejects_whitespace_inside` |
| **AC 2: Test Suite Health** (Rejection test passes, no regressions) | `tests/test_template_expression_tokenizer.py` | `make test PYTEST_ARGS="tests/test_template_expression_tokenizer.py -v"` |
| **AC 3: Quality Gate** (`make check` passing cleanly) | Repository codebase and make targets | `make check` |

## Q&A

**Q: Are there any architectural changes or refactoring required in production code?**  
A: No architectural changes are necessary. The tokenizer pattern separation (`PLAIN_VARIABLE_PATTERN` vs `LOOSE_PLAIN_VARIABLE_PATTERN`) was cleanly architected in PYPOST-1176. The strict contract is already properly enforced and verified by tests.

**Q: How does this maintain backward compatibility with hover previews for spaced tokens?**  
A: Spaced tokens like `{{ host }}` are supported by `VariableHoverResolver` via `LOOSE_PLAIN_VARIABLE_PATTERN` / `is_loose_plain_variable_token` and `extract_loose_plain_variable_name`, while keeping `is_plain_variable_token` strictly unspaced.
