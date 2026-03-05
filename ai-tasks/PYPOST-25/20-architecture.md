# Architecture: PYPOST-25 - MCP Testing Collection

## Research
No complex architecture required. This is a data creation task.

## Implementation Plan

1.  **Create Environment**:
    -   Name: "Test Env".
    -   Variables: `base_url=https://httpbin.org`.
    -   Enable MCP: True.

2.  **Create Collection**:
    -   Name: "MCP Test".
    -   Requests:
        1.  **Get Data**: GET `{{base_url}}/get`. Expose: True.
        2.  **Post Data**: POST `{{base_url}}/post`. Body: `{"foo": "bar"}`. Expose: True.
        3.  **Script Test**: GET `{{base_url}}/uuid`. Script: `pypost.env.set('uuid', response.json()['uuid'])`. Expose: True.

3.  **Save**:
    -   Save files to `collections/` and root (for `environments.json`).

## Architecture

### File Structure

```
pypost/
  collections/
    MCP_Test.json
  environments.json
```
