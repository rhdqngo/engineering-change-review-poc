# Current Project State

status: complete
phase: v4-published-and-verified
updated: 2026-08-20

## Objective

Build a reproducible NASA cFS engineering-artifact PoC that measures evidence-grounded LLM review after a fixed Hybrid Retrieval Top-K.

## Scope delivered

- Pinned NASA `nasa/sample_app` v7.0.1 subset, clean baseline, 32 spans, and 18 cases split Direct 4 / Semantic 4 / Cross-Artifact 4 / Clean 3 / Benign 3.
- One deterministic 50/50 BM25+dense Top-6 shared by Baseline and Proposed arms.
- Exactly three Google ADK `LlmAgent` roles with timeouts, exact-span/source gates, cardinality reconciliation, independent verification, and fail-closed publication.
- Version-aware v2/v3/v4 manifests, unchanged versioned prompts, remote freeze tags, and source/image/ADK/execution provenance.
- Hardened GCS input/result store, per-case checkpoints, immutable results/failures, and an explicitly validated published pointer.
- Private Cloud Run web service and single-task sequential Job using one image digest and dedicated least-privilege identities.
- Structured allowlisted logs and approval-gated provisioning, deployment, billable execution, publication, and verification scripts.
- GCS-authoritative API/UI with 503 fail-closed behavior, no browser billable control, latest-request-only rendering, stable narrow controls, and keyboard focus recovery.

## Final accepted v4 result

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

## Verification state

| Check | Result |
| --- | --- |
| Frozen data | passed; 18 source hashes, v1 freeze hashes, v2/v3/v4 manifests, unchanged v2 prompt hashes, 32 spans, 18 cases |
| Tests | passed; 34 tests including version drift/compatibility, loading, timeout, cardinality, checkpoint, logging, publication, and GCS 503 paths |
| Static/type/build | Ruff, mypy, five-script parsing, data validation, and `uv build` passed |
| Raw result | tracked 352,461-byte object SHA and generation match GCS pointer and manifest |
| Independent recomputation | 18 cases, metrics, arms, fingerprints, exact spans, reasons, and supported verifier verdicts all validate |
| Cloud service / Job | same digest; 1 task / parallelism 1 / retries 0 / 1 CPU / 1 GiB / 1800 s |
| IAM / access | dedicated identities and exact narrow roles; no Editor/Owner/Storage Admin; unauthenticated 403 |
| Logging | one run ID links start, 18 terminal cases, checkpoints, and completion without prompt/raw evidence/credentials |
| UI | independent deployed audit passes cold start, 28 rapid transitions, focus recovery, representative cases, 1440 × 900 and 390 × 844, ARIA/touch, and hidden rejected evidence |

V1 remains hash-consistent historical evidence without an externally timed preregistration claim. V2 and v3 runs/tags/GCS versions remain immutable. The failed v3 UI audit is preserved rather than rewritten; v4 closes its three major findings under a distinct pre-run freeze.

## Related artifacts

- Original plan: `docs/plans/LLM 기반 우주 Engineering Change Review.md`
- Active protocol: `docs/experiment-protocol-v4.md`
- Report: `docs/results/experiment-report-v4.md`
- Raw result: `results/runs/vertex-adk-v4.json`
- Result manifest: `results/runs/vertex-adk-v4.manifest.json`
- Deployment log: `docs/results/deployment-log.md`
- Completion audit: `docs/completion-audit.md`
- UI review: `docs/ui/reviews/2026-08-20-published-v4-docket.md`
- UI Foundation: `docs/ui/foundation.md` (provisional; validation does not promote governance status)

## Next checkpoint

No implementation or operational blocker remains. Future work must use a separately versioned experiment; do not move existing freeze tags or overwrite immutable result objects.

## Update rules

Update this document only when the active milestone, scope, major result, blocker, validation state, or next checkpoint changes materially.
