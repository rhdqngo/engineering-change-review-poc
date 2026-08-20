# Current Project State

status: complete
phase: v5-cloud-complete-baseline-published-q1-compared
updated: 2026-08-20

## Objective

Build a reproducible NASA cFS engineering-artifact PoC that measures evidence-grounded LLM review after a fixed Hybrid Retrieval Top-K.

## Completed v5 milestone

- Frozen implementation commit `4d1519f84cd5bac836ea8125ee2d63525ad2578d` is pushed and identified by both `ecr-poc-v5-freeze` and `ecr-poc-v5-q1-freeze`.
- The pinned NASA subset, clean baseline, 32 spans, and 18 cases remain split Direct 4 / Semantic 4 / Cross-Artifact 4 / Clean 3 / Benign 3 with target-specific exact evidence.
- Baseline and Proposed share one 50/50 BM25+dense Top-6 candidate object sequence and fingerprint; exactly three ADK roles operate behind deterministic fail-closed gates.
- Cloud Run revision `ecr-poc-00008-pk2` and the evaluation Job use image digest `sha256:8f4cc7cf8fa04e5832b83634b45c5139868ee7d2f8f0d56c929a49521bbe8afd`, dedicated least-privilege identities, private access, immutable GCS objects, and safe structured logging.
- Baseline run `cloud-v5-20260820T072055Z-3efe8584` is the UI result at `published/v5/demo.json`; q1 run `cloud-v5-q1-20260820T074302Z-26e9b5e5` is retained only at `published/v5-q1/comparison.json`.
- Both actual Vertex runs completed 18/18 cases with zero role errors and the same document-vector fingerprint `16de2823647b628bd132b13001a0232fe45c9bd44ca45796bb4e8928d3f8505a`.
- Actual desktop/narrow browser validation passed published authority, rapid case switching, evidence/verifier/blocked inspection, provenance, and keyboard table scrolling.
- V1-v4 manifests, results, tags, GCS prefixes, and historical evidence remain unchanged.

## Quality result

The q1 query-only change raised retrieval coverage from 10/12 to 12/12 and expected targets retrieved from 11/13 to 13/13. It also increased Clean/Benign false alarms from 4/6 to 5/6 and worsened mean target rank from 1.818182 to 1.923077. Baseline remains the published demo; no accuracy threshold was used as a completion condition.

## Verification state

| Check | Result |
| --- | --- |
| Data and history | active v5 plus offline v1-v4 validation pass |
| Pipeline and fail-closed | strict result validation passes for both Vertex runs; exact-span/off-Top-K/cardinality/verifier/provider failure tests pass |
| Local quality gates | pytest, Ruff, mypy, build, PowerShell parsing, result comparison, and historical diff pass |
| Cloud | private service, same service/Job digest, GCS pointer seals, minimum IAM, 1/18/1 structured logs, and prohibited-field audit pass |
| UI | actual baseline published result passes desktop/narrow, 20 rapid transitions, blocked-record selection, provenance, and keyboard scroll |

## Related artifacts

- Original plan: `docs/plans/LLM 기반 우주 Engineering Change Review.md`
- Protocol: `docs/experiment-protocol-v5.md`
- Report: `docs/results/experiment-report-v5.md`
- Baseline result: `results/runs/vertex-adk-v5.json`
- q1 result: `results/runs/vertex-adk-v5-q1.json`
- Actual comparison: `results/comparisons/v5-vertex-baseline-vs-v5-q1.json`
- Deployment log: `docs/results/deployment-log.md`
- Completion audit: `docs/completion-audit.md`
- Published UI review: `docs/ui/reviews/2026-08-20-published-v5-docket.md`
- UI Foundation: `docs/ui/foundation.md` remains provisional; validation does not promote governance status.

## Next checkpoint

No required v5 work remains. Any subsequent quality iteration must change one of prompt, retrieval, or verifier at a time under a new experiment identity and receive fresh billable approval before Vertex execution.

## Update rules

Update this document only when the active milestone, scope, major result, blocker, validation state, or next checkpoint changes materially.
