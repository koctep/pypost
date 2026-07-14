# PYPOST-739: Dev Docs

> Jira: [PYPOST-739](https://pypost.atlassian.net/browse/PYPOST-739)

## What Changed

Expanded the **Error Handling** section in `doc/dev/maintainability_audit.md` with the
canonical three-pattern convention (log-only, log + dialog, silent pass).

## Documentation Updated

| File | Change |
| --- | --- |
| `doc/dev/maintainability_audit.md` | Full error-handling convention: layer rules, patterns, checklist, examples |
| `ai-tasks/PYPOST-739/*` | Top-down workflow artifacts |

## For Maintainers

When adding a failure path:

1. Read the [decision checklist](../../doc/dev/maintainability_audit.md#error-handling).
2. Add or reuse a helper in `collection_item_dialogs.py` for any new modal.
3. Name log events per [logging.md](../../doc/dev/logging.md).

## Related Docs

- [logging.md](../../doc/dev/logging.md) — event naming (PYPOST-747)
- [collection_tree_actions.md](../../doc/dev/collection_tree_actions.md) — dialog helper catalog
- [request_execution.md](../../doc/dev/request_execution.md) — `ExecutionError` model
- [PYPOST-687 audit](../../ai-tasks/PYPOST-687/30-audit-report.md) — original R-P3-003 finding

## Checklist

- [x] Error-handling section covers log-only, log+dialog, silent pass
- [x] Layer rules and examples reference real modules
- [x] Cross-links to sibling dev docs
- [x] R-P3-003 remediation complete
