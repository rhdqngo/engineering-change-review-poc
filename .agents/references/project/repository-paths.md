# Repository Path Resolution

Project skills resolve files from the repository root, regardless of the current working directory.

## Root discovery

1. Use `git rev-parse --show-toplevel` when available.
2. If there is no Git root, use the nearest ancestor that contains `AGENTS.md`, `.agents/`, `.codex/`, and `START_HERE.md` together.
3. If more than one candidate exists, use the nearest candidate that contains the current working directory.
4. If the root cannot be determined confidently, report a blocker before modifying files.

## Path notation

All of these instruction paths are relative to `<repo-root>/`:

- `.agents/...`
- `.codex/...`
- `docs/...`
- `AGENTS.md`
- `START_HERE.md`

A skill's own `references/` and `assets/` paths are relative to that skill directory.

## Safety

- Do not create duplicate root documents merely because the command was run from a nested package.
- If a monorepo package needs package-specific instructions, place a separate `AGENTS.md` in that package; do not duplicate the root managed blocks.
- Create temporary files and probes only in their designated directories.
