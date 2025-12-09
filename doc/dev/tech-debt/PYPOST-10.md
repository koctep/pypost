# Technical Debt: PYPOST-10 (Post-request Scripts)

## 1. Security (Critical)
- **Problem**: The current implementation uses Python's `exec()` to run user scripts. This allows arbitrary code execution with the permissions of the running application.
- **Risk**: If a user loads a malicious collection from an untrusted source, the script could delete files, access the network, or steal data.
- **Future Solution**: Implement a sandboxed environment (e.g., restricted `globals`, distinct process, or WASM-based runtime if switching languages) or add a "Safe Mode" that prompts before running scripts from new collections.

## 2. Script Execution Stability
- **Problem**: There is no timeout mechanism for script execution.
- **Risk**: An infinite loop in a user script (`while True: pass`) will hang the `RequestWorker` thread, preventing further requests from that tab/worker.
- **Future Solution**: Execute scripts in a separate process with a strict timeout or use a watchdog.

## 3. UI/UX - Script Editor
- **Problem**: The script editor is a simple `QPlainTextEdit`.
- **Impact**: No syntax highlighting, code completion, or line numbering makes writing scripts difficult.
- **Future Solution**: Integrate a code editor widget (e.g., `QScintilla` or a custom syntax highlighter).

## 4. Debugging Experience
- **Problem**: Error messages show a standard Python traceback.
- **Impact**: It might be hard for users to map the error back to the specific line in their script editor.
- **Future Solution**: Parse tracebacks to highlight the error line in the editor and provide more user-friendly error messages.

## 5. Testing
- **Problem**: The feature was implemented without comprehensive automated unit tests for `ScriptExecutor` and `RequestWorker`.
- **Impact**: Regression risk during future refactoring.
- **Future Solution**: Add `pytest` tests covering:
    - Successful script execution.
    - Script errors/exceptions.
    - Environment variable updates.
    - Security boundary checks (if implemented).


