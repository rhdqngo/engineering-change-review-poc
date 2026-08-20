# Completion Audit

updated: 2026-08-20
overall: v4-complete-and-published

| # | Requirement | Status | Authoritative evidence |
| --- | --- | --- | --- |
| 1 | Operational install/run/test project | proven | 34 tests, Ruff, mypy, data validation, five PowerShell scripts parsed, and package build pass. |
| 2 | One sourced NASA subset and clean baseline | proven | Pinned `nasa/sample_app` v7.0.1 sources, provenance, curated spans, and hashes are unchanged. |
| 3 | 4/4/4/3/3 frozen cases and targets | proven for v4 | V4 inputs and unchanged v2 prompts were remotely frozen at `7b76bfa` before execution. V1 timing is explicitly not claimed. |
| 4 | Same analyst output and same Top-K arms | proven | All 18 Baseline/Proposed source-ID sequences and candidate fingerprints independently validate. |
| 5 | Exactly three roles plus shared non-agent retrieval | proven | Three ADK `LlmAgent` roles; `HybridRetriever` is the shared deterministic non-agent tool. |
| 6 | Exact span, source ID, reason, verifier, fail-closed | proven | All 27 exposed reviews satisfy exact-source and single-supported-verdict checks; tested failures prevent publication. |
| 7 | Type-level metrics, raw artifact, and provenance | proven | Tracked v4 result/manifest bind source/tag/manifest, prompts/input, ADK/model, execution, image, generation, and SHA. |
| 8 | Demo UI and browser evidence | proven | Deployed desktop/narrow, cold-start/disabled, rapid-source/case, focus recovery, provenance, representative, ARIA/touch, and rejected-evidence states pass independent audit. |
| 9 | Build/test/error/rejection paths | proven | Tests cover drift, legacy compatibility, v4 manifest, timeout, cardinality, checkpoint, log allowlisting, publication integrity, GCS 503, and UI repair guards. |
| 10 | Cloud Run + Vertex + GCS + Logging + minimum IAM | proven | 18-case Job, immutable result, explicit publish, same digest, dedicated identities, structured logs, and private 403 verified. |
| 11 | Git and external-change discipline | proven | Freeze tag was pushed before the billable run; final evidence is separate and does not move v2/v3/v4 tags. |

Final accepted identity: run `cloud-v4-20260820T050914Z-92f72d97`, execution `ecr-poc-evaluate-sxjnm`, revision `ecr-poc-00007-xvc`, generation `1787202918502625`, SHA-256 `22b07011b48daec60422a91c69420cdf08a58a85e972f51291de7980d0ee3116`.

The measured v4 result is accepted without an accuracy threshold: 10/12 retrieval coverage, 9/10 conditional review success, 3/6 control false alarms, and 27 verified reviews. The remaining false alarms are a product limitation, not hidden or normalized.
