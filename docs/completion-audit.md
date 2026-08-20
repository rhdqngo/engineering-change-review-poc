# Completion Audit

updated: 2026-08-20
overall: v3-experiment-complete; ui-acceptance-failed; v4-closure-active

| # | Requirement | Status | Authoritative evidence |
| --- | --- | --- | --- |
| 1 | Operational install/run/test project | proven | 31 tests, Ruff, mypy, frozen-data validation, five PowerShell scripts parsed, and package build pass. |
| 2 | One sourced NASA subset and clean baseline | proven | Pinned `nasa/sample_app` v7.0.1 sources, provenance, curated spans, and hashes are unchanged. |
| 3 | 4/4/4/3/3 frozen cases and targets | proven for v3 | V3 inputs and unchanged v2 prompt resources were remotely frozen at `3984e779` before execution. V1 timing is explicitly not claimed. |
| 4 | Same analyst output and same Top-K arms | proven | All 18 Baseline/Proposed source-ID sequences and candidate fingerprints independently validate. |
| 5 | Exactly three roles plus shared non-agent retrieval | proven | Three ADK `LlmAgent` roles; `HybridRetriever` is the shared deterministic non-agent retrieval tool. |
| 6 | Exact span, source ID, reason, verifier, fail-closed | proven | All 29 exposed reviews satisfy exact-source and single-supported-verdict checks; tested failure paths prevent publication. |
| 7 | Type-level metrics, raw artifact, and provenance | proven | Tracked v3 raw result and manifest bind source/tag/manifest, prompts/input, ADK/model, execution, image, GCS generation, and SHA. |
| 8 | Demo UI and browser evidence | failed for v3 | Loading copy passed, but the audit reproduced a stale-response source mismatch, 390 px control wrapping, and reload focus loss. |
| 9 | Build/test/error/rejection paths | proven | Tests cover prompt/input drift, v1/v2 compatibility, v3 manifest requirements, timeouts, cardinality, checkpoint failure, log allowlisting, publication integrity, and GCS fail-closed 503. |
| 10 | Cloud Run + Vertex + GCS + Logging + minimum IAM | proven | 18-case Job, immutable result, explicit publish, same digest, dedicated identities, structured logs, and private 403 boundary verified. |
| 11 | Git and external-change discipline | proven | `ecr-poc-v3-freeze` was pushed before the billable run; this final evidence commit does not move it, and the v2 tag/artifacts remain unchanged. |

Final accepted identity: run `cloud-v3-20260820T043842Z-6e260831`, execution `ecr-poc-evaluate-fq5s4`, revision `ecr-poc-00006-6jz`, generation `1787201087845537`, SHA-256 `34ba69003c632d30a93aa47d3e21d4eb166634b1dcd91b44badc1b9de5ef23a1`.

The measured v3 experiment result is accepted without an accuracy threshold: 10/12 retrieval coverage, 9/10 conditional review success, 4/6 control false alarms, and 29 verified reviews. The deployment is not accepted as final because of the three major UI findings. They will be corrected only under a distinct later freeze; the v3 tag and artifacts remain unchanged.
