param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Region = "asia-northeast3",

    [switch]$ApproveBillableResources
)

$ErrorActionPreference = "Stop"

if (-not $ApproveBillableResources) {
    throw "Refusing to build or deploy without -ApproveBillableResources."
}

$status = git status --porcelain
if (-not [string]::IsNullOrWhiteSpace($status)) {
    throw "Refusing to deploy from a dirty worktree."
}
$head = git rev-parse HEAD
$originMain = git rev-parse origin/main
$freezeTag = git rev-parse refs/tags/ecr-poc-v3-freeze
if ($LASTEXITCODE -ne 0 -or $head -ne $originMain -or $head -ne $freezeTag) {
    throw "HEAD, origin/main, and ecr-poc-v3-freeze must identify the same commit."
}

$projectNumber = gcloud projects describe $ProjectId --format "value(projectNumber)"
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($projectNumber)) {
    throw "Unable to resolve the GCP project number."
}
$bucketName = "ecr-poc-$projectNumber-$Region"
$buildServiceAccountEmail = "ecr-poc-build@$ProjectId.iam.gserviceaccount.com"
$buildServiceAccountResource = "projects/$ProjectId/serviceAccounts/$buildServiceAccountEmail"
$webServiceAccount = "ecr-poc-web@$ProjectId.iam.gserviceaccount.com"
$jobServiceAccount = "ecr-poc-job@$ProjectId.iam.gserviceaccount.com"

$webEnvironment = @(
    "ECR_RESULT_STORE=gcs"
    "ECR_GCS_BUCKET=$bucketName"
    "ECR_PUBLISHED_OBJECT=published/demo.json"
    "ECR_FREEZE_VERSION=ecr-poc-preregistered-v3"
    "ECR_SOURCE_COMMIT=$head"
) -join ","

gcloud run deploy ecr-poc `
    --source . `
    --build-service-account $buildServiceAccountResource `
    --service-account $webServiceAccount `
    --project $ProjectId `
    --region $Region `
    --platform managed `
    --execution-environment gen2 `
    --port 8080 `
    --cpu 1 `
    --memory 512Mi `
    --min-instances 0 `
    --max-instances 1 `
    --concurrency 20 `
    --set-env-vars $webEnvironment `
    --no-allow-unauthenticated `
    --quiet
if ($LASTEXITCODE -ne 0) {
    throw "Cloud Run service deployment failed."
}

$latestRevision = gcloud run services describe ecr-poc `
    --project $ProjectId `
    --region $Region `
    --platform managed `
    --format "value(status.latestReadyRevisionName)"
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($latestRevision)) {
    throw "Unable to resolve the deployed revision."
}
$imageDigest = gcloud run revisions describe $latestRevision `
    --project $ProjectId `
    --region $Region `
    --format "value(status.imageDigest)"
if (
    $LASTEXITCODE -ne 0 -or
    [string]::IsNullOrWhiteSpace($imageDigest) -or
    $imageDigest -notmatch "@sha256:[0-9a-f]{64}$"
) {
    throw "Unable to resolve the deployed immutable image digest."
}

$jobEnvironment = @(
    "GOOGLE_GENAI_USE_VERTEXAI=TRUE"
    "GOOGLE_CLOUD_PROJECT=$ProjectId"
    "GOOGLE_CLOUD_LOCATION=global"
    "ECR_LLM_MODEL=gemini-3.5-flash"
    "ECR_EMBEDDING_MODEL=gemini-embedding-001"
    "ECR_ROLE_TIMEOUT_SECONDS=120"
    "ECR_GCS_BUCKET=$bucketName"
    "ECR_GCS_INPUT_PREFIX=frozen/ecr-poc-v3"
    "ECR_EXPERIMENT_MANIFEST=ecr-poc-v3.json"
    "ECR_SOURCE_COMMIT=$head"
    "ECR_CONTAINER_IMAGE_DIGEST=$imageDigest"
) -join ","

gcloud run jobs deploy ecr-poc-evaluate `
    --image $imageDigest `
    --command uv `
    --args "run,--frozen,--no-dev,ecr-poc,cloud-evaluate" `
    --service-account $jobServiceAccount `
    --project $ProjectId `
    --region $Region `
    --tasks 1 `
    --parallelism 1 `
    --max-retries 0 `
    --task-timeout 30m `
    --cpu 1 `
    --memory 1Gi `
    --set-env-vars $jobEnvironment `
    --quiet
if ($LASTEXITCODE -ne 0) {
    throw "Cloud Run evaluation Job deployment failed."
}

Write-Output "service=ecr-poc"
Write-Output "job=ecr-poc-evaluate"
Write-Output "imageDigest=$imageDigest"
Write-Output "bucket=$bucketName"
