# Managed AGENTS Blocks

`project-bootstrap` and `sync-agents-md` do not rewrite all of `AGENTS.md`. They may edit only the content between these two marker pairs:

```text
<!-- BEGIN MANAGED:PROJECT_PROFILE -->
...
<!-- END MANAGED:PROJECT_PROFILE -->

<!-- BEGIN MANAGED:PROJECT_COMMANDS -->
...
<!-- END MANAGED:PROJECT_COMMANDS -->
```

## Required invariants

- Each BEGIN and END marker must occur exactly once.
- Every BEGIN marker must appear before its matching END marker.
- The two managed blocks must not overlap.
- Do not change the marker lines themselves.
- Do not automatically change a single character outside the managed blocks.
- If a marker is missing or duplicated, stop and report a blocker instead of attempting repair by inference.

## Atomic write

1. Read the original `AGENTS.md` and record its hash.
2. Build both replacement blocks in memory.
3. Validate the markers and the expected edit range.
4. Write a temporary file in the same directory.
5. Read the temporary file back and validate marker structure, Markdown structure, and size limits.
6. Compare the original hash again to ensure the file did not change concurrently.
7. Replace the original in one operation.
8. Confirm that the resulting diff is limited to the two managed blocks.

If any step fails, preserve the original file.

## Profile block contract

The profile block must include:

- state: `empty | scaffolded | operational`
- one-line description
- stack
- entry point

## Commands block contract

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

If no evidence supports a command, write `none` or `unknown — <reason>`. Do not invent commands.
