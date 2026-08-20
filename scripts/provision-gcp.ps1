param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Region = "asia-northeast3",

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
$freezeTag = git rev-parse refs/tags/ecr-poc-v2-freeze
if ($LASTEXITCODE -ne 0 -or $head -ne $originMain -or $head -ne $freezeTag) {
    throw "HEAD, origin/main, and ecr-poc-v2-freeze must identify the same commit."
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
    --public-access-prevention=enforced `
    --enable-versioning `
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
uv run ecr-poc upload-freeze --bucket $bucketName --prefix frozen/ecr-poc-v2
if ($LASTEXITCODE -ne 0) {
    throw "Immutable v2 input upload failed."
}
uv run ecr-poc upload-historical --bucket $bucketName
if ($LASTEXITCODE -ne 0) {
    throw "Historical v1 result upload failed."
}

Write-Output "bucket=$bucketName"
Write-Output "webServiceAccount=$webServiceAccount"
Write-Output "jobServiceAccount=$jobServiceAccount"
