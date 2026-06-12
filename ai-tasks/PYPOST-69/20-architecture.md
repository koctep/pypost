# PYPOST-69: Architecture — remove unused Environment import

## Change

Single-line import cleanup in `pypost/ui/presenters/tabs_presenter.py`:

```python
# Before (PYPOST-43 TD-4)
from pypost.models.models import RequestData, Environment

# After
from pypost.models.models import RequestData
```

## Components affected

| File | Change |
|------|--------|
| `pypost/ui/presenters/tabs_presenter.py` | Remove unused `Environment` from models import |

## No behavioral impact

`TabsPresenter` never referenced `Environment`. Environment selection and
variable propagation remain handled by `EnvPresenter` and signal wiring in
`MainWindow`.

## Note

The import removal landed earlier in PYPOST-437 (hidden-variable work). This
task verifies the fix and closes TD-4 formally.
