# Completion Audit

updated: 2026-08-20
overall: first-v2-run-valid; UI-acceptance-correction-and-rerun-pending

| # | Requirement | Status | Authoritative evidence |
| --- | --- | --- | --- |
| 1 | Operational install/run/test project | proven | 27 tests, Ruff, mypy, data validation, five PowerShell parses, and package build pass. |
| 2 | One sourced NASA subset and clean baseline | proven | Pinned sources, provenance, curated spans, and source hashes remain unchanged. |
| 3 | 4/4/4/3/3 frozen cases and targets | v1 timing unproven; v2 prepared | V1 inputs and result hashes agree, but the first Git input commit postdates the v1 run. V2 manifest and prompt hashes are ready for a remote pre-run freeze. |
| 4 | Same analyst output and same Top-K arms | proven in code and v1; v2 pending run | One retrieval object is shared by both arms; publication independently recomputes fingerprints and arm identity. |
| 5 | Exactly three roles plus shared non-agent retrieval | proven | Three ADK `LlmAgent` roles remain. The unused ADK `FunctionTool` wrapper was removed; `HybridRetriever` is the deterministic shared non-agent tool. |
| 6 | Exact span, source ID, reason, verifier, fail-closed | proven locally | Existing gates remain; v2 adds role timeouts and explicit missing reviewer-output blocking. Publication rejects role errors or invalid verified evidence. |
| 7 | Type-level metrics, raw artifact, and provenance | v1 proven; v2 prepared | V2 run schema records source commit, freeze tag, prompt/input hashes, ADK version, execution, image, and artifact store. |
| 8 | Demo UI and browser evidence | corrective implementation in progress | Independent desktop/narrow audit found ambiguous run-ID truncation and an incorrect `legacy freeze` footer, plus smaller loading/touch/accessibility issues. The correction must be frozen, redeployed, and re-audited before completion. |
| 9 | Build/test/error/rejection paths | proven locally | 27 tests include role prompt drift, timeouts, reviewer/verifier cardinality, checkpoint failure, structured-log allowlisting, publication integrity, and GCS-unavailable 503 behavior. |
| 10 | Cloud Run + Vertex + GCS + Logging + minimum IAM | implementation prepared; external execution pending | Approval-gated scripts create the hardened bucket, dedicated web/job identities, same-image service/Job, structured logs, batch execution, publication, and verification. |
| 11 | Git and external-change discipline | proven through pre-run corrections | Every code correction has occurred before any v2 model execution. Provisioning and the first service/Job deployment exposed CLI serialization/schema defects; execution remained blocked while the fixes were validated for a new freeze.

The first v2 run satisfied pipeline, GCS, IAM, logging, and private-access checks but failed UI provenance acceptance. The project must not be marked fully complete until the corrected freeze is visible remotely, a new 18-case run is validated and published, the deployed UI passes re-audit, and final evidence is committed and pushed.
