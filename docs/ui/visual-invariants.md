# Visual Invariants

state: provisional  
updated: 2026-08-20

| Role | Invariant |
| --- | --- |
| Environment provenance | 7 px vertical padding, amber strip, 11 px uppercase monospace; published source, provider, model, short run ID, and optional short commit remain one explicit provenance sequence. |
| Candidate row | 16 px vertical padding, single bottom rule, source ID plus one muted title line. |
| Disposition | 11 px uppercase monospace; text label always present. |
| Evidence | Exact span, 12 px monospace, dark surface, preserves wrapping and whitespace. |
| Verification gate | Label/value pair with a stable bottom rule; supported state explicitly says PASS or SUPPORTED. |
| Rejection | Rust color and “Fail-closed record”; never labeled as final advice. |
| Controls | Minimum 38 px height; visible focus ring; stable one-line labels. |

Long source IDs wrap in the evidence title. Candidate rows remain a horizontally scrollable table on narrow screens so rank, source, score, baseline, and proposed retain their column meanings.
