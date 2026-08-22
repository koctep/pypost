# Roadmap: PYPOST-1130

## Task Metadata

- **Implementation language**: Python
- **Branch name**: *[recorded by the commit procedure — reference only, do not switch]*

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gather requirements and document business scope in `ai-tasks/PYPOST-1130/10-requirements.md` (in progress, awaiting review gate)
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Design message stream, codec engine, export formats, and UI list model in `ai-tasks/PYPOST-1130/20-architecture.md` (in progress, awaiting review gate)
- [x] **STEP 3: Failing Repro Test**
  - [x] Failing repro test suite: `tests/test_websocket_stream_and_codecs.py` (red test suite)
- [x] **STEP 4: Development**
  - [x] Implement `pypost/core/websocket_stream.py` (StreamEntry, StreamQuery, MessageStream with dual eviction, build_stream_entry pure masking)
  - [x] Implement `pypost/core/websocket_codec.py` (encode_payload, decode_payload, detect_binary_presentation, validate_format)
  - [x] Implement `pypost/core/websocket_stream_export.py` (format_json_transcript, format_text_transcript, export_stream_to_json_file, export_stream_to_text_file)
  - [x] Implement `pypost/ui/widgets/websocket/stream_model.py` (StreamListModel with append_batch sole UI writer)
  - [x] Make all 41 test cases in `tests/test_websocket_stream_and_codecs.py` GREEN
  - [x] Verify test suite (41/41 tests passing), flake8 (clean), and mypy (clean)
- [x] **STEP 5: Code Cleanup**
  - [x] Static analysis (flake8), line length checks (<= 100 chars), and formatting verified clean across all files
  - [x] Verified explicit timeout markers on tests (pytestmark = 30s) and all 41 test cases pass
  - [x] Created cleanup report in `ai-tasks/PYPOST-1130/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Implement structured debug logging and tracking counters
  - [x] Add verification tests in `tests/test_websocket_stream_and_codecs.py`
  - [x] Create observability report in `ai-tasks/PYPOST-1130/50-observability.md`
  - [x] Implement drop accounting metrics (`dropped["capacity"]`, `dropped["memory_budget"]`) and payload byte tracking (`total_retained_bytes`) in `pypost/core/websocket_stream.py`
  - [x] Embed transcript export drop headers and session metadata in `pypost/core/websocket_stream_export.py`
  - [x] Implement structured logging for stream eviction, transcript file export, and UI batch list model transactions
  - [x] Add automated unit tests verifying structured logs and caplog capture in `tests/test_websocket_stream_and_codecs.py` (44/44 tests passing)
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze shortcuts, missing tests, and performance considerations
  - [x] Document non-blocking follow-up tasks and dependencies
  - [x] Create technical debt report in `ai-tasks/PYPOST-1130/60-tech-debt.md`
  - [x] Verify test suite and triage pre-existing test failures (0 failures, 100/100 WebSocket tests passing)
- [x] **STEP 8: Dev Docs**
  - [x] Create developer documentation in `doc/dev/websocket_message_stream.md`
  - [x] Update documentation index in `doc/dev/README.md`
- [x] **COMMIT: Commit Changes**
  - [x] Commit hash: `ffa6a8ea`
  - [x] Suggested branch: `task/PYPOST-1130-bounded-message-stream`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1130/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1130/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_websocket_stream_and_codecs.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1130/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1130/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1130/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_message_stream.md`
- `doc/dev/README.md`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
