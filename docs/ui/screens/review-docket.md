# Review Docket Screen Contract

state: provisional  
route: `/`  
primary action: inspect a frozen case's verified review selection

## Required states

- loading and run-disabled
- fixed candidates with no review
- verified review with exact evidence
- insufficient evidence
- rejected unsupported output
- clean/restore case with zero verified findings
- API failure with a visible recovery message

## Inputs

- Mouse/touch selection of a candidate row.
- Keyboard focus and activation for case select, Run case, and source buttons.

## Non-goals

No change editing, source mutation, reviewer approval, prompt display, or live Vertex call from the browser.
