# Published v3 Review Docket UI Review

**Date**: 2026-08-20  
**Mode**: review-only  
**Verdict**: fail

## Scope

- Actual private Cloud Run revision `ecr-poc-00006-6jz` through the authenticated local proxy
- Published run `cloud-v3-20260820T043842Z-6e260831`, source commit `3984e779`
- 1440 × 900 and 390 × 844, mouse/select, keyboard Enter, rapid source switching
- Cold start, published/fixture transitions, five representative case types, provenance, evidence exposure, and raw API comparison

## Evidence summary

The requested wording repair passed: cold start displayed `Loading review disposition…`, and `Reload result` was disabled until initial data resolved. Published v3 provenance and representative DIR-01, SEM-02, XART-04, CLN-01, and BEN-02 values matched the raw API, and rejected evidence was not exposed.

The overall review fails because three independently reproduced interaction/responsive defects are major. Git status was checked before and after the read-only audit; the auditor made no edits. This result does not promote the provisional Foundation.

## Gate results

| Gate | Result | Evidence / reason |
| --- | --- | --- |
| Task fit | fail | The selected source and displayed result can disagree during a race. |
| Foundation conformance | fail | Provenance and source control can contradict each other. |
| Information architecture | pass | Case, candidates, disposition, and evidence retain the intended scan order. |
| State and recovery | fail | A stale response can overwrite a newer source selection. |
| Input and adaptation | fail | Reload wraps at 390 px and keyboard focus is not restored after reload. |
| Accessibility and clarity | fail | Focus moves to `BODY` after a keyboard reload and does not return. |
| Implementation consistency | fail | Async result requests lack sequencing/cancellation. |
| Perceptual comfort / cross-screen consistency | fail | The primary control becomes an accidental two-line control at the supported narrow viewport. |
| Narrative restraint / copy necessity | pass | The previous instructional loading-copy finding is closed with state-only language. |
| Generic-pattern drift | pass | No unjustified dashboard/card/explanatory pattern was introduced. |
| Evidence completeness | fail | The earlier pass record omitted rapid source switching, reload focus, and narrow wrapping. |

## Findings

### major — stale response can replace the selected result source

- Location / condition: quickly switch Published → Fixture while result requests overlap.
- Observed: the dropdown shows Fixture while environment, footer, counts, and result content revert to Published v3; reproduced twice.
- Impact: provenance and evidence can describe a source the user did not select.
- Applicable rule: state consistency and stale-result recovery.
- Evidence: deployed interaction and `app.js` `runCase()` have no request sequence or cancellation guard.
- Smallest correction: cancel the prior fetch and accept/render only the latest request sequence.
- Revalidation: force overlapping transitions in both directions and compare dropdown, provenance, counts, and API identity.

### major — Reload result wraps at the supported narrow viewport

- Location / condition: 390 × 844.
- Observed: `Reload result` wraps to two lines and grows to 44 px.
- Impact: the primary control violates its stable one-line role and changes the header rhythm.
- Applicable rule: visual invariant `Controls — stable one-line labels` and responsive-input contract.
- Evidence: actual narrow rendering.
- Smallest correction: enforce one-line text and preserve the narrow grid allocation.
- Revalidation: measure the button at 390 × 844 and confirm one line without body overflow.

### major — keyboard focus is lost after reload

- Location / condition: focus Reload, activate with Enter, wait for disabled → enabled transition.
- Observed: focus moves to `BODY` when the control is disabled and is not restored.
- Impact: keyboard users lose place after the primary action.
- Applicable rule: predictable focus and recovery after async state changes.
- Evidence: deployed keyboard interaction.
- Smallest correction: remember whether Reload initiated the request and restore focus after the latest request re-enables it.
- Revalidation: Enter reload, confirm focus returns to Reload; confirm dropdown-initiated loads retain dropdown focus.

## Closed prior finding

The v2 minor loading-copy finding is closed. The actual v3 cold start shows `Loading review disposition…` with disabled `Reload result`.

## Fixes performed

None — review-only. The immutable v3 experiment remains published; corrections require a distinct later freeze rather than moving `ecr-poc-v3-freeze`.

## Approval decision

- Candidate: no
- Explicit approval requested: no
- Status changed: no
- Foundation remains provisional

## Next action

Create a separately versioned freeze that fixes request sequencing, narrow one-line control geometry, and focus restoration; redeploy, rerun, republish, and repeat this audit.
