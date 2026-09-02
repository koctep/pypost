# PYPOST-1245: Centralize validation palette colors and popup geometry constants

## Goals

Provide one consistent set of UI theme tokens so validation feedback and autocomplete
popups can be restyled for custom themes and remain predictable when display scaling changes.
This reduces visual drift and makes future theme work safe and discoverable.

## User Stories

- As a user, I want validation feedback to use a consistent palette across editors and tables.
- As a user, I want autocomplete popups to remain usable across display scale factors.
- As a theme maintainer, I want validation colors and popup dimensions defined in one shared place.

## Definition of Done

- Validation background, foreground, underline, and feedback-label colors have shared names.
- Autocomplete popup width, row height, padding, and maximum height have shared names.
- Existing validation and popup behavior remains unchanged under the default theme.
- QSS exposes theme-sensitive validation and popup styling without duplicating literal colors.
- Tests demonstrate token values are used by all affected validation and popup paths.

## Task Description

The UI currently repeats literal validation colors and popup dimensions in separate widgets.
Centralize these values as shared UI theme tokens and use stylesheet palette roles where Qt
styling is appropriate. Keep this task limited to validation feedback and autocomplete popup
styling; broader theme redesign and performance changes are out of scope.

## Q&A

- Why is this needed? To support custom theme styling and high-DPI scaling without editing
  multiple widgets or allowing their visual behavior to diverge.
- Which language is used? Python, with Qt stylesheets for widget styling.

