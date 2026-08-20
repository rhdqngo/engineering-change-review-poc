# Current Project State

status: in-progress
phase: v6-purpose-driven-design-freeze
updated: 2026-08-20

## Objective

Discover which unchanged NASA cFS baseline artifacts warrant human re-review after an Incoming Artifact and expose only independently supported atomic impact claims with exact source evidence.

## Design decision

- The unfinished v6 is redesigned in place; no v7 is created.
- The normative requirements are `docs/plans/LLM 기반 우주 Engineering Change Review.md` and Decision 0001.
- The final pipeline is deterministic Query Processor → Broad Hybrid Top-40 → typed identifier 1-hop expansion → deterministic Final Top-10 → Engineering Reviewer atomic claims → deterministic evidence validation → independent Evidence Verifier → Human Engineer.
- Google ADK retains exactly two `LlmAgent` roles: Engineering Reviewer and Evidence Verifier.
- The existing 20 cases become a frozen regression/diagnostic benchmark rather than an unseen preregistered evaluation.
- A dedicated `ecr-poc-v6-design-freeze` commit/tag is created before production code is changed for this redesign. The tag never moves.

## Completed local implementation

- V1-v5 tags, results, manifests, and published evidence remain untouched and pass the offline compatibility validator.
- The official cFS v7.0.1 root commit and recursive submodules are ingested deterministically into 35,515 typed chunks with stable IDs, exact line ranges, source/content hashes, exclusions, licenses, and a byte-preserving selected-source archive. A conservative 1,800-byte content window keeps every serialized document within a locally enforced 2,000-byte provider envelope.
- The v6 pre-freeze manifest and exactly 20 Incoming Artifact cases exist with Direct 5 / Semantic 5 / Cross-Artifact 5 / Clean 2 / Benign 3 distribution, basis sources, targets, and exact target evidence.
- A row-major immutable embedding-index format validates vector bytes, dimensions, ordered source IDs, package identity, and fingerprint. The current 384-dimensional deterministic index is local functional evidence only.
- The shared 50/50 BM25+dense Top-10 docket uses Incoming Artifact plus Change Analyst normalization without inserting the incoming text into the corpus.
- `POST /api/reviews` implements strict validation, one-request admission, 429/503/502/504 boundaries, three overall statuses, sanitized response/logging, and reviewer/verifier fail-closed `INCONCLUSIVE` handling.
- `/` is the Live Review flow and `/evaluation` is the separate preregistered result surface. Both reuse the docket/evidence grammar under provisional Foundation 0.2.
- Deployment scripts target `frozen/ecr-poc-v6`, `runs/v6`, and `published/v6/demo.json`, configure a private max-instance-1/concurrency-1/300-second service, and retain explicit approval switches.
- The original project requirements document now starts from a user-submitted Incoming Artifact and is synchronized with the v6 input/API contract, exact three-Agent responsibilities, frozen retrieval/index boundary, Live/Evaluation UI split, and current failure-oriented test matrix; mutation-arm language is retained only as an explicit historical non-goal.

## Current validation state

- `validate-data`: passing for 35,515 artifacts and 20 cases after exact-evidence-preserving source-ID remapping.
- `validate-historical`: passing for v1-v5, including both v5 baseline and q1 actual results.
- Two independent ingests of the same recursive checkout produced byte-identical artifact packages, provenance manifests, raw-source archives, artifact ordering, and hashes.
- Full pytest passed with 54 tests; Ruff, mypy, package build, and all five PowerShell parser checks pass after the provider-limit correction.
- Vertex document generation checkpoints each completed batch as hash/vector-only local cache shards, so a later provider failure does not rebill completed batches; live Incoming Artifact queries bypass disk caching.
- Actual in-app browser review passed at 1440×900 and 390×844 for Live Review and Evaluation, including long input, validation recovery, review-required/no-review/inconclusive states, rapid case switching, fail-closed evidence display, focus transfer, and narrow table containment.
- No Vertex document embedding, GCP provisioning, deployment, 20-case Job, or publish action has been executed for v6.

## Vertex embedding attempt

- The first approved generation completed 140 provider batches and retained 13,389 unique document vectors before stopping on a provider `INVALID_ARGUMENT`: one 3,982-byte serialized C function was reported as 2,489 tokens, above the model's 2,048-token limit.
- The failed attempt was not retried. No GCS object, deployment, Job, or published pointer was created.
- The ingest boundary was corrected locally without truncation; two fresh ingests are byte-identical and the maximum serialized document is now 1,923 bytes. Of 32,921 unique serialized texts in the corrected corpus, 10,381 reuse an existing checkpoint and 22,540 remain (226 batches). Duplicate texts are submitted only once.

## Approval-gated blocker

The next irreversible/billable checkpoint is a resumed generation of the official 768-dimensional `gemini-embedding-001` `RETRIEVAL_DOCUMENT` matrix against the corrected 35,515-chunk corpus. Immediately before that call, a new explicit user approval is required. The pre-freeze manifest must then be updated with the Vertex vector/index hashes and immutable GCS generation evidence before commit/tag.

## Next checkpoint

Finish the corrected-corpus full local regression, then request approval to resume the Vertex document embedding generation using the preserved per-text cache. After validating that index, separately approve the four-object immutable GCS payload upload, pin its generation inventory in the manifest, and rerun the final freeze gate. Do not create the v6 freeze tag or deploy the live billable service while the manifest still identifies the local deterministic index.

## Preserved v5 milestone

The v5 implementation freeze remains `4d1519f84cd5bac836ea8125ee2d63525ad2578d`; baseline run `cloud-v5-20260820T072055Z-3efe8584` remains at `published/v5/demo.json`, and q1 remains at `published/v5-q1/comparison.json`. V5 and v6 performance are not compared.
