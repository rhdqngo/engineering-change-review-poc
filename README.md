# Evidence-grounded Engineering Change Review PoC

This repository contains a frozen experiment over a pinned NASA cFS `sample_app` v7.0.1 subset. It compares a baseline fixed Hybrid Retrieval Top-6 with a proposed three-role Google ADK review over the exact same candidates. Only exact source spans supported by an independent verifier can reach final review output. The retained v1 result is hash-consistent but is not claimed as externally timed preregistration; the v2-v4 Cloud protocols establish that evidence with remote freeze tags before execution.

The accepted v4 Cloud run remains immutable historical evidence. Active development is isolated in v5: a richer case/evidence schema, fixed embedding-index identity, active-only web validation, separate health/integrity paths, generalized deployment inputs, and a one-variable local quality iteration. See `docs/results/experiment-report-v5.md`; local fixture metrics are never represented as LLM evidence.

## Setup and commands

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```powershell
$env:UV_CACHE_DIR='.cache\uv'
uv sync
uv run ecr-poc validate-data
uv run pytest -q tests -p no:cacheprovider
uv run ruff check .
uv run mypy src
uv build
uv run ecr-poc serve --host 127.0.0.1 --port 8080
```

Open `http://127.0.0.1:8080`. The default Demo UI uses a deterministic fixture and labels it as non-LLM evidence. Local published-result mode reads the active v5 fixture baseline. A Cloud deployment sets `ECR_RESULT_STORE=gcs` and accepts only the generation- and SHA-verified active experiment object; it never falls back to historical output.

## Reproducible evaluation

Offline fixture validation (not an experiment result):

```powershell
uv run ecr-poc evaluate --provider fixture --embedding local --output .runtime\deterministic-v5.json --inject-unsupported --no-update-latest
```

Local versioned Vertex/ADK diagnostic (billable and credentialed; run only after explicit approval):

```powershell
$env:GOOGLE_GENAI_USE_VERTEXAI='TRUE'
$env:GOOGLE_CLOUD_PROJECT='<project-id>'
$env:GOOGLE_CLOUD_LOCATION='global'
$sourceCommit = git rev-parse HEAD
uv run ecr-poc evaluate --provider vertex-adk --embedding vertex --experiment-manifest ecr-poc-v5.json --run-id local-v5-diagnostic --source-commit $sourceCommit --output results\runs\vertex-adk-v5-local.json --no-update-latest
```

Never reuse `vertex-adk.json` or any v1-v4 result path. The command validates frozen hashes first and writes per-role raw outputs, candidate seals, final fail-closed dispositions, and metrics by case type. The authoritative v5 execution path is the approval-gated Cloud Job below; see `docs/experiment-protocol-v5.md` before interpreting results.

## Provenance and scope

- NASA source and hashes: `data/nasa/provenance.json`
- Frozen artifacts: `data/nasa/artifacts.json`
- Pre-registered cases and targets: `data/cases/cases.json`
- Freeze hashes: `data/cases/freeze.json`
- Selection rationale: `docs/data-selection.md`
- Deployment preparation: `deploy/README.md`

## Verifiable v5 Cloud batch

V5 preserves every v1-v4 tag, result, and GCS object. Each external script requires the exact manifest, freeze tag, and source commit; prefix parameters keep v5 objects separate.

After local validation and explicit authorization, the implementation commit and requested freeze tag must identify the same remote commit. Replace `<commit>` only with that exact identity:

```powershell
.\scripts\provision-gcp.ps1 -ProjectId iceu-687 -ExperimentManifest ecr-poc-v5.json -FreezeTag ecr-poc-v5-freeze -SourceCommit <commit> -InputPrefix frozen/ecr-poc-v5 -ApproveBillableResources
.\scripts\deploy-cloud-run.ps1 -ProjectId iceu-687 -ExperimentManifest ecr-poc-v5.json -FreezeTag ecr-poc-v5-freeze -SourceCommit <commit> -InputPrefix frozen/ecr-poc-v5 -RunPrefix runs/v5 -PublishedObject published/v5/demo.json -ApproveBillableResources
.\scripts\run-cloud-evaluation.ps1 -ProjectId iceu-687 -ExperimentManifest ecr-poc-v5.json -FreezeTag ecr-poc-v5-freeze -SourceCommit <commit> -RunPrefix runs/v5 -ApproveBillableRun
.\scripts\publish-cloud-evaluation.ps1 -ProjectId iceu-687 -RunId <validated-run-id> -ExperimentManifest ecr-poc-v5.json -FreezeTag ecr-poc-v5-freeze -SourceCommit <commit> -RunPrefix runs/v5 -PublishedObject published/v5/demo.json -ApprovePublish
.\scripts\verify-cloud-run.ps1 -ProjectId iceu-687 -ExperimentManifest ecr-poc-v5.json -FreezeTag ecr-poc-v5-freeze -SourceCommit <commit> -RunPrefix runs/v5 -PublishedObject published/v5/demo.json -AuthenticatedBaseUrl http://127.0.0.1:8093
```

Run the private Cloud Run proxy on port 8093 in another terminal before the verification command. The browser never triggers a billable model run. It displays deterministic fixtures or the explicitly published GCS result. See `docs/experiment-protocol-v5.md` and `docs/results/experiment-report-v5.md`; all earlier reports remain historical evidence.
