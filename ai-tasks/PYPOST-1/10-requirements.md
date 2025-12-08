# PyPost Project Requirements (Postman Alternative)

## 1. Problem Description
Development of a desktop application in Python for API testing, similar to Postman, using a Qt-based graphical interface. The application must allow creating, saving, and sending HTTP requests, as well as managing collections and environments.

## 2. Technology Stack
- **Programming Language**: Python 3.10+
- **GUI Framework**: PySide6 (Qt for Python)
- **HTTP Client**: `requests` library
- **Data Storage Format**: JSON

## 3. Functional Requirements

### 3.1. Request Sending
- Support for HTTP methods:
  - GET
  - POST
  - PUT
  - DELETE
- Request URL input.
- Display of response status (Status Code), execution time, and response size.

### 3.2. Request Data Management
- **Headers**: Table editor (Key-Value).
- **Query Parameters**: Table editor (Key-Value), automatic addition to URL.
- **Body**:
  - JSON format support.
  - Editor with syntax highlighting (if possible) or multi-line text field.

### 3.3. Response Handling
- Display of response body.
- JSON response formatting (Pretty print).
- Display of response headers.

### 3.4. Collection Management
- Creating, renaming, and deleting collections.
- Saving requests within collections.
- Hierarchical structure (optional folders, but at least a list of requests in a collection).
- Storing collections in local JSON files.

### 3.5. Environments and Variables
- Creating and editing environments.
- Storing variables in environments (Key-Value).
- Ability to switch the active environment.
- Support for variable syntax (e.g., `{{variable_name}}`) in:
  - URL
  - Headers
  - Request Body
  - Query Parameters

## 4. Non-functional Requirements
- **Data Storage**: All data (collections, environment settings) must be saved in JSON files in a local user or project directory.
- **No Database**: Do not use complex databases (SQLite, Postgres), only files.
- **Auth**: Specialized fields for authorization (Basic Auth, OAuth) are not required in the first version. Authorization is done via manual header addition (e.g., `Authorization: Bearer ...`).

## 5. Main Entities
1. **Request**: Method, URL, Headers, Parameters, Body.
2. **Collection**: Named group of requests.
3. **Environment**: Set of variables (Key-Value) for substitution in requests.

## 6. User Scenarios (Examples)
- User creates a new collection "My API".
- User creates an environment "Dev" with variable `base_url = http://localhost:8000`.
- User creates a POST request using `{{base_url}}/items` in the address bar.
- User sends the request and sees a formatted JSON response.
- User saves the request to the "My API" collection.
