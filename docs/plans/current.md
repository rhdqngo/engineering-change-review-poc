# Current Project State

status: complete
phase: verifiable-v2-cloud-completion
updated: 2026-08-20

## Objective

Build a reproducible NASA cFS engineering-artifact PoC that measures evidence-grounded LLM review after a fixed Hybrid Retrieval Top-K.

## Scope delivered

- Pinned NASA `nasa/sample_app` v7.0.1 subset, clean baseline, 32 spans, and 18 cases split Direct 4 / Semantic 4 / Cross-Artifact 4 / Clean 3 / Benign 3.
- One deterministic 50/50 BM25+dense Top-6 shared by Baseline and Proposed arms.
- Exactly three Google ADK `LlmAgent` roles with timeouts, exact-span/source gates, cardinality reconciliation, independent verification, and fail-closed publication.
- Versioned v2 input and prompt manifest, remote freeze tag, source/image/ADK/execution provenance.
- Hardened GCS input/result store, per-case checkpoints, immutable evaluation object, failure object, and explicit published pointer.
- Private Cloud Run web service and single-task sequential evaluation Job using one image digest and dedicated least-privilege identities.
- Structured allowlisted logs and approval-gated provisioning, deployment, billable execution, publication, and verification scripts.
- GCS-authoritative API/UI with 503 fail-closed behavior, published run provenance, and no browser billable control.

## Final accepted v2 result

| Item | Value |
| --- | --- |
| Freeze | `ecr-poc-v2-freeze` → `10c59bfba3e1b37afde026548f4c1f51ec6526ed` |
| Run / execution | `cloud-v2-20260820T035505Z-56ad91df` / `ecr-poc-evaluate-587r6` |
| Service revision | `ecr-poc-00005-485` |
| Image digest | `sha256:65d65dc7924ca535c4d8c659d13e1297155c83dda993755c83399350a7b164c6` |
| Result generation | `1787198456573991` |
| Result SHA-256 | `8ac24782609bcd61f9589f78f9786468ab6badd16e8461298287e4ad2be2ffb0` |
| Completion | 18/18 cases, zero role errors |
| Retrieval coverage | 10/12 (83.3%) |
| Conditional review success | 9/10 (90.0%) |
| Control false alarm | 4/6 (66.7%) |
| Final verified reviews | 28 |

The result is accepted based on complete execution and evidence integrity, not a target accuracy. The control false-alarm rate is the primary product limitation and prevents an autonomous-use claim.

## Verification state

| Check | Result |
| --- | --- |
| Frozen data | passed; 18 source hashes, three v1 freeze hashes, v2 manifest/prompt hashes, 32 spans, 18 cases |
| Tests | passed; 28 tests including drift, timeout, cardinality, checkpoint, logging, publication, and GCS 503 paths |
| Static/type/build | Ruff, mypy, and `uv build` passed |
| Raw result | SHA and generation match GCS pointer and tracked manifest |
| Independent recomputation | 18 cases validate; metrics exactly match; all arms and fingerprints match |
| Cloud service / Job | same digest, required 1 task / parallelism 1 / retries 0 / 1 CPU / 1 GiB / 1800 s configuration |
| IAM | dedicated web/job identities; required narrow roles only; no Editor/Owner/Storage Admin on either |
| Access boundary | private Cloud Run; unauthenticated request returns 403 |
| Logging | one run ID links start, 18 terminal case events, checkpoints, and completion without raw evidence/secrets |
| UI | actual deployed published run, source commit and v2 freeze visible; representative five case types and 390 px layout passed |

V1 raw results remain historical and hash-consistent, but are not claimed as externally timed preregistration. The first completed v2 run also remains immutable, but was superseded after its deployed UI failed provenance presentation review. The corrected UI was re-frozen before the final run above.

## Blockers and next checkpoint

No completion blocker remains. Any future work is a new milestone, most plausibly reducing control false alarms and re-running under a new experiment version rather than modifying this frozen v2 result.

## Related artifacts

- Plan: `docs/plans/LLM 기반 우주 Engineering Change Review.md`
- Protocol: `docs/experiment-protocol-v2.md`
- Report: `docs/results/experiment-report-v2.md`
- Raw result: `results/runs/vertex-adk-v2.json`
- Result manifest: `results/runs/vertex-adk-v2.manifest.json`
- Deployment log: `docs/results/deployment-log.md`
- Completion audit: `docs/completion-audit.md`
- UI Foundation: `docs/ui/foundation.md` (provisional)

## Update rules

Update this document only when the active milestone, scope, major result, blocker, validation state, or next checkpoint changes materially.
