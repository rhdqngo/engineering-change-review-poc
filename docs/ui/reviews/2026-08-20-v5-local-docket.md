# V5 Local Review Docket Audit and Repair

date: 2026-08-20
foundation: provisional 0.1
initial independent verdict: fail (four major findings, no blocker)
repair verdict: conditional pass for exercised local states

## Findings closed

1. A new result request now clears prior rows, evidence, counts, seal, and provenance synchronously. A failed published request leaves the selected case visible but reports `RESULT UNAVAILABLE · EVIDENCE WITHHELD`, zero rows, and `No evidence exposed.`
2. Every rejected final record is rendered in a separate ordered Fail-closed audit list. The exercised DIR-01 unsupported span showed its unique record/stage and never exposed evidence. Duplicate and off-Top-K records use the same record-indexed path and are covered structurally by tests.
3. The narrow candidate table is a named, focusable region with a visible focus ring and explicit Left/Right/Home/End behavior. At 390 × 844, two ArrowRight presses moved the 360/680 px region from scrollLeft 0 to 320 while body overflow remained zero.
4. Catalog loading now checks HTTP status and payload shape. Failure changes the primary action to `Retry catalog`; successful retry replaces options and event handlers instead of duplicating them.
5. Compact candidate and embedding-index fingerprints expose full values through accessible title/name text.

## Browser evidence

- 20 rapid case/source transitions settled on XART-03 with the correct changed source `CONFIG_TABLE_SCHEMA`, published-fixture authority label, six candidates, two verified reviews, and zero blocked records.
- Invalid published-result storage produced a fail-closed error with no stale result surface. Switching back to fixture removed the error and restored the six-row DIR-01 result.
- A one-shot local proxy returned JSON 503 for the first catalog request. The screen showed `simulated transient catalog outage` and `Retry catalog`; one click restored exactly 18 cases, selected DIR-01, six candidate rows, and the normal fixture authority label with no remaining error.
- Desktop and narrow captures were refreshed at `docs/ui/evidence/review-docket-v5-desktop.jpg` and `docs/ui/evidence/review-docket-v5-narrow.jpg`.

## Remaining evidence boundary

The browser did not exercise an off-Top-K/duplicate synthetic result, 200% zoom, or an actual published Vertex v5 run. Those paths remain code/static-test covered or approval-gated and are not claimed as rendered proof. The Foundation remains provisional; validation does not promote it to approved.
