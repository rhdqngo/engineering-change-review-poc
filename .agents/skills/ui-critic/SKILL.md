---
name: ui-critic
description: Use for an independent review of implemented screens, flows, HUDs, and menus against the UI Foundation, screen contracts, code, and rendered evidence. Trigger for requests such as “review the UI,” “does this feel comfortable to a person,” “is it consistent across screens,” “does it have explanatory AI-style UI,” or “check states, responsive behavior, and input.” Default to review-only. Do not use to establish a new UI direction or implement ordinary features.
---

# UI Critic

All `.agents/`, `.codex/`, and `docs/` paths are relative to `<repo-root>/`. Apply `<repo-root>/.agents/references/project/repository-paths.md` first.

Review against user tasks, the active Foundation, state/input/responsive contracts, and actual evidence—not taste. Do not modify product code by default.

## 1. Mode

- `review-only`: default; analyze and write a report only
- `review-and-fix`: fix only the scope explicitly requested in the same user request, then revalidate
- `approval-review`: determine whether a Foundation or precedent is eligible for approval

A request that only says “review it” means review-only.

## 2. Scope and sources of truth

Read the actual files:

- `<repo-root>/AGENTS.md`
- `<repo-root>/docs/ui/foundation.md`
- `<repo-root>/docs/ui/decision-log.md`, when present
- `<repo-root>/docs/ui/precedents.md`, when present
- relevant `<repo-root>/docs/ui/screens/*.md`
- `<repo-root>/docs/ui/tooling.md`, when present
- `<repo-root>/docs/ui/visual-invariants.md`, when present
- `<repo-root>/docs/ui/render-matrix.md`, when present
- implementation code, tests, diffs, and real data states

Without a Foundation, do not make a project-level design-conformance or approval judgment. You may still review focused quality issues, but state `foundation missing` explicitly.

Apply `<repo-root>/.agents/references/ui/governance-status.md`. Strong validation does not promote an artifact to `approved` automatically.

## 3. Inspect actual state

- `git status --short --untracked-files=all`
- relevant diffs and code paths
- implemented loading, empty, partial, error, success, disabled, locked, permission, and offline states
- supported viewports and input methods
- existing tests and run commands

A condition described only in documentation is not verified until it appears in code and rendered behavior.

## 4. Review rendering

Use `<repo-root>/.agents/references/ui/visual-validation.md` and `<repo-root>/docs/ui/tooling.md`.

When possible, inspect the actual browser, device, engine, automated UI test, or Storybook environment.

At minimum, inspect applicable conditions:

- normal state
- loading, empty, error/recovery, and completion
- key narrow and wide viewports
- primary input method
- long content, localization, production/fallback fonts, many items, missing images, and large values
- accidental wrapping, baselines, icon-label composition, and layout shift
- all persistent copy and explanatory regions
- another screen or precedent using the same semantic role
- for games: normal, critical, notification-overload, and menu-focus conditions

A static screenshot alone cannot pass focus, gamepad, error recovery, animation, or real-time response.

## 5. Independent audit

When possible, ask the read-only `ui_auditor` agent to check:

- disagreement between the Foundation and actual screen
- information architecture that obscures the core task
- regression into generic AI defaults or explanatory UI
- perceptual instability, cross-screen inconsistency, and accidental two-line controls
- unnecessary subtitles, helper paragraphs, and feature-description cards
- missing state, input, or responsive behavior
- patterns that would be dangerous to spread as precedent

Check `git status` before and after the agent runs. The main agent must compare its output with code, documents, and rendered evidence.

## 6. Review gates

Apply `references/review-rubric.md` and these shared references:

- `<repo-root>/.agents/references/ui/pattern-justification.md`
- `<repo-root>/.agents/references/ui/state-model.md`
- `<repo-root>/.agents/references/ui/responsive-input.md`
- `<repo-root>/.agents/references/ui/perceptual-comfort.md`
- `<repo-root>/.agents/references/ui/narrative-restraint.md`
- for games, `<repo-root>/.agents/references/ui/game-context.md`; otherwise `<repo-root>/.agents/references/ui/non-game-context.md`

Rate every gate as `pass`, `fail`, `unverified`, or `not-applicable`:

1. task fit
2. Foundation conformance
3. information architecture and hierarchy
4. state and error recovery
5. input and responsive adaptation
6. accessibility and clarity
7. implementation, token, and semantic consistency
8. perceptual comfort and cross-screen consistency
9. narrative restraint and copy necessity
10. regression into unjustified AI defaults
11. completeness of validation evidence

Every `not-applicable` result requires a reason.

## 7. Findings

Write findings in severity order:

- `blocker`: core task impossible, destructive failure, inaccessible path, or fundamental direction violation
- `major`: repeated failure in a primary flow, state, or input, or a bad pattern likely to spread as precedent
- `minor`: limited clarity, consistency, or finish issue
- `note`: optional improvement or tracking item

Every finding includes:

- observed problem
- location and reproduction condition
- user and product impact
- applicable rule
- code, document, rendering, or test evidence
- smallest corrective direction
- revalidation method

“Make it prettier,” “it looks AI-generated,” or “the spacing feels wrong” is not enough. Describe a reproducible issue such as repeated alignment drift, wrapping, visual weight, layout shift, or an unjustified copy role.

## 8. Fix mode

Even in review-and-fix, draft the report first and fix blocker and major findings in the smallest scope.

- Do not silently change the selected UI direction.
- If the Foundation is the root cause, classify it as a decision problem rather than bypassing it in code.
- Rerun relevant technical, rendered, state, and input validation after fixes.
- Keep unfixed findings and unverified items in the report.

## 9. Approval review

Only `approval-review` evaluates approval eligibility.

All of the following are required:

- every applicable must-pass gate passes
- no blocker or major finding
- actual rendering and key state, viewport, input, and font validation
- perceptual comfort, cross-screen consistency, and narrative restraint pass
- visual invariants and render matrix are linked
- approved scope and explicit non-use conditions are documented
- the user or team explicitly requests approval

Passing review is not automatic approval. Only when the same request includes registration of approval, use the approval transaction in `<repo-root>/.agents/references/ui/governance-status.md` to update the Foundation, visual invariants, render matrix, decision log, precedents, and review link as one change set. If only part can be updated, do not change approval state.

## 10. Report

Use `assets/ui-review.template.md` to create `<repo-root>/docs/ui/reviews/YYYY-MM-DD-<scope>.md`.

Verdict:

- `pass`
- `pass with minor findings`
- `fail`
- `unverified`

The final user report includes scope, verdict, blocker/major findings, actual validation conditions, unverified items, report path, and whether fixes or approval changes were performed.
