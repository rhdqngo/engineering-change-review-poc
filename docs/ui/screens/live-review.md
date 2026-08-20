# Live Review Screen Contract

state: provisional  
route: `/`  
work size: new-flow  
foundation: provisional 0.2  
primary action: submit one Incoming Artifact for an evidence-grounded engineering review

## Input contract

- Required: artifact type and trimmed text from 1 to 20,000 characters.
- Optional: title up to 200 characters, subsystem up to 120 characters, and at most 20 identifiers of 120 characters each.
- Input is preserved after validation, provider, timeout, and index errors. It is cleared only by explicit `New review`.
- No browser storage is used.

## Required states

- ready
- submitting with duplicate submission disabled
- `REVIEW_REQUIRED`
- `NO_SUPPORTED_REVIEW`, with explicit limited-scope meaning
- `INCONCLUSIVE`
- validation error
- query-embedding, reviewer, or verifier timeout/error
- index unavailable
- concurrent request rejected

## Structure and behavior

- Desktop and narrow use the same order: input, overall disposition, Broad/Expanded/Final scope, ordered Final Top-10 docket, selected verified claim evidence, provenance.
- The primary action reads `Run engineering review · uses Vertex AI`; activation is the per-request billable approval.
- Completion moves focus to the result heading. Failure moves focus to the error summary without clearing the form.
- Candidate selection exposes evidence only for `VERIFIED_REVIEW`; blocked, rejected/missing, and insufficient paths expose only count, stage, and verdict state without unsupported claim text or evidence.
- The docket remains a named horizontally scrollable table at 390 × 844.
- `/evaluation` is a separate destination for the frozen regression benchmark, not an equal mode tab inside this workflow.

## Acceptance

- Empty, oversize, identifier, duplicate-submit, provider/index error, and all three overall states are represented and testable.
- Mouse and keyboard selection work at 1440 × 900 and 390 × 844; rapid candidate switching never mixes source and evidence.
- The page contains no prompt, raw model output, fixture-as-evidence claim, or persistent instructional prose.
