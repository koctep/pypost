# Environment repository migration boundary

The runtime continues to use `StorageManager` as the only collection/environment
persistence implementation. Experimental `pypost/ports` and `pypost/adapters`
repository prototypes are not imported or packaged as a second runtime path.

Before a repository implementation can replace `StorageManager`, migration must
follow this order:

1. Read legacy `environments.json` through the existing
   `EnvironmentVariablesAdapter` and configured key-provider chain.
2. Preserve environment IDs, ordering, hidden-key metadata and the current
   encrypted envelope; never serialize an `Environment.model_dump()` directly.
3. Write the candidate format atomically, then read it back through the same
   `EnvironmentSecretsCodec` and compare the logical environments.
4. Keep the legacy file as a recovery source until the verified write succeeds.
5. Switch the composition root to exactly one environment repository. Do not let
   old and new implementations write the same aggregate concurrently.

The executable contract in `tests/test_architecture_boundaries.py` prevents a
prototype import into production and proves that a hidden value is absent from
the persisted plaintext while still round-tripping through `StorageManager`.
