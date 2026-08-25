# Engineering Change Review Cloud Experiment v3

status: experiment-complete-and-published; ui-audit-failed
completed: 2026-08-20

## Result identity

- Experiment / manifest: `ecr-poc-preregistered-v3` / `ecr-poc-v3.json`
- Freeze: `ecr-poc-v3-freeze` at `3984e77961b6edeacb2286935f65c1dd13c80a3e`
- Run: `cloud-v3-20260820T043842Z-6e260831`
- Cloud Run execution: `ecr-poc-evaluate-fq5s4`
- Service revision: `ecr-poc-00006-6jz`
- Model / embedding: `gemini-3.5-flash` / `gemini-embedding-001`
- Prompt version / ADK: `ecr-poc-prompts-v2` / `2.7.1`
- Image: `sha256:6d0ccf8179655f4211344d7d57403273220e252ac7388b0e7e08787376363c79`
- GCS generation: `1787201087845537`
- Evaluation SHA-256: `34ba69003c632d30a93aa47d3e21d4eb166634b1dcd91b44badc1b9de5ef23a1`
- Execution window: `2026-08-20T04:39:06.212329Z`–`2026-08-20T04:44:47.790874Z`
- Published: `2026-08-20T04:45:11.889647Z`

The complete v3 implementation, frozen inputs, unchanged v2 prompts, and v3 manifest were committed, pushed, and tagged before execution. V2's tag, objects, runs, and published object version remain immutable historical evidence. The Job consumed only `frozen/ecr-poc-v3`, and publication required the run, pointer, manifest, source commit, freeze tag, checkpoint seal, execution, and image identity to agree.

## Metrics

| Measure | Overall | Direct | Semantic | Cross-artifact | Clean | Benign |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Cases | 18 | 4 | 4 | 4 | 3 | 3 |
| Retrieval coverage | 10/12 (83.3%) | 4/4 | 3/4 | 3/4 | n/a | n/a |
| Review success, conditional on retrieval hit | 9/10 (90.0%) | 4/4 | 3/3 | 2/3 | n/a | n/a |
| Control false alarm | 4/6 (66.7%) | n/a | n/a | n/a | 1/3 | 3/3 |
| Final verified reviews | 29 | 8 | 10 | 5 | 2 | 4 |
| Unsupported proposals blocked | 0 | 0 | 0 | 0 | 0 | 0 |

All 18 cases completed without a role error. Change Analyst and Engineering Review each produced 18 traces; Evidence Verifier ran for 16 cases and was intentionally skipped for two cases with no review proposal. Every exposed `VERIFIED_REVIEW` uses a fixed Top-K source, an exact non-empty source substring, a non-empty reason, and exactly one supported verifier verdict.

The tracked 352,018-byte raw artifact independently passed strict v3 provenance validation. Its SHA-256 matches the immutable GCS generation and published pointer; its metrics exactly match a fresh recomputation; and every Baseline/Proposed source sequence and candidate fingerprint validates.

## Interpretation

The result supports evidence-grounded review triage, not autonomous approval. Direct cases were consistently retrieved and retained, semantic cases were strong after retrieval, and cross-artifact review remained mixed. The material limitation remains the 4/6 control false-alarm rate: exact-span and verifier gates prevent unsupported evidence from reaching the UI, but a real source span can still be irrelevant to a clean or benign change.

No accuracy threshold was used for acceptance. V3 is accepted because the frozen 18-case run is complete, internally consistent, independently reproducible from its raw artifact, and externally bound to its pre-run Git/GCS/image provenance.

## Acceptance evidence

- `publish-run` validated the terminal checkpoint's generation/SHA seal and the complete run before changing `published/demo.json`.
- `verify-cloud-run.ps1` passed GCS pointer integrity, service/Job same digest, dedicated identities, least-privilege IAM, private unauthenticated 403, and structured-log completeness for one start, 18 terminal cases, and one completion.
- Actual browser review verified cold start, disabled reload, published v3 provenance, representative case values, and rejected-evidence non-exposure, but failed final UI acceptance on stale-response sequencing, narrow Reload wrapping, and keyboard focus restoration.
- Tracked artifacts: `results/runs/vertex-adk-v3.json` and `results/runs/vertex-adk-v3.manifest.json`.
