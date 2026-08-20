# Bootstrap Safety

This document covers security and partial-failure principles. For the concrete merge procedure, use `.agents/references/project/bootstrap-merge.md` relative to the repository root.

## Protected control plane

Never overwrite automatically:

- content outside managed blocks in `AGENTS.md`
- `.agents/`
- `.codex/`
- `START_HERE.md`
- `docs/`
- `.gitattributes`
- `.git/`
- content outside the managed scaffold block in `.gitignore`

## Network and execution

- Do not weaken project configuration merely to bypass blocked network access.
- Do not use remote execution such as `curl | sh` or `irm | iex`.
- Do not request administrator privileges, Defender exclusions, or execution-policy bypasses.
- Use official package managers and generators and record every command.

## Partial failure

1. Identify whether failure occurred during staging creation, staging validation, merge, or root validation.
2. Do not repeat the same command without diagnosing the cause.
3. Do not delete existing template or user files.
4. Preserve staging and the merge inventory until success.
5. Clean up only when the staging directory created by this run can be identified safely.
6. If the root was partially modified, list every changed file and do not pretend an automatic rollback occurred.

## Git

- Do not reinitialize an existing `.git` directory.
- Do not copy staging `.git` into the root.
- Do not commit, stash, reset, checkout, clean, or push automatically.
- If no baseline commit exists, inspect untracked files as well as diffs.
