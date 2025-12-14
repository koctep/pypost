# Technical Debt for Task PYPOST-25

## 1. Variable Name Validation
Currently, when creating a new variable via the context menu, only a check for an empty string is performed. It is necessary to add validation for allowed characters (alphanumeric + underscore) to ensure compatibility with Jinja2 templates.

## 2. Signal Connection
The `variable_set_requested` signal is connected in `add_new_tab`. It is worth considering a more centralized way of connecting signals for dynamically created widgets.
