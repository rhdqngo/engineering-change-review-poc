# Private GCP deployment workflow

The deployment scripts reproduce the private v6-r1 Cloud Run service and one-task evaluation Job. They are included for auditability; running them is not required for the offline PoC and every billable or externally mutating phase requires an explicit approval switch.

## Identities and storage

- `ecr-poc-build`: source-build identity with `roles/run.builder`
- `ecr-poc-web`: service identity with bucket-scoped `roles/storage.objectViewer`
- `ecr-poc-job`: Job identity with bucket-scoped `roles/storage.objectUser` and project-scoped `roles/aiplatform.user`
- Bucket convention: `ecr-poc-<project-number>-<region>`, with uniform access, public access prevention, and versioning

The default Compute service account is not used by either workload.

## Required local variables

```powershell
$PROJECT_ID = '<your-gcp-project-id>'
$SOURCE_COMMIT = git rev-parse HEAD
```

The requested source commit, local `HEAD`, `origin/main`, and freeze tag must match. Historical tags and frozen objects are immutable.

## Approval-gated commands

```powershell
.\scripts\provision-gcp.ps1 -ProjectId $PROJECT_ID -Region asia-northeast3 -ExperimentManifest ecr-poc-v6-r1.json -FreezeTag ecr-poc-v6-r1-freeze -SourceCommit $SOURCE_COMMIT -InputPrefix frozen/ecr-poc-v6-r1 -ApproveBillableResources
.\scripts\deploy-cloud-run.ps1 -ProjectId $PROJECT_ID -Region asia-northeast3 -ExperimentManifest ecr-poc-v6-r1.json -FreezeTag ecr-poc-v6-r1-freeze -SourceCommit $SOURCE_COMMIT -InputPrefix frozen/ecr-poc-v6-r1 -RunPrefix runs/v6-r1 -PublishedObject published/v6/demo.json -ApproveBillableResources
.\scripts\run-cloud-evaluation.ps1 -ProjectId $PROJECT_ID -Region asia-northeast3 -ExperimentManifest ecr-poc-v6-r1.json -FreezeTag ecr-poc-v6-r1-freeze -SourceCommit $SOURCE_COMMIT -RunPrefix runs/v6-r1 -ApproveBillableRun
.\scripts\publish-cloud-evaluation.ps1 -ProjectId $PROJECT_ID -Region asia-northeast3 -RunId <validated-run-id> -ExperimentManifest ecr-poc-v6-r1.json -FreezeTag ecr-poc-v6-r1-freeze -SourceCommit $SOURCE_COMMIT -RunPrefix runs/v6-r1 -PublishedObject published/v6/demo.json -ApprovePublish
.\scripts\verify-cloud-run.ps1 -ProjectId $PROJECT_ID -Region asia-northeast3 -ExperimentManifest ecr-poc-v6-r1.json -FreezeTag ecr-poc-v6-r1-freeze -SourceCommit $SOURCE_COMMIT -RunPrefix runs/v6-r1 -PublishedObject published/v6/demo.json -AuthenticatedBaseUrl http://127.0.0.1:8093
```

Provisioning byte-verifies the sealed v6-r1 payloads. Deployment assigns one image digest to both service and Job. Evaluation runs one task with no retry and never changes the published pointer; publication is a separate validated step.

## Verification

- Authenticated health reports a ready, integrity-valid, generation-pinned result store.
- The published result contains all 20 terminal cases and passes candidate, claim, metric, provenance, and checkpoint validation.
- Service and Job use dedicated least-privilege identities and the service rejects unauthenticated access.
- Structured logs contain lifecycle events but no prompt, raw output, evidence text, credentials, or tokens.

Before verification, proxy the private service in another terminal:

```powershell
gcloud run services proxy ecr-poc --project $PROJECT_ID --region asia-northeast3 --port 8093
```

These commands create or modify cloud resources. Do not run them merely to validate a public clone.
