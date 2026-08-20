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

## V5 active-contract extension

work size: extension
foundation: provisional 0.1

### UI profile

- Core goal: compare the fixed candidate set with the verified disposition for any of the 18 active v5 cases, then inspect exact evidence or the fail-closed reason.
- Primary mode: monitor-analyze. Secondary mode: browse-compare.
- Audience and consequence: engineering reviewer; dense evidence review; a mistaken visible recommendation is recoverable only by withholding it.
- Viewports and input: 1440 × 900 and 390 × 844; mouse, touch, and keyboard.
- Critical information: result source, active experiment/run provenance, case identity, changed source, original/changed content, final disposition, exact evidence, verifier outcome, blocked stage.
- Stress states: initial loading, published unavailable/integrity failure, rapid case/source switching, no-review control, unsupported proposal, long source IDs and code spans.

### Structure and behavior

- The change strip adds a three-field comparison: changed source, original exact content, and changed content. It remains above the fixed candidate docket and does not become a separate card.
- Fixture and published selection retain the same candidate comparison and evidence desk, but provenance must identify fixture data as non-experiment evidence and published data by experiment, run, commit, manifest, and embedding-index fingerprint when available.
- Loading keeps Reload disabled. Recoverable API failure preserves source/case selection and exposes the existing retry action. Only the latest request may update the screen.
- Loading and result failure clear the prior candidate, evidence, counts, seal, and provenance before the selected case/source identity can be interpreted as owning them.
- Every `REJECTED_UNSUPPORTED` record, including duplicate-source and off-Top-K records, appears in the Fail-closed audit list with its source and blocked stage; selection never exposes its proposed evidence.
- At narrow width, the change comparison collapses in information order; the candidate docket remains the only horizontally scrolling region and is a named focusable region with explicit ArrowLeft/ArrowRight/Home/End scrolling.
- Visible compact candidate and index hashes retain their complete value through an accessible title/name.
- Initial catalog failure shows the server detail and changes Reload into `Retry catalog`; retry replaces options and handlers without duplication.

### Copy inventory

| Text / region | Role | Default visibility | Why structure alone is insufficient | Decision |
| --- | --- | --- | --- | --- |
| Result-source option labels | identity | persistent | Fixture and published evidence have different authority. | keep |
| Changed source / Original / Changed | identity / decision data | persistent | Exact mutation provenance is required for review. | keep |
| Fixture non-evidence note | constraint | persistent in fixture | Prevents deterministic fixture output from being mistaken for measured LLM evidence. | keep |
| Published provenance sequence | state / rationale | persistent in published | Run, manifest, commit, and index identity are not visible in the candidate table. | keep |
| Loading / API error text | state / recovery | contextual | Disabled control alone does not explain availability or failure. | keep |
| Page-operating instructions | none | hidden | Native controls and object labels already communicate the flow. | remove |

### V5 acceptance

- Technical: API/UI tests, Ruff, mypy, package build, and script parsing pass.
- Render: desktop and narrow normal/loading/error/recovery/no-review/verified/blocked states are reviewed at normal scale.
- Interaction: keyboard Reload focus restoration, candidate activation, table horizontal scrolling, touch-sized source controls, rapid case/source switching, all blocked-record selection, and catalog/result error recovery pass.
- Explanation deletion: hide non-state helper prose; the task remains understandable from source/case controls, change comparison, docket, and evidence desk.
- Governance: no Foundation or new global pattern change; this extension remains provisional.
