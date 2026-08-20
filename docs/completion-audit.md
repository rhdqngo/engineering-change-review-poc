# Completion Audit

updated: 2026-08-20

| # | Requirement | Status | Authoritative evidence |
| --- | --- | --- | --- |
| 1 | Operational install/run/test project | proven | `AGENTS.md`, `README.md`; frozen sync, 13 tests, Ruff, mypy, build, health executed. |
| 2 | One sourced NASA subset and clean baseline | proven | `data/nasa/provenance.json`, `docs/data-selection.md`; source hashes validated. |
| 3 | Pre-result 4/4/4/3/3 cases and targets | proven | `data/cases/cases.json`, `freeze.json`, `docs/experiment-protocol.md`; hashes predate model result. |
| 4 | Same analyst output and same Top-K arms | proven | One structured change drives one candidate object per case; all 18 raw arm ID lists and seals match. |
| 5 | Exactly three roles plus shared retrieval tool | proven | `tests/test_agents.py`; three `LlmAgent` constructors, no coordinator/workflow agent; ADK `FunctionTool` wraps retrieval. |
| 6 | Exact span, source ID, reason, independent verifier, fail-closed | proven | 29 actual findings passed exact candidate substring and verifier checks; rejected final evidence is null; failure-path tests pass. |
| 7 | Type-level metrics and raw artifact | proven | `results/runs/vertex-adk.json`, checkpoint, fixture artifact, `metrics.py`, documented command. |
| 8 | Demo UI and browser evidence | proven | desktop/narrow/actual/local and deployed Cloud Run captures plus browser interaction records in `docs/ui/render-matrix.md`. |
| 9 | Build/test/normal/error/rejection and actual report | proven | 13 tests, package build, health, browser, `docs/results/experiment-report.md`. |
| 10 | GCP config and approved deployment verification | proven | Private revision `ecr-poc-00002-v9g` serves 100%; authenticated health/catalog, actual browser flow, fail-closed rejection, unauthenticated 403, and Cloud Logging paths passed. See `docs/results/deployment-log.md`. |
| 11 | Respect non-goals; no automatic commit/push/deploy | proven | Git remains uncommitted/unpushed; the only external deployment and minimal IAM changes were performed after exact user approval; no scope expansion occurred. |

All eleven completion requirements have direct repository, raw-result, test, browser, or deployed-runtime evidence.
