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
- published GCS result unavailable or invalid with a visible retry path and no local fallback in Cloud

## Inputs

- Mouse/touch selection of a candidate row.
- Keyboard focus and activation for case select, Run case, and source buttons.

## Non-goals

No change editing, source mutation, reviewer approval, prompt display, or live Vertex call from the browser.

## V2 repair scope

- Preserve the Docket layout, candidate comparison, evidence gate, and fixture behavior.
- Rename the saved-result control to `Published Cloud evaluation`.
- Show published run ID and source-commit provenance in the existing environment/footer roles.
- Do not add a Job execution control or persistent explanatory paragraph.
