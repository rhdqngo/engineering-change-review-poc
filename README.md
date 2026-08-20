# Evidence-grounded Engineering Change Review PoC

This repository implements a fail-closed Engineering Change Impact Review Copilot. A new engineering artifact is processed deterministically against the immutable NASA cFS v7.0.1 baseline, retrieved through Broad Hybrid Top-40 plus typed identifier 1-hop expansion, and reduced to a Final Review Docket Top-10. Exactly two Google ADK roles review and verify atomic impact claims. Only a Final Docket source with a matching absolute line range, contiguous exact span, and independent `SUPPORTED` verdict is exposed as `VERIFIED_REVIEW`.

The Human Engineer remains the decision maker; the system does not approve, reject, modify, or guarantee no baseline impact. V1-v5 remain immutable historical experiments. The 20 v6 cases are an observed frozen regression/diagnostic benchmark, not an unseen performance evaluation. The same fail-closed pipeline is exposed at `POST /api/reviews`. The approved `gemini-embedding-001` 768-dimensional document index and five immutable GCS payload generations are sealed in the v6 manifest. Push, deployment, the official Job, and publication remain separate approval boundaries.

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

Open `http://127.0.0.1:8080` for Live Review and `/evaluation` for the frozen regression benchmark. Local Live Review uses an explicitly non-LLM fixture unless `ECR_LIVE_PROVIDER=vertex-adk`; deployed activation is approval-gated and every submit button states that it uses Vertex AI. Live inputs and results are not persisted.

## Reproducible evaluation

Offline fixture validation (not an experiment result):

```powershell
uv run ecr-poc evaluate --provider fixture --embedding local --experiment-manifest ecr-poc-v6.json --source-commit LOCAL-V6-FUNCTIONAL-GATE --output .runtime\deterministic-v6.json --inject-unsupported --no-update-latest
```

Local versioned Vertex/ADK diagnostic (billable and credentialed; run only after explicit approval):

```powershell
$env:GOOGLE_GENAI_USE_VERTEXAI='TRUE'
$env:GOOGLE_CLOUD_PROJECT='<project-id>'
$env:GOOGLE_CLOUD_LOCATION='global'
$sourceCommit = git rev-parse HEAD
uv run ecr-poc evaluate --provider vertex-adk --embedding vertex --experiment-manifest ecr-poc-v6.json --run-id local-v6-diagnostic --source-commit $sourceCommit --output results\runs\vertex-adk-v6-local.json --no-update-latest
```

The separately approved one-time document-index build uses an experiment-specific resumable cache so historical embedding caches cannot be mixed into the v6 generation:

```powershell
uv run ecr-poc build-index --data-root .cache\v6-freeze --provider vertex --dimensions 768 --cache-path .cache\ecr-poc\v6-document-embeddings.json
```

Never reuse any v1-v5 result path. The command validates frozen hashes first and writes candidate seals, sanitized role traces, fail-closed dispositions, and metrics by case type. The authoritative v6 execution path is the approval-gated Cloud Job; see `docs/experiment-protocol-v6.md`.

## Provenance and scope

- NASA recursive source provenance: `.cache/v6-freeze/data/nasa/cfs-v7.0.1-provenance.json`
- Frozen artifacts/raw archive: `.cache/v6-freeze/data/nasa/`
- Frozen regression cases and claim slots: `data/cases/cases-v6.json`
- Freeze manifest: `data/experiments/ecr-poc-v6.json`
- Selection rationale: `docs/data-selection.md`
- Deployment preparation: `deploy/README.md`

## Verifiable v6 Cloud batch

V6 preserves every v1-v5 tag, result, and GCS object. Each external script requires the exact manifest, freeze tag, source commit, and v6 namespace.

After the approved Vertex document index is generated, an independently approved pre-freeze upload seals the five immutable payload objects—artifact package, raw archive, embedding metadata, vector matrix, and identifier index—and records their generations locally:

```powershell
uv run ecr-poc upload-freeze --bucket <bucket> --prefix frozen/ecr-poc-v6 --root .cache/v6-freeze --payload-only --inventory-output .runtime/v6-gcs-payload-inventory.json
```

Those generation/SHA records are copied into the tracked manifest and validated before the freeze commit. The inventory is not an experiment result. The later provisioning command uploads the final manifest and small inputs while byte-verifying the five sealed payloads.

After local validation and explicit authorization, the implementation commit and requested freeze tag must identify the same remote commit. Replace `<commit>` only with that exact identity:

```powershell
.\scripts\provision-gcp.ps1 -ProjectId iceu-687 -ExperimentManifest ecr-poc-v6.json -FreezeTag ecr-poc-v6-freeze -SourceCommit <commit> -InputPrefix frozen/ecr-poc-v6 -FrozenDataRoot .cache/v6-freeze -ApproveBillableResources
.\scripts\deploy-cloud-run.ps1 -ProjectId iceu-687 -ExperimentManifest ecr-poc-v6.json -FreezeTag ecr-poc-v6-freeze -SourceCommit <commit> -InputPrefix frozen/ecr-poc-v6 -RunPrefix runs/v6 -PublishedObject published/v6/demo.json -ApproveBillableResources
.\scripts\run-cloud-evaluation.ps1 -ProjectId iceu-687 -ExperimentManifest ecr-poc-v6.json -FreezeTag ecr-poc-v6-freeze -SourceCommit <commit> -RunPrefix runs/v6 -ApproveBillableRun
.\scripts\publish-cloud-evaluation.ps1 -ProjectId iceu-687 -RunId <validated-run-id> -ExperimentManifest ecr-poc-v6.json -FreezeTag ecr-poc-v6-freeze -SourceCommit <commit> -RunPrefix runs/v6 -PublishedObject published/v6/demo.json -ApprovePublish
.\scripts\verify-cloud-run.ps1 -ProjectId iceu-687 -ExperimentManifest ecr-poc-v6.json -FreezeTag ecr-poc-v6-freeze -SourceCommit <commit> -RunPrefix runs/v6 -PublishedObject published/v6/demo.json -AuthenticatedBaseUrl http://127.0.0.1:8093
```

Run the private Cloud Run proxy on port 8093 in another terminal before verification. On deployed v6, a Live Review submission is a user-triggered billable Vertex call; the evaluation route only reads the generation- and SHA-pinned published result. All earlier reports remain historical evidence.
