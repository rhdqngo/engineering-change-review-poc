# Current Project State

status: complete  
phase: completed-experiment-and-deployment  
updated: 2026-08-20

## Objective

- Build a reproducible NASA cFS engineering-artifact PoC that measures the added value of evidence-grounded LLM review after a fixed Hybrid Retrieval Top-K.

## Active scope

- Scope Freeze from `docs/plans/LLM 기반 우주 Engineering Change Review.md`.
- One NASA cFS subset, Experimental Clean Baseline, and 18 pre-registered cases.
- Baseline versus three-role Google ADK/Vertex-compatible proposed pipeline, fail-closed evidence verification, evaluation artifacts, Demo UI, and GCP deployment configuration.

## Milestones

| Milestone | Status | Evidence / notes |
| --- | --- | --- |
| Bootstrap | complete | Official `uv init --app --package` scaffold generated in `.bootstrap-work/20260820-ecr-poc/scaffold`, validated there, merged without protected-path conflicts, and revalidated from root. |
| Data and experiment freeze | complete | Official NASA `nasa/sample_app` v7.0.1 at commit `2f93d1a4159a02b18d67ee83342c9e96b90e23e4`; 18 source files, 32 span records, 18 pre-registered cases, and three manifest hashes fixed before model results. |
| Core implementation | complete | Shared 50/50 BM25+dense Top-6 retrieval, three ADK roles, fixed-arm seal, exact-span gate, independent verifier, metrics, raw run writer, and API implemented and tested. |
| UI Foundation | complete | Three equal-content browser probes compared; Fixed-Candidate Review Docket selected as provisional lite Foundation. |
| Representative vertical slice | complete | FastAPI Docket covers all 18 cases; actual browser verified clean, restore, direct, semantic, cross-artifact, and unsupported-rejection states at desktop and narrow viewports. |
| Validation | complete | Data, lint, type, 13 tests, package build, health, fixture and actual raw artifacts, exact-span audit, and rendered browser evidence pass. |
| GCP deployment and verification | complete | After exact approval, a dedicated `roles/run.builder` identity built private revision `ecr-poc-00002-v9g`; authenticated health/catalog, actual browser flows, fail-closed rejection, unauthenticated 403, and Cloud Logging passed. |

## Completed major results

- Repository is operational with a Python 3.13 `uv` package application and verified install, run, and build commands.
- Stack decision: one Python service to align with ADK's Python `root_agent`/FastAPI Cloud Run path; separate frontend, managed vector DB, and Agent Engine rejected as unnecessary scope.
- Data decision: use the official public NASA cFS `sample_app` release tag v7.0.1 because it contains interface, configuration, implementation, tests, and change history in one small Apache-2.0 artifact family.
- Experiment freeze: Direct 4, Semantic 4, Cross-Artifact 4, Clean 3, and Benign 3 cases and expected targets are content-hashed in `data/cases/freeze.json` with `results_observed_before_freeze=false`.
- UI direction: a fixed candidate docket was selected because it exposes the controlled Top-K and the verified selection side by side without procedural UI overhead.
- Fail-closed UI finding: browser inspection caught that rejected fixture evidence was initially visible in the evidence desk; production UI was corrected so only `VERIFIED_REVIEW` evidence is exposed, then revalidated.
- Actual result: Retrieval Coverage 10/12, conditional LLM Review Success 9/10, control False Alarm 4/6, 29 verified findings from 108 fixed candidates, and actual unsupported blocked count 0.
- Product conclusion: limited triage value for Direct and retrieval-hit Semantic cases, mixed Cross-Artifact value, and insufficient trust for autonomous use because exact-span/verifier gates did not prevent relevance false alarms.
- Deployment conclusion: the Cloud Run PoC is private and scale-to-zero. Browser validation caught and corrected a saved-result selection defect so the deployed UI pins the frozen Vertex artifact rather than mutable fixture output.

## Verification state

| Check | Result | Command / evidence |
| --- | --- | --- |
| Install / restore | passed | `uv sync` from staging and repository root using CPython 3.13.14. |
| Baseline run | passed | `uv run ecr-poc` -> `Hello from ecr-poc!` in staging and repository root. |
| Build / check | passed | `uv build` produced source and wheel distributions. |
| Frozen data | passed | `uv run ecr-poc validate-data` validated 18 pinned source-file hashes, three freeze hashes, 32 spans, 18 cases, and 12 exact expected-evidence spans. |
| Offline retrieval diagnostic | passed | Deterministic fixture retriever covered all frozen targets in all 12 mutation cases; this is not the actual Vertex result. |
| Tests | passed | `uv run pytest -q tests -p no:cacheprovider` -> 13 passed; agent count, checkpoint, exact-span, duplicate/missing verifier, provider failure, and API paths covered. |
| Static/type | passed | `uv run ruff check .` and `uv run mypy src`. |
| Package build | passed | `uv build` created sdist and wheel; cache warning checked and cache content was absent from the sdist. |
| Health / API | passed | `/health` returned valid freeze; TestClient covered normal and unknown-case paths. |
| Fixture evaluation | passed, non-experimental | 12/12 offline retrieval hits, 12/12 fixture target retention, 0/6 fixture false alarms, one injected unsupported span blocked. |
| UI render / input | passed | Browser captures at 1440×900 and 390×844; representative case counts and candidate seals remained stable; rejected evidence stayed hidden. |
| Actual Vertex experiment | passed | 18/18 cases completed with no role errors; raw SHA-256 `7832aad0728660c2283cfa41aedddf06a34e3b50e7fd6d514e0d0854b69ee28e`. |
| Actual saved-result UI | passed | Browser verified provider/model provenance and representative actual Direct, Semantic, Cross-Artifact, Clean, and restore results. |
| Container runtime | passed in Cloud Build | The repository Dockerfile built successfully and revision `ecr-poc-00002-v9g` passed startup and request checks. Local Docker Desktop's Linux engine remains unavailable but is no longer a validation blocker. |
| Deployment script safety | passed | Both PowerShell scripts parse successfully; deploy script refuses to enable/build/deploy unless `-ApproveBillableResources` is supplied. |
| Cloud Run health / API | passed | Authenticated `/health` returned valid freeze; catalog returned Top-K 6 and 18 cases; `/api/evaluation` returned `vertex-adk`. |
| Cloud Run browser | passed | Actual DIR-02, XART-03, CLN-01, CLN-02 and fixture unsupported-rejection flows passed; capture `docs/ui/evidence/review-docket-cloud-run.png`. |
| Cloud Run access / logging | passed | Direct unauthenticated health returned 403; Cloud Logging recorded startup and representative 200/403 request paths. |

## Blockers and decisions needed

- None for the requested PoC. Local Docker Desktop is not running, but the same Dockerfile passed Cloud Build and deployed-runtime validation.

## Next checkpoint

- Optional human review of the report and Cloud resource retention; no further work is required by the frozen PoC scope.

## Related artifacts

- Plans: `docs/plans/LLM 기반 우주 Engineering Change Review.md`
- Decisions: `docs/data-selection.md`, `docs/experiment-protocol.md`
- UI Foundation: `docs/ui/foundation.md` (provisional)
- Reviews: none yet
- Experiment report: `docs/results/experiment-report.md`

## Update rules

Update this document only when the active milestone, scope, major result, blocker, validation state, or next checkpoint changes materially. Do not edit it solely to record the end of a session.
