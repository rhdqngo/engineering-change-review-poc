# Completion Audit

updated: 2026-08-20
overall: v5-local-function-complete-cloud-pending

| # | Requirement | Status | Authoritative evidence |
| --- | --- | --- | --- |
| 1 | Operational install/run/test project | locally proven | Active v5 validation, 49 tests, Ruff, mypy, five PowerShell script parsers, and sdist/wheel build pass. |
| 2 | One sourced NASA subset and clean baseline | proven | Pinned `nasa/sample_app` v7.0.1 sources, provenance, curated spans, and hashes are unchanged. |
| 3 | 4/4/4/3/3 cases and target-specific evidence | proven locally for v5 | `cases-v5.json` carries changed source, original/changed content, structured values, targets, and exact evidence per target. Remote tag remains pending. |
| 4 | Same analyst output and same Top-K arms | proven | All 18 Baseline/Proposed source-ID sequences and candidate fingerprints independently validate. |
| 5 | Exactly three roles plus shared non-agent retrieval | proven | Three ADK `LlmAgent` roles; `HybridRetriever` is the shared deterministic non-agent tool. |
| 6 | Exact span, source ID, reason, verifier, fail-closed | proven | All 27 exposed reviews satisfy exact-source and single-supported-verdict checks; tested failures prevent publication. |
| 7 | Type-level metrics, raw artifact, provenance, comparison | proven locally | V5 fixture baseline/q1 artifacts include index fingerprint and complete metrics; machine comparison classifies five failure modes case by case. |
| 8 | Demo UI and browser evidence | locally proven with stated gaps | Desktop/narrow, rapid source/case ownership, catalog 503→retry, published failure/recovery, blocked record inspection, full fingerprints, and narrow keyboard scroll pass; actual Vertex v5 remains approval-gated. |
| 9 | Build/test/error/rejection paths | locally proven | 49 tests cover active/historical drift, q1 invariants, timeout, cardinality, checkpoint, safe logging, publication, caching, endpoints, GCS 503, UI guards, historical path protection, and v5 namespace identity. |
| 10 | Cloud Run + Vertex + GCS + Logging + minimum IAM | implementation complete; v5 execution pending | Generalized scripts preserve dedicated identities/private service/least privilege and require explicit approvals plus manifest/tag/commit/prefix identity. |
| 11 | Git and external-change discipline | pending v5 authorization | V1-v4 history is untouched. V5 commit/push/tag and any external execution require explicit authorization. |

Preserved historical identity: run `cloud-v4-20260820T050914Z-92f72d97`, execution `ecr-poc-evaluate-sxjnm`, revision `ecr-poc-00007-xvc`, generation `1787202918502625`, SHA-256 `22b07011b48daec60422a91c69420cdf08a58a85e972f51291de7980d0ee3116`.

The local v5 fixture is not LLM evidence. Its baseline and q1 both cover 12/12 mutation cases with zero control false alarms by construction; q1 improves expected-target mean rank from 1.846154 to 1.692308 while regressing three cross-artifact target ranks. Accuracy is not a completion threshold.

## V5 requirement-by-requirement audit

`proven` means current repository or rendered evidence directly demonstrates the requirement. `pending external evidence` is not treated as complete.

| Requirement | Status | Authoritative evidence |
| --- | --- | --- |
| NASA `sample_app` subset and Experimental Clean Baseline | proven | `data/nasa/provenance.json`, pinned source hashes, `data/nasa/artifacts.json`, and active validation of 32 spans. |
| Direct 4 / Semantic 4 / Cross-Artifact 4 / Clean 3 / Benign 3 | proven | `data/cases/cases-v5.json`; `validate-data` returns 4/4/4/3/3 across 18 cases. |
| Changed artifact, original/changed content, structured old/new, targets, target evidence | proven | Strict `CaseDefinition`, all v5 records, exact original-source and target-evidence validation, and schema tests. |
| Shared 50/50 BM25+embedding Top-K | proven | `HybridRetriever`, manifest fusion contract, and evaluation configuration; no vector DB or graph component exists. |
| Same analyst output and exact candidate objects/order/fingerprint for both arms | proven | `run_case` invokes analysis/retrieval once and aliases the same candidate list; all 18 cases are checked in tests and publication validation. |
| Reproducible embedding index identity | proven locally | v5 embedding manifest is frozen and now included in GCS input upload; run/case provenance carries the full document-vector fingerprint. Actual Vertex fingerprint awaits the approved run. |
| Exactly three ADK `LlmAgent` roles; retrieval remains a tool | proven | Exactly three constructors in `src/ecr_poc/adk_agent/agent.py`; `root_agent` aliases Change Analyst and does not create a coordinator. |
| Review decisions restricted and `REVIEW` requires source/evidence/reason | proven | Strict `Decision` enum and `ReviewItem` validator; versioned prompt and schema hashes are validated. |
| Top-K + exact span + verifier required for visible review | proven | Pipeline gate and publication recomputation; tests cover off-Top-K, wrong span, duplicate/missing decision, verifier missing/reject/duplicate, and provider errors. |
| Overall and type-level five-metric family | proven | `calculate_metrics` and both v5 fixture results contain Retrieval Coverage, conditional review success, false alarm, selection added value, and unsupported blocked overall/by type. |
| Cloud Run service and sequential evaluation Job implementation | proven as code; pending external evidence | Deployment script configures private service plus one-task/one-parallelism/no-retry Job with one immutable image. Actual v5 revision/Job not yet deployed. |
| Vertex AI generation and embedding implementation | proven as code; pending external evidence | ADK provider and Vertex embedder use manifest-pinned model/config. No approved v5 Vertex calls have run. |
| GCS immutable inputs/results/checkpoints/publish pointer | proven locally as code; pending external evidence | GCS stores use generation preconditions, terminal checkpoint validation, separate `frozen/ecr-poc-v5`, `runs/v5`, and `published/v5/demo.json`. Actual v5 objects await approval. |
| Cloud Logging safe decision events | proven locally as schema/tests; pending external evidence | `DecisionLogEvent` allowlist rejects raw fields; pipeline logs case/role/source/decision/verdict/stage/error type. Actual v5 log query awaits the Job. |
| Dedicated service accounts, least privilege, private service | proven in scripts; pending external evidence | Provision/verify scripts require web objectViewer, job objectUser + aiplatform.user, reject broad roles, and require unauthenticated 403. Actual v5 IAM/deployment audit awaits approval. |
| Fixture/published authority and full 18-case review UI | proven locally | API/UI tests and actual browser cover fixture/published labels, change delta, candidates, evidence/verifier/blocked/provenance, catalog retry, error recovery, and all case choices. |
| Historical v1-v4 immutability and offline compatibility | proven locally | Historical file diff is empty; `validate-historical` validates v1 freeze, v2-v4 manifests, and retained v1-v4 result IDs outside the web path. External objects/tags have not been touched. |
| Published result cache and split health endpoints | proven | TTL-keyed cache tests plus `/healthz`, `/readyz`, and `/integrity` API tests; case selection uses the cached published evaluation. |
| Parameterized manifest/tag/commit/GCS prefixes | proven | All five PowerShell scripts require exact manifest/tag/commit identity, accept v5 prefixes, retain approval switches, and parse successfully. |
| Excluded complexity remains excluded | proven by repository inspection | No database, knowledge graph, managed vector DB, extra agent, fine-tuning, SysML/MBSE, autonomous negotiation, or browser-triggered billable execution was introduced. |
| Unchanged function-complete baseline recorded before iteration | proven locally | `fixture-v5-baseline.json`, manifest/input/prompt/index identities, candidate seals, hashes, and report are retained unchanged by q1 execution. |
| One-variable reproducible quality iteration and case classification | proven locally | v5-q1 changes only query construction; invariant checks pass and all five requested failure classes plus target ranks are in the machine comparison. |
| Full local completion commands | proven | `validate-data`, `validate-historical`, 49 tests, Ruff, mypy, build, five-script parsing, strict baseline/q1 result validation, and historical diff check all pass. |
| Actual v5 18-case run, publish, IAM/Logging, and deployed UI | pending external evidence | Requires exact commit/tag plus the user's explicit commit/push, billable deploy/run, and publish authorization. |
