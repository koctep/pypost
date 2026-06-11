# PYPOST-67: Dev Docs

## Updated files

- `doc/dev/environment_encryption_at_rest.md` — documents `reload_current_env()` in settings flow

## Summary

Developer documentation now references the public `EnvPresenter.reload_current_env()` API used
after settings save instead of the private `_on_env_changed` handler.
