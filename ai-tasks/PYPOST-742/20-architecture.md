# PYPOST-742: Architecture

Add module-level `logger = logging.getLogger(__name__)` to `ConfigManager` and map each former
`print()` to `logger.error` with event names:

- `config_directory_create_failed`
- `config_load_failed`
- `config_save_failed`
