# UI Completion Gates

Rate every item `pass`, `fail`, `unverified`, or `not-applicable`.

## Task

- The core task and primary action are clear.
- Information appears in the user's decision order.
- The user's location after success, cancel, and failure is clear.

## Foundation

- The implementation follows the experience thesis and layout grammar.
- The design signature appears where required.
- It does not introduce an unjustified prohibited default.
- Exceptions are recorded in the decision log.

## State

- Applicable loading, empty, partial, error, and success states are implemented.
- Disabled, unavailable, locked, and permission states are distinct.
- Error recovery preserves input and context.

## Input and adaptation

- Focus, selection, and cancellation work for supported inputs.
- Information priority holds in key narrow and wide viewports.
- Meaning does not depend on hover or color alone.
- Wrapping, short-label, icon-only, and overflow transitions are explicit.

## Content

- Long strings, many items, missing images, and large values are handled.
- Localization, dates, and currency are reviewed when relevant.
- Real-time values communicate freshness and change.
- Production and fallback fonts are reviewed in applicable environments.

## Perceptual comfort

- Repeated alignment lines and baselines are stable.
- Height, padding, typography, and state treatment are consistent for the same semantic role.
- Optical icon-label alignment and gaps are stable in rendering.
- Typography, spacing rhythm, and visual weight support hierarchy.
- Loading, validation, badges, errors, and content changes do not disturb primary layout unnecessarily.
- The same role was compared with another screen or precedent, or explicitly marked `unverified`.

This gate cannot pass without actual rendered evidence.

## Narrative restraint

- Real objects, state, and actions appear before explanatory prose.
- Page subtitles, helper paragraphs, and feature-description cards do not repeat visible structure.
- Persistent text serves identity, state, constraint, consequence, recovery, or rationale.
- First-use guidance is not permanently visible in recurring workflows.
- Empty states do not become feature-marketing pages.
- The explanation-deletion test was run and unnecessary copy was removed or deferred.
- High-stakes screens still explain outcomes, risks, and rationale adequately.

If the full rendered copy was not reviewed, this gate is `unverified`.

## Evidence

- actual technical command results
- actual rendering or an explicit unverified record
- recorded state, viewport, input, and font conditions
- related visual-invariant and render-matrix rows
- Perceptual Polish Pass and explanation-deletion results
