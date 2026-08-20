# UI Work Size

## repair

Appropriate for:

- clipped focus ring
- label/icon alignment or optical mismatch
- accidental one-line/two-line transitions
- inconsistent control height, spacing, or state presentation across screens
- removing subtitles or helper copy that merely narrates structure
- a missing focused state
- overflow under long strings
- a localized defect for one input method
- a small style regression that clearly violates the Foundation

Principles:

- do not create a new global pattern
- do not redesign the entire screen
- validate only the reproduction condition and related states
- do not force a new contract

## extension

Appropriate for:

- a new page, tab, panel, or menu inside an existing flow
- a meaningful component that extends the same information architecture
- a new group of states or actions added to an existing screen

Principles:

- compact profile and contract
- solve within the Foundation grammar
- record a new pattern in the decision log
- validate key states and viewports

## new-flow

Appropriate for:

- a new top-level user task
- a new navigation boundary
- a core flow such as checkout, permissions, onboarding, or combat HUD
- a new interaction mode that changes screen structure

Principles:

- full profile and contract
- state matrix
- actual rendering and independent review
- route to ui-project-start when no active Foundation exists
