# Engineering Change Review v5 Local Completion Report

status: local-function-complete; cloud evidence pending explicit approval
updated: 2026-08-20

## Result identity and scope

The active v5 implementation has a complete 18-case deterministic fixture run. It verifies data, retrieval sharing, three-role flow, fail-closed defenses, metrics, provenance, storage validation, API, and UI behavior without invoking Vertex or changing GCP. It is not an LLM accuracy result.

| Item | v5 baseline | v5-q1 |
| --- | --- | --- |
| Experiment | `ecr-poc-preregistered-v5` | `ecr-poc-preregistered-v5-q1` |
| Query | `structured-change-v1` | `structured-change-v2-artifact-delta` |
| Run | `fixture-v5-baseline` | `fixture-v5-q1` |
| Result SHA-256 | `904358fe8b25694b06e1a9bcbc18b1e88ce10dd982039e2c58700c3014a4167a` | `44f7b4c0ea5c8073dd57ef51f2ab02e09609421579903df2a0fb4db3882aec81` |
| Document-vector fingerprint | `9235b163efa97ca5a58b4dc43ee6ebb2547ddfc811153a508868026799f3edb6` | same |
| Cases | 18/18 | 18/18 |
| Retrieval coverage | 12/12 | 12/12 |
| Conditional review success | 12/12 | 12/12 |
| Clean/Benign false alarms | 0/6 | 0/6 |
| Verified / blocked | 13 / 1 | 13 / 1 |

The identical outcome metrics are expected because the fixture provider uses the frozen expected targets. They prove the paths and gates, not Gemini behavior.

## One-variable quality result

The reproducible comparison held provider, generation model, embedding model and document-vector fingerprint, Top-K, fusion, prompt hashes, verifier, cases, and labels fixed. Only query construction changed.

| Retrieval diagnostic | baseline | v5-q1 | delta |
| --- | ---: | ---: | ---: |
| Expected targets retrieved | 13/13 | 13/13 | 0 |
| Mean expected-target rank | 1.846154 | 1.692308 | -0.153846 (better) |
| Mean reciprocal rank | 0.756410 | 0.762821 | +0.006411 (better) |

All case-level categories were empty in both fixture runs: retrieval miss, expected-target miss, mutation unnecessary warning, control false alarm, and verifier pass error. Candidate sequences changed in all 18 cases, as expected from the query change. Improvements were concentrated in DIR-03 (6→1), SEM-02 (2→1), and SEM-03 (3→2). XART-01 (1→3) and both XART-03 targets (3→4 and 1→3) regressed. The next iteration should address the cross-artifact trade-off by changing one variable only; no label or prior result should be edited.

Machine-readable details are in `results/comparisons/v5-baseline-vs-v5-q1.json` (SHA-256 `5a0130c700cbd574d8b075865bb9d280f360ecb0ddee69c77c2561a04bbf6049`).

## Remaining external evidence

V1-v4 tags, manifests, results, and GCS objects remain historical and unchanged. V5 Cloud Run/Job, Vertex embeddings/generation, v5 GCS prefix/published pointer, IAM, Logging, and deployed UI have not been executed in this worktree. They require an exact commit and freeze tag, then explicit billable/deploy/publish approval.
