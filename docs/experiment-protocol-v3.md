# Verifiable Cloud Experiment Protocol v3

status: complete-and-published
experiment: `ecr-poc-preregistered-v3`
freeze tag: `ecr-poc-v3-freeze`
freeze commit: `3984e77961b6edeacb2286935f65c1dd13c80a3e`
accepted run: `cloud-v3-20260820T043842Z-6e260831`

## Why v3 exists

V2 is a complete, immutable experiment. Its final UI audit retained one minor finding: the cold-start Evidence desk said `Run a case…` although the read-only action is `Reload result`. V3 changes only that UI loading/error language and version-aware provenance plumbing. Cases, NASA artifacts, retrieval, generation settings, and role prompts remain unchanged.

## Freeze order

1. Validate the v1 data freeze plus v2 and v3 experiment manifests.
2. Pass tests, lint, type check, build, PowerShell parsing, and local loading-state browser review.
3. Commit and push the complete v3 implementation.
4. Tag that exact remote commit as `ecr-poc-v3-freeze` and push the tag.
5. Verify a clean worktree and `HEAD == origin/main == ecr-poc-v3-freeze`.
6. Only then upload `frozen/ecr-poc-v3`, deploy one image digest, and execute the billable 18-case Job.

The v2 tag and all v1/v2 objects remain unchanged.

## Execution and publication

- One Job task, parallelism 1, retries 0, timeout 30 minutes.
- Run IDs use `cloud-v3-<UTC timestamp>-<random suffix>`; failed runs are never reused or published.
- The Job uses GCS inputs only and records `ecr-poc-v3.json`, its hash, source commit, freeze tag, execution ID, image digest, model, prompt version/hashes, and ADK version.
- V3 keeps `ecr-poc-prompts-v2` because no role instruction changed.
- Each case writes a generation-guarded checkpoint. Final `evaluation.json` is immutable and must be sealed by the terminal checkpoint.
- Publication separately validates manifest/run/pointer identity, 18 cases, fixed arms and fingerprints, exact evidence, verifier cardinality, role errors, recomputed metrics, generation, and SHA-256.
- `published/demo.json` changes only after all checks pass; otherwise the accepted v2 pointer remains current.

Accuracy is not an acceptance threshold. Any complete, evidence-valid 18-case v3 result is published and reported as observed.

## Completion record

The protocol completed on 2026-08-20. Execution `ecr-poc-evaluate-fq5s4` produced 18/18 terminal cases with zero role errors. `published/demo.json` now identifies `ecr-poc-v3.json`, immutable generation `1787201087845537`, and SHA-256 `34ba69003c632d30a93aa47d3e21d4eb166634b1dcd91b44badc1b9de5ef23a1`. The service revision and Job use the same image digest `sha256:6d0ccf8179655f4211344d7d57403273220e252ac7388b0e7e08787376363c79`.

The accepted raw result and report are `results/runs/vertex-adk-v3.json`, `results/runs/vertex-adk-v3.manifest.json`, and `docs/results/experiment-report-v3.md`. The freeze tag remains on the implementation commit and is not moved by the later evidence commit.
