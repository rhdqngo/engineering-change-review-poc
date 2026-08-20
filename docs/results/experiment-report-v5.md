# Engineering Change Review v5 Cloud Completion Report

status: complete; baseline published; q1 retained as a non-UI comparison
updated: 2026-08-20

## Frozen identity

Both experiments use source commit `4d1519f84cd5bac836ea8125ee2d63525ad2578d`, revision `ecr-poc-00008-pk2`, and image digest `sha256:8f4cc7cf8fa04e5832b83634b45c5139868ee7d2f8f0d56c929a49521bbe8afd`. Lightweight tags `ecr-poc-v5-freeze` and `ecr-poc-v5-q1-freeze` identify that commit and were not moved after execution.

| Item | v5 baseline | v5-q1 |
| --- | --- | --- |
| Query | `structured-change-v1` | `structured-change-v2-artifact-delta` |
| Run | `cloud-v5-20260820T072055Z-3efe8584` | `cloud-v5-q1-20260820T074302Z-26e9b5e5` |
| Execution | `ecr-poc-evaluate-2s5kv` | `ecr-poc-evaluate-l9mjm` |
| GCS generation | `1787210878757222` | `1787212289859637` |
| Result SHA-256 | `d04c26087b1436a956dd18ac353417c6ebcd8db828522c0fb9265516ede143ef` | `2e3b185f548eeff405e816e0c607edc11db46c8fac9c2f42dd369cd0a7a6cae2` |
| Document-vector fingerprint | `16de2823647b628bd132b13001a0232fe45c9bd44ca45796bb4e8928d3f8505a` | same |
| Pointer | `published/v5/demo.json` | `published/v5-q1/comparison.json` |
| UI exposed | yes | no |

Both immutable results contain 18/18 terminal cases, zero role errors, identical Baseline/Proposed candidate sequences within every case, and strict checkpoint/generation/SHA, exact-span, verifier, provenance, and recomputed-metric validation.

## Actual Vertex comparison

Only query construction changed. Provider, generation model, embedding model and document-vector fingerprint, Top-K, fusion, prompt hashes, verifier behavior, cases, labels, source commit, and container image remained fixed. All eight machine invariant checks passed.

| Metric | baseline | v5-q1 | Observation |
| --- | ---: | ---: | --- |
| Retrieval coverage | 10/12 | 12/12 | q1 recovered SEM-04 and XART-02 |
| Conditional LLM review success | 9/10 | 10/12 | one more mutation retained, lower conditional rate |
| Clean/Benign false alarms | 4/6 | 5/6 | q1 added a CLN-01 false alarm |
| Verified / blocked | 29 / 5 | 33 / 9 | q1 selected and blocked more outputs |
| Expected targets retrieved | 11/13 | 13/13 | +2 |
| Mean expected-target rank | 1.818182 | 1.923077 | worse by 0.104895 |
| Mean reciprocal rank | 0.760606 | 0.737179 | worse by 0.023427 |

The query delta increased retrieval recall but did not produce an overall quality win. DIR-03 improved from rank 5 to 1 and previously missed SEM-04/XART-02 targets entered Top-K. XART-01 and both XART-03 targets regressed, and control false alarms increased. Baseline therefore remains the published demo result. These accuracy values are comparison evidence, not completion thresholds, and the high control false-alarm rate prevents an autonomous-use claim.

Machine-readable comparison: `results/comparisons/v5-vertex-baseline-vs-v5-q1.json`, SHA-256 `e75ddee0a50eb6480596eedf75c6a21fd2f4071357626d186ee3c92cf10494a1`.

## Cloud and UI verification

- `frozen/ecr-poc-v5` contains 30 generation-guarded inputs; v1-v4 prefixes and tags were unchanged.
- The private service and one-task/no-retry Job share the same image digest and dedicated identities. Web has bucket `objectViewer`; Job has bucket `objectUser` plus project `aiplatform.user`; neither has a broad project role.
- The approved verifier user has service-level `roles/run.invoker`; no `allUsers` or `allAuthenticatedUsers` binding exists. Final direct unauthenticated verification returned 403.
- Each run has one `job_started`, 18 `case_completed`, and one `evaluation_completed` event. No structured record contains prompt, raw output/evidence, credential, or token fields.
- Authenticated readiness/integrity returned the baseline run, source commit, GCS store, 18 cases, and valid freeze. Actual browser checks passed published/fixture authority, 20 rapid transitions, XART-04 withheld-record inspection, desktop/narrow layout, and keyboard table scroll from 0 to 320 px with no body overflow.

## Next single-variable iterations

1. Keep baseline retrieval fixed and change only the review prompt to reduce Clean/Benign over-selection.
2. In a later version, keep the winning prompt fixed and change only verifier support criteria for control-case abstention.
3. Revisit query construction only after those results; preserve both v5 runs and labels unchanged.

Any further Vertex run requires a new experiment identity and explicit billable approval.
