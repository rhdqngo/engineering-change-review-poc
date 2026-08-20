# V6 Purpose-driven Engineering Impact Review Protocol

status: pre-freeze local functional gate  
project: `iceu-687`  
region: `asia-northeast3`

## Purpose and authority

When a new engineering artifact arrives, the system discovers unchanged NASA cFS baseline artifacts that a Human Engineer should re-review and exposes only independently supported atomic impact claims with exact source evidence. The system does not approve or reject a change, edit the baseline, or guarantee that an artifact has no impact.

## Frozen inputs and identity

- Experiment: `ecr-poc-regression-v6`
- Manifest: `data/experiments/ecr-poc-v6.json`
- Design tag: `ecr-poc-v6-design-freeze`
- Implementation tag after the final gate: `ecr-poc-v6-freeze`
- GCS input: `frozen/ecr-poc-v6`
- Runs: `runs/v6`
- Published pointer: `published/v6/demo.json`
- Benchmark: Direct 5, Semantic 5, Cross-Artifact 5, Clean 2, Benign 3

The manifest pins the normative requirements document and SHA-256, design commit/tag, official root commit, recursive submodule URL/SHA values, included file hashes, exclusions/licenses, normalized chunk package, byte-preserving selected-source archive, prompt hashes, document-vector index, and identifier index. The final implementation freeze additionally records immutable GCS generations.

## Deterministic retrieval contract

```text
Incoming Artifact
→ deterministic Query Processor
→ 50/50 BM25+dense Broad Top-40
→ typed exact-identifier 1-hop expansion
→ expanded pool, maximum 200
→ 0.75 hybrid + 0.25 relation ranking
→ Final Review Docket Top-10
```

Incoming text is authoritative query data and is never inserted into the corpus, identifier index, or document-vector matrix. The Query Processor invokes no LLM and invents no old value, dependency, or baseline relation. Broad, expanded, and Final sequences each receive a deterministic fingerprint.

The identifier index contains typed C/C++ symbols, functions, types, macros, MIDs, command codes, tables, EDS/XML names, and explicit test targets. Expansion uses exact case-sensitive identifiers with document frequency 2–50, at most eight seeds per Broad candidate, no recursive expansion, and immutable ordered postings.

## AI and fail-closed boundary

Google ADK contains exactly two `LlmAgent` roles: Engineering Reviewer and Evidence Verifier. The Reviewer returns exactly one decision for every Final Docket candidate. A `REVIEW` contains one to three atomic claims; the request maximum is 20. Claim IDs are assigned by the server from Final rank and claim ordinal.

Before verification, a deterministic validator checks Final Docket membership, frozen source identity, decision cardinality, impact type, absolute line range, contiguous exact quote, schema, and claim limits. Invalid claims never reach the verifier. The verifier receives valid claims once in fixed order and returns only `SUPPORTED`, `REJECTED`, or `MISSING`. Unsupported claim text and evidence are never exposed by the Live API or UI.

Candidate status is one of `VERIFIED_REVIEW`, `NO_REVIEW`, `NO_SUPPORTED_CLAIM`, `INSUFFICIENT_EVIDENCE`, or `BLOCKED`. Overall status is:

- `REVIEW_REQUIRED`: at least one supported claim; `partial: true` if another path is inconclusive.
- `NO_SUPPORTED_REVIEW`: every Final Docket candidate terminated normally and no supported claim exists. This is not a full-baseline no-impact guarantee.
- `INCONCLUSIVE`: no supported claim exists and at least one result is blocked, missing, insufficient, or provider-failed.

## Live request boundary

`POST /api/reviews` accepts one strict Incoming Artifact. One process admits one request at a time. Validation returns 422, concurrent execution 429, index unavailability 503, and query embedding failure 502/504. Reviewer or verifier failure returns HTTP 200 `INCONCLUSIVE` and exposes no unsupported evidence. Live input, prompts, raw model output, and responses are not persisted to GCS, application logs, or browser storage.

## Frozen regression benchmark

The 20 cases were observed during development and are a frozen regression/diagnostic benchmark, not an unseen performance evaluation. Each impact case freezes atomic claim slots containing source ID, impact type, and acceptable exact evidence spans. Expected targets are derived from claim slots.

Metrics are reported overall and by case type: Broad Hit@40, relation expansion gain, expanded target coverage, Final Hit@10 and complete coverage, target rank/MRR, expected claim proposal recall, verified expected claim recall, claim/evidence counts, candidate reduction, Clean/Benign false alarm, and unregistered additional findings. Gold-external impact findings are reported separately and are not automatically labeled false positives; automatic Claim Precision is not claimed. Accuracy thresholds are not completion conditions, and v5/v6 performance is not compared.

## Approval sequence

1. Completed: approved `gemini-embedding-001` document generation, 768-dimensional index validation, and byte-identical cache-only rebuild.
2. Completed: separately approved five-object immutable GCS upload, byte-identical existing-object verification, and generation/SHA manifest seal.
3. Completed locally: full freeze gate and implementation commit/tag without moving the design tag.
4. Separately approve push, private Cloud Run/Job deployment, the 20-case Vertex Job, and publish.
5. Publish only after 20 terminal cases, provenance/index seals, metrics, fail-closed checks, logs, IAM, and browser behavior validate.

Failures and checkpoints remain immutable under a new run ID. V1-v5 tags, results, GCS generations, and published pointers are never changed.
