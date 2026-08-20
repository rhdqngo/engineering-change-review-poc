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
- Keyboard focus and activation for case select, `Reload result`, and source buttons.

## Non-goals

No change editing, source mutation, reviewer approval, prompt display, or live Vertex call from the browser.

## V2 repair scope

- Preserve the Docket layout, candidate comparison, evidence gate, and fixture behavior.
- Rename the saved-result control to `Published Cloud evaluation`.
- Show published run ID and source-commit provenance in the existing environment/footer roles.
- Do not add a Job execution control or persistent explanatory paragraph.

## V3 loading-state repair

- Initial Evidence desk state says `Loading review disposition…`; it does not instruct the user to run a case.
- `Reload result` remains disabled until the initial result resolves.
- Loaded, error, fixture, published, evidence, and responsive behavior remain unchanged.

## V4 interaction-integrity repair

- Only the latest case/source request may update result state, provenance, errors, or action availability; superseded requests are aborted and ignored.
- `Reload result` remains a single-line control at 390 × 844 without creating body-wide overflow.
- If keyboard focus owned Reload when it initiated the latest request, focus returns after the control is re-enabled. Case/source initiated loads retain their native control focus.
