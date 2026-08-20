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

    [switch]$ApproveBillableResources
)

$ErrorActionPreference = "Stop"

if (-not $ApproveBillableResources) {
    throw "Refusing to create GCP storage or IAM resources without -ApproveBillableResources."
}

$status = git status --porcelain
if (-not [string]::IsNullOrWhiteSpace($status)) {
    throw "Refusing to provision from a dirty worktree."
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
if ($InputPrefix -match '^frozen/ecr-poc-v[1-4](?:/|$)') {
    throw "Refusing to write v5 inputs into a historical v1-v4 GCS prefix."
}

$projectNumber = gcloud projects describe $ProjectId --format "value(projectNumber)"
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($projectNumber)) {
    throw "Unable to resolve the GCP project number."
}
$bucketName = "ecr-poc-$projectNumber-$Region"
$webServiceAccount = "ecr-poc-web@$ProjectId.iam.gserviceaccount.com"
$jobServiceAccount = "ecr-poc-job@$ProjectId.iam.gserviceaccount.com"

gcloud services enable `
    run.googleapis.com `
    cloudbuild.googleapis.com `
    artifactregistry.googleapis.com `
    aiplatform.googleapis.com `
    storage.googleapis.com `
    logging.googleapis.com `
    iam.googleapis.com `
    --project $ProjectId `
    --quiet
if ($LASTEXITCODE -ne 0) {
    throw "Required GCP API enablement failed."
}

gcloud storage buckets describe "gs://$bucketName" --project $ProjectId 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    gcloud storage buckets create "gs://$bucketName" `
        --project $ProjectId `
        --location $Region `
        --uniform-bucket-level-access `
        --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "Dedicated ECR bucket creation failed."
    }
}

gcloud storage buckets update "gs://$bucketName" `
    --pap `
    --versioning `
    --quiet
if ($LASTEXITCODE -ne 0) {
    throw "Dedicated ECR bucket hardening failed."
}

foreach ($account in @(
    @{ Id = "ecr-poc-web"; Display = "ECR PoC web runtime" },
    @{ Id = "ecr-poc-job"; Display = "ECR PoC evaluation job" }
)) {
    $email = "$($account.Id)@$ProjectId.iam.gserviceaccount.com"
    gcloud iam service-accounts describe $email --project $ProjectId --format "value(email)" 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        gcloud iam service-accounts create $account.Id `
            --project $ProjectId `
            --display-name $account.Display `
            --quiet
        if ($LASTEXITCODE -ne 0) {
            throw "Service account creation failed: $($account.Id)"
        }
    }
}

gcloud storage buckets add-iam-policy-binding "gs://$bucketName" `
    --member "serviceAccount:$webServiceAccount" `
    --role "roles/storage.objectViewer" `
    --quiet
if ($LASTEXITCODE -ne 0) {
    throw "Web bucket viewer grant failed."
}

gcloud storage buckets add-iam-policy-binding "gs://$bucketName" `
    --member "serviceAccount:$jobServiceAccount" `
    --role "roles/storage.objectUser" `
    --quiet
if ($LASTEXITCODE -ne 0) {
    throw "Job bucket object-user grant failed."
}

gcloud projects add-iam-policy-binding $ProjectId `
    --member "serviceAccount:$jobServiceAccount" `
    --role "roles/aiplatform.user" `
    --condition None `
    --format none `
    --quiet
if ($LASTEXITCODE -ne 0) {
    throw "Job Vertex AI grant failed."
}

$deployerAccount = gcloud config get-value account 2>$null
if ([string]::IsNullOrWhiteSpace($deployerAccount)) {
    throw "Unable to determine the active deployer account."
}
foreach ($runtimeAccount in @($webServiceAccount, $jobServiceAccount)) {
    gcloud iam service-accounts add-iam-policy-binding $runtimeAccount `
        --project $ProjectId `
        --member "user:$deployerAccount" `
        --role "roles/iam.serviceAccountUser" `
        --format none `
        --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "Deployer actAs grant failed for $runtimeAccount."
    }
}

$env:UV_CACHE_DIR = ".cache\uv"
uv run ecr-poc upload-freeze --bucket $bucketName --prefix $InputPrefix
if ($LASTEXITCODE -ne 0) {
    throw "Immutable experiment input upload failed."
}

Write-Output "bucket=$bucketName"
Write-Output "webServiceAccount=$webServiceAccount"
Write-Output "jobServiceAccount=$jobServiceAccount"
