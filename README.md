# Evidence-grounded Engineering Change Review PoC

This repository contains a frozen experiment over a pinned NASA cFS `sample_app` v7.0.1 subset. It compares a baseline fixed Hybrid Retrieval Top-6 with a proposed three-role Google ADK review over the exact same candidates. Only exact source spans supported by an independent verifier can reach final review output. The retained v1 result is hash-consistent but is not claimed as externally timed preregistration; the v2 and v3 Cloud protocols establish that evidence with remote freeze tags before execution.

The final accepted v4 Cloud run is `cloud-v4-20260820T050914Z-92f72d97`: 18/18 cases completed, retrieval coverage was 10/12, conditional review success was 9/10, and 3/6 control cases produced at least one false alarm. See `docs/results/experiment-report-v4.md` for provenance, limitations, and immutable result identity. V1, both v2 runs, and v3 remain immutable historical evidence.

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

## Verifiable v4 Cloud batch

V4 preserves the immutable v3 experiment while correcting its independent UI audit findings. It reuses the same frozen cases and v2 role prompts, records an explicit v4 manifest in run provenance and the published pointer, and is frozen at `7b76bfaa74d743d3200421d0dad681d740f1ca1c`.

After local validation, the implementation commit and `ecr-poc-v4-freeze` tag must identify the same remote commit. Each external phase retains its explicit approval switch:

```powershell
.\scripts\provision-gcp.ps1 -ProjectId iceu-687 -ApproveBillableResources
.\scripts\deploy-cloud-run.ps1 -ProjectId iceu-687 -ApproveBillableResources
.\scripts\run-cloud-evaluation.ps1 -ProjectId iceu-687 -ApproveBillableRun
.\scripts\publish-cloud-evaluation.ps1 -ProjectId iceu-687 -RunId <validated-run-id> -ApprovePublish
.\scripts\verify-cloud-run.ps1 -ProjectId iceu-687
```

The browser never triggers a billable model run. It displays deterministic fixtures or the explicitly published GCS result. See `docs/experiment-protocol-v4.md` and `docs/results/experiment-report-v4.md` for the completed closure; the v3 report and failed UI audit remain historical evidence.
