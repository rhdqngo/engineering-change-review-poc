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
| Withheld audit list | One 44 px minimum action per rejected record; source ID and blocked stage remain visible, and selection always says `No evidence exposed.` |
| Controls | Minimum 38 px height; visible focus ring; stable one-line labels. |
| Change comparison | Changed source, original, and changed content use 12 px monospace with natural wrap; desktop preserves three comparison columns and narrow collapses them in that order with thin separators. |
| Published provenance | Experiment, run, commit, manifest, and embedding-index identity use natural wrap in the footer; fixture mode replaces them with the non-evidence constraint. |

Long source IDs wrap in the evidence title. Candidate rows remain a horizontally scrollable table on narrow screens so rank, source, score, baseline, and proposed retain their column meanings.
The table scroll container has an accessible region name, visible focus ring, and deterministic Left/Right/Home/End keyboard movement. Loading or failed requests never retain a prior seal, evidence, counts, rows, or provenance under a new case/source identity.
