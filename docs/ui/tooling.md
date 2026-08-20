# UI Tooling

updated: 2026-08-20

| Purpose | Path |
| --- | --- |
| Local server | `uv run ecr-poc serve --host 127.0.0.1 --port 8080` |
| Health | `GET http://127.0.0.1:8080/health` |
| Browser automation | Codex in-app Browser plugin through its persistent Node REPL client |
| Desktop viewport | 1440 × 900 |
| Narrow viewport | 390 × 844 |
| Capture | Browser full-page screenshot after a fresh DOM snapshot |
| Private Cloud Run browser | `gcloud run services proxy ecr-poc --project <project-id> --region asia-northeast3 --port 8093`, then open `http://127.0.0.1:8093` |

The three isolated HTML probes were served locally and inspected in the actual in-app browser before selecting the Docket direction. Production captures and interaction results are recorded in `render-matrix.md` after implementation validation. The same browser workflow was repeated against the authenticated Cloud Run proxy; direct unauthenticated access was checked separately and returned 403.
