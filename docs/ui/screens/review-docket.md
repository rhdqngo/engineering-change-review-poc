# Frozen Regression Docket Screen Contract

state: provisional
route: `/evaluation`
primary action: inspect one frozen Incoming Artifact case and its supported atomic claims

## UI profile

- Core goal: inspect the published outcome of any of the 20 frozen regression cases, then trace a supported claim to an exact baseline span.
- Primary mode: monitor-analyze. Secondary mode: browse-compare.
- Audience and consequence: engineering reviewer; an unsupported recommendation must remain hidden.
- Viewports and input: 1440 × 900 and 390 × 844; mouse, touch, and keyboard.
- Critical information: result authority, experiment/run provenance, Incoming Artifact identity, Broad/Expanded/Final retrieval scope, Final Docket status, supported claim, exact evidence, verifier outcome, and blocked stage.

## Required states

- loading with Reload disabled
- `REVIEW_REQUIRED` with supported atomic claims
- `NO_SUPPORTED_REVIEW`
- `INCONCLUSIVE`, partial, and blocked outcomes
- Clean/Benign case with zero supported findings
- published GCS result unavailable or invalid, with retry and no Cloud-side local fallback
- rapid case/candidate switching in which only the latest request owns the screen

## Structure and behavior

- Display exactly 20 frozen regression Incoming Artifact cases and their published v6 results. Never present them as unseen or preregistered performance evidence.
- Show artifact type, title/subsystem when present, identifiers, and a bounded Incoming Artifact summary. Do not show mutation original/changed fields or Change Analyst output.
- Show immutable Broad Top-40, expanded-pool, and Final Top-10 counts and fingerprints.
- The Final Docket is the only horizontally scrolling region on narrow screens. It is named, focusable, and supports ArrowLeft/ArrowRight/Home/End scrolling.
- Selecting a candidate displays only its supported atomic claims and exact evidence. Rejected or missing claim text/evidence remains hidden; only blocked count, stage, and verdict may appear.
- Provenance distinguishes deterministic fixture evidence from a published run and shows experiment, run, commit, manifest, embedding index, and identifier index identities when available.
- Loading and result failure clear stale candidate, evidence, counts, fingerprints, and provenance before a new selection can be interpreted as owning them.
- `Reload result` remains a single-line control at 390 × 844. If it owned keyboard focus when the latest request began, focus returns when it is re-enabled.
- Catalog failure changes Reload to `Retry catalog`; retry replaces options and handlers without duplication.
- Live billable review remains at `/`. The evaluation route never invokes Vertex, edits a change, approves a change, or displays prompts.

## Copy inventory

| Text / region | Role | Default visibility | Decision |
| --- | --- | --- | --- |
| Frozen regression benchmark | identity/constraint | persistent | keep |
| Fixture or published authority | identity | persistent | keep |
| Broad / Expanded / Final scope | state | persistent | keep |
| `NO_SUPPORTED_REVIEW` limitation | constraint | contextual | keep |
| Partial / blocked summary | state/risk | contextual | keep |
| Exact supported evidence and verifier verdict | decision data | contextual | keep |
| Loading / API error / recovery text | state/recovery | contextual | keep |
| Page-operating instructions | none | hidden | remove |

## Acceptance

- Technical: API/UI tests, Ruff, mypy, package build, and five PowerShell scripts pass.
- Render: desktop and narrow loading/error/recovery/review-required/no-supported/inconclusive/partial states are reviewed at normal scale.
- Interaction: keyboard Reload restoration, candidate activation, table scrolling, rapid case/candidate switching, and error recovery pass.
- Safety: no rejected or missing claim content/evidence appears in the UI, logs, or public Live response.
- Governance: Foundation and this screen remain provisional until explicit user approval.
