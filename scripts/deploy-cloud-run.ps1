param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Region = "asia-northeast3",

    [switch]$ApproveBillableResources
)

$ErrorActionPreference = "Stop"

if (-not $ApproveBillableResources) {
    throw "Refusing to enable Cloud Build or deploy without -ApproveBillableResources."
}

gcloud services enable cloudbuild.googleapis.com --project $ProjectId --quiet
if ($LASTEXITCODE -ne 0) {
    throw "Cloud Build API enablement failed."
}

$buildServiceAccountId = "ecr-poc-build"
$buildServiceAccountEmail = "$buildServiceAccountId@$ProjectId.iam.gserviceaccount.com"
$buildServiceAccountResource = "projects/$ProjectId/serviceAccounts/$buildServiceAccountEmail"

gcloud iam service-accounts describe $buildServiceAccountEmail `
    --project $ProjectId `
    --format "value(email)" 2>$null | Out-Null

if ($LASTEXITCODE -ne 0) {
    gcloud iam service-accounts create $buildServiceAccountId `
        --project $ProjectId `
        --display-name "ECR PoC Cloud Run build" `
        --description "Least-privilege build identity for the ecr-poc source deployment" `
        --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "Dedicated build service account creation failed."
    }
}

gcloud projects add-iam-policy-binding $ProjectId `
    --member "serviceAccount:$buildServiceAccountEmail" `
    --role "roles/run.builder" `
    --condition None `
    --format none `
    --quiet
if ($LASTEXITCODE -ne 0) {
    throw "Cloud Run Builder role grant failed."
}

$deployerAccount = gcloud config get-value account 2>$null
if ([string]::IsNullOrWhiteSpace($deployerAccount)) {
    throw "Unable to determine the active deployer account."
}

gcloud iam service-accounts add-iam-policy-binding $buildServiceAccountEmail `
    --project $ProjectId `
    --member "user:$deployerAccount" `
    --role "roles/iam.serviceAccountUser" `
    --format none `
    --quiet
if ($LASTEXITCODE -ne 0) {
    throw "Build service account actAs grant failed."
}

$runtimeEnvironment = @(
    "GOOGLE_GENAI_USE_VERTEXAI=TRUE"
    "GOOGLE_CLOUD_PROJECT=$ProjectId"
    "GOOGLE_CLOUD_LOCATION=global"
    "ECR_LLM_MODEL=gemini-3.5-flash"
    "ECR_EMBEDDING_MODEL=gemini-embedding-001"
) -join ","

gcloud run deploy ecr-poc `
    --source . `
    --build-service-account $buildServiceAccountResource `
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
    --set-env-vars $runtimeEnvironment `
    --no-allow-unauthenticated `
    --quiet

if ($LASTEXITCODE -ne 0) {
    throw "Cloud Run deployment failed."
}

Write-Output "Private Cloud Run service ecr-poc deployed to $Region."
