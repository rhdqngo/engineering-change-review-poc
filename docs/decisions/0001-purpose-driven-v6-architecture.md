# Decision 0001 — Purpose-driven v6 architecture

status: accepted

date: 2026-08-20

design tag: `ecr-poc-v6-design-freeze`

## Decision

The product is an evidence-grounded Engineering Change Impact Review Copilot. It discovers which immutable NASA cFS baseline artifacts warrant human re-review after an Incoming Artifact and exposes only independently supported atomic impact claims.

The unfinished v6 is redesigned in place. It uses a deterministic Query Processor, Broad Hybrid Top-40, typed identifier 1-hop expansion, deterministic Final Top-10 ranking, one Engineering Reviewer Agent, deterministic evidence validation, and one independent Evidence Verifier Agent.

The existing 20 cases are a frozen regression/diagnostic benchmark, not an unseen preregistered performance evaluation. Accuracy thresholds are not completion gates.

## Consequences

- Change Analyst is removed as an Agent and provider dependency.
- Two ADK `LlmAgent` roles remain: Engineering Reviewer and Evidence Verifier.
- Identifier relations are an immutable inverted index, not a Knowledge Graph.
- Final advice is claim-level and requires Final Docket membership, exact evidence and `SUPPORTED` verification.
- `NO_SUPPORTED_REVIEW` is scoped to the evaluated docket and never means no baseline impact.
- v1~v5 remain historical and immutable; no official legacy v6 result exists to preserve.

## Frozen parameters

- Broad Hybrid Retrieval: 40, BM25/dense 50/50
- Eligible identifier document frequency: 2–50
- Expansion: direct 1-hop, max 8 identifiers per broad candidate
- Expanded pool: max 200, including the retained Broad Top-40
- Final score: 75% hybrid relevance + 25% relation score
- Final Review Docket: 10
- Reviewer claims: max 3 per candidate and 20 per request

Changing this decision requires a new design-freeze revision. The existing design tag must not move.
