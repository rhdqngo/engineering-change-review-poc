# Engineering Change Review Cloud Experiment v2

status: complete-and-published
completed: 2026-08-20

## Result identity

- Experiment: `ecr-poc-preregistered-v2`
- Freeze: `ecr-poc-v2-freeze` at `10c59bfba3e1b37afde026548f4c1f51ec6526ed`
- Run: `cloud-v2-20260820T035505Z-56ad91df`
- Cloud Run execution: `ecr-poc-evaluate-587r6`
- Service revision: `ecr-poc-00005-485`
- Model / embedding: `gemini-3.5-flash` / `gemini-embedding-001`
- ADK: `2.7.1`
- Image: `sha256:65d65dc7924ca535c4d8c659d13e1297155c83dda993755c83399350a7b164c6`
- GCS generation: `1787198456573991`
- Evaluation SHA-256: `8ac24782609bcd61f9589f78f9786468ab6badd16e8461298287e4ad2be2ffb0`
- Execution window: `2026-08-20T03:55:28.608156Z`–`2026-08-20T04:00:56.517689Z`
- Published: `2026-08-20T04:01:19.342489Z`

The implementation, frozen inputs, role prompts, and manifest were committed, pushed, and tagged before this model execution. The Job downloaded only the GCS frozen prefix and verified its hashes. The published pointer names the immutable object generation and digest above.

## Metrics

| Measure | Overall | Direct | Semantic | Cross-artifact | Clean | Benign |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Cases | 18 | 4 | 4 | 4 | 3 | 3 |
| Retrieval coverage | 10/12 (83.3%) | 4/4 | 3/4 | 3/4 | n/a | n/a |
| Review success, conditional on retrieval hit | 9/10 (90.0%) | 4/4 | 3/3 | 2/3 | n/a | n/a |
| Control false alarm | 4/6 (66.7%) | n/a | n/a | n/a | 1/3 | 3/3 |
| Final verified reviews | 28 | 8 | 9 | 5 | 2 | 4 |
| Unsupported proposals blocked | 0 | 0 | 0 | 0 | 0 | 0 |

All 18 cases completed without a role error. Change Analyst and Engineering Review each produced 18 traces; Evidence Verifier ran for 16 cases and was intentionally skipped for the two cases with no exact review proposals. Every final `VERIFIED_REVIEW` has a fixed Top-K source, an exact non-empty source substring, a non-empty reason, and exactly one supported verifier verdict.

The metrics above were independently recomputed from the tracked raw 18-case artifact and exactly matched the stored metrics. Baseline and Proposed source IDs remain identical and ordered for every case, and all candidate fingerprints recompute correctly.

## Interpretation

The run supports a narrow triage claim, not autonomous approval. Direct changes were consistently retrieved and retained; semantic changes were strong once retrieved; cross-artifact performance was mixed. The 4/6 control false-alarm rate is the material limitation: exact-span and independent-verifier gates prevent fabricated evidence, but do not by themselves establish that a true source span is relevant to a benign or clean request.

The retained v1 run remains hash-consistent but is not described as externally timed preregistration because its Git freeze postdated execution. Its headline result was 10/12 retrieval coverage, 9/10 conditional review success, 4/6 control false alarms, and 29 verified reviews. The final v2 run has the same headline rates and one fewer verified review, while adding externally verifiable pre-run Git/GCS/prompt/image provenance.

An earlier v2 execution (`cloud-v2-20260820T032620Z-bc550a11`) was technically valid and remains immutable in GCS. It was not accepted as final because an independent browser audit found ambiguous run-ID truncation and an incorrect `legacy freeze` label. Those presentation and accessibility defects were fixed before the final freeze, redeployment, and run recorded here.

## Acceptance evidence

- `publish-run` validated the full run before changing `published/demo.json`.
- `verify-cloud-run.ps1` passed health, data freeze, pointer generation/SHA, 18 cases, same service/Job digest, dedicated service accounts, least-privilege IAM, structured-log completeness, and unauthenticated 403 checks.
- Actual browser review passed published provenance, representative Direct/Semantic/Cross-Artifact/Clean/Benign cases, 390 px layout, selectable evidence rows, and non-exposure of rejected evidence.
- Tracked artifacts: `results/runs/vertex-adk-v2.json` and `results/runs/vertex-adk-v2.manifest.json`.
