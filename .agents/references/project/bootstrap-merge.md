# Non-Empty Root Bootstrap Merge

This template already contains control files, so the project root is not empty at the filesystem level. If an official scaffolder requires an empty directory, do not run it in the root with `--force`.

## Staging location

- Generate the scaffold in `<repo-root>/.bootstrap-work/<run-id>/scaffold/`.
- Use a timestamp or another collision-free short identifier for `<run-id>`.
- Keep the staging directory in `.gitignore`.
- If an earlier staging directory exists, investigate why before creating a new run. Do not reuse it automatically.

## Protected paths

The scaffolder must not automatically overwrite or delete:

- `AGENTS.md`
- `START_HERE.md`
- `.agents/`
- `.codex/`
- `docs/`
- `.gitattributes`
- `.git/`
- template, security, and local-state rules already present in `.gitignore`

## Procedure

1. Record Git status plus the file list and hashes of protected paths.
2. Generate the official scaffold in staging.
3. In staging, run any available install/restore and baseline build/check commands.
4. Exclude a staging `.git/` directory from the merge.
5. Compare relative paths in the root and staging and create a merge inventory.
6. Classify every item as `copy`, `merge`, `preserve`, `conflict`, or `generated-ignore`.
7. Resolve each `conflict` as a small, explicit decision after comparing meaning. Never perform an ambiguous overwrite.
8. Copy new files and non-conflicting directories into the root. Do not use delete synchronization or forced overwrite.
9. Merge scaffolder ignore entries, without duplicates, into the `BEGIN/END MANAGED:SCAFFOLD_IGNORE` block in `.gitignore`.
10. From the root, rerun install/restore, build/check, tests, and the basic run path.
11. Recheck protected-path hashes and the diff. Treat any change outside an allowed managed block as a failure.
12. Remove staging only after root validation passes.

## Common collisions

| Path | Default action |
| --- | --- |
| `README.md` | Copy if the root has none. Otherwise compare content and consolidate into one user-facing README. |
| `.gitignore` | Never overwrite directly. Merge entries into the managed ignore block. |
| `.gitattributes` | Preserve the template file. Merge only scaffold rules that remain necessary after semantic comparison. |
| formatter/linter config | Copy if no root file exists. Otherwise check tool and version conflicts first. |
| package manifest | Copy only when the root has no actual manifest. If one already exists, reassess whether the project is truly in bootstrap state. |
| source directories | Copy new paths. For matching relative paths, resolve conflicts file by file. |
| `.git/` | Never merge. |

## Failure handling

- If staging validation fails, do not merge anything into the root.
- If the merge fails partway through, preserve staging and the merge inventory and report every partially applied file.
- If root revalidation fails, do not remove staging. Do not automatically retry while template control files are in an uncertain state.
- Before success, do not bulk-delete `.bootstrap-work/` with `git clean` or a similar command.
