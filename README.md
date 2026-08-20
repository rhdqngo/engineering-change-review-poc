# Evidence-grounded Engineering Change Review PoC

This repository contains a pre-registered experiment over a pinned NASA cFS `sample_app` v7.0.1 subset. It compares a baseline fixed Hybrid Retrieval Top-6 with a proposed three-role Google ADK review over the exact same candidates. Only exact source spans supported by an independent verifier can reach final review output.

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

Open `http://127.0.0.1:8080`. The default Demo UI uses a deterministic fixture and labels it as non-LLM evidence. The `Frozen Vertex evaluation` source reads the pinned completed experiment artifact at `results/runs/vertex-adk.json`; a later fixture run cannot replace that evidence by updating `results/latest.json`.

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
