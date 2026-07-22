# PYPOST-843: Architecture

Run `make check`. Fix gate failures:

1. Harness table missing mid-start cleanup module
2. SOLID LOC caps exceeded (main_window / env_presenter) — bump caps
3. Missing `70-dev-docs.md` on completed ai-tasks folders

Step 3 N/A as automated red product test — the gate run itself is the repro.
