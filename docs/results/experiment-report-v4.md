# Engineering Change Review Cloud Experiment v4

status: complete-and-published
completed: 2026-08-20

## Result identity

- Experiment / manifest: `ecr-poc-preregistered-v4` / `ecr-poc-v4.json`
- Freeze: `ecr-poc-v4-freeze` at `7b76bfaa74d743d3200421d0dad681d740f1ca1c`
- Run: `cloud-v4-20260820T050914Z-92f72d97`
- Cloud Run execution: `ecr-poc-evaluate-sxjnm`
- Service revision: `ecr-poc-00007-xvc`
- Model / embedding: `gemini-3.5-flash` / `gemini-embedding-001`
- Prompt version / ADK: `ecr-poc-prompts-v2` / `2.7.1`
- Image: `sha256:050ff3602378eb43e0fda6046bc35c788a5e891252c97589c346053d425f0a49`
- GCS generation: `1787202918502625`
- Evaluation SHA-256: `22b07011b48daec60422a91c69420cdf08a58a85e972f51291de7980d0ee3116`
- Execution window: `2026-08-20T05:09:42.396857Z`–`2026-08-20T05:15:18.451026Z`
- Published: `2026-08-20T05:15:48.851107Z`

The implementation, unchanged frozen cases/artifacts/prompts, and v4 manifest were committed, pushed, and tagged before execution. V1/v2/v3 tags, runs, objects, and historical pointer generations remain immutable. Publication required the terminal checkpoint and run/pointer/manifest/source/tag/execution/image identities to agree.

## Metrics

| Measure | Overall | Direct | Semantic | Cross-artifact | Clean | Benign |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Cases | 18 | 4 | 4 | 4 | 3 | 3 |
| Retrieval coverage | 10/12 (83.3%) | 4/4 | 3/4 | 3/4 | n/a | n/a |
| Review success, conditional on retrieval hit | 9/10 (90.0%) | 4/4 | 3/3 | 2/3 | n/a | n/a |
| Control false alarm | 3/6 (50.0%) | n/a | n/a | n/a | 1/3 | 2/3 |
| Final verified reviews | 27 | 8 | 9 | 5 | 2 | 3 |
| Unsupported proposals blocked | 0 | 0 | 0 | 0 | 0 | 0 |

All 18 cases completed without a role error. Change Analyst and Engineering Review each produced 18 traces; Evidence Verifier ran for 15 cases and was intentionally skipped for three cases with no review proposal. Every exposed `VERIFIED_REVIEW` uses a fixed Top-K source, an exact non-empty source substring, a non-empty reason, and exactly one supported verifier verdict.

The tracked 352,461-byte raw artifact independently passed strict v4 provenance validation. Its SHA-256 matches the immutable GCS generation and published pointer; its metrics exactly match a fresh recomputation; and every Baseline/Proposed source sequence and candidate fingerprint validates.

## Interpretation

V4 supports evidence-grounded triage, not autonomous approval. The observed control false-alarm rate improved from v3's 4/6 to 3/6, but no accuracy target governed acceptance and this single rerun is not evidence of a stable improvement. A real exact span can still be irrelevant to a clean or benign request, so human review remains required.

## Acceptance evidence

- Publication validated the checkpoint generation/SHA seal, 18 cases, fixed arms/fingerprints, exact evidence, verifier cardinality, zero role errors, metrics, and complete v4 provenance.
- Cloud verification passed GCS pointer integrity, one service/Job digest, dedicated identities, least-privilege IAM, private 403, and structured logs with one start, 18 terminal cases, and one completion without prohibited content.
- Actual deployed browser checks covered cold start, latest-request-only source transitions, Reload focus restoration, v4 provenance, representative five case types, responsive layout, ARIA/touch targets, and rejected-evidence non-exposure.
- Tracked artifacts: `results/runs/vertex-adk-v4.json` and `results/runs/vertex-adk-v4.manifest.json`.
