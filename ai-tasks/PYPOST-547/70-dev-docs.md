# PYPOST-547: Dev Docs

Updated `doc/dev/collection_tree_actions.md` helper table with PYPOST-547 additions.

Test patch guidance (unchanged pattern): patch helpers at the caller module import path, e.g.
`pypost.ui.presenters.env_presenter.show_invalid_variable_name_error` or
`pypost.ui.dialogs.settings_dialog.show_migration_result`.
