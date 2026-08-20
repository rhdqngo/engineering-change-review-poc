# Current Project State

status: blocked
phase: v5-local-function-complete-awaiting-explicit-external-approval
updated: 2026-08-20

## Objective

Build a reproducible NASA cFS engineering-artifact PoC that measures evidence-grounded LLM review after a fixed Hybrid Retrieval Top-K.

## Active scope delivered locally

- Separate v5 case schema over the pinned NASA subset, clean baseline, 32 spans, and 18 cases split Direct 4 / Semantic 4 / Cross-Artifact 4 / Clean 3 / Benign 3. Every mutation binds its changed source, original/changed content, structured values, targets, and target-specific exact evidence.
- One deterministic 50/50 BM25+dense Top-6 shared by Baseline and Proposed arms.
- Exactly three Google ADK `LlmAgent` roles with timeouts, exact-span/source gates, cardinality reconciliation, independent verification, and fail-closed publication.
- Active v5 manifest/index provenance and offline-only v1-v4 compatibility validation; no historical manifest, result, tag, or object was changed.
- Hardened GCS input/result store, per-case checkpoints, immutable results/failures, and an explicitly validated published pointer.
- Private Cloud Run web service and single-task sequential Job using one image digest and dedicated least-privilege identities.
- Structured allowlisted logs and approval-gated provisioning, deployment, billable execution, publication, and verification scripts.
- Active-v5 API/UI with fixture/published authority labels, TTL/GCS-generation caching, separated liveness/readiness/integrity, latest-request-only fail-closed rendering, complete blocked-record inspection, and responsive keyboard paths.
- Reproducible v5-q1 quality iteration that changes only query construction and records case-level failure classes plus before/after expected-target ranks.

## Preserved historical v4 result

| Item | Value |
| --- | --- |
| Freeze | `ecr-poc-v4-freeze` → `7b76bfaa74d743d3200421d0dad681d740f1ca1c` |
| Run / execution | `cloud-v4-20260820T050914Z-92f72d97` / `ecr-poc-evaluate-sxjnm` |
| Service revision | `ecr-poc-00007-xvc` |
| Image digest | `sha256:050ff3602378eb43e0fda6046bc35c788a5e891252c97589c346053d425f0a49` |
| Result generation | `1787202918502625` |
| Result SHA-256 | `22b07011b48daec60422a91c69420cdf08a58a85e972f51291de7980d0ee3116` |
| Completion | 18/18 cases, zero role errors |
| Retrieval coverage | 10/12 (83.3%) |
| Conditional review success | 9/10 (90.0%) |
| Control false alarm | 3/6 (50.0%) |
| Final verified reviews | 27 |

Acceptance is based on complete execution and evidence integrity, not target accuracy. The control false-alarm rate remains a material limitation and prevents an autonomous-use claim.

## V5 local verification state

| Check | Result |
| --- | --- |
| Active and historical data | active v5 validation passes; separate v1-v4 data/run validation passes and returns the preserved v1-v4 run IDs |
| Pipeline | local 18-case baseline and q1 runs complete; all within-run Baseline/Proposed candidate sequences and fingerprints match |
| Fail closed | exact-span, off-Top-K, duplicate/missing decisions, verifier rejection/missing, and provider-error paths are covered by tests |
| Metrics and comparison | complete overall/by-type metrics plus case-level classification and target-rank comparison generated |
| Tests/static/build | 49 tests pass; Ruff, mypy, package sdist/wheel build, and all five PowerShell parsers pass |
| GCP scripts | explicit manifest/tag/commit/prefix parameters and approval gates implemented; all five scripts parse |
| UI | independent audit findings repaired; actual local desktop/narrow, 20 rapid transitions, blocked-record selection, catalog 503→retry, published failure/recovery, and narrow keyboard scroll pass. Actual Vertex v5 remains approval-gated |
| Cloud v5 | not executed; explicit approval, exact commit, and freeze tag required |

V1 remains hash-consistent historical evidence without an externally timed preregistration claim. V2 and v3 runs/tags/GCS versions remain immutable. The failed v3 UI audit is preserved rather than rewritten; v4 closes its three major findings under a distinct pre-run freeze.

## Related artifacts

- Original plan: `docs/plans/LLM 기반 우주 Engineering Change Review.md`
- Active protocol: `docs/experiment-protocol-v5.md`
- Report: `docs/results/experiment-report-v5.md`
- Local baseline: `results/runs/fixture-v5-baseline.json`
- Local quality variant: `results/runs/fixture-v5-q1.json`
- Machine comparison: `results/comparisons/v5-baseline-vs-v5-q1.json`
- Deployment log: `docs/results/deployment-log.md`
- Completion audit: `docs/completion-audit.md`
- UI review: `docs/ui/reviews/2026-08-20-v5-local-docket.md`
- UI Foundation: `docs/ui/foundation.md` (provisional; validation does not promote governance status)

## Next checkpoint

User authorization is required before any remaining action. Accepted scopes are Git-only (commit/push/tag), full external execution (Git plus Cloud Run/GCS/IAM/Vertex/publish), or GCP-excluded closure. Do not move or overwrite any v1-v4 identity.

## Update rules

Update this document only when the active milestone, scope, major result, blocker, validation state, or next checkpoint changes materially.
