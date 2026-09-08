# Working on PyPost

Conventions that are not visible from any single file, and that past defects came
from breaking. Everything else follows the surrounding code.

## Ownership

**`StateManager` owns the application settings.** There is one `AppSettings`
object in the process and one path to disk. Read it through `StateManager`;
adopt a replacement with `replace_settings`; never call
`ConfigManager.save_config` from anywhere else, and never call `load_config` a
second time. Two copies drift, and whichever saves last silently wins.

**`RequestManager` owns collections and requests.** It hands out deep copies and
stores deep copies. A caller that mutates what it was given is editing its own
object, which is the point: an editor holds unsaved edits, and those must not
reach the stored collection -- or the tool list a background MCP server is
executing -- until the user saves.

If you add a getter that returns a domain model, copy it. If you add a setter
that accepts one, copy it. `tests/test_request_manager.py::TestRequestManagerBoundaryCopies`
holds this line.

## Qt

**Never name a `Signal` after one the base class already defines.** A `Signal`
called `finished` on a `QThread` subclass replaces `QThread.finished`, and the
thread's real completion becomes unobservable. Object disposal should hang off
the base-class signal, which fires on every outcome; result signals fire from
inside `run()` and cover only the paths you remembered.

**Prefer a checkable `QTableWidgetItem` to a checkbox in a cell widget.** Qt
6.11 segfaults on repeated clicks into a `QTableWidget` cell widget, and the
item carries the same state with no extra child widget to keep alive.

**Do not replace a `QTableWidgetItem` while Qt is dispatching `itemChanged` for
it.** Mutate it in place; replacing frees the native item that is still in use.

## Tests

The suite runs headless (`QT_QPA_PLATFORM=offscreen`) and cannot see everything.
The environment-manager segfault reproduces only under `wayland` on a real
display; its test asserts the structure that avoids the crash, not the absence
of the crash. When a test can only assert the shape of a fix, say so in the test
rather than letting it read as proof.

A new regression test should fail against the code before the fix. If it passes
either way, it is not testing the fix.
