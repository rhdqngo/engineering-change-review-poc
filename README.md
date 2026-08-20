# Evidence-grounded Engineering Change Review PoC

This repository contains a frozen experiment over a pinned NASA cFS `sample_app` v7.0.1 subset. It compares a baseline fixed Hybrid Retrieval Top-6 with a proposed three-role Google ADK review over the exact same candidates. Only exact source spans supported by an independent verifier can reach final review output. The retained v1 result is hash-consistent but is not claimed as externally timed preregistration; the v2 Cloud protocol establishes that evidence with a remote freeze tag before execution.

The accepted v2 Cloud run is `cloud-v2-20260820T035505Z-56ad91df`: 18/18 cases completed, retrieval coverage was 10/12, conditional review success was 9/10, and 4/6 control cases produced at least one false alarm. See `docs/results/experiment-report-v2.md` for provenance, limitations, and immutable result identity.

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

Open `http://127.0.0.1:8080`. The default Demo UI uses a deterministic fixture and labels it as non-LLM evidence. Local published-result mode reads the retained v1 artifact. A Cloud deployment sets `ECR_RESULT_STORE=gcs` and accepts only the generation- and SHA-verified object referenced by `published/demo.json`; it never silently falls back to the image-bundled v1 result.

## Reproducible evaluation

Offline fixture validation (not an experiment result):

```powershell
uv run ecr-poc evaluate --provider fixture --embedding local --output results\fixtures\deterministic.json --inject-unsupported
```

Actual frozen Vertex/ADK experiment (billable and credentialed):

```powershell
$env:GOOGLE_GENAI_USE_VERTEXAI='TRUE'
$env:GOOGLE_CLOUD_PROJECT='<project-id>'
$env:GOOGLE_CLOUD_LOCATION='global'
uv run ecr-poc evaluate --provider vertex-adk --embedding vertex --output results\runs\vertex-adk.json
```

The command validates frozen hashes first and writes per-role raw outputs, candidate seals, final fail-closed dispositions, and metrics by case type. See `docs/experiment-protocol.md` before interpreting results.

## Provenance and scope

- NASA source and hashes: `data/nasa/provenance.json`
- Frozen artifacts: `data/nasa/artifacts.json`
- Pre-registered cases and targets: `data/cases/cases.json`
- Freeze hashes: `data/cases/freeze.json`
- Selection rationale: `docs/data-selection.md`
- Deployment preparation: `deploy/README.md`

## Verifiable v2 Cloud batch

V2 adds a remote freeze tag, prompt hashes, source/image provenance, GCS input and result storage, a least-privilege Cloud Run Job, structured logs, and explicit publication.

After local validation, the implementation commit and `ecr-poc-v2-freeze` tag must be pushed with approval. Each external phase then has its own approval switch:

```powershell
.\scripts\provision-gcp.ps1 -ProjectId iceu-687 -ApproveBillableResources
.\scripts\deploy-cloud-run.ps1 -ProjectId iceu-687 -ApproveBillableResources
.\scripts\run-cloud-evaluation.ps1 -ProjectId iceu-687 -ApproveBillableRun
.\scripts\publish-cloud-evaluation.ps1 -ProjectId iceu-687 -RunId <validated-run-id> -ApprovePublish
.\scripts\verify-cloud-run.ps1 -ProjectId iceu-687
```

The browser never triggers a billable model run. It displays deterministic fixtures or the explicitly published GCS result. See `docs/experiment-protocol-v2.md` for the freeze and publication contract.
