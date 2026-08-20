---
name: handoff
description: Use when the user is ending or pausing work and intends to continue in another session. Refresh the local handoff and, when the milestone, blocker, or validation state changed materially, synchronize the versioned docs/plans/current.md. Do not use for routine progress summaries, automatic commits, pushes, or product-code changes.
---

# Handoff

All `.agents/`, `.codex/`, and `docs/` paths are relative to `<repo-root>/`. Apply `<repo-root>/.agents/references/project/repository-paths.md` first.

Write a current-state snapshot so the next session can continue without conversation memory by comparing `<repo-root>/docs/notes/handoff.local.md` with the repository. Replace the file; do not append a running journal.

## 1. Gather actual state

Do not rely only on a conversational summary.

Check when available:

- `git status --short`
- `git diff --stat`
- `git diff`
- `git diff --cached`
- `git ls-files --others --exclude-standard`
- `git log --oneline -5`
- current branch and HEAD
- commands actually run in this session and their results
- failed, interrupted, and unexecuted checks

If there is no first commit or most files are untracked, `git diff` may not reveal their content. Read and summarize important untracked files directly and record `baseline commit: absent`.

## 2. Plans and durable state

Review:

- objective, active scope, validation, blockers, and next checkpoint in `<repo-root>/docs/plans/current.md`
- active plans under `<repo-root>/docs/plans/`
- related decisions under `<repo-root>/docs/decisions/`
- for UI work: `<repo-root>/docs/ui/foundation.md`, the decision log, screen contracts, reviews, and tooling
- current Foundation state: draft / provisional / approved / superseded
- exact scope of approved precedents and any new provisional patterns

Do not hide a conflict between documentation and actual code.

## 3. Format

Use `assets/handoff.template.md` and record:

```markdown
# Handoff

**Updated**: YYYY-MM-DD HH:mm <timezone>  
**Branch / HEAD**:  
**Baseline commit**: present / absent / unknown  
**Working tree**: clean / modified / untracked-heavy

## Objective

## Changes

- `path` — what changed and why

## Verified

Only checks actually run, including command, environment, and result.

## Failed

Actual failed commands or reproduced failures.

## Unverified

Changed or assumed but not checked.

## UI state

- Foundation status/version:
- Selected direction:
- Screen contracts:
- Provisional patterns:
- Explicitly approved precedent scope:
- Verified viewports/inputs/states:
- Unverified UI conditions:

Remove this section when no UI work is involved.

## Next steps

- [ ] First concrete action
- [ ] ...

## Blockers / decisions needed

## Traps

Only details likely to waste the next session's time.
```

## 4. Versioned current state

`<repo-root>/docs/plans/current.md` is durable state shared by the team and other environments. Update it with the handoff only if one of these actually changed:

- milestone or active scope
- completed major checkpoint
- blocker or external decision
- build, test, or UI validation state
- next checkpoint

Do not edit it solely to record session-end time. Keep personal interruption details and temporary notes in the local handoff only. Do not commit automatically.

## 5. Principles

- Do not mix verified, failed, and unverified work.
- Use exact paths and commands.
- Replace vague “finish up” language with an executable next action.
- Keep committed history brief; describe the working tree and untracked state precisely.
- Do not carry secrets, `.env` values, tokens, or personal data into the handoff.
- Do not commit, stash, reset, checkout, clean, or push automatically.
- Remember that updating the handoff file itself may appear in `git status`.

## 6. Completion report

Report:

- local handoff path
- whether durable current status was updated
- counts of verified, failed, and unverified items
- first next action
- whether a baseline commit exists
- UI Foundation status, when applicable
