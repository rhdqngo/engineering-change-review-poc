# UI Governance Status

UI Foundations, screen contracts, and precedents use only these four states:

```text
draft → provisional → approved → superseded
```

## draft

- A candidate or exploratory document.
- Not authoritative for later screens.
- May be linked to implementation probes, but is not a production standard.

## provisional

- A direction has been selected and may be used as an implementation baseline.
- The representative vertical slice and review may be in progress or complete.
- Do not promote it to `approved` before explicit user or team approval.

## approved

- The user or team has explicitly approved a defined scope.
- Do not extend approval automatically to details outside that scope.
- Record the approval rationale, date, and related review.

## superseded

- Replaced by a newer standard.
- Retain only as historical context for existing screens and migrations.
- Do not reuse it in new work.

## Validation is evidence, not status

Do not use `validated` as a governance state. Record validation separately:

```yaml
status: provisional
validation:
  result: pass | fail | unverified
  review: docs/ui/reviews/2026-08-07-inventory.md
  commit: abc1234
  conditions:
    - 390x844 touch
    - 1440x900 mouse-keyboard
```

A `pass` result does not automatically make the artifact `approved`.

## Approval transaction

A `provisional → approved` transition is an atomic operation that aligns all of the following, not a one-field edit in one document:

1. Record exactly what the user approved and the scope of that approval.
2. Update status, version, and approval date in the Foundation or screen contract.
3. Record rationale, alternatives, and revisit conditions in `decision-log.md`.
4. Align approved role-level geometry, text fit, icons, rhythm, and copy scope in `visual-invariants.md`.
5. Link the actual viewport, content, state, input, font, and copy conditions in `render-matrix.md`.
6. Record the reusable aspects and explicit non-use boundaries in `precedents.md`.
7. Link the relevant review, commit, and validation conditions.
8. Confirm that target names, versions, and scopes match across every file.

Read the original files first, prepare the entire change in memory, and review the diff before applying it. If anything is missing or conflicting, do not leave any document in `approved`. If a partial update occurs, restore the prior state immediately or mark a blocker and retain `provisional`.

Treat `approved → superseded` the same way: record the new active Foundation and the replacement relationship in the decision log and precedents as one change unit.
