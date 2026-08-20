# Completion Audit

updated: 2026-08-20
overall: local-v2-implementation-complete; remote-freeze-and-cloud-execution-pending

| # | Requirement | Status | Authoritative evidence |
| --- | --- | --- | --- |
| 1 | Operational install/run/test project | proven | 27 tests, Ruff, mypy, data validation, five PowerShell parses, and package build pass. |
| 2 | One sourced NASA subset and clean baseline | proven | Pinned sources, provenance, curated spans, and source hashes remain unchanged. |
| 3 | 4/4/4/3/3 frozen cases and targets | v1 timing unproven; v2 prepared | V1 inputs and result hashes agree, but the first Git input commit postdates the v1 run. V2 manifest and prompt hashes are ready for a remote pre-run freeze. |
| 4 | Same analyst output and same Top-K arms | proven in code and v1; v2 pending run | One retrieval object is shared by both arms; publication independently recomputes fingerprints and arm identity. |
| 5 | Exactly three roles plus shared non-agent retrieval | proven | Three ADK `LlmAgent` roles remain. The unused ADK `FunctionTool` wrapper was removed; `HybridRetriever` is the deterministic shared non-agent tool. |
| 6 | Exact span, source ID, reason, verifier, fail-closed | proven locally | Existing gates remain; v2 adds role timeouts and explicit missing reviewer-output blocking. Publication rejects role errors or invalid verified evidence. |
| 7 | Type-level metrics, raw artifact, and provenance | v1 proven; v2 prepared | V2 run schema records source commit, freeze tag, prompt/input hashes, ADK version, execution, image, and artifact store. |
| 8 | Demo UI and browser evidence | v1 proven; v2 default-viewport repair proven | UI distinguishes deterministic fixture from published Cloud evaluation, uses pointer run identity, keeps rejected evidence hidden, and adds no billable control. Fresh narrow v2 rendering remains unverified because the in-app override was ignored. |
| 9 | Build/test/error/rejection paths | proven locally | 27 tests include role prompt drift, timeouts, reviewer/verifier cardinality, checkpoint failure, structured-log allowlisting, publication integrity, and GCS-unavailable 503 behavior. |
| 10 | Cloud Run + Vertex + GCS + Logging + minimum IAM | implementation prepared; external execution pending | Approval-gated scripts create the hardened bucket, dedicated web/job identities, same-image service/Job, structured logs, batch execution, publication, and verification. |
| 11 | Git and external-change discipline | proven through pre-run corrections | Every code correction has occurred before any v2 model execution. Provisioning and the first service/Job deployment exposed CLI serialization/schema defects; execution remained blocked while the fixes were validated for a new freeze.

The project must not be marked fully complete until the v2 freeze tag is visible remotely, the approved Cloud Run Job finishes all 18 cases, the GCS result is validated and published, IAM/log/browser checks pass, and final evidence is committed and pushed with approval.
