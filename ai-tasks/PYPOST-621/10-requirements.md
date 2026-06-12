# PYPOST-621: Reload AlertManager after settings save

## Goals

Operators who change alert configuration in Settings see those changes take effect
immediately for new request executions, without restarting the application.

## User Stories

- As an operator, when I change the alert log path in Settings and save, subsequent
  retry-exhaustion alerts are written to the new path.
- As an operator, when I change webhook URL or authorization in Settings and save,
  subsequent alerts use the updated delivery configuration.

## Definition of Done

| ID | Criterion |
| --- | --- |
| AC-1 | Saving Settings with changed `alert_log_path`, `alert_webhook_url`, or `alert_webhook_auth_header` rebuilds the live `AlertManager`. |
| AC-2 | The previous `AlertManager` instance is closed before replacement (no handler leak). |
| AC-3 | `TabsPresenter` receives the new instance so new `RequestWorker` runs use it. |
| AC-4 | Saving Settings without alert field changes does not reload `AlertManager`. |
| AC-5 | Qt tests cover reload on alert change and skip when unrelated settings change. |

## Scope

**In scope:** `MainWindow.open_settings`, `TabsPresenter.set_alert_manager`, unit tests,
developer documentation update.

**Out of scope:** In-flight request workers (keep injected instance); refactoring
`main.py` bootstrap factory.

## Q&A

*(No open questions.)*
