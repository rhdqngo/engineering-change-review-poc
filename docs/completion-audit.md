# Completion Audit

updated: 2026-08-20
overall: v5-complete-baseline-published-q1-compared

| # | Requirement | Status | Authoritative evidence |
| --- | --- | --- | --- |
| 1 | Operational install/run/test project | proven | Active v5 validation, 49 tests, Ruff, mypy, five PowerShell script parsers, and sdist/wheel build pass. |
| 2 | One sourced NASA subset and clean baseline | proven | Pinned `nasa/sample_app` v7.0.1 sources, provenance, curated spans, and hashes are unchanged. |
| 3 | 4/4/4/3/3 cases and target-specific evidence | proven | `cases-v5.json` carries changed source, original/changed content, structured values, targets, and exact evidence per target under the pushed v5 freeze. |
| 4 | Same analyst output and same Top-K arms | proven | All 18 Baseline/Proposed source-ID sequences and candidate fingerprints independently validate. |
| 5 | Exactly three roles plus shared non-agent retrieval | proven | Three ADK `LlmAgent` roles; `HybridRetriever` is the shared deterministic non-agent tool. |
| 6 | Exact span, source ID, reason, verifier, fail-closed | proven | Strict validation passes for 29 baseline and 33 q1 exposed reviews; 5 and 9 unsupported outputs respectively remain withheld. |
| 7 | Type-level metrics, raw artifact, provenance, comparison | proven | Actual Vertex baseline/q1 artifacts, sidecars, index fingerprint, metrics, and five-class case comparison are retained. |
| 8 | Demo UI and browser evidence | proven | Actual published baseline passes desktop/narrow, 20 rapid transitions, blocked-record inspection, provenance, and keyboard scroll. |
| 9 | Build/test/error/rejection paths | proven | 49 tests cover active/historical drift, q1 invariants, timeout, cardinality, checkpoint, safe logging, publication, caching, endpoints, GCS 503, UI guards, historical path protection, and v5 namespace identity. |
| 10 | Cloud Run + Vertex + GCS + Logging + minimum IAM | proven | Revision `ecr-poc-00008-pk2`, two 18-case Vertex runs, immutable pointers, exact runtime roles, private denial, and safe 1/18/1 logs validate. |
| 11 | Git and external-change discipline | proven | Both freeze tags identify `4d1519f`; v1-v4 history and GCS identities remain untouched; all external mutations were approval-gated. |

Preserved historical identity: run `cloud-v4-20260820T050914Z-92f72d97`, execution `ecr-poc-evaluate-sxjnm`, revision `ecr-poc-00007-xvc`, generation `1787202918502625`, SHA-256 `22b07011b48daec60422a91c69420cdf08a58a85e972f51291de7980d0ee3116`.

The local v5 fixture remains functional evidence rather than LLM evidence. Actual Vertex q1 raised retrieval coverage from 10/12 to 12/12 but increased control false alarms from 4/6 to 5/6 and worsened mean expected-target rank from 1.818182 to 1.923077. Accuracy is not a completion threshold.

## V5 requirement-by-requirement audit

`proven` means current repository, immutable Cloud artifact, or rendered evidence directly demonstrates the requirement.

| Requirement | Status | Authoritative evidence |
| --- | --- | --- |
| NASA `sample_app` subset and Experimental Clean Baseline | proven | `data/nasa/provenance.json`, pinned source hashes, `data/nasa/artifacts.json`, and active validation of 32 spans. |
| Direct 4 / Semantic 4 / Cross-Artifact 4 / Clean 3 / Benign 3 | proven | `data/cases/cases-v5.json`; `validate-data` returns 4/4/4/3/3 across 18 cases. |
| Changed artifact, original/changed content, structured old/new, targets, target evidence | proven | Strict `CaseDefinition`, all v5 records, exact original-source and target-evidence validation, and schema tests. |
| Shared 50/50 BM25+embedding Top-K | proven | `HybridRetriever`, manifest fusion contract, and evaluation configuration; no vector DB or graph component exists. |
| Same analyst output and exact candidate objects/order/fingerprint for both arms | proven | `run_case` invokes analysis/retrieval once and aliases the same candidate list; all 18 cases are checked in tests and publication validation. |
| Reproducible embedding index identity | proven | Both actual runs carry the same full document-vector fingerprint `16de2823…f8505a`; the frozen pre-run embedding manifest remains unchanged. |
| Exactly three ADK `LlmAgent` roles; retrieval remains a tool | proven | Exactly three constructors in `src/ecr_poc/adk_agent/agent.py`; `root_agent` aliases Change Analyst and does not create a coordinator. |
| Review decisions restricted and `REVIEW` requires source/evidence/reason | proven | Strict `Decision` enum and `ReviewItem` validator; versioned prompt and schema hashes are validated. |
| Top-K + exact span + verifier required for visible review | proven | Pipeline gate and publication recomputation; tests cover off-Top-K, wrong span, duplicate/missing decision, verifier missing/reject/duplicate, and provider errors. |
| Overall and type-level five-metric family | proven | `calculate_metrics` and both v5 fixture results contain Retrieval Coverage, conditional review success, false alarm, selection added value, and unsupported blocked overall/by type. |
| Cloud Run service and sequential evaluation Job implementation | proven | Private revision `ecr-poc-00008-pk2` and its one-task/one-parallelism/no-retry Job share image digest `sha256:8f4cc7…e8afd`. |
| Vertex AI generation and embedding implementation | proven | Baseline and q1 each completed 18/18 actual ADK/Vertex cases with zero role errors. |
| GCS immutable inputs/results/checkpoints/publish pointer | proven | Thirty frozen inputs, sealed baseline/q1 results, baseline UI pointer, and non-UI q1 pointer validate by generation and SHA. |
| Cloud Logging safe decision events | proven | Each actual run has one start, 18 terminal cases, and one completion; filtered structured records contain no prohibited raw or credential fields. |
| Dedicated service accounts, least privilege, private service | proven | Web has bucket objectViewer only; Job has bucket objectUser plus aiplatform.user; no public invoker exists; final unauthenticated verification returned 403. |
| Fixture/published authority and full 18-case review UI | proven | Actual browser covers fixture/published labels, change delta, candidates, evidence/verifier/blocked/provenance, 20 rapid transitions, and desktop/narrow keyboard behavior. |
| Historical v1-v4 immutability and offline compatibility | proven | Historical file diff is empty; offline validation passes; external v1-v4 objects and tags were not touched. |
| Published result cache and split health endpoints | proven | TTL-keyed cache tests plus `/healthz`, `/readyz`, and `/integrity` API tests; case selection uses the cached published evaluation. |
| Parameterized manifest/tag/commit/GCS prefixes | proven | All five PowerShell scripts require exact manifest/tag/commit identity, accept v5 prefixes, retain approval switches, and parse successfully. |
| Excluded complexity remains excluded | proven by repository inspection | No database, knowledge graph, managed vector DB, extra agent, fine-tuning, SysML/MBSE, autonomous negotiation, or browser-triggered billable execution was introduced. |
| Unchanged function-complete baseline recorded before iteration | proven locally | `fixture-v5-baseline.json`, manifest/input/prompt/index identities, candidate seals, hashes, and report are retained unchanged by q1 execution. |
| One-variable reproducible quality iteration and case classification | proven | Actual q1 changes only query construction; all invariant checks pass and five requested failure classes plus target ranks are in the retained comparison. |
| Full local completion commands | proven | `validate-data`, `validate-historical`, 49 tests, Ruff, mypy, build, five-script parsing, strict baseline/q1 result validation, and historical diff check all pass. |
| Actual v5 18-case run, publish, IAM/Logging, and deployed UI | proven | Baseline and q1 immutable runs complete; baseline UI and q1 comparison pointers validate; Cloud/IAM/Logging/browser evidence is recorded. |
