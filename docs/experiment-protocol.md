# Pre-Registered Experiment Protocol

status: frozen-before-results  
frozen: 2026-08-20

## Comparison

Both arms receive the same structured Change Analyst output and the same ordered Hybrid Retrieval Top-6 candidates.

- Baseline: show all six candidates with rank, source ID, score components, and source span.
- Proposed: review those same candidates with the Engineering Review role, require `REVIEW`, `NO_REVIEW`, or `INSUFFICIENT_EVIDENCE`, run deterministic source-ID and exact-span checks, then run the independent Evidence Verifier role. Only verifier-approved results become `VERIFIED_REVIEW`.

No agent may search outside the supplied candidates. Retrieval is a shared tool, not an agent. There are exactly three roles: Change Analyst, Engineering Review, and Evidence Verifier.

## Metrics fixed before results

- Retrieval Coverage: mutation cases whose complete expected target set is present in Top-6 / mutation cases.
- LLM Review Success: retrieval-hit mutation cases whose complete expected target set appears as `VERIFIED_REVIEW` / retrieval-hit mutation cases.
- False Alarm: Clean and Benign cases with one or more final `VERIFIED_REVIEW`, reported as count and rate by type.
- Review Selection Added Value: for each type, candidate count, final verified count, expected-target retention, evidence completeness, and reduction ratio `1 - verified_count / candidate_count`.
- Unsupported Output Blocked: proposed `REVIEW` items rejected by schema, source-ID, exact-span, or verifier checks, reported by stage and type.

Mutation success requires all pre-registered expected targets. Extra verified reviews in mutation cases are retained in raw output and reported, but they do not alter the frozen target. Clean/Benign any verified review is a false alarm.

## Fail-closed rule

A final review is exposed only when all of these hold:

1. decision is `REVIEW`;
2. source ID identifies one of the fixed Top-6 candidates;
3. evidence is a non-empty exact substring of that candidate's source span;
4. short reason is non-empty;
5. independent verifier returns supported.

Any parse failure, missing evidence, unknown source, non-exact evidence, verifier failure, timeout, or provider error becomes rejection/abstention and is never displayed as engineering advice.

## Reproducibility controls

- NASA source files and curated line ranges are hash-locked.
- Case definitions and targets are checksum-locked before the first retrieval/evaluation run.
- Model/provider, model names, temperature, prompts, Top-K, fusion weights, timestamps, and raw role outputs are written to each run artifact.
- Results may be rerun, but the preregistration file is never rewritten from outcomes.
