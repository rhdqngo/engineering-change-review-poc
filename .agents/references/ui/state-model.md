# UI State Model

Define state as part of the user's task, not as a decorative variation. For a state that does not apply, record `N/A` and the reason. A blank cell means unresolved.

## Core data states

- `idle / ready`
- `initial-loading`
- `refreshing`
- `empty`
- `partial`
- `error`
- `success / completed`
- `stale / offline`

## Action-availability states

- `enabled`
- `disabled`: cannot run under the current conditions; explain why when useful
- `unavailable`: the feature or resource is not provided
- `locked`: becomes available after a condition is met
- `permission-denied`: the user lacks permission
- `busy / submitting`: prevents duplicate execution and communicates progress

Do not collapse `disabled`, `unavailable`, `locked`, `not-owned`, and `not-selected` into the same presentation.

## Selection and ownership states

- selected
- active
- equipped / applied
- owned
- new / unread
- compared / pinned

Use only the states required by the screen's purpose and keep names and meanings consistent.

## Recovery principles

- Preserve input, filters, selection, and scroll position after recoverable errors.
- Define where the user returns after retry.
- For partial results, explain what is missing and what actions remain available.
- Connect completion feedback to the result and the next step.
- Do not remove already valid information unnecessarily during a background refresh.

## State matrix

```markdown
| Screen / region | ready | loading | refreshing | empty | partial | error | success | disabled | locked | stale/offline | permission |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |  |  |  |  |
```
