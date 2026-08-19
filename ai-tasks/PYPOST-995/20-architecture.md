# PYPOST-995: Architecture Design

## CI Lock Verification Architecture

GitHub Actions workflow `.github/workflows/test.yml` runs lock checks to ensure `requirements*.txt` files match their respective `.in` manifests:

1. `check-lock`: runs `make check-lock` for `requirements.txt` / `requirements.in`.
2. `check-lock-dev`: runs `make check-lock-dev` for `requirements-dev.txt` / `requirements-dev.in`.

Both jobs now pin `astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990` with `version: "0.11.31"` to prevent unpinned uv resolver drift across CI runs.
