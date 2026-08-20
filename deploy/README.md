# GCP Deployment Preparation

The container serves the Demo UI/API on `$PORT` and uses Application Default Credentials for Vertex AI. No secret is embedded in the image or environment file.

## Required APIs and least-privilege identities

- Cloud Run Admin and Service Account User are deployment-time permissions.
- Cloud Build and Artifact Registry are needed when deploying from source.
- The runtime service account needs `roles/aiplatform.user` for Vertex model and embedding calls.
- Cloud Run sends stdout/stderr request and application logs to Cloud Logging.

Actual API enablement, Artifact Registry/Cloud Build use, service-account creation, and deployment create external or billable resources and require explicit user approval immediately before execution.

## Prepared deployment sequence

Set `PROJECT_ID` in the operator shell, then run only after approval:

```powershell
.\scripts\deploy-cloud-run.ps1 -ProjectId $PROJECT_ID -Region asia-northeast3 -ApproveBillableResources
```

The script deploys a private service and deliberately refuses to run without the explicit approval switch. It enables Cloud Build, creates or reuses a dedicated `ecr-poc-build` identity with only `roles/run.builder`, uses the repository Dockerfile, limits the PoC to one scale-to-zero instance, and does not grant unauthenticated access.

## Post-deployment evidence checklist

1. `GET /health` returns `{"status":"ok","data_freeze":"valid"}`.
2. DIR-01 loads the same candidate seal captured in the corresponding raw run.
3. CLN-01 has zero verified reviews; a semantic or cross-artifact representative case renders its saved evaluation result.
4. A rejected unsupported output never exposes its proposed evidence as final advice.
5. `gcloud run services logs read ecr-poc --project $PROJECT_ID --region $REGION --limit 50` contains startup, health, and representative request entries without secrets.

The authenticated API checks and initial Cloud Logging read are automated by:

```powershell
.\scripts\verify-cloud-run.ps1 -ProjectId $PROJECT_ID -Region asia-northeast3
```

For actual browser validation of the private service, run an authenticated local proxy and open its localhost URL:

```powershell
gcloud run services proxy ecr-poc --project $PROJECT_ID --region asia-northeast3 --port 8093
```

## Local container validation

```powershell
docker build -t ecr-poc:local .
docker run --rm -p 8080:8080 ecr-poc:local
```
