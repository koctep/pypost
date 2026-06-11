# PYPOST-460: Observability

## Scope

No new metrics or log fields. This task preserves existing observability contracts.

## Parity checks

| Signal | Field | Expected behavior |
| --- | --- | --- |
| INFO validation failure | `token_count` | Count of `{{ ... }}` placeholders |
| DEBUG render success | `token_count` | Same count |
| WARNING render fallback | `token_count` | Same count |
| `template_expression_render_attempts_total` | N/A | Unchanged outcomes |

## Implementation note

`token_count` is `len(tokenize_template_expressions(content))`, identical to the prior
`len(re.findall(...))` result for the same pattern.

## Verification

- Existing `TestTemplateServiceObservability` tests assert metric and log behavior; all pass.
