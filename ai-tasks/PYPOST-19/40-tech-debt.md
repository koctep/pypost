# PYPOST-19: Technical Debt Analysis


## Shortcuts Taken

- **No Input Validation**: The host input field is a simple text field. There is no validation for IP address format or hostname validity. If an invalid host is entered, the server will fail to start (error will be logged, but user might not understand why). — [PYPOST-149](https://pypost.atlassian.net/browse/PYPOST-149)
    - *Mitigation*: Add regex validator or `QHostAddress` validation in the future.

## Missing Tests

- No automated tests verifying that the server actually binds to the specified host. Testing is manual (using `netstat` or connecting from external). — [PYPOST-150](https://pypost.atlassian.net/browse/PYPOST-150)

## Follow-up Tasks

- Add validation for Host and Port fields in `SettingsDialog`. — [PYPOST-151](https://pypost.atlassian.net/browse/PYPOST-151)
