# AGENTS.md

<!--
Codex combines instructions from the project root down to the current working directory. Instructions in the nearest directory are applied last and take precedence.
Put personal overrides in AGENTS.override.md; this repository ignores that file.
Keep detailed procedures in .agents/skills/ and .agents/references/, and keep this file below 32 KiB.
Only the content between MANAGED markers may be changed automatically by project-bootstrap and sync-agents-md.
-->

## Repository root and paths

- Determine the repository root first. Use `git rev-parse --show-toplevel` when possible.
- If no Git root is available, use the nearest ancestor that contains this file together with `.agents/`, `.codex/`, and `START_HERE.md`.
- Every path in these instructions that begins with `.agents/`, `.codex/`, `docs/`, `START_HERE.md`, or `AGENTS.md` is relative to the **repository root**, not the current working directory.
- Do not reinterpret root documents under an arbitrary nested package simply because the current command runs there.

<!-- BEGIN MANAGED:PROJECT_PROFILE -->
## Project state

- **State**: `operational`
- **One-line description**: Evidence-grounded PoC comparing fixed hybrid-retrieval candidates with and without LLM engineering review.
- **Stack**: Python 3.13 and uv; FastAPI, Google ADK 2.x, Vertex AI embeddings/generation, and a Cloud Run-compatible container.
- **Entry point**: `ecr-poc` console script -> `src/ecr_poc/__init__.py:main`

State definitions:

- `empty`: no meaningful manifest, engine project, or entry point exists.
- `scaffolded`: stack files and an entry point exist, but the baseline run or command table is not sufficiently verified.
- `operational`: the command table below matches the repository and a minimum baseline workflow has been verified.
<!-- END MANAGED:PROJECT_PROFILE -->

<!-- BEGIN MANAGED:PROJECT_COMMANDS -->
## Commands

| Purpose | Command |
| --- | --- |
| Install | `uv sync` |
| Development server / run | `uv run ecr-poc serve --host 127.0.0.1 --port 8080` |
| Build | `uv build` |
| Test | `uv run pytest -q tests -p no:cacheprovider` |
| Single test | `uv run pytest -q tests/test_pipeline.py -p no:cacheprovider` |
| Lint / format | `uv run ruff check .` / `uv run ruff format .` |
| Type check | `uv run mypy src` |
| UI preview | `uv run ecr-poc serve --host 127.0.0.1 --port 8080` then open `http://127.0.0.1:8080` |
| UI automation | Codex in-app Browser workflow recorded in `docs/ui/tooling.md` |
| Screenshot / capture | Browser full-page capture to `docs/ui/evidence/` |
<!-- END MANAGED:PROJECT_COMMANDS -->

`project-bootstrap` updates both managed blocks directly while completing the initial scaffold. After the stack or commands change, `$sync-agents-md` resynchronizes only those blocks. Do not guess commands that are not supported by repository evidence.

## Work-routing priority

When one request matches multiple skills, use the first matching rule below. A lower-priority stage never runs ahead of a higher-priority prerequisite.

1. **Project state is `empty`, and the user requests a new product, app, game, or tool**
   - Apply `$project-bootstrap` first and exclusively.
   - Do not begin production implementation with `$ui-project-start` or `$ui-screen-build` until scaffolding reaches `operational`.
2. **Project state is `scaffolded`**
   - Complete the active bootstrap, or run `$sync-agents-md` when the user explicitly requests synchronization.
   - Do not jump to broad UI implementation before confirming the baseline run path.
3. **Project is `operational`, the request introduces major new UI, and no active Foundation exists**
   - Apply `$ui-project-start`.
4. **An active Foundation exists and the request adds a screen, flow, menu, HUD, or structural UI change**
   - Apply `$ui-screen-build`.
5. **The request is a focused UI defect such as focus, clipping, contrast, wrapping, or state presentation**
   - Apply `$ui-screen-build` in `repair` mode, whether or not a Foundation exists.
6. **The request reviews, audits, or evaluates implementation for approval**
   - Apply `$ui-critic`. Its default mode is review-only.
7. **The user signals that the session is ending, pausing, or will continue later**
   - Apply `$handoff`.

When a skill requires the next stage, **do not assume another implicit invocation will happen automatically**. If the follow-up procedure is part of the current request, the parent workflow reads the required skill file directly and continues in the same task. Stop only when the user explicitly asks to stop at a particular stage.

## Session start

1. Read `START_HERE.md`.
2. Read the versioned `docs/plans/current.md`.
3. If `docs/notes/handoff.local.md` exists, read it as additional local state.
4. Check tracked and untracked Git state and actual manifests to verify the managed project state.
5. Route the current request according to the priority above.
6. For substantial work, update `docs/plans/current.md` and, when useful, a detailed plan under `docs/plans/`.
7. For UI work, inspect `docs/ui/foundation.md`, `docs/ui/visual-invariants.md`, `docs/ui/render-matrix.md`, `docs/ui/precedents.md`, relevant screen contracts, and UI tooling.

Do not infer current repository state from conversation memory alone.

## Durable state management

- `docs/plans/current.md` is the versioned source of truth for the active milestone, scope, blockers, and validation state.
- Do not edit it merely to record that a session ended.
- Update it when any of these change materially:
  - milestone or active scope
  - completed major result
  - blocker or external decision needed
  - validation state
  - next checkpoint
- Keep personal scratch notes and local interruption details only in `docs/notes/handoff.local.md`.
- If the two documents disagree, verify the actual repository and validation evidence, correct durable state first, then refresh the local handoff.

## Working principles

- Before claiming completion, actually run the applicable build, tests, or execution path.
- Do not describe type-check or compilation success as user-flow or rendering success.
- Clearly distinguish success, failure, and unverified work.
- Fix the root cause within the requested scope. Do not silently fix adjacent issues; record them as separate findings.
- Follow existing naming, domain models, error handling, and test style.
- Resolve reversible details from repository evidence and record the decision. Ask only about uncertainty with meaningful product, data-loss, or security impact.
- Do not ask for information the user has already provided.
- Prefer approved utilities and semantic components over introducing new patterns.
- Do not print, document, or commit secrets or personal data.

## Dependency, network, and change approval

The following are within scope without another confirmation:

- default dependencies and lockfiles created by an official scaffolder the user explicitly requested
- lockfile synchronization caused by an already approved dependency change
- code and migration-file creation for a schema change the user explicitly requested

Confirm before:

- adding a new production dependency or major upgrade after official scaffolding
- executing an actual database migration, deleting data, or applying an irreversible schema change
- deploying, publishing, or writing to an external service
- `git push`, force-push, branch or tag deletion, or history rewrite
- creating an unrequested commit
- deleting many files or restructuring outside the requested scope
- changing configuration in a way that broadens a security boundary

Outbound network access for project commands is blocked by default. Use the approval flow when installation or external documentation access is necessary, and do not bypass security controls.

## Git baseline

- Recommend a baseline commit after initial scaffolding and baseline validation.
- If the user has not requested or preapproved a commit, report the recommendation without stopping to ask.
- Do not commit automatically.
- Without a baseline commit, inspect untracked files explicitly during Handoff and review; do not interpret “no diff” as “no changes.”
- Write commit messages as one concise line describing what changed and why.

## UI authority

UI does not become design precedent merely because it exists in the repository.

Authority order:

1. the user's latest explicit requirement
2. `docs/ui/foundation.md` when its state is `approved`
3. the active `docs/ui/foundation.md` when its state is `provisional`
4. the latest applicable decision in `docs/ui/decision-log.md`
5. active role, text, and alignment rules in `docs/ui/visual-invariants.md`
6. the explicit scope marked `approved`, or `provisional` for the current work, in `docs/ui/precedents.md`
7. relevant `docs/ui/screens/*.md` screen contracts
8. existing implementation only where it agrees with the documents above

Classify existing UI as:

- `approved`: may serve as precedent within an explicit scope
- `functional-only`: preserve data, behavior, and routing, but not visual authority
- `experimental`: candidate awaiting validation
- `deprecated`: do not reuse

### UI states

Use only these four states:

- `draft`: a candidate, not an implementation baseline
- `provisional`: selected, implemented, or validated, but not explicitly approved by the user or team
- `approved`: explicitly approved by the user or team
- `superseded`: replaced by a newer standard

Record `validated` as evidence, not as a governance state. Never promote AI-validated UI to `approved` automatically.

### Atomic UI approval

When approving a Foundation or precedent, update all of the following as one change unit:

1. the exact target and scope approved by the user
2. status and version in the Foundation or screen contract
3. approval rationale and date in `decision-log.md`
4. precise reusable aspects and non-use boundaries in `precedents.md`
5. relevant role rules and exceptions in `visual-invariants.md`
6. actual viewport, content, state, input, font, and copy rows in `render-matrix.md`
7. links to the related review, commit, and validation conditions

Do not leave a mixed state in which only some files were updated. If every item cannot be aligned, keep the prior state and report a blocker.

### UI implementation principles

- Classify a screen by the user's primary action, not only by game/non-game or industry.
- Game/non-game is a contextual constraint, not a fixed visual style.
- Review real content, long strings, empty data, maximum item counts, and key states before committing to layout.
- Record height, padding, typography, icon-label gap, state treatment, and wrapping policy for repeated semantic roles in `docs/ui/visual-invariants.md`.
- Operational UI leads with objects, state, and actions. Do not add **explanatory UI** prose that merely repeats visible controls or narrates page structure.
- Persistent text must serve identification, state, a non-obvious constraint, consequence, risk, error, recovery, or decision rationale.
- Do not leave first-use guidance permanently visible in recurring workflows; make it contextual, dismissible, and progressive.
- Do not extract a generic `Card`, `Panel`, `Section`, `Tile`, or `Box` from one use case.
- Create shared abstractions only after at least two approved cases share meaning, behavior, state, and appearance.
- On narrow screens, define an information and action collapse ladder instead of mechanically stacking desktop regions or allowing accidental two-line controls.
- Actually verify every input method the project supports: keyboard, touch, mouse, or gamepad.
- Record build success, screenshot review, interaction validation, perceptual comfort, and narrative restraint as separate evidence.

## Validation

Use the strongest evidence appropriate to the change:

- code: tests, type check, lint, build
- web UI: actual browser, supported viewports, keyboard and touch flows, screenshots
- game UI: actual engine or test scene, gamepad focus, normal, critical, and notification states
- data flow: normal, empty, partial, error, and recovery

For projects with UI, record actual preview, testing, capture, viewport, and input paths in `docs/ui/tooling.md`. For major UI, use `docs/ui/render-matrix.md` to record production font, content length, state, input, cross-screen comparison, and the explanation-deletion test.

If only code and tokens were inspected and no rendered UI was reviewed, report perceptual comfort and narrative restraint as `unverified`.

## Do not touch

- Do not read or print `.env`, `.env.*`, `secrets/`, certificate, or key files.
- Do not place API keys, tokens, or passwords in code, documentation, or commit messages.
- Do not edit generated directories such as `node_modules/`, `target/`, `dist/`, or `.venv/` directly.
- Do not automatically bypass Defender, SmartScreen, execution policy, or organizational security policy.

## Session handoff

- At session start, read `docs/plans/current.md` and, when present, `docs/notes/handoff.local.md`.
- Apply `$handoff` when the user says they are done for now, will continue later, or wants to pause.
- Build the handoff from actual Git state, untracked files, executed commands, and UI-document status.
- Also update `docs/plans/current.md` when a milestone, blocker, or validation state changed materially.
- Do not commit the local handoff file.

## Key paths

| Path | Purpose |
| --- | --- |
| `START_HERE.md` | initial workflow and routing |
| `.agents/skills/` | repeatable workflows |
| `.agents/references/project/` | shared bootstrap, detection, path, and managed-block rules |
| `.agents/references/ui/` | shared UI knowledge |
| `.codex/config.toml` | project-scoped Codex settings |
| `.codex/agents/` | read-oriented UI subagents |
| `docs/plans/current.md` | versioned current project state |
| `docs/plans/` | detailed work plans |
| `docs/decisions/` | non-UI technical decisions |
| `docs/ui/` | UI Foundation, directions, contracts, reviews, and evidence |
| `docs/ui/tooling.md` | real UI preview, automation, capture, and input-validation paths |
| `docs/ui/visual-invariants.md` | role-level geometry, typography, icon, text, and copy invariants |
| `docs/ui/render-matrix.md` | rendered, cross-screen, copy-necessity, and transition-stability evidence |
| `docs/notes/handoff.local.md` | local session handoff |
