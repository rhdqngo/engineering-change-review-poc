# Verifiable Cloud Experiment Protocol v2

status: complete-and-published-historical
experiment: `ecr-poc-preregistered-v2`
freeze tag: `ecr-poc-v2-freeze`
final freeze commit: `10c59bfba3e1b37afde026548f4c1f51ec6526ed`
final accepted run: `cloud-v2-20260820T035505Z-56ad91df`

## Why v2 exists

The retained v1 run is hash-consistent, but its input commit was created after the recorded model run. The repository therefore does not claim that v1 has externally verifiable preregistration timing. V2 reuses the unchanged v1 cases and NASA sources, adds frozen prompt hashes and code provenance, and requires a remote Git freeze before any v2 model result exists.

## Freeze order

1. Validate source, case, prompt, and experiment-manifest hashes.
2. Pass tests, lint, type check, build, and script parsing.
3. Commit the complete v2 implementation and inputs.
4. With explicit approval, push `main` and tag the same commit as `ecr-poc-v2-freeze`.
5. Verify `HEAD`, `origin/main`, and the freeze tag are identical and the worktree is clean.
6. Only then provision/deploy and execute the billable 18-case Cloud Run Job.

The provisioning, deployment, and execution scripts refuse to proceed when step 5 is false.

## Execution contract

- One Cloud Run Job task, parallelism 1, retries 0, timeout 30 minutes.
- Exactly one attempt per run ID. A failed execution is retained and never published; a later attempt receives a new run ID.
- Same three ADK LLM roles and the same fixed Hybrid Retrieval Top-6 comparison as v1.
- Role timeout: 120 seconds.
- Change Analyst or frozen-input failure fails the run before publication.
- Reviewer missing, duplicate, or out-of-set decisions and verifier missing/duplicate verdicts fail closed.
- The generic `evaluate` CLI accepts `--experiment-manifest`, `--run-id`, `--source-commit`, `--gcs-input-uri`, `--gcs-output-uri`, execution ID, and image digest. The Cloud Run Job command is an environment-backed shortcut over the same input/run-store contracts.

## Storage and publication

- GCS frozen inputs are authoritative for the Job and are hash-validated after download.
- Each case updates `runs/<run-id>/checkpoint.json` with generation preconditions.
- The completed `evaluation.json` and any `failure.json` are immutable.
- Job execution never publishes automatically. `published/demo.json` changes only through a separately approved command after terminal-checkpoint, case, metric, candidate-seal, exact-span, verifier-cardinality, role-error, generation, and SHA-256 checks pass.

Accuracy is not an acceptance threshold. A complete run with poor metrics remains a valid result and must be reported as observed.
