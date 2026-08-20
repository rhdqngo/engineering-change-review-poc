---
name: project-bootstrap
description: Use first when the user asks to create a new app, web product, game, or tool in an empty repository that has no manifest or runnable entry point, including a workspace that contains only template control files. Generate and validate the official scaffold in isolation, merge it safely into the non-empty root, synchronize managed AGENTS blocks and durable state, and continue any initial UI workflow included in the request. Do not use for feature work in a repository that already contains real application code.
---

# Project Bootstrap

Turn an empty workspace into a runnable `operational` project. Do not stop after filling template documents or wait for another skill to be invoked implicitly.

## Paths and priority

Apply `<repo-root>/.agents/references/project/repository-paths.md` first.

When the project is `empty` and the user requests a new product, this skill takes precedence over UI skills. Do not begin production UI implementation before scaffolding and minimum execution validation are complete.

## Completion conditions

- select a stack appropriate to the request and platform
- generate an official or project-standard scaffold in staging
- validate the staging scaffold itself
- preserve protected paths while merging into the root
- revalidate install, build, tests, and the baseline run path from the root
- synchronize both `AGENTS.md` managed blocks directly within this workflow
- update `docs/plans/current.md` to the real milestone and validation state
- if UI is part of the original request, continue the required UI workflow after the project becomes operational
- report success, failure, unverified items, and whether staging was removed

## 1. Confirm state

Read `<repo-root>/AGENTS.md`, `<repo-root>/START_HERE.md`, `<repo-root>/docs/plans/current.md`, actual manifests, entry points, and Git state.

Proceed with bootstrap when:

- no product code or runnable entry point exists
- no language, framework, or engine manifest exists
- only template control files exist
- the user explicitly asks to discard an existing scaffold and create a new official one

Stop and route correctly when:

- a real application entry point already exists
- the request is feature work that must preserve existing code
- the user asks only for one screen or API
- the project is `scaffolded` or `operational` and only the command table is stale: use explicit `$sync-agents-md`

If code exists while documentation still says `empty`, never overwrite the code based on documentation alone.

## 2. Product goal and platform

Extract from the user request:

- one-line product description
- primary user and core task
- target platform
- whether UI is needed and which input methods apply
- local, server, multiplayer, or offline requirements
- any specified language, framework, or game engine
- deployment target and important constraints

When useful, create `<repo-root>/docs/project-brief.md` from `assets/project-brief.template.md`. Do not ask again for clear information.

Clarify only uncertainty that fundamentally changes the architecture, such as platform, data boundary, competitive multiplayer, payment, medical, or financial requirements. For low-risk details, choose official defaults and record assumptions.

## 3. Select the stack

Read:

- `references/stack-selection.md`
- `references/platform-detection.md`
- `<repo-root>/.agents/references/project/project-detection.md`

Priority:

1. stack explicitly requested by the user
2. clear platform constraints in the repository or request
3. an official, maintainable default appropriate to the target platform and core task
4. testability, accessibility, deployment path, and team fit before implementation convenience

Check current versions and CLI options in official documentation. Do not pin versions or flags from memory.

## 4. Plan staging

Read:

- `references/bootstrap-safety.md`
- `<repo-root>/.agents/references/project/bootstrap-merge.md`
- `assets/merge-inventory.template.md`

Treat a root that is non-empty only because of template control files as normal.

1. Create a fresh `<repo-root>/.bootstrap-work/<run-id>/scaffold/`.
2. Record protected paths, their hashes, and Git state.
3. Run the official scaffolder only in staging.
4. Do not move files into the root before staging validation.
5. Build a merge inventory comparing staging and root.
6. Distinguish `copy`, `merge`, `preserve`, `conflict`, and `generated-ignore`.
7. Do not begin the merge while unresolved conflicts remain.

Do not use `--force`, delete synchronization, or bulk overwrite in the root.

## 5. Scaffold and validate staging

- Use the official generator or platform-standard tool.
- Prefer a one-shot invocation over a discouraged global installation.
- Do not request administrator privileges.
- Do not pipe remote scripts directly into a shell.
- Record the selected command, version evidence, and generation scope.
- If network access is denied, do not weaken configuration to bypass it; report the blocking point.

In staging, validate when applicable:

- manifest and lockfile consistency
- install or restore
- build, check, or static analysis
- scaffold tests
- baseline run or engine-open path

If staging is broken, do not merge it into the root.

## 6. Merge into the root

Follow the procedure in `<repo-root>/.agents/references/project/bootstrap-merge.md` exactly.

In particular:

- never automatically overwrite `<repo-root>/AGENTS.md`, `.agents/`, `.codex/`, `START_HERE.md`, `docs/`, `.gitattributes`, or `.git/`
- merge only unique scaffolder ignore entries into the `MANAGED:SCAFFOLD_IGNORE` block instead of replacing `.gitignore`
- never merge a nested scaffolder `.git/`
- never overwrite an actual user file at the same relative path automatically
- after merging, check protected paths and all changes outside allowed managed blocks

On partial failure, preserve staging and the merge inventory so the next session can reproduce and continue safely.

## 7. Revalidate from the root

Run again from the root:

- install or restore
- build, check, type check, or static analysis
- tests, when present
- baseline run or engine project path
- for UI projects, the baseline rendered route or scene

A staging pass is not a root pass. Do not delete staging before root validation succeeds.

For a UI project, if `<repo-root>/docs/ui/tooling.md` does not exist, copy `<repo-root>/docs/ui/tooling.template.md` and record preview, automation, capture, viewport, and input paths. If no tool exists, record `unverified` and the reason.

## 8. Synchronize AGENTS managed blocks directly

Do not wait for a separate implicit `$sync-agents-md` invocation.

Read:

- `<repo-root>/.agents/references/project/project-detection.md`
- `<repo-root>/.agents/references/project/managed-agents-blocks.md`

Using the actual scaffold and root validation result, atomically update:

- `MANAGED:PROJECT_PROFILE`
- `MANAGED:PROJECT_COMMANDS`

Do not edit project policy outside the managed blocks.

State decision:

- manifest and entry point exist, but the minimum run path is unverified: `scaffolded`
- commands match the repository and minimum baseline validation passes: `operational`

Remove `<fill in>` from managed blocks. For unsupported commands, write `none` or `unknown — <reason>` rather than inventing one.

## 9. Update durable state

Update `<repo-root>/docs/plans/current.md` to match reality.

At minimum include:

- objective and active scope
- bootstrap checkpoint
- build, run, and test validation
- blocker or external decision
- next checkpoint
- whether a UI Foundation is needed

Do not create an edit that changes only a timestamp.

## 10. Continue UI work in the original scope

If the original request includes initial UI or screen implementation and the project is now `operational`:

1. Read `<repo-root>/.agents/skills/ui-project-start/SKILL.md` directly.
2. Check that workflow's preconditions.
3. Continue the required initial UI procedure in the same task.

Do not assume a second implicit skill invocation will happen automatically.

If the user requested scaffold-only work, deferred UI, or the project remains `scaffolded`, do not create a UI direction. Record it as the next step.

## 11. Cleanup and report

Remove this run's staging directory only when root validation, managed-block synchronization, and durable-state update all succeed. If the run fails, preserve staging and report its path and reason.

You may recommend an initial baseline commit, but never create it automatically.

Final report:

1. selected stack and rationale
2. staging path and generation command
3. copy, merge, and conflict summary from the merge inventory
4. protected paths preserved
5. validations actually run from the root and their results
6. AGENTS managed-block changes
7. durable current-status changes
8. whether the downstream UI workflow ran
9. whether staging was removed or preserved
10. whether a baseline commit exists
