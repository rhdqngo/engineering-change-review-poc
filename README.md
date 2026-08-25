# Evidence-grounded Engineering Change Review PoC

This repository is a reproducible proof of concept for narrowing an engineering change to a small, evidence-backed human review docket. It uses an immutable NASA cFS v7.0.1 baseline, deterministic hybrid retrieval and candidate reduction, and exactly two Google ADK roles for claim review and independent verification.

Only claims backed by an exact source span from the Final Top-10 docket and an independent `SUPPORTED` verdict are exposed. The Human Engineer remains the decision maker: the system does not approve changes, modify source, or guarantee that an item has no impact.

## Current release

- **Experiment:** `ecr-poc-regression-v6-r1`
- **Frozen tag:** `ecr-poc-v6-r1-freeze`
- **Cases:** 20 frozen regression and diagnostic cases
- **UI:** Live Review at `/` and the frozen Evaluation docket at `/evaluation`
- **Result:** all 20 cases completed with zero role errors; see [the v6-r1 report](docs/results/experiment-report-v6-r1.md)

The benchmark was observed during development. Its measurements are diagnostic and must not be presented as an unseen estimate of real-world accuracy or human time savings.

## Architecture

```text
Incoming Artifact
  -> deterministic Query Processor
  -> 50/50 BM25 + dense Broad Top-40
  -> typed identifier one-hop expansion (max 200)
  -> deterministic Final Top-10
  -> Engineering Reviewer
  -> exact source/span validation
  -> independent Evidence Verifier
  -> Human Engineer
```

Incoming artifacts are never inserted into the frozen baseline index. Reviewer and verifier failures are fail-closed, and raw model output is not returned by the public API.

## Local setup

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```powershell
$env:UV_CACHE_DIR='.cache\uv'
uv sync
uv run ecr-poc validate-data
uv run ecr-poc validate-historical
uv run pytest -q tests -p no:cacheprovider
uv run ruff check .
uv run mypy src
uv build
uv run ecr-poc serve --host 127.0.0.1 --port 8080
```

Open `http://127.0.0.1:8080`. Local Live Review uses a non-LLM fixture by default, needs no cloud credentials, and does not persist submissions or results.

## Offline reproducibility

Run the deterministic fixture without changing `results/latest.json`:

```powershell
uv run ecr-poc evaluate `
  --provider fixture `
  --embedding local `
  --experiment-manifest ecr-poc-v6.json `
  --source-commit LOCAL-V6-FUNCTIONAL-GATE `
  --output .runtime\deterministic-v6.json `
  --inject-unsupported `
  --no-update-latest
```

The frozen inputs, prompts, experiment manifests, historical results, and reports are tracked under `data/`, `results/`, and `docs/`. Large v6 artifacts and the approved Vertex embedding index are generation- and SHA-pinned in the experiment manifests rather than committed to Git.

## Optional Vertex AI execution

Copy the variable names from [.env.example](.env.example) into your own environment. Never commit a populated `.env` file or credentials. Vertex evaluation, GCS upload, deployment, and publication are billable or externally mutating operations and require explicit operator approval.

```powershell
$env:GOOGLE_GENAI_USE_VERTEXAI='TRUE'
$env:GOOGLE_CLOUD_PROJECT='<your-gcp-project-id>'
$env:GOOGLE_CLOUD_LOCATION='global'
$sourceCommit = git rev-parse HEAD

uv run ecr-poc evaluate `
  --provider vertex-adk `
  --embedding vertex `
  --experiment-manifest ecr-poc-v6-r1.json `
  --run-id local-v6-r1-diagnostic `
  --source-commit $sourceCommit `
  --output results\runs\vertex-adk-v6-r1-local.json `
  --no-update-latest
```

Deployment scripts are parameterized and documented in [deploy/README.md](deploy/README.md). The repository does not expose a public Cloud Run service.

## Presentation

The standalone Korean HTML presentation is in [docs/presentation/v6-demo](docs/presentation/v6-demo/README.md). It runs offline and walks through the deterministic, LLM, evidence, and human boundaries using one representative cFS change.

## Data, licensing, and attribution

Project-authored code and documentation are licensed under the [Apache License 2.0](LICENSE). The selected NASA cFS Sample App source retains its upstream Apache-2.0 license and exact provenance; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [data/nasa/provenance.json](data/nasa/provenance.json).

NASA names and source material identify provenance only. This project is not affiliated with, sponsored by, or endorsed by NASA, and it is not flight-qualified software.

Security issues should be reported as described in [SECURITY.md](SECURITY.md), not in a public issue.
