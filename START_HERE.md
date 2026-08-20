# Start Here

When a person or AI opens this project for the first time, follow the actual files in the repository root in this order.

## 1. Root and durable state

1. Read `.agents/references/project/repository-paths.md` and the routing priority in `AGENTS.md`.
2. Read the versioned `docs/plans/current.md`.
3. If this local directory has a previous session, also read `docs/notes/handoff.local.md`.
4. Prefer actual manifests, entry points, Git state, and validation evidence over documentation that may be stale.

## 2. Determine the current state

### `empty`

- no application manifest or engine project file
- no runnable entry point
- only template control files exist

For a new product request, `$project-bootstrap` takes precedence over every UI skill. Even when the request includes UI, complete safe scaffolding and baseline validation first. Do not run `$sync-agents-md` first.

### `scaffolded`

- framework or engine files exist
- baseline execution or AGENTS managed-block synchronization is incomplete

If this is part of the same bootstrap task, continue `$project-bootstrap` to completion. For an existing scaffold imported from elsewhere, verify baseline evidence and then run `$sync-agents-md` explicitly.

### `operational`

- the managed blocks in `AGENTS.md` match the actual repository
- at least one applicable baseline run, build, or test path is verified

Proceed with normal feature work and UI routing.

## 3. Scaffolding a non-empty root that contains the template

Even if an official generator requires an empty directory, do not move aside or overwrite `AGENTS.md`, `.agents/`, `.codex/`, or `docs/`.

`$project-bootstrap` uses this contract:

```text
official scaffold in an isolated staging directory
→ validate the staging result
→ classify protected paths and collisions
→ copy and merge the required files
→ validate again from the actual root
→ remove staging only after success
```

Do not merge a nested `.git` created by the generator. Merge only the required `.gitignore` and `.gitattributes` entries while preserving existing security and local-state rules.

## 4. AGENTS synchronization

Initial bootstrap directly updates these managed blocks without relying on another skill invocation:

```text
BEGIN/END MANAGED:PROJECT_PROFILE
BEGIN/END MANAGED:PROJECT_COMMANDS
```

After commands or stack change later, run `$sync-agents-md` explicitly. Do not automatically rewrite project instructions outside the managed blocks.

## 5. UI routing

Apply the first matching rule for the current state:

- initial UI, a complete redesign, reset of an “AI-generated-looking” UI, or major new UI without a Foundation: `$ui-project-start`
- a new screen, menu, HUD, or flow under an active Foundation: `$ui-screen-build`
- a focused issue such as focus ring, clipping, icon-text misalignment, accidental two-line controls, or excessive explanatory copy: `$ui-screen-build` in `repair` mode
- independent UI review or approval-candidate evaluation: `$ui-critic`

`docs/ui/foundation.md` is not required for a focused repair. However, a new major flow must not invent a design system before a Foundation is established.

For human-centered visual quality, also read:

- `.agents/references/ui/perceptual-comfort.md`
- `.agents/references/ui/narrative-restraint.md`
- `docs/ui/visual-invariants.md`, when it exists
- `docs/ui/render-matrix.md`, when it exists

## 6. Baseline and continuation

After scaffolding and baseline command validation, recommend a baseline commit but never create it automatically.

At session start, compare durable state with the actual repository. At session end, `$handoff` records local interruption details and updates durable project state only when a milestone, blocker, validation result, or next checkpoint changed materially.
