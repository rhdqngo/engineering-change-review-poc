# Evidence-grounded Engineering Change Review PoC

This repository contains a frozen experiment over a pinned NASA cFS `sample_app` v7.0.1 subset. It compares a baseline fixed Hybrid Retrieval Top-6 with a proposed three-role Google ADK review over the exact same candidates. Only exact source spans supported by an independent verifier can reach final review output. The retained v1 result is hash-consistent but is not claimed as externally timed preregistration; the v2 and v3 Cloud protocols establish that evidence with remote freeze tags before execution.

The published v3 Cloud run is `cloud-v3-20260820T043842Z-6e260831`: 18/18 cases completed, retrieval coverage was 10/12, conditional review success was 9/10, and 4/6 control cases produced at least one false alarm. Its independent UI audit closed the loading-copy issue but found three major interaction/responsive defects, so a separately frozen follow-up is active. See `docs/results/experiment-report-v3.md` and `docs/ui/reviews/2026-08-20-published-v3-docket.md`. V1 and both v2 runs remain immutable historical evidence.

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

## Verifiable v3 Cloud batch

V3 preserves the accepted v2 result while closing its last loading-copy finding. It reuses the frozen cases and v2 role prompts, and records an explicit v3 manifest in both run provenance and the published pointer. The completed freeze is `ecr-poc-v3-freeze` at `3984e77961b6edeacb2286935f65c1dd13c80a3e`.

After local validation, the implementation commit and `ecr-poc-v3-freeze` tag must identify the same remote commit. Each external phase retains its explicit approval switch:

```powershell
.\scripts\provision-gcp.ps1 -ProjectId iceu-687 -ApproveBillableResources
.\scripts\deploy-cloud-run.ps1 -ProjectId iceu-687 -ApproveBillableResources
.\scripts\run-cloud-evaluation.ps1 -ProjectId iceu-687 -ApproveBillableRun
.\scripts\publish-cloud-evaluation.ps1 -ProjectId iceu-687 -RunId <validated-run-id> -ApprovePublish
.\scripts\verify-cloud-run.ps1 -ProjectId iceu-687
```

The browser never triggers a billable model run. It displays deterministic fixtures or the explicitly published GCS result. See `docs/experiment-protocol-v3.md` for the completed freeze/publication contract and `docs/results/experiment-report-v3.md` for the accepted evidence; the v2 report remains historical.
