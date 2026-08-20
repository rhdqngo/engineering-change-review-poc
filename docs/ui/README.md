# UI Documents

This directory stores project-specific UI standards and validation evidence. The template does not precreate an empty Foundation or precedent file. Relevant skills create them only after the actual product and direction are known.

Expected files:

```text
docs/ui/
├── brief.md
├── authority-map.md          # reset/evolution only
├── foundation.md
├── visual-invariants.md
├── render-matrix.md
├── decision-log.md
├── precedents.md
├── state-matrix.md
├── tooling.md
├── tooling.template.md
├── visual-invariants.template.md
├── render-matrix.template.md
├── vertical-slice.md
├── concepts/
├── probes/
├── screens/
└── reviews/
```

Use only `draft`, `provisional`, `approved`, and `superseded` as governance states. `validated` is evidence recorded with the relevant review, command, and rendering conditions, not a state.

If `foundation.md` does not exist or is still `draft`, no authority exists yet for a major new UI flow. Existing UI code does not become precedent automatically.

`visual-invariants.md` records geometry, typography, icon-label composition, text fit, copy, and responsive rules for repeated semantic roles. `render-matrix.md` records actual viewport, content, state, input, and font conditions, plus cross-screen comparison and the explanation-deletion test.

To avoid explanatory UI, persistent copy on operational screens must serve identification, state, constraint, consequence, recovery, or rationale. Remove prose that merely restates structure, or move it into contextual help.
