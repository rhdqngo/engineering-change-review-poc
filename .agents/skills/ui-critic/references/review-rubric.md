# UI Review Rubric

## Task fit

- The core goal and primary action can be explained in one sentence.
- Information appears in the order the user needs to make decisions.
- Decoration, promotion, and supporting information do not overpower the core flow.

## Foundation conformance

- The experience thesis and design signature are visible in actual structure and interaction.
- The screen follows the layout grammar and navigation model.
- It follows role rules in visual invariants and the screen contract.
- Exceptions are recorded in the decision log.
- Draft or superseded standards are not used for new work.

## Information architecture

- Persistent, contextual, transient, and detailed information are distinct.
- Comparable items use the same axes and units.
- Visual weight reflects importance and urgency.
- Names and formats are consistent.

## State and recovery

- Applicable loading, empty, partial, error, and success states exist.
- Disabled, unavailable, locked, and permission states are distinct.
- Recoverable errors preserve input and context.
- Stale/offline data and duplicate execution are handled when relevant.

## Input and adaptation

- Supported input methods actually work.
- Focus, selected, active, disabled, and locked states are distinct.
- Narrow layouts reprioritize information.
- Full-label, short-label, icon-only, and overflow transitions are explicit.
- Wide layouts are not filled with meaningless information.

## Accessibility and clarity

- Structure and labels are meaningful.
- Focus and restoration are predictable.
- Meaning does not depend on color alone.
- Error cause and corrective action are close together.
- Alternatives are considered for time limits, motion, and sound.

## Perceptual comfort and cross-screen consistency

- Actual rendering was reviewed at a normal viewing scale.
- Initial focal point and scan path support the task.
- Repeated alignment lines and text baselines are stable.
- Height, padding, typography, and state presentation are consistent for the same semantic role.
- Optical icon size, viewBox, and icon-label gap are stable.
- Typography and spacing rhythm support grouping.
- Badges, validation, loading, and errors do not push primary actions unnecessarily.
- Production/fallback fonts, long localization, and maximum content were reviewed.
- The same role was compared with another screen or precedent.

The following are generally `major`:

- a primary control repeatedly wraps accidentally in a supported viewport
- the same role has different height or state treatment across screens and may spread as precedent
- an error or validation message pushes the primary action off-screen
- a trailing action in a repeated row drifts with content length

## Narrative restraint and copy necessity

- The first region presents real objects, state, and actions.
- Page title and subtitle do not repeat the same meaning.
- Helper text does not restate a visible label or control action.
- Feature-description cards do not replace the feature itself.
- First-use guidance is not permanently visible in recurring workflows.
- Empty states do not become feature-marketing surfaces.
- Persistent copy serves identity, state, constraint, consequence, recovery, or rationale.
- The explanation-deletion test removes or defers unnecessary copy.
- High-stakes actions explain outcomes, risk, and rationale adequately.

The following are generally `major`:

- prose appears before real data and actions in a recurring workflow
- the same concept repeats in navigation, title, subtitle, section, and card
- multiple helper paragraphs hide weak structure
- explanatory feature cards are likely to become production precedent

## Evidence

- actual technical command results
- actual rendering of key states
- primary viewport, input, and font validation
- links to visual invariants and render-matrix rows
- copy inventory and deletion-test evidence
- explicit record of anything not verified

## Overall verdict

- `pass`: every must-pass gate passes and there are no findings
- `pass with minor findings`: every must-pass gate passes, with no blocker or major finding
- `fail`: at least one must-pass gate fails, or a blocker/major finding exists
- `unverified`: evidence is insufficient to judge one or more critical gates
