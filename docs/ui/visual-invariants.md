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
| Incoming artifact summary | Artifact type, title/subsystem, and incoming text use 12 px monospace with natural wrap; evaluation desktop preserves three columns and narrow collapses them in that order. |
| Live input | Artifact type and text are always visible; optional context is progressive; the billable action explicitly says `uses Vertex AI`; failed requests preserve input. |
| Live result order | Desktop and narrow retain input → disposition → retrieval scope → horizontally scrollable Final Top-10 docket → verified claim evidence; narrow never converts candidates into cards. |
| Published provenance | Experiment, run, commit, manifest, and embedding-index identity use natural wrap in the footer; fixture mode replaces them with the non-evidence constraint. |

Long source IDs wrap in the evidence title. Candidate rows remain a horizontally scrollable table on narrow screens so rank, source, type, score, and disposition retain their column meanings.
The table scroll container has an accessible region name, visible focus ring, and deterministic Left/Right/Home/End keyboard movement. Loading or failed requests never retain a prior seal, evidence, counts, rows, or provenance under a new case/source identity.
