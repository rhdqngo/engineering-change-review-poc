# Published v2 Review Docket UI Review

date: 2026-08-20  
reviewer: independent `ui_auditor`  
verdict: PASS WITH MINOR FINDINGS  
foundation: provisional

## Scope and evidence

- Actual private Cloud Run UI through the authenticated local proxy
- Published run `cloud-v2-20260820T035505Z-56ad91df`, source commit `10c59bf`
- Chrome at 1440 × 900 and 390 × 844
- Mouse/select and Enter candidate activation
- Direct comparison with `/health` and `/api/evaluation`
- Representative DIR-01, SEM-02, XART-04, CLN-01, and BEN-02 cases
- Console warning/error count: 0

## Closed findings from the prior audit

| Finding | Final evidence |
| --- | --- |
| Ambiguous run ID and `legacy freeze` | Environment retains unique timestamp/suffix, accessible title contains the full run, and footer names v2, full run, and commit. |
| Misleading `Run case` action | Control is `Reload result`. |
| Small source target / row pointer mismatch | Source buttons are 43.59 px high at both viewports; row cursor is auto and only the button uses pointer. |
| Enabled action during initial load | Server HTML ships `Reload result` disabled and enables it after load. |
| Missing selection semantics | Exactly one source has `aria-pressed=true`; all control `evidence-desk`; the desk is an `aria-live=polite` region. |
| Narrow-layout uncertainty | At 390 px there is no body overflow; only the 345/680 px docket object scrolls horizontally. |
| Result/provenance mismatch risk | Five representative case counts, seals, and ordered Top-6 lists match the raw published API. |

## Gate assessment

- Pass: task fit, Foundation conformance, hierarchy, responsive adaptation, accessibility structure, semantic consistency, perceptual comfort, narrative restraint, and generic-AI-drift avoidance.
- Pass with minor findings: loading-copy consistency and durable validation-record completeness.
- Unverified: live GCS 503 recovery transition in a browser, physical screen-reader announcement quality, physical touch gesture, 200% zoom, and localization.
- Not applicable: billable execution controls, mutation forms, modal/upload workflows, motion, and audio.

## Minor findings

1. The cold-start Evidence desk still briefly says `Run a case to inspect its review disposition.`, although the read-only control is now `Reload result`. This does not affect result integrity or ordinary loaded-state use. Changing deployed code would require a new frozen experiment image, so it is retained as a documented wording follow-up rather than modifying the accepted run.
2. The final v2 render evidence was absent from the matrix at review time. This report and the final Cloud v2 matrix row close that documentation gap.

No blocker or major finding remains. This review does not promote the provisional UI Foundation to approved.
