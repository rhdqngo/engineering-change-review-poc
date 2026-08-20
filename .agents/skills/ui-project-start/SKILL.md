---
name: ui-project-start
description: Use in an operational product, app, or game to establish its first UI direction or structurally reset an existing generic, practice, template-driven, or overly explanatory UI. Apply to initial UI, full redesign, establishing a visually comfortable direction, or large-scale restructuring that removes excessive explanatory copy. In an empty workspace without a manifest, project-bootstrap takes precedence. Do not use for routine screens under an active Foundation or focused defects.
---

# UI Project Start

All `.agents/`, `.codex/`, and `docs/` paths are relative to `<repo-root>/`. Apply `<repo-root>/.agents/references/project/repository-paths.md` first.

Prevent the first implementation from becoming the project's accidental design system. Start from product tasks and real content, compare multiple structural directions, and validate the selected direction with isolated concept probes and a representative vertical slice.

## 0. Preconditions and routing

- If the project state is `empty`, do not begin production UI with this skill. Run `$project-bootstrap` first.
- If the project is `scaffolded`, complete baseline execution and synchronize the AGENTS managed blocks first.
- Proceed when the project is `operational` or existing UI code is actually runnable.
- When this workflow is loaded directly inside bootstrap, continue within the original request instead of waiting for another implicit invocation.

## Results

Create documents appropriate to the project's scope and these outputs:

- product and UI brief
- three structurally distinct directions
- isolated concept probes using matched content, or an explicit `unverified` record
- selection rationale and active `<repo-root>/docs/ui/foundation.md`
- `<repo-root>/docs/ui/visual-invariants.md` and `<repo-root>/docs/ui/render-matrix.md`
- representative vertical slice
- UI tooling plus functional, perceptual, and copy-validation evidence
- precedent candidates with explicit governance state

Never create `approved` without explicit user or team approval.

## Non-negotiable rules

- Existing UI is not design precedent merely because it is in the repository.
- Do not implement broad production UI before selecting a direction.
- Concepts that differ only in color, theme, radius, shadow, or font do not count as separate directions.
- Do not compare probes that use different content or states.
- Do not reuse probe code as production components.
- Do not create a generic design system before defining real content shapes and key states.
- Do not generalize `Card`, `Panel`, `Section`, `Tile`, or `Box` from one use case.
- Do not choose a landing page as the vertical slice unless it is the core product.
- Build success is not visual or interaction validation.
- Do not default to subtitles, helper paragraphs, or feature-description cards that explain operational UI.
- Reject a direction, absent strong justification, when prose appears before real objects, state, and actions.
- Do not pass perceptual comfort or narrative restraint from code and tokens alone.

## 1. Change mode

Choose one from actual repository evidence and the user request:

- `greenfield`: no meaningful UI or active Foundation exists
- `reset`: preserve functionality but reject the current UI direction or escape a generic AI prototype
- `evolution`: an active Foundation exists, but core strategy, platform, or task has changed substantially

For `reset` and `evolution`, use `references/discovery.md` and `assets/authority-map.template.md` to separate UI authority. Preserve data, routing, domain state, accessibility, and performance constraints where useful, but do not preserve layout and visual hierarchy automatically.

## 2. Documentation level

Use `references/scope-levels.md` to choose `lite`, `standard`, or `extended`.

- Do not impose full governance documentation on a small experiment.
- Use at least `standard` for a long-lived product, multiple screens, or multiple inputs/platforms.
- Create `authority-map.md` primarily for reset and evolution work.

Record the level and rationale in the brief.

## 3. Brief and real content

Use `assets/ui-brief.template.md`.

Determine:

- primary user and recurring task
- usage environment, platform, and input
- game or non-game context
- primary and secondary interaction modes
- information urgency, density, and cost of error
- actual or representative content shapes
- stress cases such as long localization strings, empty data, many items, missing images, and large values
- principles to adopt from references and surface-level imitation to avoid
- non-goals and success criteria

Translate adjectives such as `clean`, `modern`, `immersive`, and `premium` into observable structure and behavior.

Always read:

- `<repo-root>/.agents/references/ui/interaction-modes.md`
- `<repo-root>/.agents/references/ui/state-model.md`
- `<repo-root>/.agents/references/ui/responsive-input.md`
- `<repo-root>/.agents/references/ui/pattern-justification.md`
- `<repo-root>/.agents/references/ui/perceptual-comfort.md`
- `<repo-root>/.agents/references/ui/narrative-restraint.md`
- `<repo-root>/.agents/references/ui/governance-status.md`

For games, also read `<repo-root>/.agents/references/ui/game-context.md`. For non-game products, read `<repo-root>/.agents/references/ui/non-game-context.md`.

## 4. Three structurally distinct directions

Use `references/concept-divergence.md` and `assets/concept-direction.template.md`.

When custom agents are available, run the **same `ui_concept` agent three times independently**:

1. information architecture and task-flow lens
2. interaction and disclosure lens
3. product identity and spatial-model lens

Give every run the same brief, authority map, content, states, and technical/input constraints. Do not provide another candidate's output. Check `git status --short` before and after subagent runs to verify the read-only boundary.

If custom agents are unavailable, write three directions sequentially without reskinning the previous layout.

Every direction defines:

- experience thesis
- information architecture and screen boundaries
- navigation model
- spatial composition
- density and disclosure
- persistent, contextual, and transient information
- primary interaction and feedback
- key states, input, and responsive rules
- structural, interaction, and, when needed, visual design signatures
- repeated alignment lines, text fit, icon-label composition, spacing rhythm, and transition stability
- roles for persistent copy and rules for moving explanation into context
- advantages, risks, implementation cost, and failure conditions

Each pair of directions must differ meaningfully on at least four structural dimensions. If it does not, regenerate the most similar direction.

## 5. Visual concept probes

Use `references/probe-workflow.md`.

When the project can render real UI, create one low-fidelity representative screen or state for each direction.

- use the same real content, long localization, copy roles, production/fallback font, viewport, and state
- isolate probes in a Storybook story, dev-only route, engine test scene, or separate prototype path
- exclude probes from production navigation, exports, and builds
- do not extract shared UI components
- do not connect production data layers
- show one central structural and interaction idea per direction
- record screenshots or video and paths under `<repo-root>/docs/ui/probes/`

If rendered probes are impossible, create structural diagrams and state flows and record `visual probe: unverified`. Do not claim visual validation from text concepts alone.

## 6. Select a direction

Evaluate concepts and probes with `references/selection-rubric.md`.

### Requests that stop after comparison

Show recommendations and tradeoffs, then stop before implementation when the intent is clearly:

- “show me the options”
- “compare them”
- “do not implement yet”
- “let us decide the direction first”

### Requests that authorize autonomous completion

For “build it,” “implement it,” or “complete the work,” choose the highest-scoring direction and continue with a `provisional` Foundation.

When tightly competing directions have high reversal cost—payment, medical, permissions, brand transition, competitive fairness, or platform choice—ask for a selection before proceeding.

Record why the selected direction won, why the others lost, and which rejected elements must not leak into the selected direction. Use `<repo-root>/docs/ui/decision-log.md` for `standard` and `extended`, or the selection section of `<repo-root>/docs/ui/concepts/overview.md` for `lite`.

## 7. Write the Foundation

Create `<repo-root>/docs/ui/foundation.md` from `assets/ui-foundation.template.md`.

The initial active state is `provisional`. The Foundation defines a UI grammar rather than a fixed page template:

- product-experience thesis and design signature
- information priority and freshness
- layout relationships and density
- navigation and disclosure
- component semantics and abstraction thresholds
- states, errors, recovery, and feedback
- input and responsive adaptation
- accessibility and localization
- perceptual comfort, visual invariants, and text-fit policy
- narrative restraint, persistent/contextual copy, and marketing boundary
- unjustified defaults to avoid
- exceptions and change procedure

If `<repo-root>/docs/ui/tooling.md` is absent, copy `<repo-root>/docs/ui/tooling.template.md` and fill in real run and capture paths.

If `<repo-root>/docs/ui/visual-invariants.md` is absent, copy `<repo-root>/docs/ui/visual-invariants.template.md` and define provisional role-level geometry, typography, icon-label composition, text fit, copy, and responsive-collapse rules.

If `<repo-root>/docs/ui/render-matrix.md` is absent, copy `<repo-root>/docs/ui/render-matrix.template.md` and record actual probe and vertical-slice rendering conditions. Keep rows `unverified` when tooling is unavailable.

## 8. Representative vertical slice

Use `assets/vertical-slice.template.md`.

Select one flow that includes as many of these as possible:

- the recurring core task
- real interaction
- normal, loading, empty, partial, error/recovery, and success states
- primary input and viewport
- the hardest density or spatial constraint
- a moment that clearly demonstrates the selected design signature

Do not spread shallow work across the entire app. Complete this one flow deeply.

## 9. Implement

- Reuse technical infrastructure, data contracts, routing, and domain state where appropriate.
- In reset mode, rebuild unapproved visual structure in a new screen tree or isolated path.
- Use realistic content and stress cases.
- Start with domain-semantic components.
- Reimplement selected principles cleanly instead of copying probe code into production.
- Do not mix rules from rejected directions.

## 10. Validate and audit

Apply `<repo-root>/.agents/references/ui/visual-validation.md`.

Validate:

- completion of the core task
- agreement between Foundation and actual structure
- key states and recovery
- primary input and viewports
- real-content stress cases
- perceptual comfort and cross-screen consistency
- narrative restraint and the explanation-deletion test
- regression into generic AI patterns
- technical checks and actual rendering

When possible, ask `ui_auditor` for a read-only review and compare its findings with actual evidence. Perform at least one structural revision pass.

Even after strong validation, keep the Foundation `provisional`. Only explicit user or team approval can promote it to `approved`.

## 11. Precedent and approval boundary

Use `assets/precedents.template.md`, `assets/state-matrix.template.md`, and `assets/decision-log.template.md` according to the selected documentation level.

- `standard` and `extended`: record validated reusable aspects in `<repo-root>/docs/ui/precedents.md` as `provisional` candidates.
- `lite`: record reusable aspects in `foundation.md` or `vertical-slice.md`; create `precedents.md` when a second screen actually needs reuse.

Register only specific aspects and states of the representative screen, not blanket approval of the entire screen.

This skill never promotes a Foundation or precedent to `approved` through its own validation. When the user requests approval registration, apply `$ui-critic` in `approval-review` mode and update the Foundation, visual invariants, render matrix, related precedent, and decision log as one change set.

Update `<repo-root>/docs/plans/current.md` only with durable changes such as the selected direction, vertical slice, and next validation checkpoint.

Final report:

1. change mode and documentation level
2. existing-UI authority classification
3. structural differences among the three directions and probes
4. selection rationale and accepted risks
5. files created or changed
6. actual technical, rendered, input, state, perceptual, and copy validation
7. unverified items
8. states of the Foundation, visual invariants, render matrix, and precedents
