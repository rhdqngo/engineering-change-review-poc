# Engineering Change Review Experiment Report

status: actual-run-and-deployment-complete  
freeze: `ecr-poc-preregistered-v1`  
run id: `c31aabbe-91a4-4a24-9d43-2515fe0d0155`  
updated: 2026-08-20

## Result in one sentence

The LLM layer provided useful candidate triage for explicit and some semantic/cross-artifact changes, but it did **not** provide generally trustworthy additional review value: it reduced 108 fixed candidates to 29 verified findings while retaining the frozen target in only 9/12 mutation cases end-to-end and raised false alarms in 4/6 controls.

## Frozen run

- Source: official NASA `nasa/sample_app` v7.0.1 at commit `2f93d1a4159a02b18d67ee83342c9e96b90e23e4`.
- Cases: Direct 4, Semantic 4, Cross-Artifact 4, Clean 3, Benign 3.
- Retrieval: BM25 0.5 + Vertex `gemini-embedding-001` 0.5, Top-K 6.
- Roles: Change Analyst, Engineering Review, Evidence Verifier; Google ADK 2.7.1 and Vertex `gemini-3.5-flash`, temperature 0.
- Run interval: 2026-08-20 01:06:42–01:13:04 UTC.
- Raw artifact: `results/runs/vertex-adk.json` (SHA-256 `7832aad0728660c2283cfa41aedddf06a34e3b50e7fd6d514e0d0854b69ee28e`).
- Completion checkpoint: `results/runs/vertex-adk.checkpoint.json` (SHA-256 `cb6180d7ae79eadb8560182b87606d5cd660ab0769d829c46d82975a5e11d45c`).

Two adapter failures before the completed run are preserved separately. Neither produced a completed case or changed the freeze: attempt 1 used an unsupported ADK root mode; attempt 2 failed to read task-mode terminal output. The completed run uses fresh-session ADK `chat` roles with the same frozen inputs.

## Metrics

| Case type | Retrieval Coverage | LLM Review Success among hits | False Alarm | Verified / fixed candidates | Candidate reduction |
| --- | ---: | ---: | ---: | ---: | ---: |
| Direct | 4/4 (100%) | 4/4 (100%) | n/a | 8/24 | 66.7% |
| Semantic | 3/4 (75%) | 3/3 (100%) | n/a | 9/24 | 62.5% |
| Cross-Artifact | 3/4 (75%) | 2/3 (66.7%) | n/a | 6/24 | 75.0% |
| Clean | n/a | n/a | 1/3 (33.3%) | 2/18 | 88.9% |
| Benign | n/a | n/a | 3/3 (100%) | 4/18 | 77.8% |
| Overall | 10/12 (83.3%) | 9/10 (90.0%) | 4/6 (66.7%) | 29/108 | 73.1% |

All 18 Baseline and Proposed arms had identical ordered candidate source IDs and candidate fingerprints. All 29 exposed findings had a real Top-K source ID, an exact source substring, a short reason, and an independent supported verdict. No role trace reported an error in the completed run.

## Five evaluation questions

### 1. Retrieval Coverage

Coverage was 10/12. Direct cases were 4/4. `SEM-04` missed `DESIGN_NOOP`, and `XART-02` missed `DESIGN_INIT_TABLE`. This caps any downstream review value: the LLM reviewer cannot recover sources outside the sealed Top-K.

### 2. LLM Review Success

Among the ten retrieval-hit mutations, the reviewer retained the full frozen target set in nine. It succeeded on all retrieval-hit Direct and Semantic cases, but only 2/3 Cross-Artifact hits. `XART-01` retrieved `TEST_DISPLAY` but selected two configuration sources instead, missing the pre-registered verification-impact target.

### 3. False Alarm

False alarm was the decisive weakness: 1/3 Clean and 3/3 Benign cases produced verified findings. `CLN-02` treated restoring the exact baseline value as a review need. The benign representation cases treated wording, `5 * 2`, and `0x0A` changes as engineering review needs despite frozen semantic equivalence.

### 4. Review Selection Added Value

The layer reduced the review docket by 73.1% overall and by 68.1% on mutation cases (72 candidates to 23 findings). It showed its strongest practical promise in explicit interface changes such as `DIR-02`, where it selected schema, interface, implementation, and test artifacts. However, Baseline already contained the frozen target in 10/12 mutations; Proposed reduced the list but lost one additional retrievable target and created six verified findings across four control cases. The measured value is therefore **triage efficiency in selected change types**, not improved recall or autonomous correctness.

Additional mutation findings beyond frozen targets are qualitatively plausible, but the protocol did not pre-label them. They are not counted as precision gains after observing the result.

### 5. Unsupported Output Blocked

The actual model proposed no non-exact or verifier-rejected REVIEW, so the actual blocked count was 0. The deterministic stress fixture injected one nonexistent span and blocked 1/1 before verifier exposure. Tests also show that missing/duplicate verifier verdicts and Engineering Review provider failure expose no advice. This validates the mechanism, not an actual-model unsupported-output rate.

## Answer to the product question

**There is limited, type-dependent additional value.** For explicit changes and retrieval-hit semantic changes, the layer substantially shrank the fixed docket while retaining all frozen targets. It was less reliable for cross-artifact verification impact and unreliable for restore/equivalent-expression controls. With a 66.7% control false-alarm rate, the current Proposed pipeline should not be used as an autonomous review gate.

Exact spans plus an independent verifier made outputs traceable, but did not make the selection decision correct. The false alarms had valid source spans and verifier approval; the verifier confirmed that evidence mentioned the changed value, not that the change created a material engineering review need.

## What can be trusted

- Trust the candidate seal, source identity, exact-span provenance, and fail-closed exposure mechanics.
- Treat `VERIFIED_REVIEW` as “traceable claim worth human inspection,” not “correct engineering impact.”
- Retain negative controls in every evaluation and publish type-level false alarms alongside success.
- For a future frozen experiment, add an explicit semantic-equivalence/no-change gate and require the verifier to challenge material consequence and counterfactual necessity, not merely textual support. This is a future protocol change, not a post-hoc modification to this run.

## Limitations

- One small NASA application subset and one completed model run; no variance estimate.
- Expected targets are pre-registered primary targets, not exhaustive labels for every plausible mutation impact.
- Retrieval depends on the model-normalized Change Analyst output and failed on two mutation cases.
- Model service behavior may evolve even with the same model identifier; raw role traces and hashes are therefore retained.
- Unsupported-output blocking was exercised synthetically because the actual run produced no unsupported span.
- The deployment serves the retained result for inspection; it does not make the one-run experiment statistically generalizable.

## Deployment validation

After exact user approval, the PoC was built with the repository Dockerfile and deployed privately to Cloud Run in `asia-northeast3`. Final revision `ecr-poc-00002-v9g` passed authenticated freeze health, the 18-case catalog, actual saved-result browser flows, fixture unsupported-evidence rejection, unauthenticated 403, and Cloud Logging inspection. The browser-visible result pins the frozen `results/runs/vertex-adk.json` artifact, whose hash remained unchanged after deployment fixes. Full operational evidence is recorded in `docs/results/deployment-log.md`.

## Reproduction

```powershell
$env:GOOGLE_GENAI_USE_VERTEXAI='TRUE'
$env:GOOGLE_CLOUD_PROJECT='<project-id>'
$env:GOOGLE_CLOUD_LOCATION='global'
$env:UV_CACHE_DIR='.cache\uv'
uv sync --frozen
uv run ecr-poc validate-data
uv run ecr-poc evaluate --provider vertex-adk --embedding vertex --output results\runs\vertex-adk.json
```

Re-running model inference is a new run, not a reproduction of identical stochastic service output. The frozen input hashes, configuration, raw trace schema, and metric calculation are reproducible; the retained completed artifact is the authoritative result reported above.
