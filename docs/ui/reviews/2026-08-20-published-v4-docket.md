# Published v4 Review Docket UI Review

**Date**: 2026-08-20  
**Mode**: review-only  
**Verdict**: pass

## Scope

- Actual private Cloud Run revision `ecr-poc-00007-xvc` through the authenticated proxy
- Published run `cloud-v4-20260820T050914Z-92f72d97`, freeze `ecr-poc-v4-freeze`, source `7b76bfaa`
- 1440 × 900 and 390 × 844; mouse/select, keyboard Enter, CUA table scroll
- Cold start, rapid source/case transitions, reload lifecycle/focus, published/fixture results, provenance, ARIA, and console

## Evidence

The audit made no product or document edits. Cold start was captured twice with `LOCAL DEMO · LOADING`, `Loading review disposition…`, zero case options, and disabled Reload, followed by 18 ready cases and fixture provenance. Published UI identity matched the v4 API and full run title/footer.

| Scenario | Evidence | Result |
| --- | --- | --- |
| Rapid request ordering | 16 source-only plus 12 mixed source/case transitions; control, metadata, title, provenance, seal mismatches 0/28 | pass |
| Reload keyboard lifecycle | Enter → disabled/busy → enabled; focus restored to `run-button` with 2 px amber outline | pass |
| Native control focus | source and case selects retain focus after their latest request completes | pass |
| Narrow rendering | Reload 126 × 38 px, 99.95 × 21 px single-line text, nowrap, body overflow 0 | pass |
| Docket scroll | 345 px client / 680 px scroll; horizontal movement confined to the table | pass |
| Wide rendering | 1440 × 900, stable 883.5/541.5 px docket/evidence split, body overflow 0 | pass |
| Representative raw match | DIR-01 2/0, SEM-02 3/0, XART-04 1/0, CLN-01 0/0, BEN-02 1/0; ordered Top-6 and seals match API | pass |
| Fail-closed fixture | rejected source shows `No evidence exposed.`, span/verifier `—`, and `deterministic_exact_span` only | pass |
| ARIA / console | one `aria-pressed`, all `aria-controls`, live region, Enter activation; warnings/errors 0 | pass |

## Gate results

| Gate | Result | Evidence / reason |
| --- | --- | --- |
| Task fit | pass | Frozen result review and provenance remain the core task. |
| Foundation conformance | pass | Docket structure, surfaces, and fail-closed expression follow the provisional Foundation. |
| Information architecture | pass | Provenance → case → candidates → evidence order is stable. |
| State and recovery | pass | Cold loading/disabled/ready and latest-request-only behavior verified; API 503 path is covered by tests. |
| Input and adaptation | pass | Keyboard, mouse/select, 1440/390, and table-local touch-style scroll verified. |
| Accessibility and clarity | pass | Labels, alert/live region, selection semantics, and visible focus pass. |
| Implementation consistency | pass | 38 px control invariant and semantic table/button/select roles are consistent. |
| Perceptual comfort / cross-screen consistency | pass | Wide/narrow hierarchy is stable with no accidental wrapping. |
| Narrative restraint / copy necessity | pass | Persistent text is limited to identity, state, provenance, and fail-closed consequence. |
| Generic-pattern drift | pass | The engineering docket does not regress into chat, copilot, or card-grid defaults. |
| Evidence completeness | pass | Actual deployment, cold state, 28 races, five raw comparisons, two viewports, keyboard/ARIA, and console were checked. |

## Closed findings

- V3 stale-response mismatch: closed by AbortController, request sequence, and latest-request-only state updates.
- V3 390 px Reload wrapping: closed by the 126 px one-line control invariant.
- V3 reload focus loss: closed by latest-request focus ownership and restoration.
- V2 instructional loading copy: closed by state-only loading text and disabled Reload.

## Findings

No blocker, major, or minor finding.

## Notes / unverified

1. DOM semantics and the live region pass, but NVDA/VoiceOver speech order was not physically exercised.
2. Production GCS permissions/pointer were not deliberately broken to render a live 503; the alert/retry implementation and fail-closed API tests cover this path. A staging fault injection can add rendered evidence later.

## Fixes performed

None — review-only.

## Approval decision

- Candidate: yes for the reviewed v4 scope
- Explicit approval requested: no
- Status changed: no
- Foundation remains `provisional`; validation does not automatically promote it

## Next action

No UI blocker remains. Preserve this review with the final v4 evidence commit.
