# Roadmap: PYPOST-614

## Step Status

- [x] **STEP 1–7** — verification-only closure

## Notes

`Makefile` `test`, `test-slow`, and `test-cov` targets already set `QT_QPA_PLATFORM=offscreen`
(lines 32, 36, 40). CI sets the same in `.github/workflows/test.yml`.
