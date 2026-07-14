# PYPOST-796: Improve close.svg contrast on dark tab chrome

## Goals

PyPost tab bars display a close control on closable tabs using bundled SVG icons referenced from
global QSS. PYPOST-792 restored native tab layout on macOS; manual verification noted that the
**default** close icon (`close.svg`) is hard to see on **dark native tab chrome** at the platform
close-indicator size, while the **hover** icon (`close-hover.svg`) remains clearly visible.

This task improves **accessibility and usability** for users running the application with dark
system appearance or dark-themed tab chrome: the default close control must be discernible without
requiring hover, so users can locate and activate tab close reliably.

**Business intent:** Reduce friction and eye strain when closing tabs in dark mode; close the
follow-up opened from PYPOST-792 / PYPOST-793 technical-debt tracking.

## Programming Language

Python (existing PyPost desktop application codebase). The user-visible change is a bundled SVG
asset consumed by Qt stylesheets; no new Python modules are required unless validation tests are
added.

## User Stories

- As a **PyPost user** on macOS (or any platform with dark native tab chrome), I want the default
  tab close icon to be clearly visible, so I can close tabs without hunting for a faint control.
- As a **user with low vision**, I want sufficient contrast between the close icon and the tab
  background in its default state, so the control meets practical accessibility expectations.
- As a **maintainer**, I want the icon fix isolated to the bundled asset (and docs), so native tab
  layout and close-indicator metrics from PYPOST-792 are not regressed.

## Definition of Done

- **Default close icon contrast improved:** `close.svg` stroke colour provides materially better
  contrast on dark native tab chrome at native `PM_TabCloseIndicator` size compared to `#666666`.
- **Hover unchanged:** `close-hover.svg` behaviour and appearance remain as today (already visible).
- **No tab layout regression:** Native tab geometry, close-indicator metrics, and QSS policy from
  PYPOST-792 unchanged (`QTabBar::close-button` icon rules only; no `::tab` box-model styling).
- **Automated checks pass:** `make check` passes (flake8 + full test suite).
- **Documentation:** Developer docs reflect the updated default icon colour and troubleshooting
  guidance (Step 7).

## Task Description

**Problem:** The bundled `close.svg` uses `#666666` stroke. On dark tab chrome at native indicator
size, the icon blends into the background. Hover state (`close-hover.svg` with light pill +
`#333333` stroke) is fine; only the **default** state needs improvement.

**Why now:** Explicit follow-up from PYPOST-792 manual macOS verification, tracked as medium-priority
accessibility/polish debt in PYPOST-793.

### Functional requirements

- Update the default close icon asset so stroke colour improves visibility on dark tab chrome.
- Preserve icon geometry, viewBox, stroke width, and QSS wiring (`main.qss` close-button rules).
- Do not change hover icon unless required for visual consistency (not expected).

### Non-functional requirements

- **Accessibility:** Target improved contrast on dark backgrounds; aim for practical WCAG non-text
  contrast (~3:1 or better against typical dark tab chrome).
- **Cross-theme sanity:** Default icon should remain usable on light tab chrome where possible
  (single SVG colour is a known trade-off).
- **No behavioural regression:** Tab close interaction, metrics, and layout unchanged.

### Constraints and assumptions

- Scope is **icon contrast only** — not tab styling policy, not `PyPostStyle` metrics, not theme
  pipeline changes (PYPOST-793).
- Single bundled SVG colour; Qt QSS does not support theme-conditional SVG tinting without code
  changes (out of scope unless contrast cannot be achieved with one colour).
- Implementation is an asset update plus documentation; observability/logging not applicable.

### In scope

- `pypost/ui/resources/icons/close.svg` stroke colour adjustment.
- Developer documentation update for icon colours and troubleshooting.
- Regression verification via existing tab layout / style tests and `make check`.

### Out of scope

- Redesign of hover icon or adding default-state background pill.
- Theme-specific icon variants or runtime SVG recolouring.
- Changes to `PyPostStyle` close-indicator size policy.
- Makefile `help` target (PYPOST-794) or appearance pipeline consolidation (PYPOST-793).

### Main entities (business perspective)

| Entity | Role |
| --- | --- |
| Tab close control | User-facing control to dismiss a tab; default and hover visual states. |
| Bundled tab icons | Static SVG assets scaled into native close-indicator metrics. |
| Native tab chrome | Platform-rendered tab appearance (dark or light) behind the close icon. |
| Global stylesheet | Applies close-button icon images without altering tab geometry (PYPOST-792). |

## Q&A

- **Q**: Why not add a background pill to the default icon like hover?
- **A**: Hover deliberately uses a pill for emphasis. Default should stay minimal; stroke lightening
  is the scoped fix per Jira description.

- **Q**: Will one stroke colour work on both light and dark tabs?
- **A**: Partially — a lighter stroke improves dark chrome (primary goal) with a modest trade-off on
  very light chrome. Acceptable for this accessibility follow-up; theme-specific icons are out of
  scope.

- **Q**: Source references?
- **A**: Jira [PYPOST-796](https://pypost.atlassian.net/browse/PYPOST-796); parent context
  [PYPOST-792](https://pypost.atlassian.net/browse/PYPOST-792) tech-debt item; follow-up listed in
  `ai-tasks/PYPOST-793/60-tech-debt.md`.
