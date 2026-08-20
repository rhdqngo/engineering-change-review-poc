# GCP v5 Deployment

The private Cloud Run service displays an explicitly published GCS result. A separate private Cloud Run Job performs the billable 18-case ADK/Vertex evaluation. The browser cannot trigger that Job.

## Identities and storage

- `ecr-poc-build`: existing source-build identity with `roles/run.builder`.
- `ecr-poc-web`: Cloud Run service identity with `roles/storage.objectViewer` on the dedicated bucket only.
- `ecr-poc-job`: Cloud Run Job identity with bucket-level `roles/storage.objectUser` and project-level `roles/aiplatform.user`.
- Bucket: `ecr-poc-<project-number>-<region>`, uniform access, public access prevention enforced, versioning enabled.

The default Compute service account is not used by either workload. Its existing project roles are outside this PoC's removal scope.

## Mandatory freeze precondition

Provisioning, deployment, execution, and publication refuse to run unless the worktree is clean and the requested `SourceCommit`, `HEAD`, `origin/main`, and requested `FreezeTag` are the same commit. All v1-v4 tags and objects remain immutable.

## Approved phases

Each mutating or billable phase requires its own explicit switch:

```powershell
.\scripts\provision-gcp.ps1 -ProjectId $PROJECT_ID -Region asia-northeast3 -ExperimentManifest ecr-poc-v5.json -FreezeTag ecr-poc-v5-freeze -SourceCommit $SOURCE_COMMIT -InputPrefix frozen/ecr-poc-v5 -ApproveBillableResources
.\scripts\deploy-cloud-run.ps1 -ProjectId $PROJECT_ID -Region asia-northeast3 -ExperimentManifest ecr-poc-v5.json -FreezeTag ecr-poc-v5-freeze -SourceCommit $SOURCE_COMMIT -InputPrefix frozen/ecr-poc-v5 -RunPrefix runs/v5 -PublishedObject published/v5/demo.json -ApproveBillableResources
.\scripts\run-cloud-evaluation.ps1 -ProjectId $PROJECT_ID -Region asia-northeast3 -ExperimentManifest ecr-poc-v5.json -FreezeTag ecr-poc-v5-freeze -SourceCommit $SOURCE_COMMIT -RunPrefix runs/v5 -ApproveBillableRun
.\scripts\publish-cloud-evaluation.ps1 -ProjectId $PROJECT_ID -Region asia-northeast3 -RunId <validated-run-id> -ExperimentManifest ecr-poc-v5.json -FreezeTag ecr-poc-v5-freeze -SourceCommit $SOURCE_COMMIT -RunPrefix runs/v5 -PublishedObject published/v5/demo.json -ApprovePublish
.\scripts\verify-cloud-run.ps1 -ProjectId $PROJECT_ID -Region asia-northeast3 -ExperimentManifest ecr-poc-v5.json -FreezeTag ecr-poc-v5-freeze -SourceCommit $SOURCE_COMMIT -RunPrefix runs/v5 -PublishedObject published/v5/demo.json
```

Provisioning uploads immutable v5 inputs, including the embedding reproducibility manifest, without touching historical prefixes. Deployment builds once and assigns the exact same image digest to the web service and Job. Execution uses one task, no retries, and a 30-minute timeout, but never changes the published pointer. The separately approved publish command validates the requested manifest, terminal checkpoint, and immutable result before changing `published/v5/demo.json`.

## Required verification

- Authenticated health reports `result_store=gcs`, a published run ID, and a valid freeze.
- The published run has 18 cases, matching arm seals, recomputed metrics, exact verified evidence, and no role errors.
- Service and Job use their dedicated identities and neither identity has Editor, Owner, or Storage Admin.
- Structured Cloud Logging events trace the published run without prompt, raw output, evidence, credential, or token content.
- Direct unauthenticated access remains denied.

For browser validation, proxy the private service and open `http://127.0.0.1:8093`:

```powershell
gcloud run services proxy ecr-poc --project $PROJECT_ID --region asia-northeast3 --port 8093
```
