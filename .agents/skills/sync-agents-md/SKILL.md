---
name: sync-agents-md
description: Use explicitly in a scaffolded or operational repository that has a real application manifest and entry point when the PROJECT_PROFILE and PROJECT_COMMANDS managed blocks in AGENTS.md need to match the current stack and install, run, build, test, and UI-validation commands. Do not use to create an empty workspace, modify product code, or rewrite all of AGENTS.md.
---

# Sync AGENTS.md

Inspect the actual repository and atomically synchronize only the two managed blocks. Preserve every other instruction written by the user or project.

## Paths and shared contracts

First read, relative to the repository root:

- `<repo-root>/.agents/references/project/repository-paths.md`
- `<repo-root>/.agents/references/project/project-detection.md`
- `<repo-root>/.agents/references/project/managed-agents-blocks.md`
- `<repo-root>/AGENTS.md`
- `<repo-root>/docs/plans/current.md`

Only this skill's own `references/` directory is relative to the skill directory.

## 1. Preconditions

Confirm:

- a real language, framework, or engine manifest exists
- a runnable entry point or official scaffold exists
- this is not an empty template state

If the project is `empty`, do not fill managed blocks with `none`; report that `$project-bootstrap` takes precedence.

## 2. Edit boundary

The only editable regions are between these exact marker pairs:

```markdown
<!-- BEGIN MANAGED:PROJECT_PROFILE -->
...
<!-- END MANAGED:PROJECT_PROFILE -->

<!-- BEGIN MANAGED:PROJECT_COMMANDS -->
...
<!-- END MANAGED:PROJECT_COMMANDS -->
```

Apply the invariants and atomic-write procedure in `managed-agents-blocks.md` exactly.

- Do not edit if any marker does not occur exactly once.
- Do not edit if blocks overlap or markers are out of order.
- Do not rewrite a legacy AGENTS file automatically when markers are absent. If each standard heading occurs exactly once and boundaries are unambiguous, propose marker introduction while preserving existing content, or migrate only within an explicit request.
- Do not intentionally change characters, order, or line endings outside the blocks.

## 3. Detect the repository

Using shared `project-detection.md`, determine from real evidence:

- stack and version range
- package, workspace, engine, and platform boundaries
- entry point
- package manager and wrappers
- install, run, build, test, single-test, lint/format, and type-check commands
- UI preview, automated UI validation, and capture paths

If lockfiles and manifests conflict, do not choose the newest file automatically. Check CI, repository documentation, and execution evidence.

## 4. Validate commands

### Commands that can usually be run directly

- read-only `help`, `version`, and `list` commands
- type checking, static analysis, and lint
- tests and single tests
- a short build or check when it is the repository standard and the environment is prepared

### Standard commands that may be recorded but must remain unverified

- install or restore
- long-running development server
- platform signing or deployment
- commands requiring a physical device or engine GUI
- commands requiring network access or secrets

Separate pass, failure, and unverified. Do not invent a missing command from convention.

## 5. Write the managed blocks

### PROJECT_PROFILE

- state: `scaffolded | operational`
- one-line description
- stack
- entry point
- fixed state-definition guidance

### PROJECT_COMMANDS

Keep these rows:

- install
- development server / run
- build
- test
- single test
- lint / format
- type check
- UI preview
- UI automation
- screenshot / capture

Rules:

- commands must be pasteable from the repository root
- scope multi-package commands as `(web)`, `(api)`, `(game)`, or similar
- provide a real file or filter example for a single test
- when evidence is missing, write `none` or `unknown — <reason>`
- leave no `<fill in>` placeholder

## 6. Determine state

- manifest and entry point exist, but the minimum run/build path is unverified: `scaffolded`
- command block matches the repository and minimum baseline validation passes: `operational`
- code exists, but standard commands are broken or required tools are unavailable: `scaffolded`

## 7. Apply atomically and verify

1. Record the hash of the original `AGENTS.md`.
2. Prepare both new blocks in memory.
3. Validate markers, file size, and expected diff range.
4. Write the entire result to a temporary file in the same directory.
5. Confirm the original did not change concurrently.
6. Apply the result with one replacement.
7. Confirm the resulting diff is limited to the two managed blocks.
8. Recheck for `<fill in>` and duplicated markers.

If any step fails, preserve the original.

If existing `<repo-root>/docs/ui/tooling.md` disagrees with discovered UI commands, do not silently update only AGENTS. Report the drift. Update tooling only when that work is within the request.

## 8. Durable state and report

If command synchronization materially changes the project state or a validation checkpoint, update only those facts in `<repo-root>/docs/plans/current.md`. Do not record a timestamp-only edit.

Final report:

1. detected stack and evidence files
2. package, engine, and platform boundaries
3. commands run and their pass/fail results
4. commands not run and why
5. atomic result of both managed-block edits
6. project-state decision
7. UI-tooling drift
8. whether durable current state was updated
