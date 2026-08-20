# Current Project State

status: in-progress
phase: v4-ui-integrity-closure
updated: 2026-08-20

## Objective

Build a reproducible NASA cFS engineering-artifact PoC that measures evidence-grounded LLM review after a fixed Hybrid Retrieval Top-K.

## Scope delivered

- Pinned NASA `nasa/sample_app` v7.0.1 subset, clean baseline, 32 spans, and 18 cases split Direct 4 / Semantic 4 / Cross-Artifact 4 / Clean 3 / Benign 3.
- One deterministic 50/50 BM25+dense Top-6 shared by Baseline and Proposed arms.
- Exactly three Google ADK `LlmAgent` roles with timeouts, exact-span/source gates, cardinality reconciliation, independent verification, and fail-closed publication.
- Version-aware v2/v3 experiment manifests, versioned prompt resources, remote freeze tags, and source/image/ADK/execution provenance.
- Hardened GCS input/result store, per-case checkpoints, immutable evaluation objects, failure records, and an explicitly validated published pointer.
- Private Cloud Run web service and single-task sequential evaluation Job using one image digest and dedicated least-privilege identities.
- Structured allowlisted logs and approval-gated provisioning, deployment, billable execution, publication, and verification scripts.
- GCS-authoritative API/UI with 503 fail-closed behavior, published provenance, no browser billable control, and verified loading/disabled states.

## Published v3 experiment result

| Item | Value |
| --- | --- |
| Freeze | `ecr-poc-v3-freeze` → `3984e77961b6edeacb2286935f65c1dd13c80a3e` |
| Run / execution | `cloud-v3-20260820T043842Z-6e260831` / `ecr-poc-evaluate-fq5s4` |
| Service revision | `ecr-poc-00006-6jz` |
| Image digest | `sha256:6d0ccf8179655f4211344d7d57403273220e252ac7388b0e7e08787376363c79` |
| Result generation | `1787201087845537` |
| Result SHA-256 | `34ba69003c632d30a93aa47d3e21d4eb166634b1dcd91b44badc1b9de5ef23a1` |
| Completion | 18/18 cases, zero role errors |
| Retrieval coverage | 10/12 (83.3%) |
| Conditional review success | 9/10 (90.0%) |
| Control false alarm | 4/6 (66.7%) |
| Final verified reviews | 29 |

The result is accepted based on complete execution and evidence integrity, not a target accuracy. The control false-alarm rate remains the primary product limitation and prevents an autonomous-use claim.

## Verification state

| Check | Result |
| --- | --- |
| Frozen data | passed; 18 source hashes, three v1 freeze hashes, v2/v3 manifests, unchanged v2 prompt hashes, 32 spans, 18 cases |
| Tests | passed; 31 tests including v3 drift/compatibility/loading, timeout, cardinality, checkpoint, logging, publication, and GCS 503 paths |
| Static/type/build | Ruff, mypy, PowerShell parsing, data validation, and `uv build` passed |
| Raw result | tracked 352,018-byte object SHA and generation match GCS pointer and manifest |
| Independent recomputation | 18 cases validate; metrics exactly match; all arms, fingerprints, exact spans, reasons, and verifier verdicts match |
| Cloud service / Job | same digest; 1 task / parallelism 1 / retries 0 / 1 CPU / 1 GiB / 1800 s configuration |
| IAM / access | dedicated web/job identities with required narrow roles only; no Editor/Owner/Storage Admin; unauthenticated request returns 403 |
| Logging | one run ID links start, 18 terminal cases, checkpoints, and completion without prompt, raw evidence, or credentials |
| UI | v3 loading copy passed, but independent audit failed on stale response ordering, 390 px Reload wrapping, and keyboard focus restoration |

V1 remains historical and hash-consistent but is not claimed as externally timed preregistration. Both completed v2 runs, the v2 published object version, and `ecr-poc-v2-freeze` remain immutable. V3 changes no case, artifact, retrieval, model, temperature, or role prompt; it closes the last loading-copy finding under a distinct pre-run freeze.

## Related artifacts

- Plan: `docs/plans/LLM 기반 우주 Engineering Change Review.md`
- Active protocol: `docs/experiment-protocol-v4.md`
- V3 protocol: `docs/experiment-protocol-v3.md`
- Report: `docs/results/experiment-report-v3.md`
- Raw result: `results/runs/vertex-adk-v3.json`
- Result manifest: `results/runs/vertex-adk-v3.manifest.json`
- Deployment log: `docs/results/deployment-log.md`
- Completion audit: `docs/completion-audit.md`
- UI review: `docs/ui/reviews/2026-08-20-published-v3-docket.md`
- UI Foundation: `docs/ui/foundation.md` (provisional; validation does not promote governance status)

## Active closure

The v3 experiment is complete and immutable, but its UI is not an approval candidate. A separately versioned v4 freeze will retain the exact cases, artifacts, retrieval, model, temperature, and prompt hashes while adding only request sequencing/cancellation, one-line narrow control geometry, and reload focus restoration. V3's tag and GCS objects will not move.

The v3 evidence record is committed and pushed at `ac06e8975c098a06f5d46954b9a18f97b0aae90d`. V4 implementation validation passes 34 tests, Ruff, mypy, data validation, build, five-script parsing, keyboard Reload focus restoration, latest-source consistency under rapid switching, and one-line 126 × 38 px Reload geometry without body overflow.

Next checkpoint: commit and push the v4 implementation, tag that exact commit as `ecr-poc-v4-freeze`, then deploy, execute, publish, and independently audit it.

## Update rules

Update this document only when the active milestone, scope, major result, blocker, validation state, or next checkpoint changes materially.
