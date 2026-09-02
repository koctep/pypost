# MainWindow Alert-Reload Crash Classification

## Overview

The alert-reload harness checks whether the existing `MainWindow` settings
lifecycle remains alive across repeated isolated Qt test processes. It is a
diagnostic guard for native process failures, not a replacement for the
alert-reload behavior tests.

## Running the harness

Run the bounded harness through the repository Make target:

```text
make test PYTEST_ARGS="tests/test_main_window_alert_reload_crash_repro.py -q -m 'slow or not slow'" WORKERS=1 WORKER_TIMEOUT=30
```

The harness runs `tests/test_main_window_alert_reload.py` in a fresh child
process. It performs one clean-control run and three repeated runs. Each child
uses `QT_QPA_PLATFORM=offscreen`, `PYTHONFAULTHANDLER=1`, and a 20-second
subprocess timeout.

## Outcome classifications

Each child result is classified as one of the following:

- `normal_exit`: the child returned zero.
- `nonzero_exit`: the child returned a positive non-zero status, such as a
  Python assertion or test failure.
- `signal_exit`: the child was terminated by a signal, which is the relevant
  classification for a native crash such as SIGSEGV.
- `timeout`: the child exceeded the 20-second bound.

The parent test fails for every result other than `normal_exit`. This keeps a
Python assertion that happens before a native teardown failure from appearing
to be a successful crash test.

## Evidence and troubleshooting

Failure output includes the exact child command, configured Qt/faulthandler
environment, elapsed duration, classification, and bounded stdout/stderr
tails. Use those fields to distinguish an ordinary test failure from a signal
termination or a hang without allowing a crashing child to take down the
parent test process.

The current evidence-backed result is N/A for reproducing the reported native
crash: the clean control and repeated bounded runs complete with
`normal_exit` in the available environment. N/A means the crash was not
reproduced under these conditions; it does not claim that an unavailable
runtime-specific failure has been fixed. Investigate a non-normal result from
the captured classification and output before changing production alert
lifecycle code.
