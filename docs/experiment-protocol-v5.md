# Verifiable v5 Function-Complete and Quality-Iteration Protocol

status: complete; baseline published; q1 comparison retained
baseline experiment: `ecr-poc-preregistered-v5`
baseline freeze tag: `ecr-poc-v5-freeze` → `4d1519f84cd5bac836ea8125ee2d63525ad2578d`
quality variant: `ecr-poc-preregistered-v5-q1`
quality freeze tag: `ecr-poc-v5-q1-freeze` → `4d1519f84cd5bac836ea8125ee2d63525ad2578d`

## Purpose

V5 is the first runtime contract that includes the full changed-artifact identity and target-specific expected evidence. It keeps the NASA `sample_app` subset and the Direct 4 / Semantic 4 / Cross-Artifact 4 / Clean 3 / Benign 3 distribution while separating active v5 validation from immutable v1-v4 historical validation.

Function completion is independent of retrieval or model accuracy. The local deterministic results exercise the complete pipeline and UI but are not LLM experiment evidence.

## Frozen baseline contract

- Active case file: `data/cases/cases-v5.json` with `changed_source_id`, original/changed content, structured old/new values, and target-specific exact evidence.
- Shared retrieval: BM25 0.5 + embedding 0.5, min-max fusion, Top-6.
- Query: `structured-change-v1`.
- Embedding metadata: `data/embeddings/ecr-poc-v5.json`; document-vector fingerprint is recorded in every run and case.
- Agents: exactly Change Analyst, Engineering Review, and Evidence Verifier.
- Final exposure: only Top-K, exact-span, and supported-verifier proposals become `VERIFIED_REVIEW`.
- Runtime web contract: active v5 only; historical validation is the offline `validate-historical` command.
- Publication cache: GCS generation identity or short TTL; case selection does not revalidate the entire result.
- Health: `/healthz` is liveness, `/readyz` is service readiness, and `/integrity` is active data/result integrity.

Local baseline identity:

- Result: `results/runs/fixture-v5-baseline.json`
- SHA-256: `904358fe8b25694b06e1a9bcbc18b1e88ce10dd982039e2c58700c3014a4167a`
- Manifest SHA-256: `40e7ba065ceaa059c8ce894426f0bc6b256f8bad6011cd78551e7dbd70293bfb`
- Embedding index fingerprint: `9235b163efa97ca5a58b4dc43ee6ebb2547ddfc811153a508868026799f3edb6`
- Provider/model: `fixture-not-llm` / `none`

## One-variable v5-q1 iteration

The v5-q1 manifest was validated before its result was generated. It changes only query construction from `structured-change-v1` to `structured-change-v2-artifact-delta`, appending the frozen changed source ID and original/changed content. Case labels, expected evidence, artifact corpus, document vectors, Top-K, fusion weights, prompt hashes, provider, model, and verifier behavior remain unchanged.

- Manifest: `data/experiments/ecr-poc-v5-q1.json`
- Manifest SHA-256: `3d1e45277dc35123f251b7e9166f87d9d40b2e9e28daf9c54c0567d015a18dd2`
- Result: `results/runs/fixture-v5-q1.json`
- Result SHA-256: `44f7b4c0ea5c8073dd57ef51f2ab02e09609421579903df2a0fb4db3882aec81`
- Machine comparison: `results/comparisons/v5-baseline-vs-v5-q1.json`

## External execution order

No external step runs without explicit approval.

1. Pass all local validation and browser gates.
2. Commit and push the exact implementation selected for the experiment.
3. Create and push the selected manifest's freeze tag without moving any v1-v4 tag.
4. Require `HEAD == origin/main == requested source commit == requested freeze tag` and a clean worktree.
5. Provision/upload/deploy using explicit manifest, tag, commit, GCS input prefix, run prefix, and published object parameters.
6. Execute one sequential 18-case Vertex/ADK Job with no retries.
7. Validate the immutable result before the separate approval-gated publish action.
8. Verify private access, dedicated identities, least-privilege IAM, structured logs, integrity endpoints, and actual desktop/narrow UI.

The baseline v5 Cloud execution should precede any billable q1 execution. Observed quality never changes the frozen labels or historical results.

## Completed external evidence

- Baseline execution `ecr-poc-evaluate-2s5kv` produced run `cloud-v5-20260820T072055Z-3efe8584`, generation `1787210878757222`, and SHA-256 `d04c26087b1436a956dd18ac353417c6ebcd8db828522c0fb9265516ede143ef`; it is the UI result at `published/v5/demo.json`.
- Q1 execution `ecr-poc-evaluate-l9mjm` produced run `cloud-v5-q1-20260820T074302Z-26e9b5e5`, generation `1787212289859637`, and SHA-256 `2e3b185f548eeff405e816e0c607edc11db46c8fac9c2f42dd369cd0a7a6cae2`; it is retained at the non-UI pointer `published/v5-q1/comparison.json`.
- Both runs use revision `ecr-poc-00008-pk2`, the same immutable image and document-vector fingerprint, complete 18/18 cases, and have zero role errors.
- All single-variable invariants passed. Q1 improved retrieval coverage but regressed false alarms and mean expected-target rank, so baseline remains the published demo.
