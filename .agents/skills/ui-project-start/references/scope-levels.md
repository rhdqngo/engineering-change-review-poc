# Documentation Scope Levels

Choose by decision cost and expected duration, not project size alone.

## Lite

Appropriate for:

- personal experiments or short prototypes
- one to three core screens
- one platform and input method
- no conflict over existing UI authority

Minimum documents:

- `brief.md`
- `concepts/overview.md` — all three directions may share one file
- `foundation.md`
- `vertical-slice.md`
- one representative `screens/*.md`
- `tooling.md`

## Standard

Appropriate for:

- normal products intended for continued operation
- multiple screens and states
- responsive behavior or more than one input method
- continued work across a team or many sessions

Additional documents:

- separate concept files
- `decision-log.md`
- `precedents.md`
- `state-matrix.md`
- review records
- `authority-map.md` for reset or evolution

## Extended

Appropriate for:

- multiple platforms or teams
- high-stakes areas such as payment, medical, permissions, or competitive fairness
- large redesigns with staged migration
- strict accessibility, regulatory, or approval tracking

Additional material:

- detailed per-screen contracts and traceability
- migration stages and expiration conditions
- user-test and analytics evidence
- accessibility and platform-specific approval records

Document count is not the goal. Write enough that another session can reproduce the decision and an accidental prototype cannot spread as authority.
