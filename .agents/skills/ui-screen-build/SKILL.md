---
name: ui-screen-build
description: Use in an operational project to implement or structurally modify a screen, flow, page, form, HUD, or menu under a provisional or approved UI Foundation. Also use repair mode for focused defects such as icon-text misalignment, accidental two-line controls, cross-screen inconsistency, or excessive subtitle/helper copy. In an empty workspace project-bootstrap takes precedence; for initial UI or a full redesign use ui-project-start.
---

# UI Screen Build

All `.agents/`, `.codex/`, and `docs/` paths are relative to `<repo-root>/`. Apply `<repo-root>/.agents/references/project/repository-paths.md` first.

Extend the project's active UI grammar into real screens. Apply product tasks, the Foundation, the decision log, and the explicit scope of precedents instead of copying the surface of an existing screen.

## 0. Preconditions

- `empty`: stop and prioritize `$project-bootstrap`.
- `scaffolded`: unless this is a focused repair, complete baseline execution and managed AGENTS synchronization first.
- `operational`: continue to work-size classification.
- When a parent workflow loads this file directly, continue without waiting for another implicit invocation.

## 1. Determine work mode

Use `references/work-size.md` to select one. If screen boundaries are broad or interaction modes conflict, also apply the boundary test in `references/screen-classification.md`.

- `repair`: clipping, focus, contrast, state presentation, small alignment, or behavioral defect
- `extension`: new page, menu, region, or meaningful component within an existing flow
- `new-flow`: new top-level flow, core task, or interaction model

Do not force new documentation for repair. Use a compact screen contract for extension and the full contract for new-flow.

## 2. Confirm UI authority

Read the actual files:

- `<repo-root>/docs/ui/foundation.md`
- `<repo-root>/docs/ui/decision-log.md`, when present
- `<repo-root>/docs/ui/precedents.md`, when present
- relevant `<repo-root>/docs/ui/screens/*.md`
- `<repo-root>/docs/ui/tooling.md`, when present
- `<repo-root>/docs/ui/visual-invariants.md`, when present
- `<repo-root>/docs/ui/render-matrix.md`, when present
- existing code, tests, and actual data contracts

Apply `<repo-root>/.agents/references/ui/governance-status.md`.

### When there is no Foundation

- repair: make the smallest change while preserving existing behavior and accessibility constraints. Do not create a global pattern.
- extension or new-flow: route to `$ui-project-start`.

### Foundation states

- `draft`: reference only for repair or an explicitly labeled experiment; not a baseline for extension or new-flow
- `provisional` or `approved`: active baseline
- `superseded`: do not use for new work

If an extension or new-flow fundamentally changes the experience thesis, global navigation, layout grammar, or design signature, route to `$ui-project-start` in `evolution` mode rather than treating it as a screen addition.

Existing implementation may provide behavioral or technical evidence, but it is not the source of truth for design.

## 3. Classify the screen

Read:

- `<repo-root>/.agents/references/ui/interaction-modes.md`
- `<repo-root>/.agents/references/ui/state-model.md`
- `<repo-root>/.agents/references/ui/responsive-input.md`
- `<repo-root>/.agents/references/ui/pattern-justification.md`
- `<repo-root>/.agents/references/ui/perceptual-comfort.md`
- `<repo-root>/.agents/references/ui/narrative-restraint.md`
- for games, `<repo-root>/.agents/references/ui/game-context.md`
- otherwise, `<repo-root>/.agents/references/ui/non-game-context.md`

Summarize with `assets/ui-profile.template.yaml`:

- core user goal
- primary and secondary interaction modes
- information urgency and density
- input methods and viewport
- consequence of error and user expertise
- critical, primary, supporting, and optional information
- required states and stress content

Do not choose a layout from industry or game genre alone.

## 4. Screen contract

### repair

Review only the relevant rules in the existing contract and Foundation. Record in work notes:

- reproduction condition
- expected behavior
- scope that must not change
- post-fix revalidation

### extension

Use the core sections of `assets/screen-contract.template.md`. If a parent-flow contract exists, add the extension scope there. Otherwise, or when independent tracking is needed, create a compact contract at `<repo-root>/docs/ui/screens/<scope-slug>.md`.

### new-flow

Write the full contract at `<repo-root>/docs/ui/screens/<scope-slug>.md`.

The contract includes:

- core task and completion condition
- information priority and screen regions
- primary, secondary, and destructive actions
- navigation, back/cancel, and focus restoration
- state transitions and error recovery
- responsive and input adaptation
- real-content stress cases
- repeated-role visual invariants and text-fit/collapse policy
- copy inventory and explanation-deletion test
- tests and render-matrix conditions

A new contract begins `draft` and becomes `provisional` when established as the implementation baseline. Never mark it `approved` without explicit approval.

## 5. Existing patterns and new decisions

- Reuse components, tokens, and behavior that match the Foundation semantically.
- Reuse a precedent only within its recorded aspects and state scope.
- Do not force reuse when visual similarity hides different meaning or state.
- Do not create a generic visual container from one use case.
- If a required pattern is not covered by the Foundation, record the unmet requirement, alternatives, scope, and revisit condition in `decision-log.md` before introducing it provisionally.
- Do not silently change the Foundation for local implementation convenience.

## 6. Implement

- Implement semantic structure and domain state first.
- Use real or representative content fixtures.
- Implement required states, not only the normal state.
- Implement behavior and focus for every supported input: keyboard, touch, mouse, or gamepad.
- Reprioritize information on narrow screens; do not stop at vertical stacking.
- Decoration must not obstruct information or actions and must follow the Foundation's use conditions.
- Respect an approved design system, but do not use it as an excuse to preserve an unapproved prototype structure.
- Operational screens lead with real objects, state, and actions. Do not add prose that merely restates headings, controls, or layout.
- Persistent copy must serve identification, state, constraint, consequence, recovery, or rationale. Keep first-use guidance contextual or dismissible.
- Do not leave control-label wrapping to the browser. Apply an explicit collapse ladder such as full label → short label → icon-only → overflow.

## 7. Perceptual Polish Pass

After functionality and required states work, run a separate pass without changing product direction:

1. initial focal point and scan path at normal viewing scale
2. grouping and repeated alignment lines
3. text baselines and control heights
4. optical icon size and icon-label gaps
5. accidental wrapping, clipping, and overflow
6. typography and spacing rhythm
7. visual weight and competing emphasis
8. layout shift caused by loading, badges, validation, and errors
9. comparison with the same semantic role on another screen or precedent
10. copy necessity and the deletion test for explanatory subtitles, helper paragraphs, and feature cards

Rerender every affected viewport, state, and content condition. If the fix requires a Foundation or global information-architecture change, record it in the decision log or route to `$ui-project-start` evolution instead of hiding it in polish.

## 8. Validate

Apply:

- `<repo-root>/.agents/references/ui/visual-validation.md`
- `<repo-root>/.agents/references/ui/state-model.md`
- `<repo-root>/.agents/references/ui/perceptual-comfort.md`
- `<repo-root>/.agents/references/ui/narrative-restraint.md`
- `references/completion-gates.md`

Keep separate results for:

- technical: build, type/static analysis, tests, lint
- states: normal, loading, empty, partial, error/recovery, success, unavailable
- content: long strings, maximum items, missing images, large values
- adaptation: primary viewports and input methods
- conformance: Foundation, decision log, screen contract
- perceptual quality: alignment, text fit, icon-label composition, rhythm, visual weight, layout stability
- narrative restraint: persistent copy roles, prose dominance, empty state, deletion test
- drift: unjustified cards, dashboard shells, decoration, and regression into the initial prototype

Use actual paths from `<repo-root>/docs/ui/tooling.md`. For extension and new-flow, create or update `<repo-root>/docs/ui/visual-invariants.md` and `<repo-root>/docs/ui/render-matrix.md`. For repair, add only affected roles and render-matrix rows. Anything not run remains `unverified`. Perceptual quality and narrative restraint remain `unverified` when only source or tokens were inspected.

For a new-flow or visually substantial extension, run a review-only `ui_auditor` or `$ui-critic` review when possible.

## 9. Completion and document updates

- Update the screen contract with actual implementation and validation state.
- Update relevant visual invariants and render-matrix rows.
- Update keep/defer/remove/rewrite decisions in the copy inventory.
- Update the decision log when a new decision was introduced.
- Never register a precedent as `approved` automatically.
- Report validated reusable aspects as `provisional` precedent candidates; register them only when that is within the request and project policy.
- If the user requests approval, use `$ui-critic` in `approval-review` mode so the Foundation, visual invariants, render matrix, precedent, and decision log change together.
- Update `<repo-root>/docs/plans/current.md` only when a milestone, blocker, or validation checkpoint changed materially.

Final report:

1. work mode and UI profile
2. core structural and interaction decisions
3. files changed
4. actual technical, state, rendering, perceptual, and copy validation with results
5. unverified conditions
6. whether the Foundation or decision log changed
7. whether a precedent candidate exists
