# Application resource lifecycle

`compose_app()` is the process-level composition root for both desktop and agent sessions.
Every acquired resource is registered with `ApplicationLifecycle` immediately, before the next
construction step can fail. `ComposedApp.shutdown()` executes those callbacks once in reverse
creation order and continues after an individual cleanup failure.

## Ownership

| Resource | Unique owner | Cleanup path |
| --- | --- | --- |
| metrics listener/thread | `ComposedApp` | `MetricsManager.stop_server()` |
| alert file handler | `ComposedApp` | current `MainWindow._alert_manager.close()` |
| tabs, collection/history workers, environment storage workers | `MainWindow` | bounded `MainWindow._shutdown_for_exit()` / `teardown()` |
| persisted MCP registry runtimes | `ComposedApp` | `QtMCPServerRegistry.stop_all()` |
| desktop attach listener and clients | `ComposedApp` | `AgentUiAttachHost.stop()` |

The resulting top-level order is `attach host -> MainWindow and its child owners -> MCP registry
-> alert handler -> metrics listener`. Child owners use their existing bounded teardown order. Calling shutdown
again returns the cached cleanup result and does not invoke a resource twice.

## Startup rollback

`MainWindow` background loads are deferred during composition. The window is first registered as
an owned resource, then `start_initial_loads()` dispatches collection/environment work. Therefore
an exception at any construction or startup step can unwind all earlier resources. The desktop
attach host is likewise registered before `start()` so a bind failure uses the same rollback path.

Interactive close may still reject a close event when pending settings cannot be saved. Once a
desktop event loop has actually ended, or an agent session is being forcibly dismantled,
`ComposedApp.shutdown()` continues best-effort cleanup and reports the failed owner.

## Isolated composition

When `data_dir` is supplied and settings do not contain an alert path, the alert log is written to
`data_dir/pypost-alerts.log`. This fallback survives alert-manager reloads. `alert_log_path` can be
passed to `compose_app()` as an explicit, persistent override. Thus `AgentAppSession` does not
write config, storage, history, or alert files into the real user directories.

Regression coverage is in `tests/test_application_lifecycle.py`: all composition failure points,
LIFO/idempotency, alert reload ownership, attach-start failure, agent delegation, and repeated
runtime cycles with handler, descriptor, widget, and thread growth checks.
