# Completion Audit

updated: 2026-08-20
overall: complete

| # | Requirement | Status | Authoritative evidence |
| --- | --- | --- | --- |
| 1 | Operational install/run/test project | proven | 28 tests, Ruff, mypy, frozen-data validation, PowerShell parsing, and package build pass. |
| 2 | One sourced NASA subset and clean baseline | proven | Pinned `nasa/sample_app` v7.0.1 sources, provenance, curated spans, and hashes are unchanged. |
| 3 | 4/4/4/3/3 frozen cases and targets | proven for v2 | V2 inputs and prompt resources were remotely frozen at `10c59bf` before execution. V1 timing is explicitly not claimed. |
| 4 | Same analyst output and same Top-K arms | proven | All 18 Baseline/Proposed source-ID sequences and candidate fingerprints independently validate. |
| 5 | Exactly three roles plus shared non-agent retrieval | proven | Three ADK `LlmAgent` roles; `HybridRetriever` is the shared deterministic non-agent retrieval tool. |
| 6 | Exact span, source ID, reason, verifier, fail-closed | proven | All 28 exposed reviews satisfy exact-source and single-supported-verdict checks; all tested failure paths prevent publication. |
| 7 | Type-level metrics, raw artifact, and provenance | proven | Tracked raw v2 result and manifest record source/tag, prompts/input, ADK/model, execution, image, GCS generation, and SHA. |
| 8 | Demo UI and browser evidence | proven | Final deployed desktop and 390 px browser checks show unambiguous run/freeze/commit provenance and representative states; prior independent findings are corrected. |
| 9 | Build/test/error/rejection paths | proven | Tests cover prompt/input drift, timeouts, reviewer/verifier cardinality, checkpoint failure, log allowlisting, publication integrity, and GCS fail-closed 503. |
| 10 | Cloud Run + Vertex + GCS + Logging + minimum IAM | proven | 18-case Job, immutable result, explicit publish, same digest, dedicated web/job identities, structured logs, and private 403 boundary verified. |
| 11 | Git and external-change discipline | proven | Freeze tag was pushed before the final billable run; final evidence is committed separately without moving the tag. |

Final accepted identity: run `cloud-v2-20260820T035505Z-56ad91df`, execution `ecr-poc-evaluate-587r6`, revision `ecr-poc-00005-485`, generation `1787198456573991`, SHA-256 `8ac24782609bcd61f9589f78f9786468ab6badd16e8461298287e4ad2be2ffb0`.

The measured result is deliberately accepted without an accuracy threshold: 18/18 completion and evidence integrity are the acceptance conditions. The observed 4/6 control false-alarm rate remains a documented product limitation.
