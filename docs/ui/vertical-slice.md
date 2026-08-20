# Representative Vertical Slice

state: provisional  
updated: 2026-08-20

The slice is the single case docket at `/`, backed by `/api/cases` and `/api/cases/{id}/result`.

Required representative cases:

- `CLN-01`: clean baseline, no verified finding.
- `DIR-01`: explicit function-code change and an intentionally unsupported fixture proposal that must be blocked.
- `CLN-02`: restore to the frozen baseline.
- `SEM-01`: semantic counter-reset effect.
- `XART-03`: cross-artifact validation and verification impact.

Acceptance requires identical baseline/proposed candidate IDs, selectable rows, exact evidence display only for verified output, visible blocked stage, API error handling, and browser validation at desktop and narrow viewports.
