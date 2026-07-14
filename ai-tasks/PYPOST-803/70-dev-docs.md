# PYPOST-803: Dev Docs

## Updated

- `doc/dev/ui_font_and_styles.md` — added PYPOST-803 closure note under font inheritance;
  clarified that Collections/Tabs presenters do not need `apply_font`.

## Summary

Document that presenter font propagation is handled exclusively by
`StyleManager.apply_appearance`. Presenter `apply_settings` methods remain responsible
for indent size and JSON syntax colors only.
