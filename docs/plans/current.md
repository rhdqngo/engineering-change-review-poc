# Current Project State

status: in-progress
phase: v6-implementation-frozen-local
updated: 2026-08-20

## Objective

Discover which unchanged NASA cFS baseline artifacts warrant human re-review after an Incoming Artifact and expose only independently supported atomic impact claims with exact source evidence.

## Design decision

- The unfinished v6 is redesigned in place; no v7 is created.
- The normative requirements are `docs/plans/LLM 기반 우주 Engineering Change Review.md` and Decision 0001.
- The final pipeline is deterministic Query Processor → Broad Hybrid Top-40 → typed identifier 1-hop expansion → deterministic Final Top-10 → Engineering Reviewer atomic claims → deterministic evidence validation → independent Evidence Verifier → Human Engineer.
- Google ADK retains exactly two `LlmAgent` roles: Engineering Reviewer and Evidence Verifier.
- The existing 20 cases become a frozen regression/diagnostic benchmark rather than an unseen preregistered evaluation.
- Dedicated commit `ed4dd2a6da058675a62b8540451db9c18612ffa8` and local lightweight tag `ecr-poc-v6-design-freeze` freeze the purpose and architecture. The tag never moves and has not been pushed.

## Completed local implementation

- V1-v5 tags, results, manifests, and published evidence remain untouched and pass the offline compatibility validator.
- The official cFS v7.0.1 root commit and recursive submodules are ingested deterministically into 35,515 typed chunks with stable IDs, exact line ranges, source/content hashes, exclusions, licenses, and a byte-preserving selected-source archive. A conservative 1,800-byte content window keeps every serialized document within a locally enforced 2,000-byte provider envelope.
- The v6 pre-freeze manifest and exactly 20 Incoming Artifact cases exist with Direct 5 / Semantic 5 / Cross-Artifact 5 / Clean 2 / Benign 3 distribution, basis sources, frozen atomic claim slots, derived targets, and exact target evidence.
- A row-major immutable embedding-index format validates vector bytes, dimensions, ordered source IDs, package identity, and fingerprint. The approved 768-dimensional `gemini-embedding-001` `RETRIEVAL_DOCUMENT` index is complete and locally validated.
- The deterministic Query Processor uses only Incoming Artifact fields; it invokes no LLM and inserts no incoming data into any baseline index. Broad 50/50 BM25+dense Top-40, typed identifier 1-hop expansion capped at 200, and deterministic Final Top-10 ranking emit three independent fingerprints.
- The immutable identifier index contains 35,318 typed entries and was generated twice with byte-identical SHA-256 `711d8e1f48de2d356ca977b13fa5240926a44f802bb4a7371ff88552496a0dd5`.
- Google ADK now has exactly two roles. Reviewer output uses atomic claim slots; deterministic line/span validation precedes one fixed-order verifier batch. Only supported claims are projected into the public candidate results.
- `POST /api/reviews` implements strict validation, one-request admission, 429/503/502/504 boundaries, `REVIEW_REQUIRED` / `NO_SUPPORTED_REVIEW` / `INCONCLUSIVE`, partial truth, sanitized response/logging, and reviewer/verifier fail-closed handling.
- `/` is Live Review and `/evaluation` is the separate frozen regression benchmark. Both reuse the docket/evidence grammar under provisional Foundation 0.2.
- Deployment scripts target `frozen/ecr-poc-v6`, `runs/v6`, and `published/v6/demo.json`, configure a private max-instance-1/concurrency-1/300-second service, and retain explicit approval switches.
- The normative requirements, Decision 0001, manifest provenance, implementation, and current API/UI vocabulary use the same purpose-driven v6 contract. Mutation-arm and Change Analyst language remain only in explicitly historical v1-v5 evidence.

## Current validation state

- `validate-data`: passing for 35,515 artifacts and 20 cases after exact-evidence-preserving source-ID remapping.
- `validate-historical`: passing for v1-v5, including both v5 baseline and q1 actual results.
- Two independent ingests of the same recursive checkout produced byte-identical artifact packages, provenance manifests, raw-source archives, artifact ordering, and hashes.
- Final local gate passes: `validate-data`, `validate-historical`, 52 pytest tests, Ruff, mypy, package build, and PowerShell parsing 5/5.
- Vertex document generation checkpoints each completed batch as hash/vector-only local cache shards, so a later provider failure does not rebill completed batches; live Incoming Artifact queries bypass disk caching.
- Fresh in-app browser validation passes at 1440×900 and 390×844 for Live and Evaluation: long input, no-supported/review-required/inconclusive, validation/index recovery, result/error focus, supported-claim-only evidence, Broad/Expanded/Final scope, rapid case switching, keyboard docket scrolling, single-line narrow actions, and body/table overflow.
- The five large immutable payloads were uploaded once to `gs://ecr-poc-912838451352-asia-northeast3/frozen/ecr-poc-v6` with generation preconditions, then a second pass verified all five existing objects byte-for-byte without creating a new generation. The tracked and staged manifests pin every generation and SHA-256.
- No v6 full-tree upload, deployment, 20-case Job, or publish action has been executed.

## Vertex embedding generation

- The first approved generation completed 140 provider batches and retained 13,389 unique document vectors before stopping on a provider `INVALID_ARGUMENT`: one 3,982-byte serialized C function was reported as 2,489 tokens, above the model's 2,048-token limit.
- The ingest boundary was corrected locally without truncation; two fresh ingests are byte-identical and the maximum serialized document is 1,923 bytes.
- After renewed approval, generation resumed from the preserved cache: 10,381 corrected-corpus texts were reused and the remaining 22,540 unique texts completed. The cache now contains 366 atomic batch shards.
- The final index contains 35,515 ordered rows at 768 dimensions. Metadata SHA-256 is `0abacaefc3637f4ca33842df3f91940e0f03f8bfbc66f9c9b692e2bc350f82a0`, vector SHA-256 is `e480ff4846aceb79bfa40c71c446ce35555bf9b89ec6ab95e144087a74fbbb8f`, and fingerprint is `60204dd53bc1b8a9f2013552502fecf46aeb5a6a65df66fb38294d8e762b9748`.
- A second cache-only build produced byte-identical metadata and vector files. The active pre-freeze manifest and regenerated fixture now bind to this Vertex index. No GCS object, deployment, Job, or published pointer was created.

## Approval-gated boundary

The implementation tree carrying this document is the local `ecr-poc-v6-freeze`; the earlier `ecr-poc-v6-design-freeze` remains on the design commit and is not moved. Neither the implementation commit nor tag is pushed without a separate approval. Provisioning/full-tree upload and private Cloud Run/Job deployment are a later external approval boundary; the official 20-case Job and publication each require another explicit approval.

## Next checkpoint

Request approval to push the implementation commit and `ecr-poc-v6-freeze`. After that push is verified, request a separate approval to provision/verify the existing dedicated resources, upload the final small frozen inputs without changing the five sealed payloads, and deploy the private service/Job. The official 20-case execution and publication remain later independent approvals.

## Preserved v5 milestone

The v5 implementation freeze remains `4d1519f84cd5bac836ea8125ee2d63525ad2578d`; baseline run `cloud-v5-20260820T072055Z-3efe8584` remains at `published/v5/demo.json`, and q1 remains at `published/v5-q1/comparison.json`. V5 and v6 performance are not compared.
