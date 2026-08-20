param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Region = "asia-northeast3",

    [Parameter(Mandatory = $true)]
    [string]$ExperimentManifest,

    [Parameter(Mandatory = $true)]
    [string]$FreezeTag,

    [Parameter(Mandatory = $true)]
    [string]$SourceCommit,

    [string]$InputPrefix = "frozen/ecr-poc-v5",

    [string]$RunPrefix = "runs/v5",

    [string]$PublishedObject = "published/v5/demo.json",

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
$freezeCommit = git rev-parse "refs/tags/$FreezeTag"
if (
    $LASTEXITCODE -ne 0 -or
    $head -ne $SourceCommit -or
    $head -ne $originMain -or
    $head -ne $freezeCommit
) {
    throw "HEAD, requested source commit, origin/main, and requested freeze tag must identify the same commit."
}
$manifestPath = Join-Path "data/experiments" $ExperimentManifest
if ((Split-Path -Leaf $ExperimentManifest) -ne $ExperimentManifest -or -not (Test-Path -LiteralPath $manifestPath)) {
    throw "ExperimentManifest must name an existing manifest leaf in data/experiments."
}
$experiment = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($experiment.freeze_tag -ne $FreezeTag) {
    throw "Experiment manifest freeze tag does not match -FreezeTag."
}
if (
    $InputPrefix -match '^frozen/ecr-poc-v[1-4](?:/|$)' -or
    $RunPrefix -eq 'runs' -or
    $RunPrefix -match '^runs/v[1-4](?:/|$)' -or
    $PublishedObject -eq 'published/demo.json' -or
    $PublishedObject -match '^published/v[1-4](?:/|$)'
) {
    throw "Refusing to configure v5 against a historical v1-v4 GCS namespace."
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
    "ECR_PUBLISHED_OBJECT=$PublishedObject"
    "ECR_FREEZE_VERSION=$($experiment.experiment_id)"
    "ECR_PUBLISHED_CACHE_TTL_SECONDS=30"
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
    "ECR_GCS_INPUT_PREFIX=$InputPrefix"
    "ECR_GCS_RUN_PREFIX=$RunPrefix"
    "ECR_EXPERIMENT_MANIFEST=$ExperimentManifest"
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
