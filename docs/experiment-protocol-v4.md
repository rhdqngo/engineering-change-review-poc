# Verifiable Cloud Experiment Protocol v4

status: complete-and-published
experiment: `ecr-poc-preregistered-v4`
freeze tag: `ecr-poc-v4-freeze`
freeze commit: `7b76bfaa74d743d3200421d0dad681d740f1ca1c`
accepted run: `cloud-v4-20260820T050914Z-92f72d97`

## Why v4 exists

V3 is a complete immutable experiment that closed the loading-copy finding. Its independent UI audit then reproduced three major defects: an overlapping-request stale result, a two-line Reload control at 390 px, and keyboard focus loss after Reload. V4 changes only those UI behaviors plus version selection. Cases, NASA artifacts, Top-K, fusion, models, temperature, and all three v2 role prompt hashes remain unchanged.

## Freeze and execution order

1. Add latest-request-only cancellation/sequencing, one-line Reload geometry, and focus restoration with regression tests.
2. Validate v1 data plus v2/v3/v4 manifests, tests, lint, type check, build, script parsing, and local browser states.
3. Commit and push the complete implementation, then tag that exact commit `ecr-poc-v4-freeze` and push the tag.
4. Verify a clean worktree and `HEAD == origin/main == ecr-poc-v4-freeze`.
5. Upload `frozen/ecr-poc-v4`, build one immutable image, and assign it to both the private service and one-task Job.
6. Execute one sequential 18-case run with no retries; never publish automatically.
7. Publish only after terminal checkpoint, manifest/run/source/tag/execution/image, fixed arms/fingerprints, exact evidence/verifier, role errors, generation/SHA, and recomputed metrics all validate.
8. Repeat actual deployed desktop/narrow, rapid-toggle, keyboard-focus, provenance/API, rejected-evidence, IAM, access, and Logging audits.

V1/v2/v3 tags and objects remain unchanged. Accuracy is not an acceptance threshold, and a completed result is recorded exactly as observed.

## Completion record

Execution `ecr-poc-evaluate-sxjnm` completed 18/18 cases with zero role errors. `published/demo.json` identifies `ecr-poc-v4.json`, immutable generation `1787202918502625`, and SHA-256 `22b07011b48daec60422a91c69420cdf08a58a85e972f51291de7980d0ee3116`. Revision `ecr-poc-00007-xvc` and the Job use the same image digest `sha256:050ff3602378eb43e0fda6046bc35c788a5e891252c97589c346053d425f0a49`.

The accepted raw result, manifest, and report are `results/runs/vertex-adk-v4.json`, `results/runs/vertex-adk-v4.manifest.json`, and `docs/results/experiment-report-v4.md`. The freeze tag remains on the implementation commit and is not moved by the final evidence commit.
