# Requirements: PYPOST-10 - Post-request Scripts

## 1. Problem Description
Users need to automate API interactions, for example, extract data from responses (auth tokens, resource IDs) and save them to environment variables for use in subsequent requests. Currently, this has to be done manually.

## 2. Technical Stack
- **Application Language**: Python 3.10+
- **GUI Framework**: PySide6
- **Scripting Language**: Python (chosen for native integration).

## 3. Functional Requirements

### 3.1. Script Editor
- A new tab "Tests" or "Post-Script" (name to be clarified, using "Script") should appear in the Request Editor interface.
- Code editor: multi-line text field. Python syntax highlighting (desirable, but optional for first version).

### 3.2. Script Execution
- The script executes automatically **after** receiving a successful (technically) response to the request.
- Execution mechanism: `exec()` with context passing.
- Error handling:
    - Syntax and execution errors (exceptions) are caught.
    - Error message in the script is displayed to the user (e.g., in log or separate result tab), but does not block application operation.

### 3.3. Script API (Context)
The script must have access to global objects:

1.  **`response`**: Object with response data.
    - `response.status_code` (int)
    - `response.headers` (dict)
    - `response.text` (str)
    - `response.json()` (method returning dict/list)

2.  **`request`**: Object with request data.
    - `request.url`
    - `request.method`
    - `request.headers`
    - `request.body`

3.  **`pypost`** (or `env`): Interface for environment interaction.
    - `pypost.env.set(key, value)`: Set environment variable.
    - `pypost.env.get(key)`: Get value.
    - *Optional*: `pypost.log(msg)` for debug output.

### 3.4. Scenarios (User Stories)
- **Token Extraction**:
  ```python
  token = response.json()['token']
  pypost.env.set('auth_token', token)
  ```

- **Simple Check**:
  ```python
  if response.status_code != 200:
      print("Error!")
  ```

## 4. Non-functional Requirements
- **Security**: `exec()` is used. User is warned that they are executing local code. `builtins` restrictions are not required as the application is run locally by the user.
- **Performance**: Script execution must not block UI (execute in the same thread as request, or in a worker).

## 5. Main Entities
- Update `RequestData` model: add `post_script` field (str, default="").
- Modify `HTTPClient` / `Worker`: add script execution step after receiving response.
