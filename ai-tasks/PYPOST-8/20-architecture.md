# Architecture: PYPOST-8 - Post-request Scripts

## 1. System Components

We will introduce a new component `ScriptExecutor` and modify existing ones to support the scripting
lifecycle.

### 1.1. ScriptExecutor (`pypost/core/script_executor.py`)

A new dedicated class responsible for executing user scripts safely and managing the context.

*   **Responsibility**:
    *   Prepare execution context (`request`, `response`, `pypost`).
    *   Execute python code using `exec()`.
    *   Capture outputs and errors.
    *   Update environment variables based on script actions.

*   **API**:
    ```python
    class ScriptExecutor:
        def execute(self, script: str, request_data: RequestData, response_data: ResponseData, env_variables: Dict[str, str]) -> ExecutionResult:
            ...
    ```

*   **Context Objects**:
    *   `PyPostAPI`: A wrapper class exposed as `pypost` (or `env`) to the script, providing methods
        like `set_env(key, value)`.

### 1.2. Model Changes (`pypost/models/models.py`)

*   **RequestData**: Add `post_script: str` field to store the user's python script.

### 1.3. Worker Changes (`pypost/core/worker.py`)

The `RequestWorker` needs to encompass the script execution step *after* the HTTP request is
successful.

*   **Flow**:
    1.  `HTTPClient.send_request(...)` -> `ResponseData`
    1.  If `RequestData.post_script` is present:
        *   Initialize `ScriptExecutor`.
        *   Run script.
        *   If script modifies environment, capture updates.
    1.  Emit `finished` signal (now possibly containing updated environment or execution logs).

### 1.4. UI Changes

*   **RequestEditor**: Add a new tab "Script" alongside Headers/Body.
*   **MainWindow**: Handle the updated environment coming back from the worker (if variables
    changed).

## 2. Data Flow

1.  **User** writes script in `RequestEditor` -> saved to `RequestData.post_script`.
1.  **User** clicks Send -> `RequestWorker` starts.
1.  `HTTPClient` performs network request.
1.  `RequestWorker` calls `ScriptExecutor` with `response` and `request`.
1.  **Script** runs `pypost.env.set('token', 'abc')`.
1.  `ScriptExecutor` returns modified environment variables.
1.  `RequestWorker` emits signal with `(ResponseData, UpdatedEnvironment)`.
1.  `MainWindow` updates the global environment state with new variables.

## 3. Detailed Design

### 3.1. Script Context

```python
# The 'pypost' object exposed to script
class ScriptContext:
    def __init__(self, variables: Dict[str, str]):
        self._variables = variables.copy()
        self._logs = []

    @property
    def env(self):
        return self # or a sub-object

    def set(self, key: str, value: str):
        self._variables[key] = str(value)

    def get(self, key: str):
        return self._variables.get(key)

    def log(self, message: str):
        self._logs.append(str(message))
```

### 3.2. Worker Signal Update

Existing `finished = Signal(ResponseData)` might need to change or we add a new signal `env_updated
= Signal(dict)`.
Better approach:
*   Define a `RequestResult` dataclass that holds both `ResponseData` and `execution_logs` /
    `updated_variables`.
*   Or just emit a separate signal for env updates since the `ResponseView` only cares about
    response.

**Decision**:
Add `env_update = Signal(dict)` to `RequestWorker`.
If script runs successfully and changes env, emit `env_update`.
`finished` signal continues to emit `ResponseData`.

## 4. Dependencies

*   No new external dependencies (standard library `builtins`).
