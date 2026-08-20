# Render Matrix

updated: 2026-08-20

| Surface | Viewport | Content / state | Input | Build | Render | Interaction | Comfort | Narrative restraint |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Concept probes | default desktop | Identical synthetic DIR-01 | browser snapshot | n/a | passed | n/a | Docket selected | passed; probe banner prevents result confusion |
| Production docket | 1440 × 900 | DIR-01 exact evidence and blocked proposal; CLN-01/02, SEM-01, XART-03 transitions | mouse + Enter on Run | passed | passed; capture `evidence/review-docket-desktop.png` | passed; stable seals and counts | passed; fixed split remains readable | passed; fixture provenance and rejection consequence only |
| Production docket | 390 × 844 | DIR-01 with long IDs and evidence | touch-sized controls + keyboard-compatible native controls | passed | passed; capture `evidence/review-docket-narrow.png` | passed; table scroll preserves column semantics | passed with horizontal docket scroll | passed |
| Saved actual result | 1440 × 900 | Vertex DIR-02 plus transitions through SEM-01, XART-03, CLN-01, CLN-02 | mouse/select | passed | passed; capture `evidence/review-docket-actual-vertex.png` | passed; actual provider/model label and raw seals matched | passed | passed; actual and fixture provenance remain distinct |
| Private Cloud Run docket | browser default | Revision `ecr-poc-00002-v9g`; Vertex DIR-02, XART-03, CLN-01, CLN-02 plus fixture rejected span | mouse/select through authenticated proxy | passed in Cloud Build | passed; capture `evidence/review-docket-cloud-run.png` | passed; actual counts/seals, hidden rejected evidence, and 403 boundary verified | passed | passed; frozen Vertex and fixture provenance remain distinct |
| V2 published-result repair | browser default 1280 × 720 | Local published v1 compatibility plus fixture rejection; GCS-unavailable error is API-tested | mouse/select/candidate activation | passed locally | passed in fresh in-app browser review | published/fixture selection passed; rejected evidence remained hidden | passed at default viewport; prior narrow contract unchanged, fresh narrow override unavailable | passed; provenance stays in existing environment/footer roles |
| Final private Cloud v2 | 1440 × 900 and 390 × 844 | Revision `ecr-poc-00005-485`; run `cloud-v2-20260820T035505Z-56ad91df`; DIR-01, SEM-02, XART-04, CLN-01, BEN-02 | mouse/select, Enter candidate activation, responsive measurement | passed in Cloud Build | passed in actual deployed Chrome; console warning/error 0 | counts, seals and Top-6 match raw API; one `aria-pressed`; 43.59 px source target; desk live region | passed; only docket owns 345/680 px horizontal overflow at 390 px | passed; full run/v2 freeze/commit provenance without instructional prose |
| Private Cloud v3 audit | 1440 × 900 and 390 × 844 | Revision `ecr-poc-00006-6jz`; cold start then run `cloud-v3-20260820T043842Z-6e260831`; rapid Published/Fixture switching | mouse/select, keyboard Enter, responsive measurement | passed in Cloud Build | failed overall; cold-start wording passed but Reload wrapped at 390 px | failed; stale response overwrote newer selection and focus fell to BODY after Reload | failed; accidental two-line primary control at 390 px | passed; loading text is state-only and prior instructional-copy finding is closed |

Browser evidence: CLN-02 showed 0 verified/0 blocked; SEM-01 showed 1/0; XART-03 showed 2/0; DIR-01 showed 1/1. Selecting the rejected DIR-01 candidate displayed `No evidence exposed.` and only the deterministic blocking stage.

After the actual run, saved-result mode showed DIR-02 4/0, SEM-01 1/0, XART-03 2/0, CLN-01 0/0, and CLN-02 2/0 (verified/blocked). The last row is an actual control false alarm, not a UI fixture.

The deployed revision showed `SAVED EVALUATION · vertex-adk · gemini-3.5-flash` and matched DIR-02 4/0, XART-03 2/0, CLN-01 0/0, and CLN-02 2/0. Its fixture rejection exposed no evidence and identified `deterministic_exact_span` as the blocking stage.

Explanation-deletion rule: the persistent footer keeps only the non-obvious fixture provenance constraint. Visible labels identify objects, state, verification, or rejection consequences; no paragraph narrates the page structure.

The v2 repair review confirmed that legacy v1 case UUIDs are not presented as the published run identity: the environment and footer use the published-result metadata run ID (`c31aabbe-91a…`). The available in-app browser ignored its temporary 390 × 844 viewport override, so fresh narrow rendering is explicitly unverified; the previously captured narrow contract remains the current evidence.

The final deployed v2 re-audit supersedes that viewport limitation: 1440 × 900 and 390 × 844 both rendered the published run `cloud-v2-20260820T035505Z-56ad91df` with commit `10c59bf`. The full run ID is available in the accessible environment title and footer, the compact visible form keeps its timestamp and suffix, and the footer names `ecr-poc-preregistered-v2`. Body-wide overflow was absent; horizontal scrolling was confined to the docket table.

The deployed v3 audit closes the v2 loading-copy exception: cold start displays `Loading review disposition…` while `Reload result` is disabled. It also found three major defects requiring a later freeze: an overlapping-request stale response, a two-line Reload control at 390 px, and lost keyboard focus after Reload. Representative result values and provenance still matched the published API when requests were allowed to settle.
