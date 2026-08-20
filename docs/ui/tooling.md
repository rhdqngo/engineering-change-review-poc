# UI Tooling

updated: 2026-08-20

| Purpose | Path |
| --- | --- |
| Local server | `uv run ecr-poc serve --host 127.0.0.1 --port 8080` |
| Liveness | `GET http://127.0.0.1:8080/healthz` |
| Readiness | `GET http://127.0.0.1:8080/readyz` |
| Integrity | `GET http://127.0.0.1:8080/integrity` |
| Live review | `POST http://127.0.0.1:8080/api/reviews` (local default is an explicitly non-LLM fixture; deployed service uses Vertex) |
| Evaluation | `GET http://127.0.0.1:8080/evaluation` |
| Browser automation | Codex in-app Browser plugin through its persistent Node REPL client |
| Desktop viewport | 1440 × 900 |
| Narrow viewport | 390 × 844 |
| Capture | Browser full-page screenshot after a fresh DOM snapshot |
| Private Cloud Run browser | `gcloud run services proxy ecr-poc --project <project-id> --region asia-northeast3 --port 8093`, then open `http://127.0.0.1:8093` |

The three isolated HTML probes were served locally and inspected in the actual in-app browser before selecting the Docket direction. Production captures and interaction results are recorded in `render-matrix.md` after implementation validation. The same browser workflow was repeated against the authenticated Cloud Run proxy. For v5, the explicitly approved verifier has service-level run.invoker, no public binding exists, and final direct unauthenticated verification returned 403. The verification script accepts a 403 or 404 denial during Cloud Run IAM propagation. The proxy exposes the application liveness alias at `/health`; `/readyz` and `/integrity` remain the data-bearing checks.

The v5 local repair recheck used `http://127.0.0.1:8148` for the active fixture/published snapshot and an isolated invalid-result-store process on port 8149 for the fail-closed published-error/recovery path. Final Cloud verification used the private proxy on port 8093; the temporary 390 × 844 override was reset after published baseline validation.

The v6 local flow uses the immutable `.cache/v6-freeze` corpus and deterministic local query/index pair. That path verifies interaction and fail-closed behavior only; it is never presented as Vertex evaluation evidence. Live input is not written to browser storage.

Purpose-driven v6 browser verification used temporary ports 8081 (no-supported-review), 8082 (review-required fixture), 8083 (inconclusive fixture), and 8084 (index-unavailable recovery). At 1440 × 900 and 390 × 844 it checked long input, result/error focus, supported-claim-only evidence, Broad/Expanded/Final scope, one pressed candidate, body/table overflow, a single-line billable action, 20-case Evaluation loading, five rapid case changes, and keyboard Home/ArrowRight docket scrolling. The temporary viewport override was reset after the run.
